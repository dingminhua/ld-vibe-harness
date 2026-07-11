import assert from 'node:assert/strict'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import os from 'node:os'
import path from 'node:path'

const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-project-files-workspace-'))
const projectRoot = path.join(workspaceRoot, 'demo')
fs.mkdirSync(path.join(projectRoot, 'assets'), { recursive: true })
fs.mkdirSync(path.join(projectRoot, '.private'), { recursive: true })

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
fs.writeFileSync(
  path.join(projectRoot, 'LDVH-GOVERNED-PROJECTS.yaml'),
  [
    'projects:',
    '  - id: legacy',
    '    name: Legacy',
    '    description: Legacy project-local config should not win',
    '    path: .',
    '',
  ].join('\n'),
)

const svgContent = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5"/></svg>\n'
fs.writeFileSync(path.join(projectRoot, 'assets', 'mark.svg'), svgContent)
fs.writeFileSync(path.join(projectRoot, 'README.md'), '# Demo\n')
fs.writeFileSync(path.join(projectRoot, '.private', 'secret.md'), 'hidden\n')
fs.writeFileSync(path.join(projectRoot, 'large.txt'), `${'a'.repeat(310 * 1024)}tail`)
fs.writeFileSync(path.join(projectRoot, 'binary.bin'), Buffer.from([0x41, 0x00, 0x42]))

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

async function getJson(pathname: string) {
  const response = await fetch(`${baseUrl}${pathname}`)
  assert.equal(response.status, 200)
  return await response.json() as unknown
}

async function getResponse(pathname: string) {
  const response = await fetch(`${baseUrl}${pathname}`)
  const body = await response.json() as Record<string, unknown>
  return { response, body }
}

async function main() {
  const { default: app } = await import('../../../web/api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`

  const entries = await getJson('/api/project-files/entries?projectId=demo&dir=assets') as {
    entries: Array<Record<string, unknown>>
  }
  assert.equal(entries.entries.length, 1)
  assert.equal(entries.entries[0].name, 'mark.svg')
  assert.equal(entries.entries[0].kind, 'svg')

  const file = await getJson('/api/project-files/content?projectId=demo&path=assets%2Fmark.svg') as Record<string, unknown>
  assert.equal(file.kind, 'svg')
  assert.equal(file.content, svgContent)
  assert.equal(file.truncated, false)

  const rootEntries = await getJson('/api/project-files/entries?projectId=demo') as {
    entries: Array<Record<string, unknown>>
    parent: string
    dir: string
  }
  assert.equal(rootEntries.dir, '')
  assert.equal(rootEntries.parent, '')
  assert.deepEqual(rootEntries.entries.map((entry) => entry.name), [
    'assets',
    'binary.bin',
    'large.txt',
    'LDVH-GOVERNED-PROJECTS.yaml',
    'README.md',
  ])
  assert.equal(rootEntries.entries.find((entry) => entry.name === 'assets')?.type, 'directory')
  assert.equal(rootEntries.entries.find((entry) => entry.name === 'README.md')?.kind, 'markdown')

  const hiddenEntries = await getJson('/api/project-files/entries?projectId=demo&showHidden=true') as {
    entries: Array<Record<string, unknown>>
  }
  assert.ok(hiddenEntries.entries.some((entry) => entry.name === '.private'))

  const hiddenBlocked = await getResponse('/api/project-files/content?projectId=demo&path=.private%2Fsecret.md')
  assert.equal(hiddenBlocked.response.status, 403)
  assert.equal(hiddenBlocked.body.error, 'Hidden file is not visible')

  const hiddenFile = await getJson('/api/project-files/content?projectId=demo&path=.private%2Fsecret.md&showHidden=true') as Record<string, unknown>
  assert.equal(hiddenFile.content, 'hidden\n')

  const traversal = await getResponse('/api/project-files/content?projectId=demo&path=..%2FLDVH-GOVERNED-PROJECTS.yaml')
  assert.equal(traversal.response.status, 403)
  assert.equal(traversal.body.error, 'Invalid file path')

  const largeFile = await getJson('/api/project-files/content?projectId=demo&path=large.txt') as Record<string, unknown>
  assert.equal(largeFile.kind, 'text')
  assert.equal(largeFile.truncated, true)
  assert.equal(String(largeFile.content).length, 300 * 1024)

  const binaryFile = await getJson('/api/project-files/content?projectId=demo&path=binary.bin') as Record<string, unknown>
  assert.equal(binaryFile.kind, 'binary')
  assert.equal(binaryFile.content, '')
  assert.equal(binaryFile.truncated, false)
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
