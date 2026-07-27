import { Router, type Request, type Response } from 'express'
import { readGovernedProjectsSettings, updateGovernedProjectsSettings, type GovernedProjectSetting } from '../services/governedProjectsSettings.js'

const router = Router()

router.get('/governed-projects', async (_req: Request, res: Response): Promise<void> => {
  try { res.json({ ok: true, ...(await readGovernedProjectsSettings()) }) }
  catch (error) { res.status(422).json({ ok: false, error: error instanceof Error ? error.message : String(error) }) }
})

router.put('/governed-projects', async (req: Request, res: Response): Promise<void> => {
  const body = req.body as { projects?: GovernedProjectSetting[]; expectedFingerprint?: string }
  if (!Array.isArray(body.projects) || typeof body.expectedFingerprint !== 'string') {
    res.status(400).json({ ok: false, error: 'projects 与 expectedFingerprint 是必填字段' })
    return
  }
  try { res.json({ ok: true, ...(await updateGovernedProjectsSettings(body.projects, body.expectedFingerprint)) }) }
  catch (error) { res.status(422).json({ ok: false, error: error instanceof Error ? error.message : String(error) }) }
})

export default router
