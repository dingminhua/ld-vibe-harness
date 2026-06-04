/**
 * Validate API 路由：返回 ldvh-base 校验结果
 */

import { Router, type Request, type Response } from 'express'
import { validate } from '../services/pytools.js'

const router = Router()

router.get('/', async (_req: Request, res: Response): Promise<void> => {
  const result = await validate()

  if (!result.ok) {
    res.status(500).json(result)
    return
  }

  res.json(result)
})

export default router
