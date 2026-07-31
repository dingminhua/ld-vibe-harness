import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

function read(relativePath: string) {
  return fs.readFileSync(path.resolve(relativePath), 'utf8');
}

function collectSourceFiles(directory: string): string[] {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const filePath = path.join(directory, entry.name);
    if (entry.isDirectory()) return collectSourceFiles(filePath);
    return /\.(?:css|ts|tsx)$/.test(entry.name) ? [filePath] : [];
  });
}

test('compact width only changes the shell navigation and secondary reading placement', () => {
  const styles = read('src/index.css');
  const layout = read('src/components/Layout.tsx');
  const copyButton = read('src/components/CopyPathButton.tsx');
  const readingPanel = read('src/components/ReadingPanel.tsx');
  const cognitionCenter = read('src/pages/CognitionCenter.tsx');
  const objectDetail = read('src/pages/ObjectDetail.tsx');
  const objectList = read('src/pages/ObjectList.tsx');

  assert.match(layout, /className="flex flex-shrink-0 sm:hidden"[\s\S]*<Sidebar collapsed compact \/>/);
  assert.match(readingPanel, /const MOBILE_BREAKPOINT = 640/);
  assert.match(readingPanel, /if \(isMobile\)[\s\S]*fixed bottom-0 left-0 right-0/);
  assert.match(styles, /\.ldvh-page-frame\s*\{\s*@apply p-6;/);
  assert.match(styles, /\.ldvh-tab-button\s*\{\s*@apply inline-flex min-w-0[\s\S]*?\}/);
  assert.doesNotMatch(styles, /\.ldvh-tab-button[\s\S]*min-h-11|\.ldvh-tab-list[\s\S]*min-h-11/);
  assert.doesNotMatch(objectList, /onClick=\{\(\) => onOpen\(obj\.id\)\}[\s\S]{0,180}min-h-11/);
  assert.match(copyButton, /inline-flex h-7 w-7/);
  assert.match(cognitionCenter, /cursor-pointer flex-wrap items-center[\s\S]{0,500}cognition\.sparkHealth\.title/);
  assert.doesNotMatch(cognitionCenter, /cognition\.sparkHealth\.title[\s\S]{0,220}\btruncate\b/);
  assert.doesNotMatch(copyButton, /\b(?:sm|md):/);
  assert.doesNotMatch(objectDetail, /\b(?:sm|md):/);

  const compactBranchesOutsideShell = collectSourceFiles('src')
    .filter((filePath) => !filePath.endsWith('components/Layout.tsx'))
    .filter((filePath) => !filePath.endsWith('components/ReadingPanel.tsx'))
    .map((filePath) => fs.readFileSync(filePath, 'utf8'))
    .join('\n');
  assert.doesNotMatch(compactBranchesOutsideShell, /\b(?:sm|md):/);
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

test('commit hotspot nodes consume narrow-cluster width before truncating facts', () => {
  const graph = read('src/pages/cognition/CommitHotspotGraph.tsx');
  const cognitionCenter = read('src/pages/CognitionCenter.tsx');

  assert.match(graph, /const narrowRelatedWidth = Math\.min\([\s\S]*width - 32/);
  assert.match(graph, /const primaryWidth = Math\.min\([\s\S]*width - 32/);
  assert.match(graph, /WebkitLineClamp: 2/);
  assert.match(graph, /grid-cols-\[32px_minmax\(0,1fr\)_32px\]/);
  assert.match(graph, /mt-1 flex min-w-0 flex-wrap items-center justify-center/);
  assert.match(graph, /<code className="ldvh-meta-muted shrink-0">\{node\.id\}<\/code>/);
  assert.doesNotMatch(graph, /node\.id[\s\S]{0,80}\btruncate\b/);
  assert.match(graph, /ref=\{diagramHostRef\} className="mt-2 flex min-w-0 justify-center"/);
  assert.doesNotMatch(graph, /flex h-full min-w-0 flex-col/);
  assert.match(cognitionCenter, /ldvh-section-grid min-w-0 items-start/);
  assert.doesNotMatch(cognitionCenter, /cognition-commit-hotspots-content" className="flex min-h-0 flex-1/);
  assert.doesNotMatch(graph, /<section className="flex h-full/);
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
