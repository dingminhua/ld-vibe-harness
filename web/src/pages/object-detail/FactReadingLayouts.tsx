import { useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatDateTime } from '@/utils/dateFormat';
import { FactAssociationsSection } from '@/pages/object-detail/FactAssociationsSection';
import { sortRelatedContentEntries, type RelatedContentEntry } from '@/pages/object-detail/model';
import {
  ReadingNodeSection,
  RelatedContentSection,
  StudyTextNodeContent,
  getFieldLabel,
  getReadingNodeNextState,
  hasDetailContent,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';

const ADR_READING_NODES: Array<{ field: string; zh: string; en: string; kind?: 'date' }> = [
  { field: 'decision_question', zh: '问题', en: 'Question' },
  { field: 'decision', zh: '决策', en: 'Decision' },
  { field: 'applicability', zh: '范围', en: 'Scope' },
  { field: 'rationale', zh: '理由', en: 'Rationale' },
  { field: 'consequences', zh: '影响', en: 'Consequences' },
  { field: 'disposition_summary', zh: '处置', en: 'Disposition' },
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
          title={locale === 'en' ? node.en : node.zh}
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

const PITFALL_READING_NODES: Array<{ field: string; zh: string; en: string }> = [
  { field: 'symptoms', zh: '现象', en: 'Symptoms' },
  { field: 'trigger_conditions', zh: '触发', en: 'Triggers' },
  { field: 'applicability', zh: '范围', en: 'Scope' },
  { field: 'validation_summary', zh: '验证', en: 'Validation' },
  { field: 'root_cause', zh: '根因', en: 'Root Cause' },
  { field: 'resolution', zh: '方案', en: 'Resolution' },
  { field: 'avoidance', zh: '规避', en: 'Avoidance' },
  { field: 'disposition_summary', zh: '处置', en: 'Disposition' },
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
          title={locale === 'en' ? node.en : node.zh}
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
  kind: 'intent' | 'summary' | 'evolution' | 'terminal';
}> = [
  { field: 'intent', zh: '意图', en: 'Intent', kind: 'intent' },
  { field: 'summary', zh: '摘要', en: 'Current Summary', kind: 'summary' },
  { field: 'evolution', zh: '演变', en: 'Evolution', kind: 'evolution' },
  { field: 'terminal', zh: '分流', en: 'Routing', kind: 'terminal' },
];
type SparkEvolutionEntry = { key: string; at?: string; summary: string };

export function SparkReadingLayout({
  obj,
  locale,
}: {
  obj: Record<string, unknown>;
  locale: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-5">
      {SPARK_READING_NODES.map((node) => (
        <SparkReadingNode
          key={node.field}
          title={getSparkReadingNodeTitle(node, obj, locale)}
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
    </div>
  );
}

function getSparkReadingNodeTitle(
  node: (typeof SPARK_READING_NODES)[number],
  obj: Record<string, unknown>,
  locale: string,
) {
  if (node.kind === 'terminal') {
    if (obj.status === 'implemented') return locale === 'en' ? 'Implemented' : '落实';
    if (obj.status === 'discarded') return locale === 'en' ? 'Discarded' : '废弃';
  }
  return locale === 'en' ? node.en : node.zh;
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
  kind: 'intent' | 'summary' | 'evolution' | 'terminal';
}) {
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const hasContent = kind === 'intent'
    ? hasDetailContent(obj.intent)
    : kind === 'summary'
    ? hasDetailContent(obj.summary)
    : kind === 'evolution'
      ? hasDetailContent(obj.evolution)
      : hasSparkTerminalContent(obj);

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
      {kind === 'terminal' && <SparkTerminalNode obj={obj} />}
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

function SparkTerminalNode({ obj }: { obj: Record<string, unknown> }) {
  const closedAt = typeof obj.closed_at === 'string' && obj.closed_at.trim().length > 0 ? obj.closed_at : null;
  const disposition = typeof obj.disposition_summary === 'string' && obj.disposition_summary.trim().length > 0
    ? obj.disposition_summary
    : null;

  return (
    <div className="min-w-0 rounded-md border border-ldvh-border/45 bg-ldvh-bg/45 px-3 py-2">
      {closedAt && (
        <div className="mb-1.5 flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-accent" aria-hidden="true" />
          <SparkTerminalTime value={closedAt} />
        </div>
      )}
      {disposition && <StudyTextNodeContent value={disposition} compact />}
    </div>
  );
}

function SparkTerminalTime({ value }: { value: string }) {
  const [date, time] = formatDateTime(value).split(' ');
  return (
    <div className="flex min-w-0 flex-wrap items-baseline gap-x-2 gap-y-0.5 font-mono tabular-nums">
      <span className="ldvh-caption-strong min-w-0 break-words text-ldvh-text-secondary">{date}</span>
      {time && <span className="ldvh-meta-muted min-w-0 break-words leading-4">{time}</span>}
    </div>
  );
}

function hasSparkTerminalContent(obj: Record<string, unknown>) {
  const status = String(obj.status ?? 'open');
  return status === 'routed'
    || status === 'implemented'
    || status === 'discarded'
    || hasDetailContent(obj.closed_at)
    || hasDetailContent(obj.disposition_summary);
}
