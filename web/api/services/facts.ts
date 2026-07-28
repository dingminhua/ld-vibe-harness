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
import { FACT_LIST_FIELD_NAMES } from './factFieldContract.js'

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
  const base = type === 'workcase' ? projectWorkCaseCard(source) : copyPresentFields(source, FACT_LIST_FIELD_NAMES[type])
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
  if (!Array.isArray(value) || value.length === 0) return { executionItemsProjectionValid: false, executionItems: [] }
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
    executionItems: valid,
  }
}

function projectCriterionStatements(value: unknown): string[] {
  if (!Array.isArray(value) || value.length === 0) return []
  return value
    .map((candidate) => {
      if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
      const statement = (candidate as Record<string, unknown>).statement
      return typeof statement === 'string' && statement.trim() ? statement : null
    })
    .filter((statement): statement is string => statement !== null)
}

function projectContributedToTargets(value: unknown): Array<Record<string, string>> {
  if (!Array.isArray(value)) return []
  return value.flatMap((candidate) => {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return []
    const relation = candidate as Record<string, unknown>
    if (relation.relation_key !== 'contributed-to') return []
    const target = relation.target
    if (!target || typeof target !== 'object' || Array.isArray(target)) return []
    const triple = target as Record<string, unknown>
    if (typeof triple.governed_project_id !== 'string' || !triple.governed_project_id.trim()
      || triple.fact_type_key !== 'pitfall'
      || typeof triple.object_id !== 'string' || !triple.object_id.trim()) return []
    return [{ governedProjectId: triple.governed_project_id, factTypeKey: triple.fact_type_key, objectId: triple.object_id }]
  })
}

const CLOSURE_PROPOSAL_OUTCOMES = new Set(['completed', 'partial', 'not-achieved', 'cancelled'])
const RESIDUAL_DISPOSITIONS = new Set(['route_existing', 'suggest_spark', 'accept_stop'])

function projectRelationTarget(value: unknown): Record<string, string> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const target = value as Record<string, unknown>
  if (typeof target.governed_project_id !== 'string' || !target.governed_project_id.trim()
    || typeof target.fact_type_key !== 'string' || !target.fact_type_key.trim()
    || typeof target.object_id !== 'string' || !target.object_id.trim()) return null
  return { governedProjectId: target.governed_project_id, factTypeKey: target.fact_type_key, objectId: target.object_id }
}

function projectProposalRouteTarget(value: unknown): Record<string, string> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const target = value as Record<string, unknown>
  const allowed = new Set(['governed_project_id', 'fact_type_key', 'object_id', 'content_fingerprint'])
  if (Object.keys(target).some((key) => !allowed.has(key))
    || typeof target.content_fingerprint !== 'string'
    || !/^[0-9a-f]{64}$/.test(target.content_fingerprint)) return null
  const projected = projectRelationTarget(target)
  if (projected === null) return null
  if (projected.factTypeKey === 'workcase' && !/^workcase-[0-9]{4,}$/.test(projected.objectId)) return null
  if (projected.factTypeKey === 'spark' && !/^spark-[0-9]{4,}$/.test(projected.objectId)) return null
  return projected
}

function projectSparkSuggestions(value: unknown): Array<Record<string, string>> | null {
  if (value === undefined) return []
  if (!Array.isArray(value) || value.length === 0) return null
  const projected: Array<Record<string, string>> = []
  const identifiers = new Set<string>()
  const allowed = new Set([
    'suggestion_id', 'suggestion_kind', 'summary', 'follow_up_summary',
    'restriction_reason', 'impact_summary', 'resume_condition',
  ])
  for (const candidate of value) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
    const suggestion = candidate as Record<string, unknown>
    if (Object.keys(suggestion).some((key) => !allowed.has(key))) return null
    if (typeof suggestion.suggestion_id !== 'string' || !/^suggestion-[a-z0-9][a-z0-9-]*$/.test(suggestion.suggestion_id)
      || identifiers.has(suggestion.suggestion_id)
      || !['constrained_responsibility', 'follow_up_opportunity'].includes(String(suggestion.suggestion_kind))
      || typeof suggestion.summary !== 'string' || !suggestion.summary.trim()
      || typeof suggestion.follow_up_summary !== 'string' || !suggestion.follow_up_summary.trim()) return null
    const constrainedFields = ['restriction_reason', 'impact_summary', 'resume_condition']
    if (suggestion.suggestion_kind === 'constrained_responsibility'
      && constrainedFields.some((key) => typeof suggestion[key] !== 'string' || !(suggestion[key] as string).trim())) return null
    if (suggestion.suggestion_kind === 'follow_up_opportunity'
      && constrainedFields.some((key) => key in suggestion)) return null
    identifiers.add(suggestion.suggestion_id)
    projected.push({
      suggestionId: suggestion.suggestion_id,
      suggestionKind: String(suggestion.suggestion_kind),
      summary: suggestion.summary,
      followUpSummary: suggestion.follow_up_summary,
      ...(typeof suggestion.restriction_reason === 'string' ? { restrictionReason: suggestion.restriction_reason } : {}),
      ...(typeof suggestion.impact_summary === 'string' ? { impactSummary: suggestion.impact_summary } : {}),
      ...(typeof suggestion.resume_condition === 'string' ? { resumeCondition: suggestion.resume_condition } : {}),
    })
  }
  return projected
}

function projectResidualDecisions(
  value: unknown,
  outcome: string,
  suggestions: Array<Record<string, string>>,
): Array<Record<string, unknown>> | null {
  if (value === undefined) return outcome === 'completed' ? [] : null
  if (!Array.isArray(value) || value.length === 0 || outcome === 'completed') return null
  const projected: Array<Record<string, unknown>> = []
  const identifiers = new Set<string>()
  const suggestionKinds = new Map(suggestions.map((item) => [item.suggestionId, item.suggestionKind]))
  const allowed = new Set(['residual_id', 'summary', 'proposed_disposition', 'route_target', 'spark_suggestion_id'])
  for (const candidate of value) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
    const decision = candidate as Record<string, unknown>
    if (Object.keys(decision).some((key) => !allowed.has(key))) return null
    if (typeof decision.residual_id !== 'string' || !/^residual-[a-z0-9][a-z0-9-]*$/.test(decision.residual_id)
      || identifiers.has(decision.residual_id)) return null
    if (typeof decision.summary !== 'string' || !decision.summary.trim()) return null
    if (typeof decision.proposed_disposition !== 'string' || !RESIDUAL_DISPOSITIONS.has(decision.proposed_disposition)) return null
    const routeTarget = decision.proposed_disposition === 'route_existing' ? projectProposalRouteTarget(decision.route_target) : null
    if (decision.proposed_disposition === 'route_existing'
      && (routeTarget === null || !['workcase', 'spark'].includes(routeTarget.factTypeKey))) return null
    if (decision.proposed_disposition !== 'route_existing' && decision.route_target !== undefined) return null
    if (decision.proposed_disposition === 'suggest_spark') {
      if (typeof decision.spark_suggestion_id !== 'string'
        || suggestionKinds.get(decision.spark_suggestion_id) !== 'constrained_responsibility') return null
    } else if (decision.spark_suggestion_id !== undefined) return null
    identifiers.add(decision.residual_id)
    projected.push({
      residualId: decision.residual_id,
      summary: decision.summary,
      proposedDisposition: decision.proposed_disposition,
      ...(routeTarget ? { routeTarget } : {}),
    })
  }
  return projected
}

/**
 * Projects the stable closure-decision subset consumed by the Card. The whole
 * projection is dropped unless every required proposal member is readable and
 * complete. No malformed decision or suggestion is silently omitted.
 */
function projectClosureProposal(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  const proposal = value as Record<string, unknown>
  const allowed = new Set(['proposed_outcome', 'proposed_disposition_summary', 'residual_decisions', 'spark_suggestions'])
  if (Object.keys(proposal).some((key) => !allowed.has(key))) return null
  if (typeof proposal.proposed_outcome !== 'string' || !CLOSURE_PROPOSAL_OUTCOMES.has(proposal.proposed_outcome)) return null
  if (typeof proposal.proposed_disposition_summary !== 'string' || !proposal.proposed_disposition_summary.trim()) return null
  const suggestions = projectSparkSuggestions(proposal.spark_suggestions)
  if (suggestions === null) return null
  if (proposal.proposed_outcome === 'completed'
    && suggestions.some((item) => item.suggestionKind === 'constrained_responsibility')) return null
  const decisions = projectResidualDecisions(proposal.residual_decisions, proposal.proposed_outcome, suggestions)
  if (decisions === null) return null
  return {
    proposedOutcome: proposal.proposed_outcome,
    dispositionSummary: proposal.proposed_disposition_summary,
    residualDecisions: decisions,
    sparkSuggestions: suggestions,
  }
}

function projectClosedDisposition(fact: Record<string, unknown>): Record<string, unknown> | null {
  if (typeof fact.closure_outcome !== 'string' || !CLOSURE_PROPOSAL_OUTCOMES.has(fact.closure_outcome)) return null
  if (typeof fact.disposition_summary !== 'string' || !fact.disposition_summary.trim()) return null
  const suggestions = projectSparkSuggestions(fact.spark_suggestions)
  if (suggestions === null) return null
  const routedTo: Array<Record<string, string>> = []
  if (Array.isArray(fact.relations)) {
    for (const candidate of fact.relations) {
      if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) continue
      const relation = candidate as Record<string, unknown>
      if (relation.relation_key !== 'routed-to') continue
      const target = projectRelationTarget(relation.target)
      if (target === null || !['workcase', 'spark'].includes(target.factTypeKey)) return null
      routedTo.push(target)
    }
  } else if (fact.relations !== undefined) return null
  const acceptedStop: Array<Record<string, string>> = []
  const residualIdentifiers = new Set<string>()
  if (fact.residual_responsibilities !== undefined) {
    if (!Array.isArray(fact.residual_responsibilities) || fact.residual_responsibilities.length === 0) return null
    for (const candidate of fact.residual_responsibilities) {
      if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) return null
      const residual = candidate as Record<string, unknown>
      if (typeof residual.residual_id !== 'string' || !residual.residual_id.trim()
        || residualIdentifiers.has(residual.residual_id)
        || typeof residual.summary !== 'string' || !residual.summary.trim()) return null
      residualIdentifiers.add(residual.residual_id)
      acceptedStop.push({ residualId: residual.residual_id, summary: residual.summary })
    }
  }
  if (fact.closure_outcome === 'completed'
    && (routedTo.length > 0 || acceptedStop.length > 0
      || suggestions.some((item) => item.suggestionKind === 'constrained_responsibility'))) return null
  if (fact.closure_outcome !== 'completed'
    && routedTo.length === 0 && acceptedStop.length === 0
    && !suggestions.some((item) => item.suggestionKind === 'constrained_responsibility')) return null
  return {
    outcome: fact.closure_outcome,
    dispositionSummary: fact.disposition_summary,
    routedTo,
    acceptedStop,
    sparkSuggestions: suggestions,
  }
}

export function projectWorkCaseCard(fact: Record<string, unknown>): Record<string, unknown> {
  const projected = copyPresentFields(fact, ['object_id', 'fact_type_key', 'title', 'status', 'phase', 'updated_at'])
  const phase = typeof fact.phase === 'string' ? fact.phase : ''
  const progress = deriveWorkCaseProgressProjection(typeof fact.status === 'string' ? fact.status : '', phase)
  if (progress?.progressGroup === 'plan_confirmation') {
    Object.assign(projected, copyPresentFields(fact, ['priority', 'goal']), { successCriteria: projectCriterionStatements(fact.success_criterion_definitions) })
  } else if (progress?.progressGroup === 'progressing') {
    Object.assign(projected, copyPresentFields(fact, ['priority', 'goal', 'waiting_on']), projectCardWorkItems(fact.work_items))
  } else if (progress?.progressGroup === 'closure_confirmation') {
    Object.assign(projected, copyPresentFields(fact, ['goal']))
    const closureProposal = projectClosureProposal(fact.closure_proposal)
    if (closureProposal) projected.closureProposal = closureProposal
    const contributedTo = projectContributedToTargets(fact.relations)
    if (contributedTo.length > 0) projected.contributedTo = contributedTo
  } else if (progress?.progressGroup === 'closed') {
    Object.assign(projected, copyPresentFields(fact, ['goal']))
    const closureTerminal = projectClosedDisposition(fact)
    if (closureTerminal) projected.closureTerminal = closureTerminal
    const contributedTo = projectContributedToTargets(fact.relations)
    if (contributedTo.length > 0) projected.contributedTo = contributedTo
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
