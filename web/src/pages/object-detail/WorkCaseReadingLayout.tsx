import { useState, type ReactNode } from 'react';
import ChecklistCard from '@/components/ChecklistCard';
import EvidenceBlock from '@/components/EvidenceBlock';
import SummaryText from '@/components/SummaryText';
import { ExecutionFlowBar, ExecutionFlowMarker } from '@/components/ExecutionFlowStatus';
import { useI18n } from '@/i18n/context';
import type { LocaleKey } from '@/i18n/locales';
import { formatDateTime } from '@/utils/dateFormat';
import { executionFlowRowClass, getExecutionFlowLabel, getExecutionFlowTone, sortWorkCaseExecutionItems } from '@/utils/executionFlowStatus';
import { getWorkCaseDisplayStatus, isWorkCaseResultReviewStatus } from '@/shared/workcaseStatus';
import type { ObjectItem, RelatedObjectSummary } from '@/utils/api';
import { META_KEYS, sortRelatedContentEntries, type RelatedContentEntry } from '@/pages/object-detail/model';
import { FactAssociationsSection } from '@/pages/object-detail/FactAssociationsSection';
import {
  ContentField,
  DetailSection,
  EmptyHint,
  LoadingHint,
  ReadingNodeSection,
  RelatedContentSection,
  StringList,
  getFieldLabel,
  getLocalizedTitle,
  getReadingNodeNextState,
  hasDetailContent,
  type ReadingNodeState,
} from '@/pages/ObjectDetail';

interface ParsedChecklistItem {
  checked: boolean;
  text: string;
}

function parseDetailChecklist(value: unknown): ParsedChecklistItem[] {
  if (typeof value !== 'string') return [];
  return value
    .split('\n')
    .map((line) => line.match(/^\s*- \[([ xX])\]\s*(.*)/))
    .filter((match): match is RegExpMatchArray => Boolean(match))
    .map((match) => ({ checked: match[1].toLowerCase() === 'x', text: match[2].trim() }));
}

function getChecklistProgress(value: unknown) {
  const items = parseDetailChecklist(value);
  const done = items.filter((item) => item.checked).length;
  return {
    items,
    done,
    total: items.length,
    complete: items.length > 0 && done === items.length,
  };
}

function getWorkCaseChecklistValue(obj: Record<string, unknown>): string {
  if (typeof obj.success_criteria === 'string') return obj.success_criteria;
  const definitions = Array.isArray(obj.success_criterion_definitions)
    ? obj.success_criterion_definitions.filter(isDetailRecord)
    : [];
  const outcomes = new Map(
    (Array.isArray(obj.success_criterion_results) ? obj.success_criterion_results : [])
      .filter(isDetailRecord)
      .map((item) => [detailString(item.criterion_id), detailString(item.outcome)]),
  );
  return definitions
    .map((item) => {
      const criterionId = detailString(item.criterion_id);
      const statement = detailString(item.statement, criterionId);
      return `- [${outcomes.get(criterionId) === 'satisfied' ? 'x' : ' '}] ${statement}`;
    })
    .join('\n');
}

function getWorkCaseChecklistProgress(obj: Record<string, unknown>) {
  return getChecklistProgress(getWorkCaseChecklistValue(obj));
}

function isExecutionItemDone(status: string): boolean {
  return status === 'done' || status === 'completed';
}

export function WorkCaseReadingLayout({
  obj,
  summary,
  loading,
  locale,
  getStatus,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  loading: boolean;
  locale: string;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const ownExecutionItems = getWorkCaseExecutionItems(obj);
  const executionItems = sortWorkCaseExecutionItems(
    ownExecutionItems.length > 0 ? ownExecutionItems : (summary?.executionItems ?? [])
  );
  const isExecutionLoading = loading && ownExecutionItems.length === 0;
  const relatedDocs = ((obj.aggregated_related_docs as string[] | undefined) ?? (obj.related_docs as string[] | undefined)) || [];
  const relatedAdrs = ((obj.aggregated_related_adrs as string[] | undefined) ?? (obj.related_adrs as string[] | undefined)) || [];
  const relatedSparks = ((obj.aggregated_related_sparks as string[] | undefined) ?? (obj.related_sparks as string[] | undefined)) || [];
  const relatedPitfalls = ((obj.aggregated_related_pitfalls as string[] | undefined) ?? (obj.related_pitfalls as string[] | undefined)) || [];
  const hidden = new Set([
    ...META_KEYS,
    'goal',
    'summary',
    'scope',
    'phase',
    'priority',
    'description',
    'success_criteria',
    'success_criterion_definitions',
    'success_criterion_results',
    'source',
    'source_refs',
    'evidence_refs',
    'relations',
    'orchestration',
    'work_items',
    'verification_evidence',
    'closure_evidence',
    'plan_confirmed_at',
    'closure_requested_at',
    'review_requested_at',
    'closed_at',
    'closure_outcome',
    'residual_risks',
    'followup_refs',
    'revision_history',
    'related_docs',
    'related_adrs',
    'related_sparks',
    'related_pitfalls',
    'related_workcases',
    'aggregated_execution_refs',
    'aggregated_related_docs',
    'aggregated_related_adrs',
    'aggregated_related_sparks',
    'aggregated_related_pitfalls',
  ]);
  const otherEntries = Object.entries(obj).filter(([key, value]) => !hidden.has(key) && hasDetailContent(value));

  return (
    <div className="mb-6 flex flex-col gap-5">
      <WorkCaseHumanOverviewSection
        obj={obj}
        summary={summary}
        executionItems={executionItems}
        locale={locale}
      />

      <WorkCaseLifecycleSection
        obj={obj}
        summary={summary}
        executionItems={executionItems}
        getStatus={getStatus}
      />

      <WorkCaseEvidenceSummarySection obj={obj} summary={summary} />

      <DetailSection title={t('objectDetail.workcaseExecution')} tone="default">
        {isExecutionLoading ? (
          <LoadingHint text={t('objectDetail.executionItemsLoading')} />
        ) : executionItems.length > 0 ? (
          <div className="flex min-w-0 flex-col gap-3">
            <ExecutionFlowBar items={executionItems} t={t} getStatus={getStatus} />
            <div className="divide-y divide-ldvh-border/60 rounded-md border border-ldvh-border bg-ldvh-bg p-2">
              {executionItems.map((item) => (
                <ExecutionItemRow
                  key={item.id}
                  item={item}
                  locale={locale}
                  getStatus={getStatus}
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptyHint text={t('objectList.noExecutionItems')} />
        )}
      </DetailSection>

      <DetailSection title={getFieldLabel('success_criteria', locale)} tone="checklist">
        {hasDetailContent(getWorkCaseChecklistValue(obj)) ? <ChecklistCard value={getWorkCaseChecklistValue(obj)} /> : <EmptyHint text={t('objectDetail.noSuccessCriteria')} />}
      </DetailSection>
      <DetailSection title={getFieldLabel('verification_evidence', locale)} tone="evidence">
        {hasDetailContent(obj.verification_evidence) ? <EvidenceBlock value={String(obj.verification_evidence)} embedded /> : <EmptyHint text={t('objectDetail.noVerificationEvidence')} />}
      </DetailSection>
      <DetailSection title={getFieldLabel('closure_evidence', locale)} tone="evidence">
        {hasDetailContent(obj.closure_evidence) ? <EvidenceBlock value={String(obj.closure_evidence)} embedded /> : <EmptyHint text={t('objectDetail.noClosureEvidenceForWorkCase')} />}
      </DetailSection>

      <WorkCaseAiContextSection obj={obj} locale={locale} />

      <FactAssociationsSection obj={obj} locale={locale} />

      <RelatedContentSection
        entries={sortRelatedContentEntries([
          ['related_workcases', obj.related_workcases],
          ['related_docs', relatedDocs],
          ['related_adrs', relatedAdrs],
          ['related_sparks', relatedSparks],
          ['related_pitfalls', relatedPitfalls],
        ].filter((entry): entry is RelatedContentEntry => Array.isArray(entry[1]) && hasDetailContent(entry[1])))}
        locale={locale}
      />

      {otherEntries.length > 0 && (
        <DetailSection title={t('objectDetail.otherFields')} tone="default">
          <div className="flex flex-col gap-3">
            {otherEntries.map(([key, value]) => (
              <ContentField key={key} fieldKey={key} value={value} locale={locale} objType="workcase" />
            ))}
          </div>
        </DetailSection>
      )}
    </div>
  );
}

type WorkCaseLifecycleTone = 'draft' | 'planReview' | 'planConfirming' | 'active' | 'blocked' | 'verification' | 'resultReview' | 'review' | 'closed';

const workCaseLifecycleClass: Record<WorkCaseLifecycleTone, string> = {
  draft: 'border-sky-500/25 bg-sky-500/10 text-sky-400',
  planReview: 'border-sky-500/25 bg-sky-500/10 text-sky-400',
  planConfirming: 'border-violet-500/25 bg-violet-500/10 text-violet-400',
  active: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400',
  blocked: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
  verification: 'border-blue-500/25 bg-blue-500/10 text-blue-400',
  resultReview: 'border-indigo-500/25 bg-indigo-500/10 text-indigo-400',
  review: 'border-violet-500/25 bg-violet-500/10 text-violet-400',
  closed: 'border-zinc-500/25 bg-zinc-500/10 text-zinc-400',
};

function WorkCaseLifecycleSection({
  obj,
  summary,
  executionItems,
  getStatus,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  executionItems: RelatedObjectSummary[];
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const rawStatus = detailString(obj.status, detailString(summary?.status, 'unknown'));
  const lifecycle = getWorkCaseLifecycle(obj, summary, executionItems);
  const checklistProgress = getWorkCaseChecklistProgress(obj);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const executionTotal = summary?.executionItemTotal ?? executionItems.length;
  const executionDone = summary?.executionItemDone ?? executionItems.filter((item) => isExecutionItemDone(item.status)).length;
  const recordItems = [
    { label: t('objectList.planConfirmedAt'), recorded: Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at)) },
    { label: t('objectList.closureRequestedAt'), recorded: Boolean(summary?.hasClosureRequestedAt ?? (hasDetailContent(obj.closure_requested_at) || hasDetailContent(obj.review_requested_at))) },
    { label: t('objectList.verificationEvidence'), recorded: Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence)) },
    { label: t('objectList.closureEvidence'), recorded: Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence)) },
    ...(rawStatus === 'closed'
      ? [{ label: t('objectList.closedAt'), recorded: Boolean(summary?.hasClosedAt ?? hasDetailContent(obj.closed_at)) }]
      : []),
  ];

  return (
    <DetailSection title={t('objectDetail.workcaseProgress')} tone="default">
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
          <div className="ldvh-caption-strong mb-2 text-ldvh-text-secondary">{t('objectDetail.lifecycleStage')}</div>
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <span className={`ldvh-caption-strong inline-flex rounded-md border px-2 py-1 ${workCaseLifecycleClass[lifecycle.tone]}`}>
              {t(lifecycle.labelKey)}
            </span>
            <span className="ldvh-meta-muted">{getStatus(rawStatus)}</span>
          </div>
        </div>
        <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <ProgressMetric
              label={t('objectDetail.successCriteriaProgress')}
              done={successCriteriaDone}
              total={successCriteriaTotal}
              emptyText={t('objectDetail.noSuccessCriteria')}
            />
            <ProgressMetric
              label={t('objectDetail.executionItemProgress')}
              done={executionDone}
              total={executionTotal}
              emptyText={t('objectList.noExecutionItems')}
            />
          </div>
          {executionItems.length > 0 && (
            <div className="mt-3">
              <ExecutionFlowBar items={executionItems} t={t} getStatus={getStatus} compact />
            </div>
          )}
        </div>
      </div>
      <div className="mt-3 flex min-w-0 flex-wrap gap-2">
        {recordItems.map((item) => (
          <DetailRecordItem key={item.label} label={item.label} recorded={item.recorded} />
        ))}
      </div>
    </DetailSection>
  );
}

function ProgressMetric({
  label,
  done,
  total,
  emptyText,
}: {
  label: string;
  done: number;
  total: number;
  emptyText: string;
}) {
  const ratio = total > 0 ? Math.max(0, Math.min(100, (done / total) * 100)) : 0;
  return (
    <div className="min-w-0">
      <div className="mb-1.5 flex min-w-0 items-center justify-between gap-2">
        <span className="ldvh-caption-strong min-w-0 truncate text-ldvh-text-secondary">{label}</span>
        <span className="ldvh-caption shrink-0 text-ldvh-text-secondary">{total > 0 ? `${done}/${total}` : emptyText}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-ldvh-border/45">
        <div className="h-full rounded-full bg-ldvh-accent" style={{ width: `${ratio}%` }} />
      </div>
    </div>
  );
}

function WorkCaseHumanOverviewSection({
  obj,
  summary,
  executionItems,
  locale,
}: {
  obj: Record<string, unknown>;
  summary: ObjectItem | null;
  executionItems: RelatedObjectSummary[];
  locale: string;
}) {
  const { t } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('expanded');
  const goal = detailString(obj.goal);
  const currentSummary = detailString(obj.summary, detailString(obj.description));
  const priority = detailString(obj.priority) || detailString(summary?.priority);
  const checklistProgress = getWorkCaseChecklistProgress(obj);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const executionTotal = summary?.executionItemTotal ?? executionItems.length;
  const executionDone = summary?.executionItemDone ?? executionItems.filter((item) => isExecutionItemDone(item.status)).length;
  const lifecycle = getWorkCaseLifecycle(obj, summary, executionItems);
  const humanGateLabel = lifecycle.tone === 'planConfirming'
    ? t('objectDetail.humanPlanConfirmation')
    : lifecycle.tone === 'review' || lifecycle.tone === 'closed'
      ? t('objectDetail.humanClosureConfirmation')
      : t('objectDetail.humanGateTip');
  const summaryItems = [
    { label: t('objectDetail.successCriteriaProgress'), value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—' },
    { label: t('objectDetail.executionItemProgress'), value: executionTotal > 0 ? `${executionDone}/${executionTotal}` : '—' },
    { label: t('objectDetail.closeDecisionRecordState'), value: summarizeRecordState(obj, summary, executionItems, t) },
  ];

  return (
    <ReadingNodeSection
      title={t('objectDetail.workcaseHumanOverview')}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="flex flex-col gap-4">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-4">
            <div className="mb-2 flex min-w-0 flex-wrap items-center gap-2">
              <span className="ldvh-caption-strong rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-1 text-emerald-400">
                {t('objectDetail.workcaseHumanContext')}
              </span>
              {priority && <span className="ldvh-chip rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-secondary">{priority}</span>}
              <span className="ldvh-chip rounded-md border border-violet-500/25 bg-violet-500/10 px-2 py-1 text-violet-400">{humanGateLabel}</span>
            </div>
            {hasDetailContent(goal) ? (
              <SummaryText value={goal} collapseThreshold={900} />
            ) : (
              <EmptyHint text={t('objectDetail.noPlanGoal')} />
            )}
            <div className="mt-3 border-t border-ldvh-border/70 pt-3">
              <div className="ldvh-caption-strong mb-1 text-ldvh-text-secondary">{getFieldLabel('summary', locale)}</div>
              {hasDetailContent(currentSummary) ? (
                <SummaryText value={currentSummary} collapseThreshold={900} />
              ) : (
                <EmptyHint text={t('objectDetail.noPlanDescription')} />
              )}
            </div>
          </div>
          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-4">
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
              {summaryItems.map((item) => (
                <div key={item.label} className="min-w-0 rounded-md border border-ldvh-border/70 bg-ldvh-panel px-3 py-2">
                  <div className="ldvh-caption mb-1 truncate text-ldvh-text-secondary">{item.label}</div>
                  <div className="ldvh-section-title truncate">{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: t('objectDetail.lifecycleStage'), value: t(getWorkCaseLifecycle(obj, summary, executionItems).labelKey) },
            { label: t('objectDetail.successCriteriaProgress'), value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—' },
            { label: t('objectDetail.executionItemProgress'), value: executionTotal > 0 ? `${executionDone}/${executionTotal}` : '—' },
            { label: t('objectDetail.closeDecisionRecordState'), value: summarizeRecordState(obj, summary, executionItems, t) },
          ].map((item) => (
            <div key={item.label} className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-bg px-3 py-2.5">
              <div className="ldvh-caption mb-1 truncate opacity-85">{item.label}</div>
              <div className="ldvh-section-title truncate">{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </ReadingNodeSection>
  );
}

function WorkCaseEvidenceSummarySection({ obj, summary }: { obj: Record<string, unknown>; summary: ObjectItem | null }) {
  const { t } = useI18n();
  const checklistProgress = getWorkCaseChecklistProgress(obj);
  const successCriteriaTotal = summary?.successCriteriaTotal ?? checklistProgress.total;
  const successCriteriaDone = summary?.successCriteriaDone ?? checklistProgress.done;
  const items = [
    {
      label: t('objectDetail.successCriteriaProgress'),
      value: successCriteriaTotal > 0 ? `${successCriteriaDone}/${successCriteriaTotal}` : '—',
      recorded: successCriteriaTotal > 0,
    },
    {
      label: t('objectList.planConfirmedAt'),
      value: summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at)),
    },
    {
      label: t('objectDetail.verificationEvidence'),
      value: summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence)),
    },
    {
      label: t('objectDetail.closureEvidence'),
      value: summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence) ? t('objectList.hasRecord') : t('objectList.missingRecord'),
      recorded: Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence)),
    },
  ];

  return (
    <DetailSection title={t('objectDetail.closeDecisionRecordState')} tone="default">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((item) => (
          <div
            key={item.label}
            className={`min-w-0 rounded-lg border px-3 py-2.5 ${
              item.recorded
                ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
            }`}
          >
            <div className="ldvh-caption mb-1 truncate opacity-85">{item.label}</div>
            <div className="ldvh-section-title truncate">{item.value}</div>
          </div>
        ))}
      </div>
    </DetailSection>
  );
}

function WorkCaseAiContextSection({ obj, locale }: { obj: Record<string, unknown>; locale: string }) {
  const { t } = useI18n();
  const [state, setState] = useState<ReadingNodeState>('collapsed');
  const orchestration = getWorkCaseOrchestration(obj);
  const aiEntries: Array<[string, unknown]> = [
    ['orchestration', obj.orchestration],
    ['plan_confirmed_at', obj.plan_confirmed_at],
    ['closure_requested_at', obj.closure_requested_at ?? obj.review_requested_at],
    ['closed_at', obj.closed_at],
    ['closure_outcome', obj.closure_outcome],
    ['residual_risks', obj.residual_risks],
    ['followup_refs', obj.followup_refs],
    ['revision_history', orchestration.revision_history],
    ['source', obj.source],
  ].filter((entry): entry is [string, unknown] => hasDetailContent(entry[1]));

  const executionRefs = detailStringArray(obj.aggregated_execution_refs);

  return (
    <ReadingNodeSection
      title={t('objectDetail.workcaseAiContext')}
      state={state}
      locale={locale}
      onToggle={() => setState((current) => getReadingNodeNextState(current))}
    >
      <div className="flex flex-col gap-4">
        {aiEntries.length > 0 && (
          <div className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{t('objectDetail.workcaseAiCore')}</div>
            <div className="flex flex-col gap-2">
              {aiEntries.map(([fieldKey, value]) => (
                <ContentField key={fieldKey} fieldKey={fieldKey} value={value} locale={locale} objType="workcase" />
              ))}
            </div>
          </div>
        )}

        <WorkCaseReviewSection orchestration={orchestration} />

        {executionRefs.length > 0 && (
          <div className="rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{t('objectDetail.executionReferences')}</div>
            <StringList items={executionRefs} />
          </div>
        )}
      </div>
    </ReadingNodeSection>
  );
}

function summarizeRecordState(obj: Record<string, unknown>, summary: ObjectItem | null, executionItems: RelatedObjectSummary[], t: (key: LocaleKey) => string) {
  const planConfirmed = Boolean(summary?.hasPlanConfirmedAt ?? hasDetailContent(obj.plan_confirmed_at));
  const verificationRecorded = Boolean(summary?.hasVerificationEvidence ?? hasDetailContent(obj.verification_evidence));
  const closureRecorded = Boolean(summary?.hasClosureEvidence ?? hasDetailContent(obj.closure_evidence));
  const closureRequested = Boolean(summary?.hasClosureRequestedAt ?? (hasDetailContent(obj.closure_requested_at) || hasDetailContent(obj.review_requested_at)));
  const closedAtRecorded = Boolean(summary?.hasClosedAt ?? hasDetailContent(obj.closed_at));
  const blockedCount = executionItems.filter((item) => item.status === 'blocked' || Boolean(item.blockingReason)).length;
  const items = [
    planConfirmed ? t('objectList.planConfirmedAt') : null,
    verificationRecorded ? t('objectList.verificationEvidence') : null,
    closureRecorded ? t('objectList.closureEvidence') : null,
    closureRequested ? t('objectList.closureRequestedAt') : null,
    closedAtRecorded ? t('objectList.closedAt') : null,
    blockedCount > 0 ? `${blockedCount} ${t('objectDetail.lifecycleBlocked')}` : null,
  ].filter(Boolean);

  if (items.length === 0) return t('objectList.missingRecord');
  return items.slice(0, 3).join(' · ');
}

function getWorkCaseLifecycle(
  obj: Record<string, unknown>,
  summary: ObjectItem | null,
  executionItems: RelatedObjectSummary[],
): { tone: WorkCaseLifecycleTone; labelKey: 'objectDetail.lifecycleDraft' | 'objectDetail.lifecyclePlanReview' | 'objectDetail.lifecyclePlanConfirming' | 'objectDetail.lifecycleActive' | 'objectDetail.lifecycleBlocked' | 'objectDetail.lifecycleVerification' | 'objectDetail.lifecycleResultReview' | 'objectDetail.lifecycleReview' | 'objectDetail.lifecycleClosed' } {
  const status = getWorkCaseDisplayStatus(detailString(obj.phase), detailString(obj.status, detailString(summary?.status)));
  if (status === 'closed') return { tone: 'closed', labelKey: 'objectDetail.lifecycleClosed' };
  if (status === 'subagents_plan_reviewing') return { tone: 'planReview', labelKey: 'objectDetail.lifecyclePlanReview' };
  if (status === 'human_plan_confirming') return { tone: 'planConfirming', labelKey: 'objectDetail.lifecyclePlanConfirming' };
  if (status === 'human_closure_confirming') return { tone: 'review', labelKey: 'objectDetail.lifecycleReview' };
  if (isWorkCaseResultReviewStatus(status)) return { tone: 'resultReview', labelKey: 'objectDetail.lifecycleResultReview' };
  if (status === 'review_needed') return { tone: 'review', labelKey: 'objectDetail.lifecycleReview' };
  if (executionItems.some((item) => item.status === 'blocked' || Boolean(item.blockingReason))) {
    return { tone: 'blocked', labelKey: 'objectDetail.lifecycleBlocked' };
  }
  if (status === 'draft') return { tone: 'draft', labelKey: 'objectDetail.lifecycleDraft' };
  if (hasDetailContent(obj.verification_evidence) || hasDetailContent(obj.closure_evidence)) {
    return { tone: 'verification', labelKey: 'objectDetail.lifecycleVerification' };
  }
  return { tone: 'active', labelKey: 'objectDetail.lifecycleActive' };
}

function ExecutionItemRow({
  item,
  locale,
  getStatus,
}: {
  item: RelatedObjectSummary;
  locale: string;
  getStatus: (status: string) => string;
}) {
  const { t } = useI18n();
  const tone = getExecutionFlowTone(item);
  const flowLabel = getExecutionFlowLabel(item, t, getStatus);
  const toneClass = executionFlowRowClass[tone];

  return (
    <div className={`my-1 rounded-md border px-3 py-2.5 ${toneClass}`}>
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <div className="flex min-w-0 items-center gap-1.5">
            <ExecutionFlowMarker tone={tone} label={flowLabel} compact />
            <span className="ldvh-body min-w-0 truncate">{getLocalizedTitle(item, locale)}</span>
          </div>
          <div className="mt-0.5 flex min-w-0 flex-wrap gap-x-3 gap-y-1">
            <span className="ldvh-meta-muted">{item.role || item.id}</span>
            {item.mode && <span className="ldvh-caption">{item.mode}</span>}
            <span className="ldvh-caption">{flowLabel}</span>
          </div>
        </div>
      </div>
      {item.expectedOutput && (
        <p className="ldvh-body-muted mt-2 border-l-2 border-ldvh-border/50 pl-2">{item.expectedOutput}</p>
      )}
      {item.resultSummary && (
        <p className="ldvh-body mt-2 border-l-2 border-emerald-500/40 pl-2">{item.resultSummary}</p>
      )}
      {item.blockingReason && (
        <p className="ldvh-body mt-2 border-l-2 border-amber-500/60 pl-2 text-amber-300">{item.blockingReason}</p>
      )}
      {(item.inputRefs?.length || item.evidenceRefs?.length) && (
        <div className="mt-2 flex min-w-0 flex-wrap gap-1.5">
          {[
            ...(item.inputRefs ?? []).map((ref) => ({ kind: 'input', ref })),
            ...(item.evidenceRefs ?? []).map((ref) => ({ kind: 'evidence', ref })),
          ].map(({ kind, ref }, index) => (
            <span key={`${kind}-${index}-${ref}`} className="ldvh-chip max-w-full truncate rounded-md border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5 text-ldvh-text-secondary">
              {ref}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function WorkCaseReviewSection({ orchestration }: { orchestration: Record<string, unknown> }) {
  const { t } = useI18n();
  const planReview = isDetailRecord(orchestration.plan_review) ? orchestration.plan_review : null;
  const resultReview = isDetailRecord(orchestration.result_review) ? orchestration.result_review : null;
  const legacyReview = isDetailRecord(orchestration.review) ? orchestration.review : null;

  if (planReview || resultReview) {
    return (
      <DetailSection title={t('objectDetail.workcaseReview')} tone="default">
        <div className="divide-y divide-ldvh-border/60">
          {planReview && <ReviewRecordGroup title={t('objectDetail.planReview')} review={planReview} phase="plan" />}
          {resultReview && <ReviewRecordGroup title={t('objectDetail.resultReview')} review={resultReview} phase="result" />}
        </div>
      </DetailSection>
    );
  }

  if (!legacyReview) return null;
  return <LegacyWorkCaseReviewSection review={legacyReview} />;
}

function ReviewRecordGroup({
  title,
  review,
  phase,
}: {
  title: string;
  review: Record<string, unknown>;
  phase: 'plan' | 'result';
}) {
  const { t } = useI18n();
  const reviewItems = Array.isArray(review.review_items)
    ? review.review_items.filter((item): item is Record<string, unknown> => isDetailRecord(item))
    : [];
  const controllerSelfCheck = isDetailRecord(review.controller_self_check) ? review.controller_self_check : null;
  const controllerResolution = isDetailRecord(review.controller_resolution) ? review.controller_resolution : null;
  const humanConfirmation = phase === 'plan' && isDetailRecord(review.human_confirmation) ? review.human_confirmation : null;
  const humanClosureConfirmation = phase === 'result' && isDetailRecord(review.human_closure_confirmation) ? review.human_closure_confirmation : null;
  const hasBody = reviewItems.length > 0
    || controllerSelfCheck
    || controllerResolution
    || humanConfirmation
    || humanClosureConfirmation;

  if (!hasBody) return null;

  return (
    <div className="py-3 first:pt-0 last:pb-0">
      <div className="ldvh-caption-strong mb-3 text-ldvh-text-secondary">{title}</div>
      <div className="flex min-w-0 flex-col gap-3">
        {controllerSelfCheck && (
          <ReviewInlineField
            label={t('objectDetail.controllerSelfCheck')}
            value={<ReviewRecordSummary record={controllerSelfCheck} />}
            compact
          />
        )}
        {reviewItems.length > 0 && (
          <ReviewInlineField
            label={t('objectDetail.reviewItems')}
            value={<ReviewItemsList items={reviewItems} />}
            compact
          />
        )}
        {controllerResolution && (
          <ReviewInlineField
            label={t('objectDetail.controllerResolution')}
            value={<ReviewRecordSummary record={controllerResolution} />}
            compact
          />
        )}
        {humanConfirmation && (
          <ReviewInlineField
            label={t('objectDetail.humanPlanConfirmation')}
            value={<ReviewRecordSummary record={humanConfirmation} />}
            compact
          />
        )}
        {humanClosureConfirmation && (
          <ReviewInlineField
            label={t('objectDetail.humanClosureConfirmation')}
            value={<ReviewRecordSummary record={humanClosureConfirmation} />}
            compact
          />
        )}
      </div>
    </div>
  );
}

function ReviewItemsList({ items }: { items: Record<string, unknown>[] }) {
  const { getStatus } = useI18n();
  return (
    <div className="flex min-w-0 flex-col gap-2">
      {items.slice(0, 4).map((item, index) => {
        const result = isDetailRecord(item.result) ? item.result : {};
        const status = detailString(result.status);
        const title = [
          detailString(item.agent),
          detailString(item.role),
          detailString(item.phase),
        ].filter(Boolean).join(' · ') || `#${index + 1}`;
        const summary = detailString(result.summary) || detailString(item.summary);
        return (
          <div key={`${title}-${index}`} className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg px-2.5 py-2">
            <div className="mb-1 flex min-w-0 flex-wrap items-center gap-2">
              <span className="ldvh-caption-strong min-w-0 truncate text-ldvh-text">{title}</span>
              {status && (
                <span className="ldvh-chip rounded-md border border-ldvh-border px-1.5 py-0.5 text-ldvh-text-secondary">
                  {getStatus(status)}
                </span>
              )}
            </div>
            {summary && <SummaryText value={summary} collapseThreshold={220} />}
          </div>
        );
      })}
      {items.length > 4 && (
        <span className="ldvh-caption text-ldvh-text-secondary">+{items.length - 4}</span>
      )}
    </div>
  );
}

function ReviewRecordSummary({ record }: { record: Record<string, unknown> }) {
  const { getStatus } = useI18n();
  const result = isDetailRecord(record.result) ? record.result : {};
  const status = detailString(result.status) || detailString(record.decision);
  const summary = detailString(record.summary)
    || detailString(result.summary)
    || detailString(record.scope)
    || detailString(record.notes);
  const at = detailString(record.confirmed_at) || detailString(record.signed_at);

  return (
    <div className="min-w-0">
      <div className="mb-1 flex min-w-0 flex-wrap items-center gap-2">
        {status && (
          <span className="ldvh-chip rounded-md border border-ldvh-border px-1.5 py-0.5 text-ldvh-text-secondary">
            {getStatus(status)}
          </span>
        )}
        {at && <span className="ldvh-meta-muted">{formatDateTime(at)}</span>}
      </div>
      {summary ? <SummaryText value={summary} collapseThreshold={320} /> : <span className="ldvh-body-muted">-</span>}
    </div>
  );
}

function LegacyWorkCaseReviewSection({ review }: { review: Record<string, unknown> }) {
  const { t } = useI18n();

  const specialistReview = isDetailRecord(review.specialist_review) ? review.specialist_review : null;
  const hasSpecialistDetail = Boolean(
    specialistReview && (
      hasDetailContent(specialistReview.required)
      || hasDetailContent(specialistReview.role)
      || hasDetailContent(specialistReview.expected_output)
    )
  );

  return (
    <DetailSection title={t('objectDetail.workcaseReview')} tone="default">
      <div className="divide-y divide-ldvh-border/60">
        {hasDetailContent(review.controller_self_check) && (
          <ReviewInlineField
            label={t('objectDetail.controllerSelfCheck')}
            value={<ReviewBoolean value={review.controller_self_check} />}
          />
        )}
        {hasSpecialistDetail && specialistReview && (
          <div className="py-3 first:pt-0 last:pb-0">
            <div className="ldvh-caption-strong mb-2 text-ldvh-text-secondary">{t('objectDetail.specialistReview')}</div>
            <div className="flex flex-col gap-2">
              {hasDetailContent(specialistReview.required) && (
                <ReviewInlineField
                  label={t('objectDetail.reviewRequirement')}
                  value={<ReviewBoolean value={specialistReview.required} />}
                  compact
                />
              )}
              {hasDetailContent(specialistReview.role) && (
                <ReviewInlineField
                  label={t('objectDetail.reviewRole')}
                  value={<span className="ldvh-body">{String(specialistReview.role)}</span>}
                  compact
                />
              )}
              {hasDetailContent(specialistReview.expected_output) && (
                <ReviewInlineField
                  label={t('objectDetail.expectedOutput')}
                  value={<SummaryText value={String(specialistReview.expected_output)} collapseThreshold={360} />}
                  compact
                />
              )}
            </div>
          </div>
        )}
        {hasDetailContent(review.human_closure_review) && (
          <ReviewInlineField
            label={t('objectDetail.humanClosureReview')}
            value={<ReviewBoolean value={review.human_closure_review} />}
          />
        )}
      </div>
    </DetailSection>
  );
}

function ReviewInlineField({ label, value, compact = false }: { label: string; value: ReactNode; compact?: boolean }) {
  return (
    <div className={`grid gap-2 ${compact ? 'sm:grid-cols-[5.25rem_1fr]' : 'py-3 first:pt-0 last:pb-0 sm:grid-cols-[6.25rem_1fr]'}`}>
      <div className="ldvh-caption-strong text-ldvh-text-secondary">{label}</div>
      <div className="min-w-0">{value}</div>
    </div>
  );
}

function ReviewBoolean({ value }: { value: unknown }) {
  const { t } = useI18n();
  const enabled = value === true || value === 'true' || value === 'required';
  return (
    <span className={`ldvh-chip inline-flex rounded-md border px-2 py-0.5 ${
      enabled
        ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
        : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary'
    }`}
    >
      {enabled ? t('objectDetail.required') : t('objectDetail.notRequired')}
    </span>
  );
}

export function DetailRecordItem({ label, recorded }: { label: string; recorded: boolean }) {
  const { t } = useI18n();
  return (
    <span className={`ldvh-caption-strong inline-flex items-center gap-1.5 rounded-md border px-2 py-1 ${
      recorded
        ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400'
        : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
    }`}
    >
      <span>{label}</span>
      <span className="ldvh-meta-muted">{recorded ? t('objectList.hasRecord') : t('objectList.missingRecord')}</span>
    </span>
  );
}


function isDetailRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function detailString(value: unknown, fallback = ''): string {
  if (value === null || value === undefined) return fallback;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return String(value);
}

function detailStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => detailString(item).trim())
    .filter((item) => item.length > 0);
}

function getWorkCaseOrchestration(obj: Record<string, unknown>): Record<string, unknown> {
  return isDetailRecord(obj.orchestration) ? obj.orchestration : {};
}

function getWorkCaseExecutionItems(obj: Record<string, unknown>): RelatedObjectSummary[] {
  const orchestration = getWorkCaseOrchestration(obj);
  const rawItems = Array.isArray(obj.work_items)
    ? obj.work_items
    : Array.isArray(orchestration.execution_items)
      ? orchestration.execution_items
      : [];
  return rawItems
    .map((rawItem, index): RelatedObjectSummary | null => {
      if (!isDetailRecord(rawItem)) return null;
      const id = detailString(rawItem.item_id, detailString(rawItem.id, `execution-item-${index + 1}`));
      return {
        id,
        type: 'execution_item',
        title: detailString(rawItem.goal, detailString(rawItem.title, id)),
        status: detailString(rawItem.status, 'unknown'),
        path: detailString(obj.path),
        updated: detailString(obj.updated),
        role: detailString(rawItem.role, detailString(rawItem.item_id)) || undefined,
        mode: detailString(rawItem.mode) || undefined,
        expectedOutput: detailString(rawItem.expected_result, detailString(rawItem.expected_output)) || undefined,
        resultSummary: detailString(rawItem.result_summary) || undefined,
        blockingReason: detailString(rawItem.blocking_summary, detailString(rawItem.blocking_reason)) || undefined,
        inputRefs: detailStringArray(rawItem.input_refs),
        evidenceRefs: detailStringArray(rawItem.evidence_refs),
      } satisfies RelatedObjectSummary;
    })
    .filter((item): item is RelatedObjectSummary => Boolean(item));
}
