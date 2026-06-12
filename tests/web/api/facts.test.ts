import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'

const fixtureRoot = fileURLToPath(new URL('../fixtures/taskplan-with-subtasks', import.meta.url))

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

  const fixturePlans = await listObjects('taskplan', fixtureRoot)
  assert.equal(fixturePlans.ok, true)
  assert.equal(fixturePlans.data.items.length, 1)
  assert.equal((fixturePlans.data.items[0] as Record<string, unknown>).id, 'taskplan-9001')

  const fixtureTasks = await listObjects('task', fixtureRoot)
  assert.equal(fixtureTasks.ok, true)
  const taskStatuses = new Set((fixtureTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(taskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))

  const fixtureSubTasks = await listObjects('subtask', fixtureRoot)
  assert.equal(fixtureSubTasks.ok, true)
  const subtaskStatuses = new Set((fixtureSubTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(subtaskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
