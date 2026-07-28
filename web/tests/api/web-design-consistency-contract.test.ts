import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('mobile controls preserve the 44px touch target without enlarging desktop icons', () => {
  const styles = read('src/index.css');
  const copyButton = read('src/components/CopyPathButton.tsx');
  const readingPanel = read('src/components/ReadingPanel.tsx');
  const objectDetail = read('src/pages/ObjectDetail.tsx');

  assert.match(styles, /\.ldvh-tab-button[\s\S]*min-h-11[\s\S]*sm:min-h-0/);
  assert.match(copyButton, /h-11 w-11[\s\S]*sm:h-7 sm:w-7/);
  assert.match(readingPanel, /h-11 w-11[\s\S]*md:h-7 md:w-7/);
  assert.equal((objectDetail.match(/ldvh-section-title flex min-h-11/g) ?? []).length, 2);
});

test('mobile reading panel identifies the current object and terminal cards retain status identity', () => {
  const readingPanel = read('src/components/ReadingPanel.tsx');
  const objectList = read('src/pages/ObjectList.tsx');

  assert.match(readingPanel, /ldvh-card-title w-full truncate text-center">{panelTitle}/);
  assert.match(objectList, /<StatusBadge status={presentedStatus}/);
  assert.doesNotMatch(objectList, /showStatusBadge/);
});

test('fact reading labels use the central locale registry', () => {
  const layouts = read('src/pages/object-detail/FactReadingLayouts.tsx');
  const associations = read('src/pages/object-detail/FactAssociationsSection.tsx');

  assert.match(layouts, /getFieldLabel\(node\.field, locale\)/);
  assert.match(layouts, /getObjectStatusLocale\('spark'/);
  assert.doesNotMatch(layouts, /locale === 'en'/);
  assert.match(associations, /getLocalizedObjectTitle\(source, locale\)/);
});

test('prominent card title follows the documented 16px by 24px hierarchy', () => {
  const styles = read('src/index.css');
  assert.match(styles, /\.ldvh-card-title-prominent[\s\S]*text-base font-semibold leading-6/);
});
