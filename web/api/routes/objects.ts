/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { listObjects, showObject, OBJECT_TYPES, LDVH_BASE_DIR, type ObjectType } from '../services/pytools.js'

const router = Router()

/**
 * GET /api/objects/:type - 列出指定类型的对象
 */
router.get('/:type', async (req: Request, res: Response): Promise<void> => {
  const type = req.params.type as ObjectType

  if (!OBJECT_TYPES.includes(type)) {
    res.status(400).json({
      ok: false,
      error: `Invalid object type: ${type}. Valid types: ${OBJECT_TYPES.join(', ')}`,
    })
    return
  }

  const status = req.query.status as string | undefined
  const result = await listObjects(type, undefined, status)

  if (!result.ok) {
    res.status(500).json(result)
    return
  }

  res.json(result)
})

/**
 * GET /api/objects/:type/:id - 查看对象详情
 */
router.get('/:type/:id', async (req: Request, res: Response): Promise<void> => {
  const type = req.params.type as ObjectType
  const id = req.params.id

  if (!OBJECT_TYPES.includes(type)) {
    res.status(400).json({
      ok: false,
      error: `Invalid object type: ${type}. Valid types: ${OBJECT_TYPES.join(', ')}`,
    })
    return
  }

  const result = await showObject(id)

  if (!result.ok) {
    res.status(404).json(result)
    return
  }

  // TaskPlan 聚合：合并计划内 Task 的 deliverables 和 related_docs
  if (type === 'taskplan' && result.data) {
    const tasks: string[] = (result.data.tasks as string[]) || []
    if (tasks.length > 0) {
      const taskDir = path.join(LDVH_BASE_DIR, 'tasks')
      const deliverablesSet = new Set<string>()
      const docsSet = new Set<string>()

      for (const taskId of tasks) {
        try {
          if (!fs.existsSync(taskDir)) continue
          const taskFiles = fs.readdirSync(taskDir).filter(f => f.startsWith(`${taskId}-`) && f.endsWith('.yaml'))
          if (taskFiles.length === 0) continue
          const taskContent = fs.readFileSync(path.join(taskDir, taskFiles[0]), 'utf-8')
          const taskObj = yaml.load(taskContent) as Record<string, unknown>
          const taskDeliverables = (taskObj.deliverables as string[]) || []
          const taskDocs = (taskObj.related_docs as string[]) || []
          taskDeliverables.forEach(d => deliverablesSet.add(d))
          taskDocs.forEach(d => docsSet.add(d))
        } catch {
          // 单个 task 读取失败不影响整体聚合
        }
      }

      result.data.aggregated_deliverables = [...deliverablesSet]
      result.data.aggregated_docs = [...docsSet]
    } else {
      result.data.aggregated_deliverables = []
      result.data.aggregated_docs = []
    }
  }

  res.json(result)
})

export default router
