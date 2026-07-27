/** Field-level current-fact reader for Human-facing Web views. */
import {
  listLocalFacts,
  readLocalFact,
  type LocalFactItem,
  type LocalFactMetadata,
  type LocalFactScope,
} from './localFactReader.js'
import { resolveCurrentWebProject, WebGovernanceError } from './governanceScope.js'
import { deriveWorkCaseProgressProjection } from '../../shared/workcaseStatus.js'

export const ACTIVE_OBJECT_TYPES = ['workcase', 'adr', 'pitfall', 'spark', 'study'] as const
export const OBJECT_TYPES = ACTIVE_OBJECT_TYPES
export type ObjectType = (typeof OBJECT_TYPES)[number]

export interface WebFactResult {
  ok: true
  command: string
  action: string
  target: string
  summary: Record<string, unknown>
  issues: Array<Record<string, unknown>>
  data: Record<string, unknown>
}

export interface WebFactError {
  ok: false
  error: string
  stderr: string
  exitCode: number | string | null
}

function result(action: string, target: string, data: Record<string, unknown>): WebFactResult {
  return { ok: true, command: 'field-level-fact-reader', action, target, summary: { count: Array.isArray(data.items) ? data.items.length : undefined }, issues: [], data }
}

function error(value: unknown): WebFactError {
  if (value instanceof WebGovernanceError) return { ok: false, error: value.message, stderr: '', exitCode: 'governance_unavailable' }
  return { ok: false, error: value instanceof Error ? value.message : 'Fact reader unavailable', stderr: '', exitCode: 1 }
}

async function readingScope(scope?: LocalFactScope): Promise<LocalFactScope> {
  // Explicit scope is an in-process test seam; HTTP requests always resolve it via Helper.
  if (scope) return scope
  const project = await resolveCurrentWebProject()
  return { worktreeLocator: project.path, governedProjectId: project.id }
}

function notIntegrated(type: ObjectType, message: string): WebFactResult {
  const issue = { code: 'type_not_integrated', message }
  const response = result('list', type, { items: [], coverage_status: 'type_not_integrated', collection_issues: [issue] })
  response.issues = [issue]
  response.summary.coverage_status = 'type_not_integrated'
  return response
}

function readFailure(id: string, type: ObjectType, metadata: LocalFactMetadata, issues: Array<Record<string, unknown>>): WebFactResult {
  const response = result('show', id, {
    fact_read_failure: true,
    object_ref: metadata.object_ref,
    canonical_path: metadata.canonical_path,
    carrier: metadata.carrier,
    read_status: 'unreadable',
    field_issues: [],
    unparsed_structures: [],
    read_issues: issues,
  })
  response.summary = { id, type, read_status: 'unreadable' }
  response.issues = issues
  return response
}

function projectListItem(type: ObjectType, item: LocalFactItem): Record<string, unknown> {
  const source = item.fact_object ?? {}
  const base = type === 'workcase' ? projectWorkCaseCard(source) : source
  return {
    ...base,
    read_status: item.read_status,
    read_issues: item.issues,
    field_issues: item.field_issues,
    unparsed_structures: item.unparsed_structures,
  }
}

function copyPresentFields(source: Record<string, unknown>, fields: readonly string[]): Record<string, unknown> {
  return Object.fromEntries(fields.flatMap((field) => Object.prototype.hasOwnProperty.call(source, field) ? [[field, source[field]]] : []))
}

type CardWorkItem = { id: string; title: string; status: string; blockingReason?: string }

function projectCardWorkItems(value: unknown): Record<string, unknown> {
  if (!Array.isArray(value) || value.length === 0) return { executionItemsProjectionValid: false, executionItemTotal: 0, executionItemDone: 0, executionItemCancelled: 0, executionItemOpen: 0, executionItemsActive: [] }
  const items = value.map((candidate): CardWorkItem | null => {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
    const item = candidate as Record<string, unknown>
    if (typeof item.item_id !== 'string' || !item.item_id.trim() || typeof item.goal !== 'string' || !item.goal.trim() || typeof item.status !== 'string' || !item.status.trim()) return null
    return { id: item.item_id, title: item.goal, status: item.status, ...(typeof item.blocking_summary === 'string' && item.blocking_summary.trim() ? { blockingReason: item.blocking_summary } : {}) }
  })
  if (items.some((item) => item === null) || new Set((items as CardWorkItem[]).map((item) => item.id)).size !== items.length) return projectCardWorkItems(null)
  const valid = items as CardWorkItem[]
  return {
    executionItemsProjectionValid: true,
    executionItemTotal: valid.length,
    executionItemDone: valid.filter((item) => item.status === 'completed').length,
    executionItemCancelled: valid.filter((item) => item.status === 'cancelled').length,
    executionItemOpen: valid.filter((item) => ['pending', 'in_progress', 'blocked'].includes(item.status)).length,
    executionItemsActive: valid.filter((item) => ['in_progress', 'blocked'].includes(item.status)),
  }
}

function projectCriterionStatements(value: unknown): string[] {
  if (!Array.isArray(value) || value.length === 0) return []
  const statements = value.map((candidate) => {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
    const statement = (candidate as Record<string, unknown>).statement
    return typeof statement === 'string' && statement.trim() ? statement : null
  })
  return statements.every((statement): statement is string => statement !== null) ? statements : []
}

export function projectWorkCaseCard(fact: Record<string, unknown>): Record<string, unknown> {
  const projected = copyPresentFields(fact, ['object_id', 'fact_type_key', 'title', 'status', 'phase', 'updated_at'])
  const phase = typeof fact.phase === 'string' ? fact.phase : ''
  const progress = deriveWorkCaseProgressProjection(typeof fact.status === 'string' ? fact.status : '', phase)
  if (progress?.progressGroup === 'plan_confirmation') {
    Object.assign(projected, copyPresentFields(fact, ['priority', 'goal']), { successCriteria: projectCriterionStatements(fact.success_criterion_definitions) })
  } else if (progress?.progressGroup === 'progressing') {
    Object.assign(projected, copyPresentFields(fact, ['priority', 'goal', 'waiting_on']), projectCardWorkItems(fact.work_items))
  }
  if (fact.status === 'blocked' && (progress?.progressGroup === 'plan_confirmation' || progress?.progressGroup === 'progressing')) Object.assign(projected, copyPresentFields(fact, ['blocking_summary']))
  return projected
}

export async function listObjects(type: ObjectType, _baseDir?: string, status?: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  try {
    const listed = await listLocalFacts(type, await readingScope(scope))
    if (listed.status !== 'complete') return notIntegrated(type, listed.issues[0]?.message ?? `类型 ${type} 尚无对象目录`)
    const items = listed.items.map((item) => projectListItem(type, item)).filter((item) => !status || item.status === status)
    const response = result('list', type, { items, coverage_status: 'complete', collection_issues: listed.issues })
    response.issues = [
      ...listed.issues.map((issue) => ({ ...issue })),
      ...listed.items.flatMap((item) => item.issues.map((issue) => ({ ...issue, object_ref: item.object_ref }))),
      ...listed.items.flatMap((item) => item.field_issues.map((issue) => ({
        code: issue.reason,
        message: `字段 ${issue.path} ${issue.reason}；期望 ${issue.expected}`,
        path: issue.path,
        object_ref: item.object_ref,
      }))),
    ]
    return response
  } catch (caught) {
    return error(caught)
  }
}

const OBJECT_ID_PATTERN = /^(workcase|adr|pitfall|spark|study)-\d+$/

export async function showObject(id: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  const match = OBJECT_ID_PATTERN.exec(id)
  if (!match) return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
  const type = match[1] as ObjectType
  try {
    const detail = await readLocalFact(type, id, await readingScope(scope))
    if (detail.status !== 'ok') return readFailure(id, type, detail.metadata, detail.issues)
    const item = detail.item
    if (item.read_status === 'unreadable' || item.fact_object === null) return readFailure(id, type, item, item.issues)
    const data: Record<string, unknown> = {
      ...item.fact_object,
      object_ref: item.object_ref,
      canonical_path: item.canonical_path,
      carrier: item.carrier,
      read_status: item.read_status,
      field_issues: item.field_issues,
      unparsed_structures: item.unparsed_structures,
      read_issues: item.issues,
    }
    const response = { ...result('show', id, data), summary: { id, type, ...(typeof data.status === 'string' ? { status: data.status } : {}) } }
    response.issues = [...item.issues, ...item.field_issues]
    return response
  } catch (caught) {
    return error(caught)
  }
}
