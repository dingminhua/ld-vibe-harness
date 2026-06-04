/**
 * Changelog API 路由：返回 git 提交日志和 commit 详情
 */

import { Router, type Request, type Response } from 'express'
import { getGitLog, getGitShow } from '../services/git.js'

const router = Router()

/** GET /api/changelog?count=20 — 返回 git log 列表 */
router.get('/', async (req: Request, res: Response): Promise<void> => {
  try {
    const count = Math.min(Math.max(parseInt(req.query.count as string) || 50, 1), 200)
    const locale = String(req.query.locale || 'zh')
    const entries = await getGitLog(count, locale)
    res.json(entries)
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch git log'
    res.status(500).json({ ok: false, error: message })
  }
})

/** GET /api/changelog/:hash — 返回指定 commit 的 stat 信息 */
router.get('/:hash', async (req: Request, res: Response): Promise<void> => {
  try {
    const { hash } = req.params
    if (!hash || !/^[0-9a-f]{7,40}$/.test(hash)) {
      res.status(400).json({ ok: false, error: 'Invalid hash format' })
      return
    }
    const stat = await getGitShow(hash)
    res.json({ hash, stat })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Failed to fetch commit detail'
    res.status(500).json({ ok: false, error: message })
  }
})

export default router
