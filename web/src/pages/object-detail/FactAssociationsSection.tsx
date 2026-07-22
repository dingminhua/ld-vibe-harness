import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { AlertTriangle, ChevronLeft, ChevronRight, ExternalLink, FileText, Link2 } from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getLocalizedObjectTitle, getTypeLabel } from '@/i18n/locales';
import {
  DetailObjectRow,
  ReadingNodeSection,
  getReadingNodeNextState,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';
import {
  projectFactReadingAssociations,
  type ReadingMaterial,
  type ReadingRelation,
  type UnresolvedAssociation,
} from '@/pages/object-detail/factReadingProjection';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';
import { fetchObjectDetail } from '@/utils/api';

export function FactAssociationsSection({
  obj,
  locale,
  title,
  variant = 'detailed',
}: {
  obj: Record<string, unknown>;
  locale: string;
  title?: string;
  variant?: 'detailed' | 'spark';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const associations = projectFactReadingAssociations(obj);
  const sparkProjection = variant === 'spark' ? projectSparkAssociations(associations) : null;
  const hasContent = sparkProjection
    ? sparkProjection.relationGroups.length > 0
      || sparkProjection.documents.length > 0
      || associations.unresolved.length > 0
    : associations.relations.length > 0
    || associations.projectMaterials.length > 0
    || associations.externalInputs.length > 0
    || associations.evidenceMaterials.length > 0
    || associations.unresolved.length > 0;

  if (!hasContent) return null;

  const currentProjectId = getCurrentProjectId(obj);
  return (
    <ReadingNodeSection
      title={title ?? getFieldLabel('associated_materials', locale)}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="divide-y divide-ldvh-border/60">
        {sparkProjection ? (
          <>
            {sparkProjection.relationGroups.map((group) => (
              <SparkRelationGroup
                key={group.key}
                group={group}
                currentProjectId={currentProjectId}
                locale={locale}
              />
            ))}
            <MaterialGroup
              fieldKey="associated_documents"
              materials={sparkProjection.documents}
              locale={locale}
              simple
            />
          </>
        ) : (
          <>
            <RelationGroup relations={associations.relations} currentProjectId={currentProjectId} locale={locale} />
            <MaterialGroup fieldKey="project_materials" materials={associations.projectMaterials} locale={locale} />
            <MaterialGroup fieldKey="external_inputs" materials={associations.externalInputs} locale={locale} />
            <MaterialGroup fieldKey="evidence_materials" materials={associations.evidenceMaterials} locale={locale} />
          </>
        )}
        <UnresolvedGroup items={associations.unresolved} locale={locale} />
      </div>
    </ReadingNodeSection>
  );
}

type SparkRelationGroupView = {
  key: string;
  label: string;
  relations: ReadingRelation[];
};

function projectSparkAssociations(associations: ReturnType<typeof projectFactReadingAssociations>) {
  const relationGroups = new Map<string, SparkRelationGroupView>();
  associations.relations
    .filter((relation) => relation.relationKey !== 'routed-to')
    .forEach((relation) => {
      const key = relation.relationKey === 'related-to'
        ? `type:${relation.target.factTypeKey}`
        : `relation:${relation.relationKey}`;
      const current = relationGroups.get(key) ?? {
        key,
        label: relation.relationKey === 'related-to'
          ? relation.target.factTypeKey
          : `relation_${relation.relationKey.replace(/-/g, '_')}`,
        relations: [],
      };
      current.relations.push(relation);
      relationGroups.set(key, current);
    });

  const relationMaterials = associations.relations.flatMap((relation) => [
    ...relation.sourceRefs,
    ...relation.target.governanceRefs,
  ]);
  const materials = [
    ...associations.projectMaterials,
    ...relationMaterials.filter((material) => material.category === 'project'),
  ];

  return {
    relationGroups: [...relationGroups.values()],
    documents: dedupeMaterials(materials.filter((material) => material.category === 'project')),
  };
}

function SparkRelationGroup({
  group,
  currentProjectId,
  locale,
}: {
  group: SparkRelationGroupView;
  currentProjectId?: string;
  locale: string;
}) {
  const label = group.key.startsWith('type:')
    ? getTypeLabel(group.label, locale)
    : getFieldLabel(group.label, locale);
  return (
    <AssociationGroup title={label}>
      <div className="flex flex-col gap-1.5">
        {group.relations.map((relation) => (
          <SparkRelationTarget
            key={relation.originPath}
            relation={relation}
            currentProjectId={currentProjectId}
            locale={locale}
          />
        ))}
      </div>
    </AssociationGroup>
  );
}

function SparkRelationTarget({
  relation,
  currentProjectId,
  locale,
}: {
  relation: ReadingRelation;
  currentProjectId?: string;
  locale: string;
}) {
  const { isOpen, content, openPanel } = usePanel();
  const [objectInfo, setObjectInfo] = useState<{ title: string; path?: string } | null>(null);
  const target = relation.target;
  const isLocal = Boolean(currentProjectId && target.governedProjectId === currentProjectId);
  const title = objectInfo?.title ?? target.objectId;
  const isCurrentPanelOpen = Boolean(
    isOpen
    && content?.type === 'object'
    && content.objectType === target.factTypeKey
    && content.objectId === target.objectId,
  );
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const color = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;

  useEffect(() => {
    if (!isLocal) {
      setObjectInfo(null);
      return;
    }
    let cancelled = false;
    fetchObjectDetail(target.factTypeKey, target.objectId)
      .then((detail) => {
        if (cancelled) return;
        setObjectInfo({
          title: getLocalizedObjectTitle(detail.data, locale, target.objectId),
          path: typeof detail.data.absolute_path === 'string'
            ? detail.data.absolute_path
            : typeof detail.data.canonical_path === 'string'
              ? detail.data.canonical_path
              : undefined,
        });
      })
      .catch(() => {
        if (!cancelled) setObjectInfo(null);
      });
    return () => {
      cancelled = true;
    };
  }, [isLocal, locale, target.factTypeKey, target.objectId]);

  const open = () => {
    if (!isLocal) return;
    openPanel({
      type: 'object',
      title,
      objectType: target.factTypeKey,
      objectId: target.objectId,
    });
  };
  const copyValue = objectInfo?.path
    ?? `${target.governedProjectId}:${target.factTypeKey}:${target.objectId}`;

  return (
    <div
      role={isLocal ? 'button' : undefined}
      tabIndex={isLocal ? 0 : undefined}
      onClick={open}
      onKeyDown={(event) => {
        if (!isLocal || (event.key !== 'Enter' && event.key !== ' ')) return;
        event.preventDefault();
        open();
      }}
      className={`ldvh-body group flex min-h-10 w-full min-w-0 items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors ${
        isLocal ? 'cursor-pointer hover:bg-ldvh-border/25' : ''
      }`}
    >
      <ObjectTypeIcon type={target.factTypeKey} size={13} className="shrink-0" style={{ color }} />
      <div className="min-w-0 flex-1">
        <div className="ldvh-meta-primary truncate transition-colors group-hover:text-ldvh-accent">{title}</div>
      </div>
      {!isLocal && <span className="ldvh-meta-muted shrink-0">{target.governedProjectId}</span>}
      <CopyPathButton path={copyValue} />
      {isLocal && <PanelIcon size={16} className="shrink-0 text-ldvh-text-secondary group-hover:text-ldvh-accent" />}
    </div>
  );
}

function RelationGroup({
  relations,
  currentProjectId,
  locale,
}: {
  relations: ReadingRelation[];
  currentProjectId?: string;
  locale: string;
}) {
  if (relations.length === 0) return null;
  const grouped = groupRelations(relations);

  return (
    <AssociationGroup title={getFieldLabel('fact_relations', locale)}>
      <div className="flex flex-col gap-4">
        {[...grouped.entries()].map(([relationKey, items]) => (
          <div key={relationKey} className="min-w-0">
            <div className="ldvh-caption-strong mb-1.5 text-ldvh-text-secondary">
              {getFieldLabel(`relation_${relationKey.replace(/-/g, '_')}`, locale)}
            </div>
            <div className="divide-y divide-ldvh-border/45">
              {items.map((relation) => (
                <div key={relation.originPath} className="py-1 first:pt-0 last:pb-0">
                  <RelationTarget
                    relation={relation}
                    currentProjectId={currentProjectId}
                    locale={locale}
                  />
                  {(relation.sourceRefs.length > 0 || relation.target.governanceRefs.length > 0) && (
                    <div className="ml-4 border-l border-ldvh-border/60 pl-3">
                      {[...relation.sourceRefs, ...relation.target.governanceRefs].map((material) => (
                        <MaterialReferenceRow key={material.originPath} material={material} compact />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </AssociationGroup>
  );
}

function RelationTarget({
  relation,
  currentProjectId,
  locale,
}: {
  relation: ReadingRelation;
  currentProjectId?: string;
  locale: string;
}) {
  const target = relation.target;
  const relationLabel = getFieldLabel(`relation_${relation.relationKey.replace(/-/g, '_')}`, locale);
  if (currentProjectId && target.governedProjectId === currentProjectId) {
    return (
      <DetailObjectRow
        label={relationLabel}
        fallbackId={target.objectId}
        objectType={target.factTypeKey}
        locale={locale}
        compact
      />
    );
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

function MaterialGroup({
  fieldKey,
  materials,
  locale,
  simple = false,
}: {
  fieldKey: string;
  materials: ReadingMaterial[];
  locale: string;
  simple?: boolean;
}) {
  if (materials.length === 0) return null;
  return (
    <AssociationGroup title={getFieldLabel(fieldKey, locale)}>
      <div className={simple ? 'flex flex-col gap-1.5' : 'divide-y divide-ldvh-border/45'}>
        {materials.map((material) => (
          <MaterialReferenceRow key={material.originPath} material={material} simple={simple} />
        ))}
      </div>
    </AssociationGroup>
  );
}

function MaterialReferenceRow({
  material,
  compact = false,
  simple = false,
}: {
  material: ReadingMaterial;
  compact?: boolean;
  simple?: boolean;
}) {
  const { t } = useI18n();
  const { isOpen, content, openPanel } = usePanel();
  const isWeb = /^https?:\/\//i.test(material.locator);
  const isProjectPath = material.category === 'project' && material.kind !== 'git-revision';
  const title = simple ? material.locator : getMaterialTitle(material);
  const isCurrentPanelOpen = Boolean(
    isOpen && (
      (isWeb && content?.type === 'web' && content.url === material.locator)
      || (isProjectPath && content?.type === 'doc' && content.docPath === material.locator)
      || (!isWeb && !isProjectPath && content?.type === 'doc' && content.title === title)
    ),
  );
  const PanelIcon = isCurrentPanelOpen ? ChevronLeft : ChevronRight;
  const MaterialIcon = isWeb
    ? ExternalLink
    : material.role === 'relation-source' || material.role === 'governance'
      ? Link2
      : FileText;

  const open = () => {
    if (isWeb) {
      openPanel({ type: 'web', title, url: material.locator });
    } else if (isProjectPath) {
      openPanel({ type: 'doc', title, docPath: material.locator });
    } else {
      openPanel({ type: 'doc', title, data: material.locator });
    }
  };
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    open();
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={onKeyDown}
      className={`group flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-1.5 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50 ${compact ? 'py-1.5' : simple ? 'min-h-10 py-2' : 'py-2'}`}
    >
      <MaterialIcon size={13} className="shrink-0 text-ldvh-accent" />
      <div className="min-w-0 flex-1">
        <div className="ldvh-meta-primary break-all">{title}</div>
        {!simple && (
          <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1">
            <span className="ldvh-meta-muted">{material.kind}</span>
            {material.version && <span className="ldvh-meta-muted break-all">{material.version}</span>}
            {material.observedAt && <span className="ldvh-meta-muted">{formatDateTime(material.observedAt)}</span>}
          </div>
        )}
      </div>
      <CopyPathButton
        path={material.locator}
        label={isWeb ? t('common.copyUrl') : t('common.copyReference')}
        copiedLabel={isWeb ? t('common.copiedUrl') : t('common.copiedReference')}
      />
      <PanelIcon size={16} className="shrink-0 text-ldvh-text-secondary group-hover:text-ldvh-accent" />
    </div>
  );
}

function UnresolvedGroup({ items, locale }: { items: UnresolvedAssociation[]; locale: string }) {
  if (items.length === 0) return null;
  return (
    <AssociationGroup title={getFieldLabel('unresolved_materials', locale)}>
      <div className="flex flex-col gap-2">
        {items.map((item) => (
          <div key={`${item.originPath}:${item.role}`} className="rounded-md border border-amber-500/25 bg-amber-500/5 px-3 py-2">
            <div className="flex items-center gap-2">
              <AlertTriangle size={13} className="shrink-0 text-amber-400" />
              <span className="ldvh-caption-strong">{item.originPath}</span>
            </div>
            <pre className="ldvh-meta-muted mt-1 overflow-x-auto whitespace-pre-wrap break-all">{safeStringify(item.value)}</pre>
          </div>
        ))}
      </div>
    </AssociationGroup>
  );
}

function AssociationGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-2">{title}</div>
      {children}
    </div>
  );
}

function groupRelations(relations: ReadingRelation[]): Map<string, ReadingRelation[]> {
  const grouped = new Map<string, ReadingRelation[]>();
  relations.forEach((relation) => {
    const items = grouped.get(relation.relationKey) ?? [];
    items.push(relation);
    grouped.set(relation.relationKey, items);
  });
  return grouped;
}

function getCurrentProjectId(obj: Record<string, unknown>): string | undefined {
  const objectRef = obj.object_ref;
  if (!objectRef || typeof objectRef !== 'object' || Array.isArray(objectRef)) return undefined;
  const projectId = (objectRef as Record<string, unknown>).governed_project_id;
  return typeof projectId === 'string' ? projectId : undefined;
}

function getMaterialTitle(material: ReadingMaterial): string {
  if (/^https?:\/\//i.test(material.locator)) {
    try {
      const url = new URL(material.locator);
      return `${url.hostname}${url.pathname === '/' ? '' : url.pathname}`;
    } catch {
      return material.locator;
    }
  }
  if (material.kind === 'human-input') return material.locator;
  return material.locator.split('/').filter(Boolean).pop() || material.locator;
}

function dedupeMaterials(materials: ReadingMaterial[]): ReadingMaterial[] {
  const seen = new Set<string>();
  return materials.filter((material) => {
    const key = `${material.kind}:${material.locator}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function safeStringify(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}
