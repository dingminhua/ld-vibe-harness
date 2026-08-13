import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('object list cards show short_ref while retaining the full object id for actions', () => {
  const source = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');

  assert.match(source, /<span className="ldvh-meta-muted min-w-0 truncate">\{obj\.short_ref \?\? obj\.id\}<\/span>/);
  assert.match(source, /target=\{obj\.id\}/);
  assert.match(source, /shortRef=\{obj\.short_ref\}/);
  assert.match(source, /onOpen\(obj\.id\)/);
});
