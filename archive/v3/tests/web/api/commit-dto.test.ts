import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import os from 'node:os'
import path from 'node:path'

const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-commit-dto-workspace-'))
const projectRoot = path.join(workspaceRoot, 'demo')
fs.mkdirSync(projectRoot, { recursive: true })

process.env.LDVH_ROOT = projectRoot
process.env.LDVH_WORKSPACE_ROOT = workspaceRoot

fs.writeFileSync(
  path.join(workspaceRoot, 'LDVH-GOVERNED-PROJECTS.yaml'),
  [
    'projects:',
    '  - id: demo',
    '    name: Demo',
    '    description: Demo project',
    '    path: ./demo',
    '',
  ].join('\n'),
)

function git(args: string[]) {
  return execFileSync('git', args, { cwd: projectRoot, encoding: 'utf-8' }).trim()
}

git(['init'])
git(['config', 'user.email', 'tester@example.com'])
git(['config', 'user.name', 'Tester'])

fs.writeFileSync(path.join(projectRoot, 'README.md'), '# Demo\n')
git(['add', 'README.md'])
git([
  'commit',
  '-m',
  'feat(web)!: 调整提交接口',
  '-m',
  [
    '动机:',
    '- 统一 Changelog、Dashboard 和 ProjectFiles 的提交记录结构。',
    '',
    '验证结论:',
    '- 已确认契约测试覆盖结构化字段。',
  ].join('\n'),
])

let server: Server
let baseUrl = ''

async function closeServer() {
  await new Promise<void>((resolve, reject) => {
    server.close((err) => {
      if (err) reject(err)
      else resolve()
    })
  })
}

function assertCommitDto(entry: Record<string, unknown>) {
  assert.equal(typeof entry.hash, 'string')
  assert.equal(typeof entry.shortHash, 'string')
  assert.equal(entry.message, 'feat(web)!: 调整提交接口')
  assert.equal(entry.category, 'feat')
  assert.equal(entry.scope, 'web')
  assert.equal(entry.description, '调整提交接口')
  assert.equal(entry.isBreaking, true)
  assert.equal(typeof entry.body, 'string')
  assert.match(String(entry.body), /动机:/)
  assert.match(String(entry.body), /验证结论:/)
}

async function getJson(pathname: string) {
  const response = await fetch(`${baseUrl}${pathname}`)
  assert.equal(response.status, 200)
  return await response.json() as unknown
}

async function main() {
  const { default: app } = await import('../../../web/api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`

  const changelog = await getJson('/api/changelog?count=1&locale=zh') as Array<Record<string, unknown>>
  assert.equal(changelog.length, 1)
  assertCommitDto(changelog[0])

  const dashboard = await getJson('/api/dashboard?locale=zh') as { recentChanges: Array<Record<string, unknown>> }
  assert.equal(dashboard.recentChanges.length, 1)
  assertCommitDto(dashboard.recentChanges[0])

  const commits = await getJson('/api/project-files/git/commits?projectId=demo&count=1') as {
    entries: Array<Record<string, unknown>>
  }
  assert.equal(commits.entries.length, 1)
  assertCommitDto(commits.entries[0])
  assert.deepEqual(commits.entries[0].parents, [])
  assert.equal(commits.entries[0].isMerge, false)

  const hash = String(commits.entries[0].hash)
  const detail = await getJson(`/api/project-files/git/commit/${hash}?projectId=demo`) as {
    commit: Record<string, unknown>
  }
  assertCommitDto(detail.commit)
  assert.deepEqual(detail.commit.parents, [])
  assert.equal(detail.commit.isMerge, false)
  assert.deepEqual(detail.commit.files, [{
    status: 'A',
    path: 'README.md',
    absolutePath: path.join(projectRoot, 'README.md'),
  }])
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
    fs.rmSync(workspaceRoot, { recursive: true, force: true })
  })
