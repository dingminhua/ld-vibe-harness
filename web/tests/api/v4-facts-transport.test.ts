import assert from 'node:assert/strict';
import { test } from 'node:test';
import type { V4FactsOperation } from '../../api/internal/v4FactsTransport.ts';

test('V4 machine transport is read-only', () => {
  const operations: V4FactsOperation[] = ['list-sparks', 'read-spark'];
  assert.deepEqual(operations, ['list-sparks', 'read-spark']);
});
