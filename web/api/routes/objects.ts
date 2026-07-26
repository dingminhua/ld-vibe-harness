/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, showObject, OBJECT_TYPES, type ObjectType } from '../services/facts.js'
import {
  WORKCASE_PROGRESS_GROUP_ORDER,
  deriveWorkCaseProgressProjection,
  isWorkCaseProgressGroup,
} from '../../shared/workcaseStatus.ts'

const router = Router()

export interface ListedObject {
  id: string
  type: string
  status: string
  title: string
  title_en?: string
  title_zh?: string
  path: string
  created?: string
  updated: string
  [key: string]: unknown
}

interface StatusOption {
  status: string
  count: number
}

interface ProgressOption {
  group: string
  count: number
}

const SPARK_PRIORITY_ORDER = ['P0', 'P1', 'P2', 'P3']

const STATUS_PRIORITY: Record<string, number> = {
  needs_human_gate: 10,
  open: 11,
  limited: 12,
  input_issue: 13,
  capability_gap: 14,
  evidence_gap: 15,
  fact_conflict: 16,
  // A limited status remains a non-terminal display state for implemented object types.
  degraded: 17,
  suspended: 18,
  proposed: 19,
  pending: 20,
  resolved: 21,
  accepted: 22,
  archived: 23,
  discarded: 24,
  rejected: 25,
  deprecated: 26,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function toStringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback
}

function normalizeItem(value: unknown): ListedObject | null {
  if (!isRecord(value)) return null
  const v4Object = typeof value.object_id === 'string' && typeof value.fact_type_key === 'string'
  const id = toStringValue(value.object_id) || toStringValue(value.id)
  if (!id) return null
  const type = toStringValue(value.fact_type_key) || toStringValue(value.type)
  const status = toStringValue(value.status, 'unknown')
  const phase = toStringValue(value.phase)
  const progressProjection = type === 'workcase'
    ? deriveWorkCaseProgressProjection(status, phase || undefined)
    : null

  return {
    ...value,
    id,
    type,
    status,
    progress_group: progressProjection?.progressGroup,
    progress_step: progressProjection?.progressStep,
    title: toStringValue(value.title, id),
    title_en: toStringValue(value.title_en) || undefined,
    title_zh: toStringValue(value.title_zh) || undefined,
    path: v4Object ? toStringValue(value.canonical_path) : toStringValue(value.path),
    created: v4Object ? toStringValue(value.created_at) || undefined : toStringValue(value.created) || undefined,
    updated: v4Object ? toStringValue(value.updated_at) : toStringValue(value.updated),
  }
}

function getResultItems(result: unknown): ListedObject[] {
  if (!isRecord(result) || !isRecord(result.data) || !Array.isArray(result.data.items)) return []
  return result.data.items
    .map(normalizeItem)
    .filter((item): item is ListedObject => Boolean(item))
}

function getRawItems(result: unknown): Array<Record<string, unknown>> {
  if (!isRecord(result) || !isRecord(result.data) || !Array.isArray(result.data.items)) return []
  return result.data.items.filter(isRecord)
}

function countByStatus(items: Array<{ status: string }>): Record<string, number> {
  return items.reduce<Record<string, number>>((counts, item) => {
    counts[item.status] = (counts[item.status] ?? 0) + 1
    return counts
  }, {})
}

function getUpdatedTime(value: string | undefined): number {
  return new Date(value || 0).getTime() || 0
}

function sortByUpdatedDesc<T extends { updated?: string; id: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const timeDelta = getUpdatedTime(b.updated) - getUpdatedTime(a.updated)
    if (timeDelta !== 0) return timeDelta
    const updatedDelta = String(b.updated || '').localeCompare(String(a.updated || ''))
    if (updatedDelta !== 0) return updatedDelta
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

function getPriorityOptions(items: ListedObject[]): StatusOption[] {
  const counts = countByStatus(
    items
      .filter((item) => typeof item.priority === 'string')
      .map((item) => ({ status: item.priority as string })),
  )
  return SPARK_PRIORITY_ORDER.map((status) => ({ status, count: counts[status] ?? 0 }))
}

function getWorkCaseProgressOptions(items: ListedObject[]): ProgressOption[] {
  const counts = new Map<string, number>()
  for (const item of items) {
    if (typeof item.progress_group !== 'string') continue
    counts.set(item.progress_group, (counts.get(item.progress_group) ?? 0) + 1)
  }
  return WORKCASE_PROGRESS_GROUP_ORDER.map((group) => ({ group, count: counts.get(group) ?? 0 }))
}

function matchesSparkListFilter(item: ListedObject, status?: string, priority?: string): boolean {
  return (!status || item.status === status)
    && (!priority || item.priority === priority)
}

async function listObjectSummaries(type: ObjectType, baseDir?: string): Promise<ListedObject[]> {
  const result = await listObjects(type, baseDir)
  if (!result.ok) return []
  return getResultItems(result)
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

  const status = typeof req.query.status === 'string' ? req.query.status : undefined
  const progress = type === 'workcase' && typeof req.query.progress === 'string'
    ? req.query.progress
    : undefined
  if (progress && !isWorkCaseProgressGroup(progress)) {
    res.status(400).json({ ok: false, error: `Invalid WorkCase progress group: ${progress}` })
    return
  }
  const priority = (type === 'spark' || type === 'workcase') && typeof req.query.priority === 'string'
    ? req.query.priority
    : undefined
  const result = await listObjects(type, undefined, type === 'workcase' || type === 'spark' ? undefined : status)

  if (!result.ok) {
    res.status(typeof result.exitCode === 'string' ? 503 : 500).json(result)
    return
  }

  const rawItems = getRawItems(result)
  const allItems = getResultItems(result)
  const items = type === 'workcase'
    ? allItems.filter((item) => (!progress || item.progress_group === progress) && (!priority || item.priority === priority))
    : type === 'spark'
      ? allItems.filter((item) => matchesSparkListFilter(item, status, priority))
      : allItems
  if (isRecord(result.data)) {
    const statusItems = type === 'workcase' || type === 'spark'
      ? allItems
      : status ? await listObjectSummaries(type) : items
    if (type === 'workcase') {
      result.data.progressOptions = getWorkCaseProgressOptions(allItems)
    } else {
      result.data.statusOptions = getStatusOptions(statusItems)
    }
    result.data.statusTotal = statusItems.length
    if (type === 'spark' || type === 'workcase') {
      const groupItems = type === 'workcase' && progress
        ? allItems.filter((item) => item.progress_group === progress)
        : status ? allItems.filter((item) => item.status === status) : allItems
      result.data.priorityOptions = getPriorityOptions(groupItems)
    }
  }
  if (isRecord(result.data)) {
    result.data.items = type === 'spark'
      ? rawItems
        .map(normalizeItem)
        .filter((item): item is ListedObject => Boolean(item))
        .filter((item) => matchesSparkListFilter(item, status, priority))
        .sort((left, right) => String(right.updated || '').localeCompare(String(left.updated || '')))
      : sortByUpdatedDesc(items)
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
    res.status(typeof result.exitCode === 'string' ? 503 : 404).json(result)
    return
  }
  const resultType = isRecord(result.data) && typeof result.data.fact_type_key === 'string'
    ? result.data.fact_type_key
    : isRecord(result.data) && isRecord(result.data.object_ref)
      && typeof result.data.object_ref.fact_type_key === 'string'
      ? result.data.object_ref.fact_type_key
      : undefined
  if (resultType !== undefined && resultType !== type) {
    res.status(404).json({
      ok: false,
      error: `Object not found for type ${type}: ${id}`,
      stderr: '',
      exitCode: 1,
    })
    return
  }

  res.json(result)
})

export default router
