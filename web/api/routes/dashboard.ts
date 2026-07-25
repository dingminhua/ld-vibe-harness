/**
 * Dashboard API 路由：聚合对象统计、最近更新项和最近提交。
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, ACTIVE_OBJECT_TYPES } from '../services/facts.js'
import { getGitLog } from '../services/git.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor } from '../services/typeColors.js'
import { getWorkCaseProgressGroup } from '../../shared/workcaseStatus.js'

const router = Router()

function getUpdatedAt(item: Record<string, unknown>): string {
  return String(item.updated_at || item.updated || '')
}

function getDisplayStatus(type: string, item: Record<string, unknown>): string {
  const status = String(item.status || 'unknown')
  return type === 'workcase' ? getWorkCaseProgressGroup(String(item.phase || '')) ?? 'unknown' : status
}

function isFactItem(item: Record<string, unknown>): boolean {
  return item.kind !== 'type_not_integrated'
}

/** 判断状态是否为"可推进"（非终态） */
function isActionableStatus(type: string, status: string): boolean {
  const terminalStatuses = ['closed', 'retired', 'accepted', 'rejected', 'deprecated', 'archived', 'resolved', 'discarded']
  return !terminalStatuses.includes(status)
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
        return { type, total: 0, byStatus: {} as Record<string, number> }
      }
      const items = ((result.data as { items: Array<Record<string, unknown>> }).items || []).filter(isFactItem)
      const byStatus: Record<string, number> = {}
      for (const item of items) {
        const status = getDisplayStatus(type, item)
        byStatus[status] = (byStatus[status] || 0) + 1
      }
      return { type, total: items.length, byStatus }
    })

    // 聚合所有对象，用于最近更新和待推进
    const allItems: Array<Record<string, unknown>> = []
    for (const { type, result } of listResults) {
      if (!result.ok || !('data' in result)) continue
      const items = ((result.data as { items: Array<Record<string, unknown>> }).items || []).filter(isFactItem)
      for (const item of items) {
        const updatedAt = getUpdatedAt(item)
        allItems.push({
          ...item,
          id: String(item.object_id || item.id || ''),
          type,
          status: getDisplayStatus(type, item),
          path: String(item.canonical_path || item.path || ''),
          updated: updatedAt,
          relativeTime: getRelativeTime(updatedAt, locale),
          typeColor: getTypeColor(type),
        })
      }
    }

    // 最近更新项（取 top 10）
    const sortedByUpdated = [...allItems].sort((a, b) => getUpdatedAt(b).localeCompare(getUpdatedAt(a)))
    const recentItems = sortedByUpdated.slice(0, 10)

    // 待推进项：筛选非终态，按 updated 时间倒序排列
    const actionItems = allItems
      .filter(item => isActionableStatus(String(item.type || ''), String(item.status || '')))
      .sort((a, b) => getUpdatedAt(b).localeCompare(getUpdatedAt(a)))
      .slice(0, 8)

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
