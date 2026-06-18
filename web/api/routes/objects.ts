/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, showObject, OBJECT_TYPES, readFactData, type ObjectType } from '../services/facts.js'

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

interface RelatedObjectSummary {
  id: string
  type: string
  status: string
  title: string
  title_en?: string
  title_zh?: string
  path: string
  updated: string
  priority?: string
  role?: string
  mode?: string
  expectedOutput?: string
  resultSummary?: string
  blockingReason?: string
  inputRefs?: string[]
  evidenceRefs?: string[]
}

interface RelatedPlanSummary extends RelatedObjectSummary {
  workarea?: string
  executionItems?: RelatedObjectSummary[]
  executionItemTotal?: number
  executionItemDone?: number
  executionItemBlocked?: number
  executionItemOpen?: number
  hasSuccessCriteria: boolean
  hasReviewRequestedAt: boolean
  hasVerificationEvidence?: boolean
  hasClosureEvidence?: boolean
  hasClosedAt: boolean
}

interface StatusOption {
  status: string
  count: number
}

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'discarded', 'superseded'])
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
  pending: 10,
  draft: 10,
  closed: 20,
  resolved: 21,
  accepted: 22,
  archived: 23,
  discarded: 24,
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
    priority: typeof item.priority === 'string' ? item.priority : undefined,
  }
}

function toExecutionItemSummary(value: unknown, plan: ListedObject, index: number): RelatedObjectSummary | null {
  if (!isRecord(value)) return null
  const id = toStringValue(value.id) || `execution-item-${index + 1}`
  const status = toStringValue(value.status, 'unknown')
  const title = toStringValue(value.title, id)

  return {
    id,
    type: 'execution_item',
    status,
    title,
    path: plan.path,
    updated: plan.updated,
    role: toStringValue(value.role) || undefined,
    mode: toStringValue(value.mode) || undefined,
    expectedOutput: toStringValue(value.expected_output) || undefined,
    resultSummary: toStringValue(value.result_summary) || undefined,
    blockingReason: toStringValue(value.blocking_reason) || undefined,
    inputRefs: toStringArray(value.input_refs),
    evidenceRefs: toStringArray(value.evidence_refs),
  }
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

function countOpenExecutionItems(items: Array<{ status: string }>): number {
  return items.filter((item) => item.status === 'pending' || item.status === 'in_progress' || item.status === 'blocked').length
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

  return planItems.map((item) => {
    const data = readFactData(item.path)
    const orchestration = isRecord(data.orchestration) ? data.orchestration : {}
    const executionItems = Array.isArray(orchestration.execution_items)
      ? orchestration.execution_items
        .map((executionItem, index) => toExecutionItemSummary(executionItem, item, index))
        .filter((executionItem): executionItem is RelatedObjectSummary => Boolean(executionItem))
      : []

    return {
      ...toRelatedSummary(item, 'workplan'),
      workarea: toStringValue(data.workarea) || undefined,
      executionItems: sortRelatedObjects(executionItems),
      executionItemTotal: executionItems.length,
      executionItemDone: executionItems.filter((executionItem) => executionItem.status === 'done').length,
      executionItemBlocked: executionItems.filter((executionItem) => executionItem.status === 'blocked').length,
      executionItemOpen: countOpenExecutionItems(executionItems),
      hasSuccessCriteria: hasContent(data.success_criteria),
      hasReviewRequestedAt: hasContent(data.review_requested_at),
      hasVerificationEvidence: hasContent(data.verification_evidence),
      hasClosureEvidence: hasContent(data.closure_evidence),
      hasClosedAt: hasContent(data.closed_at),
    }
  })
}

async function enrichWorkareas(items: ListedObject[]): Promise<ListedObject[]> {
  const workPlanItems = await listObjectSummaries('workplan')
  const plans = await buildPlanSummaries(workPlanItems)
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

async function enrichWorkPlans(items: ListedObject[]): Promise<ListedObject[]> {
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
      executionItems: summary.executionItems ?? [],
      executionItemTotal: summary.executionItemTotal ?? 0,
      executionItemDone: summary.executionItemDone ?? 0,
      executionItemBlocked: summary.executionItemBlocked ?? 0,
      executionItemOpen: summary.executionItemOpen ?? 0,
      hasSuccessCriteria: summary.hasSuccessCriteria,
      hasReviewRequestedAt: summary.hasReviewRequestedAt,
      hasVerificationEvidence: summary.hasVerificationEvidence,
      hasClosureEvidence: summary.hasClosureEvidence,
      hasClosedAt: summary.hasClosedAt,
      executionItemByStatus: countByStatus(summary.executionItems ?? []),
    }
  })
}

async function enrichMemos(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = readFactData(item.path)
    return {
      ...item,
      source: toStringValue(data.source) || undefined,
      description: toStringValue(data.description) || undefined,
    }
  })
}

async function enrichPitfalls(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = readFactData(item.path)
    return {
      ...item,
      resolution: toStringValue(data.resolution) || undefined,
      source_memos: toStringArray(data.source_memos),
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
  if (isRecord(result.data) && type === 'workplan') {
    result.data.items = await enrichWorkPlans(items)
  }
  if (isRecord(result.data) && type === 'adr') {
    result.data.items = await enrichAdrs(items)
  }
  if (isRecord(result.data) && type === 'memo') {
    result.data.items = await enrichMemos(items)
  }
  if (isRecord(result.data) && type === 'pitfall') {
    result.data.items = await enrichPitfalls(items)
  }

  res.json(result)
})

/**
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
  if (isRecord(result.data) && result.data.type !== type) {
    res.status(404).json({
      ok: false,
      error: `Object not found for type ${type}: ${id}`,
      stderr: '',
      exitCode: 1,
    })
    return
  }

  // WorkPlan 派生阅读材料：计划自身材料 + execution_items 的输入和证据引用。
  if (type === 'workplan' && result.data) {
    const relatedDocsSet = new Set<string>()
    const relatedAdrsSet = new Set<string>()
    const relatedMemosSet = new Set<string>()
    const relatedPitfallsSet = new Set<string>()
    const relatedChangesSet = new Set<string>()
    const executionRefsSet = new Set<string>()
    const orchestration = isRecord(result.data.orchestration) ? result.data.orchestration : {}
    const executionItems = Array.isArray(orchestration.execution_items) ? orchestration.execution_items : []

    addStringArray(relatedDocsSet, result.data.related_docs)
    addStringArray(relatedAdrsSet, result.data.related_adrs)
    addStringArray(relatedMemosSet, result.data.related_memos)
    addStringArray(relatedPitfallsSet, result.data.related_pitfalls)
    addStringArray(relatedChangesSet, result.data.related_changes)

    for (const executionItem of executionItems) {
      if (!isRecord(executionItem)) continue
      addStringArray(executionRefsSet, executionItem.input_refs)
      addStringArray(executionRefsSet, executionItem.evidence_refs)
    }

    result.data.aggregated_related_docs = [...relatedDocsSet]
    result.data.aggregated_related_adrs = [...relatedAdrsSet]
    result.data.aggregated_related_memos = [...relatedMemosSet]
    result.data.aggregated_related_pitfalls = [...relatedPitfallsSet]
    result.data.aggregated_related_changes = [...relatedChangesSet]
    result.data.aggregated_execution_refs = [...executionRefsSet]
  }

  res.json(result)
})

export default router
async function enrichAdrs(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = readFactData(item.path)
    return {
      ...item,
      date: toStringValue(data.date) || undefined,
      decision: toStringValue(data.decision) || undefined,
      consequences: toStringValue(data.consequences) || undefined,
      affects: toStringArray(data.affects),
      related_rules: toStringArray(data.related_rules),
      superseded_by: toStringValue(data.superseded_by) || undefined,
      alternatives: toStringValue(data.alternatives) || undefined,
      status: toStringValue(data.status) || item.status,
    }
  })
}
