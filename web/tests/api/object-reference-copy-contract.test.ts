import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('all fact-object copy controls use the governed-project object reference', () => {
  const referenceButton = read('src/components/ObjectReferenceCopyButton.tsx');
  const identityActions = read('src/components/ObjectIdentityActions.tsx');
  const cognition = read('src/pages/CognitionCenter.tsx');
  const detail = read('src/pages/ObjectDetail.tsx');
  const associations = read('src/pages/object-detail/FactAssociationsSection.tsx');
  const workcaseReading = read('src/pages/object-detail/WorkCaseReadingLayout.tsx');
  const referenceCard = read('src/components/ReferenceCard.tsx');
  const panelContent = read('src/components/reading-panel/PanelContent.tsx');

  assert.match(referenceButton, /return `\$\{projectId\}@\$\{objectId\}`;/);
  assert.match(identityActions, /<ObjectReferenceCopyButton objectId=\{target\}/);
  assert.match(cognition, /<ObjectReferenceCopyButton objectId=\{item\.id\}/);
  assert.match(cognition, /formatObjectReference\(projectId, item\.id\)/);
  assert.match(detail, /target=\{objId\}/);
  assert.match(detail, /<ObjectReferenceCopyButton objectId=\{value\}/);
  assert.match(panelContent, /target=\{objectId\}/);
  assert.match(associations, /<ObjectReferenceCopyButton projectId=\{target\.governedProjectId\} objectId=\{target\.objectId\}/);
  assert.match(workcaseReading, /<ObjectReferenceCopyButton projectId=\{projectId\} objectId=\{objectId\}/);
  assert.match(referenceCard, /<ObjectReferenceCopyButton objectId=\{refId\}/);

  for (const source of [associations, workcaseReading, referenceCard]) {
    assert.doesNotMatch(source, /CopyPathButton path=\{(?:canonicalPath|info\?\.path)\}/);
  }
});
