/** V4-only fact reader for Human-facing Web views. */

import {
  V4FactsTransportError,
  type V4FactsMachineResponse,
} from '../internal/v4FactsTransport.js'
import { listV4WorkCases, readV4WorkCase } from './v4FactReader.js'
import { V4FactsConfigurationError, v4FactReaderConfig } from './v4FactsConfig.js'
import { listLocalFacts, readLocalFact, type LocalFactItem, type LocalFactMetadata, type LocalFactScope } from './localFactReader.js'
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

type MachineReadStatus = 'mechanically_valid' | 'invalid' | 'not_found' | 'unavailable'
type MachineCoverageStatus = 'complete' | 'partial' | 'unavailable'

interface MachineFactIssue {
  category: string
  field_path: string | null
  summary: string
}

interface MachineFactReadItem {
  object_ref: {
    governed_project_id: string
    fact_type_key: 'workcase'
    object_id: string
  }
  canonical_path: string
  absolute_path: string
  carrier: string
  check_status: MachineReadStatus
  fact_object: Record<string, unknown> | null
  content_fingerprint: string | null
  issues: MachineFactIssue[]
}

interface MachineWorkCaseListResult {
  status: MachineCoverageStatus
  observed_at: string
  items: MachineFactReadItem[]
  object_problems: MachineFactReadItem[]
  structural_problems: Array<{
    fact_type_key: 'workcase'
    canonical_path: string
    check_status: 'unavailable'
    issues: MachineFactIssue[]
  }>
}

interface MachineWorkCaseDetailResult {
  status: 'ok' | 'invalid' | 'not_found' | 'unavailable'
  observed_at: string
  item: MachineFactReadItem | null
  problems: MachineFactReadItem[]
  coverage_status: MachineCoverageStatus
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function machineResult<T>(response: V4FactsMachineResponse): T {
  if (!isRecord(response.result)) {
    throw new V4FactsTransportError(
      'v4_facts_unavailable',
      response.error ?? 'V4 facts machine did not return an operation result',
    )
  }
  return response.result as T
}

function result(action: string, target: string, data: Record<string, unknown>): WebFactResult {
  return {
    ok: true,
    command: 'v4-web-facts',
    action,
    target,
    summary: { count: Array.isArray(data.items) ? data.items.length : undefined },
    issues: [],
    data,
  }
}

function error(value: unknown): WebFactError {
  if (value instanceof V4FactsTransportError) {
    return { ok: false, error: value.message, stderr: value.diagnostic, exitCode: value.code }
  }
  if (value instanceof V4FactsConfigurationError) {
    return { ok: false, error: value.message, stderr: '', exitCode: value.code }
  }
  return { ok: false, error: value instanceof Error ? value.message : 'V4 facts unavailable', stderr: '', exitCode: 1 }
}

function localIssueToMachine(issue: LocalFactItem['issues'][number]): MachineFactIssue {
  return {
    category: issue.code || 'read',
    field_path: issue.path || null,
    summary: issue.message,
  }
}

/** item-02：目录缺失表示该类型尚未接入；返回非空诊断项，避免与“已接入但暂无数据”混淆。 */
function notIntegrated(type: ObjectType, message: string): WebFactResult {
  const listed = result('list', type, {
    items: [{
      id: `type-not-integrated-${type}`,
      type,
      status: 'type_not_integrated',
      title: message,
      path: `ldvh-base/${type}`,
      updated: '',
      kind: 'type_not_integrated',
      message,
    }],
    coverage_status: 'type_not_integrated',
  })
  listed.issues = [{ code: 'type_not_integrated', message }]
  listed.summary.coverage_status = 'type_not_integrated'
  return listed
}

/** 精确详情的扁平 DTO：事实字段与读取元数据同时交给详情消费者。 */
function projectDetailItem(item: LocalFactItem): Record<string, unknown> {
  return {
    ...item.fact_object,
    object_ref: item.object_ref,
    canonical_path: item.canonical_path,
    absolute_path: item.absolute_path,
    carrier: item.carrier,
    check_status: item.check_status,
  }
}

/**
 * 列表只承担候选发现；不得把尚未由该消费点精确读取的 source metadata
 * 或正文载体承诺给卡片、复制和预览。
 */
function projectListItem(item: LocalFactItem): Record<string, unknown> {
  return { ...item.fact_object }
}

function copyPresentFields(
  source: Record<string, unknown>,
  fields: readonly string[],
): Record<string, unknown> {
  return Object.fromEntries(fields.flatMap((field) => (
    Object.prototype.hasOwnProperty.call(source, field) ? [[field, source[field]]] : []
  )))
}

type CardWorkItem = {
  id: string
  title: string
  status: string
  blockingReason?: string
}

function projectCardWorkItems(value: unknown): {
  executionItemsProjectionValid: boolean
  executionItemTotal: number
  executionItemDone: number
  executionItemCancelled: number
  executionItemOpen: number
  executionItemsActive: CardWorkItem[]
} {
  if (!Array.isArray(value) || value.length === 0) {
    return {
      executionItemsProjectionValid: false,
      executionItemTotal: 0,
      executionItemDone: 0,
      executionItemCancelled: 0,
      executionItemOpen: 0,
      executionItemsActive: [],
    }
  }
  const items = value.map((candidate): CardWorkItem | null => {
    if (!isRecord(candidate)
      || typeof candidate.item_id !== 'string'
      || !candidate.item_id.trim()
      || typeof candidate.goal !== 'string'
      || !candidate.goal.trim()
      || typeof candidate.status !== 'string'
      || !candidate.status.trim()) return null
    return {
      id: candidate.item_id,
      title: candidate.goal,
      status: candidate.status,
      ...(typeof candidate.blocking_summary === 'string' && candidate.blocking_summary.trim()
        ? { blockingReason: candidate.blocking_summary }
        : {}),
    }
  })
  if (items.some((item) => item === null)) return projectCardWorkItems(null)
  const validItems = items as CardWorkItem[]
  if (new Set(validItems.map((item) => item.id)).size !== validItems.length) {
    return projectCardWorkItems(null)
  }
  return {
    executionItemsProjectionValid: true,
    executionItemTotal: validItems.length,
    executionItemDone: validItems.filter((item) => item.status === 'completed').length,
    executionItemCancelled: validItems.filter((item) => item.status === 'cancelled').length,
    executionItemOpen: validItems.filter((item) => (
      item.status === 'pending' || item.status === 'in_progress' || item.status === 'blocked'
    )).length,
    executionItemsActive: validItems.filter((item) => (
      item.status === 'in_progress' || item.status === 'blocked'
    )),
  }
}

function projectCriterionStatements(value: unknown): string[] {
  if (!Array.isArray(value) || value.length === 0) return []
  const statements = value.map((candidate) => (
    isRecord(candidate) && typeof candidate.statement === 'string' && candidate.statement.trim()
      ? candidate.statement
      : null
  ))
  return statements.every((statement): statement is string => statement !== null) ? statements : []
}

/** 08 external Card projection: never forward the complete exact-detail object. */
export function projectWorkCaseCard(fact: Record<string, unknown>): Record<string, unknown> {
  const projected = copyPresentFields(fact, [
    'object_id',
    'fact_type_key',
    'title',
    'status',
    'phase',
    'updated_at',
  ])
  const phase = typeof fact.phase === 'string' ? fact.phase : ''
  const progress = deriveWorkCaseProgressProjection(String(fact.status || ''), phase)
  if (progress?.progressGroup === 'plan_confirmation') {
    Object.assign(
      projected,
      copyPresentFields(fact, ['priority', 'goal']),
      { successCriteria: projectCriterionStatements(fact.success_criterion_definitions) },
    )
  } else if (progress?.progressGroup === 'progressing') {
    Object.assign(
      projected,
      copyPresentFields(fact, ['priority', 'goal', 'waiting_on']),
      projectCardWorkItems(fact.work_items),
    )
  }
  if (fact.status === 'blocked'
    && (progress?.progressGroup === 'plan_confirmation' || progress?.progressGroup === 'progressing')) {
    Object.assign(projected, copyPresentFields(fact, ['blocking_summary']))
  }
  return projected
}

function machineIssueRecords(items: MachineFactReadItem[]): Array<Record<string, unknown>> {
  return items.flatMap((item) => item.issues.map((issue) => ({
    ...issue,
    object_ref: item.object_ref,
    check_status: item.check_status,
  })))
}

function machineObjectReadProblems(listed: MachineWorkCaseListResult): Array<Record<string, unknown>> {
  return listed.object_problems.map((item) => ({
      code: `workcase_${item.check_status}`,
      error: item.issues.map((issue) => issue.summary).join('；'),
      object_ref: item.object_ref,
      check_status: item.check_status,
      issues: item.issues,
      targets: [],
    }))
}

function machineCoverageProblems(listed: MachineWorkCaseListResult): Array<Record<string, unknown>> {
  return listed.structural_problems.map((problem) => ({
      code: 'workcase_coverage_unavailable',
      error: problem.issues.map((issue) => issue.summary).join('；'),
      scope: 'workcase_collection',
      fact_type_key: problem.fact_type_key,
      check_status: problem.check_status,
      issues: problem.issues,
      targets: [],
    }))
}

function workCaseReaderConfig(scope?: LocalFactScope) {
  const config = v4FactReaderConfig()
  if (scope && (
    scope.worktreeLocator !== config.scope.worktree_locator
    || scope.governedProjectId !== config.scope.expected_governed_project_id
  )) {
    throw new V4FactsConfigurationError(
      'Explicit WorkCase scope does not match the configured Web fact-reading boundary',
    )
  }
  return config
}

async function listWorkCasesFromMachine(status?: string, scope?: LocalFactScope): Promise<WebFactResult> {
  const listed = machineResult<MachineWorkCaseListResult>(
    await listV4WorkCases(workCaseReaderConfig(scope)),
  )
  const items = listed.items
    .map((item) => projectWorkCaseCard(item.fact_object as Record<string, unknown>))
    .filter((item) => !status || item.status === status)
  const response = result('list', 'workcase', {
    items,
    coverage_status: listed.status,
    observed_at: listed.observed_at,
    object_read_problems: machineObjectReadProblems(listed),
    coverage_problems: machineCoverageProblems(listed),
  })
  response.summary.coverage_status = listed.status
  response.issues = [
    ...machineIssueRecords(listed.object_problems),
    ...listed.structural_problems.flatMap((problem) => problem.issues.map((issue) => ({
      ...issue,
      scope: 'workcase_collection',
      fact_type_key: problem.fact_type_key,
      check_status: problem.check_status,
    }))),
  ]
  return response
}

function readFailure(
  id: string,
  type: ObjectType,
  status: 'invalid' | 'not_found' | 'unavailable',
  metadata: LocalFactMetadata,
  issues: LocalFactItem['issues'],
): WebFactResult {
  const machineIssues = issues.map(localIssueToMachine)
  const response = result('show', id, {
    fact_read_failure: true,
    object_ref: metadata.object_ref,
    canonical_path: metadata.canonical_path,
    absolute_path: metadata.absolute_path,
    carrier: metadata.carrier,
    check_status: status,
    read_issues: machineIssues,
  })
  response.summary = { id, type, read_status: status }
  response.issues = machineIssues.map((issue) => ({ ...issue }))
  return response
}

function machineReadFailure(
  id: string,
  detail: MachineWorkCaseDetailResult,
  item: MachineFactReadItem,
): WebFactResult {
  const response = result('show', id, {
    fact_read_failure: true,
    object_ref: item.object_ref,
    canonical_path: item.canonical_path,
    carrier: item.carrier,
    check_status: item.check_status,
    coverage_status: detail.coverage_status,
    observed_at: detail.observed_at,
    read_issues: item.issues,
  })
  response.summary = { id, type: 'workcase', read_status: item.check_status }
  response.issues = item.issues.map((issue) => ({ ...issue }))
  return response
}

async function showWorkCaseFromMachine(id: string, scope?: LocalFactScope): Promise<WebFactResult> {
  const detail = machineResult<MachineWorkCaseDetailResult>(
    await readV4WorkCase(workCaseReaderConfig(scope), id),
  )
  if (detail.status !== 'ok' || detail.item === null || detail.item.fact_object === null) {
    const problem = detail.problems[0]
    if (!problem) {
      throw new V4FactsTransportError(
        'malformed_machine_response',
        'WorkCase detail failure omitted its exact read result',
      )
    }
    return machineReadFailure(id, detail, problem)
  }
  const item = detail.item
  const data: Record<string, unknown> = {
    ...item.fact_object,
    object_ref: item.object_ref,
    canonical_path: item.canonical_path,
    carrier: item.carrier,
    check_status: item.check_status,
    content_fingerprint: item.content_fingerprint,
    coverage_status: detail.coverage_status,
    observed_at: detail.observed_at,
    read_issues: item.issues,
  }
  const response = {
    ...result('show', id, data),
    summary: {
      id: typeof data.object_id === 'string' ? data.object_id : id,
      type: 'workcase',
      status: typeof data.status === 'string' ? data.status : 'unknown',
      ...(typeof data.phase === 'string' ? { phase: data.phase } : {}),
    },
  }
  response.issues = item.issues.map((issue) => ({ ...issue }))
  return response
}

export async function listObjects(type: ObjectType, _baseDir?: string, status?: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  try {
    if (type === 'workcase') return await listWorkCasesFromMachine(status, scope)
    const listed = await listLocalFacts(type, scope)
    if (listed.status !== 'complete') {
      const message = listed.issues[0]?.message ?? `类型 ${type} 尚无对象目录`
      return notIntegrated(type, message)
    }
    const projectionProblems: Array<Record<string, unknown>> = listed.items
      .filter((item) => item.check_status !== 'readable')
      .map((item) => ({
        code: 'local_read_issue',
        error: item.issues.map((issue) => issue.message).join('；'),
        object_ref: item.object_ref,
        targets: [],
      }))
    projectionProblems.push(...listed.issues.map((issue) => ({
      code: issue.code,
      error: issue.message,
      canonical_path: issue.path,
      targets: [],
    })))
    const items = listed.items
      .filter((item) => item.check_status === 'readable')
      .map(projectListItem)
      .filter((item) => !status || item.status === status)
    const response = result('list', type, {
      items,
      coverage_status: listed.status,
      projection_problems: projectionProblems,
    })
    response.issues = [
      ...listed.issues.map((issue) => ({ ...issue }) as Record<string, unknown>),
      ...listed.items.flatMap((item) => item.issues.map((issue) => ({ ...issue }) as Record<string, unknown>)),
    ]
    return response
  } catch (caught) {
    return error(caught)
  }
}

const OBJECT_ID_PATTERN = /^(workcase|adr|pitfall|spark|study)-\d+$/

export async function showObject(id: string, scope?: LocalFactScope): Promise<WebFactResult | WebFactError> {
  const match = OBJECT_ID_PATTERN.exec(id)
  if (!match) {
    return { ok: false, error: `Object not found: ${id}`, stderr: '', exitCode: 1 }
  }
  const type = match[1] as ObjectType
  try {
    if (type === 'workcase') return await showWorkCaseFromMachine(id, scope)
    const detail = await readLocalFact(type, id, scope)
    if (detail.status === 'not_found') return readFailure(id, type, 'not_found', detail.metadata, detail.issues)
    if (detail.status === 'type_not_integrated') {
      return readFailure(id, type, 'unavailable', detail.metadata, detail.issues)
    }
    if (detail.status === 'unavailable') {
      return readFailure(id, type, 'unavailable', detail.metadata, detail.issues)
    }
    if (detail.item.check_status !== 'readable') {
      return readFailure(id, type, 'invalid', detail.item, detail.item.issues)
    }
    const data: Record<string, unknown> = {
      ...projectDetailItem(detail.item),
      coverage_status: 'complete',
      read_issues: detail.item.issues.map(localIssueToMachine),
    }
    const response = {
      ...result('show', id, data),
      summary: {
        id: typeof data.object_id === 'string' ? data.object_id : id,
        type: typeof data.fact_type_key === 'string' ? data.fact_type_key : type,
        status: typeof data.status === 'string' ? data.status : 'unknown',
      },
    }
    response.issues = detail.item.issues.map(localIssueToMachine).map((issue) => ({ ...issue }))
    return response
  } catch (caught) {
    return error(caught)
  }
}

/** No compatibility reader: unsupported callers receive no invented fact data. */
export function readFactData(_filePath: string): Record<string, unknown> {
  return {}
}

export { V4FactsConfigurationError }
