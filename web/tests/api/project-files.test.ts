import assert from 'node:assert/strict'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import os from 'node:os'
import path from 'node:path'
import { after, before, test } from 'node:test'

const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-project-files-workspace-'))
const projectRoot = path.join(workspaceRoot, 'demo')
fs.mkdirSync(path.join(projectRoot, 'assets'), { recursive: true })
fs.mkdirSync(path.join(projectRoot, '.private'), { recursive: true })

process.env.LDVH_ROOT = projectRoot
process.env.LDVH_WORKSPACE_ROOT = workspaceRoot

fs.writeFileSync(
  path.join(workspaceRoot, 'LDVH-GOVERNED-PROJECTS.yaml'),
  ['projects:', '  - id: demo', '    name: Demo', '    description: Demo project', '    path: ./demo', ''].join('\n'),
)

const svgContent = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5"/></svg>\n'
fs.writeFileSync(path.join(projectRoot, 'assets', 'mark.svg'), svgContent)
fs.writeFileSync(path.join(projectRoot, 'README.md'), '# Demo\n')
fs.writeFileSync(path.join(projectRoot, '.private', 'secret.md'), 'hidden\n')
fs.writeFileSync(path.join(projectRoot, 'large.txt'), `${'a'.repeat(310 * 1024)}tail`)
fs.writeFileSync(path.join(projectRoot, 'binary.bin'), Buffer.from([0x41, 0x00, 0x42]))

let server: Server
let baseUrl = ''

before(async () => {
  const { default: app } = await import('../../api/app.ts')
  server = app.listen(0)
  const address = server.address() as AddressInfo
  baseUrl = `http://127.0.0.1:${address.port}`
})

after(async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve())
  })
  fs.rmSync(workspaceRoot, { recursive: true, force: true })
})

async function get(pathname: string) {
  const response = await fetch(`${baseUrl}${pathname}`)
  const body = await response.json() as Record<string, unknown>
  return { response, body }
}

test('lists and reads the current supported file kinds', async () => {
  const entries = await get('/api/project-files/entries?projectId=demo&dir=assets')
  assert.equal(entries.response.status, 200)
  const listed = entries.body.entries as Array<Record<string, unknown>>
  assert.equal(listed.length, 1)
  assert.equal(listed[0].name, 'mark.svg')
  assert.equal(listed[0].kind, 'svg')

  const file = await get('/api/project-files/content?projectId=demo&path=assets%2Fmark.svg')
  assert.equal(file.response.status, 200)
  assert.equal(file.body.kind, 'svg')
  assert.equal(file.body.content, svgContent)
  assert.equal(file.body.truncated, false)
})

test('preserves hidden-file and lexical traversal responses', async () => {
  const hidden = await get('/api/project-files/content?projectId=demo&path=.private%2Fsecret.md')
  assert.equal(hidden.response.status, 403)
  assert.equal(hidden.body.error, 'Hidden file is not visible')

  const visible = await get('/api/project-files/content?projectId=demo&path=.private%2Fsecret.md&showHidden=true')
  assert.equal(visible.response.status, 200)
  assert.equal(visible.body.content, 'hidden\n')

  const traversal = await get('/api/project-files/content?projectId=demo&path=..%2FLDVH-GOVERNED-PROJECTS.yaml')
  assert.equal(traversal.response.status, 403)
  assert.equal(traversal.body.error, 'Invalid file path')
})

test('preserves truncation and binary responses', async () => {
  const large = await get('/api/project-files/content?projectId=demo&path=large.txt')
  assert.equal(large.response.status, 200)
  assert.equal(large.body.kind, 'text')
  assert.equal(large.body.truncated, true)
  assert.equal(String(large.body.content).length, 300 * 1024)

  const binary = await get('/api/project-files/content?projectId=demo&path=binary.bin')
  assert.equal(binary.response.status, 200)
  assert.equal(binary.body.kind, 'binary')
  assert.equal(binary.body.content, '')
  assert.equal(binary.body.truncated, false)
})
