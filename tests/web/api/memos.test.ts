import assert from 'node:assert/strict'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { createRequire } from 'node:module'
import os from 'node:os'
import path from 'node:path'

const requireFromWeb = createRequire(new URL('../../../web/package.json', import.meta.url))
const yaml = requireFromWeb('js-yaml') as typeof import('js-yaml')

const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-memos-api-'))
process.env.LDVH_ROOT = tempRoot

const memosDir = path.join(tempRoot, 'ldvh-base', 'memos')
fs.mkdirSync(memosDir, { recursive: true })

let server: Server
let baseUrl = ''

type MutableFs = typeof fs & {
  existsSync: typeof fs.existsSync
  readFileSync: typeof fs.readFileSync
}

const mutableFs = fs as MutableFs

function resetMemosDir() {
  fs.rmSync(memosDir, { recursive: true, force: true })
  fs.mkdirSync(memosDir, { recursive: true })
}

async function postMemo(body: Record<string, unknown>) {
  return fetch(`${baseUrl}/api/memos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function validMemo(overrides: Record<string, unknown> = {}) {
  return {
    title: 'API Memo',
    description: 'Captured from the Web memo quick entry.',
    source: 'human test',
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

async function testCreateMemo() {
  resetMemosDir()

  const response = await postMemo(validMemo())
  const payload = await response.json() as Record<string, unknown>

  assert.equal(response.status, 201)
  assert.equal(payload.ok, true)
  assert.equal(payload.action, 'create')
  assert.deepEqual(payload.summary, { id: 'memo-0001', type: 'memo', status: 'pending' })

  const files = fs.readdirSync(memosDir)
  assert.deepEqual(files, ['memo-0001-api-memo.yaml'])
  const persisted = yaml.load(
    fs.readFileSync(path.join(memosDir, files[0]), 'utf-8'),
  ) as Record<string, unknown>
  assert.equal(persisted.id, 'memo-0001')
  assert.equal(persisted.status, 'pending')
  assert.equal('category' in persisted, false)
  assert.ok(Array.isArray(persisted.status_history))
}

async function testFieldValidation() {
  resetMemosDir()

  const response = await postMemo({ title: 'Incomplete' })
  const payload = await response.json() as { ok: boolean, errors: string[] }

  assert.equal(response.status, 400)
  assert.equal(payload.ok, false)
  assert.ok(payload.errors.includes('description is required'))
  assert.ok(payload.errors.includes('source is required'))
  assert.ok(payload.errors.some((error) => error.startsWith('priority must be one of:')))
  assert.deepEqual(fs.readdirSync(memosDir), [])
}

async function testFileConflict() {
  resetMemosDir()
  const originalExistsSync = fs.existsSync
  mutableFs.existsSync = ((target: fs.PathLike) => {
    if (typeof target === 'string' && target.endsWith(`${path.sep}memo-0001-conflict.yaml`)) {
      return true
    }
    return originalExistsSync(target)
  }) as typeof fs.existsSync

  try {
    const response = await postMemo(validMemo({ title: 'Conflict' }))
    const payload = await response.json() as Record<string, unknown>

    assert.equal(response.status, 409)
    assert.equal(payload.ok, false)
    assert.equal(payload.code, 'MEMO_FILE_CONFLICT')
    assert.deepEqual(fs.readdirSync(memosDir), [])
  } finally {
    mutableFs.existsSync = originalExistsSync
  }
}

async function testWriteVerificationFailure() {
  resetMemosDir()
  const originalReadFileSync = fs.readFileSync
  mutableFs.readFileSync = ((target: fs.PathOrFileDescriptor, options?: unknown) => {
    if (typeof target === 'string' && target.endsWith(`${path.sep}memo-0001-verify-fail.yaml`)) {
      return 'id: memo-0001\ntype: memo\nstatus: resolved\n'
    }
    return originalReadFileSync(target, options as never)
  }) as typeof fs.readFileSync

  try {
    const response = await postMemo(validMemo({ title: 'Verify Fail' }))
    const payload = await response.json() as { ok: boolean, code: string, errors: string[] }

    assert.equal(response.status, 500)
    assert.equal(payload.ok, false)
    assert.equal(payload.code, 'MEMO_WRITE_VERIFY_FAILED')
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

  await testCreateMemo()
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
