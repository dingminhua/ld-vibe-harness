import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { EventEmitter } from 'node:events'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { PassThrough } from 'node:stream'
import { test } from 'node:test'

import {
  invokeV4FactsMachine,
  V4FactsTransportError,
  type SpawnProcess,
  type SpawnedProcess,
  type V4FactsMachineRequest,
} from '../../api/internal/v4FactsTransport.ts'

interface Observation {
  command?: string
  args?: readonly string[]
  options?: Record<string, unknown>
  input?: Buffer
}

interface FakeConfig {
  emitSpawn?: boolean
  closeOnKill?: boolean
  killResult?: boolean
}

class FakeProcess extends EventEmitter implements SpawnedProcess {
  stdin = new PassThrough()
  stdout = new PassThrough()
  stderr = new PassThrough()
  killed = false
  detached = false

  constructor(
    private readonly observation: Observation,
    private readonly action: (child: FakeProcess) => void,
    private readonly config: FakeConfig,
  ) {
    super()
    const input: Buffer[] = []
    this.stdin.on('data', (chunk: Buffer) => input.push(chunk))
    this.stdin.on('finish', () => {
      this.observation.input = Buffer.concat(input)
      this.action(this)
    })
    if (config.emitSpawn !== false) queueMicrotask(() => this.emit('spawn'))
  }

  kill(signal: NodeJS.Signals = 'SIGTERM'): boolean {
    this.killed = true
    if (this.config.closeOnKill !== false) queueMicrotask(() => this.emit('close', null, signal))
    return this.config.killResult !== false
  }

  unref(): void {
    this.detached = true
  }
}

function fixture(): { executable: string; cleanup: () => void } {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-v4-transport-'))
  const executable = path.join(directory, process.platform === 'win32' ? 'python.exe' : 'python')
  fs.writeFileSync(executable, '')
  return { executable, cleanup: () => fs.rmSync(directory, { recursive: true, force: true }) }
}

function request(operation: V4FactsMachineRequest['operation'] = 'list-sparks'): V4FactsMachineRequest {
  const argumentsByOperation: Record<V4FactsMachineRequest['operation'], Record<string, unknown>> = {
    'list-sparks': {},
    'read-spark': { object_id: 'spark-0001' },
    'create-spark': { title: 'Capture', description: 'Closed transport', priority: 'P2' },
  }
  return {
    protocol_version: 1,
    operation,
    scope: {
      workspace_root: path.resolve('/workspace'),
      worktree_locator: path.resolve('/workspace/project'),
      expected_governed_project_id: 'sample',
    },
    arguments: argumentsByOperation[operation],
  }
}

function readItem() {
  return {
    object_ref: { governed_project_id: 'sample', fact_type_key: 'spark', object_id: 'spark-0001' },
    canonical_path: 'ldvh-base/sparks/spark-0001.yaml',
    absolute_path: path.resolve('/workspace/project/ldvh-base/sparks/spark-0001.yaml'),
    carrier: 'yaml',
    check_status: 'mechanically_valid',
    fact_object: { fact_type_key: 'spark', object_id: 'spark-0001' },
    content_fingerprint: 'sha256',
    issues: [],
  }
}

function resultFor(operation: V4FactsMachineRequest['operation']): Record<string, unknown> {
  const governance_resolution = { scope_status: 'governed_single' }
  if (operation === 'list-sparks') {
    return {
      status: 'complete',
      items: [readItem()],
      object_problems: [],
      structural_problems: [],
      governance_resolution,
    }
  }
  if (operation === 'read-spark') {
    return {
      status: 'ok',
      item: readItem(),
      problems: [],
      coverage_status: 'complete',
      governance_resolution,
    }
  }
  return {
    status: 'created',
    code: 'created',
    summary: 'Created',
    actual_ref: { governed_project_id: 'sample', fact_type_key: 'spark', object_id: 'spark-0001' },
    existing_ref: null,
    canonical_path: 'ldvh-base/sparks/spark-0001.yaml',
    fact_object: { fact_type_key: 'spark', object_id: 'spark-0001' },
    details: [],
    governance_resolution,
  }
}

function response(operation: V4FactsMachineRequest['operation']): Buffer {
  const result = resultFor(operation)
  return Buffer.from(`${JSON.stringify({
    protocol_version: 1,
    operation,
    status: result.status,
    result,
    error: null,
    completion_unknown: false,
  })}\n`)
}

function errorResponse(
  operation: V4FactsMachineRequest['operation'],
  status: 'invalid' | 'unavailable' | 'error',
): Buffer {
  return Buffer.from(`${JSON.stringify({
    protocol_version: 1,
    operation,
    status,
    result: null,
    error: 'typed machine failure',
    completion_unknown: operation === 'create-spark' && status === 'error',
  })}\n`)
}

function fakeSpawn(
  observation: Observation,
  action: (child: FakeProcess) => void,
  config: FakeConfig = {},
): SpawnProcess {
  return (command, args, options) => {
    Object.assign(observation, { command, args, options })
    return new FakeProcess(observation, action, config)
  }
}

function closeWith(child: FakeProcess, raw: Buffer, code = 0, signal: NodeJS.Signals | null = null): void {
  child.stdout.end(raw)
  child.stderr.end()
  queueMicrotask(() => child.emit('close', code, signal))
}

test('transport invokes one isolated machine with closed stdin and a safe environment', async () => {
  const local = fixture()
  const observation: Observation = {}
  process.env.LDVH_SHOULD_NOT_LEAK = 'secret'
  try {
    const result = await invokeV4FactsMachine(request(), {
      pythonExecutable: local.executable,
      spawnProcess: fakeSpawn(observation, (child) => {
        const encoded = response('list-sparks')
        child.stdout.write(encoded.subarray(0, 7))
        child.stdout.end(encoded.subarray(7))
        child.stderr.end('diagnostic only')
        queueMicrotask(() => child.emit('close', 0, null))
      }),
    })

    assert.equal(result.status, 'complete')
    assert.equal(observation.command, local.executable)
    assert.deepEqual(observation.args, ['-I', '-X', 'utf8', '-m', 'ldvh.facts.web_machine'])
    assert.equal(observation.options?.cwd, path.dirname(local.executable))
    assert.equal(observation.options?.shell, false)
    assert.equal((observation.options?.env as NodeJS.ProcessEnv).LDVH_SHOULD_NOT_LEAK, undefined)
    assert.deepEqual(JSON.parse(observation.input?.toString('utf8') ?? ''), request())
  } finally {
    delete process.env.LDVH_SHOULD_NOT_LEAK
    local.cleanup()
  }
})

test('real transport runs through the ordinary project venv interpreter link', async () => {
  const repositoryRoot = path.resolve(import.meta.dirname, '../../..')
  const pythonExecutable = process.platform === 'win32'
    ? path.join(repositoryRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(repositoryRoot, '.venv', 'bin', 'python')
  assert.equal(fs.existsSync(pythonExecutable), true)
  const workspace = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-v4-real-transport-'))
  const project = path.join(workspace, 'project')
  fs.mkdirSync(project)
  execFileSync('git', ['init', '-q', project])
  fs.writeFileSync(
    path.join(workspace, 'LDVH-GOVERNED-PROJECTS.yaml'),
    [
      'product_name: Real transport',
      'product_description: Ordinary venv symlink integration.',
      'projects:',
      '  - id: sample',
      `    path: ${project}`,
      '    name: Sample',
      '    description: Real transport project.',
      '',
    ].join('\n'),
  )
  try {
    const observed = await invokeV4FactsMachine({
      protocol_version: 1,
      operation: 'list-sparks',
      scope: {
        workspace_root: workspace,
        worktree_locator: project,
        expected_governed_project_id: 'sample',
      },
      arguments: {},
    }, { pythonExecutable })

    assert.equal(observed.status, 'complete')
    assert.deepEqual((observed.result as { items: unknown[] }).items, [])
    const captured = await invokeV4FactsMachine({
      protocol_version: 1,
      operation: 'create-spark',
      scope: {
        workspace_root: workspace,
        worktree_locator: project,
        expected_governed_project_id: 'sample',
      },
      arguments: { title: 'Real bridge', description: 'Validate the real create result.', priority: 'P2' },
    }, { pythonExecutable })
    assert.equal(captured.status, 'created')
    const detail = await invokeV4FactsMachine({
      protocol_version: 1,
      operation: 'read-spark',
      scope: {
        workspace_root: workspace,
        worktree_locator: project,
        expected_governed_project_id: 'sample',
      },
      arguments: { object_id: 'spark-0001' },
    }, { pythonExecutable })
    assert.equal(detail.status, 'ok')
  } finally {
    fs.rmSync(workspace, { recursive: true, force: true })
  }
})

test('all operation result shapes and typed machine errors are runtime validated', async () => {
  const local = fixture()
  try {
    for (const operation of ['list-sparks', 'read-spark', 'create-spark'] as const) {
      const observed = await invokeV4FactsMachine(request(operation), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => closeWith(child, response(operation))),
      })
      assert.equal(observed.status, resultFor(operation).status)
    }
    for (const [operation, status] of [
      ['list-sparks', 'unavailable'],
      ['read-spark', 'invalid'],
      ['create-spark', 'error'],
    ] as const) {
      const observed = await invokeV4FactsMachine(request(operation), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => closeWith(child, errorResponse(operation, status))),
      })
      assert.equal(observed.status, status)
    }
  } finally {
    local.cleanup()
  }
})

test('framing, UTF-8, operation identity, status, and closed result shape fail closed', async () => {
  const local = fixture()
  const badResult = JSON.parse(response('list-sparks').toString('utf8'))
  delete badResult.result.structural_problems
  const badStatus = JSON.parse(response('list-sparks').toString('utf8'))
  badStatus.status = 'anything'
  badStatus.result.status = 'anything'
  const contradictoryItem = JSON.parse(response('list-sparks').toString('utf8'))
  contradictoryItem.result.items[0].fact_object = null
  const contradictoryNotFound = JSON.parse(response('read-spark').toString('utf8'))
  contradictoryNotFound.status = 'not_found'
  contradictoryNotFound.result.status = 'not_found'
  const contradictoryCreated = JSON.parse(response('create-spark').toString('utf8'))
  contradictoryCreated.result.actual_ref = null
  contradictoryCreated.result.canonical_path = null
  contradictoryCreated.result.fact_object = null
  try {
    for (const raw of [
      Buffer.from('{}\nextra\n'),
      response('read-spark'),
      Buffer.from([0xff, 0x0a]),
      Buffer.from(`${JSON.stringify(badResult)}\n`),
      Buffer.from(`${JSON.stringify(badStatus)}\n`),
      Buffer.from(`${JSON.stringify(contradictoryItem)}\n`),
      Buffer.from(`${JSON.stringify(contradictoryNotFound)}\n`),
      Buffer.from(`${JSON.stringify(contradictoryCreated)}\n`),
      Buffer.from('{"protocol_version":1}\n'),
    ]) {
      await assert.rejects(
        invokeV4FactsMachine(request(), {
          pythonExecutable: local.executable,
          spawnProcess: fakeSpawn({}, (child) => closeWith(child, raw)),
        }),
        (error: unknown) => error instanceof V4FactsTransportError
          && error.code === 'malformed_machine_response',
      )
    }
  } finally {
    local.cleanup()
  }
})

test('timeout is a hard upper bound even when kill fails and no close arrives', async () => {
  const local = fixture()
  let starts = 0
  const startedAt = Date.now()
  try {
    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        timeoutMs: 5,
        spawnProcess: fakeSpawn(
          {},
          () => { starts += 1 },
          { closeOnKill: false, killResult: false },
        ),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_timeout'
        && error.completionUnknown,
    )
    assert.equal(starts, 1)
    assert.ok(Date.now() - startedAt < 250)
  } finally {
    local.cleanup()
  }
})

test('safe interpreter validation accepts a verified symlink chain and rejects invalid targets', async () => {
  const local = fixture()
  const link = `${local.executable}-link`
  try {
    if (process.platform !== 'win32') {
      fs.symlinkSync(local.executable, link)
      const observation: Observation = {}
      await invokeV4FactsMachine(request(), {
        pythonExecutable: link,
        spawnProcess: fakeSpawn(observation, (child) => closeWith(child, response('list-sparks'))),
      })
      assert.equal(observation.command, link)
    }
    for (const executable of [
      'python',
      path.join(path.dirname(local.executable), 'missing'),
      path.dirname(local.executable),
    ]) {
      await assert.rejects(
        invokeV4FactsMachine(request(), { pythonExecutable: executable }),
        (error: unknown) => error instanceof V4FactsTransportError
          && error.code === 'invalid_python_executable',
      )
    }
  } finally {
    local.cleanup()
  }
})

test('request and stdout budgets fail before unbounded transport accumulation', async () => {
  const local = fixture()
  let spawned = false
  try {
    const oversized = request('create-spark')
    oversized.arguments.title = 'x'.repeat(12 * 1024 * 1024)
    await assert.rejects(
      invokeV4FactsMachine(oversized, {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, () => { spawned = true }),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_request_overflow',
    )
    assert.equal(spawned, false)

    for (const operation of ['list-sparks', 'create-spark'] as const) {
      await assert.rejects(
        invokeV4FactsMachine(request(operation), {
          pythonExecutable: local.executable,
          spawnProcess: fakeSpawn({}, (child) => {
            child.stdout.write(Buffer.alloc(32 * 1024 * 1024 + 1))
          }, { closeOnKill: false }),
        }),
        (error: unknown) => error instanceof V4FactsTransportError
          && error.code === 'transport_response_overflow'
          && error.completionUnknown === (operation === 'create-spark'),
      )
    }
  } finally {
    local.cleanup()
  }
})

test('spawn, process, and all stream error paths are typed with phase-aware completion', async () => {
  const local = fixture()
  try {
    const synchronousThrow: SpawnProcess = () => { throw new Error('sync spawn') }
    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        spawnProcess: synchronousThrow,
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_spawn_failed'
        && !error.completionUnknown,
    )

    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => child.emit('error', new Error('not started')), {
          emitSpawn: false,
        }),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_spawn_failed'
        && !error.completionUnknown,
    )

    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => {
          setImmediate(() => child.emit('error', new Error('started process failed')))
        }),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_process_error'
        && error.completionUnknown,
    )

    for (const [stream, code] of [
      ['stdin', 'transport_stdin_error'],
      ['stdout', 'transport_stdout_error'],
      ['stderr', 'transport_stderr_error'],
    ] as const) {
      await assert.rejects(
        invokeV4FactsMachine(request('create-spark'), {
          pythonExecutable: local.executable,
          spawnProcess: fakeSpawn({}, (child) => setImmediate(
            () => child[stream].emit('error', new Error(`${stream} failed`)),
          ), {
            closeOnKill: false,
          }),
        }),
        (error: unknown) => error instanceof V4FactsTransportError
          && error.code === code
          && error.completionUnknown,
      )
    }

    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => child.stdin.emit('error', new Error('pre-spawn stdin')), {
          emitSpawn: false,
          closeOnKill: false,
        }),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'transport_stdin_error'
        && !error.completionUnknown,
    )
  } finally {
    local.cleanup()
  }
})

test('nonzero exit and signal cap diagnostics and preserve create uncertainty', async () => {
  const local = fixture()
  try {
    for (const [code, signal] of [[7, null], [null, 'SIGTERM']] as const) {
      let observed: unknown
      try {
        await invokeV4FactsMachine(request('create-spark'), {
          pythonExecutable: local.executable,
          spawnProcess: fakeSpawn({}, (child) => {
            child.stderr.end('x'.repeat(70 * 1024))
            child.stdout.end()
            queueMicrotask(() => child.emit('close', code, signal))
          }),
        })
      } catch (error) {
        observed = error
      }
      assert.ok(observed instanceof V4FactsTransportError)
      assert.equal(observed.code, 'transport_process_failed')
      assert.equal(observed.completionUnknown, true)
      assert.equal(observed.diagnostic.length, 64 * 1024)
    }
  } finally {
    local.cleanup()
  }
})

test('malformed create response is completion-unknown after the process ran', async () => {
  const local = fixture()
  try {
    await assert.rejects(
      invokeV4FactsMachine(request('create-spark'), {
        pythonExecutable: local.executable,
        spawnProcess: fakeSpawn({}, (child) => closeWith(child, Buffer.from('{}\n'))),
      }),
      (error: unknown) => error instanceof V4FactsTransportError
        && error.code === 'malformed_machine_response'
        && error.completionUnknown,
    )
  } finally {
    local.cleanup()
  }
})
