import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'
import { buildPlanSummaries, type ListedObject } from '../../../web/api/routes/objects.ts'

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

  const fixtureWorkareas = await listObjects('workarea', fixtureRoot)
  assert.equal(fixtureWorkareas.ok, true)
  assert.equal(fixtureWorkareas.data.items.length, 4)
  const fixtureWorkareaStatuses = new Set((fixtureWorkareas.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(fixtureWorkareaStatuses, new Set(['active', 'archived']))

  const fixturePlans = await listObjects('taskplan', fixtureRoot)
  assert.equal(fixturePlans.ok, true)
  assert.equal(fixturePlans.data.items.length, 6)
  const fixturePlanIds = new Set((fixturePlans.data.items as Array<Record<string, unknown>>).map((item) => item.id))
  assert.deepEqual(fixturePlanIds, new Set([
    'taskplan-9001',
    'taskplan-9002',
    'taskplan-9003',
    'taskplan-9004',
    'taskplan-9005',
    'taskplan-9006',
  ]))
  const activeFixturePlans = await listObjects('taskplan', fixtureRoot, 'active')
  assert.equal(activeFixturePlans.ok, true)
  assert.equal(activeFixturePlans.data.items.length, 4)

  const fixtureTasks = await listObjects('task', fixtureRoot)
  assert.equal(fixtureTasks.ok, true)
  assert.equal(fixtureTasks.data.items.length, 25)
  const taskStatuses = new Set((fixtureTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(taskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))

  const fixtureSubTasks = await listObjects('subtask', fixtureRoot)
  assert.equal(fixtureSubTasks.ok, true)
  assert.equal(fixtureSubTasks.data.items.length, 22)
  const subtaskStatuses = new Set((fixtureSubTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(subtaskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))

  const planSummaries = await buildPlanSummaries(fixturePlans.data.items as ListedObject[], fixtureRoot)
  assert.equal(planSummaries.length, 6)
  const complexPlan = planSummaries.find((plan) => plan.id === 'taskplan-9001')
  assert.ok(complexPlan)
  assert.equal(complexPlan.tasks.length, 10)
  const taskWithSubtasks = complexPlan.tasks.find((task) => task.id === 'task-9002')
  assert.ok(taskWithSubtasks)
  assert.equal(taskWithSubtasks.subtasks?.length, 5)
  const nestedStatuses = new Set(taskWithSubtasks.subtasks?.map((item) => item.status))
  assert.deepEqual(nestedStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))
  const waitingSubtask = taskWithSubtasks.subtasks?.find((item) => item.id === 'subtask-9005')
  assert.equal(waitingSubtask?.openBlockers?.[0]?.id, 'subtask-9002')
  const parallelTask = complexPlan.tasks.find((task) => task.id === 'task-9006')
  assert.equal(parallelTask?.subtasks?.length, 3)
  const verifyingTask = complexPlan.tasks.find((task) => task.id === 'task-9008')
  assert.equal(verifyingTask?.subtasks?.length, 3)
  const noSubtaskTask = complexPlan.tasks.find((task) => task.id === 'task-9007')
  assert.equal(noSubtaskTask?.subtasks, undefined)
  const parallelPlan = planSummaries.find((plan) => plan.id === 'taskplan-9003')
  assert.equal(parallelPlan?.workarea, 'workarea-9002')
  assert.equal(parallelPlan?.tasks.find((task) => task.id === 'task-9032')?.subtasks?.length, 4)
  const verificationPlan = planSummaries.find((plan) => plan.id === 'taskplan-9004')
  assert.equal(verificationPlan?.workarea, 'workarea-9003')
  assert.equal(verificationPlan?.tasks.find((task) => task.id === 'task-9042')?.subtasks?.length, 3)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
