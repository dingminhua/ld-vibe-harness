import assert from 'node:assert/strict'
import { test } from 'node:test'

import { projectV4Spark, projectV4SparkList } from '../../api/services/v4SparkProjector.ts'

function hasOwn(value: Record<string, unknown>, field: string): boolean {
  return Object.prototype.hasOwnProperty.call(value, field)
}

function item(overrides: Record<string, unknown> = {}) {
  const factObject: Record<string, unknown> = {
    fact_type_key: 'spark',
    object_id: 'spark-0001',
    title: 'Projection',
    summary: 'Preserve V4 truth while adapting the existing DTO.',
    status: 'open',
    priority: 'P2',
    created_at: '2026-07-15T16:00:00+08:00',
    updated_at: '2026-07-15T16:00:00+08:00',
    source_refs: [{ kind: 'repository-path', locator: 'docs/input.md' }],
    evidence_refs: [{ kind: 'repository-path', locator: 'docs/evidence.md' }],
    relations: [],
    evolution: [{ changed_at: '2026-07-15T16:00:00+08:00' }],
    ...overrides,
  }
  if (factObject.status === 'routed' || factObject.status === 'discarded') delete factObject.priority
  return {
    object_ref: {
      governed_project_id: 'sample',
      fact_type_key: 'spark',
      object_id: 'spark-0001',
    },
    absolute_path: '/workspace/project/ldvh-base/sparks/spark-0001.yaml',
    check_status: 'mechanically_valid',
    fact_object: factObject,
  }
}

function minimalItem(overrides: Record<string, unknown> = {}) {
  const factObject: Record<string, unknown> = {
    fact_type_key: 'spark',
    object_id: 'spark-0001',
    title: 'Minimal',
    summary: 'Only V4 fields that actually exist may be projected.',
    status: 'open',
    priority: 'P2',
    created_at: '2026-07-15T16:00:00+08:00',
    updated_at: '2026-07-15T16:00:00+08:00',
    source_refs: [{ kind: 'web-direct-capture', locator: 'data:application/json;base64,e30=' }],
    ...overrides,
  }
  if (factObject.status === 'routed' || factObject.status === 'discarded') delete factObject.priority
  return {
    object_ref: {
      governed_project_id: 'sample',
      fact_type_key: 'spark',
      object_id: 'spark-0001',
    },
    absolute_path: '/workspace/project/ldvh-base/sparks/spark-0001.yaml',
    check_status: 'mechanically_valid',
    fact_object: factObject,
  }
}

test('minimal open Spark does not invent absent optional arrays', () => {
  const projected = projectV4Spark(minimalItem())

  assert.equal(projected.ok, true)
  if (!projected.ok) return
  for (const field of ['evidence_refs', 'relations', 'evolution']) {
    assert.equal(hasOwn(projected.data, field), false)
  }
  assert.deepEqual(projected.data.source_refs, [
    { kind: 'web-direct-capture', locator: 'data:application/json;base64,e30=' },
  ])
})

test('open Spark preserves V4 fields and adds only transport metadata', () => {
  const projected = projectV4Spark(item())

  assert.equal(projected.ok, true)
  if (!projected.ok) return
  assert.equal(projected.data.status, 'open')
  assert.equal(projected.data.created_at, '2026-07-15T16:00:00+08:00')
  assert.equal(projected.data.updated_at, '2026-07-15T16:00:00+08:00')
  assert.equal(projected.data.summary, 'Preserve V4 truth while adapting the existing DTO.')
  assert.equal(projected.data.absolute_path, '/workspace/project/ldvh-base/sparks/spark-0001.yaml')
  assert.deepEqual(projected.data.source_refs, [{ kind: 'repository-path', locator: 'docs/input.md' }])
  assert.deepEqual(projected.data.evidence_refs, [{ kind: 'repository-path', locator: 'docs/evidence.md' }])
  assert.equal(projected.data.fact_type_key, 'spark')
  assert.equal(projected.data.object_id, 'spark-0001')
  for (const noncanonicalField of ['id', 'type', 'description', 'resolved_to', 'resolved_at', 'related_workcases']) {
    assert.equal(hasOwn(projected.data, noncanonicalField), false)
  }
})

test('relations remain V4 relations without navigation aliases', () => {
  const relations = [
    {
      relation_key: 'related-to',
      target: { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0002' },
    },
    {
      relation_key: 'related-to',
      target: { governed_project_id: 'other', fact_type_key: 'adr', object_id: 'adr-0003' },
    },
  ]
  const projected = projectV4Spark(item({ relations }))

  assert.equal(projected.ok, true)
  if (!projected.ok) return
  assert.deepEqual(projected.data.relations, relations)
  assert.equal(hasOwn(projected.data, 'related_workcases'), false)
  assert.equal(hasOwn(projected.data, 'related_adrs'), false)
})

test('routed Spark keeps routed status and its original relation', () => {
  const relation = {
    relation_key: 'routed-to',
    target: { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0002' },
  }
  const projected = projectV4Spark(item({
    status: 'routed',
    relations: [relation],
    closed_at: '2026-07-15T17:00:00+08:00',
    disposition_summary: 'Promoted to execution.',
  }))

  assert.equal(projected.ok, true)
  if (!projected.ok) return
  assert.equal(projected.data.status, 'routed')
  assert.equal(projected.data.closed_at, '2026-07-15T17:00:00+08:00')
  assert.equal(projected.data.disposition_summary, 'Promoted to execution.')
  assert.deepEqual(projected.data.relations, [relation])
})

test('minimal routed and discarded Sparks preserve only present terminal truth', () => {
  const routedRelation = {
    relation_key: 'routed-to',
    target: { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0002' },
  }
  const routed = projectV4Spark(minimalItem({
    status: 'routed',
    relations: [routedRelation],
    closed_at: '2026-07-15T17:00:00+08:00',
    disposition_summary: 'Fully routed to the WorkCase.',
    evidence_refs: [{ kind: 'repository-path', locator: 'docs/routing-evidence.md' }],
  }))
  assert.equal(routed.ok, true)
  if (routed.ok) {
    assert.deepEqual(routed.data.evidence_refs, [
      { kind: 'repository-path', locator: 'docs/routing-evidence.md' },
    ])
    assert.equal(hasOwn(routed.data, 'evolution'), false)
    assert.deepEqual(routed.data.relations, [routedRelation])
  }

  const discarded = projectV4Spark(minimalItem({
    status: 'discarded',
    disposition_summary: 'No longer relevant.',
    closed_at: '2026-07-15T18:00:00+08:00',
    evidence_refs: [{ kind: 'repository-path', locator: 'docs/discard-evidence.md' }],
  }))
  assert.equal(discarded.ok, true)
  if (discarded.ok) {
    assert.equal(discarded.data.disposition_summary, 'No longer relevant.')
    assert.equal(hasOwn(discarded.data, 'relations'), false)
    assert.deepEqual(discarded.data.evidence_refs, [
      { kind: 'repository-path', locator: 'docs/discard-evidence.md' },
    ])
    assert.equal(hasOwn(discarded.data, 'evolution'), false)
  }
})

test('routed Spark does not collapse zero, multiple, or cross-project targets', () => {
  const same = { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0002' }
  const cross = { governed_project_id: 'other', fact_type_key: 'workcase', object_id: 'workcase-0003' }
  const cases = [
    [],
    [
      { relation_key: 'routed-to', target: same },
      { relation_key: 'routed-to', target: cross },
    ],
    [{ relation_key: 'routed-to', target: cross }],
  ]
  for (const relations of cases) {
    const projected = projectV4Spark(item({
      status: 'routed',
      relations,
      closed_at: '2026-07-15T17:00:00+08:00',
      disposition_summary: 'Fully routed by the represented targets.',
    }))
    assert.equal(projected.ok, true)
    if (!projected.ok) continue
    assert.deepEqual(projected.data.relations, relations)
  }
})

test('status-conditional Spark fields fail closed when schema semantics are contradicted', () => {
  const invalid = [
    minimalItem({ priority: undefined }),
    minimalItem({ status: 'open', closed_at: '2026-07-15T17:00:00+08:00' }),
    minimalItem({ status: 'routed', closed_at: '2026-07-15T17:00:00+08:00' }),
    minimalItem({
      status: 'discarded',
      closed_at: '2026-07-15T17:00:00+08:00',
      disposition_summary: 'Missing evidence.',
    }),
  ]
  for (const current of invalid) {
    const projected = projectV4Spark(current)
    assert.equal(projected.ok, false)
    if (!projected.ok) assert.equal(projected.code, 'spark_projection_invalid')
  }
})

test('discarded status retains disposition summary and list remains partial on projection loss', () => {
  const discarded = projectV4Spark(item({
    status: 'discarded',
    disposition_summary: 'No longer relevant.',
    closed_at: '2026-07-15T18:00:00+08:00',
  }))
  assert.equal(discarded.ok, true)
  if (discarded.ok) {
    assert.equal(discarded.data.status, 'discarded')
    assert.equal(discarded.data.disposition_summary, 'No longer relevant.')
  }

  const listed = projectV4SparkList([item(), { check_status: 'invalid' }])
  assert.equal(listed.ok, false)
  assert.equal(listed.status, 'partial')
  assert.equal(listed.items.length, 1)
  assert.equal(listed.projection_problems[0].code, 'spark_projection_invalid')
})
