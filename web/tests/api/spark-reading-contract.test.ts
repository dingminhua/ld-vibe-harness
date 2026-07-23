import assert from 'node:assert/strict';
import { test } from 'node:test';
import fs from 'node:fs';
import path from 'node:path';

test('Spark association UI reads only relations', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactAssociationsSection.tsx'), 'utf8');
  assert.match(source, /projectFactReadingAssociations/);
  assert.doesNotMatch(source, /projectMaterials|evidenceMaterials|externalInputs/);
});

test('Spark terminal headings distinguish routed, implemented, and discarded', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactReadingLayouts.tsx'), 'utf8');

  assert.match(source, /obj\.status === 'implemented'.*'落实'/);
  assert.match(source, /obj\.status === 'discarded'.*'废弃'/);
  assert.match(source, /zh: '分流', en: 'Routing'/);
});
