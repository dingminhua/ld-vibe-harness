import assert from 'node:assert/strict';
import { test } from 'node:test';
import { projectV4Spark } from '../../api/services/v4SparkProjector.ts';

test('Spark projector does not require legacy reference fields', () => {
  const result = projectV4Spark({
    check_status: 'mechanically_valid',
    object_ref: { governed_project_id: 'p', fact_type_key: 'spark', object_id: 'spark-0001' },
    canonical_path: 'ldvh-base/sparks/spark-0001.yaml', absolute_path: '/tmp/spark-0001.yaml', carrier: 'yaml', content_fingerprint: 'x', issues: [],
    fact_object: { object_id: 'spark-0001', fact_type_key: 'spark', title: 'Spark', summary: 'Question', status: 'open', priority: 'P2', created_at: '2026-01-01T00:00:00+00:00', updated_at: '2026-01-01T00:00:00+00:00' },
  });
  assert.equal(result.ok, true);
});
