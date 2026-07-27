/**
 * Dashboard API 路由：聚合对象统计、最近更新项和最近提交。
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, ACTIVE_OBJECT_TYPES } from '../services/facts.js'
import { getGitLog } from '../services/git.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor } from '../services/typeColors.js'
import {
  deriveWorkCaseProgressProjection,
  type WorkCaseProgressGroup,
} from '../../shared/workcaseStatus.js'

const router = Router()

type DashboardObjectType = typeof ACTIVE_OBJECT_TYPES[number]

interface DashboardFactItemBase {
  id: string
  title: string
  title_en?: string
  title_zh?: string
  relativeTime: string
  typeColor: string
}

type DashboardFactItem =
  | DashboardFactItemBase & {
    type: 'workcase'
    progress_group: WorkCaseProgressGroup
    status?: never
  }
  | DashboardFactItemBase & {
    type: Exclude<DashboardObjectType, 'workcase'>
    status: string
    progress_group?: never
  }

type DashboardCandidate = DashboardFactItem & {
  updatedAt: string
  source_status: string
}

function getUpdatedAt(item: Record<string, unknown>): string {
  return String(item.updated_at || item.updated || '')
}

function getWorkCaseProgressGroup(item: Record<string, unknown>): WorkCaseProgressGroup | null {
  const status = String(item.status || 'unknown')
  const phase = typeof item.phase === 'string' ? item.phase : undefined
  return deriveWorkCaseProgressProjection(status, phase)?.progressGroup ?? null
}

function isFactItem(item: Record<string, unknown>): boolean {
  return item.kind !== 'type_not_integrated'
}

function getCoverageStatus(result: unknown): 'complete' | 'partial' | 'unavailable' {
  if (!result || typeof result !== 'object' || !('ok' in result) || result.ok !== true || !('data' in result)) {
    return 'unavailable'
  }
  const data = result.data
  if (!data || typeof data !== 'object' || !('coverage_status' in data)) return 'complete'
  return data.coverage_status === 'partial' || data.coverage_status === 'unavailable'
    ? data.coverage_status
    : data.coverage_status === 'complete'
      ? 'complete'
      : 'unavailable'
}

/** 按每种当前事实类型的唯一定义识别终态，不共享历史状态词。 */
function isActionableSourceStatus(type: Exclude<DashboardObjectType, 'workcase'>, status: string): boolean {
  if (type === 'spark') return !['routed', 'implemented', 'discarded'].includes(status)
  if (type === 'adr' || type === 'pitfall' || type === 'study') return status !== 'retired'
  return false
}

function isActionableItem(item: DashboardCandidate): boolean {
  return item.type === 'workcase'
    ? item.progress_group !== 'closed'
    : isActionableSourceStatus(item.type, item.source_status)
}

router.get('/', async (req: Request, res: Response): Promise<void> => {
  try {
    const locale = String(req.query.locale || 'zh')

    // 并行请求所有对象类型列表
    const listPromises = ACTIVE_OBJECT_TYPES.map(async (type) => {
      const result = await listObjects(type)
      return { type, result }
    })

    const [listResults, gitLog] = await Promise.all([
      Promise.all(listPromises),
      getGitLog(10, locale).catch(() => []),
    ])

    // 聚合统计信息
    const stats = listResults.map(({ type, result }) => {
      if (!result.ok || !('data' in result)) {
        return type === 'workcase'
          ? { type, total: 0, byProgressGroup: {} as Record<string, number>, coverageStatus: 'unavailable' as const }
          : { type, total: 0, byStatus: {} as Record<string, number>, coverageStatus: 'unavailable' as const }
      }
      const items = ((result.data as { items: Array<Record<string, unknown>> }).items || []).filter(isFactItem)
      if (type === 'workcase') {
        const byProgressGroup: Record<string, number> = {}
        let unclassifiedCount = 0
        for (const item of items) {
          const progressGroup = getWorkCaseProgressGroup(item)
          if (!progressGroup) {
            unclassifiedCount += 1
            continue
          }
          byProgressGroup[progressGroup] = (byProgressGroup[progressGroup] || 0) + 1
        }
        return { type, total: items.length, byProgressGroup, unclassifiedCount, coverageStatus: getCoverageStatus(result) }
      }
      const byStatus: Record<string, number> = {}
      for (const item of items) {
        const status = String(item.status || 'unknown')
        byStatus[status] = (byStatus[status] || 0) + 1
      }
      return { type, total: items.length, byStatus, coverageStatus: getCoverageStatus(result) }
    })

    // 聚合所有对象，用于最近更新和待推进
    const allItems: DashboardCandidate[] = []
    for (const { type, result } of listResults) {
      if (!result.ok || !('data' in result)) continue
      const items = ((result.data as { items: Array<Record<string, unknown>> }).items || []).filter(isFactItem)
      for (const item of items) {
        const updatedAt = getUpdatedAt(item)
        const sourceStatus = String(item.status || 'unknown')
        const commonItem: DashboardFactItemBase & Pick<DashboardCandidate, 'updatedAt' | 'source_status'> = {
          id: String(item.object_id || item.id || ''),
          title: String(item.title || item.object_id || item.id || ''),
          ...(typeof item.title_en === 'string' ? { title_en: item.title_en } : {}),
          ...(typeof item.title_zh === 'string' ? { title_zh: item.title_zh } : {}),
          source_status: sourceStatus,
          updatedAt,
          relativeTime: getRelativeTime(updatedAt, locale),
          typeColor: getTypeColor(type),
        }
        if (type === 'workcase') {
          const progressGroup = getWorkCaseProgressGroup(item)
          if (!progressGroup) continue
          allItems.push({ ...commonItem, type, progress_group: progressGroup })
        } else {
          allItems.push({ ...commonItem, type, status: sourceStatus })
        }
      }
    }

    // 最近更新项（取 top 10）
    const sortedByUpdated = [...allItems].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
    const toPublicItem = ({ updatedAt: _updatedAt, source_status: _sourceStatus, ...item }: DashboardCandidate): DashboardFactItem => item
    const recentItems = sortedByUpdated.slice(0, 10).map(toPublicItem)

    // 待推进项：筛选非终态，按 updated 时间倒序排列
    const actionItems = allItems
      .filter(isActionableItem)
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      .slice(0, 8)
      .map(toPublicItem)

    res.json({
      stats,
      recentItems,
      actionItems,
      recentChanges: gitLog,
    })
  } catch (err) {
    void err
    res.status(500).json({ ok: false, error: 'Dashboard aggregation failed' })
  }
})

export default router
