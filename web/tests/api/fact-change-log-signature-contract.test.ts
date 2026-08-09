import assert from 'node:assert/strict';
import { test } from 'node:test';
import { getLatestFactChangeSignature } from '../../src/utils/factChangeLog';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const repositoryRoot = path.resolve(import.meta.dirname, '../../..');

test('object header attribution reads the newest complete signature from change_log only', () => {
  assert.deepEqual(getLatestFactChangeSignature([
    { signature: { agent_id: 'older', host_environment: 'old-host' } },
    { signature: { agent_id: 'partial' } },
    { signature: { agent_id: 'codex', host_environment: 'Cindy' } },
  ]), { agentId: 'codex', hostEnvironment: 'Cindy' });

  assert.deepEqual(getLatestFactChangeSignature([
    { signature: { agent_id: 'legacy', host_environment: 'old-host' } },
    { signature: { model_id: 'gpt-5', agent_workbench: 'Cindy' } },
  ]), { modelId: 'gpt-5', hostName: 'Cindy' });

  assert.deepEqual(getLatestFactChangeSignature([
    { signature: { model_id: 'gpt-5', host_name: 'Cindy' } },
  ]), { modelId: 'gpt-5', hostName: 'Cindy' });

  assert.equal(getLatestFactChangeSignature([
    { signature: { agent_id: 'partial' } },
    { signature: { host_environment: 'missing-agent' } },
  ]), undefined);
  assert.equal(getLatestFactChangeSignature(undefined), undefined);
});

test('all fact Cards reuse the shared update and update-log attribution surface', () => {
  const list = readFileSync(path.join(repositoryRoot, 'web/src/pages/ObjectList.tsx'), 'utf8');
  const facts = readFileSync(path.join(repositoryRoot, 'web/api/services/facts.ts'), 'utf8');

  assert.match(list, /import ObjectUpdatedMeta from '@\/components\/ObjectUpdatedMeta'/);
  assert.match(list, /<ObjectUpdatedMeta source=\{obj\} updatedAt=\{obj\.updated\} \/>/);
  assert.match(list, /flex min-w-0 items-center justify-end pt-0\.5 text-right/);
  assert.doesNotMatch(list, /formatDateTime\(obj\.updated\)/);
  assert.match(facts, /copyPresentFields\(source, \['change_log'\]\)/);
});
