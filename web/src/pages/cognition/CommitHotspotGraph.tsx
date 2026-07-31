import { useEffect, useMemo, useRef, useState } from 'react';
import { GitCommitHorizontal } from 'lucide-react';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getLocalizedObjectTitle, getObjectStatusLocale, getTypeLabel, type LocaleKey } from '@/i18n/locales';
import { usePanel } from '@/utils/panelContext';
import type {
  CognitionCommitHotspotCluster,
  CognitionCommitHotspotNode,
} from '@/utils/api';

type Position = { x: number; y: number };
type NodeSize = { width: number; height: number };
type NodeRole = 'primary' | 'secondary-hotspot' | 'related-work';

const PRIMARY_NODE_MIN_WIDTH = 244;
const PRIMARY_NODE_MAX_WIDTH = 340;
const PRIMARY_NODE_HEIGHT = 96;
const RELATED_NODE_MIN_WIDTH = 172;
const RELATED_NODE_WIDE_WIDTH = 220;
const RELATED_NODE_NARROW_MAX_WIDTH = 300;
const RELATED_NODE_HEIGHT = 82;
const GRAPH_MIN_WIDTH = 280;
const GRAPH_MAX_WIDTH = 760;
const SINGLE_COLUMN_WIDTH = 520;

/**
 * Small clusters use one deterministic anchor-and-grid layout. It is not a
 * force graph and never infers relation strength: order only affects reading.
 */
function createLayout(nodes: CognitionCommitHotspotNode[], availableWidth?: number): {
  width: number;
  height: number;
  positions: Map<string, Position>;
  sizes: Map<string, NodeSize>;
} {
  const fallbackWidth = Math.max(GRAPH_MIN_WIDTH, Math.min(GRAPH_MAX_WIDTH, Math.max(2, Math.ceil(Math.sqrt(nodes.length))) * 220));
  const width = availableWidth && availableWidth > 0
    ? Math.max(GRAPH_MIN_WIDTH, Math.min(GRAPH_MAX_WIDTH, Math.floor(availableWidth)))
    : fallbackWidth;
  const remaining = nodes.slice(1);
  const narrowRelatedWidth = Math.min(
    RELATED_NODE_NARROW_MAX_WIDTH,
    Math.max(RELATED_NODE_MIN_WIDTH, width - 32),
  );
  const candidateRelatedWidth = width < SINGLE_COLUMN_WIDTH ? narrowRelatedWidth : RELATED_NODE_WIDE_WIDTH;
  const supportedColumns = Math.max(1, Math.floor((width - 20) / (candidateRelatedWidth + 28)));
  const columns = Math.max(1, Math.min(4, supportedColumns, Math.ceil(Math.sqrt(Math.max(remaining.length, 1)))));
  const relatedWidth = columns === 1 ? narrowRelatedWidth : RELATED_NODE_WIDE_WIDTH;
  const rows = remaining.length > 0 ? Math.ceil(remaining.length / columns) : 0;
  const primaryWidth = Math.min(PRIMARY_NODE_MAX_WIDTH, Math.max(PRIMARY_NODE_MIN_WIDTH, width - 32));
  const primaryY = 50;
  const firstRelatedY = primaryY + PRIMARY_NODE_HEIGHT / 2 + 14 + RELATED_NODE_HEIGHT / 2;
  const rowStep = RELATED_NODE_HEIGHT + 16;
  const height = rows === 0
    ? PRIMARY_NODE_HEIGHT + 20
    : firstRelatedY + (rows - 1) * rowStep + RELATED_NODE_HEIGHT / 2 + 12;
  const positions = new Map<string, Position>();
  const sizes = new Map<string, NodeSize>();
  if (nodes[0]) {
    positions.set(nodeKey(nodes[0]), { x: width / 2, y: primaryY });
    sizes.set(nodeKey(nodes[0]), { width: primaryWidth, height: PRIMARY_NODE_HEIGHT });
  }
  const horizontalPadding = Math.min(relatedWidth / 2 + 10, Math.max(relatedWidth / 2, width / 2));
  const gridWidth = Math.max(0, width - horizontalPadding * 2);
  remaining.forEach((node, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    const nodesInRow = Math.min(columns, remaining.length - row * columns);
    const rowGap = nodesInRow > 1 ? Math.min(300, gridWidth / (nodesInRow - 1)) : 0;
    const rowStart = (width - rowGap * (nodesInRow - 1)) / 2;
    positions.set(nodeKey(node), {
      x: rowStart + column * rowGap,
      y: firstRelatedY + row * rowStep,
    });
    sizes.set(nodeKey(node), { width: relatedWidth, height: RELATED_NODE_HEIGHT });
  });
  return { width, height, positions, sizes };
}

function nodeKey(node: CognitionCommitHotspotNode): string {
  return `${node.type}:${node.id}`;
}

function relationColor(relationKey: string): string {
  const colors = ['#64748b', '#0f766e', '#2563eb', '#7c3aed', '#b45309'];
  let hash = 0;
  for (const character of relationKey) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  return colors[hash % colors.length];
}

function relationDashArray(relationKey: string): string | undefined {
  if (relationKey === 'related-to') return undefined;
  if (relationKey === 'routed-to') return '7 4';
  if (relationKey === 'informs') return '2 4';
  if (relationKey === 'inspired-by') return '10 3 2 3';
  return '5 4';
}

function getNodeRole(node: CognitionCommitHotspotNode, primaryKey: string): NodeRole {
  if (nodeKey(node) === primaryKey) return 'primary';
  return node.commitRefs.length > 0 ? 'secondary-hotspot' : 'related-work';
}

function getNodeSize(role: NodeRole): NodeSize {
  return role === 'primary'
    ? { width: PRIMARY_NODE_MIN_WIDTH, height: PRIMARY_NODE_HEIGHT }
    : { width: RELATED_NODE_MIN_WIDTH, height: RELATED_NODE_HEIGHT };
}

function rectangleEdgePoint(from: Position, to: Position, size: { width: number; height: number }): Position {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  if (dx === 0 && dy === 0) return from;
  const xScale = dx === 0 ? Number.POSITIVE_INFINITY : (size.width / 2) / Math.abs(dx);
  const yScale = dy === 0 ? Number.POSITIVE_INFINITY : (size.height / 2) / Math.abs(dy);
  const scale = Math.min(xScale, yScale);
  return { x: from.x + dx * scale, y: from.y + dy * scale };
}

function curvedEdgePath(start: Position, end: Position): string {
  const dy = end.y - start.y;
  if (Math.abs(dy) < 10) {
    const middleX = (start.x + end.x) / 2;
    return `M ${start.x} ${start.y} C ${middleX} ${start.y}, ${middleX} ${end.y}, ${end.x} ${end.y}`;
  }
  const middleY = (start.y + end.y) / 2;
  return `M ${start.x} ${start.y} C ${start.x} ${middleY}, ${end.x} ${middleY}, ${end.x} ${end.y}`;
}

function relationMarkerId(index: number, relationKey: string): string {
  return `commit-hotspot-arrow-${index}-${relationKey.replace(/[^a-z0-9_-]/gi, '-')}`;
}

function RelationSwatch({ relationKey }: { relationKey: string }) {
  const color = relationColor(relationKey);
  return (
    <svg width="28" height="10" viewBox="0 0 28 10" aria-hidden="true" className="shrink-0 overflow-visible">
      <line x1="1" y1="5" x2="23" y2="5" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeDasharray={relationDashArray(relationKey)} />
      <path d="M 21.5 2 L 26 5 L 21.5 8" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CommitHotspotLegend({
  clusters,
  totalCommits,
  hotspotTotal,
  relationTotal,
}: {
  clusters: CognitionCommitHotspotCluster[];
  totalCommits: number;
  hotspotTotal: number;
  relationTotal: number;
}) {
  const { locale, t } = useI18n();
  const relationKeys = [...new Set(clusters.flatMap((cluster) => cluster.edges.map((edge) => edge.relationKey)))].sort();
  const nodeTypes = [...new Map(
    clusters.flatMap((cluster) => cluster.nodes).map((node) => [node.type, node.typeColor] as const),
  ).entries()].sort(([a], [b]) => a.localeCompare(b));
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5 border-y border-ldvh-border/70 py-2.5">
      <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5">
        <span className="ldvh-caption text-ldvh-text-secondary">{t('cognition.commitHotspots.totalCommits', { count: String(totalCommits) })}</span>
        <span className="ldvh-caption text-ldvh-text-secondary">{t('cognition.commitHotspots.summary', { hotspots: String(hotspotTotal), relations: String(relationTotal) })}</span>
      </div>
      <div className="ml-auto flex min-w-0 flex-wrap items-center justify-end gap-x-3 gap-y-1.5">
        <span className="inline-flex items-center gap-1 ldvh-caption text-ldvh-text-secondary/75">
          <GitCommitHorizontal size={14} className="text-ldvh-accent" aria-hidden="true" />
          {t('cognition.commitHotspots.legend.hotspot')}
        </span>
        {nodeTypes.map(([type, color]) => (
          <span key={type} className="inline-flex items-center gap-1 ldvh-caption text-ldvh-text-secondary/75">
            <ObjectTypeIcon type={type} size={14} style={{ color }} aria-hidden="true" />
            {getTypeLabel(type, locale)}
          </span>
        ))}
        {relationKeys.map((relationKey) => (
          <span key={relationKey} className="inline-flex items-center gap-1 ldvh-caption text-ldvh-text-secondary/75">
            <RelationSwatch relationKey={relationKey} />
            <span title={relationKey}>{getFieldLabel(`relation_${relationKey.replace(/-/g, '_')}`, locale)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function GraphNode({ node, position, role, size }: {
  node: CognitionCommitHotspotNode;
  position: Position;
  role: NodeRole;
  size: NodeSize;
}) {
  const { locale, t } = useI18n();
  const { openPanel } = usePanel();
  const title = getLocalizedObjectTitle(node, locale, node.id);
  const status = node.type === 'workcase' ? node.progress_group : node.status;
  const roleLabel = t(`cognition.commitHotspots.nodeRole.${role}` as LocaleKey);
  return (
    <button
      type="button"
      onClick={() => openPanel({ type: 'object', title, objectType: node.type, objectId: node.id })}
      aria-label={`${roleLabel}: ${title}`}
      className={`absolute min-w-0 rounded-lg border bg-ldvh-panel px-2.5 py-2 text-left shadow-sm transition-[border-color,box-shadow] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ldvh-accent/50 ${
        role === 'primary' ? 'border-ldvh-accent/50 shadow-md' : 'border-ldvh-border'
      } hover:border-ldvh-accent/40 hover:shadow-md`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        transform: 'translate(-50%, -50%)',
        borderTopColor: node.typeColor,
        borderTopWidth: role === 'primary' ? 3 : 2,
      }}
    >
      <div className={role === 'primary'
        ? 'grid h-full min-w-0 grid-cols-[40px_minmax(0,1fr)_40px] items-center gap-1'
        : 'grid h-full min-w-0 grid-cols-[32px_minmax(0,1fr)_32px] items-center gap-1'}>
        <span className={role === 'primary'
          ? 'inline-flex h-8 w-10 items-center justify-center'
          : 'inline-flex h-8 w-8 items-center justify-center'}>
          <ObjectTypeIcon
            type={node.type}
            size={role === 'primary' ? 22 : 16}
            style={{ color: node.typeColor }}
          />
        </span>
        <div className="min-w-0 flex-1">
          <span
            title={title}
            className={`block overflow-hidden text-center text-ldvh-text-primary ${role === 'primary' ? 'text-[15px] font-semibold leading-5' : 'text-sm font-medium leading-5'}`}
            style={{ display: '-webkit-box', WebkitBoxOrient: 'vertical', WebkitLineClamp: 2 }}
          >
            {title}
          </span>
          <div className="mt-1 flex min-w-0 flex-wrap items-center justify-center gap-x-1.5 gap-y-0.5">
            <code className="ldvh-meta-muted shrink-0">{node.id}</code>
            <PriorityIcon source={node} type={node.type} locale={locale} size="sm" />
            {status && <span className="ldvh-caption shrink-0 text-ldvh-text-secondary/70">{getObjectStatusLocale(node.type, status, locale)}</span>}
          </div>
        </div>
        {node.commitRefs.length > 0 && (
          <span className={`inline-flex shrink-0 items-center gap-1 rounded-full border border-ldvh-accent/25 bg-ldvh-accent/5 px-1.5 py-0.5 text-[11px] font-medium text-ldvh-accent ${role === 'primary' ? 'justify-self-center' : ''}`} title={t('cognition.commitHotspots.commitRefs')}>
            <GitCommitHorizontal size={12} aria-hidden="true" />
            {node.commitRefs.length}
          </span>
        )}
      </div>
    </button>
  );
}

export function CommitHotspotCluster({ cluster, index }: { cluster: CognitionCommitHotspotCluster; index: number }) {
  const { t } = useI18n();
  const diagramHostRef = useRef<HTMLDivElement>(null);
  const [diagramWidth, setDiagramWidth] = useState<number>();
  useEffect(() => {
    const host = diagramHostRef.current;
    if (!host) return undefined;
    const syncWidth = () => setDiagramWidth(Math.floor(host.getBoundingClientRect().width));
    syncWidth();
    const observer = new ResizeObserver(syncWidth);
    observer.observe(host);
    return () => observer.disconnect();
  }, []);
  const primary = cluster.nodes[0];
  const primaryKey = primary ? nodeKey(primary) : '';
  const layout = useMemo(() => createLayout(cluster.nodes, diagramWidth), [cluster.nodes, diagramWidth]);
  const relatedWorkCount = Math.max(0, cluster.nodes.length - 1);

  if (!primary) return null;

  return (
    <section className="flex min-w-0 flex-col overflow-hidden rounded-lg border border-ldvh-border/75 bg-ldvh-bg/35 p-3">
      <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
        <p className="ldvh-caption-strong text-ldvh-text-secondary">{t('cognition.commitHotspots.cluster', { count: String(index + 1) })}</p>
        <span className="ldvh-caption text-ldvh-text-secondary/65">
          {t('cognition.commitHotspots.clusterSummary', {
            commits: String(primary.commitRefs.length),
            work: String(relatedWorkCount),
          })}
        </span>
      </div>
      <div ref={diagramHostRef} className="mt-2 flex min-w-0 justify-center">
        <div className="relative mx-auto" style={{ width: `${layout.width}px`, maxWidth: '100%', height: `${layout.height}px` }}>
          <svg className="pointer-events-none absolute inset-0 h-full w-full" viewBox={`0 0 ${layout.width} ${layout.height}`} aria-hidden="true">
            <defs>
              {[...new Set(cluster.edges.map((edge) => edge.relationKey))].map((relationKey) => (
                <marker key={relationKey} id={relationMarkerId(index, relationKey)} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
                  <path d="M 0.5 0.5 L 6 3.5 L 0.5 6.5 z" fill={relationColor(relationKey)} />
                </marker>
              ))}
            </defs>
            {cluster.edges.map((edge) => {
              const source = layout.positions.get(edge.source);
              const target = layout.positions.get(edge.target);
              if (!source || !target) return null;
              const color = relationColor(edge.relationKey);
              const sourceNode = cluster.nodes.find((node) => nodeKey(node) === edge.source);
              const targetNode = cluster.nodes.find((node) => nodeKey(node) === edge.target);
              if (!sourceNode || !targetNode) return null;
              const start = rectangleEdgePoint(source, target, layout.sizes.get(edge.source) ?? getNodeSize(getNodeRole(sourceNode, primaryKey)));
              const end = rectangleEdgePoint(target, source, layout.sizes.get(edge.target) ?? getNodeSize(getNodeRole(targetNode, primaryKey)));
              return (
                <path
                    key={`${edge.source}-${edge.target}-${edge.relationKey}`}
                    d={curvedEdgePath(start, end)}
                    fill="none"
                    stroke={color}
                    strokeOpacity="0.68"
                    strokeWidth="1.7"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray={relationDashArray(edge.relationKey)}
                    markerEnd={`url(#${relationMarkerId(index, edge.relationKey)})`}
                    vectorEffect="non-scaling-stroke"
                  />
              );
            })}
          </svg>
          {cluster.nodes.map((node) => {
            const position = layout.positions.get(nodeKey(node));
            const key = nodeKey(node);
            const size = layout.sizes.get(key);
            return position && size ? (
              <GraphNode
                key={key}
                node={node}
                position={position}
                role={getNodeRole(node, primaryKey)}
                size={size}
              />
            ) : null;
          })}
        </div>
      </div>
    </section>
  );
}
