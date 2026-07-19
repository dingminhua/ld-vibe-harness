import { spawn } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { TextDecoder } from 'node:util'

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
  'status', 'items', 'object_problems', 'structural_problems', 'governance_resolution',
])
const DETAIL_RESULT_FIELDS = new Set([
  'status', 'item', 'problems', 'coverage_status', 'governance_resolution',
])
const CREATE_RESULT_FIELDS = new Set([
  'status', 'code', 'summary', 'actual_ref', 'existing_ref', 'canonical_path',
  'fact_object', 'details', 'governance_resolution',
])
const ITEM_FIELDS = new Set([
  'object_ref', 'canonical_path', 'absolute_path', 'carrier', 'check_status',
  'fact_object', 'content_fingerprint', 'issues',
])
const LIST_STATUSES = new Set(['complete', 'partial', 'unavailable', 'integrity_conflict'])
const DETAIL_STATUSES = new Set(['ok', 'not_found', 'invalid', 'unavailable'])
const CREATE_STATUSES = new Set([
  'created', 'exact_duplicate', 'invalid', 'unavailable', 'integrity_conflict',
  'readback_failed', 'rollback_residue',
])
const COMMON_ERROR_STATUSES = new Set(['invalid', 'unavailable', 'error'])

export type V4FactsOperation = 'list-sparks' | 'read-spark' | 'create-spark'

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

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isObjectRef(value: unknown, withStatus = false): boolean {
  if (!isRecord(value)) return false
  const keys = Object.keys(value).sort().join(',')
  return keys === (withStatus
    ? 'fact_type_key,governed_project_id,object_id,status'
    : 'fact_type_key,governed_project_id,object_id')
    && typeof value.governed_project_id === 'string'
    && typeof value.fact_type_key === 'string'
    && typeof value.object_id === 'string'
    && (!withStatus || typeof value.status === 'string')
}

function isIssue(value: unknown): boolean {
  return isRecord(value)
    && Object.keys(value).sort().join(',') === 'category,field_path,summary'
    && typeof value.category === 'string'
    && (value.field_path === null || typeof value.field_path === 'string')
    && typeof value.summary === 'string'
}

function isStructuralProblem(value: unknown): boolean {
  return isRecord(value)
    && Object.keys(value).sort().join(',') === 'canonical_path,check_status,fact_type_key,issues'
    && typeof value.fact_type_key === 'string'
    && typeof value.canonical_path === 'string'
    && value.check_status === 'unavailable'
    && Array.isArray(value.issues)
    && value.issues.length > 0
    && value.issues.every(isIssue)
}

function isReadItem(value: unknown): value is Record<string, unknown> {
  return isRecord(value)
    && hasExactFields(value, ITEM_FIELDS)
    && isObjectRef(value.object_ref)
    && typeof value.canonical_path === 'string'
    && typeof value.absolute_path === 'string'
    && typeof value.carrier === 'string'
    && ['mechanically_valid', 'invalid', 'unavailable'].includes(String(value.check_status))
    && Array.isArray(value.issues)
    && value.issues.every(isIssue)
    && (value.check_status === 'mechanically_valid'
      ? isRecord(value.fact_object)
        && typeof value.content_fingerprint === 'string'
        && value.issues.length === 0
      : value.fact_object === null
        && value.content_fingerprint === null
        && value.issues.length > 0)
}

function validateOperationResult(value: Record<string, unknown>, operation: V4FactsOperation): boolean {
  if (operation === 'list-sparks') {
    const items = value.items
    const objectProblems = value.object_problems
    const structuralProblems = value.structural_problems
    const validShape = hasExactFields(value, LIST_RESULT_FIELDS)
      && LIST_STATUSES.has(String(value.status))
      && Array.isArray(items) && items.every(isReadItem)
      && Array.isArray(objectProblems) && objectProblems.every(isReadItem)
      && Array.isArray(structuralProblems) && structuralProblems.every(isStructuralProblem)
      && isRecord(value.governance_resolution)
    if (!validShape) return false
    if (value.status === 'complete') {
      return objectProblems.length === 0 && structuralProblems.length === 0
    }
    if (value.status === 'partial') return objectProblems.length > 0
    return structuralProblems.length > 0
  }
  if (operation === 'read-spark') {
    const item = value.item
    const problems = value.problems
    const validShape = hasExactFields(value, DETAIL_RESULT_FIELDS)
      && DETAIL_STATUSES.has(String(value.status))
      && (item === null || isReadItem(item))
      && Array.isArray(problems)
      && problems.every((problem) => isReadItem(problem) || isStructuralProblem(problem))
      && LIST_STATUSES.has(String(value.coverage_status))
      && isRecord(value.governance_resolution)
    if (!validShape) return false
    if (value.status === 'ok') {
      return isRecord(item)
        && item.check_status === 'mechanically_valid'
        && problems.length === 0
    }
    if (value.status === 'not_found') {
      return item === null && problems.length === 0 && value.coverage_status === 'complete'
    }
    return item === null && problems.length > 0
  }
  const validShape = hasExactFields(value, CREATE_RESULT_FIELDS)
    && CREATE_STATUSES.has(String(value.status))
    && typeof value.code === 'string' && value.code.length > 0
    && typeof value.summary === 'string' && value.summary.length > 0
    && (value.actual_ref === null || isObjectRef(value.actual_ref))
    && (value.existing_ref === null || isObjectRef(value.existing_ref, true))
    && (value.canonical_path === null || typeof value.canonical_path === 'string')
    && (value.fact_object === null || isRecord(value.fact_object))
    && isStringArray(value.details)
    && isRecord(value.governance_resolution)
  if (!validShape) return false
  if (value.status === 'created') {
    return value.actual_ref !== null
      && value.existing_ref === null
      && typeof value.canonical_path === 'string'
      && value.fact_object !== null
  }
  if (value.status === 'exact_duplicate') {
    return value.actual_ref === null
      && value.existing_ref !== null
      && value.canonical_path === null
      && value.fact_object === null
  }
  return value.actual_ref === null && value.existing_ref === null && value.fact_object === null
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

function validateRequest(request: V4FactsMachineRequest): Buffer {
  if (!isRecord(request) || Object.keys(request).sort().join(',') !== 'arguments,operation,protocol_version,scope') {
    throw new V4FactsTransportError('invalid_transport_request', 'Machine request fields are not closed')
  }
  if (request.protocol_version !== 1 || !['list-sparks', 'read-spark', 'create-spark'].includes(request.operation)) {
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
  if ((request.operation === 'list-sparks' && Object.keys(request.arguments).length !== 0)
    || (request.operation === 'read-spark'
      && (Object.keys(request.arguments).sort().join(',') !== 'object_id'
        || typeof request.arguments.object_id !== 'string'
        || !/^spark-[0-9]{4,}$/.test(request.arguments.object_id)))
    || (request.operation === 'create-spark'
      && (Object.keys(request.arguments).sort().join(',') !== 'description,priority,title'
        || typeof request.arguments.title !== 'string'
        || typeof request.arguments.description !== 'string'
        || typeof request.arguments.priority !== 'string'))) {
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

function decodeResponse(raw: Buffer, operation: V4FactsOperation): V4FactsMachineResponse {
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
    || value.operation !== operation
    || typeof value.status !== 'string'
    || (value.error !== null && typeof value.error !== 'string')
    || typeof value.completion_unknown !== 'boolean') {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine response envelope is invalid')
  }
  if (value.result === null) {
    const expectedUnknown = operation === 'create-spark' && value.status === 'error'
    if (!COMMON_ERROR_STATUSES.has(value.status)
      || typeof value.error !== 'string' || value.error.length === 0
      || value.completion_unknown !== expectedUnknown) {
      throw new V4FactsTransportError('malformed_machine_response', 'Machine error response is inconsistent')
    }
  } else if (!isRecord(value.result)
    || value.error !== null
    || value.completion_unknown
    || value.result.status !== value.status
    || !validateOperationResult(value.result, operation)) {
    throw new V4FactsTransportError('malformed_machine_response', 'Machine operation result is invalid')
  }
  return value as unknown as V4FactsMachineResponse
}

export async function invokeV4FactsMachine(
  request: V4FactsMachineRequest,
  options: V4FactsTransportOptions,
): Promise<V4FactsMachineResponse> {
  const pythonExecutable = validatePythonExecutable(options.pythonExecutable)
  const input = validateRequest(request)
  const timeoutMs = options.timeoutMs ?? (request.operation === 'create-spark' ? 45_000 : 30_000)
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0 || timeoutMs > 120_000) {
    throw new V4FactsTransportError('invalid_transport_timeout', 'Machine timeout is outside the allowed range')
  }
  const spawnProcess = options.spawnProcess ?? (spawn as unknown as SpawnProcess)

  return await new Promise<V4FactsMachineResponse>((resolve, reject) => {
    let child: SpawnedProcess
    try {
      child = spawnProcess(
        pythonExecutable,
        ['-I', '-X', 'utf8', '-m', 'ldvh.facts.web_machine'],
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
        completionUnknown: request.operation === 'create-spark',
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
          completionUnknown: request.operation === 'create-spark',
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
        completionUnknown: started && request.operation === 'create-spark',
        diagnostic: error.message,
      }))
      if (started) {
        terminate()
        boundedDetach()
      }
    })
    child.stdin.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stdin_error', 'V4 facts machine stdin failed', {
        completionUnknown: started && request.operation === 'create-spark',
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.stdout.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stdout_error', 'V4 facts machine stdout failed', {
        completionUnknown: started && request.operation === 'create-spark',
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.stderr.once('error', (error) => {
      fail(new V4FactsTransportError('transport_stderr_error', 'V4 facts machine stderr failed', {
        completionUnknown: started && request.operation === 'create-spark',
        diagnostic: error.message,
      }))
      terminate()
      boundedDetach()
    })
    child.once('close', (code, signal) => {
      const diagnostic = Buffer.concat(stderr).toString('utf8')
      if (code !== 0 || signal !== null) {
        fail(new V4FactsTransportError('transport_process_failed', 'V4 facts machine exited unexpectedly', {
          completionUnknown: request.operation === 'create-spark',
          diagnostic,
        }))
        return
      }
      try {
        const response = decodeResponse(Buffer.concat(stdout), request.operation)
        finish(() => resolve(response))
      } catch (error) {
        const observed = error instanceof V4FactsTransportError
          ? error
          : new V4FactsTransportError('malformed_machine_response', 'Machine response validation failed')
        fail(new V4FactsTransportError(observed.code, observed.message, {
          completionUnknown: observed.completionUnknown || request.operation === 'create-spark',
          diagnostic: observed.diagnostic,
        }))
      }
    })
    try {
      child.stdin.end(input)
    } catch (error) {
      fail(new V4FactsTransportError('transport_stdin_error', 'V4 facts machine stdin failed', {
        completionUnknown: started && request.operation === 'create-spark',
        diagnostic: error instanceof Error ? error.message : String(error),
      }))
      terminate()
      boundedDetach()
    }
  })
}
