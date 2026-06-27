import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { listObjects, showObject } from '../../../web/api/services/facts.ts'
import { buildWorkCaseSummaries, type ListedObject } from '../../../web/api/routes/objects.ts'
import { isObjectRef, isPreviewablePathForField } from '../../../web/src/utils/fieldFormats.ts'
import { getObjectPriority, getObjectSignals } from '../../../web/src/utils/objectSignals.ts'
import { getFallbackStatuses } from '../../../web/src/components/ObjectStatusFilter.tsx'
import { formatDateTime } from '../../../web/src/utils/dateFormat.ts'
import { getDefaultListStatus } from '../../../web/src/utils/listStatus.ts'
import { WORKCASE_DEFAULT_LIST_STATUS, WORKCASE_STATUS_ORDER } from '../../../web/src/utils/workcaseStatus.ts'

function createPitfallFixtureRoot() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'ldvh-pitfall-fixture-'))
  const pitfallsDir = path.join(root, 'ldvh-base', 'pitfalls')
  fs.mkdirSync(pitfallsDir, { recursive: true })
  fs.writeFileSync(
    path.join(pitfallsDir, 'pitfall-0001-api-contract.yaml'),
    [
      'id: pitfall-0001',
      'type: pitfall',
      'title: API contract fixture',
      'status: active',
      "created: '2026-06-25T03:40:00+08:00'",
      "updated: '2026-06-25T03:40:00+08:00'",
      'resolution: Keep fixture data out of the repository fact source.',
      'source_sparks: []',
      '',
    ].join('\n'),
  )
  fs.writeFileSync(
    path.join(pitfallsDir, 'pitfall-0002-archived-contract.yaml'),
    [
      'id: pitfall-0002',
      'type: pitfall',
      'title: Archived API contract fixture',
      'status: archived',
      "created: '2026-06-25T03:41:00+08:00'",
      "updated: '2026-06-25T03:41:00+08:00'",
      'archive_reason: Covered by a stronger fixture.',
      'resolution: Keep archived filtering explicit.',
      'source_sparks: []',
      '',
    ].join('\n'),
  )

  return root
}

async function main() {
  const workcases = await listObjects('workcase')
  assert.equal(workcases.ok, true)
  assert.ok(Array.isArray(workcases.data.items))
  assert.ok(workcases.data.items.length > 0)

  const firstWorkCase = workcases.data.items[0] as Record<string, unknown>
  assert.equal(firstWorkCase.type, 'workcase')
  assert.equal(typeof firstWorkCase.id, 'string')
  assert.deepEqual(getObjectSignals(firstWorkCase, 'workcase').map((signal) => signal.field), ['priority'])
  assert.equal(getObjectPriority(firstWorkCase, 'workcase'), firstWorkCase.priority)

  const pitfalls = await listObjects('pitfall')
  assert.equal(pitfalls.ok, true)
  assert.equal(typeof pitfalls.summary.count, 'number')
  assert.ok(Array.isArray(pitfalls.data.items))
  assert.equal(pitfalls.summary.count, pitfalls.data.items.length)
  for (const pitfall of pitfalls.data.items as Array<Record<string, unknown>>) {
    assert.equal(pitfall.type, 'pitfall')
    assert.equal(typeof pitfall.id, 'string')
  }
  const archivedPitfalls = await listObjects('pitfall', undefined, 'archived')
  assert.equal(archivedPitfalls.ok, true)
  assert.equal(typeof archivedPitfalls.summary.count, 'number')
  assert.ok(Array.isArray(archivedPitfalls.data.items))
  assert.equal(archivedPitfalls.summary.count, archivedPitfalls.data.items.length)
  for (const pitfall of archivedPitfalls.data.items as Array<Record<string, unknown>>) {
    assert.equal(pitfall.status, 'archived')
  }

  const pitfallFixtureRoot = createPitfallFixtureRoot()
  try {
    const fixturePitfalls = await listObjects('pitfall', pitfallFixtureRoot)
    assert.equal(fixturePitfalls.ok, true)
    assert.equal(fixturePitfalls.summary.count, 2)
    assert.ok(Array.isArray(fixturePitfalls.data.items))
    const firstPitfall = fixturePitfalls.data.items[0] as Record<string, unknown>
    assert.equal(firstPitfall.type, 'pitfall')
    assert.equal('repeatability' in firstPitfall, false)
    assert.deepEqual(getObjectSignals(firstPitfall, 'pitfall'), [])
    const fixtureArchivedPitfalls = await listObjects('pitfall', pitfallFixtureRoot, 'archived')
    assert.equal(fixtureArchivedPitfalls.ok, true)
    assert.equal(fixtureArchivedPitfalls.summary.count, 1)
    const archivedPitfall = (fixtureArchivedPitfalls.data.items as Array<Record<string, unknown>>)[0]
    assert.equal(typeof archivedPitfall.archive_reason, 'string')
    assert.ok(String(archivedPitfall.archive_reason).trim().length > 0)
  } finally {
    fs.rmSync(pitfallFixtureRoot, { recursive: true, force: true })
  }

  const detail = await showObject(String(firstWorkCase.id))
  assert.equal(detail.ok, true)
  assert.equal(detail.data.id, firstWorkCase.id)
  assert.equal(detail.summary.id, firstWorkCase.id)
  assert.equal(detail.summary.type, 'workcase')

  const summaries = await buildWorkCaseSummaries(workcases.data.items as ListedObject[])
  assert.equal(summaries.length, workcases.data.items.length)
  const summary = summaries.find((item) => item.id === firstWorkCase.id)
  assert.ok(summary)
  assert.equal(summary.type, 'workcase')
  assert.equal(typeof summary.status, 'string')
  assert.equal(typeof summary.executionItemTotal, 'number')
  assert.equal(typeof summary.executionItemDone, 'number')
  assert.equal(typeof summary.executionItemBlocked, 'number')
  assert.equal(typeof summary.executionItemOpen, 'number')
  assert.equal(typeof summary.successCriteriaTotal, 'number')
  assert.equal(typeof summary.successCriteriaDone, 'number')
  assert.equal(typeof summary.hasPlanConfirmedAt, 'boolean')
  assert.equal(typeof summary.hasClosureRequestedAt, 'boolean')
  assert.ok(summary.successCriteriaDone <= summary.successCriteriaTotal)

  assert.equal(isObjectRef('workcase-0001'), true)
  assert.equal(isObjectRef('taskplan-0001'), false)
  assert.equal(isObjectRef('task-0001'), false)
  assert.equal(isObjectRef('subtask-0001'), false)
  assert.equal(isPreviewablePathForField('related_docs', 'specs/21-WorkCase-工作项.md'), true)
  assert.equal(isPreviewablePathForField('related_rules', 'web/src/pages/ObjectDetail.tsx'), true)
  assert.equal(isPreviewablePathForField('urls', 'https://developers.openai.com/codex/subagents'), true)

  const missing = await showObject('taskplan-9999')
  assert.equal(missing.ok, false)

  assert.deepEqual(getFallbackStatuses('study', 'active'), ['active', 'archived'])
  assert.equal(getFallbackStatuses('study', 'active').includes('draft'), false)
  assert.equal(getDefaultListStatus('workcase'), WORKCASE_DEFAULT_LIST_STATUS)
  assert.equal(WORKCASE_DEFAULT_LIST_STATUS, null)
  assert.deepEqual(WORKCASE_STATUS_ORDER.slice(0, 7), [
    'subagents_plan_reviewing',
    'human_plan_confirming',
    'executing',
    'result_self_checking',
    'subagents_result_reviewing',
    'human_closure_confirming',
    'closed',
  ])
  assert.equal(getFallbackStatuses('workcase', 'closed').includes('closed'), true)
  assert.equal(getFallbackStatuses('workcase', WORKCASE_DEFAULT_LIST_STATUS).includes('human_closure_confirming'), true)

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
