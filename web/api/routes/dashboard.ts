/**
 * Dashboard API 路由：聚合所有对象类型统计、最近更新项和校验结果
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, validate, OBJECT_TYPES, type ObjectType, LDVH_ROOT } from '../services/pytools.js'
import { getGitLog } from '../services/git.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor, TYPE_COLORS } from '../services/typeColors.js'

const router = Router()

/** 待推进状态优先级排序 */
const ACTION_STATUS_PRIORITY: Record<string, number> = {
  verifying: 1,
  review_needed: 2,
  executing: 3,
  planned: 4,
  active: 5,
  proposed: 6,
  pending_review: 7,
  observed: 8,
  confirmed: 9,
  draft: 10,
  suspended: 11,
}

/** 判断状态是否为"可推进"（非终态） */
function isActionableStatus(status: string): boolean {
  const terminalStatuses = ['closed', 'completed', 'rejected', 'superseded', 'deprecated', 'archived', 'resolved', 'implemented', 'applied', 'cancelled', 'filed']
  return !terminalStatuses.includes(status)
}

router.get('/', async (req: Request, res: Response): Promise<void> => {
  try {
    const locale = String(req.query.locale || 'zh')

    // 并行请求所有对象类型列表
    const listPromises = OBJECT_TYPES.map(async (type) => {
      const result = await listObjects(type)
      return { type, result }
    })

    // 同时请求校验结果和 git log
    const [listResults, validationResult, gitLog] = await Promise.all([
      Promise.all(listPromises),
      validate(),
      getGitLog(10, locale).catch(() => []),
    ])

    // 聚合 profile（取第一个 profile 对象）
    let profile = null
    const profileResult = listResults.find(r => r.type === 'profile')
    if (profileResult && profileResult.result.ok && 'data' in profileResult.result) {
      const items = (profileResult.result.data as { items: Array<Record<string, unknown>> }).items
      if (items && items.length > 0) {
        profile = items[0]
      }
    }

    // 聚合统计信息
    const stats = listResults.map(({ type, result }) => {
      if (!result.ok || !('data' in result)) {
        return { type, total: 0, byStatus: {} as Record<string, number> }
      }
      const items = (result.data as { items: Array<Record<string, unknown>> }).items || []
      const byStatus: Record<string, number> = {}
      for (const item of items) {
        const status = String(item.status || 'unknown')
        byStatus[status] = (byStatus[status] || 0) + 1
      }
      return { type, total: items.length, byStatus }
    })

    // 聚合所有对象，用于最近更新和待推进
    const allItems: Array<Record<string, unknown>> = []
    for (const { type, result } of listResults) {
      if (!result.ok || !('data' in result)) continue
      const items = (result.data as { items: Array<Record<string, unknown>> }).items || []
      for (const item of items) {
        allItems.push({
          ...item,
          type,
          relativeTime: getRelativeTime(String(item.updated || ''), locale),
          typeColor: getTypeColor(type),
        })
      }
    }

    // 最近更新项（取 top 10）
    const sortedByUpdated = [...allItems].sort((a, b) => String(b.updated || '').localeCompare(String(a.updated || '')))
    const recentItems = sortedByUpdated.slice(0, 10)

    // 待推进项：筛选非终态，按优先级排序
    const actionItems = allItems
      .filter(item => isActionableStatus(String(item.status || '')))
      .sort((a, b) => {
        const priorityA = ACTION_STATUS_PRIORITY[String(a.status)] ?? 99
        const priorityB = ACTION_STATUS_PRIORITY[String(b.status)] ?? 99
        if (priorityA !== priorityB) return priorityA - priorityB
        return String(a.updated || '').localeCompare(String(b.updated || ''))
      })
      .slice(0, 8)

    // 校验结果
    let validation: { ok: boolean; errors: number; warnings: number } = { ok: true, errors: 0, warnings: 0 }
    if (validationResult.ok && 'summary' in validationResult) {
      const summary = validationResult.summary as { errors?: number; warnings?: number }
      validation = {
        ok: validationResult.ok,
        errors: summary.errors ?? 0,
        warnings: summary.warnings ?? 0,
      }
    }

    res.json({
      profile,
      stats,
      recentItems,
      actionItems,
      recentChanges: gitLog,
      validation,
    })
  } catch (err) {
    res.status(500).json({ ok: false, error: 'Dashboard aggregation failed' })
  }
})

export default router
