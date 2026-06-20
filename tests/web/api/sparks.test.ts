import assert from 'node:assert/strict'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { createRequire } from 'node:module'
import os from 'node:os'
import path from 'node:path'

const requireFromWeb = createRequire(new URL('../../../web/package.json', import.meta.url))
const yaml = requireFromWeb('js-yaml') as typeof import('js-yaml')

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-sparks-api-'))
process.env.LDVH_ROOT = tempRoot

const sparksDir = path.join(tempRoot, 'ldvh-base', 'sparks')
fs.mkdirSync(sparksDir, { recursive: true })

let server: Server
let baseUrl = ''

type MutableFs = typeof fs & {
  existsSync: typeof fs.existsSync
  readFileSync: typeof fs.readFileSync
}

const mutableFs = fs as MutableFs

function resetSparksDir() {
  fs.rmSync(sparksDir, { recursive: true, force: true })
  fs.mkdirSync(sparksDir, { recursive: true })
}

async function postSpark(body: Record<string, unknown>) {
  return fetch(`${baseUrl}/api/sparks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function validSpark(overrides: Record<string, unknown> = {}) {
  return {
    title: 'API Spark',
    description: 'Captured from the Web spark quick entry.',
    priority: 'P1',
    ...overrides,
  }
}

async function closeServer() {
  await new Promise<void>((resolve, reject) => {
    server.close((err) => {
      if (err) reject(err)
      else resolve()
    })
  })
}

async function testCreateSpark() {
  resetSparksDir()

  const response = await postSpark(validSpark())
  const payload = await response.json() as Record<string, unknown>

  assert.equal(response.status, 201)
  assert.equal(payload.ok, true)
  assert.equal(payload.action, 'create')
  assert.deepEqual(payload.summary, { id: 'spark-0001', type: 'spark', status: 'pending' })

  const files = fs.readdirSync(sparksDir)
  assert.deepEqual(files, ['spark-0001-api-spark.yaml'])
  const persisted = yaml.load(
    fs.readFileSync(path.join(sparksDir, files[0]), 'utf-8'),
    { schema: yaml.JSON_SCHEMA },
  ) as Record<string, unknown>
  assert.equal(persisted.id, 'spark-0001')
  assert.equal(persisted.status, 'pending')
  assert.equal(persisted.source, 'web')
  assert.match(String(persisted.created), /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/)
  assert.match(String(persisted.updated), /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/)
  assert.equal(persisted.source_detail, '')
  assert.deepEqual(persisted.evolution, [])
  assert.deepEqual(persisted.related_studies, [])
  assert.equal('category' in persisted, false)
  assert.equal('status_history' in persisted, false)
}

async function testFieldValidation() {
  resetSparksDir()

  const response = await postSpark({ title: 'Incomplete' })
  const payload = await response.json() as { ok: boolean, errors: string[] }

  assert.equal(response.status, 400)
  assert.equal(payload.ok, false)
  assert.ok(payload.errors.includes('description is required'))
  assert.ok(payload.errors.some((error) => error.startsWith('priority must be one of:')))
  assert.deepEqual(fs.readdirSync(sparksDir), [])
}

async function testFileConflict() {
  resetSparksDir()
  const originalExistsSync = fs.existsSync
  mutableFs.existsSync = ((target: fs.PathLike) => {
    if (typeof target === 'string' && target.endsWith(`${path.sep}spark-0001-conflict.yaml`)) {
      return true
    }
    return originalExistsSync(target)
  }) as typeof fs.existsSync

  try {
    const response = await postSpark(validSpark({ title: 'Conflict' }))
    const payload = await response.json() as Record<string, unknown>

    assert.equal(response.status, 409)
    assert.equal(payload.ok, false)
    assert.equal(payload.code, 'SPARK_FILE_CONFLICT')
    assert.deepEqual(fs.readdirSync(sparksDir), [])
  } finally {
    mutableFs.existsSync = originalExistsSync
  }
}

async function testWriteVerificationFailure() {
  resetSparksDir()
  const originalReadFileSync = fs.readFileSync
  mutableFs.readFileSync = ((target: fs.PathOrFileDescriptor, options?: unknown) => {
    if (typeof target === 'string' && target.endsWith(`${path.sep}spark-0001-verify-fail.yaml`)) {
      return 'id: spark-0001\ntype: spark\nstatus: resolved\n'
    }
    return originalReadFileSync(target, options as never)
  }) as typeof fs.readFileSync

  try {
    const response = await postSpark(validSpark({ title: 'Verify Fail' }))
    const payload = await response.json() as { ok: boolean, code: string, errors: string[] }

    assert.equal(response.status, 500)
    assert.equal(payload.ok, false)
    assert.equal(payload.code, 'SPARK_WRITE_VERIFY_FAILED')
    assert.ok(payload.errors.includes('status must be pending'))
  } finally {
    mutableFs.readFileSync = originalReadFileSync
  }
}

async function main() {
  const { default: app } = await import('../../../web/api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`

  await testCreateSpark()
  await testFieldValidation()
  await testFileConflict()
  await testWriteVerificationFailure()
}

main()
  .catch((error) => {
    console.error(error)
    process.exitCode = 1
  })
  .finally(async () => {
    if (server) {
      await closeServer()
    }
    fs.rmSync(tempRoot, { recursive: true, force: true })
  })
