/** V4-only, loopback-only Spark direct-capture endpoint. */

import { Router, type Request, type Response } from 'express'

import { captureV4Spark } from '../services/v4SparkReader.js'
import { v4SparkReaderConfig, V4FactsConfigurationError } from '../services/v4FactsConfig.js'

const router = Router()

function isLoopback(request: Request): boolean {
  const address = request.socket.remoteAddress ?? ''
  return address === '127.0.0.1' || address === '::1' || address === '::ffff:127.0.0.1'
}

function statusCode(status: unknown): number {
  if (status === 'created') return 201
  if (status === 'exact_duplicate' || status === 'integrity_conflict') return 409
  if (status === 'invalid') return 400
  if (status === 'unavailable') return 503
  return 500
}

router.post('/', async (req: Request, res: Response): Promise<void> => {
  if (!isLoopback(req)) {
    res.status(403).json({ ok: false, code: 'LOOPBACK_REQUIRED', error: 'V4 Spark capture is available only on loopback' })
    return
  }
  try {
    const response = await captureV4Spark(v4SparkReaderConfig(), req.body)
    const payload = response.result
    if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
      res.status(503).json({ ok: false, code: 'V4_MACHINE_UNAVAILABLE', error: response.error ?? 'V4 Spark machine unavailable' })
      return
    }
    const result = payload as Record<string, unknown>
    const status = result.status
    const success = status === 'created'
    res.status(statusCode(status)).json({
      ok: success,
      action: success ? 'create' : undefined,
      target: result.canonical_path,
      summary: success ? { id: (result.actual_ref as Record<string, unknown> | null)?.object_id, type: 'spark', status: 'open' } : undefined,
      data: success ? result.fact_object : undefined,
      code: result.code,
      error: success ? undefined : result.summary,
      details: result.details,
      governance_resolution: result.governance_resolution,
    })
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : 'V4 Spark capture unavailable'
    const code = caught instanceof V4FactsConfigurationError ? 'V4_WEB_CONFIGURATION_REQUIRED' : 'V4_MACHINE_UNAVAILABLE'
    res.status(503).json({ ok: false, code, error: message })
  }
})

export default router
