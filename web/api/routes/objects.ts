/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { listObjects, showObject, OBJECT_TYPES, LDVH_BASE_DIR, type ObjectType } from '../services/pytools.js'

const router = Router()

/** 允许通过 PATCH 更新的字段白名单 */
const FIELD_UPDATE_WHITELIST: Record<string, string[]> = {
  task: ['source_intent'],
}

/**
 * PATCH /api/objects/:type/:id/field - 更新对象的指定字段
 */
router.patch('/:type/:id/field', async (req: Request, res: Response): Promise<void> => {
  const objType = req.params.type as ObjectType
  const objId = req.params.id
  const { field, value } = req.body

  // 校验对象类型
  if (!OBJECT_TYPES.includes(objType)) {
    res.status(400).json({ ok: false, error: `Invalid object type: ${objType}` })
    return
  }

  // 校验字段白名单
  const allowedFields = FIELD_UPDATE_WHITELIST[objType] || []
  if (!allowedFields.includes(field)) {
    res.status(400).json({ ok: false, error: `Field "${field}" is not allowed for type "${objType}"` })
    return
  }

  // 校验 value 非空
  if (value === null || value === undefined || value === '') {
    res.status(400).json({ ok: false, error: 'Value must not be empty' })
    return
  }

  // 查找对象 YAML 文件
  const typeDir = path.join(LDVH_BASE_DIR, `${objType}s`)
  if (!fs.existsSync(typeDir)) {
    res.status(404).json({ ok: false, error: `Type directory not found: ${objType}` })
    return
  }

  const files = fs.readdirSync(typeDir).filter(f => f.startsWith(`${objId}-`) && f.endsWith('.yaml'))
  if (files.length === 0) {
    res.status(404).json({ ok: false, error: `Object not found: ${objId}` })
    return
  }

  const filePath = path.join(typeDir, files[0])
  const fileContent = fs.readFileSync(filePath, 'utf-8')
  const obj = yaml.load(fileContent) as Record<string, unknown>

  // source_intent 字段特殊处理：校验目标 Intent 存在性 + 双向关联同步
  if (field === 'source_intent') {
    const newIntentId = value as string

    // 校验目标 Intent 存在
    const intentDir = path.join(LDVH_BASE_DIR, 'intents')
    const intentFiles = fs.readdirSync(intentDir).filter(f => f.startsWith(`${newIntentId}-`) && f.endsWith('.yaml'))
    if (intentFiles.length === 0) {
      res.status(400).json({ ok: false, error: `Target intent not found: ${newIntentId}` })
      return
    }

    const oldIntentId = obj.source_intent as string | undefined

    // 读取新 Intent，添加 Task 到 related_tasks
    const newIntentPath = path.join(intentDir, intentFiles[0])
    const newIntentContent = fs.readFileSync(newIntentPath, 'utf-8')
    const newIntent = yaml.load(newIntentContent) as Record<string, unknown>
    const newRelatedTasks: string[] = (newIntent.related_tasks as string[]) || []
    if (!newRelatedTasks.includes(objId)) {
      newRelatedTasks.push(objId)
      newIntent.related_tasks = newRelatedTasks
      newIntent.updated = new Date().toISOString()
      fs.writeFileSync(newIntentPath, yaml.dump(newIntent, { lineWidth: -1, quotingType: '"', forceQuotes: false }), 'utf-8')
    }

    // 如果原 Intent 存在且不同于新 Intent，从原 Intent 的 related_tasks 移除该 Task
    if (oldIntentId && oldIntentId !== newIntentId) {
      const oldIntentFiles = fs.readdirSync(intentDir).filter(f => f.startsWith(`${oldIntentId}-`) && f.endsWith('.yaml'))
      if (oldIntentFiles.length > 0) {
        const oldIntentPath = path.join(intentDir, oldIntentFiles[0])
        const oldIntentContent = fs.readFileSync(oldIntentPath, 'utf-8')
        const oldIntent = yaml.load(oldIntentContent) as Record<string, unknown>
        const oldRelatedTasks: string[] = (oldIntent.related_tasks as string[]) || []
        oldIntent.related_tasks = oldRelatedTasks.filter(t => t !== objId)
        oldIntent.updated = new Date().toISOString()
        fs.writeFileSync(oldIntentPath, yaml.dump(oldIntent, { lineWidth: -1, quotingType: '"', forceQuotes: false }), 'utf-8')
      }
    }
  }

  // 更新对象字段
  obj[field] = value
  obj.updated = new Date().toISOString()

  // 写回 YAML 文件
  fs.writeFileSync(filePath, yaml.dump(obj, { lineWidth: -1, quotingType: '"', forceQuotes: false }), 'utf-8')

  // 返回更新后的对象
  const result = await showObject(objId)
  res.json(result)
})

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

  // Intent 聚合：合并关联 Task 的 deliverables 和 related_docs
  if (type === 'intent' && result.data) {
    const relatedTasks: string[] = (result.data.related_tasks as string[]) || []
    if (relatedTasks.length > 0) {
      const taskDir = path.join(LDVH_BASE_DIR, 'tasks')
      const deliverablesSet = new Set<string>()
      const docsSet = new Set<string>()

      for (const taskId of relatedTasks) {
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
