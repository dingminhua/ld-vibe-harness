import assert from 'node:assert/strict'
import { EventEmitter } from 'node:events'
import { mkdirSync, mkdtempSync, realpathSync, rmSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { PassThrough } from 'node:stream'
import { test } from 'node:test'

import {
  invokeV4FactsMachine,
  V4_FACTS_OPERATIONS,
  V4_FACTS_MACHINE_SCRIPT,
  V4FactsTransportError,
  type SpawnedProcess,
  type SpawnProcess,
  type V4FactsMachineRequest,
  type V4FactsOperation,
} from '../../api/internal/v4FactsTransport.ts'
import {
  listV4WorkCases,
  readV4WorkCase,
  type V4FactReaderConfig,
} from '../../api/services/v4FactReader.ts'
import {
  v4FactReaderConfig,
  V4FactsConfigurationError,
} from '../../api/services/v4FactsConfig.ts'
import {
  listV4Sparks as listExistingV4Sparks,
  readV4Spark as readExistingV4Spark,
} from '../../api/services/v4SparkReader.ts'

const GOVERNED_PROJECT_ID = 'project-current'
const FINGERPRINT = 'a'.repeat(64)
const OBSERVED_AT = '2026-07-26T15:00:00+08:00'

function machineRequest(operation: V4FactsOperation, args: Record<string, unknown>): V4FactsMachineRequest {
  return {
    protocol_version: 1,
    operation,
    scope: {
      workspace_root: '/workspace',
      worktree_locator: '/workspace/project',
      expected_governed_project_id: GOVERNED_PROJECT_ID,
    },
    arguments: args,
  }
}

function readItem(
  factTypeKey: 'spark' | 'workcase',
  objectId: string,
  worktreeRoot = '/workspace/project',
): Record<string, unknown> {
  const plural = factTypeKey === 'spark' ? 'sparks' : 'workcases'
  return {
    object_ref: {
      governed_project_id: GOVERNED_PROJECT_ID,
      fact_type_key: factTypeKey,
      object_id: objectId,
    },
    canonical_path: `ldvh-base/${plural}/${objectId}.yaml`,
    absolute_path: path.join(worktreeRoot, 'ldvh-base', plural, `${objectId}.yaml`),
    carrier: 'yaml',
    check_status: 'mechanically_valid',
    fact_object: {
      object_id: objectId,
      fact_type_key: factTypeKey,
      title: 'Current object',
    },
    content_fingerprint: FINGERPRINT,
    issues: [],
  }
}

function problemItem(
  factTypeKey: 'spark' | 'workcase',
  objectId: string,
  checkStatus: 'invalid' | 'not_found' | 'unavailable' = 'invalid',
): Record<string, unknown> {
  return {
    ...readItem(factTypeKey, objectId),
    check_status: checkStatus,
    fact_object: null,
    content_fingerprint: null,
    issues: [{ category: 'schema', field_path: 'status', summary: 'current object is invalid' }],
  }
}

function sourceReference(
  kind: string,
  locator: string,
  details: Record<string, unknown>,
): Record<string, unknown> {
  return { kind, locator, observed_at: OBSERVED_AT, details }
}

function governanceResolution(options: {
  workspaceRoot?: string
  worktreeLocator?: string
  worktreeRoot?: string
  registeredProjectPath?: string
} = {}): Record<string, unknown> {
  const workspaceRoot = options.workspaceRoot ?? '/workspace'
  const worktreeLocator = options.worktreeLocator ?? '/workspace/project'
  const worktreeRoot = options.worktreeRoot ?? '/workspace/project'
  const registeredProjectPath = options.registeredProjectPath ?? worktreeRoot
  const configPath = path.join(workspaceRoot, 'LDVH-GOVERNED-PROJECTS.yaml')
  const gitCommonDir = path.join(worktreeRoot, '.git')
  const configurationSource = sourceReference(
    'governed_projects_configuration', configPath, {
      discovery_bases: [{ kind: 'explicit_workspace_root', start: workspaceRoot }],
    },
  )
  const registeredIdentitySource = sourceReference(
    'registered_project_git_identity', registeredProjectPath, {
      project_id: GOVERNED_PROJECT_ID,
      status: 'git_worktree',
      git_worktree_root: worktreeRoot,
      git_common_dir: gitCommonDir,
    },
  )
  const pathSource = sourceReference('path_observation', worktreeLocator, {
    locator_index: 0,
    original_locator: worktreeLocator,
    base: workspaceRoot,
    exists: true,
    uses_existing_ancestor: false,
  })
  const gitSource = sourceReference('git_identity_observation', worktreeRoot, {
    locator_index: 0,
    git_common_dir: gitCommonDir,
  })
  return {
    workspace_root: workspaceRoot,
    config_path: configPath,
    config_status: 'valid',
    scope_status: 'governed_single',
    object_resolutions: [{
      locator_index: 0,
      locator: worktreeLocator,
      resolved_identity: worktreeRoot,
      identity_evidence: [pathSource, gitSource, configurationSource, registeredIdentitySource],
      source: 'explicit_locator',
      status: 'governed',
      governed_project_id: GOVERNED_PROJECT_ID,
      registered_project_path: registeredProjectPath,
      governed_via: 'path',
      git_worktree_root: worktreeRoot,
      git_common_dir: gitCommonDir,
      source_refs: [pathSource, gitSource, configurationSource, registeredIdentitySource],
      unknown_reason: null,
    }],
    registered_project_candidates: [{
      governed_project_id: GOVERNED_PROJECT_ID,
      registered_project_path: registeredProjectPath,
      git_worktree_root: worktreeRoot,
      git_common_dir: gitCommonDir,
      source_refs: [configurationSource, registeredIdentitySource],
    }],
    source_refs: [pathSource, gitSource, configurationSource, registeredIdentitySource],
  }
}

function additionalCandidate(
  governance: Record<string, unknown>,
  governedProjectId: string,
  pathSuffix: string,
): Record<string, unknown> {
  const template = (governance.registered_project_candidates as Record<string, unknown>[])[0]
  const candidate = structuredClone(template)
  const projectPath = `/workspace/${pathSuffix}`
  candidate.governed_project_id = governedProjectId
  candidate.registered_project_path = projectPath
  candidate.git_worktree_root = projectPath
  candidate.git_common_dir = `${projectPath}/.git`
  const identity = (candidate.source_refs as Record<string, unknown>[]).find((source) => (
    source.kind === 'registered_project_git_identity'
  )) as Record<string, unknown>
  identity.locator = projectPath
  const details = identity.details as Record<string, unknown>
  details.project_id = governedProjectId
  details.git_worktree_root = projectPath
  details.git_common_dir = `${projectPath}/.git`
  return candidate
}

function listResult(
  factTypeKey: 'spark' | 'workcase',
  objectId: string,
  options: {
    worktreeRoot?: string
    governance?: Record<string, unknown>
  } = {},
): Record<string, unknown> {
  return {
    status: 'complete',
    items: [readItem(factTypeKey, objectId, options.worktreeRoot)],
    object_problems: [],
    structural_problems: [],
    governance_resolution: options.governance ?? governanceResolution(),
    observed_at: OBSERVED_AT,
  }
}

function detailResult(factTypeKey: 'spark' | 'workcase', objectId: string): Record<string, unknown> {
  return {
    status: 'ok',
    item: readItem(factTypeKey, objectId),
    problems: [],
    coverage_status: 'complete',
    governance_resolution: governanceResolution(),
    observed_at: OBSERVED_AT,
  }
}

function structuralProblem(factTypeKey: 'spark' | 'workcase'): Record<string, unknown> {
  const plural = factTypeKey === 'spark' ? 'sparks' : 'workcases'
  return {
    fact_type_key: factTypeKey,
    canonical_path: `ldvh-base/${plural}`,
    check_status: 'unavailable',
    issues: [{ category: 'location', field_path: null, summary: 'directory coverage is incomplete' }],
  }
}

function responseLine(
  operation: V4FactsOperation,
  status: string,
  result: Record<string, unknown> | null,
  error: string | null = null,
): Buffer {
  return Buffer.from(`${JSON.stringify({
    protocol_version: 1,
    operation,
    status,
    result,
    error,
    completion_unknown: false,
  })}\n`, 'utf8')
}

function respondingSpawn(
  respond: (request: Buffer) => Buffer,
  observe?: (request: Buffer) => void,
): SpawnProcess {
  return () => {
    const events = new EventEmitter()
    const stdin = new PassThrough()
    const stdout = new PassThrough()
    const stderr = new PassThrough()
    const chunks: Buffer[] = []
    stdin.on('data', (chunk: Buffer | string) => {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk))
    })
    stdin.on('finish', () => {
      queueMicrotask(() => {
        const request = Buffer.concat(chunks)
        observe?.(request)
        events.emit('spawn')
        stdout.write(respond(request))
        stdout.end()
        stderr.end()
        events.emit('close', 0, null)
      })
    })
    Object.assign(events, {
      stdin,
      stdout,
      stderr,
      kill: () => true,
      unref: () => undefined,
    })
    return events as unknown as SpawnedProcess
  }
}

function readerConfig(spawnProcess: SpawnProcess): V4FactReaderConfig {
  return {
    pythonExecutable: process.execPath,
    spawnProcess,
    scope: machineRequest('list-workcases', {}).scope,
  }
}

test('V4 machine transport exposes only the four read-only current operations', () => {
  assert.deepEqual(V4_FACTS_OPERATIONS, [
    'list-sparks',
    'read-spark',
    'list-workcases',
    'read-workcase',
  ])
})

test('Node invokes the absolute Web-owned Python script in isolated mode', async () => {
  let observedCommand = ''
  let observedArgs: readonly string[] = []
  const baseSpawn = respondingSpawn(() => (
    responseLine('list-workcases', 'complete', listResult('workcase', 'workcase-0001'))
  ))
  const spawnProcess: SpawnProcess = (command, args, options) => {
    observedCommand = command
    observedArgs = args
    return baseSpawn(command, args, options)
  }

  await listV4WorkCases(readerConfig(spawnProcess))

  assert.equal(observedCommand, process.execPath)
  assert.equal(path.isAbsolute(V4_FACTS_MACHINE_SCRIPT), true)
  assert.deepEqual(observedArgs.slice(0, 4), ['-I', '-B', '-X', 'utf8'])
  assert.equal(observedArgs[4], realpathSync.native(V4_FACTS_MACHINE_SCRIPT))
  assert.equal(observedArgs.includes('-m'), false)
  assert.match(observedArgs[4] ?? '', /web[/\\]python[/\\]ldvh_web_facts[/\\]machine\.py$/)
})

test('WorkCase reader sends strict one-object JSON for list and read operations', async () => {
  const observed: Array<Record<string, unknown>> = []
  const spawnProcess = respondingSpawn((raw) => {
    assert.equal(raw.includes(0x0a), false)
    const request = JSON.parse(raw.toString('utf8')) as V4FactsMachineRequest
    observed.push(request as unknown as Record<string, unknown>)
    if (request.operation === 'list-workcases') {
      return responseLine(request.operation, 'complete', listResult('workcase', 'workcase-0001'))
    }
    return responseLine(request.operation, 'ok', detailResult('workcase', 'workcase-0001'))
  })
  const config = readerConfig(spawnProcess)

  const listed = await listV4WorkCases(config)
  const detail = await readV4WorkCase(config, 'workcase-0001')

  assert.equal(listed.status, 'complete')
  assert.equal(detail.status, 'ok')
  assert.deepEqual(observed.map((item) => [item.operation, item.arguments]), [
    ['list-workcases', {}],
    ['read-workcase', { object_id: 'workcase-0001' }],
  ])
})

test('existing Spark reader uses the same list and detail DTO validation', async () => {
  const spawnProcess = respondingSpawn((raw) => {
    const request = JSON.parse(raw.toString('utf8')) as V4FactsMachineRequest
    return request.operation === 'list-sparks'
      ? responseLine(request.operation, 'complete', listResult('spark', 'spark-0001'))
      : responseLine(request.operation, 'ok', detailResult('spark', 'spark-0001'))
  })
  const config = readerConfig(spawnProcess)

  assert.equal((await listExistingV4Sparks(config)).status, 'complete')
  assert.equal((await readExistingV4Spark(config, 'spark-0001')).status, 'ok')
})

test('read operation rejects an object identity from another current layout before spawning', async () => {
  let spawnCount = 0
  const spawnProcess: SpawnProcess = () => {
    spawnCount += 1
    throw new Error('must not spawn')
  }

  await assert.rejects(
    readV4WorkCase(readerConfig(spawnProcess), 'spark-0001'),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'invalid_transport_request')
      return true
    },
  )
  assert.equal(spawnCount, 0)
})

test('WorkCase list rejects a mechanically valid Spark item instead of crossing fact types', async () => {
  const spawnProcess = respondingSpawn(() => (
    responseLine('list-workcases', 'complete', listResult('spark', 'spark-0001'))
  ))

  await assert.rejects(
    listV4WorkCases(readerConfig(spawnProcess)),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'malformed_machine_response')
      return true
    },
  )
})

test('list binds every source path and carrier to the resolved current layout', async () => {
  for (const mutate of [
    (item: Record<string, unknown>) => { item.canonical_path = 'ldvh-base/workcases/workcase-9999.yaml' },
    (item: Record<string, unknown>) => { item.absolute_path = '/workspace/other/workcase-0001.yaml' },
    (item: Record<string, unknown>) => { item.carrier = 'markdown' },
  ]) {
    const result = listResult('workcase', 'workcase-0001')
    mutate((result.items as Record<string, unknown>[])[0])
    const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'complete', result))

    await assert.rejects(
      listV4WorkCases(readerConfig(spawnProcess)),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  }
})

test('machine result governance must independently match the requested scope', async () => {
  for (const mutate of [
    (governance: Record<string, unknown>) => { governance.workspace_root = '/different-workspace' },
    (governance: Record<string, unknown>) => {
      const wrongPath = path.join('/workspace', '.ldvh', 'projects.yaml')
      governance.config_path = wrongPath
      for (const source of governance.source_refs as Record<string, unknown>[]) {
        if (source.kind === 'governed_projects_configuration') source.locator = wrongPath
      }
    },
    (governance: Record<string, unknown>) => {
      const configuration = (governance.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'governed_projects_configuration'
      )) as Record<string, unknown>
      ;(configuration.details as Record<string, unknown>).discovery_bases = []
    },
    (governance: Record<string, unknown>) => {
      const configuration = (governance.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'governed_projects_configuration'
      )) as Record<string, unknown>
      ;(configuration.details as Record<string, unknown>).discovery_bases = [{
        kind: 'path', start: '/workspace/project',
      }]
    },
    (governance: Record<string, unknown>) => { governance.scope_status = 'mixed_scope' },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.governed_project_id = 'project-other'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.git_worktree_root = '/workspace/other'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.governed_via = 'worktree'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.unknown_reason = 'unexpected uncertainty'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.identity_evidence = []
    },
    (governance: Record<string, unknown>) => {
      governance.registered_project_candidates = []
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      evidence.details = {}
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.exists = false
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.locator_index = 1
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.original_locator = '/workspace/forged-project'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.base = '/forged-workspace'
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.uses_existing_ancestor = true
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[0]
      const details = evidence.details as Record<string, unknown>
      details.forged = true
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      const evidence = (resolution.identity_evidence as Record<string, unknown>[])[1]
      const details = evidence.details as Record<string, unknown>
      details.locator_index = 1
    },
    (governance: Record<string, unknown>) => {
      const candidate = (governance.registered_project_candidates as Record<string, unknown>[])[0]
      const identity = (candidate.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'registered_project_git_identity'
      )) as Record<string, unknown>
      const details = identity.details as Record<string, unknown>
      details.status = 'not_git_worktree'
    },
    (governance: Record<string, unknown>) => {
      const configuration = (governance.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'governed_projects_configuration'
      )) as Record<string, unknown>
      const details = configuration.details as Record<string, unknown>
      details.forged = true
    },
    (governance: Record<string, unknown>) => {
      const candidate = (governance.registered_project_candidates as Record<string, unknown>[])[0]
      const duplicate = structuredClone(candidate)
      duplicate.governed_project_id = 'project-other'
      const identity = (duplicate.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'registered_project_git_identity'
      )) as Record<string, unknown>
      ;(identity.details as Record<string, unknown>).project_id = 'project-other'
      ;(governance.registered_project_candidates as Record<string, unknown>[]).push(duplicate)
    },
    (governance: Record<string, unknown>) => {
      const candidate = (governance.registered_project_candidates as Record<string, unknown>[])[0]
      const earlier = structuredClone(candidate)
      earlier.governed_project_id = 'project-before'
      earlier.registered_project_path = '/workspace/project-before'
      earlier.git_worktree_root = '/workspace/project-before'
      earlier.git_common_dir = '/workspace/project-before/.git'
      const identity = (earlier.source_refs as Record<string, unknown>[]).find((source) => (
        source.kind === 'registered_project_git_identity'
      )) as Record<string, unknown>
      identity.locator = earlier.registered_project_path
      const details = identity.details as Record<string, unknown>
      details.project_id = earlier.governed_project_id
      details.git_worktree_root = earlier.git_worktree_root
      details.git_common_dir = earlier.git_common_dir
      ;(governance.registered_project_candidates as Record<string, unknown>[]).push(earlier)
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.unexpected = true
    },
    (governance: Record<string, unknown>) => {
      const resolution = (governance.object_resolutions as Record<string, unknown>[])[0]
      resolution.source_refs = (resolution.source_refs as Record<string, unknown>[]).filter((source) => (
        source.kind !== 'git_identity_observation'
      ))
    },
  ]) {
    const result = listResult('workcase', 'workcase-0001')
    mutate(result.governance_resolution as Record<string, unknown>)
    const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'complete', result))

    await assert.rejects(
      listV4WorkCases(readerConfig(spawnProcess)),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  }
})

test('governance accepts a symlink alias only when it resolves to the returned worktree identity', async () => {
  const root = mkdtempSync(path.join(tmpdir(), 'ldvh-v4-transport-'))
  const realWorktree = path.join(root, 'real-project')
  const aliasWorktree = path.join(root, 'alias-project')
  const forgedWorktree = path.join(root, 'forged-project')
  mkdirSync(realWorktree)
  mkdirSync(forgedWorktree)
  symlinkSync(realWorktree, aliasWorktree, 'dir')
  try {
    const canonicalRealWorktree = realpathSync.native(realWorktree)
    const canonicalForgedWorktree = realpathSync.native(forgedWorktree)
    const request = machineRequest('list-workcases', {})
    request.scope = {
      workspace_root: root,
      worktree_locator: aliasWorktree,
      expected_governed_project_id: GOVERNED_PROJECT_ID,
    }
    const valid = listResult('workcase', 'workcase-0001', {
      worktreeRoot: canonicalRealWorktree,
      governance: governanceResolution({
        workspaceRoot: root,
        worktreeLocator: aliasWorktree,
        worktreeRoot: canonicalRealWorktree,
      }),
    })
    const validSpawn = respondingSpawn(() => responseLine('list-workcases', 'complete', valid))
    assert.equal((await invokeV4FactsMachine(request, {
      pythonExecutable: process.execPath,
      spawnProcess: validSpawn,
    })).status, 'complete')

    const forged = listResult('workcase', 'workcase-0001', {
      worktreeRoot: canonicalForgedWorktree,
      governance: governanceResolution({
        workspaceRoot: root,
        worktreeLocator: aliasWorktree,
        worktreeRoot: canonicalForgedWorktree,
      }),
    })
    const forgedSpawn = respondingSpawn(() => responseLine('list-workcases', 'complete', forged))
    await assert.rejects(
      invokeV4FactsMachine(request, {
        pythonExecutable: process.execPath,
        spawnProcess: forgedSpawn,
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
})

test('registered candidates use Unicode code point order rather than UTF-16 unit order', async () => {
  const result = listResult('workcase', 'workcase-0001')
  const governance = result.governance_resolution as Record<string, unknown>
  const candidates = governance.registered_project_candidates as Record<string, unknown>[]
  candidates.push(
    additionalCandidate(governance, 'project-\uE000', 'project-private-use'),
    additionalCandidate(governance, 'project-\u{10000}', 'project-supplementary'),
  )
  const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'complete', result))

  assert.equal((await listV4WorkCases(readerConfig(spawnProcess))).status, 'complete')
})

test('list rejects duplicate identities and overlap between valid items and problems', async () => {
  const duplicated = listResult('workcase', 'workcase-0001')
  duplicated.items = [
    readItem('workcase', 'workcase-0001'),
    readItem('workcase', 'workcase-0001'),
  ]
  const duplicateSpawn = respondingSpawn(() => responseLine('list-workcases', 'complete', duplicated))
  await assert.rejects(
    listV4WorkCases(readerConfig(duplicateSpawn)),
    (error: unknown) => error instanceof V4FactsTransportError
      && error.code === 'malformed_machine_response',
  )

  const overlapped = listResult('workcase', 'workcase-0001')
  overlapped.object_problems = [problemItem('workcase', 'workcase-0001')]
  const overlapSpawn = respondingSpawn(() => responseLine('list-workcases', 'complete', overlapped))
  await assert.rejects(
    listV4WorkCases(readerConfig(overlapSpawn)),
    (error: unknown) => error instanceof V4FactsTransportError
      && error.code === 'malformed_machine_response',
  )
})

test('completed object failures stay independent from list coverage', async () => {
  const complete = listResult('workcase', 'workcase-0001')
  complete.object_problems = [problemItem('workcase', 'workcase-0002')]
  const completeSpawn = respondingSpawn(() => responseLine('list-workcases', 'complete', complete))
  assert.equal((await listV4WorkCases(readerConfig(completeSpawn))).status, 'complete')

  const falsePartial = { ...complete, status: 'partial' }
  const falsePartialSpawn = respondingSpawn(() => responseLine('list-workcases', 'partial', falsePartial))
  await assert.rejects(
    listV4WorkCases(readerConfig(falsePartialSpawn)),
    (error: unknown) => error instanceof V4FactsTransportError
      && error.code === 'malformed_machine_response',
  )

  const partial = {
    ...complete,
    status: 'partial',
    structural_problems: [structuralProblem('workcase')],
  }
  const partialSpawn = respondingSpawn(() => responseLine('list-workcases', 'partial', partial))
  assert.equal((await listV4WorkCases(readerConfig(partialSpawn))).status, 'partial')

  const validWithUnavailable = listResult('workcase', 'workcase-0001')
  validWithUnavailable.status = 'partial'
  validWithUnavailable.object_problems = [problemItem('workcase', 'workcase-0002', 'unavailable')]
  const validWithUnavailableSpawn = respondingSpawn(() => (
    responseLine('list-workcases', 'partial', validWithUnavailable)
  ))
  assert.equal((await listV4WorkCases(readerConfig(validWithUnavailableSpawn))).status, 'partial')

  const allUnavailable = {
    ...listResult('workcase', 'workcase-0001'),
    status: 'unavailable',
    items: [],
    object_problems: [problemItem('workcase', 'workcase-0002', 'unavailable')],
  }
  const allUnavailableSpawn = respondingSpawn(() => (
    responseLine('list-workcases', 'unavailable', allUnavailable)
  ))
  assert.equal((await listV4WorkCases(readerConfig(allUnavailableSpawn))).status, 'unavailable')
})

test('structural diagnostics accept only normalized paths inside the current layout', async () => {
  for (const canonicalPath of [
    'ldvh-base/workcases/../../other',
    'ldvh-base/workcases\\workcase-0001.yml',
    '/ldvh-base/workcases/workcase-0001.yml',
    'ldvh-base/workcases//workcase-0001.yml',
  ]) {
    const result = listResult('workcase', 'workcase-0001')
    result.status = 'partial'
    const problem = structuralProblem('workcase')
    problem.canonical_path = canonicalPath
    result.structural_problems = [problem]
    const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'partial', result))
    await assert.rejects(
      listV4WorkCases(readerConfig(spawnProcess)),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  }
})

test('mechanical issues use the shared closed diagnostic shape', async () => {
  for (const issue of [
    { category: 'semantic', field_path: 'status', summary: 'unsupported category' },
    { category: 'schema', field_path: '', summary: 'empty field path' },
    { category: 'schema', field_path: null, summary: '   ' },
  ]) {
    const result = listResult('workcase', 'workcase-0001')
    result.status = 'complete'
    const problem = problemItem('workcase', 'workcase-0002')
    problem.issues = [issue]
    result.object_problems = [problem]
    const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'complete', result))
    await assert.rejects(
      listV4WorkCases(readerConfig(spawnProcess)),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  }
})

test('detail rejects a response whose object reference does not match the requested WorkCase', async () => {
  const spawnProcess = respondingSpawn(() => (
    responseLine('read-workcase', 'ok', detailResult('workcase', 'workcase-0002'))
  ))

  await assert.rejects(
    readV4WorkCase(readerConfig(spawnProcess), 'workcase-0001'),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'malformed_machine_response')
      return true
    },
  )
})

test('detail only accepts not_found when machine coverage is complete', async () => {
  const result = {
    status: 'not_found',
    item: null,
    problems: [problemItem('workcase', 'workcase-0001', 'not_found')],
    coverage_status: 'complete',
    governance_resolution: governanceResolution(),
    observed_at: OBSERVED_AT,
  }
  const completeSpawn = respondingSpawn(() => responseLine('read-workcase', 'not_found', result))
  assert.equal(
    (await readV4WorkCase(readerConfig(completeSpawn), 'workcase-0001')).status,
    'not_found',
  )

  result.coverage_status = 'partial'
  const incompleteSpawn = respondingSpawn(() => responseLine('read-workcase', 'not_found', result))

  await assert.rejects(
    readV4WorkCase(readerConfig(incompleteSpawn), 'workcase-0001'),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'malformed_machine_response')
      return true
    },
  )
})

test('invalid detail keeps diagnostics but never expands a partial fact object', async () => {
  const validFailure = respondingSpawn(() => responseLine('read-workcase', 'invalid', {
    status: 'invalid',
    item: null,
    problems: [problemItem('workcase', 'workcase-0001')],
    coverage_status: 'complete',
    governance_resolution: governanceResolution(),
    observed_at: OBSERVED_AT,
  }))
  assert.equal(
    (await readV4WorkCase(readerConfig(validFailure), 'workcase-0001')).status,
    'invalid',
  )

  const leakedFailure = problemItem('workcase', 'workcase-0001')
  leakedFailure.fact_object = { object_id: 'workcase-0001', fact_type_key: 'workcase' }
  const leakedSpawn = respondingSpawn(() => responseLine('read-workcase', 'invalid', {
    status: 'invalid',
    item: null,
    problems: [leakedFailure],
    coverage_status: 'complete',
    governance_resolution: governanceResolution(),
    observed_at: OBSERVED_AT,
  }))
  await assert.rejects(
    readV4WorkCase(readerConfig(leakedSpawn), 'workcase-0001'),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'malformed_machine_response')
      return true
    },
  )
})

test('machine stdout must remain exactly one JSON line', async () => {
  const spawnProcess = respondingSpawn(() => Buffer.concat([
    responseLine('list-workcases', 'complete', listResult('workcase', 'workcase-0001')),
    Buffer.from('{}\n'),
  ]))

  await assert.rejects(
    invokeV4FactsMachine(machineRequest('list-workcases', {}), {
      pythonExecutable: process.execPath,
      spawnProcess,
    }),
    (error: unknown) => {
      assert.ok(error instanceof V4FactsTransportError)
      assert.equal(error.code, 'malformed_machine_response')
      return true
    },
  )
})

test('machine results require a real RFC 3339 observation time', async () => {
  for (const observedAt of [
    '0000-01-01T00:00:00Z',
    '2026-07-26',
    '2026-02-31T00:00:00Z',
    '2026-07-26T25:00:00Z',
    '2026-07-26T12:00:00+24:00',
    '2026-07-26T12:00:00-00:00',
  ]) {
    const result = listResult('workcase', 'workcase-0001')
    result.observed_at = observedAt
    const spawnProcess = respondingSpawn(() => responseLine('list-workcases', 'complete', result))
    await assert.rejects(
      listV4WorkCases(readerConfig(spawnProcess)),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response',
    )
  }
})

test('missing V4 machine configuration is explicitly unavailable and has no local fallback', () => {
  const names = [
    'LDVH_WEB_PYTHON',
    'LDVH_WEB_WORKSPACE_ROOT',
    'LDVH_WEB_WORKTREE_LOCATOR',
    'LDVH_WEB_GOVERNED_PROJECT_ID',
  ] as const
  const previous = new Map(names.map((name) => [name, process.env[name]]))
  try {
    for (const name of names) delete process.env[name]
    assert.throws(v4FactReaderConfig, (error: unknown) => {
      assert.ok(error instanceof V4FactsConfigurationError)
      assert.equal(error.code, 'v4_facts_unavailable')
      assert.match(error.message, /must be configured/)
      return true
    })
  } finally {
    for (const name of names) {
      const value = previous.get(name)
      if (value === undefined) delete process.env[name]
      else process.env[name] = value
    }
  }
})
