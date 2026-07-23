import assert from 'node:assert/strict';
import { test } from 'node:test';
import { groupRelationsByTargetType, projectFactReadingAssociations } from '../../src/pages/object-detail/factReadingProjection.ts';

test('projects only relation_key and stable target', () => {
  const projected = projectFactReadingAssociations({
    relations: [{ relation_key: 'related-to', target: { governed_project_id: 'sample', fact_type_key: 'spark', object_id: 'spark-0002' } }],
  });
  assert.deepEqual(projected.relations, [{
    originPath: 'relations[0]', relationKey: 'related-to',
    target: { governedProjectId: 'sample', factTypeKey: 'spark', objectId: 'spark-0002' },
  }]);
  assert.deepEqual(projected.unresolved, []);
});

test('legacy reference fields are not projected', () => {
  const projected = projectFactReadingAssociations({ source_refs: [{ kind: 'web-page', locator: 'https://example.com' }], evidence_refs: [] });
  assert.deepEqual(projected.relations, []);
  assert.deepEqual(projected.unresolved, []);
});

test('malformed relations stay visible as unresolved', () => {
  const projected = projectFactReadingAssociations({ relations: [{ relation_key: 'related-to', target: { object_id: 'spark-0002' } }] });
  assert.deepEqual(projected.unresolved.map((item) => item.originPath), ['relations[0]']);
});

test('groups ordinary relations by target type rather than their relation key', () => {
  const relations = projectFactReadingAssociations({
    relations: [
      { relation_key: 'related-to', target: { governed_project_id: 'sample', fact_type_key: 'spark', object_id: 'spark-0002' } },
      { relation_key: 'depends-on', target: { governed_project_id: 'sample', fact_type_key: 'study', object_id: 'study-0001' } },
      { relation_key: 'related-to', target: { governed_project_id: 'sample', fact_type_key: 'spark', object_id: 'spark-0003' } },
    ],
  }).relations;
  assert.deepEqual(groupRelationsByTargetType(relations).map((group) => [group.factTypeKey, group.relations.map((relation) => relation.target.objectId)]), [
    ['spark', ['spark-0002', 'spark-0003']],
    ['study', ['study-0001']],
  ]);
});
