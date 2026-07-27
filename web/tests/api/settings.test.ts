import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import type { AddressInfo } from 'node:net'
import type { Server } from 'node:http'
import os from 'node:os'
import path from 'node:path'
import { after, before, test } from 'node:test'

const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-settings-workspace-'))
const firstProject = path.join(workspaceRoot, 'first')
const secondProject = path.join(workspaceRoot, 'second')
const configPath = path.join(workspaceRoot, 'LDVH-GOVERNED-PROJECTS.yaml')
const repositoryRoot = path.resolve(import.meta.dirname, '../../..')

fs.mkdirSync(firstProject, { recursive: true })
fs.mkdirSync(secondProject, { recursive: true })
execFileSync('git', ['init', '-q', firstProject])
execFileSync('git', ['init', '-q', secondProject])
fs.writeFileSync(configPath, [
  '# Settings test configuration.',
  'product_name: Settings test',
  'product_description: A governed-project configuration fixture.',
  'projects:',
  '  - id: first',
  `    path: ${firstProject}`,
  '    name: First project',
  '    description: This description must survive a name edit.',
  '',
].join('\n'))

process.env.LDVH_ROOT = firstProject
process.env.LDVH_WORKSPACE_ROOT = workspaceRoot
process.env.LDVH_HELPER_EXECUTABLE = process.platform === 'win32'
  ? path.join(repositoryRoot, '.venv', 'Scripts', 'ldvh.exe')
  : path.join(repositoryRoot, '.venv', 'bin', 'ldvh')
process.env.LDVH_WEB_WORKTREE_LOCATOR = firstProject

let server: Server
let baseUrl = ''

before(async () => {
  const { default: app } = await import('../../api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`
})

after(async () => {
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()))
  fs.rmSync(workspaceRoot, { recursive: true, force: true })
})

async function request(pathname: string, init?: RequestInit) {
  const response = await fetch(`${baseUrl}${pathname}`, init)
  return { response, body: await response.json() as Record<string, unknown> }
}

test('reads the editable project projection without changing the configuration', async () => {
  const { response, body } = await request('/api/settings/governed-projects')
  assert.equal(response.status, 200)
  assert.equal(body.ok, true)
  assert.equal(body.configPath, configPath)
  assert.deepEqual(body.projects, [{ id: 'first', path: firstProject, name: 'First project' }])
  assert.match(fs.readFileSync(configPath, 'utf8'), /description: This description must survive/)
})

test('renames, adds and removes entries while preserving unmanaged description fields', async () => {
  const initial = await request('/api/settings/governed-projects')
  const fingerprint = String(initial.body.fingerprint)
  const update = await request('/api/settings/governed-projects', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expectedFingerprint: fingerprint,
      projects: [
        { id: 'first', path: firstProject, name: 'Renamed project' },
        { id: 'second', path: secondProject, name: 'Second project' },
      ],
    }),
  })
  assert.equal(update.response.status, 200)
  assert.deepEqual(update.body.projects, [
    { id: 'first', path: firstProject, name: 'Renamed project' },
    { id: 'second', path: secondProject, name: 'Second project' },
  ])
  assert.match(fs.readFileSync(configPath, 'utf8'), /description: This description must survive a name edit\./)

  const remove = await request('/api/settings/governed-projects', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expectedFingerprint: update.body.fingerprint,
      projects: [{ id: 'second', path: secondProject, name: 'Second project' }],
    }),
  })
  assert.equal(remove.response.status, 200)
  assert.deepEqual(remove.body.projects, [{ id: 'second', path: secondProject, name: 'Second project' }])
})

test('rejects stale or invalid updates and leaves the configuration untouched', async () => {
  const current = await request('/api/settings/governed-projects')
  const beforeContent = fs.readFileSync(configPath, 'utf8')
  const stale = await request('/api/settings/governed-projects', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ expectedFingerprint: 'stale', projects: current.body.projects }),
  })
  assert.equal(stale.response.status, 422)

  const invalid = await request('/api/settings/governed-projects', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expectedFingerprint: current.body.fingerprint,
      projects: [{ id: 'not-a-worktree', path: path.join(workspaceRoot, 'missing'), name: 'Broken' }],
    }),
  })
  assert.equal(invalid.response.status, 422)
  assert.equal(fs.readFileSync(configPath, 'utf8'), beforeContent)
})
