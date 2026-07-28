import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const testDir = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(testDir, '../..');

test('breaking commits use one icon-and-label badge in list and detail identities', async () => {
  const [badge, list, panel, locales] = await Promise.all([
    readFile(path.join(webRoot, 'src/components/CommitBreakingBadge.tsx'), 'utf8'),
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
});
