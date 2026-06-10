/**
 * Landing Plan API 路由：返回 landing-plan 只读聚合计划供 Web 展示
 */

import { Router, type Request, type Response } from 'express'
import { runPyToolsJson, type PyToolsError } from '../services/pytools.js'

const router = Router()

function isToolError(result: unknown): result is PyToolsError {
  return typeof result === 'object' && result !== null && 'error' in result && 'stderr' in result && 'exitCode' in result
}

router.get('/', async (_req: Request, res: Response): Promise<void> => {
  const result = await runPyToolsJson('specs_validate.py', ['landing-plan', '--format', 'json'])

  if (isToolError(result)) {
    res.status(500).json(result)
    return
  }

  res.json(result)
})

export default router
