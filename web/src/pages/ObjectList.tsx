import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowRight, CheckCircle2, CircleAlert, ClipboardCheck, PauseCircle } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import WorkCaseProgressFilter from '@/components/WorkCaseProgressFilter';
import ObjectPriorityFilter from '@/components/ObjectPriorityFilter';
import CopyPathButton from '@/components/CopyPathButton';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { ExecutionFlowBar, ExecutionFlowLegend, ExecutionFlowMarker } from '@/components/ExecutionFlowStatus';
import { fetchObjects, type ObjectItem, type ObjectStatusOption, type RelatedObjectSummary, type WorkCaseProgressOption } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getLocalizedObjectTitle, getObjectStatusLocale } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';
import { getExecutionFlowLabel, getExecutionFlowTone, sortWorkCaseExecutionItems } from '@/utils/executionFlowStatus';
import {
  WORKCASE_PROGRESS_GROUP_ORDER,
  WORKCASE_PROGRESS_STEP_ORDER,
  isWorkCaseProgressGroup,
  isWorkCaseClosureConfirmingStatus,
  type WorkCaseProgressGroup,
  type WorkCaseProgressStep,
} from '@/shared/workcaseStatus';

type Translate = ReturnType<typeof useI18n>['t'];
type WorkCaseRecordState = 'recorded' | 'missing';
type StatusReason = { label: string; text: string; missing?: boolean };
type WorkCaseCardSummaryTone = 'default' | 'risk' | 'ready' | 'gate';

const WORKCASE_PROGRESS_GROUP_INDEX = new Map<string, number>(
  WORKCASE_PROGRESS_GROUP_ORDER.map((group, index) => [group, index]),
);

const WORKCASE_PROGRESS_STEP_INDEX = new Map<string, number>(
  WORKCASE_PROGRESS_STEP_ORDER.map((step, index) => [step, index]),
);

const TITLE_ACCENT_CLASS: Record<string, string> = {
  active: 'border-emerald-400/80',
  human_plan_confirming: 'border-violet-400/80',
  executing: 'border-emerald-400/80',
  result_self_checking: 'border-blue-400/80',
  subagents_result_reviewing: 'border-indigo-400/80',
  human_closure_confirming: 'border-violet-400/80',
  plan_confirmation: 'border-violet-400/80',
  progressing: 'border-sky-400/80',
  closure_confirmation: 'border-violet-400/80',
  accepted: 'border-emerald-400/70',
  review_needed: 'border-violet-400/80',
  verifying: 'border-blue-400/80',
  draft: 'border-amber-400/75',
  proposed: 'border-amber-400/75',
  planned: 'border-amber-400/75',
  pending: 'border-amber-400/75',
  open: 'border-amber-400/75',
  closed: 'border-zinc-500/50',
  retired: 'border-zinc-500/50',
  resolved: 'border-zinc-500/50',
  routed: 'border-zinc-500/50',
  archived: 'border-zinc-500/50',
  discarded: 'border-red-400/75',
  rejected: 'border-red-400/75',
  deprecated: 'border-red-400/75',
  suspended: 'border-red-400/75',
};

function getTitleAccentClass(status: string): string {
  return TITLE_ACCENT_CLASS[status] ?? 'border-ldvh-accent/70';
}

function formatReasonText(value: string): string {
  return value
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((line) => line
      .trim()
      .replace(/^#{1,6}\s+/, '')
      .replace(/\[[ xX]\]\s*/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .trim())
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function statusRequiresReason(obj: ObjectItem): boolean {
  return obj.status === 'archived'
    || obj.status === 'deprecated'
    || obj.status === 'discarded'
    || obj.status === 'closed'
    || obj.status === 'routed'
    || (obj.fact_type_key === 'spark' && obj.status === 'implemented');
}

function getNonActiveReason(obj: ObjectItem, t: Translate): StatusReason | null {
  if (obj.status === 'active') return null;
  const labels = {
    archive_reason: t('objectList.archiveReason'),
    deprecated_reason: t('objectList.deprecatedReason'),
    discard_reason: t('objectList.discardReason'),
    disposition_summary: t('objectList.disposition'),
    closure_evidence: t('objectList.closeReason'),
  };
  const orderedFields = obj.status === 'routed'
    ? ['disposition_summary', 'closure_evidence', 'discard_reason']
    : obj.status === 'archived'
    ? ['archive_reason', 'closure_evidence', 'deprecated_reason', 'discard_reason']
    : obj.status === 'deprecated'
      ? ['deprecated_reason', 'archive_reason', 'closure_evidence', 'discard_reason']
      : obj.status === 'discarded'
        ? ['discard_reason', 'archive_reason', 'deprecated_reason', 'closure_evidence']
        : obj.status === 'closed'
          ? ['closure_evidence', 'archive_reason', 'deprecated_reason', 'discard_reason']
          : ['archive_reason', 'deprecated_reason', 'discard_reason', 'closure_evidence'];

  for (const field of orderedFields) {
    const value = obj[field as keyof ObjectItem];
    if (typeof value !== 'string' || !value.trim()) continue;
    const text = formatReasonText(value);
    if (!text) continue;
    return { label: labels[field as keyof typeof labels], text };
  }
  if (statusRequiresReason(obj)) {
    return {
      label: t('objectList.missingReason'),
      text: t('objectList.missingReasonText'),
      missing: true,
    };
  }
  return null;
}

function StatusReasonNote({ reason }: { reason: StatusReason }) {
  const isMissing = Boolean(reason.missing);
  return (
    <div
      onClick={(event) => event.stopPropagation()}
      className={`min-w-0 cursor-default px-1.5 py-1 ${
        isMissing
          ? 'rounded-md bg-red-500/5'
          : ''
      }`}
    >
      <div className={`ldvh-meta mb-1 flex min-w-0 items-center gap-1.5 ${
        isMissing ? 'text-red-400' : 'text-ldvh-text-secondary/75'
      }`}
      >
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${isMissing ? 'bg-red-400' : 'bg-ldvh-text-secondary/75'}`} aria-hidden="true" />
        <span className="min-w-0 truncate">{reason.label}</span>
      </div>
      <p className={`whitespace-pre-wrap break-words text-[12px] leading-5 ${
        isMissing ? 'text-red-400' : 'text-ldvh-text-secondary/75'
      }`}
      >
        {reason.text}
      </p>
    </div>
  );
}

function handleKeyboardOpen(event: KeyboardEvent<HTMLElement>, onOpen: () => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    event.stopPropagation();
    onOpen();
  }
}

function getWorkCaseRecordStateLabel(state: WorkCaseRecordState, t: Translate): string {
  if (state === 'recorded') return t('objectList.hasRecord');
  return t('objectList.missingRecord');
}

function getWorkCaseRecordClassName(state: WorkCaseRecordState): string {
  if (state === 'recorded') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500';
  return 'border-red-500/60 bg-red-500/15 text-red-400 ring-1 ring-inset ring-red-500/20';
}

function getWorkCaseRecordIcon(state: WorkCaseRecordState) {
  if (state === 'recorded') return CheckCircle2;
  return CircleAlert;
}

function WorkCaseRecordItem({ label, state, t }: { label: string; state: WorkCaseRecordState; t: Translate }) {
  const stateLabel = getWorkCaseRecordStateLabel(state, t);
  const StateIcon = getWorkCaseRecordIcon(state);
  return (
    <span
      aria-label={`${label} ${stateLabel}`}
      title={`${label} ${stateLabel}`}
      className={`ldvh-chip inline-flex min-w-0 items-center gap-1.5 rounded-md border px-2 py-1 ${getWorkCaseRecordClassName(state)}`}
    >
      <ClipboardCheck size={12} className="shrink-0" />
      <span className="min-w-0 truncate">{label}</span>
      <StateIcon size={state === 'missing' ? 13 : 12} strokeWidth={state === 'missing' ? 2.6 : 2} className="shrink-0 opacity-95" />
    </span>
  );
}

function WorkCaseCardSummary({
  label,
  value,
  helper,
  tone = 'default',
}: {
  label: string;
  value: string;
  helper?: string;
  tone?: WorkCaseCardSummaryTone;
}) {
  const toneClass = {
    default: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
    risk: 'border-amber-500/30 bg-amber-500/10 text-amber-400',
    ready: 'border-emerald-500/25 bg-emerald-500/10 text-emerald-400',
    gate: 'border-violet-500/25 bg-violet-500/10 text-violet-400',
  }[tone];

  return (
    <div className={`flex min-w-0 items-center justify-between gap-2 rounded-md border px-2.5 py-2 ${toneClass}`}>
      <div className="min-w-0">
        <div className="ldvh-caption-strong truncate">{label}</div>
        {helper && <div className="ldvh-meta-muted mt-0.5 truncate">{helper}</div>}
      </div>
      <div className="shrink-0 font-mono text-[15px] leading-none tracking-tight">{value}</div>
    </div>
  );
}

function WorkCasePlanConfirmationContent({
  goal,
  successCriteria,
  t,
}: {
  goal?: string;
  successCriteria?: string[];
  t: Translate;
}) {
  const criteria = successCriteria?.filter((criterion) => criterion.trim()) ?? [];

  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} />
      <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-ldvh-accent/45 bg-ldvh-bg/65 px-3.5 py-3">
        <div className="flex min-w-0 items-center justify-between gap-2">
          <h3 className="ldvh-card-decision-title">{t('objectList.successCriteria')}</h3>
          {criteria.length > 0 && (
            <span className="ldvh-meta-muted shrink-0">{t('objectList.workcaseCriteriaCount', { count: String(criteria.length) })}</span>
          )}
        </div>
        {criteria.length > 0 ? (
          <ul className="mt-2 grid min-w-0 gap-1.5">
            {criteria.map((criterion, index) => (
              <li key={`${index}-${criterion}`} className="flex min-w-0 items-start gap-2">
                <span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-text-secondary/60" />
                <span className="ldvh-card-decision-body min-w-0 break-words">{formatReasonText(criterion)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="ldvh-card-decision-body mt-1.5 text-red-400">{t('objectList.workcaseFieldMissing')}</p>
        )}
      </section>
    </div>
  );
}

function WorkCaseGoalSection({ goal, t }: { goal?: string; t: Translate }) {
  return (
    <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-ldvh-accent/45 bg-ldvh-bg/65 px-3.5 py-3">
      <h3 className="ldvh-card-decision-title">{t('objectList.workcaseGoal')}</h3>
      <p className={`ldvh-card-decision-body mt-1.5 max-w-[82ch] whitespace-pre-line break-words ${goal?.trim() ? '' : 'text-red-400'}`}>
        {goal?.trim() ? formatReasonText(goal) : t('objectList.workcaseFieldMissing')}
      </p>
    </section>
  );
}

function WorkCaseProgressingContent({
  goal,
  progressStep,
  executionItemsProjectionValid,
  executionItemTotal,
  executionItemDone,
  executionItemCancelled,
  executionItemOpen,
  executionItemsActive,
  isBlocked,
  waitingOn,
  blockingSummary,
  t,
}: {
  goal?: string;
  progressStep: WorkCaseProgressStep | null;
  executionItemsProjectionValid: boolean;
  executionItemTotal: number;
  executionItemDone: number;
  executionItemCancelled: number;
  executionItemOpen: number;
  executionItemsActive: RelatedObjectSummary[];
  isBlocked: boolean;
  waitingOn?: string;
  blockingSummary?: string;
  t: Translate;
}) {
  const stepLabels = [
    t('objectList.workcaseStageExecute'),
    t('objectList.workcaseStageSelfCheck'),
    t('objectList.workcaseStageResultReview'),
    t('objectList.workcaseStageSynthesis'),
  ];
  const currentStep = progressStep ? WORKCASE_PROGRESS_STEP_ORDER.indexOf(progressStep) : -1;
  const currentStepLabel = currentStep >= 0
    ? stepLabels[currentStep]
    : t('objectList.workcaseStageUnavailable');
  const itemExecution = progressStep === 'item_execution';
  const itemStageMismatch = executionItemsProjectionValid && currentStep >= 0 && (
    (itemExecution && executionItemsActive.length === 0 && executionItemOpen === 0)
    || (!itemExecution && executionItemOpen > 0)
  );
  const showActiveItems = !executionItemsProjectionValid
    || itemExecution
    || executionItemsActive.length > 0
    || itemStageMismatch;

  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} />
      <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-sky-400/55 bg-ldvh-bg/65 px-3.5 py-3">
        <h3 className="ldvh-card-decision-title">{t('objectList.workcaseCurrentProgress')}</h3>

        <div className={`mt-2.5 min-w-0 rounded-md border px-3 py-2.5 ${
          currentStep >= 0
            ? 'border-sky-500/25 bg-sky-500/[0.07]'
            : 'border-red-500/30 bg-red-500/[0.07]'
        }`}>
          <div className="flex min-w-0 flex-wrap items-start justify-between gap-x-4 gap-y-2">
            <div className={`flex min-w-0 items-center gap-2 ${currentStep >= 0 ? 'text-sky-400' : 'text-red-400'}`}>
              {currentStep >= 0 && (
                <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
                  <span className="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-25" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
                </span>
              )}
              <div className="ldvh-card-decision-title min-w-0 break-words text-current">{currentStepLabel}</div>
            </div>

            <div className="min-w-0 text-left sm:text-right">
              {executionItemsProjectionValid ? (
                <div className="ldvh-meta-primary whitespace-nowrap">
                  {t('objectList.workcaseItemProgress', {
                    done: String(executionItemDone),
                    total: String(executionItemTotal),
                  })}
                </div>
              ) : (
                <div className="ldvh-meta text-red-400">{t('objectList.workcaseItemsUnavailable')}</div>
              )}
              {executionItemsProjectionValid && executionItemCancelled > 0 && (
                <div className="ldvh-meta-muted mt-0.5">
                  {t('objectList.workcaseItemsCancelled', { count: String(executionItemCancelled) })}
                </div>
              )}
            </div>
          </div>
        </div>

        <ol
          className="mt-3 grid min-w-0 grid-cols-4"
          aria-label={`${t('objectList.workcaseDynamicStages')}：${currentStepLabel}`}
        >
          {WORKCASE_PROGRESS_STEP_ORDER.map((step, index) => {
            const isCurrent = index === currentStep;
            return (
              <li
                key={step}
                aria-current={isCurrent ? 'step' : undefined}
                className="relative flex min-w-0 flex-col items-center px-1 text-center"
              >
                {index > 0 && (
                  <span className="absolute left-0 right-1/2 top-2.5 h-px bg-ldvh-border" aria-hidden="true" />
                )}
                {index < WORKCASE_PROGRESS_STEP_ORDER.length - 1 && (
                  <span className="absolute left-1/2 right-0 top-2.5 h-px bg-ldvh-border" aria-hidden="true" />
                )}
                <span className={`ldvh-meta relative z-10 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border bg-ldvh-bg ${
                  isCurrent
                    ? 'border-sky-400/60 bg-sky-500/15 font-semibold text-sky-400 ring-2 ring-sky-500/10'
                    : 'border-ldvh-border text-ldvh-text-secondary'
                }`}>
                  {index + 1}
                </span>
                <span className={`ldvh-card-decision-body mt-1.5 min-w-0 break-words leading-4 ${
                  isCurrent ? 'font-medium text-sky-400' : 'text-ldvh-text-secondary/80'
                }`}>
                  {stepLabels[index]}
                </span>
              </li>
            );
          })}
        </ol>

        {showActiveItems && (
          <div className="mt-2.5 border-t border-ldvh-border/70 pt-2.5">
            <div className="ldvh-caption-strong text-ldvh-text-secondary">{t('objectList.workcaseCurrentItems')}</div>
            {!executionItemsProjectionValid ? (
              <p className="ldvh-card-decision-body mt-1.5 text-red-400">
                {t('objectList.workcaseItemsUnavailable')}
              </p>
            ) : (
              <>
                {itemStageMismatch && (
                  <p className="ldvh-card-decision-body mt-1.5 text-red-400">
                    {t('objectList.workcaseItemStageMismatch')}
                  </p>
                )}
                {executionItemsActive.length > 0 ? (
                  <ul className="mt-1.5 grid min-w-0 gap-2">
                    {executionItemsActive.map((item) => {
                      const blocked = item.status === 'blocked';
                      return (
                        <li key={item.id} className="flex min-w-0 items-start gap-2">
                          <span
                            aria-hidden="true"
                            className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${blocked ? 'bg-amber-400/80' : 'bg-sky-400/75'}`}
                          />
                          <div className="min-w-0">
                            <div className={`ldvh-meta-muted break-all ${blocked ? 'text-amber-400' : ''}`}>
                              {item.id}
                              <span className="px-1 text-ldvh-text-secondary/60" aria-hidden="true">·</span>
                              {blocked
                                ? t('objectList.workcaseItemBlocked')
                                : t('objectList.workcaseItemInProgress')}
                            </div>
                            <p className="ldvh-card-decision-body mt-0.5 min-w-0 break-words">
                              {formatReasonText(item.title)}
                            </p>
                            {blocked && (
                              <p className={`ldvh-card-decision-body mt-0.5 whitespace-pre-line break-words ${item.blockingReason?.trim() ? 'text-amber-300' : 'text-red-400'}`}>
                                {item.blockingReason?.trim()
                                  ? formatReasonText(item.blockingReason)
                                  : t('objectList.workcaseFieldMissing')}
                              </p>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : !itemStageMismatch ? (
                  <p className="ldvh-caption mt-1 text-ldvh-text-secondary/75">
                    {t('objectList.workcaseNoCurrentItems')}
                  </p>
                ) : null}
              </>
            )}
          </div>
        )}

        {waitingOn?.trim() && (
          <div className="mt-2.5 flex min-w-0 items-start gap-2 rounded-md border border-ldvh-border/80 bg-ldvh-panel/45 px-2.5 py-2 text-ldvh-text-secondary">
            <PauseCircle size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <div className="ldvh-caption-strong">{t('objectList.workcaseWaitingOn')}</div>
              <p className="ldvh-card-decision-body mt-0.5 whitespace-pre-line break-words">
                {formatReasonText(waitingOn)}
              </p>
            </div>
          </div>
        )}

        {isBlocked && (
          <div className="mt-2.5 flex min-w-0 items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-2 text-amber-400">
            <CircleAlert size={14} className="mt-0.5 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <div className="ldvh-caption-strong">{t('objectList.workcaseBlockingReason')}</div>
              <p className={`ldvh-card-decision-body mt-0.5 whitespace-pre-line break-words ${blockingSummary?.trim() ? 'text-amber-300' : 'text-red-400'}`}>
                {blockingSummary?.trim() ? formatReasonText(blockingSummary) : t('objectList.workcaseFieldMissing')}
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function WorkCaseProgressSignal({
  progressGroup,
  progressStep,
  locale,
  t,
}: {
  progressGroup: WorkCaseProgressGroup | null;
  progressStep: WorkCaseProgressStep | null;
  locale: string;
  t: Translate;
}) {
  const progressing = progressGroup === 'progressing';
  const closed = progressGroup === 'closed';
  const currentStep = progressStep ? WORKCASE_PROGRESS_STEP_ORDER.indexOf(progressStep) : -1;
  const stepLabels = [
    t('objectList.workcaseStageExecute'),
    t('objectList.workcaseStageSelfCheck'),
    t('objectList.workcaseStageResultReview'),
    t('objectList.workcaseStageSynthesis'),
  ];
  const groupLabel = progressGroup
    ? getObjectStatusLocale('workcase', progressGroup, locale)
    : t('objectList.workcaseProgressUnavailable');
  const stepLabel = currentStep >= 0 ? stepLabels[currentStep] : null;
  const toneClass = progressing
    ? 'border-sky-500/25 bg-sky-500/5 text-sky-400'
    : closed
      ? 'border-zinc-500/30 bg-zinc-500/5 text-zinc-400'
      : 'border-violet-500/25 bg-violet-500/5 text-violet-400';

  return (
    <div
      onClick={(event) => event.stopPropagation()}
      className={`min-w-0 cursor-default rounded-md border px-3 py-2.5 ${toneClass}`}
    >
      <div className="flex min-w-0 items-center gap-2">
        {progressing ? (
          <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
            <span className="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-35" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
          </span>
        ) : closed ? (
          <CheckCircle2 size={14} className="shrink-0" aria-hidden="true" />
        ) : (
          <PauseCircle size={14} className="shrink-0" aria-hidden="true" />
        )}
        <span className="ldvh-caption-strong min-w-0 truncate">{groupLabel}</span>
        {stepLabel && <span className="ldvh-meta-muted min-w-0 truncate">{stepLabel}</span>}
      </div>

      {progressing && currentStep >= 0 && (
        <div
          className="mt-2.5 grid grid-cols-4 gap-1.5"
          aria-label={`${t('objectList.workcaseDynamicStages')}：${stepLabel}`}
        >
          {WORKCASE_PROGRESS_STEP_ORDER.map((step, index) => {
            const isCurrent = index === currentStep;
            return (
              <div key={step} className="min-w-0">
                <div className="flex items-center gap-1" aria-hidden="true">
                  <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${
                    isCurrent
                      ? 'motion-safe:animate-pulse bg-current'
                      : 'bg-ldvh-border'
                  }`} />
                  {index < WORKCASE_PROGRESS_STEP_ORDER.length - 1 && (
                    <span className="h-px min-w-0 flex-1 bg-ldvh-border" />
                  )}
                </div>
                <span className={`mt-1 block truncate text-[10px] leading-4 ${isCurrent ? 'font-medium text-current' : 'text-ldvh-text-secondary/70'}`}>
                  {stepLabels[index]}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function sortObjectsForList(items: ObjectItem[], currentType: string): ObjectItem[] {
  if (currentType !== 'workcase') return items;
  return [...items].sort((a, b) => {
    const groupDelta = (WORKCASE_PROGRESS_GROUP_INDEX.get(a.progress_group ?? '') ?? 999)
      - (WORKCASE_PROGRESS_GROUP_INDEX.get(b.progress_group ?? '') ?? 999);
    if (groupDelta !== 0) return groupDelta;
    const stepDelta = (WORKCASE_PROGRESS_STEP_INDEX.get(a.progress_step ?? '') ?? 999)
      - (WORKCASE_PROGRESS_STEP_INDEX.get(b.progress_step ?? '') ?? 999);
    if (stepDelta !== 0) return stepDelta;
    const updatedDelta = Date.parse(b.updated || '') - Date.parse(a.updated || '');
    if (Number.isFinite(updatedDelta) && updatedDelta !== 0) return updatedDelta;
    return a.id.localeCompare(b.id);
  });
}

function sparkViewItem(value: ObjectItem): ObjectItem {
  if (value.fact_type_key !== 'spark' || typeof value.object_id !== 'string') return value;
  return {
    ...value,
    id: value.object_id,
    type: value.fact_type_key,
    path: value.canonical_path ?? '',
    created: value.created_at,
    updated: value.updated_at ?? '',
  };
}


function ObjectCardFrame({
  obj,
  locale,
  onOpen,
  children,
  showNonActiveReason = true,
  displayStatus,
  prominentTitle = false,
}: {
  obj: ObjectItem;
  locale: string;
  onOpen: (objId: string) => void;
  children?: ReactNode;
  showNonActiveReason?: boolean;
  displayStatus?: string;
  prominentTitle?: boolean;
}) {
  const { t } = useI18n();
  const presentedStatus = displayStatus ?? obj.status;
  const titleAccentClass = getTitleAccentClass(presentedStatus);
  const typeColor = CATEGORY_COLORS[obj.type] || CATEGORY_COLORS.other;
  const nonActiveReason = getNonActiveReason(obj, t);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(obj.id)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(obj.id))}
      className="group/card flex min-w-0 cursor-pointer flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left outline-none transition-colors hover:border-ldvh-accent/40 hover:bg-ldvh-panel/95 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ldvh-accent/70"
    >
      <div className="flex min-w-0 items-center justify-between gap-2">
        <span className="ldvh-meta-muted min-w-0 truncate">{obj.id}</span>
        <div className="flex shrink-0 items-center gap-2">
          <CopyPathButton path={obj.path} label={t('common.copyObjectPath')} copiedLabel={t('common.copiedObjectPath')} />
          <StatusBadge status={presentedStatus} statusLabel={getObjectStatusLocale(obj.type, presentedStatus, locale)} objectType={obj.type} />
        </div>
      </div>
      <div
        className={`-mx-1 flex min-w-0 items-center gap-1.5 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 text-left ring-1 ring-inset ring-ldvh-border/50 transition-colors group-hover/card:bg-ldvh-bg/85 ${titleAccentClass}`}
      >
        <PriorityIcon source={obj} type={obj.type} locale={locale} size="sm" />
        <ObjectTypeIcon type={obj.type} size={14} className="shrink-0" style={{ color: typeColor }} />
        <h2 className={`${prominentTitle ? 'ldvh-card-title-prominent' : 'ldvh-card-title'} min-w-0 flex-1 whitespace-normal break-words transition-colors group-hover/card:text-ldvh-accent`}>
          {getLocalizedObjectTitle(obj, locale)}
        </h2>
        <ArrowRight size={14} className="shrink-0 text-ldvh-text-secondary transition-all group-hover/card:translate-x-0.5 group-hover/card:text-ldvh-accent" />
      </div>
      {showNonActiveReason && nonActiveReason && <StatusReasonNote reason={nonActiveReason} />}
      {children}
      <div className="mt-auto flex min-w-0 justify-end pt-1 text-right">
        <span className="ldvh-meta-muted">
          {t('objectList.updated', { time: formatDateTime(obj.updated) })}
        </span>
      </div>
    </div>
  );
}

function hasSparkResolvedFact(obj: ObjectItem) {
  return obj.status === 'routed';
}

function hasSparkDiscardFact(obj: ObjectItem) {
  return obj.status === 'discarded';
}

function hasSparkImplementedFact(obj: ObjectItem) {
  return obj.status === 'implemented';
}

function TerminalFactPanel({
  tone,
  title,
  children,
}: {
  tone: 'routed' | 'implemented' | 'discarded' | 'retired';
  title?: string;
  children: ReactNode;
}) {
  void tone;
  return (
    <div
      onClick={(event) => event.stopPropagation()}
      className="min-w-0 cursor-default px-1.5 py-1"
    >
      {title && (
        <div className="ldvh-meta mb-1 flex min-w-0 items-center gap-1.5 text-ldvh-text-secondary/75">
          <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-ldvh-text-secondary/75" aria-hidden="true" />
          <span className="min-w-0 truncate">{title}</span>
        </div>
      )}
      <div className="min-w-0 text-ldvh-text-secondary/75">
        {children}
      </div>
    </div>
  );
}

function SparkTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const reason = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');
  const tone = obj.status === 'discarded' ? 'discarded' : obj.status === 'implemented' ? 'implemented' : 'routed';

  return (
    <TerminalFactPanel tone={tone}>
      <div className="min-w-0 whitespace-pre-line break-words text-[12px] leading-5 text-ldvh-text-secondary/75">
        {formatReasonText(reason)}
      </div>
    </TerminalFactPanel>
  );
}

function SparkCardContent({ obj }: { obj: ObjectItem }) {
  if (hasSparkDiscardFact(obj) || hasSparkImplementedFact(obj) || hasSparkResolvedFact(obj)) return <SparkTerminalCardContent obj={obj} />;
  return null;
}

function PitfallTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const disposition = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');

  return (
    <TerminalFactPanel tone="retired">
      <div className="min-w-0 whitespace-pre-line break-words text-[12px] leading-5 text-ldvh-text-secondary/75">
        {formatReasonText(disposition)}
      </div>
    </TerminalFactPanel>
  );
}

function PitfallCardContent({ obj }: { obj: ObjectItem }) {
  if (obj.status === 'retired') return <PitfallTerminalCardContent obj={obj} />;
  return null;
}

function AdrTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const disposition = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');

  return (
    <TerminalFactPanel tone="retired">
      <div className="min-w-0 whitespace-pre-line break-words text-[12px] leading-5 text-ldvh-text-secondary/75">
        {formatReasonText(disposition)}
      </div>
    </TerminalFactPanel>
  );
}

function AdrCardContent({ obj }: { obj: ObjectItem }) {
  if (obj.status === 'retired') return <AdrTerminalCardContent obj={obj} />;
  return null;
}

export default function ObjectList() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [statusOptions, setStatusOptions] = useState<ObjectStatusOption[]>([]);
  const [progressOptions, setProgressOptions] = useState<WorkCaseProgressOption[]>([]);
  const [priorityOptions, setPriorityOptions] = useState<ObjectStatusOption[]>([]);
  const [statusTotal, setStatusTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'workcase';
  const statusParam = searchParams.get('status');
  const activeStatus = currentType === 'workcase' ? null : getEffectiveListStatus(currentType, statusParam);
  const progressParam = searchParams.get('progress');
  const activeProgressGroup = currentType === 'workcase' && isWorkCaseProgressGroup(progressParam)
    ? progressParam
    : null;
  const priorityParam = searchParams.get('priority');
  const supportsPriorityNavigation = currentType === 'spark' || currentType === 'workcase';
  const activePriority = supportsPriorityNavigation && ['P0', 'P1', 'P2', 'P3'].includes(priorityParam ?? '')
    ? priorityParam
    : null;
  const isPriorityApplicable = currentType === 'spark'
    ? activeStatus === 'open' || activeStatus === null
    : currentType === 'workcase' && activeProgressGroup !== 'closed';

  useEffect(() => {
    const removesLegacyCategory = currentType === 'spark' && searchParams.has('category');
    const removesWorkCaseStatus = currentType === 'workcase' && searchParams.has('status');
    const removesForeignProgress = currentType !== 'workcase' && searchParams.has('progress');
    if (!removesLegacyCategory && !removesWorkCaseStatus && !removesForeignProgress) return;
    const nextParams = new URLSearchParams(searchParams);
    if (removesLegacyCategory) nextParams.delete('category');
    if (removesWorkCaseStatus) nextParams.delete('status');
    if (removesForeignProgress) nextParams.delete('progress');
    setSearchParams(nextParams, { replace: true });
  }, [currentType, searchParams, setSearchParams]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setStatusOptions([]);
    setProgressOptions([]);
    setPriorityOptions([]);
    setStatusTotal(0);
    fetchObjects(currentType, activeStatus ?? undefined, activePriority ?? undefined, activeProgressGroup ?? undefined)
      .then((result) => {
        const receivedItems = result.data?.items ?? [];
        const nextItems = currentType === 'spark' ? receivedItems.map(sparkViewItem) : receivedItems;
        setItems(nextItems);
        setStatusOptions(result.data?.statusOptions ?? []);
        setProgressOptions(result.data?.progressOptions ?? []);
        setPriorityOptions(result.data?.priorityOptions ?? []);
        setStatusTotal(result.data?.statusTotal ?? nextItems.length);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentType, activeStatus, activePriority, activeProgressGroup, reloadKey]);

  const sortedItems = sortObjectsForList(items, currentType);
  const typeNotIntegrated = sortedItems.find((item) => item.kind === 'type_not_integrated');
  const visibleItems = sortedItems.filter((item) => item.kind !== 'type_not_integrated');

  const handleStatusChange = (status: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    writeListStatusParam(currentType, nextParams, status);
    if (currentType === 'spark' && status !== 'open' && status !== null) {
      nextParams.delete('priority');
    }
    setSearchParams(nextParams);
  };

  const handleProgressGroupChange = (group: WorkCaseProgressGroup | null) => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('status');
    if (group) nextParams.set('progress', group);
    else nextParams.delete('progress');
    if (group === 'closed') nextParams.delete('priority');
    setSearchParams(nextParams);
  };

  const handlePriorityChange = (priority: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    if (priority) {
      nextParams.set('priority', priority);
      if (currentType === 'spark') writeListStatusParam('spark', nextParams, 'open');
    } else {
      nextParams.delete('priority');
    }
    setSearchParams(nextParams);
  };

  const detailSearch = searchParams.toString();
  const returnToListPath = `${location.pathname}${location.search}`;
  const openObject = (objId: string) => {
    navigate(`/objects/${currentType}/${objId}${detailSearch ? `?${detailSearch}` : ''}`, {
      state: { from: returnToListPath },
    });
  };

  const renderObjectCard = (obj: ObjectItem) => {

    if (currentType === 'workcase') {
      const progressGroup = isWorkCaseProgressGroup(obj.progress_group) ? obj.progress_group : null;
      const progressStep = WORKCASE_PROGRESS_STEP_ORDER.includes(obj.progress_step as WorkCaseProgressStep)
        ? obj.progress_step as WorkCaseProgressStep
        : null;
      if (progressGroup === 'plan_confirmation') {
        return (
          <ObjectCardFrame
            key={obj.id}
            obj={obj}
            locale={locale}
            onOpen={openObject}
            showNonActiveReason={false}
            displayStatus={progressGroup}
            prominentTitle
          >
            <WorkCasePlanConfirmationContent goal={obj.goal} successCriteria={obj.successCriteria} t={t} />
          </ObjectCardFrame>
        );
      }
      if (progressGroup === 'progressing') {
        return (
          <ObjectCardFrame
            key={obj.id}
            obj={obj}
            locale={locale}
            onOpen={openObject}
            showNonActiveReason={false}
            displayStatus={progressGroup}
            prominentTitle
          >
            <WorkCaseProgressingContent
              goal={obj.goal}
              progressStep={progressStep}
              executionItemsProjectionValid={obj.executionItemsProjectionValid ?? false}
              executionItemTotal={obj.executionItemTotal ?? 0}
              executionItemDone={obj.executionItemDone ?? 0}
              executionItemCancelled={obj.executionItemCancelled ?? 0}
              executionItemOpen={obj.executionItemOpen ?? 0}
              executionItemsActive={obj.executionItemsActive ?? []}
              isBlocked={obj.responsibilityStatus === 'blocked'}
              waitingOn={obj.waiting_on}
              blockingSummary={obj.blocking_summary}
              t={t}
            />
          </ObjectCardFrame>
        );
      }
      const executionItems = obj.executionItems ?? [];
      const sortedExecutionItems = sortWorkCaseExecutionItems(executionItems);
      const visibleExecutionItems = sortedExecutionItems.slice(0, 8);
      const moreCount = Math.max(0, sortedExecutionItems.length - visibleExecutionItems.length);
      const needsCloseDecision = progressGroup === 'closure_confirmation' || isWorkCaseClosureConfirmingStatus(obj.status);
      const isClosedWorkCase = progressGroup === 'closed';
      const successCriteriaState: WorkCaseRecordState = obj.hasSuccessCriteria ? 'recorded' : 'missing';
      const planConfirmedState: WorkCaseRecordState = obj.hasPlanConfirmedAt ? 'recorded' : 'missing';
      const closureRequestedState: WorkCaseRecordState = obj.hasClosureRequestedAt ? 'recorded' : 'missing';
      const verificationEvidenceState: WorkCaseRecordState = obj.hasVerificationEvidence ? 'recorded' : 'missing';
      const closureEvidenceState: WorkCaseRecordState = obj.hasClosureEvidence ? 'recorded' : 'missing';
      const closeDecisionFields = [
        { label: t('objectList.successCriteria'), state: successCriteriaState },
        { label: t('objectList.planConfirmedAt'), state: planConfirmedState },
        { label: t('objectList.closureRequestedAt'), state: closureRequestedState },
        { label: t('objectList.verificationEvidence'), state: verificationEvidenceState },
        { label: t('objectList.closureEvidence'), state: closureEvidenceState },
      ];
      const closedIntegrityFields = closeDecisionFields;
      const hasClosedIntegrityIssue = isClosedWorkCase && closedIntegrityFields.some((field) => field.state === 'missing');
      const shouldShowCloseDecision = needsCloseDecision || hasClosedIntegrityIssue;
      const closeDecisionTitle = hasClosedIntegrityIssue && !needsCloseDecision
        ? t('objectList.closureIssue')
        : t('objectList.closeDecision');
      const visibleCloseFields = isClosedWorkCase ? closedIntegrityFields : closeDecisionFields;
      const successCriteriaTotal = obj.successCriteriaTotal ?? 0;
      const successCriteriaDone = obj.successCriteriaDone ?? 0;
      const executionTotal = obj.executionItemTotal ?? executionItems.length;
      const executionDone = obj.executionItemDone ?? executionItems.filter((item) => item.status === 'done').length;
      const executionBlocked = obj.executionItemBlocked ?? executionItems.filter((item) => item.status === 'blocked' || item.blockingReason).length;
      const missingCloseFields = visibleCloseFields.filter((field) => field.state === 'missing').length;
      const summaryTone: WorkCaseCardSummaryTone = hasClosedIntegrityIssue || executionBlocked > 0
        ? 'risk'
        : needsCloseDecision
          ? 'gate'
          : successCriteriaTotal > 0 && successCriteriaDone === successCriteriaTotal
            ? 'ready'
            : 'default';
      const primarySummary = shouldShowCloseDecision
        ? {
            label: closeDecisionTitle,
            value: missingCloseFields > 0 ? String(missingCloseFields) : getWorkCaseRecordStateLabel('recorded', t),
            helper: needsCloseDecision ? getStatus(obj.status) : undefined,
            tone: summaryTone,
          }
        : executionBlocked > 0
          ? {
              label: t('objectList.planExecutionRisk'),
              value: String(executionBlocked),
              helper: t('objectList.planExecutionItems'),
              tone: 'risk' as const,
            }
          : {
              label: t('objectList.planExecutionItems'),
              value: executionTotal > 0 ? `${executionDone}/${executionTotal}` : '—',
              helper: successCriteriaTotal > 0 ? `${t('objectList.successCriteria')} ${successCriteriaDone}/${successCriteriaTotal}` : undefined,
              tone: successCriteriaTotal > 0 && successCriteriaDone === successCriteriaTotal ? 'ready' as const : 'default' as const,
            };

      return (
        <ObjectCardFrame
          key={obj.id}
          obj={obj}
          locale={locale}
          onOpen={openObject}
          showNonActiveReason={false}
          displayStatus={progressGroup ?? 'unknown'}
        >
          <WorkCaseProgressSignal progressGroup={progressGroup} progressStep={progressStep} locale={locale} t={t} />
          <div onClick={(event) => event.stopPropagation()} className="min-w-0 cursor-default">
            <WorkCaseCardSummary {...primarySummary} />
          </div>

          {shouldShowCloseDecision && (
            <div
              onClick={(event) => event.stopPropagation()}
              className={`min-w-0 cursor-default rounded-md border p-3 ${
              hasClosedIntegrityIssue
                ? 'border-red-500/30 bg-red-500/5'
                : 'border-sky-500/25 bg-sky-500/5'
            }`}
            >
              <div className="mb-2 flex min-w-0 items-center gap-1.5">
                <ClipboardCheck size={13} className={`shrink-0 ${hasClosedIntegrityIssue ? 'text-red-400' : 'text-sky-400'}`} />
                <span className="ldvh-caption-strong min-w-0 truncate">{closeDecisionTitle}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {visibleCloseFields.map((field) => (
                  <WorkCaseRecordItem key={field.label} label={field.label} state={field.state} t={t} />
                ))}
              </div>
            </div>
          )}

          <div
            onClick={(event) => event.stopPropagation()}
            className="min-w-0 cursor-default rounded-md border border-ldvh-border bg-ldvh-bg p-3"
          >
            <div className="mb-2 flex min-w-0 items-center justify-between gap-2">
              <span className="ldvh-caption-strong inline-flex min-w-0 items-center gap-1.5 truncate">
                <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-sky-400" aria-hidden="true" />
                {t('objectList.planExecutionItems')}
              </span>
              {executionItems.length > 0 && (
                <span className="ldvh-caption shrink-0 text-ldvh-text-secondary">
                  {t('objectList.executionFlowCount', { status: t('objectList.executionFlowDone'), count: String(executionDone) })}
                  {' · '}
                  {t('objectList.executionFlowCount', { status: t('objectList.executionFlowBlocked'), count: String(executionBlocked) })}
                </span>
              )}
            </div>
            {executionItems.length > 0 && (
              <div className="mb-2 min-w-0">
                <ExecutionFlowBar items={executionItems} t={t} getStatus={getStatus} compact />
              </div>
            )}
            <div className="min-w-0 divide-y divide-ldvh-border/60">
              {visibleExecutionItems.length > 0 ? (
                visibleExecutionItems.map((item) => {
                  const tone = getExecutionFlowTone(item);
                  const label = getExecutionFlowLabel(item, t, getStatus);
                  return (
                    <div key={item.id} className="flex min-w-0 items-center gap-2 py-2">
                      <ExecutionFlowMarker tone={tone} label={label} compact />
                      <div className="min-w-0 flex-1">
                        <span className="ldvh-body block min-w-0 truncate">{getLocalizedObjectTitle(item, locale)}</span>
                        <span className="ldvh-meta-muted block min-w-0 truncate">
                          {[item.role || item.id, label].filter(Boolean).join(' · ')}
                        </span>
                      </div>
                      {item.blockingReason && (
                        <CircleAlert size={13} className="shrink-0 text-amber-400" />
                      )}
                    </div>
                  );
                })
              ) : (
                <p className="ldvh-body-muted rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-3 py-4 text-center">
                  {t('objectList.noExecutionItems')}
                </p>
              )}
            </div>
            {moreCount > 0 && (
              <span className="ldvh-caption mt-2 block">{t('objectList.moreExecutionItems', { count: String(moreCount) })}</span>
            )}
          </div>
        </ObjectCardFrame>
      );
    }

    if (currentType === 'adr') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} showNonActiveReason={false}>
          <AdrCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    if (currentType === 'pitfall') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} showNonActiveReason={false}>
          <ObjectSignalBadges source={obj} type={obj.type} locale={locale} />
          <PitfallCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    if (currentType === 'spark') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} showNonActiveReason={false}>
          <ObjectSignalBadges source={obj} type={obj.type} locale={locale} />
          <SparkCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    return (
      <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
        <ObjectSignalBadges source={obj} type={obj.type} locale={locale} />
      </ObjectCardFrame>
    );
  };

  return (
    <div className="ldvh-page-frame">
      <div className="sticky top-0 z-20 -mx-4 -mt-4 mb-4 flex min-h-8 flex-wrap items-center justify-between gap-3 border-b border-ldvh-border bg-ldvh-bg/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:-mt-6 sm:px-6">
        <div className="min-w-0 flex-1">
          {supportsPriorityNavigation && (
            <div className="mb-2 flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-2">
              {isPriorityApplicable ? (
                <ObjectPriorityFilter
                  activePriority={activePriority}
                  onChange={handlePriorityChange}
                  options={priorityOptions}
                  loading={loading}
                />
              ) : (
                <p className="ldvh-meta text-ldvh-text-secondary">{t('objectList.priorityNotApplicable')}</p>
              )}
              {currentType === 'workcase' && (
                <ExecutionFlowLegend t={t} getStatus={getStatus} />
              )}
            </div>
          )}
          <div className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5">
            {currentType === 'workcase' ? (
              <>
                <span className="ldvh-meta shrink-0 text-ldvh-text-secondary">{t('objectList.progressGroupFilter')}</span>
                <WorkCaseProgressFilter
                  activeGroup={activeProgressGroup}
                  onChange={handleProgressGroupChange}
                  options={progressOptions}
                  total={statusTotal}
                  loading={loading}
                />
              </>
            ) : (
              <>
                {currentType === 'spark' && <span className="ldvh-meta shrink-0 text-ldvh-text-secondary">{t('objectList.lifecycleFilter')}</span>}
                <ObjectStatusFilter
                  type={currentType}
                  activeStatus={activeStatus}
                  onChange={handleStatusChange}
                  options={statusOptions}
                  total={statusTotal}
                  loading={loading}
                />
              </>
            )}
          </div>
        </div>
        {!supportsPriorityNavigation && currentType === 'workcase' && (
          <ExecutionFlowLegend t={t} getStatus={getStatus} />
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : error ? (
        <div className="py-20 text-center">
          <p className="ldvh-body-muted">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
        </div>
      ) : typeNotIntegrated ? (
        <div className="mx-auto max-w-2xl rounded-lg border border-amber-500/30 bg-amber-500/10 px-5 py-8 text-center">
          <CircleAlert className="mx-auto mb-3 text-amber-400" size={24} />
          <p className="ldvh-card-title text-amber-300">{t('objectList.typeNotIntegrated')}</p>
          <p className="ldvh-body-muted mt-2">{typeNotIntegrated.message || typeNotIntegrated.title}</p>
        </div>
      ) : visibleItems.length === 0 ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t('objectList.noObjects', { type: currentType })}
        </div>
      ) : (
        <div className="ldvh-section-grid">
          {visibleItems.map((obj) => renderObjectCard(obj))}
        </div>
      )}
    </div>
  );
}
