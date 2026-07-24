import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getFactReadMeta, isReadableFact } from '../../src/utils/factReadMeta.ts';

test('source metadata is consumable only from a readable exact result', () => {
  const meta = getFactReadMeta({
    canonical_path: 'ldvh-base/studies/study-0010.md',
    carrier: 'markdown',
    check_status: 'readable',
  });

  assert.equal(isReadableFact(meta), true);
  assert.equal(meta.canonicalPath, 'ldvh-base/studies/study-0010.md');
  assert.equal(meta.carrier, 'markdown');
});

test('a route target, ID, or expected path alone never becomes a source path', () => {
  const fromNavigation = getFactReadMeta({
    target: 'study-0010',
    object_id: 'study-0010',
    carrier: 'markdown',
    check_status: 'readable',
  });
  assert.equal(isReadableFact(fromNavigation), false);
  assert.equal(fromNavigation.canonicalPath, undefined);

  const failure = getFactReadMeta({
    fact_read_failure: true,
    canonical_path: 'ldvh-base/studies/study-0010.md',
    carrier: 'markdown',
    check_status: 'invalid',
    read_issues: [{ code: 'object_id_mismatch', message: 'identity does not match' }],
  });
  assert.equal(isReadableFact(failure), false);
  assert.equal(failure.canonicalPath, 'ldvh-base/studies/study-0010.md');
  assert.equal(failure.issues[0]?.code, 'object_id_mismatch');
});
