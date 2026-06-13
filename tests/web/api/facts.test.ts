import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import yaml from 'js-yaml'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'
import { buildPlanSummaries, type ListedObject } from '../../../web/api/routes/objects.ts'

const fixtureRoot = fileURLToPath(new URL('../fixtures/taskplan-with-subtasks', import.meta.url))
const projectRoot = path.resolve(fixtureRoot, '../../../..')

const FIXTURE_ALLOWED_FIELDS: Record<string, Set<string>> = {
  workarea: new Set([
    'id', 'type', 'title', 'title_en', 'title_zh', 'status', 'created', 'updated',
    'description', 'scope', 'constraints', 'source',
    'related_docs', 'related_adrs', 'related_memos', 'related_pitfalls',
    'status_history', 'archive_reason',
  ]),
  taskplan: new Set([
    'id', 'type', 'title', 'title_en', 'title_zh', 'status', 'created', 'updated',
    'workarea', 'description', 'success_criteria', 'source', 'tasks',
    'related_docs', 'related_adrs', 'related_memos', 'related_pitfalls',
    'status_history', 'review_requested_at', 'completion_evidence', 'closed_at',
  ]),
  task: new Set([
    'id', 'type', 'title', 'title_en', 'title_zh', 'status', 'created', 'updated',
    'taskplan', 'description', 'source', 'blocked_by', 'acceptance', 'verification',
    'risk_assessment', 'assignee', 'related_adrs', 'related_changes', 'related_docs',
    'affected_docs', 'deliverables', 'status_history', 'closed_at', 'closure_evidence',
  ]),
  subtask: new Set([
    'id', 'type', 'title', 'title_en', 'title_zh', 'status', 'created', 'updated',
    'task', 'description', 'source', 'acceptance', 'blocked_by', 'verification',
    'closure_evidence', 'closed_at', 'status_history',
  ]),
}

const FIXTURE_REQUIRED_FIELDS: Record<string, string[]> = {
  workarea: ['id', 'type', 'title', 'status', 'created', 'updated', 'description', 'source'],
  taskplan: ['id', 'type', 'title', 'status', 'created', 'updated', 'workarea', 'description', 'success_criteria', 'source', 'tasks'],
  task: ['id', 'type', 'title', 'status', 'created', 'updated', 'taskplan', 'description', 'source', 'acceptance'],
  subtask: ['id', 'type', 'title', 'status', 'created', 'updated', 'task', 'description', 'source', 'acceptance'],
}

const PLAN_CLOSE_REVIEW_STATUSES = new Set(['review_needed', 'closed'])
const STARTED_TASK_STATUSES = new Set(['executing', 'verifying', 'review_needed', 'closed'])
const OBJECT_CLOSURE_EVIDENCE_STATUSES = new Set(['review_needed', 'closed'])
const PATH_REFERENCE_FIELDS = ['related_docs', 'affected_docs', 'deliverables'] as const
const AFFECTED_DOC_PREFIXES = ['docs/', 'web/docs/', 'specs/'] as const
const OBJECT_REFERENCE_FIELDS: Record<string, string> = {
  related_adrs: 'adr',
  related_memos: 'memo',
  related_pitfalls: 'pitfall',
}

function listYamlFiles(dir: string): string[] {
  return fs.existsSync(dir)
    ? fs.readdirSync(dir)
      .filter((file) => file.endsWith('.yaml') || file.endsWith('.yml'))
      .map((file) => path.join(dir, file))
    : []
}

interface FixtureRecord {
  file: string
  relativeFile: string
  obj: Record<string, unknown>
}

function isBlank(value: unknown): boolean {
  if (value === undefined || value === null) return true
  if (typeof value === 'string') return value.trim().length === 0
  if (Array.isArray(value)) return value.length === 0
  return false
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : []
}

function isAffectedDocReference(reference: string): boolean {
  const normalized = reference.replace(/\\/g, '/')
  return /\.(md|mdx)$/i.test(normalized)
    && AFFECTED_DOC_PREFIXES.some((prefix) => normalized.startsWith(prefix))
}

function resolveFixturePath(reference: string): string {
  if (path.isAbsolute(reference)) return reference
  if (reference.startsWith('docs/')) return path.join(fixtureRoot, reference)
  return path.join(projectRoot, reference)
}

function loadFixtureRecords(): FixtureRecord[] {
  const files = ['workareas', 'taskplans', 'tasks', 'subtasks', 'adrs', 'memos', 'pitfalls']
    .flatMap((dir) => listYamlFiles(path.join(fixtureRoot, 'ldvh-base', dir)))

  return files.flatMap((file) => {
    const obj = yaml.load(fs.readFileSync(file, 'utf8')) as Record<string, unknown> | null
    if (!obj || typeof obj !== 'object') return []
    return [{ file, relativeFile: path.relative(fixtureRoot, file), obj }]
  })
}

function assertFixtureConformsToSpecs() {
  const records = loadFixtureRecords()
  const byId = new Map<string, FixtureRecord>()
  for (const record of records) {
    const id = typeof record.obj.id === 'string' ? record.obj.id : ''
    if (id) byId.set(id, record)
  }

  const mainRecords = records.filter((record) => ['workarea', 'taskplan', 'task', 'subtask'].includes(String(record.obj.type ?? '')))
  const tasks = mainRecords.filter((record) => record.obj.type === 'task')
  const subtasks = mainRecords.filter((record) => record.obj.type === 'subtask')
  const subtasksByTask = new Map<string, FixtureRecord[]>()
  for (const subtask of subtasks) {
    const taskId = String(subtask.obj.task ?? '')
    const list = subtasksByTask.get(taskId) ?? []
    list.push(subtask)
    subtasksByTask.set(taskId, list)
  }

  const issues: string[] = []
  for (const { relativeFile, obj } of mainRecords) {
    const type = String(obj.type ?? '')
    const allowed = FIXTURE_ALLOWED_FIELDS[type]
    const required = FIXTURE_REQUIRED_FIELDS[type] ?? []
    const id = String(obj.id ?? type)

    const extra = allowed ? Object.keys(obj).filter((field) => !allowed.has(field)) : []
    if (extra.length > 0) {
      issues.push(`${relativeFile} (${id}): undefined fields ${extra.join(', ')}`)
    }

    const missing = required.filter((field) => isBlank(obj[field]))
    if (missing.length > 0) {
      issues.push(`${relativeFile} (${id}): missing required fields ${missing.join(', ')}`)
    }
    if (typeof obj.source === 'string' && /^\s*(来源|用途)[:：]/m.test(obj.source)) {
      issues.push(`${relativeFile} (${id}): source field must not repeat source/purpose labels`)
    }

    if (type === 'workarea') {
      if (obj.status === 'archived' && isBlank(obj.archive_reason)) {
        issues.push(`${relativeFile} (${id}): archived WorkArea requires archive_reason`)
      }
      if (obj.status !== 'archived' && !isBlank(obj.archive_reason)) {
        issues.push(`${relativeFile} (${id}): archive_reason is only valid when status is archived`)
      }
    }

    if (type === 'taskplan') {
      const workarea = byId.get(String(obj.workarea ?? ''))
      if (!workarea || workarea.obj.type !== 'workarea') {
        issues.push(`${relativeFile} (${id}): workarea reference does not exist`)
      }

      const taskIds = stringArray(obj.tasks)
      if (taskIds.length === 0) {
        issues.push(`${relativeFile} (${id}): tasks must be a non-empty list`)
      }
      for (const taskId of taskIds) {
        const task = byId.get(taskId)
        if (!task || task.obj.type !== 'task') {
          issues.push(`${relativeFile} (${id}): task reference ${taskId} does not exist`)
          continue
        }
        if (task.obj.taskplan !== id) {
          issues.push(`${relativeFile} (${id}): task ${taskId} must point back to this TaskPlan`)
        }
        if (PLAN_CLOSE_REVIEW_STATUSES.has(String(obj.status)) && task.obj.status !== 'closed') {
          issues.push(`${relativeFile} (${id}): ${String(obj.status)} TaskPlan cannot contain non-closed task ${taskId}`)
        }
      }

      if (PLAN_CLOSE_REVIEW_STATUSES.has(String(obj.status))) {
        const closeFields = ['review_requested_at', 'completion_evidence']
        const missingCloseFields = closeFields.filter((field) => isBlank(obj[field]))
        if (missingCloseFields.length > 0) {
          issues.push(`${relativeFile} (${id}): ${String(obj.status)} TaskPlan requires ${missingCloseFields.join(', ')}`)
        }
      } else if (!isBlank(obj.review_requested_at) || !isBlank(obj.completion_evidence)) {
        issues.push(`${relativeFile} (${id}): active TaskPlan must not carry close-review fields`)
      }
      if (obj.status === 'closed' && isBlank(obj.closed_at)) {
        issues.push(`${relativeFile} (${id}): closed TaskPlan requires closed_at`)
      }
    }

    if (type === 'task') {
      const plan = byId.get(String(obj.taskplan ?? ''))
      if (!plan || plan.obj.type !== 'taskplan') {
        issues.push(`${relativeFile} (${id}): taskplan reference does not exist`)
      } else if (!stringArray(plan.obj.tasks).includes(id)) {
        issues.push(`${relativeFile} (${id}): parent TaskPlan must include this Task`)
      }

      for (const blockerId of stringArray(obj.blocked_by)) {
        const blocker = byId.get(blockerId)
        if (!blocker || blocker.obj.type !== 'task') {
          issues.push(`${relativeFile} (${id}): blocked_by ${blockerId} does not exist`)
          continue
        }
        if (blocker.obj.taskplan !== obj.taskplan) {
          issues.push(`${relativeFile} (${id}): blocked_by ${blockerId} must belong to the same TaskPlan`)
        }
        if (STARTED_TASK_STATUSES.has(String(obj.status)) && blocker.obj.status !== 'closed') {
          issues.push(`${relativeFile} (${id}): started Task cannot be blocked by non-closed task ${blockerId}`)
        }
      }

      const childSubtasks = subtasksByTask.get(id) ?? []
      if (obj.status === 'closed') {
        const missingCloseFields = ['closed_at', 'verification', 'closure_evidence'].filter((field) => isBlank(obj[field]))
        if (missingCloseFields.length > 0) {
          issues.push(`${relativeFile} (${id}): closed Task requires ${missingCloseFields.join(', ')}`)
        }
        for (const subtask of childSubtasks) {
          if (subtask.obj.status !== 'closed') {
            issues.push(`${relativeFile} (${id}): closed Task cannot contain non-closed SubTask ${String(subtask.obj.id ?? '')}`)
          }
        }
      }
      if (!OBJECT_CLOSURE_EVIDENCE_STATUSES.has(String(obj.status)) && !isBlank(obj.closure_evidence)) {
        issues.push(`${relativeFile} (${id}): closure_evidence belongs to review_needed or closed Task states`)
      }
    }

    if (type === 'subtask') {
      const task = byId.get(String(obj.task ?? ''))
      if (!task || task.obj.type !== 'task') {
        issues.push(`${relativeFile} (${id}): task reference does not exist`)
      }

      for (const blockerId of stringArray(obj.blocked_by)) {
        const blocker = byId.get(blockerId)
        if (!blocker || blocker.obj.type !== 'subtask') {
          issues.push(`${relativeFile} (${id}): blocked_by ${blockerId} does not exist`)
          continue
        }
        if (blocker.obj.task !== obj.task) {
          issues.push(`${relativeFile} (${id}): blocked_by ${blockerId} must belong to the same Task`)
        }
        if (STARTED_TASK_STATUSES.has(String(obj.status)) && blocker.obj.status !== 'closed') {
          issues.push(`${relativeFile} (${id}): started SubTask cannot be blocked by non-closed subtask ${blockerId}`)
        }
      }

      if (obj.status === 'closed') {
        const missingCloseFields = ['closed_at', 'verification', 'closure_evidence'].filter((field) => isBlank(obj[field]))
        if (missingCloseFields.length > 0) {
          issues.push(`${relativeFile} (${id}): closed SubTask requires ${missingCloseFields.join(', ')}`)
        }
      }
      if (!OBJECT_CLOSURE_EVIDENCE_STATUSES.has(String(obj.status)) && !isBlank(obj.closure_evidence)) {
        issues.push(`${relativeFile} (${id}): closure_evidence belongs to review_needed or closed SubTask states`)
      }
    }

    for (const field of PATH_REFERENCE_FIELDS) {
      const value = obj[field]
      if (value === undefined) continue
      if (!Array.isArray(value)) {
        issues.push(`${relativeFile} (${id}): ${field} must be a list`)
        continue
      }
      for (const reference of stringArray(value)) {
        if (field === 'affected_docs' && !isAffectedDocReference(reference)) {
          issues.push(`${relativeFile} (${id}): affected_docs must reference docs/, web/docs/, or specs/ Markdown documents: ${reference}`)
        }
        if (!fs.existsSync(resolveFixturePath(reference))) {
          issues.push(`${relativeFile} (${id}): ${field} reference not found: ${reference}`)
        }
      }
    }

    for (const [field, expectedType] of Object.entries(OBJECT_REFERENCE_FIELDS)) {
      const value = obj[field]
      if (value === undefined) continue
      if (!Array.isArray(value)) {
        issues.push(`${relativeFile} (${id}): ${field} must be a list`)
        continue
      }
      for (const reference of stringArray(value)) {
        const target = byId.get(reference)
        if (!target || target.obj.type !== expectedType) {
          issues.push(`${relativeFile} (${id}): ${field} reference not found: ${reference}`)
        }
      }
    }
  }

  assert.deepEqual(issues, [], `Fixture data must match work model specs:\n${issues.join('\n')}`)
}

async function main() {
  assertFixtureConformsToSpecs()

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
  assert.equal(fixturePlans.data.items.length, 10)
  const fixturePlanIds = new Set((fixturePlans.data.items as Array<Record<string, unknown>>).map((item) => item.id))
  assert.deepEqual(fixturePlanIds, new Set([
    'taskplan-9001',
    'taskplan-9002',
    'taskplan-9003',
    'taskplan-9004',
    'taskplan-9005',
    'taskplan-9006',
    'taskplan-9007',
    'taskplan-9008',
    'taskplan-9009',
    'taskplan-9010',
  ]))
  const activeFixturePlans = await listObjects('taskplan', fixtureRoot, 'active')
  assert.equal(activeFixturePlans.ok, true)
  assert.equal(activeFixturePlans.data.items.length, 6)

  const fixtureTasks = await listObjects('task', fixtureRoot)
  assert.equal(fixtureTasks.ok, true)
  assert.equal(fixtureTasks.data.items.length, 33)
  const taskStatuses = new Set((fixtureTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(taskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))

  const fixtureSubTasks = await listObjects('subtask', fixtureRoot)
  assert.equal(fixtureSubTasks.ok, true)
  assert.equal(fixtureSubTasks.data.items.length, 22)
  const subtaskStatuses = new Set((fixtureSubTasks.data.items as Array<Record<string, unknown>>).map((item) => item.status))
  assert.deepEqual(subtaskStatuses, new Set(['planned', 'executing', 'verifying', 'review_needed', 'closed']))

  const planSummaries = await buildPlanSummaries(fixturePlans.data.items as ListedObject[], fixtureRoot)
  assert.equal(planSummaries.length, 10)
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
  const closeReadyPlan = planSummaries.find((plan) => plan.id === 'taskplan-9007')
  assert.equal(closeReadyPlan?.tasks.length, 2)
  assert.deepEqual(new Set(closeReadyPlan?.tasks.map((task) => task.status)), new Set(['closed']))
  const missingEvidencePlan = planSummaries.find((plan) => plan.id === 'taskplan-9008')
  assert.equal(missingEvidencePlan?.tasks.length, 2)
  assert.deepEqual(new Set(missingEvidencePlan?.tasks.map((task) => task.status)), new Set(['closed']))
  const partialEvidencePlan = planSummaries.find((plan) => plan.id === 'taskplan-9009')
  assert.equal(partialEvidencePlan?.tasks.length, 2)
  assert.deepEqual(new Set(partialEvidencePlan?.tasks.map((task) => task.status)), new Set(['closed', 'verifying']))
  const closedCompletePlan = planSummaries.find((plan) => plan.id === 'taskplan-9010')
  assert.equal(closedCompletePlan?.tasks.length, 2)
  assert.deepEqual(new Set(closedCompletePlan?.tasks.map((task) => task.status)), new Set(['closed']))
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
