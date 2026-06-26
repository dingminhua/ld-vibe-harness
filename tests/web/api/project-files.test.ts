import assert from 'node:assert/strict'
import fs from 'node:fs'
import type { Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import os from 'node:os'
import path from 'node:path'

const workspaceRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-project-files-workspace-'))
const projectRoot = path.join(workspaceRoot, 'demo')
fs.mkdirSync(path.join(projectRoot, 'assets'), { recursive: true })

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

const svgContent = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 12"><circle cx="6" cy="6" r="5"/></svg>\n'
fs.writeFileSync(path.join(projectRoot, 'assets', 'mark.svg'), svgContent)

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
