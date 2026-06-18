import { useEffect, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowRight, CheckCircle2, ChevronDown, ChevronUp, CircleAlert, ClipboardCheck } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import CopyPathButton from '@/components/CopyPathButton';
import MemoCreate from '@/components/MemoCreate';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import PriorityIcon from '@/components/PriorityIcon';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { TaskFlowBar, TaskFlowLegend } from '@/components/TaskFlowStatus';
import { fetchObjects, type ObjectItem, type ObjectStatusOption, type RelatedObjectSummary, type RelatedPlanSummary } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';
import { CATEGORY_COLORS } from '@/utils/categoryColors';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';

type LocalizedTitleItem = Pick<ObjectItem, 'id'> & Partial<Pick<ObjectItem, 'title' | 'title_en' | 'title_zh'>>;

type OpenEvent = MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>;
type Translate = ReturnType<typeof useI18n>['t'];
type PlanRecordState = 'recorded' | 'missing';
type StatusReason = { label: string; text: string; missing?: boolean };

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'discarded', 'superseded']);
const PENDING_CLOSE_STATUSES = new Set(['review_needed']);
const TITLE_ACCENT_CLASS: Record<string, string> = {
  active: 'border-emerald-400/80',
  executing: 'border-emerald-400/80',
  accepted: 'border-emerald-400/70',
  review_needed: 'border-violet-400/80',
  verifying: 'border-blue-400/80',
  draft: 'border-amber-400/75',
  proposed: 'border-amber-400/75',
  planned: 'border-amber-400/75',
  pending: 'border-amber-400/75',
  closed: 'border-zinc-500/50',
  resolved: 'border-zinc-500/50',
  archived: 'border-zinc-500/50',
  discarded: 'border-red-400/75',
  superseded: 'border-zinc-500/50',
  rejected: 'border-red-400/75',
  deprecated: 'border-red-400/75',
  suspended: 'border-red-400/75',
};

function getLocalizedTitle(item: LocalizedTitleItem, locale: string): string {
  if (locale === 'en') {
    return item.title_en || item.title || item.id;
  }
  return item.title_zh || item.title || item.id;
}

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

function statusRequiresReason(status: string): boolean {
  return status === 'archived' || status === 'deprecated' || status === 'discarded' || status === 'closed';
}

function getNonActiveReason(obj: ObjectItem, locale: string): StatusReason | null {
  if (obj.status === 'active') return null;
  const labels = {
    archive_reason: locale === 'en' ? 'Archive reason' : '归档原因',
    deprecated_reason: locale === 'en' ? 'Deprecated reason' : '废弃原因',
    discard_reason: locale === 'en' ? 'Discard reason' : '废弃原因',
    closure_evidence: locale === 'en' ? 'Close reason' : '关闭原因',
  };
  const orderedFields = obj.status === 'archived'
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
  if (statusRequiresReason(obj.status)) {
    return {
      label: locale === 'en' ? 'Missing reason' : '原因缺失',
      text: locale === 'en'
        ? 'This non-active object must record a reason in its fact source.'
        : '该非活跃对象必须在事实源中记录原因。',
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

function isTerminalStatus(status: string): boolean {
  return TERMINAL_STATUSES.has(status);
}

function isPendingCloseStatus(status: string): boolean {
  return PENDING_CLOSE_STATUSES.has(status);
}

function handleKeyboardOpen(event: KeyboardEvent<HTMLElement>, onOpen: () => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    event.stopPropagation();
    onOpen();
  }
}

function getPlanRecordStateLabel(state: PlanRecordState, t: Translate): string {
  if (state === 'recorded') return t('objectList.hasRecord');
  return t('objectList.missingRecord');
}

function getPlanRecordClassName(state: PlanRecordState): string {
  if (state === 'recorded') return 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500';
  return 'border-red-500/60 bg-red-500/15 text-red-400 ring-1 ring-inset ring-red-500/20';
}

function getPlanRecordIcon(state: PlanRecordState) {
  if (state === 'recorded') return CheckCircle2;
  return CircleAlert;
}

function PlanRecordItem({ label, state, t }: { label: string; state: PlanRecordState; t: Translate }) {
  const stateLabel = getPlanRecordStateLabel(state, t);
  const StateIcon = getPlanRecordIcon(state);
  return (
    <span
      aria-label={`${label} ${stateLabel}`}
      title={`${label} ${stateLabel}`}
      className={`ldvh-chip inline-flex min-w-0 items-center gap-1.5 rounded-md border px-2 py-1 ${getPlanRecordClassName(state)}`}
    >
      <ClipboardCheck size={12} className="shrink-0" />
      <span className="min-w-0 truncate">{label}</span>
      <StateIcon size={state === 'missing' ? 13 : 12} strokeWidth={state === 'missing' ? 2.6 : 2} className="shrink-0 opacity-95" />
    </span>
  );
}

const workAreaSectionToneClass = {
  active: {
    section: 'border-emerald-500/30 bg-emerald-500/5',
    header: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
    rowHover: 'hover:bg-emerald-500/10',
    icon: 'text-emerald-400',
    hoverText: 'group-hover/workarea-row:text-emerald-400',
    action: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-emerald-500/10 hover:text-emerald-400',
  },
  review: {
    section: 'border-violet-500/30 bg-violet-500/5',
    header: 'border-violet-500/30 bg-violet-500/10 text-violet-400',
    rowHover: 'hover:bg-violet-500/10',
    icon: 'text-violet-400',
    hoverText: 'group-hover/workarea-row:text-violet-400',
    action: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-violet-500/10 hover:text-violet-400',
  },
  closed: {
    section: 'border-ldvh-border bg-ldvh-bg',
    header: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
    rowHover: 'hover:bg-ldvh-border/35',
    icon: 'text-ldvh-text-secondary',
    hoverText: 'group-hover/workarea-row:text-ldvh-accent',
    action: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
  },
};

function WorkAreaPlanRow({
  item,
  locale,
  tone,
  t,
  getStatus,
  onOpen,
}: {
  item: RelatedPlanSummary;
  locale: string;
  tone: keyof typeof workAreaSectionToneClass;
  t: Translate;
  getStatus: (status: string) => string;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  const toneClass = workAreaSectionToneClass[tone];
  const planType = item.type || 'workplan';
  const flowItems = item.executionItems ?? [];

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => onOpen(event, item)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(event, item))}
      className={`group/workarea-row flex min-w-0 cursor-pointer flex-col gap-1.5 rounded-md px-2 py-2 text-left outline-none transition-colors hover:brightness-[1.04] focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ldvh-accent/70 ${toneClass.rowHover}`}
    >
      <div className="flex min-w-0 items-center gap-2">
        <div className="min-w-0 flex-1">
          <span className={`ldvh-body flex min-w-0 items-center gap-1.5 truncate transition-colors ${toneClass.hoverText}`}>
            <PriorityIcon source={item} type={planType} locale={locale} size="sm" />
            <ObjectTypeIcon type={planType} size={12} className="shrink-0" />
            <span className="min-w-0 truncate">{getLocalizedTitle(item, locale)}</span>
          </span>
          <span className="ldvh-meta-muted block min-w-0 truncate">{item.id}</span>
        </div>
        <CopyPathButton path={item.path} toneClassName={toneClass.action} />
        <ArrowRight size={13} className={`shrink-0 text-ldvh-text-secondary/70 transition-all group-hover/workarea-row:translate-x-0.5 ${toneClass.hoverText}`} />
      </div>
      {flowItems.length > 0 && (
        <div className="min-w-0 self-stretch">
          <TaskFlowBar tasks={flowItems} t={t} getStatus={getStatus} compact />
        </div>
      )}
    </div>
  );
}

function WorkAreaPlanSection({
  title,
  plans,
  locale,
  tone,
  t,
  getStatus,
  onOpen,
  defaultCollapsed = false,
}: {
  title: string;
  plans?: RelatedPlanSummary[];
  locale: string;
  tone: keyof typeof workAreaSectionToneClass;
  t: Translate;
  getStatus: (status: string) => string;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
  defaultCollapsed?: boolean;
}) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);
  const toneClass = workAreaSectionToneClass[tone];
  const canCollapse = defaultCollapsed || tone === 'closed';
  const hasPlans = Boolean(plans && plans.length > 0);
  const headerClassName = `ldvh-caption-strong flex w-full min-w-0 items-center gap-2 border px-3 py-2 text-left ${toneClass.header}`;
  const headerContent = (
    <>
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-80" aria-hidden="true" />
      <span className="min-w-0 flex-1 truncate">{title}</span>
      {canCollapse && hasPlans && (collapsed ? <ChevronDown size={13} className="shrink-0" /> : <ChevronUp size={13} className="shrink-0" />)}
    </>
  );

  return (
    <div
      onClick={(event) => event.stopPropagation()}
      className={`min-w-0 cursor-default overflow-hidden rounded-md border ${toneClass.section}`}
    >
      {canCollapse && hasPlans ? (
        <button
          type="button"
          aria-expanded={!collapsed}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
            setCollapsed((value) => !value);
          }}
          onKeyDown={(event) => event.stopPropagation()}
          className={`${headerClassName} cursor-pointer`}
        >
          {headerContent}
        </button>
      ) : (
        <div className={`${headerClassName} cursor-default`}>
          {headerContent}
        </div>
      )}
      {!collapsed && plans && plans.length > 0 && (
        <div className="min-w-0 divide-y divide-ldvh-border/60 px-1 py-1">
          {plans.map((plan) => (
            <WorkAreaPlanRow
              key={plan.id}
              item={plan}
              locale={locale}
              tone={tone}
              t={t}
              getStatus={getStatus}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ObjectCardFrame({
  obj,
  locale,
  onOpen,
  children,
}: {
  obj: ObjectItem;
  locale: string;
  onOpen: (objId: string) => void;
  children?: ReactNode;
}) {
  const titleAccentClass = getTitleAccentClass(obj.status);
  const typeColor = CATEGORY_COLORS[obj.type] || CATEGORY_COLORS.other;
  const nonActiveReason = getNonActiveReason(obj, locale);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(obj.id)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(obj.id))}
      className="group/card flex min-w-0 cursor-pointer flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left outline-none transition-colors hover:border-ldvh-accent/40 hover:bg-ldvh-panel/95 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ldvh-accent/70"
    >
      <div className="flex min-w-0 items-start justify-between gap-2">
        <span className="ldvh-meta-muted min-w-0 truncate">{obj.id}</span>
        <div className="flex shrink-0 items-center gap-2">
          <CopyPathButton path={obj.path} />
          <StatusBadge status={obj.status} statusLabel={getObjectStatusLocale(obj.type, obj.status, locale)} objectType={obj.type} />
        </div>
      </div>
      <div
        className={`-mx-1 flex min-w-0 items-start gap-1.5 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 text-left ring-1 ring-inset ring-ldvh-border/50 transition-colors group-hover/card:bg-ldvh-bg/85 ${titleAccentClass}`}
      >
        <PriorityIcon source={obj} type={obj.type} locale={locale} size="sm" />
        <ObjectTypeIcon type={obj.type} size={14} className="mt-0.5 shrink-0" style={{ color: typeColor }} />
        <span className="ldvh-card-title min-w-0 flex-1 whitespace-normal break-words leading-snug transition-colors group-hover/card:text-ldvh-accent">
          {getLocalizedTitle(obj, locale)}
        </span>
        <ArrowRight size={14} className="mt-0.5 shrink-0 text-ldvh-text-secondary transition-all group-hover/card:translate-x-0.5 group-hover/card:text-ldvh-accent" />
      </div>
      {nonActiveReason && <StatusReasonNote reason={nonActiveReason} />}
      {children}
      <div className="mt-auto flex min-w-0 justify-end pt-1 text-right">
        <span className="ldvh-meta-muted">
          {locale === 'en' ? 'Updated ' : '更新 '}{formatDateTime(obj.updated)}
        </span>
      </div>
    </div>
  );
}

export default function ObjectList() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [statusOptions, setStatusOptions] = useState<ObjectStatusOption[]>([]);
  const [statusTotal, setStatusTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'workplan';
  const statusParam = searchParams.get('status');
  const activeStatus = getEffectiveListStatus(currentType, statusParam);

  useEffect(() => {
    if (currentType !== 'memo' || !searchParams.has('category')) return;
    const nextParams = new URLSearchParams(searchParams);
    nextParams.delete('category');
    setSearchParams(nextParams, { replace: true });
  }, [currentType, searchParams, setSearchParams]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setStatusOptions([]);
    setStatusTotal(0);
    fetchObjects(currentType, activeStatus ?? undefined)
      .then((result) => {
        const nextItems = result.data?.items ?? [];
        setItems(nextItems);
        setStatusOptions(result.data?.statusOptions ?? []);
        setStatusTotal(result.data?.statusTotal ?? nextItems.length);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [currentType, activeStatus, reloadKey]);

  const handleStatusChange = (status: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    writeListStatusParam(currentType, nextParams, status);
    setSearchParams(nextParams);
  };

  const detailSearch = searchParams.toString();
  const returnToListPath = `${location.pathname}${location.search}`;
  const openObject = (objId: string) => {
    navigate(`/objects/${currentType}/${objId}${detailSearch ? `?${detailSearch}` : ''}`, {
      state: { from: returnToListPath },
    });
  };

  const openRelatedObject = (event: OpenEvent, item: RelatedObjectSummary) => {
    event.preventDefault();
    event.stopPropagation();
    navigate(`/objects/${item.type}/${item.id}`, {
      state: { from: returnToListPath },
    });
  };

  const renderObjectCard = (obj: ObjectItem) => {
    if (currentType === 'workarea') {
      const plans = obj.plans ?? [];
      const planTotal = obj.planTotal ?? plans.length;
      const activePlans = plans.filter((plan) => !isPendingCloseStatus(plan.status) && !isTerminalStatus(plan.status));
      const reviewPlans = plans.filter((plan) => isPendingCloseStatus(plan.status));
      const closedPlans = plans.filter((plan) => isTerminalStatus(plan.status));
      const closedPlanCount = obj.planClosed ?? closedPlans.length;

      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
          {planTotal === 0 ? (
            <p
              onClick={(event) => event.stopPropagation()}
              className="ldvh-body-muted cursor-default rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-3 py-4 text-center"
            >
              {t('objectList.noPlans')}
            </p>
          ) : (
            <>
              {activePlans.length > 0 && (
                <WorkAreaPlanSection
                  title={t('objectList.activePlanCount', { count: String(activePlans.length) })}
                  plans={activePlans}
                  locale={locale}
                  tone="active"
                  t={t}
                  getStatus={getStatus}
                  onOpen={openRelatedObject}
                />
              )}
              {reviewPlans.length > 0 && (
                <WorkAreaPlanSection
                  title={t('objectList.pendingClosePlanCount', { count: String(reviewPlans.length) })}
                  plans={reviewPlans}
                  locale={locale}
                  tone="review"
                  t={t}
                  getStatus={getStatus}
                  onOpen={openRelatedObject}
                />
              )}
              {closedPlanCount > 0 && (
                <WorkAreaPlanSection
                  title={t('objectList.closedPlanCount', { count: String(closedPlanCount) })}
                  plans={closedPlans}
                  locale={locale}
                  tone="closed"
                  t={t}
                  getStatus={getStatus}
                  onOpen={openRelatedObject}
                  defaultCollapsed
                />
              )}
            </>
          )}
        </ObjectCardFrame>
      );
    }

    if (currentType === 'workplan') {
      const executionItems = obj.executionItems ?? [];
      const visibleExecutionItems = executionItems.slice(0, 8);
      const moreCount = Math.max(0, executionItems.length - visibleExecutionItems.length);
      const needsCloseDecision = obj.status === 'review_needed';
      const isClosedPlan = obj.status === 'closed';
      const successCriteriaState: PlanRecordState = obj.hasSuccessCriteria ? 'recorded' : 'missing';
      const reviewRequestedState: PlanRecordState = obj.hasReviewRequestedAt ? 'recorded' : 'missing';
      const verificationEvidenceState: PlanRecordState = obj.hasVerificationEvidence ? 'recorded' : 'missing';
      const closureEvidenceState: PlanRecordState = obj.hasClosureEvidence ? 'recorded' : 'missing';
      const closedAtState: PlanRecordState = obj.hasClosedAt ? 'recorded' : 'missing';
      const closeDecisionFields = [
        { label: t('objectList.successCriteria'), state: successCriteriaState },
        { label: t('objectList.reviewRequestedAt'), state: reviewRequestedState },
        { label: t('objectList.verificationEvidence'), state: verificationEvidenceState },
        { label: t('objectList.closureEvidence'), state: closureEvidenceState },
      ];
      const closedIntegrityFields = [...closeDecisionFields, { label: t('objectList.closedAt'), state: closedAtState }];
      const hasClosedIntegrityIssue = isClosedPlan && closedIntegrityFields.some((field) => field.state === 'missing');
      const shouldShowCloseDecision = needsCloseDecision || hasClosedIntegrityIssue;
      const closeDecisionTitle = hasClosedIntegrityIssue && !needsCloseDecision
        ? t('objectList.closureIssue')
        : t('objectList.closeDecision');
      const visibleCloseFields = isClosedPlan ? closedIntegrityFields : closeDecisionFields;

      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
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
                  <PlanRecordItem key={field.label} label={field.label} state={field.state} t={t} />
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
                  {obj.executionItemDone ?? 0}/{obj.executionItemTotal ?? executionItems.length}
                </span>
              )}
            </div>
            <div className="min-w-0 divide-y divide-ldvh-border/60">
              {visibleExecutionItems.length > 0 ? (
                visibleExecutionItems.map((item) => (
                  <div key={item.id} className="flex min-w-0 items-center gap-2 py-2">
                    <ObjectTypeIcon type="workplan" size={12} className="shrink-0 text-sky-400" />
                    <div className="min-w-0 flex-1">
                      <span className="ldvh-body block min-w-0 truncate">{getLocalizedTitle(item, locale)}</span>
                      <span className="ldvh-meta-muted block min-w-0 truncate">{item.role || item.id}</span>
                    </div>
                    {item.blockingReason && (
                      <CircleAlert size={13} className="shrink-0 text-amber-400" />
                    )}
                    <StatusBadge status={item.status} statusLabel={getObjectStatusLocale('workplan', item.status, locale)} objectType="workplan" size="sm" />
                  </div>
                ))
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

    if (currentType === 'memo') {
      const memoSource = obj.source || '';
      const description = obj.description || '';

      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
          <ObjectSignalBadges source={obj} type={obj.type} locale={locale} />
          {memoSource && (
            <div className="flex items-center gap-1.5">
              <span className="ldvh-caption-strong shrink-0 rounded-md border border-ldvh-border px-1.5 py-0.5 text-ldvh-text-secondary">
                {locale === 'en' ? 'Source' : '来源'}
              </span>
              <span
                className="ldvh-chip max-w-[16rem] truncate rounded-md border border-ldvh-border/50 bg-ldvh-bg px-1.5 py-0.5 text-ldvh-text-primary"
                title={memoSource}
              >
                {memoSource}
              </span>
            </div>
          )}
          {description && (
            <p className="ldvh-body-muted line-clamp-2 border-l-2 border-ldvh-border/40 pl-2">
              {description}
            </p>
          )}
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
      <div className="sticky top-0 z-20 -mx-4 mb-4 flex min-h-8 flex-wrap items-center justify-between gap-3 border-b border-ldvh-border bg-ldvh-bg/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <ObjectStatusFilter
          type={currentType}
          activeStatus={activeStatus}
          onChange={handleStatusChange}
          options={statusOptions}
          total={statusTotal}
          loading={loading}
        />
        {(currentType === 'workarea' || currentType === 'workplan') && (
          <TaskFlowLegend t={t} getStatus={getStatus} />
        )}
        {currentType === 'memo' && (
          <MemoCreate onCreated={() => setReloadKey((value) => value + 1)} />
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
      ) : items.length === 0 ? (
        <div className="ldvh-body-muted py-20 text-center">
          {t('objectList.noObjects', { type: currentType })}
        </div>
      ) : (
        <div className="ldvh-section-grid">
          {items.map((obj) => renderObjectCard(obj))}
        </div>
      )}
    </div>
  );
}
