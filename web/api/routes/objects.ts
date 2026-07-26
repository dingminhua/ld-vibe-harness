/**
 * Objects API 路由：按类型列表和按 ID 查看详情
 */

import { Router, type Request, type Response } from 'express'
import { listObjects, showObject, OBJECT_TYPES, type ObjectType } from '../services/facts.js'
import {
  WORKCASE_PROGRESS_GROUP_ORDER,
  WORKCASE_STATUS_ORDER,
  getWorkCaseDisplayStatus,
  getWorkCaseProgressProjection,
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
}

interface RelatedWorkCaseSummary extends RelatedObjectSummary {
  executionItems?: RelatedObjectSummary[]
  executionItemsProjectionValid?: boolean
  executionItemTotal?: number
  executionItemDone?: number
  executionItemCancelled?: number
  executionItemBlocked?: number
  executionItemOpen?: number
  executionItemsInProgress?: RelatedObjectSummary[]
  progressHistoryCoverage?: 'full' | 'partial'
  progressHistoryState?: 'missing' | 'valid' | 'invalid'
  progressRound?: number
  progressEventId?: string
  successCriteriaTotal?: number
  successCriteriaDone?: number
  successCriteria?: string[]
  hasSuccessCriteria: boolean
  hasPlanConfirmedAt: boolean
  hasClosureRequestedAt: boolean
  hasVerificationEvidence?: boolean
  hasClosureEvidence?: boolean
}

interface StatusOption {
  status: string
  count: number
}

interface ProgressOption {
  group: string
  count: number
}

type WorkCaseProfileKind = 'current' | 'legacy' | 'invalid'

const WORKCASE_CURRENT_BOUNDARY = '2026-07-20T07:30:00+08:00'
const WORKCASE_PROGRESS_BOUNDARY = '2026-07-26T07:30:00+08:00'

const SPARK_PRIORITY_ORDER = ['P0', 'P1', 'P2', 'P3']

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
  // A limited status remains a non-terminal display state for implemented object types.
  degraded: 18,
  suspended: 19,
  proposed: 20,
  planned: 21,
  pending: 22,
  resolved: 23,
  accepted: 24,
  archived: 25,
  discarded: 26,
  rejected: 27,
  deprecated: 28,
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function hasOwn(value: object, key: PropertyKey): boolean {
  return Object.prototype.hasOwnProperty.call(value, key)
}

function parseStrictRfc3339(value: string): bigint | null {
  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|([+-])(\d{2}):(\d{2}))$/,
  )
  if (!match) return null
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, fraction = '', zone, sign, offsetHourText, offsetMinuteText] = match
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const hour = Number(hourText)
  const minute = Number(minuteText)
  const second = Number(secondText)
  const offsetHour = zone === 'Z' ? 0 : Number(offsetHourText)
  const offsetMinute = zone === 'Z' ? 0 : Number(offsetMinuteText)
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  const daysInMonth = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  if (
    year < 1
    || month < 1 || month > 12
    || day < 1 || day > daysInMonth[month - 1]
    || hour > 23 || minute > 59 || second > 59
    || offsetHour > 23 || offsetMinute > 59
  ) return null

  const base = new Date(0)
  base.setUTCFullYear(year, month - 1, day)
  base.setUTCHours(hour, minute, second, 0)
  const offsetDirection = sign === '-' ? -1 : 1
  const offsetMilliseconds = offsetDirection * (offsetHour * 60 + offsetMinute) * 60_000
  const epochMilliseconds = base.getTime() - offsetMilliseconds
  if (!Number.isFinite(epochMilliseconds)) return null
  const microseconds = BigInt(fraction.slice(0, 6).padEnd(6, '0'))
  return BigInt(epochMilliseconds) * 1_000n + microseconds
}

function getWorkCaseProfileKind(data: Record<string, unknown>): WorkCaseProfileKind {
  const createdAt = parseStrictRfc3339(toStringValue(data.created_at))
  if (data.workcase_profile === 'control-contract-v1') return createdAt === null ? 'invalid' : 'current'
  if (hasOwn(data, 'workcase_profile')) return 'invalid'
  const currentBoundary = parseStrictRfc3339(WORKCASE_CURRENT_BOUNDARY)
  return createdAt !== null && currentBoundary !== null && createdAt < currentBoundary ? 'legacy' : 'invalid'
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
  const v4Object = typeof value.object_id === 'string' && typeof value.fact_type_key === 'string'
  const id = toStringValue(value.object_id) || toStringValue(value.id)
  if (!id) return null
  const type = toStringValue(value.fact_type_key) || toStringValue(value.type)
  const responsibilityStatus = toStringValue(value.status, 'unknown')
  const progressProjection = type === 'workcase'
    ? getWorkCaseProgressProjection(toStringValue(value.phase))
    : null
  const status = type === 'workcase'
    ? getWorkCaseDisplayStatus(toStringValue(value.phase), responsibilityStatus)
    : responsibilityStatus

  return {
    ...value,
    id,
    type,
    status,
    responsibilityStatus,
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

function toExecutionItemSummary(
  value: unknown,
  workcase: ListedObject,
  index: number,
  currentProfile = false,
): RelatedObjectSummary | null {
  if (!isRecord(value)) return null
  const currentId = toStringValue(value.item_id)
  const currentGoal = toStringValue(value.goal)
  const currentStatus = toStringValue(value.status)
  if (
    currentProfile
    && (!/^item-[0-9]{2,}$/.test(currentId)
      || !currentGoal.trim()
      || !['pending', 'in_progress', 'blocked', 'completed', 'cancelled'].includes(currentStatus))
  ) return null
  const id = currentProfile
    ? currentId
    : currentId || toStringValue(value.id) || `execution-item-${index + 1}`
  const status = toStringValue(value.status, 'unknown')
  const title = currentProfile ? currentGoal : currentGoal || toStringValue(value.title, id)

  return {
    id,
    type: 'execution_item',
    status,
    title,
    path: workcase.path,
    updated: workcase.updated,
    role: toStringValue(value.role) || toStringValue(value.item_id) || undefined,
    mode: toStringValue(value.mode) || undefined,
    expectedOutput: toStringValue(value.expected_result) || toStringValue(value.expected_output) || undefined,
    resultSummary: toStringValue(value.result_summary) || undefined,
    blockingReason: toStringValue(value.blocking_summary) || toStringValue(value.blocking_reason) || undefined,
    inputRefs: toStringArray(value.input_refs),
  }
}

function hasNonEmptyString(value: unknown): boolean {
  return typeof value === 'string' && value.trim().length > 0
}

function hasUniqueNonEmptyStrings(value: unknown): value is string[] {
  return Array.isArray(value)
    && value.length > 0
    && value.every(hasNonEmptyString)
    && new Set(value).size === value.length
}

function hasValidCurrentWorkItems(value: unknown): value is Array<Record<string, unknown>> {
  if (!Array.isArray(value) || value.length === 0 || value.some((item) => !isRecord(item))) return false
  const items = value as Array<Record<string, unknown>>
  const allowedFields = new Set([
    'item_id', 'goal', 'expected_result', 'status', 'depends_on', 'approach_summary', 'template_keys',
    'template_deviation_summary', 'current_summary', 'resume_from', 'blocking_summary', 'result_summary',
  ])
  const ids = items.map((item) => toStringValue(item.item_id))
  if (new Set(ids).size !== items.length) return false
  const statuses = new Map(ids.map((id, index) => [id, toStringValue(items[index].status)]))

  for (const item of items) {
    const id = toStringValue(item.item_id)
    const status = toStringValue(item.status)
    if (
      Object.keys(item).some((key) => !allowedFields.has(key))
      || !/^item-[0-9]{2,}$/.test(id)
      || !hasNonEmptyString(item.goal)
      || !hasNonEmptyString(item.expected_result)
      || !hasNonEmptyString(item.approach_summary)
      || !['pending', 'in_progress', 'blocked', 'completed', 'cancelled'].includes(status)
    ) return false

    const conditional = ['current_summary', 'resume_from', 'blocking_summary', 'result_summary']
    const required = status === 'blocked'
      ? ['current_summary', 'resume_from', 'blocking_summary']
      : status === 'in_progress'
        ? ['current_summary', 'resume_from']
        : ['completed', 'cancelled'].includes(status)
          ? ['result_summary']
          : []
    const allowed = new Set(required)
    if (required.some((key) => !hasNonEmptyString(item[key]))) return false
    if (conditional.some((key) => hasOwn(item, key) && !allowed.has(key))) return false

    if (hasOwn(item, 'depends_on')) {
      if (!hasUniqueNonEmptyStrings(item.depends_on)) return false
      if (item.depends_on.some((dependency) => !statuses.has(dependency) || dependency === id)) return false
      if (
        status === 'in_progress'
        && item.depends_on.some((dependency) => !['completed', 'cancelled'].includes(statuses.get(dependency) ?? ''))
      ) return false
    }
    if (hasOwn(item, 'template_keys') && !hasUniqueNonEmptyStrings(item.template_keys)) return false
    if (hasOwn(item, 'template_deviation_summary') && !hasNonEmptyString(item.template_deviation_summary)) {
      return false
    }
  }

  const dependencies = new Map(items.map((item) => [
    toStringValue(item.item_id),
    Array.isArray(item.depends_on) ? item.depends_on as string[] : [],
  ]))
  const visiting = new Set<string>()
  const visited = new Set<string>()
  const hasCycle = (id: string): boolean => {
    if (visiting.has(id)) return true
    if (visited.has(id)) return false
    visiting.add(id)
    if ((dependencies.get(id) ?? []).some(hasCycle)) return true
    visiting.delete(id)
    visited.add(id)
    return false
  }
  return !ids.some(hasCycle)
}

function countByStatus(items: Array<{ status: string }>): Record<string, number> {
  return items.reduce<Record<string, number>>((counts, item) => {
    counts[item.status] = (counts[item.status] ?? 0) + 1
    return counts
  }, {})
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

function getWorkCaseCriterionStatements(
  data: Record<string, unknown>,
  profileKind: WorkCaseProfileKind,
): string[] {
  if (profileKind === 'invalid') return []
  const definitions = Array.isArray(data.success_criterion_definitions)
    ? data.success_criterion_definitions.filter(isRecord)
    : []
  if (profileKind === 'current') {
    return definitions
      .map((item) => toStringValue(item.statement).trim())
      .filter(Boolean)
  }

  const legacyCriteria = toStringArray(data.success_criteria).map((item) => item.trim()).filter(Boolean)
  if (legacyCriteria.length > 0) return legacyCriteria
  if (typeof data.success_criteria !== 'string') return []

  return data.success_criteria
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*[-*]\s+(?:\[[ xX]\]\s*)?/, '').trim())
    .filter(Boolean)
}

function getWorkCaseCriterionProgress(
  data: Record<string, unknown>,
  profileKind: WorkCaseProfileKind,
): { total: number; done: number } {
  if (profileKind === 'invalid') return { total: 0, done: 0 }
  const definitions = Array.isArray(data.success_criterion_definitions)
    ? data.success_criterion_definitions.filter(isRecord)
    : []
  if (profileKind === 'legacy') {
    const checklist = getChecklistProgress(data.success_criteria)
    return { total: getWorkCaseCriterionStatements(data, profileKind).length, done: checklist.done }
  }

  const satisfied = new Set(
    (Array.isArray(data.success_criterion_results) ? data.success_criterion_results : [])
      .filter(isRecord)
      .filter((item) => toStringValue(item.outcome) === 'satisfied')
      .map((item) => toStringValue(item.criterion_id))
      .filter(Boolean),
  )
  const criterionIds = definitions.map((item) => toStringValue(item.criterion_id)).filter(Boolean)
  return { total: definitions.length, done: criterionIds.filter((id) => satisfied.has(id)).length }
}

function isExecutionItemDone(status: string, currentProfile: boolean): boolean {
  return status === 'completed' || (!currentProfile && status === 'done')
}

function isExecutionItemCancelled(status: string, currentProfile: boolean): boolean {
  return status === 'cancelled' || (!currentProfile && status === 'skipped')
}

function isExecutionItemInProgress(status: string, currentProfile: boolean): boolean {
  return status === 'in_progress' || (!currentProfile && status === 'executing')
}

function getWorkCaseProgressHistoryProjection(
  data: Record<string, unknown>,
  profileKind: WorkCaseProfileKind,
): {
  progressHistoryState: 'missing' | 'valid' | 'invalid'
  progressHistoryCoverage?: 'full' | 'partial'
  progressRound?: number
  progressEventId?: string
} {
  if (profileKind === 'invalid') return { progressHistoryState: 'invalid' }
  if (profileKind === 'legacy') {
    return { progressHistoryState: hasOwn(data, 'progress_history') ? 'invalid' : 'missing' }
  }
  const currentPhase = toStringValue(data.phase)
  const validPhases = new Set([
    'human_plan_confirming', 'executing', 'controller_checking', 'independent_reviewing',
    'closure_preparing', 'human_closure_confirming', 'closed',
  ])
  if (!validPhases.has(currentPhase)) return { progressHistoryState: 'invalid' }
  if (!hasOwn(data, 'progress_history')) {
    const createdTime = parseStrictRfc3339(toStringValue(data.created_at))
    const boundaryTime = parseStrictRfc3339(WORKCASE_PROGRESS_BOUNDARY)
    const progressedPhase = currentPhase !== 'human_plan_confirming'
    if (createdTime === null || boundaryTime === null || (createdTime >= boundaryTime && progressedPhase)) {
      return { progressHistoryState: 'invalid' }
    }
    return { progressHistoryState: 'missing' }
  }
  if (!isRecord(data.progress_history)) return { progressHistoryState: 'invalid' }
  const coverage = data.progress_history.coverage
  if (coverage !== 'full' && coverage !== 'partial') return { progressHistoryState: 'invalid' }
  if (Object.keys(data.progress_history).some((key) => !['coverage', 'entries'].includes(key))) {
    return { progressHistoryState: 'invalid' }
  }
  const entries = Array.isArray(data.progress_history.entries)
    ? data.progress_history.entries
    : []
  if (entries.length === 0 || entries.some((entry) => !isRecord(entry))) {
    return { progressHistoryState: 'invalid' }
  }
  const planVersion = data.plan_version
  const createdAt = toStringValue(data.created_at)
  const updatedAt = toStringValue(data.updated_at)
  const createdTime = parseStrictRfc3339(createdAt)
  const updatedTime = parseStrictRfc3339(updatedAt)
  const boundaryTime = parseStrictRfc3339(WORKCASE_PROGRESS_BOUNDARY)
  if (!Number.isInteger(planVersion) || Number(planVersion) <= 0 || createdTime === null || updatedTime === null) {
    return { progressHistoryState: 'invalid' }
  }
  if (boundaryTime === null || (createdTime >= boundaryTime && coverage !== 'full')) {
    return { progressHistoryState: 'invalid' }
  }

  let previous: Record<string, unknown> | null = null
  let previousTime: bigint | null = null
  for (const [index, rawEntry] of entries.entries()) {
    const entry = rawEntry as Record<string, unknown>
    if (
      Object.keys(entry).some((key) => ![
        'event_id', 'plan_version', 'round', 'phase', 'entered_at', 'transition_kind', 'transition_summary',
      ].includes(key))
      || entry.event_id !== `progress-${String(index + 1).padStart(3, '0')}`
      || !Number.isInteger(entry.plan_version)
      || Number(entry.plan_version) <= 0
      || Number(entry.plan_version) > Number(planVersion)
      || !Number.isInteger(entry.round)
      || Number(entry.round) <= 0
      || !['executing', 'controller_checking', 'independent_reviewing', 'closure_preparing'].includes(String(entry.phase))
      || !['started', 'advanced', 'returned', 'repeated', 'baseline'].includes(String(entry.transition_kind))
      || !toStringValue(entry.transition_summary).trim()
    ) return { progressHistoryState: 'invalid' }
    const enteredTime = parseStrictRfc3339(toStringValue(entry.entered_at))
    if (
      enteredTime === null
      || enteredTime < createdTime
      || enteredTime > updatedTime
      || (previousTime !== null && enteredTime <= previousTime)
    ) return { progressHistoryState: 'invalid' }

    if (previous === null) {
      const firstKind = coverage === 'partial' ? 'baseline' : 'started'
      if (entry.round !== 1 || entry.transition_kind !== firstKind) {
        return { progressHistoryState: 'invalid' }
      }
    } else {
      const previousPlan = Number(previous.plan_version)
      const eventPlan = Number(entry.plan_version)
      if (eventPlan < previousPlan) return { progressHistoryState: 'invalid' }
      if (eventPlan !== previousPlan) {
        if (entry.round !== 1 || entry.transition_kind !== 'started') {
          return { progressHistoryState: 'invalid' }
        }
      } else {
        const ranks: Record<string, number> = {
          executing: 0,
          controller_checking: 1,
          independent_reviewing: 2,
          closure_preparing: 3,
        }
        const previousRound = Number(previous.round)
        const previousRank = ranks[String(previous.phase)]
        const currentRank = ranks[String(entry.phase)]
        const expectedRound = currentRank > previousRank ? previousRound : previousRound + 1
        const expectedKind = currentRank > previousRank
          ? 'advanced'
          : currentRank < previousRank
            ? 'returned'
            : 'repeated'
        if (entry.round !== expectedRound || entry.transition_kind !== expectedKind) {
          return { progressHistoryState: 'invalid' }
        }
      }
    }
    previous = entry
    previousTime = enteredTime
  }

  const latest = entries.at(-1) as Record<string, unknown>
  const round = latest.round
  const progressPhases = new Set(['executing', 'controller_checking', 'independent_reviewing', 'closure_preparing'])
  if (
    latest.plan_version !== planVersion
    || (progressPhases.has(currentPhase) && latest.phase !== currentPhase)
    || (['human_closure_confirming', 'closed'].includes(currentPhase) && latest.phase !== 'closure_preparing')
    || (currentPhase === 'human_plan_confirming' && latest.plan_version === planVersion)
  ) return { progressHistoryState: 'invalid' }
  return {
    progressHistoryState: 'valid',
    progressHistoryCoverage: coverage,
    progressRound: Number(round),
    progressEventId: toStringValue(latest.event_id) || undefined,
  }
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

export async function buildWorkCaseSummaries(workcaseItems: ListedObject[]): Promise<RelatedWorkCaseSummary[]> {
  if (workcaseItems.length === 0) return []

  return workcaseItems.map((item) => {
    const data = item
    const orchestration = isRecord(data.orchestration) ? data.orchestration : {}
    const rawExecutionItems = Array.isArray(data.work_items)
      ? data.work_items
      : Array.isArray(orchestration.execution_items)
        ? orchestration.execution_items
        : []
    const profileKind = getWorkCaseProfileKind(data)
    const currentProfile = profileKind === 'current'
    const strictWorkItems = profileKind !== 'legacy'
    const currentWorkItemsValid = currentProfile && hasValidCurrentWorkItems(data.work_items)
    const projectedExecutionItems = rawExecutionItems
      .map((executionItem, index) => toExecutionItemSummary(executionItem, item, index, strictWorkItems))
      .filter((executionItem): executionItem is RelatedObjectSummary => Boolean(executionItem))
    const uniqueItemIds = new Set(projectedExecutionItems.map((executionItem) => executionItem.id))
    const executionItemsProjectionValid = profileKind === 'legacy' || (currentProfile
      && currentWorkItemsValid
      && projectedExecutionItems.length === rawExecutionItems.length
      && uniqueItemIds.size === projectedExecutionItems.length)
    const executionItems = executionItemsProjectionValid ? projectedExecutionItems : []
    const successCriteriaProgress = getWorkCaseCriterionProgress(data, profileKind)
    const successCriteria = getWorkCaseCriterionStatements(data, profileKind)
    const progressHistory = getWorkCaseProgressHistoryProjection(data, profileKind)

    return {
      ...toRelatedSummary(item, 'workcase'),
      executionItems: sortExecutionItems(executionItems),
      executionItemsProjectionValid,
      executionItemTotal: executionItems.length,
      executionItemDone: executionItems.filter((executionItem) => isExecutionItemDone(executionItem.status, currentProfile)).length,
      executionItemCancelled: executionItems.filter((executionItem) => isExecutionItemCancelled(executionItem.status, currentProfile)).length,
      executionItemBlocked: executionItems.filter((executionItem) => executionItem.status === 'blocked').length,
      executionItemOpen: countOpenExecutionItems(executionItems),
      executionItemsInProgress: executionItems.filter((executionItem) => isExecutionItemInProgress(executionItem.status, currentProfile)),
      ...progressHistory,
      successCriteriaTotal: successCriteriaProgress.total,
      successCriteriaDone: successCriteriaProgress.done,
      successCriteria,
      hasSuccessCriteria: successCriteriaProgress.total > 0,
      hasPlanConfirmedAt: hasContent(data.execution_approval) || hasContent(data.plan_confirmed_at),
      hasClosureRequestedAt: toStringValue(data.phase) === 'human_closure_confirming' || hasContent(data.closure_requested_at) || hasContent(data.review_requested_at),
      hasVerificationEvidence: hasContent(data.controller_check_summary) || hasContent(data.validation_summary),
      hasClosureEvidence: hasContent(data.validation_summary) || hasContent(data.closure_evidence),
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
      executionItemsProjectionValid: summary.executionItemsProjectionValid ?? true,
      executionItemTotal: summary.executionItemTotal ?? 0,
      executionItemDone: summary.executionItemDone ?? 0,
      executionItemCancelled: summary.executionItemCancelled ?? 0,
      executionItemBlocked: summary.executionItemBlocked ?? 0,
      executionItemOpen: summary.executionItemOpen ?? 0,
      executionItemsInProgress: summary.executionItemsInProgress ?? [],
      progressHistoryCoverage: summary.progressHistoryCoverage,
      progressHistoryState: summary.progressHistoryState,
      progressRound: summary.progressRound,
      progressEventId: summary.progressEventId,
      successCriteriaTotal: summary.successCriteriaTotal ?? 0,
      successCriteriaDone: summary.successCriteriaDone ?? 0,
      successCriteria: summary.successCriteria ?? [],
      hasSuccessCriteria: summary.hasSuccessCriteria,
      hasPlanConfirmedAt: summary.hasPlanConfirmedAt,
      hasClosureRequestedAt: summary.hasClosureRequestedAt,
      hasVerificationEvidence: summary.hasVerificationEvidence,
      hasClosureEvidence: summary.hasClosureEvidence,
      closure_evidence: toStringValue(item.disposition_summary) || toStringValue(item.validation_summary) || toStringValue(item.closure_evidence) || undefined,
      executionItemByStatus: countByStatus(summary.executionItems ?? []),
    }
  })
}

async function enrichPitfalls(items: ListedObject[]): Promise<ListedObject[]> {
  return items.map((item) => {
    const data = item
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
    res.status(500).json(result)
    return
  }

  const rawItems = getRawItems(result)
  const allItems = getResultItems(result)
  const items = type === 'workcase'
    ? allItems.filter((item) => (!progress || item.progress_group === progress) && (!priority || item.priority === priority))
    : type === 'spark'
      ? allItems.filter((item) => matchesSparkListFilter(item, status, priority))
      : allItems
  let enrichedItems = items
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
  if (isRecord(result.data) && type === 'workcase') {
    enrichedItems = await enrichWorkCases(items)
  }
  if (isRecord(result.data) && type === 'adr') {
    enrichedItems = await enrichAdrs(items)
  }
  if (isRecord(result.data) && type === 'pitfall') {
    enrichedItems = await enrichPitfalls(items)
  }
  if (isRecord(result.data)) {
    result.data.items = type === 'spark'
      ? rawItems
        .map(normalizeItem)
        .filter((item): item is ListedObject => Boolean(item))
        .filter((item) => matchesSparkListFilter(item, status, priority))
        .sort((left, right) => String(right.updated || '').localeCompare(String(left.updated || '')))
      : sortByUpdatedDesc(enrichedItems)
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
  if (isRecord(result.data) && typeof result.data.fact_type_key === 'string' && result.data.fact_type_key !== type) {
    res.status(404).json({
      ok: false,
      error: `Object not found for type ${type}: ${id}`,
      stderr: '',
      exitCode: 1,
    })
    return
  }

  // WorkCase 派生阅读材料：仅保留旧兼容输入项；事实对象证据以自然语言字段表达。
  if (type === 'workcase' && result.data) {
    const relatedDocsSet = new Set<string>()
    const relatedAdrsSet = new Set<string>()
    const relatedSparksSet = new Set<string>()
    const relatedPitfallsSet = new Set<string>()
    const executionRefsSet = new Set<string>()
    const orchestration = isRecord(result.data.orchestration) ? result.data.orchestration : {}
    const executionItems = Array.isArray(result.data.work_items)
      ? result.data.work_items
      : Array.isArray(orchestration.execution_items)
        ? orchestration.execution_items
        : []

    addStringArray(relatedDocsSet, result.data.related_docs)
    addStringArray(relatedAdrsSet, result.data.related_adrs)
    addStringArray(relatedSparksSet, result.data.related_sparks)
    addStringArray(relatedPitfallsSet, result.data.related_pitfalls)

    for (const executionItem of executionItems) {
      if (!isRecord(executionItem)) continue
      addStringArray(executionRefsSet, executionItem.input_refs)
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
    const data = item
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
