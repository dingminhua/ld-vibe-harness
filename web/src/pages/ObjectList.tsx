import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowRight, Circle, CircleAlert, CircleCheck, CircleMinus, CirclePlay, PauseCircle } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import WorkCaseProgressFilter from '@/components/WorkCaseProgressFilter';
import ObjectPriorityFilter from '@/components/ObjectPriorityFilter';
import CopyPathButton from '@/components/CopyPathButton';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import PriorityIcon from '@/components/PriorityIcon';
import SummaryText from '@/components/SummaryText';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { fetchObjectDetail, fetchObjects, type FactCoverageStatus, type FactListProblem, type ObjectDetail, type ObjectItem, type ObjectStatusOption, type WorkCaseClosureProposalCard, type WorkCaseClosureTerminalCard, type WorkCaseContributionTarget, type WorkCaseExecutionItem, type WorkCaseProgressOption, type WorkCaseSparkSuggestionCard } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getFieldValueLabel, getLocalizedObjectTitle, getObjectStatusLocale, getTypeLabel } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { getFactReadMeta, isReadableFact } from '@/utils/factReadMeta';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';
import {
  WORKCASE_PROGRESS_STEP_ORDER,
  isWorkCaseProgressGroup,
  type WorkCaseProgressGroup,
  type WorkCaseProgressStep,
} from '@/shared/workcaseStatus';

type Translate = ReturnType<typeof useI18n>['t'];
type StatusReason = { label: string; text: string; missing?: boolean };

const TITLE_ACCENT_CLASS: Record<string, string> = {
  active: 'border-emerald-400/80',
  human_plan_confirming: 'border-violet-400/80',
  plan_revising: 'border-sky-400/80',
  executing: 'border-emerald-400/80',
  controller_checking: 'border-blue-400/80',
  independent_reviewing: 'border-indigo-400/80',
  closure_preparing: 'border-sky-400/80',
  human_closure_confirming: 'border-violet-400/80',
  plan_confirmation: 'border-violet-400/80',
  progressing: 'border-sky-400/80',
  closure_confirmation: 'border-violet-400/80',
  accepted: 'border-emerald-400/70',
  draft: 'border-amber-400/75',
  proposed: 'border-amber-400/75',
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

function statusRequiresDisposition(obj: ObjectItem): boolean {
  return obj.status === 'retired'
    || obj.status === 'discarded'
    || obj.status === 'routed'
    || (obj.fact_type_key === 'spark' && obj.status === 'implemented');
}

function getNonActiveReason(obj: ObjectItem, t: Translate): StatusReason | null {
  if (!statusRequiresDisposition(obj)) return null;
  const disposition = obj.disposition_summary;
  if (typeof disposition === 'string' && disposition.trim()) {
    const text = formatReasonText(disposition);
    if (text) return { label: t('objectList.disposition'), text };
  }
  return {
    label: t('objectList.missingReason'),
    text: t('objectList.missingReasonText'),
    missing: true,
  };
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
          <h3 className="ldvh-card-title">{t('objectList.successCriteria')}</h3>
          {criteria.length > 0 && (
            <span className="ldvh-meta-muted shrink-0">{t('objectList.workcaseCriteriaCount', { count: String(criteria.length) })}</span>
          )}
        </div>
        {criteria.length > 0 ? (
          <ul className="mt-2 grid min-w-0 gap-0">
            {criteria.map((criterion, index) => (
              <li key={`${index}-${criterion}`} className="flex min-w-0 items-start gap-2">
                <span
                  aria-hidden="true"
                  className="mt-3.5 h-1 w-1 shrink-0 rounded-full bg-ldvh-text-secondary/70"
                />
                <div className="ldvh-caption min-w-0 flex-1 break-words">
                  <SummaryText
                    value={criterion}
                    collapseThreshold={Number.MAX_SAFE_INTEGER}
                    className="text-[13px] leading-5 text-ldvh-text-secondary"
                  />
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="ldvh-caption mt-1.5 text-red-400">{t('objectList.workcaseFieldMissing')}</p>
        )}
      </section>
    </div>
  );
}

function WorkCaseGoalSection({ goal, t }: { goal?: string; t: Translate }) {
  return (
    <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-ldvh-accent/45 bg-ldvh-bg/65 px-3.5 py-3">
      <h3 className="ldvh-card-title">{t('objectList.workcaseGoal')}</h3>
      {goal?.trim() ? (
        <div className="ldvh-caption mt-1.5 max-w-[82ch] break-words">
          <SummaryText
            value={goal}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="text-[13px] leading-5 text-ldvh-text-secondary"
          />
        </div>
      ) : (
        <p className="ldvh-caption mt-1.5 text-red-400">{t('objectList.workcaseFieldMissing')}</p>
      )}
    </section>
  );
}

function WorkCaseBlockingNotice({
  blockingSummary,
  t,
}: {
  blockingSummary?: string;
  t: Translate;
}) {
  return (
    <div
      role="status"
      aria-label={t('objectList.workcaseBlockingReason')}
      className="min-w-0 rounded-md border border-amber-400/25 border-l-2 border-l-amber-400 bg-amber-500/5 px-2.5 py-2"
    >
      <div className="flex min-w-0 items-center gap-2">
        <CircleAlert size={14} className="shrink-0 text-amber-500 dark:text-amber-400" aria-hidden="true" />
        <div className="ldvh-meta-primary min-w-0 text-amber-700/70 dark:text-amber-300/70">
          {t('objectList.workcaseBlockingReason')}
        </div>
      </div>
      {blockingSummary?.trim() ? (
        <div className="mt-0.5 break-words">
          <SummaryText
            value={blockingSummary}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="[&_p]:my-0 text-[13px] leading-5 text-amber-800 dark:text-amber-200"
          />
        </div>
      ) : (
        <p className="ldvh-card-decision-body mt-0.5 text-red-400">{t('objectList.workcaseFieldMissing')}</p>
      )}
    </div>
  );
}

function WorkCaseProgressingContent({
  goal,
  phase,
  progressStep,
  executionItemsProjectionValid,
  executionItems,
  isBlocked,
  waitingOn,
  blockingSummary,
  t,
}: {
  goal?: string;
  phase?: string;
  progressStep: WorkCaseProgressStep | null;
  executionItemsProjectionValid: boolean;
  executionItems: WorkCaseExecutionItem[];
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
  const planRevising = phase === 'plan_revising';
  const currentPositionKnown = planRevising || currentStep >= 0;
  const currentStepLabel = planRevising
    ? t('objectList.workcasePlanRevising')
    : currentStep >= 0
      ? stepLabels[currentStep]
      : t('objectList.workcaseStageUnavailable');
  const itemExecution = progressStep === 'item_execution';
  const executionItemsActive = executionItems.filter((item) => item.status === 'in_progress' || item.status === 'blocked');
  const executionItemOpen = executionItems.filter((item) => ['pending', 'in_progress', 'blocked'].includes(item.status)).length;
  const displayedExecutionItems = itemExecution
    ? executionItems
      .map((item, index) => ({ item, index }))
      .sort((a, b) => {
        const rank = { completed: 0, in_progress: 1, blocked: 2, pending: 3, cancelled: 4 };
        return rank[a.item.status] - rank[b.item.status] || a.index - b.index;
      })
      .map(({ item }) => item)
    : executionItemsActive;
  const itemStageMismatch = executionItemsProjectionValid && currentStep >= 0 && (
    (itemExecution && executionItemsActive.length === 0 && executionItemOpen === 0)
    || (!itemExecution && executionItemOpen > 0)
  );
  const showWorkItems = planRevising
    || !executionItemsProjectionValid
    || itemExecution
    || executionItemsActive.length > 0
    || itemStageMismatch;

  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} />
      <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-sky-400/55 bg-ldvh-bg/65 px-3.5 py-3">
        <h3 className="ldvh-card-title">{t('objectList.workcaseCurrentProgress')}</h3>

        {planRevising && (
          <div className="ldvh-caption mt-2 flex min-w-0 items-center gap-2 text-sky-500 dark:text-sky-400">
            <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" aria-hidden="true" />
            <span className="min-w-0 break-words">{currentStepLabel}</span>
            <span className="ldvh-meta-muted">{t('objectList.workcaseOutsideProgressTrack')}</span>
          </div>
        )}
        {!currentPositionKnown && (
          <p role="status" className="ldvh-caption mt-2 text-red-400">{currentStepLabel}</p>
        )}

        {!planRevising && (
          <ol
            className="mt-2.5 grid min-w-0 grid-cols-4"
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
                    <span className="absolute left-0 right-1/2 top-2.5 z-0 h-px bg-ldvh-border" aria-hidden="true" />
                  )}
                  {index < WORKCASE_PROGRESS_STEP_ORDER.length - 1 && (
                    <span className="absolute left-1/2 right-0 top-2.5 z-0 h-px bg-ldvh-border" aria-hidden="true" />
                  )}
                  <span className={`ldvh-meta relative z-10 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border bg-ldvh-bg ${
                    isCurrent
                      ? 'border-sky-400/60 bg-sky-100 font-semibold text-sky-600 ring-2 ring-sky-500/10 dark:bg-sky-950 dark:text-sky-300'
                      : 'border-ldvh-border text-ldvh-text-secondary'
                  }`}>
                    {index + 1}
                  </span>
                  <div className="mt-1.5 min-w-0">
                    <div className={`ldvh-card-decision-body break-words leading-4 ${
                      isCurrent ? 'font-medium text-sky-400' : 'text-ldvh-text-secondary/80'
                    }`}>
                      {stepLabels[index]}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        )}

        {showWorkItems && (
          <div className="mt-2.5 border-t border-ldvh-border/70 pt-2.5">
            <div className="ldvh-caption-strong text-ldvh-text-secondary">
              {itemExecution ? t('objectList.workcaseItems') : t('objectList.workcaseCurrentItems')}
            </div>
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
                {displayedExecutionItems.length > 0 ? (
                  <ul className="mt-1.5 grid min-w-0 gap-2">
                    {displayedExecutionItems.map((item) => {
                      const blocked = item.status === 'blocked';
                      const completed = item.status === 'completed';
                      const inProgress = item.status === 'in_progress';
                      const cancelled = item.status === 'cancelled';
                      const itemTextTone = inProgress
                        ? 'text-sky-700 dark:text-sky-200'
                        : completed
                          ? 'text-emerald-700 dark:text-emerald-200'
                          : blocked
                            ? 'text-amber-800 dark:text-amber-200'
                            : cancelled
                              ? 'text-slate-400 dark:text-slate-500 line-through'
                              : 'text-slate-600 dark:text-slate-300';
                      const itemIdTone = inProgress
                        ? 'text-sky-600/70 dark:text-sky-300/70'
                        : completed
                          ? 'text-emerald-600/70 dark:text-emerald-300/70'
                          : blocked
                            ? 'text-amber-700/70 dark:text-amber-300/70'
                            : cancelled
                              ? 'text-slate-400/70 dark:text-slate-500/70 line-through'
                              : 'text-slate-500/75 dark:text-slate-400/75';
                      return (
                        <li
                          key={item.id}
                          className={`min-w-0 border-l-2 ${
                            inProgress
                              ? 'rounded-md border border-sky-400/35 border-l-sky-400 bg-sky-500/10 px-2.5 py-2'
                              : blocked
                                ? 'rounded-md border border-amber-400/25 border-l-amber-400 bg-amber-500/5 px-2.5 py-2'
                                : completed
                                  ? 'rounded-md border border-emerald-400/25 border-l-emerald-400 bg-emerald-500/5 px-2.5 py-2'
                                  : cancelled
                                    ? 'rounded-md border border-ldvh-border/70 border-l-ldvh-text-secondary/30 bg-ldvh-bg/60 px-2.5 py-2'
                                    : 'rounded-md border border-ldvh-border/70 border-l-ldvh-text-secondary/35 bg-ldvh-bg/60 px-2.5 py-2'
                          }`}
                        >
                          <div className="flex min-w-0 items-center gap-2">
                            <span className="flex h-4 w-4 shrink-0 items-center justify-center" aria-hidden="true">
                              {completed ? (
                                <CircleCheck size={14} className="text-emerald-500/85 dark:text-emerald-400" />
                              ) : inProgress ? (
                                <CirclePlay size={14} className="text-sky-500 dark:text-sky-400" />
                              ) : blocked ? (
                                <CircleAlert size={14} className="text-amber-500 dark:text-amber-400" />
                              ) : cancelled ? (
                                <CircleMinus size={14} className="text-ldvh-text-secondary/45" />
                              ) : (
                                <Circle size={14} className="text-ldvh-text-secondary/55" />
                              )}
                            </span>
                            <div className={`ldvh-meta-primary min-w-0 break-all ${itemIdTone}`}>
                              {item.id}
                            </div>
                          </div>
                          <div className="mt-0.5">
                            <div className="min-w-0 break-words">
                              <SummaryText
                                value={item.title}
                                collapseThreshold={Number.MAX_SAFE_INTEGER}
                                className={`[&_p]:my-0 text-[13px] leading-5 ${itemTextTone}`}
                              />
                            </div>
                            {blocked && (
                              item.blockingReason?.trim() ? (
                                <div className="mt-0.5 break-words">
                                  <SummaryText
                                    value={item.blockingReason}
                                    collapseThreshold={Number.MAX_SAFE_INTEGER}
                                    className="[&_p]:my-0 text-[13px] leading-5 text-amber-700 dark:text-amber-300"
                                  />
                                </div>
                              ) : (
                                <p className="ldvh-card-decision-body mt-0.5 text-red-400">
                                  {t('objectList.workcaseFieldMissing')}
                                </p>
                              )
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
          <div className="mt-2.5 min-w-0 rounded-md border border-ldvh-border/70 border-l-2 border-l-ldvh-text-secondary/35 bg-ldvh-bg/60 px-2.5 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <PauseCircle size={14} className="shrink-0 text-slate-500 dark:text-slate-400" aria-hidden="true" />
              <div className="ldvh-meta-primary min-w-0 text-slate-500/75 dark:text-slate-400/75">
                {t('objectList.workcaseWaitingOn')}
              </div>
            </div>
            <div className="mt-0.5 break-words">
              <SummaryText
                value={waitingOn}
                collapseThreshold={Number.MAX_SAFE_INTEGER}
                className="[&_p]:my-0 text-[13px] leading-5 text-slate-600 dark:text-slate-300"
              />
            </div>
          </div>
        )}

        {isBlocked && (
          <div className="mt-2.5">
            <WorkCaseBlockingNotice blockingSummary={blockingSummary} t={t} />
          </div>
        )}
      </section>
    </div>
  );
}

/** Weak signal colors for the proposed closure outcome; red is reserved for the failed outcome only. */
const PROPOSED_OUTCOME_CHIP_CLASS: Record<string, string> = {
  completed: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300',
  partial: 'border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-300',
  'not-achieved': 'border-red-500/30 bg-red-500/10 text-red-500 dark:text-red-300',
  cancelled: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-500 dark:text-zinc-300',
};

/** Left-bar + heading accent color per outcome (used for the section's colored edge). */
const PROPOSED_OUTCOME_ACCENT: Record<string, string> = {
  completed: 'border-l-emerald-500/70',
  partial: 'border-l-amber-500/70',
  'not-achieved': 'border-l-red-500/70',
  cancelled: 'border-l-zinc-500/70',
};

/** Plain text color for residual disposition labels (no chip frame). */
const PROPOSED_DISPOSITION_TEXT_CLASS: Record<string, string> = {
  route_existing: 'text-emerald-600 dark:text-emerald-300',
  suggest_spark: 'text-amber-600 dark:text-amber-300',
  accept_stop: 'text-zinc-500 dark:text-zinc-300',
};

function WorkCaseSparkSuggestions({ suggestions }: { suggestions: WorkCaseSparkSuggestionCard[] }) {
  const { t, locale } = useI18n();
  if (suggestions.length === 0) return null;
  return (
    <div className="mt-3 border-t border-ldvh-border/45 pt-2.5">
      <h4 className={`ldvh-caption-strong ${PROPOSED_DISPOSITION_TEXT_CLASS.suggest_spark}`}>
        {getFieldValueLabel('proposed_disposition', 'suggest_spark', locale)}
      </h4>
      <p className="ldvh-caption mt-0.5">{t('objectList.workcaseSparkSuggestions')}</p>
      <ul className="mt-1.5 grid min-w-0 gap-2">
        {suggestions.map((suggestion) => (
          <li key={suggestion.suggestionId} className="grid gap-0.5 rounded border border-ldvh-border/45 px-2.5 py-2">
            <span className="ldvh-caption-strong">{suggestion.summary}</span>
            {suggestion.restrictionReason && <span className="ldvh-caption">{t('objectList.workcaseRestrictionReason')}: {suggestion.restrictionReason}</span>}
            {suggestion.impactSummary && <span className="ldvh-caption">{t('objectList.workcaseImpactSummary')}: {suggestion.impactSummary}</span>}
            {suggestion.resumeCondition && <span className="ldvh-caption">{t('objectList.workcaseResumeCondition')}: {suggestion.resumeCondition}</span>}
            <span className="ldvh-caption">{t('objectList.workcaseFollowUpSummary')}: {suggestion.followUpSummary}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function WorkCaseClosureConfirmationContent({
  goal,
  closureProposal,
}: {
  goal?: string;
  closureProposal?: WorkCaseClosureProposalCard;
}) {
  const { t, locale } = useI18n();
  const outcome = closureProposal?.proposedOutcome;
  const accentClass = outcome
    ? (PROPOSED_OUTCOME_ACCENT[outcome] ?? 'border-l-violet-400/55')
    : 'border-l-red-500/70'; // missing-proposal state: red edge to signal the gap
  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} />
      <section className={`min-w-0 rounded-md border border-ldvh-border/80 border-l-2 ${accentClass} bg-ldvh-bg/65 px-3.5 py-3`}>
        {closureProposal ? (
          <>
            {/* Outcome: same size/weight as the "目标" label, wrapped in a colored frame */}
            <div className="flex min-w-0 items-baseline">
              <span
                className={`ldvh-card-title inline-flex items-center rounded border px-1.5 py-0.5 ${PROPOSED_OUTCOME_CHIP_CLASS[closureProposal.proposedOutcome] ?? 'border-ldvh-border/70 text-ldvh-text-primary'}`}
              >
                {getFieldValueLabel('proposed_outcome', closureProposal.proposedOutcome, locale)}
              </span>
            </div>
            {/* Disposition summary: matches the goal section's body (13px/secondary) */}
            <div className="ldvh-caption mt-1.5 max-w-[82ch] break-words">
              <SummaryText
                value={closureProposal.dispositionSummary}
                collapseThreshold={Number.MAX_SAFE_INTEGER}
                className="text-[13px] leading-5 text-ldvh-text-secondary"
              />
            </div>
            {closureProposal.residualDecisions.length > 0 && (
              <div className="mt-3 border-t border-ldvh-border/45 pt-2.5">
                <ul className="grid min-w-0 gap-1.5">
                  {closureProposal.residualDecisions.map((decision) => (
                    <li key={decision.residualId} className="grid min-w-0 gap-0.5 py-0.5">
                      <span
                        className={`ldvh-caption-strong ${PROPOSED_DISPOSITION_TEXT_CLASS[decision.proposedDisposition] ?? 'text-ldvh-text-secondary'}`}
                      >
                        {getFieldValueLabel('proposed_disposition', decision.proposedDisposition, locale)}
                      </span>
                      <span className="min-w-0 break-words">
                        <SummaryText
                          value={decision.summary}
                          collapseThreshold={Number.MAX_SAFE_INTEGER}
                          className="text-[13px] leading-5 text-ldvh-text-secondary"
                        />
                      </span>
                      {decision.routeTarget && <WorkCaseContributionTargetRow target={decision.routeTarget} locale={locale} showStatus={false} />}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <WorkCaseSparkSuggestions suggestions={closureProposal.sparkSuggestions} />
          </>
        ) : (
          <p role="status" className="ldvh-card-decision-body text-red-400">{t('objectList.workcaseClosureProposalMissing')}</p>
        )}
      </section>
    </div>
  );
}

function WorkCaseClosedContent({ goal, terminal }: { goal?: string; terminal?: WorkCaseClosureTerminalCard }) {
  const { t, locale } = useI18n();
  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} />
      {terminal ? (
        <section className={`min-w-0 rounded-md border border-ldvh-border/80 border-l-2 ${PROPOSED_OUTCOME_ACCENT[terminal.outcome] ?? 'border-l-zinc-500/70'} bg-ldvh-bg/65 px-3.5 py-3`}>
          <span className={`ldvh-card-title inline-flex rounded border px-1.5 py-0.5 ${PROPOSED_OUTCOME_CHIP_CLASS[terminal.outcome] ?? ''}`}>
            {getFieldValueLabel('proposed_outcome', terminal.outcome, locale)}
          </span>
          <SummaryText value={terminal.dispositionSummary} collapseThreshold={Number.MAX_SAFE_INTEGER} className="mt-1.5 text-[13px] leading-5 text-ldvh-text-secondary" />
          {terminal.routedTo.length > 0 && (
            <div className="mt-3 border-t border-ldvh-border/45 pt-2.5">
              <span className={`ldvh-caption-strong ${PROPOSED_DISPOSITION_TEXT_CLASS.route_existing}`}>
                {getFieldValueLabel('proposed_disposition', 'route_existing', locale)}
              </span>
              {terminal.routedTo.map((target) => <WorkCaseContributionTargetRow key={`route/${target.factTypeKey}/${target.objectId}`} target={target} locale={locale} showStatus={false} />)}
            </div>
          )}
          {terminal.acceptedStop.map((residual) => (
            <div key={residual.residualId} className="mt-2">
              <span className={`ldvh-caption-strong ${PROPOSED_DISPOSITION_TEXT_CLASS.accept_stop}`}>{getFieldValueLabel('proposed_disposition', 'accept_stop', locale)}</span>
              <p className="ldvh-caption">{residual.summary}</p>
            </div>
          ))}
          <WorkCaseSparkSuggestions suggestions={terminal.sparkSuggestions} />
        </section>
      ) : <p role="status" className="ldvh-card-decision-body text-red-400">{t('objectList.workcaseClosureProposalMissing')}</p>}
    </div>
  );
}

function WorkCaseContributionsContent({
  contributions,
  locale,
}: {
  contributions?: WorkCaseContributionTarget[];
  locale: string;
}) {
  const { t } = useI18n();
  if (!contributions || contributions.length === 0) return null;
  return (
    <section className="min-w-0 rounded-md border border-ldvh-border/80 border-l-2 border-l-ldvh-accent/45 bg-ldvh-bg/65 px-3.5 py-3">
      <h3 className="ldvh-card-title">{t('objectList.workcaseContributions')}</h3>
      <div className="mt-1.5 divide-y divide-ldvh-border/45">
        {contributions.map((target) => (
          <WorkCaseContributionTargetRow
            key={`${target.governedProjectId}/${target.factTypeKey}/${target.objectId}`}
            target={target}
            locale={locale}
          />
        ))}
      </div>
    </section>
  );
}

/** Targets resolve on demand exactly like the detail relation rows; titles are never duplicated into the Card. */
function WorkCaseContributionTargetRow({ target, locale, showStatus = true }: { target: WorkCaseContributionTarget; locale: string; showStatus?: boolean }) {
  const navigate = useNavigate();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    fetchObjectDetail(target.factTypeKey, target.objectId)
      .then((value) => { if (!cancelled) setDetail(value); })
      .catch(() => { if (!cancelled) setDetail(null); });
    return () => { cancelled = true; };
  }, [target.factTypeKey, target.objectId]);

  const title = contributionTargetTitle(detail, getFactReadMeta(detail?.data), locale);
  const targetStatus = showStatus && detail && isReadableFact(getFactReadMeta(detail.data)) && typeof detail.data.status === 'string'
    ? getObjectStatusLocale(target.factTypeKey, detail.data.status, locale)
    : null;
  const typeColor = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;
  const open = () => navigate(`/objects/${target.factTypeKey}/${target.objectId}`);
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    event.stopPropagation();
    open();
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => { event.stopPropagation(); open(); }}
      onKeyDown={onKeyDown}
      className="group flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-1.5 py-2 text-left transition-colors hover:bg-ldvh-border/25 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ldvh-accent/50"
    >
      <ObjectTypeIcon type={target.factTypeKey} size={13} className="shrink-0" style={{ color: typeColor }} />
      <span className="ldvh-meta-muted shrink-0">{getTypeLabel(target.factTypeKey, locale)}</span>
      <span className="ldvh-meta-primary min-w-0 flex-1 truncate group-hover:text-ldvh-accent">{title}</span>
      {targetStatus && <span className="ldvh-meta-muted shrink-0">{targetStatus}</span>}
    </div>
  );
}

function contributionTargetTitle(detail: ObjectDetail | null, readMeta: ReturnType<typeof getFactReadMeta>, locale: string): string {
  if (!detail || !isReadableFact(readMeta)) return '—';
  const source = detail.data as { title?: unknown; title_en?: unknown; title_zh?: unknown };
  const localized = locale === 'en' ? source.title_en : source.title_zh;
  if (typeof localized === 'string' && localized.trim()) return localized;
  return typeof source.title === 'string' && source.title.trim() ? source.title : '—';
}

function sortObjectsForList(items: ObjectItem[], _currentType: string): ObjectItem[] {
  return [...items].sort((a, b) => {
    const updatedDelta = Date.parse(b.updated || '') - Date.parse(a.updated || '');
    if (Number.isFinite(updatedDelta) && updatedDelta !== 0) return updatedDelta;
    const lexicalDelta = String(b.updated || '').localeCompare(String(a.updated || ''));
    if (lexicalDelta !== 0) return lexicalDelta;
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
  const isPlanConfirmation = presentedStatus === 'plan_confirmation';
  const typeColor = CATEGORY_COLORS[obj.type] || CATEGORY_COLORS.other;
  const nonActiveReason = getNonActiveReason(obj, t);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(obj.id)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(obj.id))}
      className={`group/card flex min-w-0 cursor-pointer flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left outline-none transition-colors hover:border-ldvh-accent/40 hover:bg-ldvh-panel/95 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ldvh-accent/70 ${isPlanConfirmation ? 'ldvh-card-plan-confirmation' : ''}`}
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
  const [coverageStatus, setCoverageStatus] = useState<FactCoverageStatus>('complete');
  const [coverageProblemCount, setCoverageProblemCount] = useState(0);
  const [coverageProblems, setCoverageProblems] = useState<FactListProblem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t, locale } = useI18n();

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
    setCoverageStatus('complete');
    setCoverageProblemCount(0);
    setCoverageProblems([]);
    fetchObjects(currentType, activeStatus ?? undefined, activePriority ?? undefined, activeProgressGroup ?? undefined)
      .then((result) => {
        const receivedItems = result.data?.items ?? [];
        const nextItems = currentType === 'spark' ? receivedItems.map(sparkViewItem) : receivedItems;
        setItems(nextItems);
        setStatusOptions(result.data?.statusOptions ?? []);
        setProgressOptions(result.data?.progressOptions ?? []);
        setPriorityOptions(result.data?.priorityOptions ?? []);
        setStatusTotal(result.data?.statusTotal ?? nextItems.length);
        setCoverageStatus(result.data?.coverage_status ?? 'complete');
        const nextCoverageProblems = result.data?.collection_issues ?? [];
        setCoverageProblems(nextCoverageProblems);
        setCoverageProblemCount(nextCoverageProblems.length);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentType, activeStatus, activePriority, activeProgressGroup]);

  const sortedItems = sortObjectsForList(items, currentType);

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
            <>
              <WorkCasePlanConfirmationContent goal={obj.goal} successCriteria={obj.successCriteria} t={t} />
              {obj.status === 'blocked' && (
                <WorkCaseBlockingNotice blockingSummary={obj.blocking_summary} t={t} />
              )}
            </>
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
              phase={obj.phase}
              progressStep={progressStep}
              executionItemsProjectionValid={obj.executionItemsProjectionValid ?? false}
              executionItems={obj.executionItems ?? []}
              isBlocked={obj.status === 'blocked'}
              waitingOn={obj.waiting_on}
              blockingSummary={obj.blocking_summary}
              t={t}
            />
          </ObjectCardFrame>
        );
      }
      if (progressGroup === 'closure_confirmation') {
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
            <>
              <WorkCaseClosureConfirmationContent goal={obj.goal} closureProposal={obj.closureProposal} />
              <WorkCaseContributionsContent contributions={obj.contributedTo} locale={locale} />
            </>
          </ObjectCardFrame>
        );
      }
      if (progressGroup === 'closed') {
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
            <>
              <WorkCaseClosedContent goal={obj.goal} terminal={obj.closureTerminal} />
              <WorkCaseContributionsContent contributions={obj.contributedTo} locale={locale} />
            </>
          </ObjectCardFrame>
        );
      }
      return (
        <ObjectCardFrame
          key={obj.id}
          obj={obj}
          locale={locale}
          onOpen={openObject}
          showNonActiveReason={false}
          displayStatus={progressGroup ?? 'unknown'}
        >
          {!progressGroup && (
            <p className="ldvh-card-decision-body rounded-md border border-red-500/30 bg-red-500/[0.07] px-3 py-2 text-red-400">
              {t('objectList.workcaseProgressGroupUnavailable')}
            </p>
          )}
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
                  coverageStatus={coverageStatus}
                />
              ) : (
                <p className="ldvh-meta text-ldvh-text-secondary">{t('objectList.priorityNotApplicable')}</p>
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
                  coverageStatus={coverageStatus}
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
      </div>

      {!loading && !error && (coverageStatus !== 'complete' || coverageProblemCount > 0) && (
        <div
          role="status"
          className={`mb-4 flex min-w-0 items-start gap-2 rounded-lg border px-4 py-3 ${
            coverageStatus === 'unavailable'
              ? 'border-red-500/30 bg-red-500/10 text-red-300'
              : coverageStatus === 'partial' || coverageStatus === 'type_not_integrated'
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-300'
              : 'border-sky-500/30 bg-sky-500/10 text-sky-300'
          }`}
        >
          <CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="ldvh-body">
              {coverageStatus === 'type_not_integrated'
                ? t('objectList.typeNotIntegrated')
                : coverageStatus === 'complete'
                ? t(currentType === 'workcase' ? 'objectList.workcaseObjectProblems' : 'objectList.objectProblems')
                : coverageStatus === 'partial'
                ? t(currentType === 'workcase' ? 'objectList.workcaseCoveragePartial' : 'objectList.coveragePartial')
                : t(currentType === 'workcase' ? 'objectList.workcaseCoverageUnavailable' : 'objectList.coverageUnavailable')}
            </p>
            {coverageProblemCount > 0 && (
              <details className="mt-2">
                <summary className="ldvh-meta cursor-pointer">
                  {t(currentType === 'workcase' ? 'objectList.workcaseCoverageProblemCount' : 'objectList.coverageProblemCount', { count: String(coverageProblemCount) })}
                </summary>
                <ul className="mt-2 grid gap-2">
                  {coverageProblems.map((problem, index) => {
                    const problemIdentity = problem.object_ref?.object_id
                      ?? t(currentType === 'workcase' ? 'objectList.workcaseCoverageCollectionScope' : 'objectList.coverageCollectionScope');
                    return (
                    <li key={`${problem.object_ref?.object_id ?? problem.scope ?? 'scope'}-${index}`} className="rounded-md border border-current/20 px-3 py-2">
                      <div className="ldvh-meta-primary break-all font-mono">
                        {problemIdentity}
                      </div>
                      {problem.read_status && (
                        <div className="ldvh-meta mt-1">
                          {getFieldValueLabel('read_status', problem.read_status, locale)}
                        </div>
                      )}
                      {(problem.message ?? problem.error ?? problem.code) && (
                        <p className="ldvh-meta mt-1 break-words">
                          {problem.message ?? problem.error ?? problem.code}
                        </p>
                      )}
                    </li>
                    );
                  })}
                </ul>
              </details>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
        </div>
      ) : error ? (
        currentType === 'workcase' ? (
          <div className="mx-auto max-w-2xl rounded-lg border border-red-500/30 bg-red-500/10 px-5 py-8 text-center">
            <CircleAlert className="mx-auto mb-3 text-red-400" size={24} />
            <p className="ldvh-card-title text-red-300">{t('objectList.workcaseCoverageUnavailable')}</p>
            <p className="ldvh-meta mt-2 break-words text-red-300/80">{error}</p>
          </div>
        ) : (
          <div className="py-20 text-center">
            <p className="ldvh-body-muted">{t('common.loadFailed')}</p>
            <p className="ldvh-meta text-red-400">{error}</p>
          </div>
        )
      ) : coverageStatus === 'type_not_integrated' ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t('objectList.typeNotIntegrated')}
        </div>
      ) : coverageStatus === 'unavailable' ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t(currentType === 'workcase' ? 'objectList.workcaseCoverageUnavailableEmpty' : 'objectList.coverageUnavailableEmpty')}
        </div>
      ) : sortedItems.length === 0 && coverageStatus === 'partial' ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t(currentType === 'workcase' ? 'objectList.workcaseCoveragePartialEmpty' : 'objectList.coveragePartialEmpty')}
        </div>
      ) : sortedItems.length === 0 && coverageProblemCount > 0 ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t(currentType === 'workcase' ? 'objectList.workcaseObjectProblemsEmpty' : 'objectList.objectProblemsEmpty')}
        </div>
      ) : sortedItems.length === 0 ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t('objectList.noObjects', { type: currentType })}
        </div>
      ) : (
        <div className="ldvh-section-grid">
          {sortedItems.map((obj) => renderObjectCard(obj))}
        </div>
      )}
    </div>
  );
}
