/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, showObject, OBJECT_TYPES, readFactData, type ObjectType } from '../services/facts.js'
import { WORKCASE_STATUS_ORDER } from '../../src/utils/workcaseStatus.ts'

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

interface RelatedWorkCaseSummary extends RelatedObjectSummary {
  executionItems?: RelatedObjectSummary[]
  executionItemTotal?: number
  executionItemDone?: number
  executionItemBlocked?: number
  executionItemOpen?: number
  successCriteriaTotal?: number
  successCriteriaDone?: number
  hasSuccessCriteria: boolean
  hasPlanConfirmedAt: boolean
  hasClosureRequestedAt: boolean
  hasVerificationEvidence?: boolean
  hasClosureEvidence?: boolean
  hasClosedAt: boolean
}

interface StatusOption {
  status: string
  count: number
}

const STATUS_PRIORITY: Record<string, number> = {
  ...Object.fromEntries(WORKCASE_STATUS_ORDER.map((status, index) => [status, index])),
  needs_human_gate: 10,
  verifying: 11,
  open: 12,
  limited: 13,
  input_issue: 14,
  capability_gap: 15,
  evidence_gap: 16,
  fact_conflict: 17,
  // Legacy backend status; Human-facing labels render this as a limited/risk state.
  degraded: 18,
  suspended: 19,
  proposed: 20,
  planned: 21,
  pending: 22,
  resolved: 23,
  accepted: 24,
  archived: 25,
  discarded: 26,
  superseded: 26,
  rejected: 27,
  deprecated: 28,
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

function toExecutionItemSummary(value: unknown, workcase: ListedObject, index: number): RelatedObjectSummary | null {
  if (!isRecord(value)) return null
  const id = toStringValue(value.id) || `execution-item-${index + 1}`
  const status = toStringValue(value.status, 'unknown')
  const title = toStringValue(value.title, id)

  return {
    id,
    type: 'execution_item',
    status,
    title,
    path: workcase.path,
    updated: workcase.updated,
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

function getChecklistProgress(value: unknown): { total: number; done: number } {
  if (typeof value !== 'string') return { total: 0, done: 0 }
  return value.split(/\r?\n/).reduce(
    (progress, line) => {
      const match = line.match(/^\s*[-*]\s+\[([ xX])\]\s+/)
      if (!match) return progress
      progress.total += 1
      if (match[1].toLowerCase() === 'x') progress.done += 1
      return progress
    },
    { total: 0, done: 0 },
  )
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

function sortExecutionItems<T extends { status: string; updated: string; id: string }>(items: T[]): T[] {
  return [...items].sort((a, b) => {
    const statusDelta = (STATUS_PRIORITY[a.status] ?? 50) - (STATUS_PRIORITY[b.status] ?? 50)
    if (statusDelta !== 0) return statusDelta
    const timeDelta = getUpdatedTime(b.updated) - getUpdatedTime(a.updated)
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

export async function buildWorkCaseSummaries(workcaseItems: ListedObject[]): Promise<RelatedWorkCaseSummary[]> {
  if (workcaseItems.length === 0) return []

  return workcaseItems.map((item) => {
    const data = readFactData(item.path)
    const orchestration = isRecord(data.orchestration) ? data.orchestration : {}
    const executionItems = Array.isArray(orchestration.execution_items)
      ? orchestration.execution_items
        .map((executionItem, index) => toExecutionItemSummary(executionItem, item, index))
        .filter((executionItem): executionItem is RelatedObjectSummary => Boolean(executionItem))
      : []
    const successCriteriaProgress = getChecklistProgress(data.success_criteria)

    return {
      ...toRelatedSummary(item, 'workcase'),
      executionItems: sortExecutionItems(executionItems),
      executionItemTotal: executionItems.length,
      executionItemDone: executionItems.filter((executionItem) => executionItem.status === 'done').length,
      executionItemBlocked: executionItems.filter((executionItem) => executionItem.status === 'blocked').length,
      executionItemOpen: countOpenExecutionItems(executionItems),
      successCriteriaTotal: successCriteriaProgress.total,
      successCriteriaDone: successCriteriaProgress.done,
      hasSuccessCriteria: hasContent(data.success_criteria),
      hasPlanConfirmedAt: hasContent(data.plan_confirmed_at),
      hasClosureRequestedAt: hasContent(data.closure_requested_at) || hasContent(data.review_requested_at),
      hasVerificationEvidence: hasContent(data.verification_evidence),
      hasClosureEvidence: hasContent(data.closure_evidence),
      hasClosedAt: hasContent(data.closed_at),
    }
  })
}

async function enrichWorkCases(items: ListedObject[]): Promise<ListedObject[]> {
  const workcaseSummaries = await buildWorkCaseSummaries(items)
  const summariesById = new Map(workcaseSummaries.map((workcase) => [workcase.id, workcase]))

  return items.map((item) => {
    const summary = summariesById.get(item.id)
    if (!summary) return item
    return {
      ...item,
      executionItems: summary.executionItems ?? [],
      executionItemTotal: summary.executionItemTotal ?? 0,
      executionItemDone: summary.executionItemDone ?? 0,
      executionItemBlocked: summary.executionItemBlocked ?? 0,
      executionItemOpen: summary.executionItemOpen ?? 0,
      successCriteriaTotal: summary.successCriteriaTotal ?? 0,
      successCriteriaDone: summary.successCriteriaDone ?? 0,
      hasSuccessCriteria: summary.hasSuccessCriteria,
      hasPlanConfirmedAt: summary.hasPlanConfirmedAt,
      hasClosureRequestedAt: summary.hasClosureRequestedAt,
      hasVerificationEvidence: summary.hasVerificationEvidence,
      hasClosureEvidence: summary.hasClosureEvidence,
      hasClosedAt: summary.hasClosedAt,
      executionItemByStatus: countByStatus(summary.executionItems ?? []),
    }
  })
}

async function enrichSparks(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = readFactData(item.path)
    return {
      ...item,
      source: toStringValue(data.source) || undefined,
      description: toStringValue(data.description) || undefined,
      source_detail: toStringValue(data.source_detail) || undefined,
      resolved_to: data.resolved_to || undefined,
      resolved_at: toStringValue(data.resolved_at) || undefined,
      discard_reason: toStringValue(data.discard_reason) || undefined,
    }
  })
}

async function enrichPitfalls(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = readFactData(item.path)
    return {
      ...item,
      resolution: toStringValue(data.resolution) || undefined,
      source_sparks: toStringArray(data.source_sparks),
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
  let enrichedItems = items
  if (isRecord(result.data)) {
    const statusItems = status ? await listObjectSummaries(type) : items
    result.data.statusOptions = getStatusOptions(statusItems)
    result.data.statusTotal = statusItems.length
  }
  if (isRecord(result.data) && type === 'workcase') {
    enrichedItems = await enrichWorkCases(items)
  }
  if (isRecord(result.data) && type === 'adr') {
    enrichedItems = await enrichAdrs(items)
  }
  if (isRecord(result.data) && type === 'spark') {
    enrichedItems = await enrichSparks(items)
  }
  if (isRecord(result.data) && type === 'pitfall') {
    enrichedItems = await enrichPitfalls(items)
  }
  if (isRecord(result.data)) {
    result.data.items = sortByUpdatedDesc(enrichedItems)
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

  // WorkCase 派生阅读材料：工作项自身材料 + execution_items 的输入和证据引用。
  if (type === 'workcase' && result.data) {
    const relatedDocsSet = new Set<string>()
    const relatedAdrsSet = new Set<string>()
    const relatedSparksSet = new Set<string>()
    const relatedPitfallsSet = new Set<string>()
    const executionRefsSet = new Set<string>()
    const orchestration = isRecord(result.data.orchestration) ? result.data.orchestration : {}
    const executionItems = Array.isArray(orchestration.execution_items) ? orchestration.execution_items : []

    addStringArray(relatedDocsSet, result.data.related_docs)
    addStringArray(relatedAdrsSet, result.data.related_adrs)
    addStringArray(relatedSparksSet, result.data.related_sparks)
    addStringArray(relatedPitfallsSet, result.data.related_pitfalls)

    for (const executionItem of executionItems) {
      if (!isRecord(executionItem)) continue
      addStringArray(executionRefsSet, executionItem.input_refs)
      addStringArray(executionRefsSet, executionItem.evidence_refs)
    }

    result.data.aggregated_related_docs = [...relatedDocsSet]
    result.data.aggregated_related_adrs = [...relatedAdrsSet]
    result.data.aggregated_related_sparks = [...relatedSparksSet]
    result.data.aggregated_related_pitfalls = [...relatedPitfallsSet]
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
      related_rules: toStringArray(data.related_rules),
      status: toStringValue(data.status) || item.status,
    }
  })
}
