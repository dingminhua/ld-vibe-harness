import assert from 'node:assert/strict';
import { test } from 'node:test';

import { ApiRequestError, fetchObjects } from '../../src/utils/api.ts';

test('WorkCase list transport failure preserves the safe machine reason and code', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    ok: false,
    error: 'V4 facts machine boundary is unavailable',
    stderr: 'private diagnostic must not become the message',
    exitCode: 'v4_facts_unavailable',
  }), {
    status: 503,
    headers: { 'content-type': 'application/json' },
  });
  try {
    await assert.rejects(fetchObjects('workcase'), (error: unknown) => {
      assert.ok(error instanceof ApiRequestError);
      assert.equal(error.status, 503);
      assert.equal(error.code, 'v4_facts_unavailable');
      assert.equal(error.message, 'V4 facts machine boundary is unavailable');
      assert.doesNotMatch(error.message, /private diagnostic/);
      return true;
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
