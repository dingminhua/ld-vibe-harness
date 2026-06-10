/**
 * Validate API 路由：调用 Code 工具返回 Web Validate 只读数据合同
 */

import { Router, type Request, type Response } from 'express'
import { runPyToolsJson, type PyToolsError } from '../services/pytools.js'

const router = Router()

function isToolError(result: unknown): result is PyToolsError {
  return typeof result === 'object' && result !== null && 'error' in result && 'stderr' in result && 'exitCode' in result
}

router.get('/', async (_req: Request, res: Response): Promise<void> => {
  const result = await runPyToolsJson('specs_validate.py', ['web-validate', '--format', 'json'])

  if (isToolError(result)) {
    res.status(500).json(result)
    return
  }

  res.json(result)
})

export default router
