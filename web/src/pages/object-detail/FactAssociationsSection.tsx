import { useState, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { getFieldLabel } from '@/i18n/locales';
import {
  DetailObjectRow,
  ReadingNodeSection,
  getReadingNodeNextState,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';
import {
  projectFactReadingAssociations,
  type ReadingRelation,
  type UnresolvedAssociation,
} from '@/pages/object-detail/factReadingProjection';
import { CATEGORY_COLORS } from '@/utils/categoryColors';

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
      title={title ?? getFieldLabel('associated_materials', locale)}
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
  const grouped = new Map<string, ReadingRelation[]>();
  for (const relation of relations) {
    grouped.set(relation.relationKey, [...(grouped.get(relation.relationKey) ?? []), relation]);
  }
  return (
    <AssociationGroup title={getFieldLabel('fact_relations', locale)}>
      <div className="flex flex-col gap-4">
        {[...grouped.entries()].map(([relationKey, items]) => (
          <div key={relationKey} className="min-w-0">
            <div className="ldvh-caption-strong mb-1.5 text-ldvh-text-secondary">
              {getFieldLabel(`relation_${relationKey.replace(/-/g, '_')}`, locale)}
            </div>
            <div className="divide-y divide-ldvh-border/45">
              {items.map((relation) => <RelationTarget key={relation.originPath} relation={relation} currentProjectId={currentProjectId} locale={locale} />)}
            </div>
          </div>
        ))}
      </div>
    </AssociationGroup>
  );
}

function RelationTarget({ relation, currentProjectId, locale }: {
  relation: ReadingRelation;
  currentProjectId?: string;
  locale: string;
}) {
  const target = relation.target;
  const relationLabel = getFieldLabel(`relation_${relation.relationKey.replace(/-/g, '_')}`, locale);
  if (currentProjectId && target.governedProjectId === currentProjectId) {
    return <DetailObjectRow label={relationLabel} fallbackId={target.objectId} objectType={target.factTypeKey} locale={locale} compact />;
  }
  const color = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;
  return (
    <div className="grid min-w-0 items-center gap-2 py-2 sm:grid-cols-[5.625rem_1fr]">
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{relationLabel}</div>
      <div className="flex min-w-0 items-center gap-2 rounded-md px-2 py-1.5">
        <ObjectTypeIcon type={target.factTypeKey} size={12} className="shrink-0" style={{ color }} />
        <span className="ldvh-body min-w-0 flex-1 truncate">{target.objectId}</span>
        <span className="ldvh-meta-muted shrink-0">{target.governedProjectId}</span>
        <CopyPathButton path={`${target.governedProjectId}:${target.factTypeKey}:${target.objectId}`} />
      </div>
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
