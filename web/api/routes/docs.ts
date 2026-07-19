/**
 * GET /api/docs?path=specs/21-ADR-决策.md — 读取项目内文档内容
 */
import { Router, type Request, type Response } from 'express'
import { readFile } from 'fs/promises'
import path from 'path'
import { LDVH_ROOT } from '../services/pytools.js'

const router = Router()

/** 允许读取的目录前缀（安全白名单） */
const ALLOWED_PREFIXES = ['specs/', 'web/docs/']

router.get('/', async (req: Request, res: Response): Promise<void> => {
  const docPath = String(req.query.path || '')

  if (!docPath) {
    res.status(400).json({ error: 'Missing path parameter' })
    return
  }

  // 安全检查：只允许白名单目录
  const isAllowed = ALLOWED_PREFIXES.some(prefix => docPath.startsWith(prefix))
  if (!isAllowed) {
    res.status(403).json({ error: 'Path not allowed' })
    return
  }

  // 防止路径穿越
  const resolvedPath = path.resolve(LDVH_ROOT, docPath)
  if (!resolvedPath.startsWith(path.resolve(LDVH_ROOT))) {
    res.status(403).json({ error: 'Invalid path' })
    return
  }

  try {
    const content = await readFile(resolvedPath, 'utf-8')
    // 限制返回内容大小（最大 200KB）
    if (content.length > 200 * 1024) {
      res.json({ path: docPath, content: content.slice(0, 200 * 1024), truncated: true })
      return
    }
    res.json({ path: docPath, content, truncated: false })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'File not found'
    res.status(404).json({ error: message })
  }
})

export default router
