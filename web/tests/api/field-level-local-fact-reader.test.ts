import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { listLocalFacts, readLocalFact, type LocalFactScope } from '../../api/services/localFactReader.ts';

const base = [
  'fact_type_key: adr',
  'status: proposed',
  'created_at: "2026-01-01"',
  'updated_at: "2026-01-02"',
].join('\n');

test('field-level reader keeps recoverable field defects separate from unreadable carriers', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-field-reader-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  const directory = path.join(root, 'ldvh-base', 'adrs');
  await mkdir(directory, { recursive: true });
  try {
    await writeFile(path.join(directory, 'adr-0001.yaml'), `object_id: adr-0001\n${base}\n`, 'utf8');
    await writeFile(path.join(directory, 'adr-0002.yaml'), `object_id: adr-0002\ntitle: [not, text]\n${base}\n`, 'utf8');
    await writeFile(path.join(directory, 'adr-0003.yaml'), `object_id: adr-0003\ntitle: Legacy\nlegacy_owner: old\n${base}\n`, 'utf8');
    await writeFile(path.join(directory, 'adr-0004.yaml'), `object_id: adr-0004\ntitle: Nested\nunknown_tree:\n  before: after\n${base}\n`, 'utf8');
    await writeFile(path.join(directory, 'adr-0005.yaml'), 'object_id: [unterminated\n', 'utf8');

    const listed = await listLocalFacts('adr', scope);
    assert.equal(listed.status, 'complete');
    assert.equal(listed.items.length, 5);
    const byId = new Map(listed.items.map((item) => [item.object_ref.object_id, item]));
    assert.deepEqual(byId.get('adr-0001')?.field_issues.map((issue) => issue.path), ['title']);
    assert.equal(byId.get('adr-0002')?.fact_object?.title, undefined);
    assert.deepEqual(byId.get('adr-0002')?.field_issues.map((issue) => issue.reason), ['type_mismatch']);
    assert.deepEqual(byId.get('adr-0003')?.unparsed_structures, [{ path: 'legacy_owner', reason: 'unconsumed_field', raw_value: 'old' }]);
    assert.deepEqual(byId.get('adr-0004')?.unparsed_structures, [{ path: 'unknown_tree', reason: 'unconsumed_field', raw_value: { before: 'after' } }]);
    assert.equal(byId.get('adr-0005')?.read_status, 'unreadable');
    assert.equal(byId.get('adr-0005')?.issues[0]?.code, 'yaml_parse_failed');

    const detail = await readLocalFact('adr', 'adr-0003', scope);
    assert.equal(detail.status, 'ok');
    if (detail.status === 'ok') assert.equal(detail.item.read_status, 'readable');
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('unclosed Markdown frontmatter is the only Study field-path failure that becomes unreadable', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-field-reader-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  const directory = path.join(root, 'ldvh-base', 'studies');
  await mkdir(directory, { recursive: true });
  try {
    await writeFile(path.join(directory, 'study-0001.md'), '---\nobject_id: study-0001\n', 'utf8');
    const detail = await readLocalFact('study', 'study-0001', scope);
    assert.equal(detail.status, 'ok');
    if (detail.status === 'ok') {
      assert.equal(detail.item.read_status, 'unreadable');
      assert.equal(detail.item.issues[0]?.code, 'frontmatter_unclosed');
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('WorkCase object fields and malformed consumed array members remain visible separately', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-field-reader-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  const directory = path.join(root, 'ldvh-base', 'workcases');
  await mkdir(directory, { recursive: true });
  try {
    await writeFile(path.join(directory, 'workcase-0001.yaml'), [
      'object_id: workcase-0001', 'fact_type_key: workcase', 'title: Object fields',
      'status: open', 'created_at: "2026-01-01"', 'updated_at: "2026-01-02"',
      'execution_approval:', '  subject_version: 1', 'closure_proposal:', '  proposed_outcome: partial',
      'work_items:', '  - item_id: item-valid', '    goal: Keep this item', '  - malformed member',
    ].join('\n'), 'utf8');

    const detail = await readLocalFact('workcase', 'workcase-0001', scope);
    assert.equal(detail.status, 'ok');
    if (detail.status === 'ok') {
      assert.equal(detail.item.fact_object?.execution_approval && typeof detail.item.fact_object.execution_approval, 'object');
      assert.equal(detail.item.fact_object?.closure_proposal && typeof detail.item.fact_object.closure_proposal, 'object');
      assert.deepEqual(detail.item.unparsed_structures, [{
        path: 'work_items[1]', reason: 'unparseable_member', raw_value: 'malformed member',
      }]);
    }
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('Spark evolution members without a timestamp and forbidden Pitfall tags remain unparsed', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-field-reader-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  const sparkDir = path.join(root, 'ldvh-base', 'sparks');
  const pitfallDir = path.join(root, 'ldvh-base', 'pitfalls');
  await mkdir(sparkDir, { recursive: true });
  await mkdir(pitfallDir, { recursive: true });
  try {
    await writeFile(path.join(sparkDir, 'spark-0001.yaml'), [
      'object_id: spark-0001', 'fact_type_key: spark', 'title: Missing event time',
      'status: open', 'summary: Current observation', 'created_at: "2026-01-01"', 'updated_at: "2026-01-02"',
      'evolution:', '  - summary: This entry has no source time',
    ].join('\n'), 'utf8');
    await writeFile(path.join(pitfallDir, 'pitfall-0001.yaml'), [
      'object_id: pitfall-0001', 'fact_type_key: pitfall', 'title: Forbidden tag',
      'status: active', 'created_at: "2026-01-01"', 'updated_at: "2026-01-02"', 'tags: [legacy]',
    ].join('\n'), 'utf8');

    const spark = await readLocalFact('spark', 'spark-0001', scope);
    const pitfall = await readLocalFact('pitfall', 'pitfall-0001', scope);
    assert.equal(spark.status, 'ok');
    assert.equal(pitfall.status, 'ok');
    if (spark.status === 'ok') assert.deepEqual(spark.item.unparsed_structures, [{
      path: 'evolution[0]', reason: 'unparseable_member', raw_value: { summary: 'This entry has no source time' },
    }]);
    if (pitfall.status === 'ok') assert.deepEqual(pitfall.item.unparsed_structures, [{
      path: 'tags', reason: 'unconsumed_field', raw_value: ['legacy'],
    }]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
