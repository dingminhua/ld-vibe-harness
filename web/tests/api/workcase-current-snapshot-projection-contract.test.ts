import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { test } from 'node:test'
import { listObjects, projectCurrentWorkCaseCard, showObject } from '../../api/services/facts.ts'
import type { LocalFactScope } from '../../api/services/localFactReader.ts'
import {
  WORKCASE_CURRENT_PHASES,
  deriveWorkCasePresentationProjection,
} from '../../shared/workcaseStatus.ts'

const fingerprint = 'a'.repeat(64)

test('the shared contract covers every active phase and reserves gate2_waiting for one open snapshot', () => {
  const open = WORKCASE_CURRENT_PHASES.map((phase) => deriveWorkCasePresentationProjection('open', phase, fingerprint))
  const blocked = WORKCASE_CURRENT_PHASES.map((phase) => deriveWorkCasePresentationProjection('blocked', phase, fingerprint))
  const gate2 = [...open, ...blocked].filter(
    (projection) => projection.resolution === 'resolved' && projection.handoff_narrative_key === 'gate2_waiting',
  )

  assert.equal(gate2.length, 1)
  assert.equal(gate2[0]?.resolution, 'resolved')
  if (gate2[0]?.resolution === 'resolved') {
    assert.equal(gate2[0].lifecycle_position, 'human_closure_confirming')
    assert.equal(gate2[0].blocking_overlay, false)
  }
  for (const phase of ['independent_reviewing', 'closure_preparing'] as const) {
    const projection = deriveWorkCasePresentationProjection('open', phase, fingerprint)
    assert.equal(projection.resolution, 'resolved')
    if (projection.resolution === 'resolved') assert.notEqual(projection.handoff_narrative_key, 'gate2_waiting')
  }
  const blockedClosure = deriveWorkCasePresentationProjection('blocked', 'human_closure_confirming', fingerprint)
  assert.equal(blockedClosure.resolution, 'resolved')
  if (blockedClosure.resolution === 'resolved') {
    assert.equal(blockedClosure.progress_group, 'closure_confirmation')
    assert.equal(blockedClosure.handoff_narrative_key, 'gate2_position_blocked')
    assert.equal(blockedClosure.blocking_overlay, true)
  }
})

test('unresolved projections do not guess progress, handoff, or the next control step', () => {
  for (const projection of [
    deriveWorkCasePresentationProjection('open', 'unknown', fingerprint),
    deriveWorkCasePresentationProjection('open', undefined, fingerprint),
    deriveWorkCasePresentationProjection('closed', 'executing', fingerprint),
    deriveWorkCasePresentationProjection('open', 'executing', undefined),
  ]) {
    assert.equal(projection.resolution, 'unresolved')
    assert.equal('progress_group' in projection, false)
    assert.equal('handoff_narrative_key' in projection, false)
    assert.equal('next_required_control_step' in projection, false)
  }
})

test('current Card and Cognition consumers never manufacture a source fingerprint', async () => {
  const fact = {
    object_id: 'workcase-0001',
    fact_type_key: 'workcase',
    title: 'Current projection only',
    status: 'open',
    phase: 'executing',
  }
  const missing = projectCurrentWorkCaseCard(fact, null)
  assert.deepEqual(missing.current_snapshot_projection, {
    contract_identity: 'workcase-current-snapshot-presentation/1',
    resolution: 'unresolved',
    source_content_fingerprint: null,
    unresolved_reason: 'missing_source_content_fingerprint',
  })
  assert.equal(missing.progress_group, undefined)

  const resolved = projectCurrentWorkCaseCard(fact, fingerprint)
  assert.equal((resolved.current_snapshot_projection as Record<string, unknown>).source_content_fingerprint, fingerprint)
  assert.equal(resolved.progress_group, 'progressing')
  assert.equal(resolved.progress_step, 'item_execution')

  const repositoryRoot = path.resolve(import.meta.dirname, '../../..')
  const sharedSource = await readFile(path.join(repositoryRoot, 'web/shared/workcaseStatus.ts'), 'utf8')
  const factsSource = await readFile(path.join(repositoryRoot, 'web/api/services/facts.ts'), 'utf8')
  const cognitionSource = await readFile(path.join(repositoryRoot, 'web/api/routes/cognition.ts'), 'utf8')
  assert.doesNotMatch(sharedSource, /repeat\(64\)/)
  assert.match(factsSource, /projectCurrentWorkCaseCard\(source, item\.source_content_fingerprint\)/)
  assert.doesNotMatch(cognitionSource, /deriveWorkCaseProgressProjection/)
  assert.match(cognitionSource, /currentWorkCaseProjection\(raw\)/)
})

test('Web list and detail bind projection to raw carrier bytes while preserving field issues', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-workcase-projection-'))
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' }
  const directory = path.join(root, 'ldvh-base', 'workcases')
  await mkdir(directory, { recursive: true })
  const reviewing = [
    'object_id: workcase-0001',
    'fact_type_key: workcase',
    'title: Independent review',
    'status: open',
    'phase: independent_reviewing',
    'created_at: "2026-01-01"',
    'updated_at: "2026-01-02"',
    'goal: Verify the result',
    'scope: One result',
    'success_criterion_definitions: []',
    '',
  ].join('\n')
  const invalidStatus = [
    'object_id: workcase-0002',
    'fact_type_key: workcase',
    'title: Readable with an invalid status field',
    'status: [open]',
    'phase: closure_preparing',
    'created_at: "2026-01-01"',
    'updated_at: "2026-01-02"',
    'goal: Preserve readable fields',
    'scope: One result',
    'success_criterion_definitions: []',
    '',
  ].join('\n')
  await writeFile(path.join(directory, 'workcase-0001.yaml'), reviewing, 'utf8')
  await writeFile(path.join(directory, 'workcase-0002.yaml'), invalidStatus, 'utf8')
  try {
    const detail = await showObject('workcase-0001', scope)
    if (!detail.ok) throw new Error(detail.error)
    const raw = await readFile(path.join(directory, 'workcase-0001.yaml'))
    const expectedFingerprint = createHash('sha256').update(raw).digest('hex')
    const projection = detail.data.current_snapshot_projection as Record<string, unknown>
    assert.equal(projection.source_content_fingerprint, expectedFingerprint)
    assert.equal(projection.handoff_narrative_key, 'independent_result_review_in_progress')
    assert.equal(projection.next_required_control_step, 'complete_independent_result_review')
    assert.equal(detail.data.progress_group, 'progressing')
    assert.equal(detail.data.progress_step, 'independent_review')

    const listed = await listObjects('workcase', undefined, undefined, scope)
    if (!listed.ok) throw new Error(listed.error)
    const byId = new Map(
      (listed.data.items as Array<Record<string, unknown>>).map((item) => [item.object_id, item]),
    )
    const invalid = byId.get('workcase-0002')
    assert.equal(invalid?.title, 'Readable with an invalid status field')
    assert.deepEqual(
      (invalid?.field_issues as Array<Record<string, unknown>>).map((issue) => [issue.path, issue.reason]),
      [['status', 'type_mismatch']],
    )
    assert.deepEqual(invalid?.current_snapshot_projection, {
      contract_identity: 'workcase-current-snapshot-presentation/1',
      resolution: 'unresolved',
      source_content_fingerprint: createHash('sha256').update(invalidStatus).digest('hex'),
      unresolved_reason: 'missing_status',
    })
    assert.equal(invalid?.progress_group, undefined)
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})
