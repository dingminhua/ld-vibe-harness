import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

test('primary mobile controls preserve the 44px touch target while filter tabs remain compact', () => {
  const styles = read('src/index.css');
  const copyButton = read('src/components/CopyPathButton.tsx');
  const readingPanel = read('src/components/ReadingPanel.tsx');
  const objectDetail = read('src/pages/ObjectDetail.tsx');
  const objectList = read('src/pages/ObjectList.tsx');

  assert.match(styles, /\.ldvh-tab-button\s*\{\s*@apply inline-flex min-w-0[\s\S]*?\}/);
  assert.doesNotMatch(styles, /\.ldvh-tab-button[\s\S]*min-h-11|\.ldvh-tab-list[\s\S]*min-h-11/);
  assert.doesNotMatch(objectList, /onClick=\{\(\) => onOpen\(obj\.id\)\}[\s\S]{0,180}min-h-11/);
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

test('detail identity header keeps status immediately before its copy control', () => {
  const objectDetail = read('src/pages/ObjectDetail.tsx');
  const identityHeader = objectDetail.slice(
    objectDetail.indexOf('export function ObjectIdentityHeader'),
    objectDetail.indexOf('function HeaderDateMeta'),
  );

  assert.match(
    identityHeader,
    /className="ml-auto flex shrink-0 items-center gap-2"[\s\S]{0,700}statusLabel \|\| status[\s\S]{0,320}<CopyPathButton path=\{target\}/,
  );
  assert.doesNotMatch(identityHeader, /\{extraBadges\}[\s\S]{0,320}statusLabel \|\| status/);
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
  assert.match(styles, /\.ldvh-inline-markdown\.ldvh-card-decision-body[\s\S]*text-xs leading-5/);
});

test('WorkCase semantic blocks keep the compact 14/13px by 22px hierarchy', () => {
  const styles = read('src/index.css');
  const layout = read('src/pages/object-detail/WorkCaseReadingLayout.tsx');
  assert.match(styles, /\.ldvh-detail-semantic-title[\s\S]*text-sm font-semibold[\s\S]*line-height: 1\.375rem/);
  assert.match(styles, /\.ldvh-detail-semantic-body[\s\S]*font-size: 0\.8125rem[\s\S]*line-height: 1\.375rem/);
  assert.match(styles, /\.ldvh-inline-markdown\.ldvh-detail-semantic-body[\s\S]*font-size: 0\.8125rem[\s\S]*line-height: 1\.375rem/);
  assert.match(layout, /const WORKCASE_DETAIL_SEMANTIC_ICON_SIZE = 14/);
  assert.doesNotMatch(layout, /className=\{`ldvh-body \$\{styles\.body\}`\}/);
});
