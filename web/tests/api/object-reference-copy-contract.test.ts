import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('fact-object copy controls prefer the type-bearing short UID reference with legacy fallback', async () => {
  const { formatObjectReference } = await import('../../src/utils/objectReference.ts');
  assert.equal(formatObjectReference('sample', 'spark-0001', 'spark', 'SABCDE'), 'sample@SABCDE');
  assert.equal(formatObjectReference('sample', 'spark-0001'), 'sample@spark-0001');
  assert.equal(formatObjectReference('sample', 'spark-0001', 'spark', 'AABCDE'), 'sample@spark-0001');
  assert.equal(formatObjectReference('sample', 'spark-0001', 'spark', 'SABC1E'), 'sample@spark-0001');
  assert.equal(formatObjectReference(undefined, undefined), undefined);
  const referenceButton = read('src/components/ObjectReferenceCopyButton.tsx');
  const referenceFormatter = read('src/utils/objectReference.ts');
  const identityActions = read('src/components/ObjectIdentityActions.tsx');
  const cognition = read('src/pages/CognitionCenter.tsx');
  const detail = read('src/pages/ObjectDetail.tsx');
  const associations = read('src/pages/object-detail/FactAssociationsSection.tsx');
  const workcaseReading = read('src/pages/object-detail/WorkCaseReadingLayout.tsx');
  const referenceCard = read('src/components/ReferenceCard.tsx');
  const panelContent = read('src/components/reading-panel/PanelContent.tsx');

  assert.match(referenceButton, /formatObjectReference\(projectId \?\? selectedProjectId, objectId, objectType, shortRef\)/);
  assert.match(referenceFormatter, /\^\[ACPST\]\[A-Z\]\{5\}\$/);
  assert.match(referenceFormatter, /return `\$\{projectId\}@\$\{objectId\}`;/);
  assert.match(identityActions, /objectType=\{objectType\} shortRef=\{shortRef\}/);
  assert.match(cognition, /objectType=\{item\.type\} shortRef=\{item\.short_ref\}/);
  assert.match(cognition, /formatObjectReference\(projectId, item\.id, item\.type, item\.short_ref\)/);
  assert.match(detail, /target=\{objId\}/);
  assert.match(detail, /<ObjectReferenceCopyButton objectId=\{value\}/);
  assert.match(panelContent, /target=\{objectId\}/);
  assert.doesNotMatch(associations, /ObjectReferenceCopyButton/);
  assert.match(associations, /objectType=\{locator\.factTypeKey\} size="xs"/);
  assert.match(workcaseReading, /<ObjectReferenceCopyButton projectId=\{projectId\} objectId=\{objectId\}/);
  assert.match(referenceCard, /<ObjectReferenceCopyButton objectId=\{refId\}/);

  for (const source of [associations, workcaseReading, referenceCard]) {
    assert.doesNotMatch(source, /CopyPathButton path=\{(?:canonicalPath|info\?\.path)\}/);
  }
});
