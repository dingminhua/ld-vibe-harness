import assert from 'node:assert/strict';
import { mkdtemp, mkdir, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { test } from 'node:test';
import { listObjects, showObject } from '../../api/services/facts.ts';
import type { LocalFactScope } from '../../api/services/localFactReader.ts';

const fixtures = [
  { type: 'adr', id: 'adr-0001', directory: 'adrs', carrier: 'yaml', body: 'object_id: adr-0001\nfact_type_key: adr\ntitle: ADR fixture\nstatus: proposed\n' },
  { type: 'pitfall', id: 'pitfall-0001', directory: 'pitfalls', carrier: 'yaml', body: 'object_id: pitfall-0001\nfact_type_key: pitfall\ntitle: Pitfall fixture\nstatus: active\n' },
  {
    type: 'study', id: 'study-0001', directory: 'studies', carrier: 'markdown',
    body: '---\nobject_id: study-0001\nfact_type_key: study\ntitle: Study fixture\nstatus: active\n---\n\n## 研究问题\n\nFixture body.\n',
  },
] as const;

test('local exact reads carry source metadata for each local carrier, while list candidates do not', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-web-facts-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  try {
    for (const fixture of fixtures) {
      const extension = fixture.carrier === 'markdown' ? '.md' : '.yaml';
      const dir = path.join(root, 'ldvh-base', fixture.directory);
      await mkdir(dir, { recursive: true });
      await writeFile(path.join(dir, `${fixture.id}${extension}`), fixture.body, 'utf8');
    }

    for (const fixture of fixtures) {
      const result = await showObject(fixture.id, scope);
      if (!result.ok) throw new Error(result.error);
      assert.equal(result.ok, true);
      assert.equal(result.data.canonical_path, `ldvh-base/${fixture.directory}/${fixture.id}${fixture.carrier === 'markdown' ? '.md' : '.yaml'}`);
      assert.equal(result.data.carrier, fixture.carrier);
      assert.equal(result.data.check_status, 'readable');
      assert.equal(result.data.fact_read_failure, undefined);
    }

    const listed = await listObjects('study', undefined, undefined, scope);
    if (!listed.ok) throw new Error(listed.error);
    assert.equal(listed.ok, true);
    const candidate = (listed.data.items as Array<Record<string, unknown>>)[0];
    assert.equal(candidate?.object_id, 'study-0001');
    assert.equal('canonical_path' in (candidate ?? {}), false);
    assert.equal('carrier' in (candidate ?? {}), false);
    assert.equal('check_status' in (candidate ?? {}), false);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test('unreadable exact reads expose only read metadata, not a partial fact or domain status', async () => {
  const root = await mkdtemp(path.join(tmpdir(), 'ldvh-web-facts-'));
  const scope: LocalFactScope = { worktreeLocator: root, governedProjectId: 'fixture' };
  const studyDir = path.join(root, 'ldvh-base', 'studies');
  await mkdir(studyDir, { recursive: true });
  await writeFile(
    path.join(studyDir, 'study-0002.md'),
    '---\nobject_id: study-9999\nfact_type_key: study\nstatus: active\n---\n\n## 研究问题\n\nBroken identity.\n',
    'utf8',
  );
  try {
    const invalid = await showObject('study-0002', scope);
    if (!invalid.ok) throw new Error(invalid.error);
    assert.equal(invalid.ok, true);
    assert.equal(invalid.summary.read_status, 'invalid');
    assert.equal(invalid.summary.status, undefined);
    assert.equal(invalid.data.fact_read_failure, true);
    assert.equal(invalid.data.canonical_path, 'ldvh-base/studies/study-0002.md');
    assert.equal(invalid.data.carrier, 'markdown');
    assert.equal(invalid.data.report_body, undefined);
    assert.equal(invalid.data.status, undefined);

    const missing = await showObject('study-9999', scope);
    if (!missing.ok) throw new Error(missing.error);
    assert.equal(missing.ok, true);
    assert.equal(missing.summary.read_status, 'not_found');
    assert.equal(missing.data.fact_read_failure, true);
    assert.equal(missing.data.canonical_path, 'ldvh-base/studies/study-9999.md');
    assert.equal(missing.data.report_body, undefined);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
