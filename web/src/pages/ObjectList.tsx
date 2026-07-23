import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowRight, CheckCircle2, CircleAlert, ClipboardCheck } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import ObjectPriorityFilter from '@/components/ObjectPriorityFilter';
import CopyPathButton from '@/components/CopyPathButton';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { ExecutionFlowBar, ExecutionFlowLegend, ExecutionFlowMarker } from '@/components/ExecutionFlowStatus';
import { fetchObjects, type ObjectItem, type ObjectStatusOption } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getLocalizedObjectTitle, getObjectStatusLocale } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';
import { getExecutionFlowLabel, getExecutionFlowTone, sortWorkCaseExecutionItems } from '@/utils/executionFlowStatus';
import {
  WORKCASE_STATUS_ORDER,
  isWorkCaseClosureConfirmingStatus,
} from '@/shared/workcaseStatus';

type Translate = ReturnType<typeof useI18n>['t'];
type WorkCaseRecordState = 'recorded' | 'missing';
type StatusReason = { label: string; text: string; missing?: boolean };
type WorkCaseCardSummaryTone = 'default' | 'risk' | 'ready' | 'gate';

const WORKCASE_STATUS_ORDER_INDEX = new Map<string, number>(
  WORKCASE_STATUS_ORDER.map((status, index) => [status, index]),
);

const TITLE_ACCENT_CLASS: Record<string, string> = {
  active: 'border-emerald-400/80',
  subagents_plan_reviewing: 'border-sky-400/80',
  human_plan_confirming: 'border-violet-400/80',
  executing: 'border-emerald-400/80',
  result_self_checking: 'border-blue-400/80',
  subagents_result_reviewing: 'border-indigo-400/80',
  human_closure_confirming: 'border-violet-400/80',
  accepted: 'border-emerald-400/70',
  review_needed: 'border-violet-400/80',
  verifying: 'border-blue-400/80',
  draft: 'border-amber-400/75',
  proposed: 'border-amber-400/75',
  planned: 'border-amber-400/75',
  pending: 'border-amber-400/75',
  open: 'border-amber-400/75',
  closed: 'border-zinc-500/50',
  resolved: 'border-zinc-500/50',
  routed: 'border-zinc-500/50',
  archived: 'border-zinc-500/50',
  discarded: 'border-red-400/75',
  superseded: 'border-zinc-500/50',
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

function getWorkCaseLifecycleOrder(status: string): number {
  if (status === 'review_needed') return WORKCASE_STATUS_ORDER_INDEX.get('human_closure_confirming') ?? 999;
  if (status === 'active' || status === 'draft') return WORKCASE_STATUS_ORDER_INDEX.get('executing') ?? 999;
  return WORKCASE_STATUS_ORDER_INDEX.get(status) ?? 999;
}

function sortObjectsForList(items: ObjectItem[], currentType: string): ObjectItem[] {
  if (currentType !== 'workcase') return items;
  return [...items].sort((a, b) => {
    const statusDelta = getWorkCaseLifecycleOrder(a.status) - getWorkCaseLifecycleOrder(b.status);
    if (statusDelta !== 0) return statusDelta;
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
}: {
  obj: ObjectItem;
  locale: string;
  onOpen: (objId: string) => void;
  children?: ReactNode;
  showNonActiveReason?: boolean;
}) {
  const { t } = useI18n();
  const titleAccentClass = getTitleAccentClass(obj.status);
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
          <StatusBadge status={obj.status} statusLabel={getObjectStatusLocale(obj.type, obj.status, locale)} objectType={obj.type} />
        </div>
      </div>
      <div
        className={`-mx-1 flex min-w-0 items-center gap-1.5 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 text-left ring-1 ring-inset ring-ldvh-border/50 transition-colors group-hover/card:bg-ldvh-bg/85 ${titleAccentClass}`}
      >
        <PriorityIcon source={obj} type={obj.type} locale={locale} size="sm" />
        <ObjectTypeIcon type={obj.type} size={14} className="shrink-0" style={{ color: typeColor }} />
        <span className="ldvh-card-title min-w-0 flex-1 whitespace-normal break-words leading-snug transition-colors group-hover/card:text-ldvh-accent">
          {getLocalizedObjectTitle(obj, locale)}
        </span>
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

function SparkFactPanel({
  tone,
  title,
  children,
}: {
  tone: 'open' | 'routed' | 'implemented' | 'discarded';
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
    <SparkFactPanel tone={tone}>
      <div className="min-w-0 whitespace-pre-line break-words text-[12px] leading-5 text-ldvh-text-secondary/75">
        {formatReasonText(reason)}
      </div>
    </SparkFactPanel>
  );
}

function SparkCardContent({ obj }: { obj: ObjectItem }) {
  if (hasSparkDiscardFact(obj) || hasSparkImplementedFact(obj) || hasSparkResolvedFact(obj)) return <SparkTerminalCardContent obj={obj} />;
  return null;
}

export default function ObjectList() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [statusOptions, setStatusOptions] = useState<ObjectStatusOption[]>([]);
  const [priorityOptions, setPriorityOptions] = useState<ObjectStatusOption[]>([]);
  const [statusTotal, setStatusTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'workcase';
  const statusParam = searchParams.get('status');
  const activeStatus = getEffectiveListStatus(currentType, statusParam);
  const priorityParam = searchParams.get('priority');
  const supportsPriorityNavigation = currentType === 'spark' || currentType === 'workcase';
  const activePriority = supportsPriorityNavigation && ['P0', 'P1', 'P2', 'P3'].includes(priorityParam ?? '')
    ? priorityParam
    : null;
  const isPriorityApplicable = currentType === 'spark'
    ? activeStatus === 'open' || activeStatus === null
    : currentType === 'workcase' && activeStatus !== 'closed';

  useEffect(() => {
    if (currentType !== 'spark' || !searchParams.has('category')) return;
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('category');
    setSearchParams(nextParams, { replace: true });
  }, [currentType, searchParams, setSearchParams]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setStatusOptions([]);
    setPriorityOptions([]);
    setStatusTotal(0);
    fetchObjects(currentType, activeStatus ?? undefined, activePriority ?? undefined)
      .then((result) => {
        const receivedItems = result.data?.items ?? [];
        const nextItems = currentType === 'spark' ? receivedItems.map(sparkViewItem) : receivedItems;
        setItems(nextItems);
        setStatusOptions(result.data?.statusOptions ?? []);
        setPriorityOptions(result.data?.priorityOptions ?? []);
        setStatusTotal(result.data?.statusTotal ?? nextItems.length);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentType, activeStatus, activePriority, reloadKey]);

  const sortedItems = sortObjectsForList(items, currentType);
  const typeNotIntegrated = sortedItems.find((item) => item.kind === 'type_not_integrated');
  const visibleItems = sortedItems.filter((item) => item.kind !== 'type_not_integrated');

  const handleStatusChange = (status: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    writeListStatusParam(currentType, nextParams, status);
    if ((currentType === 'spark' && status !== 'open' && status !== null)
      || (currentType === 'workcase' && status === 'closed')) {
      nextParams.delete('priority');
    }
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
      const executionItems = obj.executionItems ?? [];
      const sortedExecutionItems = sortWorkCaseExecutionItems(executionItems);
      const visibleExecutionItems = sortedExecutionItems.slice(0, 8);
      const moreCount = Math.max(0, sortedExecutionItems.length - visibleExecutionItems.length);
      const needsCloseDecision = isWorkCaseClosureConfirmingStatus(obj.status);
      const isClosedWorkCase = obj.status === 'closed';
      const successCriteriaState: WorkCaseRecordState = obj.hasSuccessCriteria ? 'recorded' : 'missing';
      const planConfirmedState: WorkCaseRecordState = obj.hasPlanConfirmedAt ? 'recorded' : 'missing';
      const closureRequestedState: WorkCaseRecordState = obj.hasClosureRequestedAt ? 'recorded' : 'missing';
      const verificationEvidenceState: WorkCaseRecordState = obj.hasVerificationEvidence ? 'recorded' : 'missing';
      const closureEvidenceState: WorkCaseRecordState = obj.hasClosureEvidence ? 'recorded' : 'missing';
      const closedAtState: WorkCaseRecordState = obj.hasClosedAt ? 'recorded' : 'missing';
      const closeDecisionFields = [
        { label: t('objectList.successCriteria'), state: successCriteriaState },
        { label: t('objectList.planConfirmedAt'), state: planConfirmedState },
        { label: t('objectList.closureRequestedAt'), state: closureRequestedState },
        { label: t('objectList.verificationEvidence'), state: verificationEvidenceState },
        { label: t('objectList.closureEvidence'), state: closureEvidenceState },
      ];
      const closedIntegrityFields = [...closeDecisionFields, { label: t('objectList.closedAt'), state: closedAtState }];
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
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
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
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject} />
      );
    }

    if (currentType === 'pitfall') {
      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
          <ObjectSignalBadges source={obj} type={obj.type} locale={locale} />
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
            {supportsPriorityNavigation && <span className="ldvh-meta shrink-0 text-ldvh-text-secondary">{t('objectList.lifecycleFilter')}</span>}
            <ObjectStatusFilter
              type={currentType}
              activeStatus={activeStatus}
              onChange={handleStatusChange}
              options={statusOptions}
              total={statusTotal}
              loading={loading}
            />
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
