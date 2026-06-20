import assert from 'node:assert/strict'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'
import { buildPlanSummaries, type ListedObject } from '../../../web/api/routes/objects.ts'
import { isObjectRef, isPreviewablePathForField } from '../../../web/src/utils/fieldFormats.ts'
import { getObjectPriority, getObjectSignals } from '../../../web/src/utils/objectSignals.ts'
import { getFallbackStatuses } from '../../../web/src/components/ObjectStatusFilter.tsx'
import { formatDateTime } from '../../../web/src/utils/dateFormat.ts'

async function main() {
  const workareas = await listObjects('workarea')
  assert.equal(workareas.ok, true)
  assert.ok(Array.isArray(workareas.data.items))
  assert.ok(workareas.data.items.length > 0)

  const workplans = await listObjects('workplan')
  assert.equal(workplans.ok, true)
  assert.ok(Array.isArray(workplans.data.items))
  assert.ok(workplans.data.items.length > 0)

  const firstWorkplan = workplans.data.items[0] as Record<string, unknown>
  assert.equal(firstWorkplan.type, 'workplan')
  assert.equal(typeof firstWorkplan.id, 'string')
  assert.deepEqual(getObjectSignals(firstWorkplan, 'workplan').map((signal) => signal.field), ['priority'])
  assert.equal(getObjectPriority(firstWorkplan, 'workplan'), firstWorkplan.priority)

  const pitfalls = await listObjects('pitfall')
  assert.equal(pitfalls.ok, true)
  assert.ok(Array.isArray(pitfalls.data.items))
  const firstPitfall = pitfalls.data.items[0] as Record<string, unknown>
  assert.equal(firstPitfall.type, 'pitfall')
  assert.equal('repeatability' in firstPitfall, false)
  assert.deepEqual(getObjectSignals(firstPitfall, 'pitfall'), [])
  const archivedPitfalls = await listObjects('pitfall', undefined, 'archived')
  assert.equal(archivedPitfalls.ok, true)
  const archivedPitfall = (archivedPitfalls.data.items as Array<Record<string, unknown>>)[0]
  assert.equal(typeof archivedPitfall.archive_reason, 'string')
  assert.ok(String(archivedPitfall.archive_reason).trim().length > 0)

  const detail = await showObject(String(firstWorkplan.id))
  assert.equal(detail.ok, true)
  assert.equal(detail.data.id, firstWorkplan.id)
  assert.equal(detail.summary.id, firstWorkplan.id)
  assert.equal(detail.summary.type, 'workplan')

  const summaries = await buildPlanSummaries(workplans.data.items as ListedObject[])
  assert.equal(summaries.length, workplans.data.items.length)
  const summary = summaries.find((item) => item.id === firstWorkplan.id)
  assert.ok(summary)
  assert.equal(summary.type, 'workplan')
  assert.equal(typeof summary.executionItemTotal, 'number')
  assert.equal(typeof summary.executionItemDone, 'number')
  assert.equal(typeof summary.executionItemBlocked, 'number')
  assert.equal(typeof summary.executionItemOpen, 'number')
  assert.equal(typeof summary.successCriteriaTotal, 'number')
  assert.equal(typeof summary.successCriteriaDone, 'number')
  assert.ok(summary.successCriteriaDone <= summary.successCriteriaTotal)

  assert.equal(isObjectRef('workplan-0001'), true)
  assert.equal(isObjectRef('taskplan-0001'), false)
  assert.equal(isObjectRef('task-0001'), false)
  assert.equal(isObjectRef('subtask-0001'), false)
  assert.equal(isPreviewablePathForField('related_docs', 'specs/21-WorkPlan-工作计划.md'), true)
  assert.equal(isPreviewablePathForField('related_rules', 'web/src/pages/ObjectDetail.tsx'), true)
  assert.equal(isPreviewablePathForField('urls', 'https://developers.openai.com/codex/subagents'), true)

  const missing = await showObject('taskplan-9999')
  assert.equal(missing.ok, false)

  assert.deepEqual(getFallbackStatuses('study', 'active'), ['active', 'archived'])
  assert.equal(getFallbackStatuses('study', 'active').includes('draft'), false)
  assert.equal(getFallbackStatuses('workplan', 'draft').includes('draft'), true)

  const studies = await listObjects('study')
  assert.equal(studies.ok, true)
  assert.ok(Array.isArray(studies.data.items))
  const firstStudy = studies.data.items[0] as Record<string, unknown>
  assert.equal(typeof firstStudy.updated, 'string')
  assert.match(String(firstStudy.updated), /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/)
  assert.match(formatDateTime(String(firstStudy.updated)), /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/)
  assert.equal(formatDateTime('2026-06-18T17:10:00+08:00'), '2026-06-18 17:10')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
