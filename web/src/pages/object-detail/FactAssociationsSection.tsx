import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import StatusBadge from '@/components/StatusBadge';
import { getFieldLabel, getLocalizedObjectTitle, getObjectStatusLocale, getTypeLabel } from '@/i18n/locales';
import {
  ReadingNodeSection,
  getReadingNodeNextState,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';
import {
  groupRelationsByTargetType,
  projectFactReadingAssociations,
  type ReadingRelation,
  type UnresolvedAssociation,
} from '@/pages/object-detail/factReadingProjection';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { fetchObjectDetail, type ObjectDetail } from '@/utils/api';
import { getFactReadMeta, isReadableFact } from '@/utils/factReadMeta';
import { usePanel } from '@/utils/panelContext';

/** Reads the deliberately minimal relation contract, not source or evidence projections. */
export function FactAssociationsSection({
  obj,
  locale,
  title,
}: {
  obj: Record<string, unknown>;
  locale: string;
  title?: string;
  variant?: 'detailed' | 'spark';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const associations = projectFactReadingAssociations(obj);
  if (associations.relations.length === 0 && associations.unresolved.length === 0) return null;
  const currentProjectId = getCurrentProjectId(obj);
  return (
    <ReadingNodeSection
      title={title ?? getFieldLabel('fact_associations', locale)}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="divide-y divide-ldvh-border/60">
        <RelationGroup relations={associations.relations} currentProjectId={currentProjectId} locale={locale} />
        <UnresolvedGroup items={associations.unresolved} locale={locale} />
      </div>
    </ReadingNodeSection>
  );
}

function RelationGroup({ relations, currentProjectId, locale }: {
  relations: ReadingRelation[];
  currentProjectId?: string;
  locale: string;
}) {
  if (relations.length === 0) return null;
  return (
    <div className="flex flex-col gap-4">
      {groupRelationsByTargetType(relations).map(({ factTypeKey, relations: items }) => (
        <div key={factTypeKey} className="min-w-0">
          <div className="ldvh-caption-strong mb-1.5 text-ldvh-text-secondary">
            {getTypeLabel(factTypeKey, locale)}
          </div>
          <div className="divide-y divide-ldvh-border/45">
            {items.map((relation) => <RelationTarget key={relation.originPath} relation={relation} currentProjectId={currentProjectId} locale={locale} />)}
          </div>
        </div>
      ))}
    </div>
  );
}

/** A target is resolved on demand; title and status are never duplicated into relations. */
function RelationTarget({ relation, currentProjectId, locale }: {
  relation: ReadingRelation;
  currentProjectId?: string;
  locale: string;
}) {
  const target = relation.target;
  if (currentProjectId && target.governedProjectId === currentProjectId) {
    return <ReadableRelationTarget target={target} locale={locale} />;
  }
  return <ExternalRelationTarget target={target} />;
}

function ReadableRelationTarget({ target, locale }: {
  target: ReadingRelation['target'];
  locale: string;
}) {
  const { isOpen: panelOpen, content: panelContent, openPanel } = usePanel();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    fetchObjectDetail(target.factTypeKey, target.objectId)
      .then((value) => { if (!cancelled) setDetail(value); })
      .catch(() => { if (!cancelled) setDetail(null); });
    return () => { cancelled = true; };
  }, [target.factTypeKey, target.objectId]);

  const title = detail
    ? getLocalizedObjectTitle(detail.data as { title?: string; title_en?: string; title_zh?: string }, locale, target.objectId)
    : target.objectId;
  const status = detail?.summary.status;
  const readMeta = getFactReadMeta(detail?.data);
  const canonicalPath = isReadableFact(readMeta) ? readMeta.canonicalPath : undefined;
  const typeColor = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;
  const isCurrentPanelOpen = Boolean(panelOpen && panelContent?.type === 'object'
    && panelContent.objectType === target.factTypeKey && panelContent.objectId === target.objectId);
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const open = () => openPanel({ type: 'object', title, objectType: target.factTypeKey, objectId: target.objectId });
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open();
  };

  return (
    <div role="button" tabIndex={0} onClick={open} onKeyDown={onKeyDown} className="group flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50">
      <ObjectTypeIcon type={target.factTypeKey} size={13} className="shrink-0" style={{ color: typeColor }} />
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate group-hover:text-ldvh-accent">{title}</span>
      <span className="ldvh-meta-muted shrink-0">{target.objectId}</span>
      {status && <StatusBadge status={status} statusLabel={getObjectStatusLocale(target.factTypeKey, status, locale)} objectType={target.factTypeKey} size="sm" />}
      <CopyPathButton path={canonicalPath} />
      <PanelIcon size={16} className="shrink-0 text-ldvh-text-secondary/70 transition-colors group-hover:text-ldvh-accent" aria-hidden="true" />
    </div>
  );
}

/** A target outside the currently readable project remains a reference, not a fabricated local object. */
function ExternalRelationTarget({ target }: { target: ReadingRelation['target'] }) {
  const typeColor = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-md px-1.5 py-2">
      <ObjectTypeIcon type={target.factTypeKey} size={13} className="shrink-0" style={{ color: typeColor }} />
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate">{target.objectId}</span>
      <span className="ldvh-meta-muted shrink-0">{target.governedProjectId}</span>
      <CopyPathButton path={`${target.governedProjectId}:${target.factTypeKey}:${target.objectId}`} />
    </div>
  );
}

function UnresolvedGroup({ items, locale }: { items: UnresolvedAssociation[]; locale: string }) {
  if (items.length === 0) return null;
  return (
    <AssociationGroup title={getFieldLabel('unresolved_materials', locale)}>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <div key={item.originPath} className="rounded-md border border-amber-500/25 bg-amber-500/5 px-3 py-2">
            <div className="flex items-center gap-2"><AlertTriangle size={13} className="shrink-0 text-amber-400" /><span className="ldvh-caption-strong">{item.originPath}</span></div>
            <pre className="ldvh-meta-muted mt-1 overflow-x-auto whitespace-pre-wrap break-all">{safeStringify(item.value)}</pre>
          </div>
        ))}
      </div>
    </AssociationGroup>
  );
}

function AssociationGroup({ title, children }: { title: string; children: ReactNode }) {
  return <div className="py-3 first:pt-0 last:pb-0"><div className="ldvh-caption-strong mb-2">{title}</div>{children}</div>;
}

function getCurrentProjectId(obj: Record<string, unknown>): string | undefined {
  const ref = obj.object_ref;
  if (!ref || typeof ref !== 'object' || Array.isArray(ref)) return undefined;
  const projectId = (ref as Record<string, unknown>).governed_project_id;
  return typeof projectId === 'string' ? projectId : undefined;
}

function safeStringify(value: unknown): string {
  try { return JSON.stringify(value, null, 2); } catch { return String(value); }
}
