import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('object list cards keep the short reference for actions without displaying it', () => {
  const source = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');

  assert.doesNotMatch(source, /obj\.short_ref \?\? obj\.id/);
  assert.match(source, /target=\{obj\.id\}/);
  assert.match(source, /shortRef=\{obj\.short_ref\}/);
  assert.match(source, /onOpen\(obj\.id\)/);
});
