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

test('FileAsset list cards defer carrier metadata to detail and show only the deletion reason when terminal', () => {
  const objectList = read('src/pages/ObjectList.tsx');
  const fileAssetDetail = read('src/pages/object-detail/FileAssetReadingLayout.tsx');
  const fileAssetCard = objectList.slice(
    objectList.indexOf('function FileAssetCardContent'),
    objectList.indexOf('export default function ObjectList'),
  );

  assert.match(fileAssetCard, /obj\.status !== 'deleted'/);
  assert.match(fileAssetCard, /<TerminalFactPanel[\s\S]*tone="retired"[\s\S]*disposition_summary/);
  assert.doesNotMatch(fileAssetCard, /filename|media_type|size_bytes|formatFileSize/);
  assert.match(fileAssetDetail, /getFieldLabel\('filename', locale\)/);
  assert.match(fileAssetDetail, /getFieldLabel\('media_type', locale\)/);
  assert.match(fileAssetDetail, /getFieldLabel\('size_bytes', locale\)/);
  assert.match(fileAssetDetail, /ldvh-study-node-content grid min-w-0/);
  assert.match(fileAssetDetail, /'ldvh-caption-strong text-ldvh-text-secondary\/80'/);
  assert.match(fileAssetDetail, /hideLabel/);
  assert.match(fileAssetDetail, /hideLabel \? 'sr-only'/);
  assert.match(fileAssetDetail, /aria-label=\{hideLabel \? label : undefined\}/);
  assert.match(fileAssetDetail, /ldvh-detail-semantic-body/);
  assert.doesNotMatch(fileAssetDetail, /font-mono/);
  assert.doesNotMatch(fileAssetDetail, /<DetailInlineField/);
});

test('FileAsset detail exposes its YAML manifest as the standard collapsed technical node', () => {
  const objectDetail = read('src/pages/ObjectDetail.tsx');

  assert.match(
    objectDetail,
    /objType === 'file-asset' && readMeta\.carrier === 'directory'/,
  );
  assert.match(objectDetail, /const yamlSource = showYamlSource \? reconstructFactYaml\(obj\) : ''/);
  assert.match(objectDetail, /aria-expanded=\{showYaml\}/);
  assert.match(objectDetail, /objectDetail\.yamlSource/);
});

test('FileAsset payload preview stays separate from object metadata and opens in secondary reading', () => {
  const fileAssetDetail = read('src/pages/object-detail/FileAssetReadingLayout.tsx');
  const panelContext = read('src/utils/panelContext.tsx');
  const panelContent = read('src/components/reading-panel/PanelContent.tsx');
  const api = read('src/utils/api.ts');
  const objectRoutes = read('api/routes/objects.ts');
  const previewService = read('api/services/fileAssetPreview.ts');

  assert.match(fileAssetDetail, /type: 'file-preview'/);
  assert.match(fileAssetDetail, /objectDetail\.openReadingPanel/);
  assert.match(fileAssetDetail, /<ChevronRight size=\{14\}/);
  assert.match(panelContext, /'file-preview'/);
  assert.match(panelContent, /fetchFileAssetPreview/);
  assert.match(panelContent, /blockRemoteImages/);
  assert.match(api, /\/objects\/file-asset\/\$\{encodeURIComponent\(objectId\)\}\/preview/);
  assert.match(objectRoutes, /router\.get\('\/file-asset\/:id\/preview'/);
  assert.match(previewService, /FILE_ASSET_PREVIEW_LIMIT_BYTES = 4 \* 1024 \* 1024/);
  assert.match(previewService, /O_NOFOLLOW/);
  assert.match(previewService, /createHash\('sha256'\)/);
});

test('prominent card title follows the documented 16px by 24px hierarchy', () => {
  const styles = read('src/index.css');
  assert.match(styles, /\.ldvh-card-title-prominent[\s\S]*text-base font-semibold leading-6/);
  assert.match(styles, /\.ldvh-inline-markdown\.ldvh-card-decision-body[\s\S]*text-xs leading-5/);
});

test('commit hotspots keep a compact relationship overview and a focused one-hop mind map', () => {
  const graph = read('src/pages/cognition/CommitHotspotGraph.tsx');
  const cognitionCenter = read('src/pages/CognitionCenter.tsx');
  const styles = read('src/index.css');

  assert.match(graph, /relatedWorkItems\(cluster\.relations\)/);
  assert.match(graph, /const items = new Map<string, RelatedWork>\(\)/);
  assert.match(graph, /const COMPACT_WORK_LIMIT = 5/);
  assert.match(graph, /const primarySize = \{ width: Math\.max\(96, width - horizontalPadding \* 2\), height: 120 \}/);
  assert.match(graph, /const relatedSize = \{ width: primarySize\.width \* 0\.75, height: 120 \}/);
  assert.match(graph, /className={`flex h-full min-w-0 flex-col items-center justify-center px-3 py-2\.5 \$\{expanded \? 'gap-2' : 'gap-1'\}`}/);
  assert.match(graph, /className="inline-flex h-6 w-6 shrink-0 items-center justify-center"/);
  assert.match(graph, /className={`block w-full/);
  assert.match(graph, /data-hotspot-node-meta className="mt-0\.5 flex min-w-0/);
  assert.match(graph, /const relatedSize = \{ width: primarySize\.width \* 0\.75, height: 152 \}/);
  assert.match(graph, /position: \{ x: width \/ 2, y: firstRelatedY \+ index \* rowGap \}/);
  assert.doesNotMatch(graph, /supportedColumns|indexInRow|nodesInRow/);
  assert.doesNotMatch(graph, /Math\.min\((272|320|420|440|460),/);
  assert.match(graph, /function compactLayout/);
  assert.match(graph, /function compactMultiRoutePath/);
  assert.match(graph, /function expandedLayout/);
  assert.match(graph, /function splitMindMapSides/);
  assert.match(graph, /function expandedMindMapAnchors/);
  assert.match(graph, /mode === 'expanded' && layout\.edgeOrientation === 'horizontal'[\s\S]*expandedMindMapAnchors/);
  assert.match(graph, /x: primaryPosition\.x \+ \(relatedOnLeft \? -primarySize\.width \/ 2 : primarySize\.width \/ 2\)/);
  assert.match(graph, /x: relatedPosition\.x \+ \(relatedOnLeft \? relatedSize\.width \/ 2 : -relatedSize\.width \/ 2\)/);
  assert.match(graph, /function CompactHotspotDiagram/);
  assert.match(graph, /function ExpandedHotspotMindMap/);
  assert.match(graph, /function DiagramEdges/);
  assert.match(graph, /function AccessibleRelationList/);
  assert.match(graph, /cognition\.commitHotspots\.workRelation\.related/);
  assert.match(graph, /getFieldLabel\(`relation_\$\{relationKey\.replace/);
  assert.match(graph, /className="ml-auto flex min-w-0 flex-wrap items-center justify-end/);
  assert.match(graph, /<GitCommitHorizontal size=\{12\} \/>[\s\S]*cognition\.commitHotspots\.commitRefs[\s\S]*relationKeys\.map/);
  assert.match(graph, /mode === 'expanded'/);
  assert.match(graph, /markerStart=\{directions\.incoming/);
  assert.match(graph, /markerEnd=\{directions\.outgoing/);
  assert.match(graph, /highlightedKey !== null && highlightedKey !== key/);
  assert.match(graph, /mode="compact" layout=\{layout\} highlightedKey=\{highlightedKey\}/);
  assert.match(graph, /mode === 'compact' && layout\.edgeOrientation === 'vertical'[\s\S]*compactMultiRoutePath/);
  assert.match(graph, /mode="compact"[\s\S]*dimmed=\{highlightedKey !== null && highlightedKey !== key\}[\s\S]*onHighlight=\{\(active\) => setHighlightedKey/);
  assert.match(graph, /aria-label=\{`\$\{roleLabel\}: \$\{title\}[\s\S]*cognition\.commitHotspots\.commitRefs/);
  assert.doesNotMatch(graph, /title=\{labels\.join\(' · '\)\}/);
  assert.match(graph, /data-hotspot-node-header[\s\S]*PriorityIcon[\s\S]*node\.id[\s\S]*data-hotspot-node-title[\s\S]*data-hotspot-node-meta[\s\S]*node\.commitRefs\.length[\s\S]*status/);
  assert.match(graph, /primary \? 18 : \(expanded \? 18 : 16\)/);
  assert.match(graph, /primary \? \(expanded \? 'text-lg font-semibold leading-6' : 'text-base font-semibold leading-\[22px\]'\) : 'text-sm font-medium leading-5'/);
  assert.match(graph, /gridColumn: '1 \/ -1'/);
  assert.match(graph, /data-hotspot-mode=\{expanded \? 'expanded' : 'compact'\}/);
  assert.match(graph, /cognition\.commitHotspots\.expandClusterWidth/);
  assert.match(graph, /cognition\.commitHotspots\.restoreClusterWidth/);
  assert.match(graph, /aria-expanded=\{expanded\}/);
  assert.match(graph, /aria-controls=\{contentId\}/);
  assert.match(graph, /canExpand &&/);
  assert.match(graph, /<code className="ldvh-meta-muted shrink-0">\{node\.id\}<\/code>/);
  assert.doesNotMatch(graph, /forceSimulation|d3-force|semanticSimilarity|multiHop/);
  assert.match(cognitionCenter, /ldvh-hotspot-grid min-w-0 items-start/);
  assert.match(cognitionCenter, /type CommitHotspotStatusFilter = 'all' \| 'progressing' \| 'decision' \| 'settled'/);
  assert.match(cognitionCenter, /useState<CommitHotspotStatusFilter>\('progressing'\)/);
  assert.match(cognitionCenter, /getCommitHotspotStatusGroup\(cluster\.primary\) === commitHotspotStatusFilter/);
  assert.match(cognitionCenter, /COMMIT_HOTSPOT_STATUS_FILTERS\.map/);
  assert.match(cognitionCenter, /aria-pressed=\{commitHotspotStatusFilter === filter\}/);
  assert.match(cognitionCenter, /setExpandedHotspotKey\(null\)/);
  assert.match(cognitionCenter, /filteredCommitHotspotClusters\.map/);
  assert.match(cognitionCenter, /cognition\.commitHotspots\.filterEmpty/);
  assert.match(styles, /\.ldvh-hotspot-grid[\s\S]*width: 100%[\s\S]*max\(22rem, calc\(\(100% - 6rem\) \/ 5\)\)/);
  assert.doesNotMatch(styles, /\.ldvh-hotspot-grid[\s\S]{0,180}max-width/);
  assert.match(cognitionCenter, /expandedHotspotKey/);
  assert.match(cognitionCenter, /canExpand=\{cluster\.relations\.length > 0\}/);
  assert.match(cognitionCenter, /expanded=\{expandedHotspotKey ===/);
  assert.doesNotMatch(cognitionCenter, /cognition-commit-hotspots-content" className="flex min-h-0 flex-1/);
  assert.doesNotMatch(graph, /<section className="flex h-full/);
});

test('Web development docs describe the current Focus modules, shell scrolling, and reading panel', () => {
  const globalDoc = read('docs/01-全局设计约束.md');
  const cognitionDoc = read('docs/02-CognitionCenter.md');
  const baselineDoc = read('docs/10-Web开发现状与设计语言基线.md');
  const cognitionCenter = read('src/pages/CognitionCenter.tsx');

  assert.match(cognitionDoc, /三期均已完成/);
  assert.match(cognitionDoc, /待决定事项.*推进中事项.*Spark 健康度.*近期动态.*近期提交热点关系/);
  assert.match(cognitionCenter, /模块二 近期动态[\s\S]*?<section className="order-2 rounded-xl/);
  assert.match(cognitionCenter, /模块四 Spark 池健康[\s\S]*?<section className="order-1 rounded-xl/);
  assert.match(cognitionDoc, /HV1-HV5/);
  assert.match(cognitionDoc, /HV1 \| 决策提请清晰可决/);
  assert.match(cognitionDoc, /HV2 \| 授权执行受控可续/);
  assert.match(cognitionDoc, /HV3 \| 入档闭环节点可验/);
  assert.match(cognitionDoc, /HV4 \| 积累效用直观可见.*尚未完整承接/);
  assert.match(cognitionDoc, /HV5 \| 项目演进脉络可循/);
  assert.match(cognitionDoc, /不再是当前价值标准来源/);
  assert.doesNotMatch(cognitionDoc, /服务六项 Human 价值标准/);
  assert.doesNotMatch(cognitionDoc, /H1[–-]H6 当前由 open Spark/);
  assert.match(cognitionDoc, /SPARK_SILENT_THRESHOLD_DAYS = 5/);
  assert.match(cognitionDoc, /pitfall_confirmation/);
  assert.doesNotMatch(cognitionDoc, /点击可回指提交短哈希/);
  assert.doesNotMatch(cognitionDoc, /默认 5 天，前端常量/);

  assert.match(globalDoc, /App Shell 根节点唯一拥有视口高度并使用 `overflow-hidden`/);
  assert.match(globalDoc, /左侧导航只在自身条目溢出时纵向滚动/);
  assert.match(globalDoc, /底部阅读抽屉为拖动和触摸保留的头部与按钮命中区/);

  assert.match(baselineDoc, /聚焦 \/ Focus/);
  assert.match(baselineDoc, /桌面右侧面板保留拖动宽度、前后导航和关闭控件/);
  assert.match(baselineDoc, /不显示或复制页面“观察时间”/);
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
