/**
 * Dashboard API 路由：聚合所有对象类型统计、最近更新项、校验结果和 landing 健康度
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, validate, OBJECT_TYPES, runPyToolsJson } from '../services/pytools.js'
import { getGitLog } from '../services/git.js'
import { getRelativeTime } from '../services/time.js'
import { getTypeColor } from '../services/typeColors.js'

const router = Router()

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

    // 同时请求校验结果、git log 和 landing-plan 摘要
    const [listResults, validationResult, gitLog, landingPlanResult] = await Promise.all([
      Promise.all(listPromises),
      validate(),
      getGitLog(10, locale).catch(() => []),
      runPyToolsJson('specs_validate.py', ['landing-plan', '--format', 'json']).catch(() => null),
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

    // 待推进项：筛选非终态，按 updated 时间倒序排列
    const actionItems = allItems
      .filter(item => isActionableStatus(String(item.status || '')))
      .sort((a, b) => String(b.updated || '').localeCompare(String(a.updated || '')))
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

    // landing 健康度摘要
    let landing: {
      totalRequirements: number
      gapTotal: number
      gapByArea: Record<string, number>
      capabilityStatus: Record<string, string>
      humanGateStatus: string
      validationPlanStatus: Record<string, string>
    } | null = null
    if (landingPlanResult && typeof landingPlanResult === 'object' && 'requirements' in landingPlanResult) {
      const lp = landingPlanResult as Record<string, unknown>
      const reqs = lp.requirements as Record<string, unknown> | undefined
      const caps = (lp.capabilities as Array<{ id: string; status: string }> | undefined) || []
      const hg = lp.human_gate as Record<string, unknown> | undefined
      const vp = lp.validation_plan as Record<string, string> | undefined
      landing = {
        totalRequirements: (reqs?.total as number) ?? 0,
        gapTotal: (reqs?.gap_total as number) ?? 0,
        gapByArea: (lp.gaps as Record<string, unknown>)?.by_owner_area as Record<string, number> ?? {},
        capabilityStatus: Object.fromEntries(caps.map(c => [c.id, c.status])),
        humanGateStatus: (hg as Record<string, unknown>)?.summary_label as string ?? 'unknown',
        validationPlanStatus: vp || {},
      }
    }

    res.json({
      profile,
      stats,
      recentItems,
      actionItems,
      recentChanges: gitLog,
      validation,
      landing,
    })
  } catch (err) {
    void err
    res.status(500).json({ ok: false, error: 'Dashboard aggregation failed' })
  }
})

export default router
