import { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import StatusBadge from '@/components/StatusBadge';
import { formatDateTime } from '@/utils/dateFormat';
import { getObjectStatusLocale } from '@/i18n/locales';
import { FactAssociationsSection } from '@/pages/object-detail/FactAssociationsSection';
import { sortRelatedContentEntries, type RelatedContentEntry } from '@/pages/object-detail/model';
import {
  DetailInlineField,
  DetailObjectRow,
  ReadingNodeSection,
  RelatedContentSection,
  StudyTextNodeContent,
  getFieldLabel,
  getReadingNodeNextState,
  hasDetailContent,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';

const ADR_READING_NODES: Array<{ field: string; kind?: 'date' }> = [
  { field: 'decision_question' },
  { field: 'decision' },
  { field: 'applicability' },
  { field: 'rationale' },
  { field: 'consequences' },
  { field: 'decided_at', kind: 'date' },
  { field: 'disposition_summary' },
];

export function AdrReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {ADR_READING_NODES.map((node) => (
        <AdrReadingNode
          key={node.field}
          title={getFieldLabel(node.field, locale)}
          value={obj[node.field]}
          locale={locale}
          kind={node.kind}
        />
      ))}
      <FactAssociationsSection obj={obj} locale={locale} />
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
}

function AdrReadingNode({
  title,
  value,
  locale,
  kind,
}: {
  title: string;
  value: unknown;
  locale: string;
  kind?: 'date';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (!hasDetailContent(value)) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {kind === 'date' ? (
        <span className="ldvh-definition-text">{formatDateTime(String(value))}</span>
      ) : (
        <StudyTextNodeContent value={value} />
      )}
    </ReadingNodeSection>
  );
}

const PITFALL_READING_NODES: Array<{ field: string }> = [
  { field: 'symptoms' },
  { field: 'trigger_conditions' },
  { field: 'applicability' },
  { field: 'validation_summary' },
  { field: 'root_cause' },
  { field: 'resolution' },
  { field: 'avoidance' },
  { field: 'disposition_summary' },
];

export function PitfallReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {PITFALL_READING_NODES.map((node) => (
        <PitfallReadingNode
          key={node.field}
          title={getFieldLabel(node.field, locale)}
          value={obj[node.field]}
          locale={locale}
        />
      ))}
      <FactAssociationsSection obj={obj} locale={locale} />
      <RelatedContentSection entries={sortRelatedContentEntries(relatedEntries)} locale={locale} />
    </div>
  );
}

function PitfallReadingNode({
  title,
  value,
  locale,
}: {
  title: string;
  value: unknown;
  locale: string;
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  if (!hasDetailContent(value)) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <PitfallTextNodeContent value={value} />
    </ReadingNodeSection>
  );
}

export function PitfallTextNodeContent({ value }: { value: unknown }) {
  return (
    <div className="ldvh-study-node-content">
      <div className="ldvh-inline-markdown max-w-none">
        <Markdown remarkPlugins={[remarkGfm]}>{String(value)}</Markdown>
      </div>
    </div>
  );
}

const SPARK_READING_NODES: Array<{
  field: string;
  zh: string;
  en: string;
  kind: 'intent' | 'summary' | 'evolution' | 'routing';
}> = [
  { field: 'intent', zh: '意图', en: 'Intent', kind: 'intent' },
  { field: 'summary', zh: '摘要', en: 'Current Summary', kind: 'summary' },
  { field: 'evolution', zh: '演变', en: 'Evolution', kind: 'evolution' },
  { field: 'routing', zh: '分流', en: 'Routing', kind: 'routing' },
];
type SparkEvolutionEntry = { key: string; at?: string; summary: string };

export function SparkReadingLayout({
  obj,
  relatedEntries,
  locale,
}: {
  obj: Record<string, unknown>;
  relatedEntries: RelatedContentEntry[];
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {SPARK_READING_NODES.map((node) => (
        <SparkReadingNode
          key={node.field}
          title={locale === 'en' ? node.en : node.zh}
          obj={obj}
          locale={locale}
          kind={node.kind}
        />
      ))}
      <FactAssociationsSection
        obj={obj}
        locale={locale}
        title={locale === 'en' ? 'Related' : '关联'}
        variant="spark"
      />
      <RelatedContentSection entries={relatedEntries} locale={locale} />
    </div>
  );
}

function SparkReadingNode({
  title,
  obj,
  locale,
  kind,
}: {
  title: string;
  obj: Record<string, unknown>;
  locale: string;
  kind: 'intent' | 'summary' | 'evolution' | 'routing';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const hasContent = kind === 'intent'
    ? hasDetailContent(obj.intent)
    : kind === 'summary'
    ? hasDetailContent(obj.summary)
    : kind === 'evolution'
      ? hasDetailContent(obj.evolution)
      : hasSparkRoutingContent(obj);

  if (!hasContent) return null;

  return (
    <ReadingNodeSection
      title={title}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      {kind === 'intent' && <StudyTextNodeContent value={obj.intent} className="ldvh-spark-reading-prose" />}
      {kind === 'summary' && <SparkSummaryNode value={obj.summary} />}
      {kind === 'evolution' && <SparkEvolutionNode value={obj.evolution} locale={locale} />}
      {kind === 'routing' && <SparkRoutingNode obj={obj} locale={locale} />}
    </ReadingNodeSection>
  );
}

function SparkSummaryNode({ value }: { value: unknown }) {
  return (
    <StudyTextNodeContent
      value={value}
      className="ldvh-spark-reading-prose"
    />
  );
}

function SparkEvolutionNode({ value, locale }: { value: unknown; locale: string }) {
  if (!Array.isArray(value)) return <StudyTextNodeContent value={value} />;
  const entries = value
    .map((item, index) => parseSparkEvolutionEntry(item, index))
    .filter((entry): entry is SparkEvolutionEntry => Boolean(entry))
    .reverse();

  if (entries.length === 0) return null;

  return (
    <div className="flex min-w-0 flex-col gap-2">
      {entries.map((entry) => (
        <div key={entry.key} className="min-w-0 rounded-md border border-ldvh-border/45 bg-ldvh-bg/45 px-3 py-2">
          <div className="mb-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" aria-hidden="true" />
            <SparkEvolutionTime value={entry.at} locale={locale} />
          </div>
          <StudyTextNodeContent value={entry.summary} compact />
        </div>
      ))}
    </div>
  );
}

function parseSparkEvolutionEntry(item: unknown, index: number): SparkEvolutionEntry | null {
  if (typeof item === 'string' && item.trim().length > 0) {
    return { key: `${index}-${item}`, summary: item };
  }
  if (!item || typeof item !== 'object') return null;
  const record = item as Record<string, unknown>;
  const summary = typeof record.summary === 'string' ? record.summary.trim() : '';
  if (!summary) return null;
  return {
    key: `${index}-${String(record.at ?? summary)}`,
    at: typeof record.at === 'string' ? record.at : undefined,
    summary,
  };
}

function SparkEvolutionTime({ value, locale }: { value?: string; locale: string }) {
  if (!value) {
    return (
      <div className="ldvh-caption-strong min-w-0 break-words text-ldvh-text-secondary">
        {getFieldLabel('evolution', locale)}
      </div>
    );
  }
  const [date, time] = formatDateTime(value).split(' ');
  return (
    <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5 font-mono tabular-nums">
      <span className="ldvh-caption-strong min-w-0 break-words text-ldvh-text-secondary">{date}</span>
      {time && <span className="ldvh-meta-muted min-w-0 break-words leading-4">{time}</span>}
    </div>
  );
}

function SparkRoutingNode({ obj, locale }: { obj: Record<string, unknown>; locale: string }) {
  const status = String(obj.status ?? 'open');
  const statusLabel = getObjectStatusLocale('spark', status, locale);
  const routedTargets = getSparkRoutedReferences(obj.relations);
  const closedAt = typeof obj.closed_at === 'string' && obj.closed_at.trim().length > 0 ? obj.closed_at : null;
  const disposition = typeof obj.disposition_summary === 'string' && obj.disposition_summary.trim().length > 0
    ? obj.disposition_summary
    : null;

  return (
    <div className="flex flex-col divide-y divide-ldvh-border/60">
      <DetailInlineField
        label={getFieldLabel('status', locale)}
        value={<StatusBadge status={status} statusLabel={statusLabel} objectType="spark" size="sm" />}
      />
      {routedTargets.map((target) => (
        <DetailObjectRow
          key={`${target.objectType}:${target.ref}`}
          label={getFieldLabel('resolved_to', locale)}
          fallbackId={target.ref}
          objectType={target.objectType}
          locale={locale}
          variant="property"
        />
      ))}
      {closedAt && (
        <DetailInlineField
          label={getFieldLabel('closed_at', locale)}
          value={<span className="ldvh-definition-text">{formatDateTime(closedAt)}</span>}
        />
      )}
      {disposition && (
        <DetailInlineField
          label={getFieldLabel('disposition_summary', locale)}
          value={<StudyTextNodeContent value={disposition} />}
        />
      )}
    </div>
  );
}

function hasSparkRoutingContent(obj: Record<string, unknown>) {
  const status = String(obj.status ?? 'open');
  return status === 'routed'
    || status === 'discarded'
    || getSparkRoutedReferences(obj.relations).length > 0
    || hasDetailContent(obj.closed_at)
    || hasDetailContent(obj.disposition_summary);
}

function getSparkRoutedReferences(value: unknown): Array<{ ref: string; objectType: string }> {
  if (!Array.isArray(value)) return [];
  return value.flatMap((relation) => {
    if (!relation || typeof relation !== 'object') return [];
    const record = relation as Record<string, unknown>;
    if (record.relation_key !== 'routed-to' || !record.target || typeof record.target !== 'object') return [];
    const target = record.target as Record<string, unknown>;
    if (typeof target.object_id !== 'string' || typeof target.fact_type_key !== 'string') return [];
    return [{ ref: target.object_id, objectType: target.fact_type_key }];
  });
}
