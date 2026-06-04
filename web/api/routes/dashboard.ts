/**
 * Dashboard API 路由：聚合所有对象类型统计、最近更新项和校验结果
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, validate, OBJECT_TYPES, type ObjectType, LDVH_ROOT } from '../services/pytools.js'

const router = Router()

router.get('/', async (_req: Request, res: Response): Promise<void> => {
  try {
    // 并行请求所有对象类型列表
    const listPromises = OBJECT_TYPES.map(async (type) => {
      const result = await listObjects(type)
      return { type, result }
    })

    // 同时请求校验结果
    const [listResults, validationResult] = await Promise.all([
      Promise.all(listPromises),
      validate(),
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

    // 聚合最近更新项（取 top 10）
    const allItems: Array<{ id: string; type: string; title: string; status: string; updated: string }> = []
    for (const { type, result } of listResults) {
      if (!result.ok || !('data' in result)) continue
      const items = (result.data as { items: Array<Record<string, unknown>> }).items || []
      for (const item of items) {
        allItems.push({
          id: String(item.id || ''),
          type,
          title: String(item.title || ''),
          status: String(item.status || ''),
          updated: String(item.updated || ''),
        })
      }
    }
    allItems.sort((a, b) => b.updated.localeCompare(a.updated))
    const recentItems = allItems.slice(0, 10)

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
      validation,
    })
  } catch (err) {
    res.status(500).json({ ok: false, error: 'Dashboard aggregation failed' })
  }
})

export default router
