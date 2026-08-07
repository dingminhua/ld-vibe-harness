import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('discarded Pitfall cards use the terminal disposition presentation', () => {
  const source = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');

  assert.match(source, /function PitfallTerminalCardContent/);
  assert.match(source, /obj\.status === 'discarded'/);
  assert.doesNotMatch(source, /obj\.status === 'retired' \|\| obj\.status === 'discarded'/);
  assert.match(source, /obj\.disposition_summary\?\.trim\(\) \|\| t\('objectList\.dispositionMissing'\)/);
  assert.match(source, /currentType === 'pitfall'[\s\S]*showNonActiveReason=\{false\}[\s\S]*PitfallCardContent/);
});

test('active Pitfall cards retain only the shared identity and title frame', () => {
  const source = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');

  assert.match(source, /function PitfallCardContent[\s\S]*?obj\.status === 'active'\) return null/);
});
