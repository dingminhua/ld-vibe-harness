import { useEffect, useState, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowRight, Circle, CircleAlert, CircleCheck, CircleMinus, CirclePlay, ClipboardList, Clock3, Lightbulb, ListChecks, ShieldCheck, Target } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import WorkCaseProgressFilter from '@/components/WorkCaseProgressFilter';
import WorkCaseProgressTrack from '@/components/WorkCaseProgressTrack';
import ObjectPriorityFilter from '@/components/ObjectPriorityFilter';
import PriorityIcon from '@/components/PriorityIcon';
import CopyPathButton from '@/components/CopyPathButton';
import SummaryText from '@/components/SummaryText';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { WorkCaseCriteriaList, WORKCASE_CRITERIA_SURFACE_CLASS } from '@/components/WorkCaseCriteriaList';
import { fetchObjectDetail, fetchObjects, type FactCoverageStatus, type FactListProblem, type ObjectDetail, type ObjectItem, type ObjectStatusOption, type WorkCaseClosureProposalCard, type WorkCaseClosureTerminalCard, type WorkCaseContributionTarget, type WorkCaseExecutionItem, type WorkCaseProgressOption, type WorkCaseSparkSuggestionCard } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getFieldLabel, getFieldValueLabel, getLocalizedObjectTitle, getObjectStatusLocale } from '@/i18n/locales';
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

const WORKCASE_SECTION_ICON_SIZE = 14;
/** Shared vertical rhythm between a semantic card title and its first body block. */
const WORKCASE_CARD_TITLE_BODY_GAP_CLASS = 'mt-1.5';

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
      <p className={`ldvh-card-decision-body whitespace-pre-wrap break-words ${
        isMissing ? 'text-red-400' : 'text-ldvh-text-secondary/75'
      }`}
      >
        {reason.text}
      </p>
    </div>
  );
}

/** 计划判断输入区：与认知中心收件箱"待批准计划"决定依据区同源消费（02 §7.5）。 */
// eslint-disable-next-line react-refresh/only-export-components
export function WorkCasePlanConfirmationContent({
  mode = 'card',
  goal,
  scope,
  successCriteria,
  successCriterionDefinitions,
  workItems,
  creationReviews,
  executionAuthorization,
  executionApproval,
  isBlocked = false,
  blockingSummary,
  t,
}: {
  mode?: 'card' | 'decision';
  goal?: string;
  scope?: string;
  successCriteria?: string[];
  successCriterionDefinitions?: unknown;
  workItems?: unknown;
  creationReviews?: unknown;
  executionAuthorization?: unknown;
  executionApproval?: unknown;
  isBlocked?: boolean;
  blockingSummary?: string;
  t: Translate;
}) {
  const { locale } = useI18n();
  const criteria = successCriteria?.filter((criterion) => criterion.trim()) ?? [];
  const showsCompleteGateMaterial = mode === 'decision';

  return (
    <div className="grid min-w-0 gap-2">
      {isBlocked && <WorkCaseBlockingNotice blockingSummary={blockingSummary} t={t} />}
      <WorkCaseGoalSection goal={goal} t={t} />
      {showsCompleteGateMaterial && (
        <GateOneFieldSection fieldKey="scope" value={scope} valid={isNonEmptyString(scope)} locale={locale} />
      )}
      <section className={WORKCASE_CRITERIA_SURFACE_CLASS}>
        <div className="flex min-w-0 items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <ListChecks size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-blue-500 dark:text-blue-400" aria-hidden="true" />
            <h3 className="ldvh-card-decision-title text-blue-700/85 dark:text-blue-200/85">{t('objectDetail.workcaseSuccessCriteria')}</h3>
          </div>
          {criteria.length > 0 && (
            <span className="ldvh-meta shrink-0 text-blue-700/60 dark:text-blue-200/65">
              {t('objectList.workcaseCriteriaCount', { count: String(criteria.length) })}
            </span>
          )}
        </div>
        {isValidCriterionDefinitions(successCriterionDefinitions) ? (
          showsCompleteGateMaterial ? (
            <GateOneValue value={successCriterionDefinitions} locale={locale} depth={0} />
          ) : (
            <WorkCaseCriteriaList
              className={WORKCASE_CARD_TITLE_BODY_GAP_CLASS}
              items={successCriterionDefinitions.map((criterion) => ({
                key: String(criterion.criterion_id),
                statement: String(criterion.statement),
              }))}
            />
          )
        ) : successCriterionDefinitions !== undefined ? (
          <div className="min-w-0">
            <p className="ldvh-caption mt-1.5 text-red-400">{t('objectList.workcaseGateFieldMalformed')}</p>
            <GateOneValue value={successCriterionDefinitions} locale={locale} depth={0} />
          </div>
        ) : criteria.length > 0 ? (
          <div className="min-w-0">
            <p className="ldvh-caption mt-1.5 text-red-400">{t('objectList.workcaseGateFieldMalformed')}</p>
            <WorkCaseCriteriaList
              className={WORKCASE_CARD_TITLE_BODY_GAP_CLASS}
              items={criteria.map((criterion, index) => ({
                key: `${index}-${criterion}`,
                statement: criterion,
              }))}
            />
          </div>
        ) : (
          <p className="ldvh-caption mt-1.5 text-red-400">{t('objectList.workcaseFieldMissing')}</p>
        )}
      </section>
      {showsCompleteGateMaterial && (
        <>
          <GateOneFieldSection
            fieldKey="work_items"
            value={workItems}
            valid={isValidGateWorkItems(workItems)}
            locale={locale}
          />
          <GateOneFieldSection
            fieldKey="creation_reviews"
            value={creationReviews}
            valid={isValidGateReviews(creationReviews)}
            locale={locale}
          />
        </>
      )}
      <ExecutionAuthorizationCard
        authorization={executionAuthorization}
        locale={locale}
        compact={mode === 'card'}
      />
      {showsCompleteGateMaterial && executionApproval !== undefined && (
        <GateOneFieldSection
          fieldKey="execution_approval"
          value={executionApproval}
          valid={isValidExecutionApproval(executionApproval)}
          locale={locale}
        />
      )}
    </div>
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && Boolean(value.trim());
}

function isStringArray(value: unknown, allowEmpty = true): value is string[] {
  return Array.isArray(value)
    && (allowEmpty || value.length > 0)
    && value.every(isNonEmptyString);
}

function isValidGateWorkItems(value: unknown): boolean {
  return Array.isArray(value) && value.length > 0 && value.every((candidate) => {
    if (!isRecord(candidate)) return false;
    return isNonEmptyString(candidate.item_id)
      && isNonEmptyString(candidate.goal)
      && isNonEmptyString(candidate.expected_result)
      && isNonEmptyString(candidate.status)
      && (candidate.depends_on === undefined || isStringArray(candidate.depends_on))
      && (candidate.approach_summary === undefined || isNonEmptyString(candidate.approach_summary))
      && (candidate.template_keys === undefined || isStringArray(candidate.template_keys));
  });
}

function isValidCriterionDefinitions(value: unknown): value is Array<Record<string, unknown>> {
  return Array.isArray(value) && value.length > 0 && value.every((candidate) => (
    isRecord(candidate)
    && isNonEmptyString(candidate.criterion_id)
    && isNonEmptyString(candidate.statement)
  ));
}

function isValidGateReviews(value: unknown): boolean {
  return Array.isArray(value) && value.length > 0 && value.every((candidate) => {
    if (!isRecord(candidate)) return false;
    return isNonEmptyString(candidate.reviewer)
      && isNonEmptyString(candidate.reviewed_at)
      && typeof candidate.subject_version === 'number'
      && isNonEmptyString(candidate.scope)
      && isNonEmptyString(candidate.conclusion)
      && (candidate.feedback === undefined || isStringArray(candidate.feedback))
      && (candidate.controller_resolution === undefined || isNonEmptyString(candidate.controller_resolution));
  });
}

function isValidExecutionAuthorization(value: unknown): value is Record<string, unknown> {
  if (!isRecord(value)) return false;
  const actions = value.authorized_actions;
  return Array.isArray(actions) && actions.length > 0 && actions.every((candidate) => {
    if (!isRecord(candidate)) return false;
    return ['action_id', 'summary', 'target_scope', 'effect_scope', 'risk_summary', 'rollback_summary']
      .every((key) => isNonEmptyString(candidate[key]))
      && isStringArray(candidate.rule_refs, false);
  })
    && isNonEmptyString(value.action_ceiling)
    && isStringArray(value.prohibited_actions, false)
    && isNonEmptyString(value.allowed_adjustments)
    && isNonEmptyString(value.verification_and_rollback)
    && isNonEmptyString(value.out_of_bounds_handling)
    && (value.human_prerequisites === undefined || isStringArray(value.human_prerequisites, false));
}

function isValidExecutionApproval(value: unknown): boolean {
  return isRecord(value)
    && typeof value.subject_version === 'number'
    && isNonEmptyString(value.approved_at)
    && isNonEmptyString(value.summary)
    && isNonEmptyString(value.baseline_fingerprint)
    && isStringArray(value.source_refs, false);
}

function GateOneFieldSection({
  fieldKey,
  value,
  valid,
  locale,
  title,
}: {
  fieldKey: string;
  value: unknown;
  valid: boolean;
  locale: string;
  title?: string;
}) {
  const { t } = useI18n();
  const missing = value === undefined || value === null || value === '';
  return (
    <section className={`min-w-0 rounded-lg border px-3 py-2.5 ${valid ? 'border-slate-300/55 bg-slate-500/[0.025] dark:border-slate-600/55' : 'border-red-400/30 bg-red-500/[0.035]'}`}>
      <div className="flex min-w-0 items-center justify-between gap-2">
        <h3 className={`ldvh-card-decision-title min-w-0 ${valid ? 'text-slate-700/85 dark:text-slate-200/85' : 'text-red-500 dark:text-red-300'}`}>
          {title ?? getFieldLabel(fieldKey, locale)}
        </h3>
        {!valid && (
          <span className="ldvh-meta shrink-0 text-red-400">
            {missing ? t('objectList.workcaseFieldMissing') : t('objectList.workcaseGateFieldMalformed')}
          </span>
        )}
      </div>
      {!missing && <GateOneValue value={value} locale={locale} depth={0} />}
    </section>
  );
}

function ExecutionAuthorizationCard({
  authorization,
  locale,
  compact,
}: {
  authorization: unknown;
  locale: string;
  compact: boolean;
}) {
  const { t } = useI18n();
  if (!isValidExecutionAuthorization(authorization)) {
    return (
      <GateOneFieldSection
        fieldKey="execution_authorization"
        value={authorization}
        valid={false}
        locale={locale}
        title={t('objectDetail.workcaseExecutionAuthorization')}
      />
    );
  }

  const actions = authorization.authorized_actions as Record<string, unknown>[];
  const prohibitedActions = authorization.prohibited_actions as string[];
  const prerequisites = (authorization.human_prerequisites ?? []) as string[];

  return (
    <section className="min-w-0 rounded-lg border border-amber-400/35 bg-amber-500/[0.035] px-3 py-2.5 dark:border-amber-300/30">
      <div className="flex min-w-0 items-center gap-2">
        <ShieldCheck size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-amber-600 dark:text-amber-300" aria-hidden="true" />
        <h3 className="ldvh-card-decision-title min-w-0 text-amber-800/90 dark:text-amber-100/90">
          {t('objectDetail.workcaseExecutionAuthorization')}
        </h3>
      </div>
      <p className="ldvh-caption mt-1.5 text-amber-900/65 dark:text-amber-100/65">
        {t('objectDetail.workcaseExecutionAuthorizationBoundary')}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5" aria-label={t('objectDetail.workcaseExecutionAuthorization')}>
        <span className="ldvh-meta rounded-full border border-emerald-400/30 bg-emerald-500/[0.06] px-2 py-0.5 text-emerald-700 dark:text-emerald-200">
          {t('objectList.workcaseAuthorizedActionCount', { count: String(actions.length) })}
        </span>
        <span className="ldvh-meta rounded-full border border-rose-400/30 bg-rose-500/[0.06] px-2 py-0.5 text-rose-700 dark:text-rose-200">
          {t('objectList.workcaseProhibitedActionCount', { count: String(prohibitedActions.length) })}
        </span>
        {prerequisites.length > 0 && (
          <span className="ldvh-meta rounded-full border border-violet-400/30 bg-violet-500/[0.06] px-2 py-0.5 text-violet-700 dark:text-violet-200">
            {t('objectList.workcasePrerequisiteCount', { count: String(prerequisites.length) })}
          </span>
        )}
      </div>
      {!compact && (
        <div className="mt-2.5 grid min-w-0 gap-2.5">
          <section className="min-w-0 rounded-md border border-amber-400/20 bg-amber-500/[0.025] px-2.5 py-2">
            <p className="ldvh-meta text-amber-800/70 dark:text-amber-100/70">{getFieldLabel('authorized_actions', locale)}</p>
            <ul className="mt-1.5 grid min-w-0 gap-2">
              {actions.map((action) => (
                <li key={String(action.action_id)} className="min-w-0 rounded-md border border-amber-400/20 bg-ldvh-surface/45 px-2.5 py-2 dark:bg-ldvh-surface/20">
                  <p className="ldvh-card-decision-title text-ldvh-text-primary">{String(action.summary)}</p>
                  <AuthorizationCardText fieldKey="target_scope" value={String(action.target_scope)} locale={locale} />
                  <AuthorizationCardText fieldKey="effect_scope" value={String(action.effect_scope)} locale={locale} />
                  <div className="mt-1.5 grid min-w-0 grid-cols-2 gap-1.5 border-t border-ldvh-border/60 pt-1.5">
                    <AuthorizationCardText fieldKey="risk_summary" value={String(action.risk_summary)} locale={locale} />
                    <AuthorizationCardText fieldKey="rollback_summary" value={String(action.rollback_summary)} locale={locale} />
                  </div>
                  <AuthorizationCardList fieldKey="rule_refs" items={action.rule_refs as string[]} locale={locale} />
                </li>
              ))}
            </ul>
          </section>
          <section className="grid min-w-0 gap-2 rounded-md border border-ldvh-border/65 bg-ldvh-surface/35 px-2.5 py-2">
            <AuthorizationCardText fieldKey="action_ceiling" value={String(authorization.action_ceiling)} locale={locale} />
            <AuthorizationCardList fieldKey="prohibited_actions" items={prohibitedActions} locale={locale} emphasis="warning" />
            <AuthorizationCardText fieldKey="allowed_adjustments" value={String(authorization.allowed_adjustments)} locale={locale} />
            <AuthorizationCardText fieldKey="verification_and_rollback" value={String(authorization.verification_and_rollback)} locale={locale} />
            <AuthorizationCardText fieldKey="out_of_bounds_handling" value={String(authorization.out_of_bounds_handling)} locale={locale} />
            {prerequisites.length > 0 && <AuthorizationCardList fieldKey="human_prerequisites" items={prerequisites} locale={locale} />}
          </section>
        </div>
      )}
    </section>
  );
}

function AuthorizationCardText({ fieldKey, value, locale }: { fieldKey: string; value: string; locale: string }) {
  return (
    <div className="min-w-0">
      <p className="ldvh-meta text-ldvh-text-secondary/70">{getFieldLabel(fieldKey, locale)}</p>
      <SummaryText value={value} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-card-decision-body mt-1 text-ldvh-text-secondary" />
    </div>
  );
}

function AuthorizationCardList({
  fieldKey,
  items,
  locale,
  emphasis = 'default',
}: {
  fieldKey: string;
  items: string[];
  locale: string;
  emphasis?: 'default' | 'warning';
}) {
  const bulletClass = emphasis === 'warning' ? 'bg-rose-500/75' : 'bg-ldvh-text-secondary/55';
  return (
    <div className="min-w-0">
      <p className="ldvh-meta text-ldvh-text-secondary/70">{getFieldLabel(fieldKey, locale)}</p>
      <ul className="mt-1 grid min-w-0 gap-1">
        {items.map((item) => (
          <li key={item} className="flex min-w-0 items-start gap-1.5">
            <span className={`mt-[0.5rem] h-1 w-1 shrink-0 rounded-full ${bulletClass}`} aria-hidden="true" />
            <SummaryText value={item} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-card-decision-body min-w-0 text-ldvh-text-secondary" />
          </li>
        ))}
      </ul>
    </div>
  );
}

function GateOneValue({ value, locale, depth }: { value: unknown; locale: string; depth: number }) {
  if (typeof value === 'string') {
    return <SummaryText value={value} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-card-decision-body mt-1.5 !text-ldvh-text-secondary" />;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return <p className="ldvh-card-decision-body mt-1.5 font-mono text-ldvh-text-secondary">{String(value)}</p>;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return <p className="ldvh-caption mt-1.5 text-red-400">[]</p>;
    return (
      <ul className="mt-1.5 grid min-w-0 gap-1.5">
        {value.map((entry, index) => (
          <li key={index} className={`min-w-0 ${isRecord(entry) ? 'rounded-md border border-ldvh-border/60 px-2.5 py-2' : 'flex items-start gap-2'}`}>
            {!isRecord(entry) && <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-ldvh-text-secondary/55" aria-hidden="true" />}
            <GateOneValue value={entry} locale={locale} depth={depth + 1} />
          </li>
        ))}
      </ul>
    );
  }
  if (isRecord(value)) {
    return (
      <dl className={`mt-1.5 grid min-w-0 gap-2 ${depth === 0 ? 'grid-cols-2' : ''}`}>
        {Object.entries(value).map(([key, entry]) => (
          <div key={key} className="min-w-0">
            <dt className="ldvh-meta break-words text-ldvh-text-secondary/70">{getFieldLabel(key, locale)}</dt>
            <dd className="min-w-0"><GateOneValue value={entry} locale={locale} depth={depth + 1} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return <p className="ldvh-caption mt-1.5 break-all font-mono text-red-400">{String(value)}</p>;
}

function WorkCaseGoalSection({
  goal,
  t,
  emphasis = 'primary',
}: {
  goal?: string;
  t: Translate;
  emphasis?: 'primary' | 'supporting';
}) {
  const surfaceClass = emphasis === 'primary'
    ? 'border-violet-400/45 border-l-violet-400 bg-violet-100/70 dark:bg-violet-950/50'
    : 'border-violet-400/20 border-l-violet-400/70 bg-violet-500/[0.025] dark:bg-violet-950/20';

  return (
    <section className={`min-w-0 rounded-md border border-l-2 px-3.5 py-3 ${surfaceClass}`}>
      <div className="flex min-w-0 items-center gap-2">
        <Target size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-violet-500 dark:text-violet-400" aria-hidden="true" />
        <h3 className="ldvh-card-decision-title text-violet-700/85 dark:text-violet-200/85">{t('objectDetail.workcaseResponsibility')}</h3>
      </div>
      {goal?.trim() ? (
        <div className={`ldvh-caption ${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} w-full break-words`}>
          <SummaryText
            value={goal}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="ldvh-card-decision-body text-violet-950/65 dark:text-violet-100/75"
          />
        </div>
      ) : (
        <p className={`ldvh-caption ${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} text-red-400`}>{t('objectList.workcaseFieldMissing')}</p>
      )}
    </section>
  );
}

/** waiting_on 提示块：与认知中心收件箱"已阻塞待处置"决定依据区同源消费（02 §7.5）。 */
// eslint-disable-next-line react-refresh/only-export-components
export function WorkCaseWaitingOnNotice({ waitingOn }: { waitingOn?: string }) {
  const { locale } = useI18n();
  if (!waitingOn?.trim()) return null;
  return (
    <div className="min-w-0 rounded-md border border-amber-400/30 border-l-2 border-l-amber-400 bg-amber-500/[0.045] px-2.5 py-2">
      <div className="flex min-w-0 items-center gap-2">
        <Clock3 size={14} className="shrink-0 text-amber-500 dark:text-amber-400" aria-hidden="true" />
        <div className="ldvh-card-decision-title min-w-0 text-amber-700/80 dark:text-amber-200/80">
          {getFieldLabel('waiting_on', locale)}
        </div>
      </div>
      <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} break-words`}>
        <SummaryText
          value={waitingOn}
          collapseThreshold={Number.MAX_SAFE_INTEGER}
          className="ldvh-card-decision-body [&_p]:my-0 text-amber-950/70 dark:text-amber-100/75"
        />
      </div>
    </div>
  );
}

/** 阻塞说明提示块：与认知中心收件箱"已阻塞待处置"决定依据区同源消费（02 §7.5）。 */
// eslint-disable-next-line react-refresh/only-export-components
export function WorkCaseBlockingNotice({
  blockingSummary,
  t,
}: {
  blockingSummary?: string;
  t: Translate;
}) {
  const { locale } = useI18n();
  const label = getFieldLabel('blocking_summary', locale);
  return (
    <div
      role="status"
      aria-label={label}
      className="min-w-0 rounded-md border border-rose-400/30 border-l-2 border-l-rose-400 bg-rose-500/[0.045] px-2.5 py-2"
    >
      <div className="flex min-w-0 items-center gap-2">
        <CircleAlert size={14} className="shrink-0 text-rose-500 dark:text-rose-400" aria-hidden="true" />
        <div className="ldvh-card-decision-title min-w-0 text-rose-700/80 dark:text-rose-200/80">
          {label}
        </div>
      </div>
      {blockingSummary?.trim() ? (
        <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} break-words`}>
          <SummaryText
            value={blockingSummary}
            collapseThreshold={Number.MAX_SAFE_INTEGER}
            className="ldvh-card-decision-body [&_p]:my-0 text-rose-950/70 dark:text-rose-100/75"
          />
        </div>
      ) : (
        <p className={`ldvh-card-decision-body ${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} text-red-400`}>{t('objectList.workcaseFieldMissing')}</p>
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
  const currentStep = progressStep ? WORKCASE_PROGRESS_STEP_ORDER.indexOf(progressStep) : -1;
  const planRevising = phase === 'plan_revising';
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
      {isBlocked && <WorkCaseBlockingNotice blockingSummary={blockingSummary} t={t} />}
      {isBlocked && <WorkCaseWaitingOnNotice waitingOn={waitingOn} />}
      <WorkCaseGoalSection goal={goal} t={t} emphasis="supporting" />
      <section className="min-w-0 rounded-md border border-sky-400/25 border-l-2 border-l-sky-400 bg-sky-500/[0.035] px-3.5 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <CirclePlay size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-sky-500 dark:text-sky-400" aria-hidden="true" />
          <h3 className="ldvh-card-decision-title text-sky-700/85 dark:text-sky-200/85">{t('objectDetail.workcaseCurrentSnapshot')}</h3>
        </div>

        <WorkCaseProgressTrack
          phase={phase}
          step={progressStep}
          showUnavailable
        />

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
                        ? 'text-sky-950/70 dark:text-sky-100/75'
                        : completed
                          ? 'text-emerald-950/70 dark:text-emerald-100/75'
                          : blocked
                            ? 'text-amber-950/70 dark:text-amber-100/75'
                            : cancelled
                              ? 'text-slate-400 dark:text-slate-500 line-through'
                              : 'text-slate-700/70 dark:text-slate-200/70';
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
                                className={`ldvh-card-decision-body [&_p]:my-0 ${itemTextTone}`}
                              />
                            </div>
                            {blocked && (
                              item.blockingReason?.trim() ? (
                                <div className="mt-0.5 break-words">
                                  <SummaryText
                                    value={item.blockingReason}
                                    collapseThreshold={Number.MAX_SAFE_INTEGER}
                                    className="ldvh-card-decision-body [&_p]:my-0 text-amber-950/70 dark:text-amber-100/75"
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

        {!isBlocked && waitingOn?.trim() && (
          <div className="mt-2.5">
            <WorkCaseWaitingOnNotice waitingOn={waitingOn} />
          </div>
        )}

      </section>
    </div>
  );
}

/** Closure inputs reuse the same subdued status-card grammar as progressing work items. */
const PROPOSED_OUTCOME_NOTICE_CLASS: Record<string, string> = {
  completed: 'border-emerald-400/25 border-l-emerald-400 bg-emerald-500/5',
  partial: 'border-amber-400/25 border-l-amber-400 bg-amber-500/5',
  'not-achieved': 'border-red-400/25 border-l-red-400 bg-red-500/5',
  cancelled: 'border-zinc-400/25 border-l-zinc-400 bg-zinc-500/5',
};

const PROPOSED_OUTCOME_TEXT_CLASS: Record<string, string> = {
  completed: 'text-emerald-700/85 dark:text-emerald-200/85',
  partial: 'text-amber-700/85 dark:text-amber-200/85',
  'not-achieved': 'text-red-700/85 dark:text-red-200/85',
  cancelled: 'text-zinc-600/85 dark:text-zinc-300/85',
};

const PROPOSED_OUTCOME_BODY_CLASS: Record<string, string> = {
  completed: 'text-emerald-950/70 dark:text-emerald-100/75',
  partial: 'text-amber-950/70 dark:text-amber-100/75',
  'not-achieved': 'text-red-950/70 dark:text-red-100/75',
  cancelled: 'text-zinc-700/70 dark:text-zinc-200/70',
};

const CLOSURE_PROPOSAL_NOTICE_CLASS = 'border-amber-400/25 border-l-amber-400 bg-amber-500/5';
const CLOSURE_PROPOSAL_TEXT_CLASS = 'text-amber-700/80 dark:text-amber-200/80';
const CLOSURE_PROPOSAL_BODY_CLASS = 'text-amber-900/75 dark:text-amber-100/80';

const PROPOSED_DISPOSITION_NOTICE_CLASS: Record<string, string> = {
  route_existing: 'border-emerald-400/25 border-l-emerald-400 bg-emerald-500/5',
  suggest_spark: 'border-amber-400/25 border-l-amber-400 bg-amber-500/5',
  accept_stop: 'border-cyan-400/25 border-l-cyan-400 bg-cyan-500/5',
};

/** A literal quarter-filled circle keeps the "partial" outcome legible at card-icon size. */
function QuarterCircle({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" width={WORKCASE_SECTION_ICON_SIZE} height={WORKCASE_SECTION_ICON_SIZE} className={className} aria-hidden="true">
      <circle cx="8" cy="8" r="6.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M8 8V1.75A6.25 6.25 0 0 1 14.25 8Z" fill="currentColor" />
    </svg>
  );
}

function WorkCaseOutcomeNotice({
  outcome,
  dispositionSummary,
  mode,
}: {
  outcome: WorkCaseClosureProposalCard['proposedOutcome'];
  dispositionSummary: string;
  mode: 'proposal' | 'terminal';
}) {
  const { t, locale } = useI18n();
  const tone = mode === 'proposal'
    ? CLOSURE_PROPOSAL_TEXT_CLASS
    : PROPOSED_OUTCOME_TEXT_CLASS[outcome] ?? 'text-ldvh-text-secondary';
  const bodyTone = mode === 'proposal'
    ? CLOSURE_PROPOSAL_BODY_CLASS
    : PROPOSED_OUTCOME_BODY_CLASS[outcome] ?? 'text-ldvh-text-secondary/80';
  const surface = mode === 'proposal'
    ? CLOSURE_PROPOSAL_NOTICE_CLASS
    : PROPOSED_OUTCOME_NOTICE_CLASS[outcome] ?? 'border-ldvh-border/70 border-l-ldvh-text-secondary/35 bg-ldvh-bg/60';
  const outcomeLabel = mode === 'proposal'
    ? getFieldValueLabel('proposed_outcome', outcome, locale)
    : null;
  const heading = mode === 'proposal'
    ? t('objectList.workcaseClosureProposal')
    : t('objectList.workcaseTerminalDisposition');
  const outcomeIcon = mode === 'proposal'
    ? <ClipboardList size={WORKCASE_SECTION_ICON_SIZE} className={`shrink-0 ${CLOSURE_PROPOSAL_TEXT_CLASS}`} aria-hidden="true" />
    : outcome === 'completed'
      ? <CircleCheck size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-emerald-500 dark:text-emerald-400" aria-hidden="true" />
      : outcome === 'partial'
        ? <QuarterCircle className="shrink-0 text-amber-500 dark:text-amber-400" />
        : outcome === 'not-achieved'
          ? <CircleAlert size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-red-500 dark:text-red-400" aria-hidden="true" />
          : <CircleMinus size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-zinc-500 dark:text-zinc-400" aria-hidden="true" />;
  return (
    <section className={`min-w-0 rounded-md border border-l-2 px-3.5 py-3 ${surface}`}>
      <div className="flex min-w-0 items-center gap-2">
        {outcomeIcon}
        <span className={`ldvh-card-decision-title min-w-0 ${tone}`}>
          {heading}
        </span>
        {outcomeLabel && <span className={`ldvh-meta ml-auto shrink-0 ${tone}`}>{outcomeLabel}</span>}
      </div>
      <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} min-w-0 break-words`}>
        <SummaryText value={dispositionSummary} collapseThreshold={Number.MAX_SAFE_INTEGER} className={`ldvh-card-decision-body [&_p]:my-0 ${bodyTone}`} />
      </div>
    </section>
  );
}

/** Plain text color for residual disposition labels (no chip frame). */
const PROPOSED_DISPOSITION_TEXT_CLASS: Record<string, string> = {
  route_existing: 'text-emerald-700/85 dark:text-emerald-200/85',
  suggest_spark: 'text-amber-700/85 dark:text-amber-200/85',
  accept_stop: 'text-cyan-700/85 dark:text-cyan-200/85',
};

const PROPOSED_DISPOSITION_BODY_CLASS: Record<string, string> = {
  route_existing: 'text-emerald-950/70 dark:text-emerald-100/75',
  suggest_spark: 'text-amber-950/70 dark:text-amber-100/75',
  accept_stop: 'text-cyan-950/70 dark:text-cyan-100/75',
};

function WorkCaseSparkSuggestions({ suggestions }: { suggestions: WorkCaseSparkSuggestionCard[] }) {
  const { t, locale } = useI18n();
  if (suggestions.length === 0) return null;
  return (
    <ul className="grid min-w-0 gap-2">
      {suggestions.map((suggestion) => (
        <li key={suggestion.suggestionId} className="min-w-0 rounded-md border border-amber-400/25 border-l-2 border-l-amber-400 bg-amber-500/5 px-3.5 py-3">
          <div className="flex min-w-0 items-center gap-2">
            <Lightbulb size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-amber-500 dark:text-amber-400" aria-hidden="true" />
            <span className="ldvh-card-decision-title min-w-0 text-amber-700/85 dark:text-amber-200/85">
              {getFieldValueLabel('proposed_disposition', 'suggest_spark', locale)}
            </span>
          </div>
          <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} min-w-0 break-words`}>
            <SummaryText value={suggestion.summary} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-card-decision-body [&_p]:my-0 text-amber-950/70 dark:text-amber-100/75" />
          </div>
          {suggestion.restrictionReason && <div className="ldvh-caption mt-1 text-amber-950/65 dark:text-amber-100/70">{t('objectList.workcaseRestrictionReason')}: {suggestion.restrictionReason}</div>}
          {suggestion.impactSummary && <div className="ldvh-caption mt-0.5 text-amber-950/65 dark:text-amber-100/70">{t('objectList.workcaseImpactSummary')}: {suggestion.impactSummary}</div>}
          {suggestion.resumeCondition && <div className="ldvh-caption mt-0.5 text-amber-950/65 dark:text-amber-100/70">{t('objectList.workcaseResumeCondition')}: {suggestion.resumeCondition}</div>}
          <div className="ldvh-caption mt-0.5 text-amber-950/65 dark:text-amber-100/70">{t('objectList.workcaseFollowUpSummary')}: {suggestion.followUpSummary}</div>
        </li>
      ))}
    </ul>
  );
}

/** 关闭判断输入区：与认知中心收件箱"待确认关闭"决定依据区同源消费（02 §7.5）。 */
// eslint-disable-next-line react-refresh/only-export-components
export function WorkCaseClosureConfirmationContent({
  goal,
  closureProposal,
}: {
  goal?: string;
  closureProposal?: WorkCaseClosureProposalCard;
}) {
  const { t, locale } = useI18n();
  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} emphasis="supporting" />
      {closureProposal ? (
        <>
          <WorkCaseOutcomeNotice outcome={closureProposal.proposedOutcome} dispositionSummary={closureProposal.dispositionSummary} mode="proposal" />
          {closureProposal.residualDecisions.length > 0 && (
            <ul className="grid min-w-0 gap-2">
              {closureProposal.residualDecisions.map((decision) => (
                <li key={decision.residualId} className={`min-w-0 rounded-md border border-l-2 px-3.5 py-3 ${PROPOSED_DISPOSITION_NOTICE_CLASS[decision.proposedDisposition] ?? 'border-ldvh-border/70 border-l-ldvh-text-secondary/35 bg-ldvh-bg/60'}`}>
                  <div className="flex min-w-0 items-center gap-2">
                    {decision.proposedDisposition === 'accept_stop' ? (
                      <CircleMinus size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-cyan-500 dark:text-cyan-400" aria-hidden="true" />
                    ) : decision.proposedDisposition === 'suggest_spark' ? (
                      <Lightbulb size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-amber-500 dark:text-amber-400" aria-hidden="true" />
                    ) : (
                      <ArrowRight size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-emerald-600 dark:text-emerald-200" aria-hidden="true" />
                    )}
                    <span className={`ldvh-card-decision-title min-w-0 ${PROPOSED_DISPOSITION_TEXT_CLASS[decision.proposedDisposition] ?? 'text-ldvh-text-secondary'}`}>
                      {getFieldValueLabel('proposed_disposition', decision.proposedDisposition, locale)}
                    </span>
                  </div>
                  <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} min-w-0 break-words`}>
                    <SummaryText value={decision.summary} collapseThreshold={Number.MAX_SAFE_INTEGER} className={`ldvh-card-decision-body [&_p]:my-0 ${PROPOSED_DISPOSITION_BODY_CLASS[decision.proposedDisposition] ?? 'text-ldvh-text-secondary'}`} />
                  </div>
                  {decision.routeTarget && <WorkCaseContributionTargetRow target={decision.routeTarget} locale={locale} showStatus={false} compact />}
                </li>
              ))}
            </ul>
          )}
          <WorkCaseSparkSuggestions suggestions={closureProposal.sparkSuggestions} />
        </>
      ) : (
        <section role="status" className="min-w-0 rounded-md border border-red-400/25 border-l-2 border-l-red-400 bg-red-500/5 px-2.5 py-2">
          <p className="ldvh-card-decision-body text-red-500 dark:text-red-300">{t('objectList.workcaseClosureProposalMissing')}</p>
        </section>
      )}
    </div>
  );
}

function WorkCaseClosedContent({ goal, terminal }: { goal?: string; terminal?: WorkCaseClosureTerminalCard }) {
  const { t, locale } = useI18n();
  return (
    <div className="grid min-w-0 gap-2">
      <WorkCaseGoalSection goal={goal} t={t} emphasis="supporting" />
      {terminal ? (
        <>
          <WorkCaseOutcomeNotice outcome={terminal.outcome} dispositionSummary={terminal.dispositionSummary} mode="terminal" />
          {terminal.routedTo.length > 0 && (
            <ul className="grid min-w-0 gap-2">
              {terminal.routedTo.map((target) => (
                <li key={`route/${target.factTypeKey}/${target.objectId}`} className={`min-w-0 rounded-md border border-l-2 px-3.5 py-3 ${PROPOSED_DISPOSITION_NOTICE_CLASS.route_existing}`}>
                  <div className="flex min-w-0 items-center gap-2">
                    <ArrowRight size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-emerald-600 dark:text-emerald-200" aria-hidden="true" />
                    <span className={`ldvh-card-decision-title min-w-0 ${PROPOSED_DISPOSITION_TEXT_CLASS.route_existing}`}>
                      {getFieldValueLabel('proposed_disposition', 'route_existing', locale)}
                    </span>
                  </div>
                  <WorkCaseContributionTargetRow target={target} locale={locale} showStatus={false} compact />
                </li>
              ))}
            </ul>
          )}
          {terminal.acceptedStop.length > 0 && (
            <ul className="grid min-w-0 gap-2">
              {terminal.acceptedStop.map((residual) => (
                <li key={residual.residualId} className={`min-w-0 rounded-md border border-l-2 px-3.5 py-3 ${PROPOSED_DISPOSITION_NOTICE_CLASS.accept_stop}`}>
                  <div className="flex min-w-0 items-center gap-2">
                    <CircleMinus size={WORKCASE_SECTION_ICON_SIZE} className="shrink-0 text-cyan-500 dark:text-cyan-400" aria-hidden="true" />
                    <span className={`ldvh-card-decision-title min-w-0 ${PROPOSED_DISPOSITION_TEXT_CLASS.accept_stop}`}>
                      {getFieldValueLabel('proposed_disposition', 'accept_stop', locale)}
                    </span>
                  </div>
                  <div className={`${WORKCASE_CARD_TITLE_BODY_GAP_CLASS} min-w-0 break-words`}>
                    <SummaryText value={residual.summary} collapseThreshold={Number.MAX_SAFE_INTEGER} className="ldvh-card-decision-body [&_p]:my-0 text-cyan-950/70 dark:text-cyan-100/75" />
                  </div>
                </li>
              ))}
            </ul>
          )}
          <WorkCaseSparkSuggestions suggestions={terminal.sparkSuggestions} />
        </>
      ) : (
        <section role="status" className="min-w-0 rounded-md border border-red-400/25 border-l-2 border-l-red-400 bg-red-500/5 px-2.5 py-2">
          <p className="ldvh-card-decision-body text-red-500 dark:text-red-300">{t('objectList.workcaseClosureProposalMissing')}</p>
        </section>
      )}
    </div>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function WorkCaseContributionsContent({
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
      <h3 className="ldvh-card-decision-title">{t('objectList.workcaseContributions')}</h3>
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
function WorkCaseContributionTargetRow({ target, locale, showStatus = true, compact = false }: { target: WorkCaseContributionTarget; locale: string; showStatus?: boolean; compact?: boolean }) {
  const { t } = useI18n();
  const [detail, setDetail] = useState<ObjectDetail | null>(null);
  const [readState, setReadState] = useState<'loading' | 'resolved' | 'unavailable'>('loading');

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setReadState('loading');
    fetchObjectDetail(target.factTypeKey, target.objectId)
      .then((value) => {
        if (!cancelled) {
          setDetail(value);
          setReadState('resolved');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDetail(null);
          setReadState('unavailable');
        }
      });
    return () => { cancelled = true; };
  }, [target.factTypeKey, target.objectId]);

  const readMeta = getFactReadMeta(detail?.data);
  const readable = Boolean(detail && isReadableFact(readMeta));
  const title = contributionTargetTitle(detail, readMeta, locale);
  const targetStatus = showStatus && readable && typeof detail?.data.status === 'string'
    ? getObjectStatusLocale(target.factTypeKey, detail.data.status, locale)
    : null;
  const readStatus = readable
    ? null
    : readState === 'loading'
      ? t('objectList.workcaseTargetReading')
      : getFieldValueLabel('read_status', readMeta.readStatus ?? 'unreadable', locale);
  const typeColor = CATEGORY_COLORS[target.factTypeKey] || CATEGORY_COLORS.other;
  return (
    <div
      className={`flex min-w-0 items-center gap-2 rounded-md px-1.5 text-left ${compact ? 'pb-1 pt-1.5' : 'py-2'}`}
    >
      <ObjectTypeIcon type={target.factTypeKey} size={13} className="-translate-y-0.5 shrink-0" style={{ color: typeColor }} />
      <span className="ldvh-meta-primary min-w-0 flex-1 whitespace-normal break-words text-left">
        {title}
      </span>
      <span className="ldvh-meta-muted shrink-0">{target.objectId}</span>
      {targetStatus && <span className="ldvh-meta-muted shrink-0">{targetStatus}</span>}
      {readStatus && <span className="ldvh-meta-muted shrink-0">{readStatus}</span>}
    </div>
  );
}

function contributionTargetTitle(detail: ObjectDetail | null, readMeta: ReturnType<typeof getFactReadMeta>, locale: string): string {
  if (!detail || !isReadableFact(readMeta)) return '—';
  return getLocalizedObjectTitle(detail.data as { title?: string; title_en?: string; title_zh?: string }, locale);
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


// eslint-disable-next-line react-refresh/only-export-components
export function ObjectCardFrame({
  obj,
  locale,
  onOpen,
  children,
  showNonActiveReason = true,
  displayStatus,
}: {
  obj: ObjectItem;
  locale: string;
  onOpen: (objId: string) => void;
  children?: ReactNode;
  showNonActiveReason?: boolean;
  displayStatus?: string;
}) {
  const { t } = useI18n();
  const presentedStatus = displayStatus ?? obj.status;
  const titleAccentClass = getTitleAccentClass(presentedStatus);
  const typeColor = CATEGORY_COLORS[obj.type] || CATEGORY_COLORS.other;
  const nonActiveReason = getNonActiveReason(obj, t);
  return (
    <div
      className="flex min-w-0 flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left"
    >
      <div className="flex min-w-0 items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="ldvh-meta-muted min-w-0 truncate">{obj.id}</span>
          <PriorityIcon source={obj} type={obj.type} locale={locale} size="sm" />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusBadge status={presentedStatus} statusLabel={getObjectStatusLocale(obj.type, presentedStatus, locale)} objectType={obj.type} />
          {/* List Cards only have a stable object identity, not an exact-read source path. */}
          <CopyPathButton
            path={obj.id}
            label={t('common.copyObjectId')}
            copiedLabel={t('common.copiedObjectId')}
          />
        </div>
      </div>
      <div
        className={`-mx-1 flex min-w-0 items-center gap-1.5 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 text-left ring-1 ring-inset ring-ldvh-border/50 ${titleAccentClass}`}
      >
        <ObjectTypeIcon type={obj.type} size={14} className="shrink-0" style={{ color: typeColor }} />
        <h2 className="ldvh-card-title min-w-0 flex-1 whitespace-normal break-words">
          <button
            type="button"
            onClick={() => onOpen(obj.id)}
            className="text-left transition-colors hover:text-ldvh-accent focus-visible:outline-none focus-visible:text-ldvh-accent focus-visible:underline"
          >
            {getLocalizedObjectTitle(obj, locale)}
          </button>
        </h2>
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
  content,
}: {
  tone: 'routed' | 'implemented' | 'discarded' | 'retired';
  content: string;
}) {
  const styles = {
    routed: {
      panel: 'border-emerald-400/25 border-l-emerald-400 bg-emerald-500/5',
      body: 'text-emerald-700/75 dark:text-emerald-200/75',
    },
    implemented: {
      panel: 'border-emerald-400/25 border-l-emerald-400 bg-emerald-500/5',
      body: 'text-emerald-700/75 dark:text-emerald-200/75',
    },
    discarded: {
      panel: 'border-red-400/25 border-l-red-400 bg-red-500/5',
      body: 'text-red-700/75 dark:text-red-200/75',
    },
    retired: {
      panel: 'border-zinc-400/25 border-l-zinc-400 bg-zinc-500/5',
      body: 'text-zinc-600/75 dark:text-zinc-300/75',
    },
  }[tone];

  return (
    <section
      onClick={(event) => event.stopPropagation()}
      className={`min-w-0 cursor-default rounded-md border border-l-2 px-3.5 py-3 ${styles.panel}`}
    >
      <div className="ldvh-terminal-fact-content min-w-0 break-words">
        <SummaryText value={content} collapseThreshold={Number.MAX_SAFE_INTEGER} className={`ldvh-card-decision-body [&_p]:my-0 ${styles.body}`} />
      </div>
    </section>
  );
}

function SparkTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const reason = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');
  const tone = obj.status === 'discarded' ? 'discarded' : obj.status === 'implemented' ? 'implemented' : 'routed';

  return (
    <TerminalFactPanel tone={tone} content={formatReasonText(reason)} />
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
    <TerminalFactPanel tone="discarded" content={formatReasonText(disposition)} />
  );
}

function PitfallCardContent({ obj }: { obj: ObjectItem }) {
  if (obj.status === 'discarded') return <PitfallTerminalCardContent obj={obj} />;
  return null;
}

function AdrTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const disposition = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');

  return (
    <TerminalFactPanel tone="retired" content={formatReasonText(disposition)} />
  );
}

function AdrCardContent({ obj }: { obj: ObjectItem }) {
  if (obj.status === 'retired') return <AdrTerminalCardContent obj={obj} />;
  return null;
}

function StudyTerminalCardContent({ obj }: { obj: ObjectItem }) {
  const { t } = useI18n();
  const disposition = obj.disposition_summary?.trim() || t('objectList.dispositionMissing');

  return (
    <TerminalFactPanel tone="retired" content={formatReasonText(disposition)} />
  );
}

function StudyCardContent({ obj }: { obj: ObjectItem }) {
  if (obj.status === 'retired') return <StudyTerminalCardContent obj={obj} />;
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
          >
            <>
              <WorkCasePlanConfirmationContent
                mode="card"
                goal={obj.goal}
                successCriteria={obj.successCriteria}
                successCriterionDefinitions={obj.success_criterion_definitions}
                executionAuthorization={obj.execution_authorization}
                isBlocked={obj.status === 'blocked'}
                blockingSummary={obj.blocking_summary}
                t={t}
              />
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
          <PitfallCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    if (currentType === 'spark') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} showNonActiveReason={false}>
          <SparkCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    if (currentType === 'study') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} showNonActiveReason={false}>
          <StudyCardContent obj={obj} />
        </ObjectCardFrame>
      );
    }

    return (
      <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
      </ObjectCardFrame>
    );
  };

  return (
    <div className="ldvh-page-frame">
      <div className="sticky top-0 z-20 -mx-6 -mt-6 mb-4 flex min-h-8 flex-wrap items-center justify-between gap-3 border-b border-ldvh-border bg-ldvh-bg/95 px-6 py-3 backdrop-blur">
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
              ? 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300'
              : coverageStatus === 'partial' || coverageStatus === 'type_not_integrated'
              ? 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300'
              : 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-300'
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
            <p className="ldvh-card-title text-red-700 dark:text-red-300">{t('objectList.workcaseCoverageUnavailable')}</p>
            <p className="ldvh-meta mt-2 break-words text-red-700/80 dark:text-red-300/80">{error}</p>
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
