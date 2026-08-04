import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const testDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(testDir, '../..');

test('breaking and push-state badges use one presentation in list and detail identities', async () => {
  const [badge, pushBadge, signatureMeta, list, panel, locales] = await Promise.all([
    readFile(path.join(webRoot, 'src/components/CommitBreakingBadge.tsx'), 'utf8'),
    readFile(path.join(webRoot, 'src/components/CommitPushStatusBadge.tsx'), 'utf8'),
    readFile(path.join(webRoot, 'src/components/CommitSignatureMeta.tsx'), 'utf8'),
    readFile(path.join(webRoot, 'src/pages/Changelog.tsx'), 'utf8'),
    readFile(path.join(webRoot, 'src/components/reading-panel/PanelContent.tsx'), 'utf8'),
    readFile(path.join(webRoot, 'src/i18n/locales.ts'), 'utf8'),
  ]);

  assert.match(badge, /<Unplug size=\{10\}/);
  assert.match(badge, /text-\[10px\]/);
  assert.doesNotMatch(badge, /className="ml-1\.5/);
  assert.match(badge, /t\('changelog\.breakingChange'\)/);
  assert.match(list, /entry\.isBreaking && \(\s*<CommitBreakingBadge className="ml-1\.5" \/>/);
  assert.match(panel, /entry\?\.isBreaking && \(\s*<CommitBreakingBadge \/>/);
  assert.doesNotMatch(list, /entry\.isBreaking[\s\S]{0,200}>\s*!\s*</);
  assert.doesNotMatch(panel, /entry\?\.isBreaking[\s\S]{0,200}>\s*!\s*</);
  assert.match(locales, /'changelog\.breakingChange': '不兼容变更'/);
  assert.match(locales, /'changelog\.breakingChange': 'Breaking change'/);
  assert.match(pushBadge, /status === 'unknown'\) return null/);
  assert.match(pushBadge, /t\(isPushed \? 'changelog\.pushed' : 'changelog\.unpushed'\)/);
  assert.match(list, /<CommitPushStatusBadge status=\{entry\.pushStatus\} \/>/);
  assert.match(panel, /actionBadges=\{entry\?\.pushStatus \? <CommitPushStatusBadge status=\{entry\.pushStatus\} \/> : undefined\}/);
  assert.match(signatureMeta, /signature\?\.agentId/);
  assert.match(signatureMeta, /signature\?\.hostEnvironment/);
  assert.match(list, /<ObjectUpdatedMeta source=\{\{\}\} updatedAt=\{entry\.date\} signature=\{entry\.signature\} \/>/);
  assert.match(panel, /<CommitSignatureMeta signature=\{entry\.signature\} \/>/);
  assert.match(panel, /stripCommitSignatureTrailers\(commitBody\)/);
  assert.match(panel, /<CommitSignatureSection signature=\{entry\.signature\} labels=\{labels\} \/>/);
  assert.match(locales, /'changelog\.pushed': '已推送'/);
  assert.match(locales, /'changelog\.unpushed': 'Not pushed'/);
});
