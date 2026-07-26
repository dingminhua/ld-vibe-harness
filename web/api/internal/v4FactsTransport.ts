import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { TextDecoder } from 'node:util'
import { fileURLToPath } from 'node:url'

const REQUEST_LIMIT = 12 * 1024 * 1024
const RESPONSE_LIMIT = 32 * 1024 * 1024
const STDERR_LIMIT = 64 * 1024
const RESPONSE_FIELDS = new Set([
  'protocol_version',
  'operation',
  'status',
  'result',
  'error',
  'completion_unknown',
])
const LIST_RESULT_FIELDS = new Set([
  'status', 'items', 'object_problems', 'structural_problems', 'governance_resolution', 'observed_at',
])
const DETAIL_RESULT_FIELDS = new Set([
  'status', 'item', 'problems', 'coverage_status', 'governance_resolution', 'observed_at',
])
const ITEM_FIELDS = new Set([
  'object_ref', 'canonical_path', 'absolute_path', 'carrier', 'check_status',
  'fact_object', 'content_fingerprint', 'issues',
])
const LIST_STATUSES = new Set(['complete', 'partial', 'unavailable'])
const DETAIL_STATUSES = new Set(['ok', 'not_found', 'invalid', 'unavailable'])
const COMMON_ERROR_STATUSES = new Set(['invalid', 'unavailable', 'error'])
const ISSUE_CATEGORIES = new Set([
  'location', 'git-traceability', 'parse', 'schema', 'identity', 'reference', 'relation',
])

export const V4_FACTS_MACHINE_SCRIPT = fileURLToPath(new URL(
  '../../python/ldvh_web_facts/machine.py',
  import.meta.url,
))

export const V4_FACTS_OPERATIONS = [
  'list-sparks',
  'read-spark',
  'list-workcases',
  'read-workcase',
] as const

export type V4FactsOperation = (typeof V4_FACTS_OPERATIONS)[number]

type V4FactsOperationKind = 'list' | 'read'
type V4FactsMachineFactType = 'spark' | 'workcase'

interface V4FactsOperationDescriptor {
  kind: V4FactsOperationKind
  factTypeKey: V4FactsMachineFactType
  objectIdPattern: RegExp
  canonicalDirectory: string
  carrier: 'yaml'
}

interface V4FactsObjectRef {
  governed_project_id: string
  fact_type_key: string
  object_id: string
}

const OPERATION_DESCRIPTORS: Record<V4FactsOperation, V4FactsOperationDescriptor> = {
  'list-sparks': {
    kind: 'list', factTypeKey: 'spark', objectIdPattern: /^spark-[0-9]{4,}$/,
    canonicalDirectory: 'ldvh-base/sparks', carrier: 'yaml',
  },
  'read-spark': {
    kind: 'read', factTypeKey: 'spark', objectIdPattern: /^spark-[0-9]{4,}$/,
    canonicalDirectory: 'ldvh-base/sparks', carrier: 'yaml',
  },
  'list-workcases': {
    kind: 'list', factTypeKey: 'workcase', objectIdPattern: /^workcase-[0-9]{4,}$/,
    canonicalDirectory: 'ldvh-base/workcases', carrier: 'yaml',
  },
  'read-workcase': {
    kind: 'read', factTypeKey: 'workcase', objectIdPattern: /^workcase-[0-9]{4,}$/,
    canonicalDirectory: 'ldvh-base/workcases', carrier: 'yaml',
  },
}

export interface V4FactsScope {
  workspace_root: string
  worktree_locator: string
  expected_governed_project_id: string
}

export interface V4FactsMachineRequest {
  protocol_version: 1
  operation: V4FactsOperation
  scope: V4FactsScope
  arguments: Record<string, unknown>
}

export interface V4FactsMachineResponse {
  protocol_version: 1
  operation: V4FactsOperation | null
  status: string
  result: unknown
  error: string | null
  completion_unknown: boolean
}

export interface SpawnedProcess {
  stdin: NodeJS.WritableStream & { destroy(error?: Error): void }
  stdout: NodeJS.ReadableStream & { destroy(error?: Error): void }
  stderr: NodeJS.ReadableStream & { destroy(error?: Error): void }
  once(event: 'spawn', listener: () => void): this
  once(event: 'error', listener: (error: Error) => void): this
  once(event: 'close', listener: (code: number | null, signal: NodeJS.Signals | null) => void): this
  kill(signal?: NodeJS.Signals): boolean
  unref(): void
}

export type SpawnProcess = (
  command: string,
  args: readonly string[],
  options: {
    cwd: string
    env: NodeJS.ProcessEnv
    shell: false
    windowsHide: true
    stdio: ['pipe', 'pipe', 'pipe']
  },
) => SpawnedProcess

export interface V4FactsTransportOptions {
  pythonExecutable: string
  timeoutMs?: number
  spawnProcess?: SpawnProcess
}

export class V4FactsTransportError extends Error {
  readonly code: string
  readonly completionUnknown: boolean
  readonly diagnostic: string

  constructor(code: string, message: string, options: { completionUnknown?: boolean; diagnostic?: string } = {}) {
    super(message)
    this.name = 'V4FactsTransportError'
    this.code = code
    this.completionUnknown = options.completionUnknown ?? false
    this.diagnostic = options.diagnostic ?? ''
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}

function hasExactFields(value: Record<string, unknown>, fields: Set<string>): boolean {
  return Object.keys(value).length === fields.size && Object.keys(value).every((field) => fields.has(field))
}

function operationDescriptor(value: unknown): V4FactsOperationDescriptor | null {
  if (typeof value !== 'string'
    || !Object.prototype.hasOwnProperty.call(OPERATION_DESCRIPTORS, value)) return null
  return OPERATION_DESCRIPTORS[value as V4FactsOperation]
}

function isObjectRef(
  value: unknown,
  descriptor: V4FactsOperationDescriptor,
  expectedGovernedProjectId: string,
): value is V4FactsObjectRef {
  if (!isRecord(value)) return false
  const keys = Object.keys(value).sort().join(',')
  return keys === 'fact_type_key,governed_project_id,object_id'
    && value.governed_project_id === expectedGovernedProjectId
    && value.fact_type_key === descriptor.factTypeKey
    && typeof value.object_id === 'string'
    && descriptor.objectIdPattern.test(value.object_id)
}

function isIssue(value: unknown): boolean {
  return isRecord(value)
    && Object.keys(value).sort().join(',') === 'category,field_path,summary'
    && typeof value.category === 'string'
    && ISSUE_CATEGORIES.has(value.category)
    && (value.field_path === null
      || (typeof value.field_path === 'string' && value.field_path.trim().length > 0))
    && typeof value.summary === 'string'
    && value.summary.trim().length > 0
}

function isRfc3339Timestamp(value: unknown): value is string {
  if (typeof value !== 'string') return false
  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$/,
  )
  if (!match) return false
  const [, yearText, monthText, dayText, hourText, minuteText, secondText, offsetSign, offsetHourText, offsetMinuteText] = match
  const year = Number(yearText)
  const month = Number(monthText)
  const day = Number(dayText)
  const hour = Number(hourText)
  const minute = Number(minuteText)
  const second = Number(secondText)
  if (year < 1 || month < 1 || month > 12 || hour > 23 || minute > 59 || second > 59) return false
  const isLeapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
  if (day < 1 || day > daysInMonth) return false
  if (offsetSign !== undefined
    && (Number(offsetHourText) > 23 || Number(offsetMinuteText) > 59)) return false
  if (offsetSign === '-' && Number(offsetHourText) === 0 && Number(offsetMinuteText) === 0) return false
  return true
}

function isStructuralProblem(value: unknown, descriptor: V4FactsOperationDescriptor): boolean {
  const canonicalPath = isRecord(value) ? value.canonical_path : null
  return isRecord(value)
    && Object.keys(value).sort().join(',') === 'canonical_path,check_status,fact_type_key,issues'
    && value.fact_type_key === descriptor.factTypeKey
    && typeof canonicalPath === 'string'
    && !canonicalPath.includes('\\')
    && !canonicalPath.startsWith('/')
    && canonicalPath.split('/').every((part) => part !== '' && part !== '.' && part !== '..')
    && path.posix.normalize(canonicalPath) === canonicalPath
    && (canonicalPath === descriptor.canonicalDirectory
      || canonicalPath.startsWith(`${descriptor.canonicalDirectory}/`))
    && value.check_status === 'unavailable'
    && Array.isArray(value.issues)
    && value.issues.length > 0
    && value.issues.every(isIssue)
}

const SOURCE_REFERENCE_FIELDS = new Set(['kind', 'locator', 'version', 'observed_at', 'details'])
const GOVERNANCE_RESULT_FIELDS = new Set([
  'workspace_root', 'config_path', 'config_status', 'scope_status', 'object_resolutions',
  'registered_project_candidates', 'source_refs',
])
const OBJECT_RESOLUTION_FIELDS = new Set([
  'locator_index', 'locator', 'resolved_identity', 'identity_evidence', 'source', 'status',
  'governed_project_id', 'registered_project_path', 'governed_via', 'git_worktree_root',
  'git_common_dir', 'source_refs', 'unknown_reason',
])
const REGISTERED_PROJECT_CANDIDATE_FIELDS = new Set([
  'governed_project_id', 'registered_project_path', 'git_worktree_root', 'git_common_dir', 'source_refs',
])
const SOURCE_REFERENCE_REQUIRED_FIELDS = new Set(['kind', 'locator', 'observed_at', 'details'])
const PATH_OBSERVATION_DETAILS_FIELDS = new Set([
  'locator_index', 'original_locator', 'base', 'exists', 'uses_existing_ancestor',
])
const GIT_IDENTITY_DETAILS_FIELDS = new Set(['locator_index', 'git_common_dir'])
const REGISTERED_GIT_IDENTITY_DETAILS_FIELDS = new Set([
  'project_id', 'status', 'git_worktree_root', 'git_common_dir',
])
const CONFIGURATION_DETAILS_FIELDS = new Set(['discovery_bases'])
const CONFIGURATION_DISCOVERY_BASIS_FIELDS = new Set(['kind', 'start'])
const CONFIGURATION_DISCOVERY_KINDS = new Set([
  'explicit_workspace_root', 'path', 'git.common_dir_parent',
])

function hasSourceReferenceFields(value: Record<string, unknown>): boolean {
  const keys = Object.keys(value)
  return SOURCE_REFERENCE_REQUIRED_FIELDS.size <= keys.length
    && keys.length <= SOURCE_REFERENCE_FIELDS.size
    && keys.every((field) => SOURCE_REFERENCE_FIELDS.has(field))
    && [...SOURCE_REFERENCE_REQUIRED_FIELDS].every((field) => (
      Object.prototype.hasOwnProperty.call(value, field)
    ))
}

function hasPathObservationDetails(value: unknown): boolean {
  return isRecord(value)
    && hasExactFields(value, PATH_OBSERVATION_DETAILS_FIELDS)
    && Number.isInteger(value.locator_index)
    && Number(value.locator_index) >= 0
    && typeof value.original_locator === 'string'
    && value.original_locator.trim().length > 0
    && typeof value.base === 'string'
    && value.base.trim().length > 0
    && typeof value.exists === 'boolean'
    && typeof value.uses_existing_ancestor === 'boolean'
}

function hasGitIdentityDetails(value: unknown): boolean {
  return isRecord(value)
    && hasExactFields(value, GIT_IDENTITY_DETAILS_FIELDS)
    && Number.isInteger(value.locator_index)
    && Number(value.locator_index) >= 0
    && typeof value.git_common_dir === 'string'
    && path.isAbsolute(value.git_common_dir)
}

function hasRegisteredGitIdentityDetails(value: unknown): boolean {
  return isRecord(value)
    && hasExactFields(value, REGISTERED_GIT_IDENTITY_DETAILS_FIELDS)
    && typeof value.project_id === 'string'
    && value.project_id.trim().length > 0
    && value.status === 'git_worktree'
    && typeof value.git_worktree_root === 'string'
    && path.isAbsolute(value.git_worktree_root)
    && typeof value.git_common_dir === 'string'
    && path.isAbsolute(value.git_common_dir)
}

function hasConfigurationDetails(value: unknown): boolean {
  if (!isRecord(value)
    || !hasExactFields(value, CONFIGURATION_DETAILS_FIELDS)
    || !Array.isArray(value.discovery_bases)
    || value.discovery_bases.length === 0) return false
  return value.discovery_bases.every((basis) => (
    isRecord(basis)
      && hasExactFields(basis, CONFIGURATION_DISCOVERY_BASIS_FIELDS)
      && typeof basis.kind === 'string'
      && CONFIGURATION_DISCOVERY_KINDS.has(basis.kind)
      && typeof basis.start === 'string'
      && path.isAbsolute(basis.start)
  ))
}

function isSourceReference(value: unknown): value is Record<string, unknown> {
  if (!isRecord(value)
    || !hasSourceReferenceFields(value)
    || typeof value.kind !== 'string'
    || typeof value.locator !== 'string'
    || value.locator.trim().length === 0
    || (value.version !== undefined
      && (typeof value.version !== 'string' || value.version.trim().length === 0))
    || !isRfc3339Timestamp(value.observed_at)) return false
  if (value.kind === 'path_observation') return hasPathObservationDetails(value.details)
  if (value.kind === 'git_identity_observation') return hasGitIdentityDetails(value.details)
  if (value.kind === 'registered_project_git_identity') {
    return hasRegisteredGitIdentityDetails(value.details)
  }
  if (value.kind === 'governed_projects_configuration') return hasConfigurationDetails(value.details)
  return false
}

function sourceReferenceArray(value: unknown): Record<string, unknown>[] | null {
  return Array.isArray(value) && value.length > 0 && value.every(isSourceReference)
    ? value
    : null
}

function realPathOrResolved(value: string): string {
  try {
    return fs.realpathSync.native(value)
  } catch {
    return path.resolve(value)
  }
}

function normalizedPathEqual(left: string, right: string): boolean {
  return realPathOrResolved(left) === realPathOrResolved(right)
}

function isExpectedConfigurationSource(
  source: Record<string, unknown>,
  expectedConfigPath: string,
  workspaceRoot: string,
): boolean {
  if (source.kind !== 'governed_projects_configuration'
    || typeof source.locator !== 'string'
    || !normalizedPathEqual(source.locator, expectedConfigPath)
    || !isRecord(source.details)
    || !Array.isArray(source.details.discovery_bases)) return false
  return source.details.discovery_bases.some((basis) => (
    isRecord(basis)
      && basis.kind === 'explicit_workspace_root'
      && typeof basis.start === 'string'
      && normalizedPathEqual(basis.start, workspaceRoot)
  ))
}

function hasExpectedConfigurationSources(
  sources: Record<string, unknown>[],
  expectedConfigPath: string,
  workspaceRoot: string,
): boolean {
  const configurationSources = sources.filter((source) => (
    source.kind === 'governed_projects_configuration'
  ))
  return configurationSources.length > 0 && configurationSources.every((source) => (
    isExpectedConfigurationSource(source, expectedConfigPath, workspaceRoot)
  ))
}

function isExpectedPathObservationSource(
  source: Record<string, unknown>,
  worktreeLocator: string,
): boolean {
  return source.kind === 'path_observation'
    && typeof source.locator === 'string'
    && normalizedPathEqual(source.locator, worktreeLocator)
    && isRecord(source.details)
    && source.details.locator_index === 0
    && typeof source.details.original_locator === 'string'
    && normalizedPathEqual(source.details.original_locator, worktreeLocator)
    && typeof source.details.base === 'string'
    && normalizedPathEqual(source.details.base, path.dirname(worktreeLocator))
    && source.details.exists === true
    && source.details.uses_existing_ancestor === false
}

function hasExpectedPathObservationSources(
  sources: Record<string, unknown>[],
  worktreeLocator: string,
): boolean {
  const pathSources = sources.filter((source) => source.kind === 'path_observation')
  return pathSources.length > 0 && pathSources.every((source) => (
    isExpectedPathObservationSource(source, worktreeLocator)
  ))
}

function compareUnicodeCodePoints(left: string, right: string): number {
  const leftPoints = Array.from(left, (value) => value.codePointAt(0) ?? -1)
  const rightPoints = Array.from(right, (value) => value.codePointAt(0) ?? -1)
  const sharedLength = Math.min(leftPoints.length, rightPoints.length)
  for (let index = 0; index < sharedLength; index += 1) {
    const difference = leftPoints[index] - rightPoints[index]
    if (difference !== 0) return difference
  }
  return leftPoints.length - rightPoints.length
}

function isWithinPath(candidate: string, root: string): boolean {
  const relative = path.relative(realPathOrResolved(root), realPathOrResolved(candidate))
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative))
}

function resolvedWorktreeRoot(
  value: unknown,
  request: V4FactsMachineRequest,
): string | null {
  const governanceSources = isRecord(value) ? sourceReferenceArray(value.source_refs) : null
  const expectedConfigPath = path.join(
    request.scope.workspace_root,
    'LDVH-GOVERNED-PROJECTS.yaml',
  )
  if (!isRecord(value)
    || !hasExactFields(value, GOVERNANCE_RESULT_FIELDS)
    || !normalizedPathEqual(String(value.workspace_root ?? ''), request.scope.workspace_root)
    || typeof value.config_path !== 'string'
    || !path.isAbsolute(value.config_path)
    || !normalizedPathEqual(value.config_path, expectedConfigPath)
    || value.config_status !== 'valid'
    || value.scope_status !== 'governed_single'
    || governanceSources === null
    || !Array.isArray(value.registered_project_candidates)
    || !Array.isArray(value.object_resolutions)
    || value.object_resolutions.length !== 1) {
    return null
  }

  if (!hasExpectedConfigurationSources(
    governanceSources,
    expectedConfigPath,
    request.scope.workspace_root,
  ) || !hasExpectedPathObservationSources(
    governanceSources,
    request.scope.worktree_locator,
  )) return null

  const resolution = value.object_resolutions[0]
  const identityEvidence = isRecord(resolution) ? sourceReferenceArray(resolution.identity_evidence) : null
  const resolutionSources = isRecord(resolution) ? sourceReferenceArray(resolution.source_refs) : null
  if (!isRecord(resolution)
    || !hasExactFields(resolution, OBJECT_RESOLUTION_FIELDS)
    || resolution.locator_index !== 0
    || typeof resolution.locator !== 'string'
    || !normalizedPathEqual(resolution.locator, request.scope.worktree_locator)
    || resolution.source !== 'explicit_locator'
    || resolution.status !== 'governed'
    || resolution.governed_project_id !== request.scope.expected_governed_project_id
    || !['path', 'git.common_dir'].includes(String(resolution.governed_via))
    || resolution.unknown_reason !== null
    || typeof resolution.resolved_identity !== 'string'
    || !path.isAbsolute(resolution.resolved_identity)
    || !normalizedPathEqual(resolution.resolved_identity, request.scope.worktree_locator)
    || typeof resolution.git_worktree_root !== 'string'
    || !path.isAbsolute(resolution.git_worktree_root)
    || typeof resolution.git_common_dir !== 'string'
    || !path.isAbsolute(resolution.git_common_dir)
    || typeof resolution.registered_project_path !== 'string'
    || !path.isAbsolute(resolution.registered_project_path)
    || identityEvidence === null
    || resolutionSources === null
    || !hasExpectedConfigurationSources(
      identityEvidence,
      expectedConfigPath,
      request.scope.workspace_root,
    )
    || !hasExpectedConfigurationSources(
      resolutionSources,
      expectedConfigPath,
      request.scope.workspace_root,
    )
    || !hasExpectedPathObservationSources(
      identityEvidence,
      request.scope.worktree_locator,
    )
    || !hasExpectedPathObservationSources(
      resolutionSources,
      request.scope.worktree_locator,
    )
    || !isWithinPath(resolution.resolved_identity, resolution.git_worktree_root)) {
    return null
  }

  const gitEvidence = identityEvidence.find((source) => (
    source.kind === 'git_identity_observation'
      && typeof source.locator === 'string'
      && normalizedPathEqual(source.locator, resolution.git_worktree_root as string)
      && isRecord(source.details)
      && source.details.locator_index === 0
      && typeof source.details.git_common_dir === 'string'
      && normalizedPathEqual(source.details.git_common_dir, resolution.git_common_dir as string)
  ))
  if (!gitEvidence) return null

  const resolutionGitSource = resolutionSources.find((source) => (
    source.kind === 'git_identity_observation'
      && typeof source.locator === 'string'
      && normalizedPathEqual(source.locator, resolution.git_worktree_root as string)
      && isRecord(source.details)
      && source.details.locator_index === 0
      && typeof source.details.git_common_dir === 'string'
      && normalizedPathEqual(source.details.git_common_dir, resolution.git_common_dir as string)
  ))
  const resolutionConfigurationSource = resolutionSources.find((source) => (
    isExpectedConfigurationSource(source, expectedConfigPath, request.scope.workspace_root)
  ))
  if (!resolutionGitSource || !resolutionConfigurationSource) return null

  const candidates = value.registered_project_candidates
  if (!candidates.every((candidate) => {
    if (!isRecord(candidate)
      || !hasExactFields(candidate, REGISTERED_PROJECT_CANDIDATE_FIELDS)
      || typeof candidate.governed_project_id !== 'string'
      || candidate.governed_project_id.trim().length === 0
      || typeof candidate.registered_project_path !== 'string'
      || !path.isAbsolute(candidate.registered_project_path)
      || typeof candidate.git_worktree_root !== 'string'
      || !path.isAbsolute(candidate.git_worktree_root)
      || typeof candidate.git_common_dir !== 'string'
      || !path.isAbsolute(candidate.git_common_dir)) return false
    const sources = sourceReferenceArray(candidate.source_refs)
    if (sources === null || !hasExpectedConfigurationSources(
      sources,
      expectedConfigPath,
      request.scope.workspace_root,
    )) return false
    const configuration = sources.find((source) => (
      isExpectedConfigurationSource(source, expectedConfigPath, request.scope.workspace_root)
    ))
    const identity = sources.find((source) => (
      source.kind === 'registered_project_git_identity'
        && typeof source.locator === 'string'
        && normalizedPathEqual(source.locator, candidate.registered_project_path as string)
        && isRecord(source.details)
        && source.details.project_id === candidate.governed_project_id
        && source.details.status === 'git_worktree'
        && typeof source.details.git_worktree_root === 'string'
        && normalizedPathEqual(source.details.git_worktree_root, candidate.git_worktree_root as string)
        && typeof source.details.git_common_dir === 'string'
        && normalizedPathEqual(source.details.git_common_dir, candidate.git_common_dir as string)
    ))
    return Boolean(configuration && identity)
  })) {
    return null
  }
  const candidateProjectIds = candidates.map((candidate) => (
    isRecord(candidate) ? String(candidate.governed_project_id) : ''
  ))
  if (candidateProjectIds.some((current, index) => (
    index > 0 && compareUnicodeCodePoints(candidateProjectIds[index - 1], current) > 0
  ))) {
    return null
  }
  const uniqueCandidateFields = [
    'governed_project_id', 'registered_project_path', 'git_common_dir',
  ] as const
  if (uniqueCandidateFields.some((field) => (
    new Set(candidates.map((candidate) => (
      field === 'governed_project_id'
        ? String(candidate[field])
        : realPathOrResolved(String(candidate[field]))
    ))).size !== candidates.length
  ))) {
    return null
  }
  const expectedCandidates = candidates.filter((candidate) => (
    isRecord(candidate)
      && candidate.governed_project_id === request.scope.expected_governed_project_id
  ))
  if (expectedCandidates.length !== 1) return null
  const candidate = expectedCandidates[0]
  const candidateSources = sourceReferenceArray(candidate.source_refs)
  if (typeof candidate.registered_project_path !== 'string'
    || typeof candidate.git_worktree_root !== 'string'
    || typeof candidate.git_common_dir !== 'string'
    || !path.isAbsolute(candidate.registered_project_path)
    || !path.isAbsolute(candidate.git_worktree_root)
    || !path.isAbsolute(candidate.git_common_dir)
    || !normalizedPathEqual(candidate.registered_project_path, resolution.registered_project_path)
    || !normalizedPathEqual(candidate.git_common_dir, resolution.git_common_dir)
    || (resolution.governed_via === 'path'
      && !normalizedPathEqual(candidate.git_worktree_root, resolution.git_worktree_root))
    || candidateSources === null) {
    return null
  }
  const candidateConfiguration = candidateSources.find((source) => (
    isExpectedConfigurationSource(source, expectedConfigPath, request.scope.workspace_root)
  ))
  const candidateGitIdentity = candidateSources.find((source) => (
    source.kind === 'registered_project_git_identity'
      && typeof source.locator === 'string'
      && normalizedPathEqual(source.locator, candidate.registered_project_path as string)
      && isRecord(source.details)
      && source.details.project_id === request.scope.expected_governed_project_id
      && source.details.status === 'git_worktree'
      && typeof source.details.git_worktree_root === 'string'
      && normalizedPathEqual(source.details.git_worktree_root, candidate.git_worktree_root as string)
      && typeof source.details.git_common_dir === 'string'
      && normalizedPathEqual(source.details.git_common_dir, candidate.git_common_dir as string)
  ))
  if (!candidateConfiguration || !candidateGitIdentity) return null
  return realPathOrResolved(resolution.git_worktree_root)
}

function isReadItem(
  value: unknown,
  descriptor: V4FactsOperationDescriptor,
  expectedGovernedProjectId: string,
  worktreeRoot: string,
  expectedObjectId?: string,
): value is Record<string, unknown> {
  if (!isRecord(value)) return false
  const objectRef = value.object_ref
  if (
    !hasExactFields(value, ITEM_FIELDS)
    || !isObjectRef(objectRef, descriptor, expectedGovernedProjectId)
    || (expectedObjectId !== undefined && objectRef.object_id !== expectedObjectId)
    || value.canonical_path !== `${descriptor.canonicalDirectory}/${objectRef.object_id}.yaml`
    || value.absolute_path !== path.resolve(
      worktreeRoot,
      descriptor.canonicalDirectory,
      `${objectRef.object_id}.yaml`,
    )
    || value.carrier !== descriptor.carrier
    || !['mechanically_valid', 'invalid', 'not_found', 'unavailable'].includes(String(value.check_status))
    || !Array.isArray(value.issues)
    || !value.issues.every(isIssue)) {
    return false
  }

  if (value.check_status !== 'mechanically_valid') {
    return value.fact_object === null
      && value.content_fingerprint === null
      && value.issues.length > 0
  }

  const factObject = value.fact_object
  return isRecord(factObject)
    && factObject.fact_type_key === objectRef.fact_type_key
    && factObject.object_id === objectRef.object_id
    && typeof value.content_fingerprint === 'string'
    && /^[0-9a-f]{64}$/.test(value.content_fingerprint)
    && value.issues.length === 0
}

function isMechanicallyValidItem(
  value: unknown,
  descriptor: V4FactsOperationDescriptor,
  expectedGovernedProjectId: string,
  worktreeRoot: string,
  expectedObjectId?: string,
): value is Record<string, unknown> {
  return isReadItem(value, descriptor, expectedGovernedProjectId, worktreeRoot, expectedObjectId)
    && value.check_status === 'mechanically_valid'
}

function isProblemItem(
  value: unknown,
  descriptor: V4FactsOperationDescriptor,
  expectedGovernedProjectId: string,
  worktreeRoot: string,
  expectedObjectId?: string,
): value is Record<string, unknown> {
  return isReadItem(value, descriptor, expectedGovernedProjectId, worktreeRoot, expectedObjectId)
    && value.check_status !== 'mechanically_valid'
}

function hasUniqueReadItemIdentities(...groups: unknown[][]): boolean {
  const identities: string[] = []
  for (const group of groups) {
    for (const item of group) {
      if (!isRecord(item) || !isRecord(item.object_ref)) return false
      const project = item.object_ref.governed_project_id
      const factType = item.object_ref.fact_type_key
      const objectId = item.object_ref.object_id
      if (typeof project !== 'string' || typeof factType !== 'string' || typeof objectId !== 'string') {
        return false
      }
      identities.push(`${project}\u0000${factType}\u0000${objectId}`)
    }
  }
  return new Set(identities).size === identities.length
}

function validateOperationResult(
  value: Record<string, unknown>,
  request: V4FactsMachineRequest,
): boolean {
  const descriptor = OPERATION_DESCRIPTORS[request.operation]
  const expectedGovernedProjectId = request.scope.expected_governed_project_id
  const worktreeRoot = resolvedWorktreeRoot(value.governance_resolution, request)
  if (worktreeRoot === null || !isRfc3339Timestamp(value.observed_at)) return false
  if (descriptor.kind === 'list') {
    const items = value.items
    const objectProblems = value.object_problems
    const structuralProblems = value.structural_problems
    const completedProblems = Array.isArray(objectProblems)
      ? objectProblems.filter((problem) => isRecord(problem)
        && (problem.check_status === 'invalid' || problem.check_status === 'not_found'))
      : []
    const unavailableProblems = Array.isArray(objectProblems)
      ? objectProblems.filter((problem) => isRecord(problem) && problem.check_status === 'unavailable')
      : []
    const validShape = hasExactFields(value, LIST_RESULT_FIELDS)
      && LIST_STATUSES.has(String(value.status))
      && Array.isArray(items)
      && items.every((item) => isMechanicallyValidItem(
        item, descriptor, expectedGovernedProjectId, worktreeRoot,
      ))
      && Array.isArray(objectProblems)
      && objectProblems.every((item) => isProblemItem(
        item, descriptor, expectedGovernedProjectId, worktreeRoot,
      ))
      && Array.isArray(structuralProblems)
      && structuralProblems.every((problem) => isStructuralProblem(problem, descriptor))
      && hasUniqueReadItemIdentities(items, objectProblems)
    if (!validShape) return false
    if (value.status === 'complete') {
      return structuralProblems.length === 0 && unavailableProblems.length === 0
    }
    if (value.status === 'partial') {
      return (structuralProblems.length > 0 || unavailableProblems.length > 0)
        && (items.length > 0 || completedProblems.length > 0)
    }
    return items.length === 0
      && completedProblems.length === 0
      && (unavailableProblems.length > 0 || structuralProblems.length > 0)
  }
  if (descriptor.kind === 'read') {
    const item = value.item
    const problems = value.problems
    const requestedObjectId = request.arguments.object_id
    if (typeof requestedObjectId !== 'string') return false
    const validShape = hasExactFields(value, DETAIL_RESULT_FIELDS)
      && DETAIL_STATUSES.has(String(value.status))
      && (item === null || isMechanicallyValidItem(
        item,
        descriptor,
        expectedGovernedProjectId,
        worktreeRoot,
        requestedObjectId,
      ))
      && Array.isArray(problems)
      && problems.every((problem) => isProblemItem(
        problem,
        descriptor,
        expectedGovernedProjectId,
        worktreeRoot,
        requestedObjectId,
      ))
      && LIST_STATUSES.has(String(value.coverage_status))
    if (!validShape) return false
    if (value.status === 'ok') {
      return isMechanicallyValidItem(
        item,
        descriptor,
        expectedGovernedProjectId,
        worktreeRoot,
        requestedObjectId,
      ) && problems.length === 0 && value.coverage_status === 'complete'
    }
    if (value.status === 'not_found') {
      return item === null
        && problems.length === 1
        && problems[0].check_status === 'not_found'
        && value.coverage_status === 'complete'
    }
    if (value.status === 'invalid') {
      return item === null
        && problems.length === 1
        && isProblemItem(
          problems[0], descriptor, expectedGovernedProjectId, worktreeRoot, requestedObjectId,
        )
        && problems[0].check_status === 'invalid'
        && value.coverage_status === 'complete'
    }
    return item === null
      && problems.length === 1
      && problems[0].check_status === 'unavailable'
      && value.coverage_status === 'unavailable'
  }
  return false
}

function safeEnvironment(): NodeJS.ProcessEnv {
  const names = [
    'PATH',
    'SystemRoot',
    'WINDIR',
    'COMSPEC',
    'PATHEXT',
    'TEMP',
    'TMP',
    'TMPDIR',
  ]
  return Object.fromEntries(names.flatMap((name) => process.env[name] === undefined ? [] : [[name, process.env[name]]]))
}

function validatePythonExecutable(value: string): string {
  if (!path.isAbsolute(value)) {
    throw new V4FactsTransportError('invalid_python_executable', 'Python executable must be an absolute path')
  }
  let resolved: string
  let observed: fs.Stats
  try {
    resolved = fs.realpathSync.native(value)
    observed = fs.lstatSync(resolved)
  } catch {
    throw new V4FactsTransportError('invalid_python_executable', 'Python executable is not readable')
  }
  if (!path.isAbsolute(resolved) || !observed.isFile() || observed.isSymbolicLink()) {
    throw new V4FactsTransportError(
      'invalid_python_executable',
      'Python executable must resolve through a valid link chain to a regular file',
    )
  }
  return value
}

function validateMachineScript(): string {
  let resolved: string
  let observed: fs.Stats
  try {
    observed = fs.lstatSync(V4_FACTS_MACHINE_SCRIPT)
    resolved = fs.realpathSync.native(V4_FACTS_MACHINE_SCRIPT)
  } catch {
    throw new V4FactsTransportError(
      'invalid_machine_script',
      'The Web V4 facts machine script is unavailable',
    )
  }
  if (!path.isAbsolute(V4_FACTS_MACHINE_SCRIPT)
    || !path.isAbsolute(resolved)
    || !observed.isFile()
    || observed.isSymbolicLink()) {
    throw new V4FactsTransportError(
      'invalid_machine_script',
      'The Web V4 facts machine must be one absolute regular script',
    )
  }
  return resolved
}

function validateRequest(request: V4FactsMachineRequest): Buffer {
  if (!isRecord(request) || Object.keys(request).sort().join(',') !== 'arguments,operation,protocol_version,scope') {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine request fields are not closed')
  }
  const descriptor = operationDescriptor(request.operation)
  if (request.protocol_version !== 1 || descriptor === null) {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine request protocol or operation is invalid')
  }
  if (!isRecord(request.scope)
    || Object.keys(request.scope).sort().join(',') !== 'expected_governed_project_id,workspace_root,worktree_locator'
    || typeof request.scope.workspace_root !== 'string'
    || typeof request.scope.worktree_locator !== 'string'
    || typeof request.scope.expected_governed_project_id !== 'string'
    || !path.isAbsolute(request.scope.workspace_root)
    || !path.isAbsolute(request.scope.worktree_locator)
    || !request.scope.expected_governed_project_id) {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine scope is not one closed absolute boundary')
  }
  if (!isRecord(request.arguments)) {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine arguments must be an object')
  }
  if ((descriptor.kind === 'list' && Object.keys(request.arguments).length !== 0)
    || (descriptor.kind === 'read'
      && (Object.keys(request.arguments).sort().join(',') !== 'object_id'
        || typeof request.arguments.object_id !== 'string'
        || !descriptor.objectIdPattern.test(request.arguments.object_id)))) {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine arguments do not match the operation')
  }
  let encoded: Buffer
  try {
    encoded = Buffer.from(JSON.stringify(request), 'utf8')
  } catch {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine request is not JSON serializable')
  }
  if (encoded.length > REQUEST_LIMIT) {
    throw new V4FactsTransportError('transport_request_overflow', 'Machine request exceeds 12 MiB')
  }
  return encoded
}

function decodeResponse(raw: Buffer, request: V4FactsMachineRequest): V4FactsMachineResponse {
  if (raw.length === 0 || raw.length > RESPONSE_LIMIT) {
    throw new V4FactsTransportError('transport_response_overflow', 'Machine response is empty or exceeds 32 MiB')
  }
  if (raw[raw.length - 1] !== 0x0a || raw.subarray(0, raw.length - 1).includes(0x0a)) {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine stdout must be exactly one JSON line')
  }
  let text: string
  try {
    text = new TextDecoder('utf-8', { fatal: true }).decode(raw.subarray(0, raw.length - 1))
  } catch {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine stdout is not strict UTF-8')
  }
  let value: unknown
  try {
    value = JSON.parse(text)
  } catch {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine stdout is not JSON')
  }
  if (!isRecord(value)
    || Object.keys(value).length !== RESPONSE_FIELDS.size
    || Object.keys(value).some((field) => !RESPONSE_FIELDS.has(field))
    || value.protocol_version !== 1
    || value.operation !== request.operation
    || typeof value.status !== 'string'
    || (value.error !== null && typeof value.error !== 'string')
    || typeof value.completion_unknown !== 'boolean') {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine response envelope is invalid')
  }
  if (value.result === null) {
    if (!COMMON_ERROR_STATUSES.has(value.status)
      || typeof value.error !== 'string' || value.error.length === 0
      || value.completion_unknown) {
      throw new V4FactsTransportError('malformed_machine_response', 'Machine error response is inconsistent')
    }
  } else if (!isRecord(value.result)
    || value.error !== null
    || value.completion_unknown
    || value.result.status !== value.status
    || !validateOperationResult(value.result, request)) {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine operation result is invalid')
  }
  return value as unknown as V4FactsMachineResponse
}

export async function invokeV4FactsMachine(
  request: V4FactsMachineRequest,
  options: V4FactsTransportOptions,
): Promise<V4FactsMachineResponse> {
  const pythonExecutable = validatePythonExecutable(options.pythonExecutable)
  const machineScript = validateMachineScript()
  const input = validateRequest(request)
  const timeoutMs = options.timeoutMs ?? 30_000
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 120_000) {
    throw new V4FactsTransportError('invalid_transport_timeout', 'Machine timeout is outside the allowed range')
  }
  const spawnProcess = options.spawnProcess ?? (spawn as unknown as SpawnProcess)

  return await new Promise<V4FactsMachineResponse>((resolve, reject) => {
    let child: SpawnedProcess
    try {
      child = spawnProcess(
        pythonExecutable,
        ['-I', '-B', '-X', 'utf8', machineScript],
        {
          cwd: path.dirname(pythonExecutable),
          env: safeEnvironment(),
          shell: false,
          windowsHide: true,
          stdio: ['pipe', 'pipe', 'pipe'],
        },
      )
    } catch (error) {
      reject(new V4FactsTransportError('transport_spawn_failed', 'Unable to start the V4 facts machine', {
        completionUnknown: false,
        diagnostic: error instanceof Error ? error.message : String(error),
      }))
      return
    }
    const stdout: Buffer[] = []
    const stderr: Buffer[] = []
    let stdoutBytes = 0
    let stderrBytes = 0
    let settled = false
    let started = false

    const finish = (action: () => void) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      action()
    }
    const fail = (error: V4FactsTransportError) => finish(() => reject(error))
    const terminate = () => {
      try {
        child.kill('SIGKILL')
      } catch {
        // The promise is already settled; kill failure must not extend the public deadline.
      }
    }
    const boundedDetach = () => {
      const reapTimer = setTimeout(() => {
        child.stdin.destroy()
        child.stdout.destroy()
        child.stderr.destroy()
        child.unref()
      }, 250)
      reapTimer.unref()
    }
    const timer = setTimeout(() => {
      const diagnostic = Buffer.concat(stderr).toString('utf8')
      fail(new V4FactsTransportError('transport_timeout', 'V4 facts machine timed out', {
        completionUnknown: false,
        diagnostic,
      }))
      terminate()
      boundedDetach()
    }, timeoutMs)

    child.once('spawn', () => { started = true })
    child.stdout.on('data', (chunk: Buffer | string) => {
      const data = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
      stdoutBytes += data.length
      if (stdoutBytes > RESPONSE_LIMIT) {
        fail(new V4FactsTransportError('transport_response_overflow', 'Machine stdout exceeded 32 MiB', {
          completionUnknown: false,
        }))
        terminate()
        boundedDetach()
        return
      }
      stdout.push(data)
    })
    child.stderr.on('data', (chunk: Buffer | string) => {
      if (stderrBytes >= STDERR_LIMIT) return
      const data = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)
      const remaining = STDERR_LIMIT - stderrBytes
      stderr.push(data.subarray(0, remaining))
      stderrBytes += Math.min(data.length, remaining)
    })
    child.once('error', (error) => {
      fail(new V4FactsTransportError(
        started ? 'transport_process_error' : 'transport_spawn_failed',
        started ? 'V4 facts machine process failed' : 'Unable to start the V4 facts machine', {
        completionUnknown: false,
        diagnostic: error.message,
      }))
      if (started) {
        terminate()
        boundedDetach()
      }
    })
    child.stdin.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stdin_error', 'V4 facts machine stdin failed', {
        completionUnknown: false,
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.stdout.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stdout_error', 'V4 facts machine stdout failed', {
        completionUnknown: false,
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.stderr.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stderr_error', 'V4 facts machine stderr failed', {
        completionUnknown: false,
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.once('close', (code, signal) => {
      const diagnostic = Buffer.concat(stderr).toString('utf8')
      if (code !== 0 || signal !== null) {
        fail(new V4FactsTransportError('transport_process_failed', 'V4 facts machine exited unexpectedly', {
          completionUnknown: false,
          diagnostic,
        }))
        return
      }
      try {
        const response = decodeResponse(Buffer.concat(stdout), request)
        finish(() => resolve(response))
      } catch (error) {
        const observed = error instanceof V4FactsTransportError
          ? error
          : new V4FactsTransportError('malformed_machine_response', 'Machine response validation failed')
        fail(new V4FactsTransportError(observed.code, observed.message, {
          completionUnknown: observed.completionUnknown,
          diagnostic: observed.diagnostic,
        }))
      }
    })
    try {
      child.stdin.end(input)
    } catch (error) {
      fail(new V4FactsTransportError('transport_stdin_error', 'V4 facts machine stdin failed', {
        completionUnknown: false,
        diagnostic: error instanceof Error ? error.message : String(error),
      }))
      terminate()
      boundedDetach()
    }
  })
}
