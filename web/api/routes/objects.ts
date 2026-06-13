/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'
import { listObjects, showObject, OBJECT_TYPES, LDVH_BASE_DIR, readFactData, type ObjectType } from '../services/facts.js'

const router = Router()

export interface ListedObject {
  id: string
  type: string
  status: string
  title: string
  title_en?: string
  title_zh?: string
  path: string
  updated: string
  [key: string]: unknown
}

interface RelatedObjectSummary {
  id: string
  type: string
  status: string
  title: string
  title_en?: string
  title_zh?: string
  path: string
  updated: string
  blockedBy?: string[]
  openBlockers?: RelatedObjectSummary[]
  subtasks?: RelatedObjectSummary[]
}

interface RelatedPlanSummary extends RelatedObjectSummary {
  workarea?: string
  taskTotal: number
  taskClosed: number
  taskReviewNeeded: number
  taskActive: number
  taskBlocked: number
  taskRisk: number
  tasks: RelatedObjectSummary[]
  hasSuccessCriteria: boolean
  hasReviewRequestedAt: boolean
  hasCompletionEvidence: boolean
  hasClosedAt: boolean
}

interface StatusOption {
  status: string
  count: number
}

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'superseded'])
const REVIEW_STATUSES = new Set(['review_needed', 'needs_human_gate', 'proposed'])
const ACTIVE_STATUSES = new Set(['active', 'executing', 'verifying'])
const RISK_STATUSES = new Set(['open', 'degraded', 'suspended', 'rejected', 'deprecated'])

const STATUS_PRIORITY: Record<string, number> = {
  review_needed: 0,
  needs_human_gate: 1,
  executing: 2,
  verifying: 3,
  active: 4,
  open: 5,
  degraded: 6,
  suspended: 7,
  proposed: 8,
  planned: 9,
  draft: 10,
  closed: 20,
  resolved: 21,
  accepted: 22,
  archived: 23,
  superseded: 24,
  rejected: 25,
  deprecated: 26,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function toStringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function toStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
}

function addStringArray(target: Set<string>, value: unknown): void {
  toStringArray(value).forEach((item) => target.add(item))
}

function hasContent(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'string') return value.trim().length > 0
  return value !== null && value !== undefined
}

function normalizeItem(value: unknown): ListedObject | null {
  if (!isRecord(value)) return null
  const id = toStringValue(value.id)
  if (!id) return null

  return {
    ...value,
    id,
    type: toStringValue(value.type),
    status: toStringValue(value.status, 'unknown'),
    title: toStringValue(value.title, id),
    title_en: toStringValue(value.title_en) || undefined,
    title_zh: toStringValue(value.title_zh) || undefined,
    path: toStringValue(value.path),
    updated: toStringValue(value.updated),
  }
}

function getResultItems(result: unknown): ListedObject[] {
  if (!isRecord(result) || !isRecord(result.data) || !Array.isArray(result.data.items)) return []
  return result.data.items
    .map(normalizeItem)
    .filter((item): item is ListedObject => Boolean(item))
}

function toRelatedSummary(item: ListedObject, type = item.type): RelatedObjectSummary {
  return {
    id: item.id,
    type,
    status: item.status,
    title: item.title,
    title_en: item.title_en,
    title_zh: item.title_zh,
    path: item.path,
    updated: item.updated,
  }
}

function toBlockedSummary(item: ListedObject, type: 'task' | 'subtask'): RelatedObjectSummary {
  const data = readFactData(item.path)
  const blockedBy = toStringArray(data.blocked_by)
  return {
    ...toRelatedSummary(item, type),
    ...(blockedBy.length > 0 ? { blockedBy } : {}),
  }
}

function toTaskSummary(item: ListedObject): RelatedObjectSummary {
  return toBlockedSummary(item, 'task')
}

function toSubtaskSummary(item: ListedObject): RelatedObjectSummary {
  return toBlockedSummary(item, 'subtask')
}

function toMissingRelatedSummary(id: string, type: 'task' | 'subtask'): RelatedObjectSummary {
  return {
    id,
    type,
    status: 'unknown',
    title: id,
    path: '',
    updated: '',
  }
}

function stripDerivedSummary(item: RelatedObjectSummary): RelatedObjectSummary {
  return {
    id: item.id,
    type: item.type,
    status: item.status,
    title: item.title,
    title_en: item.title_en,
    title_zh: item.title_zh,
    path: item.path,
    updated: item.updated,
    blockedBy: item.blockedBy,
  }
}

function hasOpenBlockers(item: RelatedObjectSummary): boolean {
  return !TERMINAL_STATUSES.has(item.status) && (item.openBlockers?.length ?? 0) > 0
}

function enrichBlockers(items: RelatedObjectSummary[], type: 'task' | 'subtask'): RelatedObjectSummary[] {
  const itemsById = new Map(items.map((item) => [item.id, item]))

  return items.map((item) => {
    const openBlockers = (item.blockedBy ?? [])
      .map((blockerId) => itemsById.get(blockerId) ?? toMissingRelatedSummary(blockerId, type))
      .filter((blocker) => !TERMINAL_STATUSES.has(blocker.status))
      .map(stripDerivedSummary)

    return openBlockers.length > 0 ? { ...item, openBlockers } : item
  })
}

function countByStatus(items: Array<{ status: string }>): Record<string, number> {
  return items.reduce<Record<string, number>>((counts, item) => {
    counts[item.status] = (counts[item.status] ?? 0) + 1
    return counts
  }, {})
}

function countMatching(items: Array<{ status: string }>, statuses: Set<string>): number {
  return items.filter((item) => statuses.has(item.status)).length
}

function sortRelatedObjects<T extends { status: string; updated: string; id: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const statusDelta = (STATUS_PRIORITY[a.status] ?? 50) - (STATUS_PRIORITY[b.status] ?? 50)
    if (statusDelta !== 0) return statusDelta
    const aTime = new Date(a.updated || 0).getTime() || 0
    const bTime = new Date(b.updated || 0).getTime() || 0
    const timeDelta = bTime - aTime
    if (timeDelta !== 0) return timeDelta
    return a.id.localeCompare(b.id)
  })
}

function getStatusOptions(items: ListedObject[]): StatusOption[] {
  return Object.entries(countByStatus(items))
    .map(([status, count]) => ({ status, count }))
    .sort((a, b) => {
      const statusDelta = (STATUS_PRIORITY[a.status] ?? 50) - (STATUS_PRIORITY[b.status] ?? 50)
      if (statusDelta !== 0) return statusDelta
      if (a.count !== b.count) return b.count - a.count
      return a.status.localeCompare(b.status)
    })
}

async function listObjectSummaries(type: ObjectType, baseDir?: string): Promise<ListedObject[]> {
  const result = await listObjects(type, baseDir)
  if (!result.ok) return []
  return getResultItems(result)
}

export async function buildPlanSummaries(planItems: ListedObject[], baseDir?: string): Promise<RelatedPlanSummary[]> {
  if (planItems.length === 0) return []

  const [taskItems, subtaskItems] = await Promise.all([
    listObjectSummaries('task', baseDir),
    listObjectSummaries('subtask', baseDir),
  ])
  const tasksById = new Map(taskItems.map((item) => [item.id, item]))
  const subtasksByTask = new Map<string, RelatedObjectSummary[]>()

  for (const subtaskItem of subtaskItems) {
    const data = readFactData(subtaskItem.path)
    const taskId = toStringValue(data.task)
    if (!taskId) continue
    const current = subtasksByTask.get(taskId) ?? []
    current.push(toSubtaskSummary(subtaskItem))
    subtasksByTask.set(taskId, current)
  }

  return planItems.map((item) => {
    const data = readFactData(item.path)
    const taskIds = toStringArray(data.tasks)
    const tasks = enrichBlockers(taskIds.map((taskId) => {
      const taskItem = tasksById.get(taskId)
      if (!taskItem) return toMissingRelatedSummary(taskId, 'task')

      const subtasks = sortRelatedObjects(enrichBlockers(subtasksByTask.get(taskId) ?? [], 'subtask'))
      return {
        ...toTaskSummary(taskItem),
        ...(subtasks.length > 0 ? { subtasks } : {}),
      }
    }), 'task')

    return {
      ...toRelatedSummary(item, 'taskplan'),
      workarea: toStringValue(data.workarea) || undefined,
      taskTotal: tasks.length,
      taskClosed: countMatching(tasks, TERMINAL_STATUSES),
      taskReviewNeeded: countMatching(tasks, REVIEW_STATUSES),
      taskActive: countMatching(tasks, ACTIVE_STATUSES),
      taskBlocked: tasks.filter(hasOpenBlockers).length,
      taskRisk: countMatching(tasks, RISK_STATUSES),
      tasks: sortRelatedObjects(tasks),
      hasSuccessCriteria: hasContent(data.success_criteria),
      hasReviewRequestedAt: hasContent(data.review_requested_at),
      hasCompletionEvidence: hasContent(data.completion_evidence),
      hasClosedAt: hasContent(data.closed_at),
    }
  })
}

async function enrichWorkareas(items: ListedObject[]): Promise<ListedObject[]> {
  const allPlanItems = await listObjectSummaries('taskplan')
  const plans = await buildPlanSummaries(allPlanItems)
  const plansByWorkarea = new Map<string, RelatedPlanSummary[]>()

  for (const plan of plans) {
    if (!plan.workarea) continue
    const current = plansByWorkarea.get(plan.workarea) ?? []
    current.push(plan)
    plansByWorkarea.set(plan.workarea, current)
  }

  return items.map((item) => {
    const relatedPlans = sortRelatedObjects(plansByWorkarea.get(item.id) ?? [])
    return {
      ...item,
      plans: relatedPlans,
      planTotal: relatedPlans.length,
      planClosed: countMatching(relatedPlans, TERMINAL_STATUSES),
      planReviewNeeded: countMatching(relatedPlans, REVIEW_STATUSES),
      planActive: countMatching(relatedPlans, ACTIVE_STATUSES),
      planRisk: countMatching(relatedPlans, RISK_STATUSES),
      planByStatus: countByStatus(relatedPlans),
    }
  })
}

async function enrichTaskPlans(items: ListedObject[]): Promise<ListedObject[]> {
  const planSummaries = await buildPlanSummaries(items)
  const summariesById = new Map(planSummaries.map((plan) => [plan.id, plan]))
  const workareaItems = await listObjectSummaries('workarea')
  const workareasById = new Map(workareaItems.map((item) => [item.id, item]))

  return items.map((item) => {
    const summary = summariesById.get(item.id)
    if (!summary) return item
    const workarea = summary.workarea ? workareasById.get(summary.workarea) : undefined
    return {
      ...item,
      workarea: summary.workarea,
      workareaSummary: workarea ? toRelatedSummary(workarea, 'workarea') : undefined,
      tasks: summary.tasks,
      taskTotal: summary.taskTotal,
      taskClosed: summary.taskClosed,
      taskReviewNeeded: summary.taskReviewNeeded,
      taskActive: summary.taskActive,
      taskBlocked: summary.taskBlocked,
      taskRisk: summary.taskRisk,
      hasSuccessCriteria: summary.hasSuccessCriteria,
      hasReviewRequestedAt: summary.hasReviewRequestedAt,
      hasCompletionEvidence: summary.hasCompletionEvidence,
      hasClosedAt: summary.hasClosedAt,
      taskByStatus: countByStatus(summary.tasks),
    }
  })
}

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

  const items = getResultItems(result)
  if (isRecord(result.data)) {
    const statusItems = status ? await listObjectSummaries(type) : items
    result.data.statusOptions = getStatusOptions(statusItems)
    result.data.statusTotal = statusItems.length
  }
  if (isRecord(result.data) && type === 'workarea') {
    result.data.items = await enrichWorkareas(items)
  }
  if (isRecord(result.data) && type === 'taskplan') {
    result.data.items = await enrichTaskPlans(items)
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

  // TaskPlan 派生阅读材料：计划自身优先，再合并计划内 Task 的关联材料并去重。
  if (type === 'taskplan' && result.data) {
    const tasks: string[] = (result.data.tasks as string[]) || []
    const relatedDocsSet = new Set<string>()
    const relatedAdrsSet = new Set<string>()
    const relatedMemosSet = new Set<string>()
    const relatedPitfallsSet = new Set<string>()
    const relatedChangesSet = new Set<string>()

    addStringArray(relatedDocsSet, result.data.related_docs)
    addStringArray(relatedAdrsSet, result.data.related_adrs)
    addStringArray(relatedMemosSet, result.data.related_memos)
    addStringArray(relatedPitfallsSet, result.data.related_pitfalls)
    addStringArray(relatedChangesSet, result.data.related_changes)

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
          addStringArray(relatedDocsSet, taskObj.related_docs)
          addStringArray(relatedAdrsSet, taskObj.related_adrs)
          addStringArray(relatedMemosSet, taskObj.related_memos)
          addStringArray(relatedPitfallsSet, taskObj.related_pitfalls)
          addStringArray(relatedChangesSet, taskObj.related_changes)
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
    result.data.aggregated_related_docs = [...relatedDocsSet]
    result.data.aggregated_related_adrs = [...relatedAdrsSet]
    result.data.aggregated_related_memos = [...relatedMemosSet]
    result.data.aggregated_related_pitfalls = [...relatedPitfallsSet]
    result.data.aggregated_related_changes = [...relatedChangesSet]
  }

  res.json(result)
})

export default router
