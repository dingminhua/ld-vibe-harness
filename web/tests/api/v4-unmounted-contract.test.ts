import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { test } from 'node:test'

const webRoot = path.resolve(import.meta.dirname, '../..')

test('V4 bridge remains absent from the production route graph', async () => {
  for (const relative of ['api/app.ts', 'api/routes/sparks.ts', 'api/routes/objects.ts', 'api/services/facts.ts']) {
    const source = fs.readFileSync(path.join(webRoot, relative), 'utf8')
    assert.doesNotMatch(source, /v4Facts|v4Spark|V4Facts|V4Spark/)
  }

  const { default: app } = await import('../../api/app.ts')
  const server = app.listen(0)
  try {
    const address = server.address()
    assert.ok(address && typeof address === 'object')
    const response = await fetch(`http://127.0.0.1:${address.port}/api/v4/sparks`)
    assert.equal(response.status, 404)
    assert.deepEqual(await response.json(), { success: false, error: 'API not found' })
  } finally {
    await new Promise<void>((resolve, reject) => {
      server.close((error) => error ? reject(error) : resolve())
    })
  }
})

test('this stage does not modify the frozen presentation tree', () => {
  const changed = execFileSync(
    'git',
    ['diff', '--name-only', 'HEAD', '--', 'web/src'],
    { cwd: path.dirname(webRoot), encoding: 'utf8' },
  )
    .trim()
  assert.equal(changed, '')
})
