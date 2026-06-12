import assert from 'node:assert/strict'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'

async function main() {
  const workareas = await listObjects('workarea')
  assert.equal(workareas.ok, true)
  assert.ok(Array.isArray(workareas.data.items))
  assert.ok(workareas.data.items.length > 0)

  const firstWorkarea = workareas.data.items[0] as Record<string, unknown>
  assert.equal(typeof firstWorkarea.id, 'string')
  assert.equal(firstWorkarea.type, 'workarea')
  assert.equal(typeof firstWorkarea.path, 'string')
  assert.ok(String(firstWorkarea.path).includes('/ldvh-base/workareas/'))

  const activeWorkareas = await listObjects('workarea', undefined, 'active')
  assert.equal(activeWorkareas.ok, true)
  for (const item of activeWorkareas.data.items as Array<Record<string, unknown>>) {
    assert.equal(item.status, 'active')
  }

  const detail = await showObject(String(firstWorkarea.id))
  assert.equal(detail.ok, true)
  assert.equal(detail.data.id, firstWorkarea.id)
  assert.equal(detail.summary.id, firstWorkarea.id)
  assert.equal(typeof detail.data.path, 'string')

  const missing = await showObject('workarea-9999')
  assert.equal(missing.ok, false)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
