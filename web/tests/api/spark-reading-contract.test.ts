import assert from 'node:assert/strict';
import { test } from 'node:test';
import fs from 'node:fs';
import path from 'node:path';

test('Spark association UI reads only relations', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactAssociationsSection.tsx'), 'utf8');
  assert.match(source, /projectFactReadingAssociations/);
  assert.doesNotMatch(source, /projectMaterials|evidenceMaterials|externalInputs/);
});

test('every fact list card shows exact-read formal associations in a minimal secondary-reading row', () => {
  const source = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');
  const docs = fs.readFileSync(path.resolve('../web/docs/03-ObjectList.md'), 'utf8');

  assert.match(source, /function FactAssociationsCardContent/);
  assert.match(source, /associations=\{obj\.factAssociations\}/);
  assert.match(source, /dedupeFactCardAssociations\(associations\)/);
  assert.match(source, /visibleAssociations\.map/);
  assert.match(source, /whitespace-normal break-words/);
  assert.match(source, /openPanel\(\{ type: 'object', title, objectType: target\.factTypeKey, objectId: target\.objectId \}\)/);
  assert.doesNotMatch(source, /StatusBadge status=\{association\.status\}/);
  assert.match(source, /dedupeFactCardAssociations\(associations\)[\s\S]*\.filter\(\(association\) => !\['closed', 'implemented', 'discarded', 'retired'\]\.includes\(association\.status \?\? ''\)\)/);
  assert.doesNotMatch(source, /getFieldLabel\('fact_associations'/);
  assert.doesNotMatch(source, /ObjectReferenceCopyButton/);
  assert.doesNotMatch(source, /factAssociations[^\n]{0,120}\.slice\(/);
  const detailSource = fs.readFileSync(path.resolve('src/pages/object-detail/factReadingProjection.ts'), 'utf8');
  assert.match(detailSource, /dedupeRelationsByTarget/);
  assert.match(docs, /正式 `relations` 由所有五类对象 Card 统一呈现/);
});

test('Spark terminal headings distinguish implemented and discarded with a legacy fallback', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactReadingLayouts.tsx'), 'utf8');
  const list = fs.readFileSync(path.resolve('src/pages/ObjectList.tsx'), 'utf8');
  const badge = fs.readFileSync(path.resolve('src/components/StatusBadge.tsx'), 'utf8');

  assert.match(source, /obj\.status === 'implemented' \|\| obj\.status === 'discarded'/);
  assert.match(source, /getObjectStatusLocale\('spark', String\(obj\.status\), locale\)/);
  assert.match(source, /labelKey: 'routing'/);
  assert.match(list, /tone=\{obj\.status === 'implemented' \? 'implemented' : 'retired'\}/);
  assert.match(badge, /objectType === 'spark' && status === 'discarded'/);
  assert.match(badge, /objectType === 'adr' && status === 'retired'/);
});
