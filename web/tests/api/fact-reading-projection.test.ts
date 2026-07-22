import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  projectFactReadingAssociations,
} from '../../src/pages/object-detail/factReadingProjection.ts';

test('projects formal v4 associations without creating legacy related fields', () => {
  const obj = {
    source_refs: [
      { kind: 'human-input', locator: 'Human asked to preserve this question.' },
      { kind: 'repository-path', locator: 'docs/input.md' },
      { kind: 'web-page', locator: 'https://example.com/reference', observed_at: '2026-07-21T10:00:00+08:00' },
    ],
    evidence_refs: [
      { kind: 'repository-path', locator: 'tests/result.txt', version: 'abc123' },
    ],
    relations: [
      {
        relation_key: 'related-to',
        target: {
          governed_project_id: 'sample',
          fact_type_key: 'spark',
          object_id: 'spark-0002',
          governance_refs: [{ kind: 'repository-path', locator: 'LDVH-GOVERNED-PROJECTS.yaml' }],
        },
        source_refs: [{ kind: 'repository-path', locator: 'docs/relation.md' }],
      },
    ],
  };

  const projected = projectFactReadingAssociations(obj);
  assert.equal(projected.relations.length, 1);
  assert.equal(projected.relations[0].relationKey, 'related-to');
  assert.equal(projected.relations[0].target.objectId, 'spark-0002');
  assert.equal(projected.relations[0].sourceRefs[0].role, 'relation-source');
  assert.equal(projected.relations[0].target.governanceRefs[0].role, 'governance');
  assert.deepEqual(projected.projectMaterials.map((item) => item.locator), ['docs/input.md']);
  assert.deepEqual(projected.externalInputs.map((item) => item.locator), [
    'Human asked to preserve this question.',
    'https://example.com/reference',
  ]);
  assert.deepEqual(projected.evidenceMaterials.map((item) => item.locator), ['tests/result.txt']);
  assert.deepEqual(projected.unresolved, []);
  assert.equal(Object.prototype.hasOwnProperty.call(projected, 'related_workcases'), false);
});

test('Spark sources remain source materials and are never projected as intent', () => {
  const projected = projectFactReadingAssociations({
    summary: 'This must not be relabelled as intent.',
    source_refs: [
      { kind: 'repository-path', locator: 'docs/input.md' },
      { kind: 'human-input', locator: 'Human explicitly asked this question.' },
    ],
  });

  assert.deepEqual(projected.externalInputs.map((item) => item.locator), [
    'Human explicitly asked this question.',
  ]);
  assert.deepEqual(projected.projectMaterials.map((item) => item.locator), ['docs/input.md']);
  assert.equal(Object.prototype.hasOwnProperty.call(projected, 'intent'), false);
});

test('malformed and unknown associations remain visible as unresolved', () => {
  const projected = projectFactReadingAssociations({
    source_refs: [
      { kind: 'future-kind', locator: 'opaque:future' },
      { kind: 'repository-path' },
    ],
    evidence_refs: 'not-an-array',
    relations: [{ relation_key: 'related-to', target: { object_id: 'spark-0002' } }],
  });

  assert.equal(projected.unresolved.length, 4);
  assert.deepEqual(projected.unresolved.map((item) => item.originPath).sort(), [
    'evidence_refs',
    'relations[0]',
    'source_refs[0]',
    'source_refs[1]',
  ]);
});
