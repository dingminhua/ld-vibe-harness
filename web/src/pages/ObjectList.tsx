import { useEffect, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, BadgeCheck, CheckCircle2, CircleAlert, CircleDashed, CirclePlay, Clock3, ClipboardCheck, Flag, GitBranch, Hourglass, Layers3, MapPinned } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import CopyPathButton from '@/components/CopyPathButton';
import MemoCreate from '@/components/MemoCreate';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import { fetchObjects, type ObjectItem, type ObjectStatusOption, type RelatedObjectSummary } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale } from '@/i18n/locales';
import { getObjectSignalAccent } from '@/utils/objectSignals';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';

type LocalizedTitleItem = Pick<ObjectItem, 'id'> & Partial<Pick<ObjectItem, 'title' | 'title_en' | 'title_zh'>>;

type OpenEvent = MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>;
type Translate = ReturnType<typeof useI18n>['t'];
type PlanRecordState = 'recorded' | 'missing';

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'superseded']);
const PENDING_CLOSE_STATUSES = new Set(['review_needed']);
const TASK_RISK_STATUSES = new Set(['open', 'degraded', 'suspended', 'rejected', 'deprecated', 'unknown']);

const TITLE_ACCENT_CLASS: Record<string, string> = {
  active: 'border-emerald-400/80',
  executing: 'border-emerald-400/80',
  accepted: 'border-emerald-400/70',
  review_needed: 'border-violet-400/80',
  verifying: 'border-violet-400/80',
  draft: 'border-amber-400/75',
  proposed: 'border-amber-400/75',
  planned: 'border-amber-400/75',
  closed: 'border-zinc-500/50',
  resolved: 'border-zinc-500/50',
  archived: 'border-zinc-500/50',
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

const taskFlowToneClass = {
  ready: 'border-sky-500/25 bg-sky-500/10 text-sky-500',
  executing: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  verifying: 'border-blue-500/30 bg-blue-500/10 text-blue-400',
  absorbing: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
  closed: 'border-zinc-500/30 bg-zinc-500/10 text-ldvh-text-secondary',
  blocked: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
  risk: 'border-red-500/30 bg-red-500/10 text-red-500',
  neutral: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
};

type TaskFlowTone = keyof typeof taskFlowToneClass;

const TASK_FLOW_ORDER: TaskFlowTone[] = ['ready', 'executing', 'verifying', 'absorbing', 'closed', 'blocked', 'risk', 'neutral'];
const TASK_FLOW_LEGEND_ORDER: TaskFlowTone[] = ['ready', 'executing', 'verifying', 'absorbing', 'closed', 'blocked'];

const taskFlowBarClass: Record<TaskFlowTone, string> = {
  ready: 'bg-sky-500',
  executing: 'bg-emerald-500',
  verifying: 'bg-blue-500',
  absorbing: 'bg-violet-500',
  closed: 'bg-zinc-500',
  blocked: 'bg-amber-500',
  risk: 'bg-red-500',
  neutral: 'bg-ldvh-border',
};

const taskFlowIconClass: Record<TaskFlowTone, string> = {
  ready: 'text-sky-500',
  executing: 'text-emerald-500',
  verifying: 'text-blue-400',
  absorbing: 'text-violet-500',
  closed: 'text-zinc-500',
  blocked: 'text-amber-500',
  risk: 'text-red-500',
  neutral: 'text-ldvh-text-secondary',
};

function getTaskFlowIcon(tone: TaskFlowTone) {
  if (tone === 'ready') return CircleDashed;
  if (tone === 'executing') return CirclePlay;
  if (tone === 'verifying') return ClipboardCheck;
  if (tone === 'absorbing') return BadgeCheck;
  if (tone === 'blocked') return Hourglass;
  if (tone === 'closed') return CheckCircle2;
  if (tone === 'risk') return CircleAlert;
  return Clock3;
}

function isTaskWaitingForBlocker(item: RelatedObjectSummary): boolean {
  return item.status === 'planned' && (item.openBlockers?.length ?? 0) > 0;
}

function getTaskFlowTone(item: RelatedObjectSummary): TaskFlowTone {
  if (isTaskWaitingForBlocker(item)) return 'blocked';
  if (item.status === 'executing') return 'executing';
  if (item.status === 'verifying') return 'verifying';
  if (isPendingCloseStatus(item.status)) return 'absorbing';
  if (isTerminalStatus(item.status)) return 'closed';
  if (item.status === 'planned') return 'ready';
  if (TASK_RISK_STATUSES.has(item.status)) return 'risk';
  return 'neutral';
}

function getTaskFlowLabel(item: RelatedObjectSummary, t: Translate, getStatus: (status: string) => string): string {
  const tone = getTaskFlowTone(item);
  if (tone === 'blocked') return t('objectList.taskFlowBlocked');
  if (tone === 'executing') return t('objectList.taskFlowExecuting');
  if (tone === 'verifying') return t('objectList.taskFlowVerifying');
  if (tone === 'absorbing') return t('objectList.taskFlowAbsorbing');
  if (tone === 'closed') return getStatus(item.status);
  if (tone === 'ready') return t('objectList.taskFlowReady');
  return getStatus(item.status);
}

function getTaskFlowToneLabel(tone: TaskFlowTone, t: Translate, getStatus: (status: string) => string): string {
  if (tone === 'blocked') return t('objectList.taskFlowBlocked');
  if (tone === 'executing') return t('objectList.taskFlowExecuting');
  if (tone === 'verifying') return t('objectList.taskFlowVerifying');
  if (tone === 'absorbing') return t('objectList.taskFlowAbsorbing');
  if (tone === 'closed') return getStatus('closed');
  if (tone === 'ready') return t('objectList.taskFlowReady');
  if (tone === 'risk') return t('objectList.taskFlowRisk');
  return t('objectList.taskFlowOther');
}

function getTaskFlowCounts(tasks: RelatedObjectSummary[]): Record<TaskFlowTone, number> {
  return tasks.reduce<Record<TaskFlowTone, number>>((counts, task) => {
    const tone = getTaskFlowTone(task);
    counts[tone] += 1;
    return counts;
  }, {
    ready: 0,
    executing: 0,
    verifying: 0,
    absorbing: 0,
    blocked: 0,
    closed: 0,
    risk: 0,
    neutral: 0,
  });
}

function getTaskFlowPriority(item: RelatedObjectSummary): number {
  const tone = getTaskFlowTone(item);
  if (tone === 'executing') return 0;
  if (tone === 'verifying') return 1;
  if (tone === 'absorbing') return 2;
  if (tone === 'blocked') return 3;
  if (tone === 'ready') return 4;
  if (tone === 'risk') return 5;
  if (tone === 'closed') return 8;
  return 5;
}

function sortPlanTasks(tasks: RelatedObjectSummary[]): RelatedObjectSummary[] {
  return [...tasks].sort((a, b) => {
    const priorityDelta = getTaskFlowPriority(a) - getTaskFlowPriority(b);
    if (priorityDelta !== 0) return priorityDelta;
    return a.id.localeCompare(b.id);
  });
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

function TaskFlowBar({
  tasks,
  t,
  getStatus,
}: {
  tasks: RelatedObjectSummary[];
  t: Translate;
  getStatus: (status: string) => string;
}) {
  const total = tasks.length;
  const counts = getTaskFlowCounts(tasks);
  const entries = TASK_FLOW_ORDER
    .map((tone) => ({
      tone,
      count: counts[tone],
      label: getTaskFlowToneLabel(tone, t, getStatus),
    }))
    .filter((entry) => entry.count > 0);
  const summary = entries.length > 0
    ? entries.map((entry) => t('objectList.taskFlowCount', { status: entry.label, count: String(entry.count) })).join(' · ')
    : t('objectList.noTasks');

  return (
    <div className="min-w-0" role="group" aria-label={summary} title={summary}>
      <div className="flex h-2.5 min-w-0 rounded-full bg-ldvh-border/45">
        {entries.length > 0 ? (
          entries.map((entry, index) => {
            const tooltip = t('objectList.taskFlowCount', { status: entry.label, count: String(entry.count) });
            const roundedClass = entries.length === 1
              ? 'rounded-full'
              : `${index === 0 ? 'rounded-l-full' : ''} ${index === entries.length - 1 ? 'rounded-r-full' : ''}`;
            return (
              <div
                key={entry.tone}
                tabIndex={0}
                aria-label={tooltip}
                title={tooltip}
                data-tooltip={tooltip}
                className={`relative h-full min-w-1 outline-none transition-[filter] after:pointer-events-none after:absolute after:bottom-full after:left-1/2 after:z-20 after:mb-1 after:hidden after:-translate-x-1/2 after:whitespace-nowrap after:rounded-md after:border after:border-ldvh-border after:bg-ldvh-panel after:px-2 after:py-1 after:text-xs after:leading-5 after:text-ldvh-text-primary after:shadow-lg after:shadow-black/20 after:content-[attr(data-tooltip)] hover:brightness-110 hover:after:block focus:after:block focus-visible:ring-2 focus-visible:ring-ldvh-accent/70 ${taskFlowBarClass[entry.tone]} ${roundedClass}`}
                style={{ width: `${(entry.count / total) * 100}%` }}
              />
            );
          })
        ) : (
          <div className="h-full w-full rounded-full bg-ldvh-border/45" />
        )}
      </div>
    </div>
  );
}

function TaskFlowLegend({
  t,
  getStatus,
}: {
  t: Translate;
  getStatus: (status: string) => string;
}) {
  return (
    <div className="flex min-h-7 flex-wrap items-center justify-end gap-x-2.5 gap-y-1" aria-label={t('objectList.taskFlowLegend')}>
      {TASK_FLOW_LEGEND_ORDER.map((tone) => {
        const label = getTaskFlowToneLabel(tone, t, getStatus);
        const Icon = getTaskFlowIcon(tone);
        return (
          <span key={tone} className="ldvh-caption inline-flex items-center gap-1.5 text-ldvh-text-secondary">
            <Icon size={12} strokeWidth={2.2} className={taskFlowIconClass[tone]} />
            <span>{label}</span>
          </span>
        );
      })}
    </div>
  );
}

const workAreaSectionToneClass = {
  active: {
    section: 'border-emerald-500/30 bg-emerald-500/5',
    header: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400',
    rowHover: 'hover:bg-emerald-500/10',
    icon: 'text-emerald-400',
  },
  review: {
    section: 'border-violet-500/30 bg-violet-500/5',
    header: 'border-violet-500/30 bg-violet-500/10 text-violet-400',
    rowHover: 'hover:bg-violet-500/10',
    icon: 'text-violet-400',
  },
  closed: {
    section: 'border-ldvh-border bg-ldvh-bg',
    header: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
    rowHover: 'hover:bg-ldvh-border/35',
    icon: 'text-ldvh-text-secondary',
  },
};

function WorkAreaPlanRow({
  item,
  locale,
  tone,
  onOpen,
}: {
  item: RelatedObjectSummary;
  locale: string;
  tone: keyof typeof workAreaSectionToneClass;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  const toneClass = workAreaSectionToneClass[tone];

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => onOpen(event, item)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(event, item))}
      className={`group/workarea-row flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-left transition-colors ${toneClass.rowHover}`}
    >
      <div className="min-w-0 flex-1">
        <span className="ldvh-body block min-w-0 truncate transition-colors group-hover/workarea-row:text-ldvh-accent">
          {getLocalizedTitle(item, locale)}
        </span>
        <span className="ldvh-meta-muted block min-w-0 truncate">{item.id}</span>
      </div>
      <CopyPathButton path={item.path} />
      <ArrowRight size={14} className={`shrink-0 transition-transform group-hover/workarea-row:translate-x-0.5 ${toneClass.icon}`} />
    </div>
  );
}

function WorkAreaPlanSection({
  title,
  plans,
  locale,
  tone,
  onOpen,
}: {
  title: string;
  plans?: RelatedObjectSummary[];
  locale: string;
  tone: keyof typeof workAreaSectionToneClass;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  const toneClass = workAreaSectionToneClass[tone];

  return (
    <div className={`min-w-0 overflow-hidden rounded-md border ${toneClass.section}`}>
      <div className={`ldvh-caption-strong flex min-w-0 items-center gap-2 border px-3 py-2 ${toneClass.header}`}>
        <Layers3 size={13} className="shrink-0" />
        <span className="min-w-0 truncate">{title}</span>
      </div>
      {plans && plans.length > 0 && (
        <div className="min-w-0 divide-y divide-ldvh-border/60 px-1 py-1">
          {plans.map((plan) => (
            <WorkAreaPlanRow
              key={plan.id}
              item={plan}
              locale={locale}
              tone={tone}
              onOpen={onOpen}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function TaskFlowMarker({
  tone,
  label,
}: {
  tone: TaskFlowTone;
  label: string;
}) {
  const Icon = getTaskFlowIcon(tone);
  return (
    <span
      aria-label={label}
      title={label}
      className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md border ${taskFlowToneClass[tone]}`}
    >
      <Icon size={14} strokeWidth={2.2} />
    </span>
  );
}

function TaskQueueRow({
  item,
  locale,
  getStatus,
  t,
  onOpen,
}: {
  item: RelatedObjectSummary;
  locale: string;
  getStatus: (status: string) => string;
  t: Translate;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  const flowTone = getTaskFlowTone(item);
  const flowLabel = getTaskFlowLabel(item, t, getStatus);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => onOpen(event, item)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(event, item))}
      className="group/row flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/35"
    >
      <div className="min-w-0 flex-1">
        <span className="ldvh-body block min-w-0 truncate transition-colors group-hover/row:text-ldvh-accent">
          {getLocalizedTitle(item, locale)}
        </span>
        <span className="ldvh-meta-muted block min-w-0 truncate">{item.id}</span>
      </div>
      <TaskFlowMarker tone={flowTone} label={flowLabel} />
      <CopyPathButton path={item.path} />
      <ArrowRight size={14} className="shrink-0 text-ldvh-text-secondary transition-colors group-hover/row:text-ldvh-accent" />
    </div>
  );
}

function PlanWorkareaRow({
  workarea,
  fallbackId,
  locale,
  emptyLabel,
  onOpen,
}: {
  workarea?: RelatedObjectSummary;
  fallbackId?: string;
  locale: string;
  emptyLabel: string;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  const item = workarea ?? (fallbackId ? {
    id: fallbackId,
    type: 'workarea',
    title: fallbackId,
    status: 'unknown',
    path: '',
    updated: '',
  } : undefined);

  if (!item) {
    return (
      <div className="ldvh-caption flex min-w-0 items-center gap-1.5 px-1 text-ldvh-text-secondary">
        <MapPinned size={12} className="shrink-0" />
        <span className="min-w-0 truncate">{emptyLabel}</span>
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => onOpen(event, item)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(event, item))}
      className="ldvh-caption group/workarea flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-ldvh-text-secondary transition-colors hover:bg-ldvh-border/35 hover:text-ldvh-text-primary"
    >
      <MapPinned size={12} className="shrink-0" />
      <span className="min-w-0 flex-1 truncate text-ldvh-text-primary/85 transition-colors group-hover/workarea:text-ldvh-accent">
        {getLocalizedTitle(item, locale)}
      </span>
      <span className="ldvh-meta-muted ml-auto shrink-0 text-right">{item.id}</span>
      <ArrowRight size={12} className="shrink-0 transition-colors group-hover/workarea:text-ldvh-accent" />
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
  children: ReactNode;
}) {
  const signalAccent = getObjectSignalAccent(obj);
  const titleAccentClass = getTitleAccentClass(obj.status);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(obj.id)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(obj.id))}
      className="group flex min-w-0 cursor-pointer flex-col gap-3 rounded-lg border border-ldvh-border bg-ldvh-panel p-4 text-left transition-colors hover:border-ldvh-accent/40"
      style={signalAccent ? { borderLeftColor: signalAccent, borderLeftWidth: 3 } : undefined}
    >
      <div className="flex min-w-0 items-start justify-between gap-2">
        <span className="ldvh-meta-muted min-w-0 truncate">{obj.id}</span>
        <div className="flex shrink-0 items-center gap-2">
          <CopyPathButton path={obj.path} />
          <StatusBadge status={obj.status} statusLabel={getObjectStatusLocale(obj.type, obj.status, locale)} />
        </div>
      </div>
      <div className={`-mx-1 min-w-0 rounded-md border-l-2 bg-ldvh-bg/65 px-2.5 py-2 ring-1 ring-inset ring-ldvh-border/50 transition-colors group-hover:bg-ldvh-bg/85 ${titleAccentClass}`}>
        <span className="ldvh-card-title block min-w-0 truncate transition-colors group-hover:text-ldvh-accent">
          {getLocalizedTitle(obj, locale)}
        </span>
      </div>
      {children}
      <span className="ldvh-meta self-end text-right">{formatDateTime(obj.updated)}</span>
    </div>
  );
}

export default function ObjectList() {
  const { type } = useParams<{ type: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState<ObjectItem[]>([]);
  const [statusOptions, setStatusOptions] = useState<ObjectStatusOption[]>([]);
  const [statusTotal, setStatusTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const { t, getStatus, locale } = useI18n();

  const currentType = type ?? 'task';
  const statusParam = searchParams.get('status');
  const activeStatus = getEffectiveListStatus(currentType, statusParam);

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
  const openObject = (objId: string) => {
    navigate(`/objects/${currentType}/${objId}${detailSearch ? `?${detailSearch}` : ''}`);
  };

  const openRelatedObject = (event: OpenEvent, item: RelatedObjectSummary) => {
    event.preventDefault();
    event.stopPropagation();
    navigate(`/objects/${item.type}/${item.id}`);
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
            <p className="ldvh-body-muted rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-3 py-4 text-center">
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
                  onOpen={openRelatedObject}
                />
              )}
              {reviewPlans.length > 0 && (
                <WorkAreaPlanSection
                  title={t('objectList.pendingClosePlanCount', { count: String(reviewPlans.length) })}
                  plans={reviewPlans}
                  locale={locale}
                  tone="review"
                  onOpen={openRelatedObject}
                />
              )}
              {closedPlanCount > 0 && (
                <WorkAreaPlanSection
                  title={t('objectList.closedPlanCount', { count: String(closedPlanCount) })}
                  locale={locale}
                  tone="closed"
                  onOpen={openRelatedObject}
                />
              )}
            </>
          )}
        </ObjectCardFrame>
      );
    }

    if (currentType === 'taskplan') {
      const tasks = obj.tasks ?? [];
      const orderedTasks = sortPlanTasks(tasks);
      const visibleTasks = orderedTasks.slice(0, 4);
      const moreCount = Math.max(0, tasks.length - visibleTasks.length);
      const needsCloseDecision = obj.status === 'review_needed';
      const isClosedPlan = obj.status === 'closed';
      const successCriteriaState: PlanRecordState = obj.hasSuccessCriteria ? 'recorded' : 'missing';
      const reviewRequestedState: PlanRecordState = obj.hasReviewRequestedAt ? 'recorded' : 'missing';
      const completionEvidenceState: PlanRecordState = obj.hasCompletionEvidence ? 'recorded' : 'missing';
      const closedAtState: PlanRecordState = obj.hasClosedAt ? 'recorded' : 'missing';
      const closeDecisionFields = [
        { label: t('objectList.successCriteria'), state: successCriteriaState },
        { label: t('objectList.reviewRequestedAt'), state: reviewRequestedState },
        { label: t('objectList.completionEvidence'), state: completionEvidenceState },
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
          <PlanWorkareaRow
            workarea={obj.workareaSummary}
            fallbackId={obj.workarea}
            locale={locale}
            emptyLabel={t('objectList.noWorkarea')}
            onOpen={openRelatedObject}
          />

          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="mb-2 flex min-w-0 items-center gap-1.5">
              <span className="ldvh-caption-strong inline-flex min-w-0 items-center gap-1.5 truncate">
                <Flag size={13} className="shrink-0 text-ldvh-accent" />
                {t('objectList.planProgress')}
              </span>
            </div>
            <TaskFlowBar tasks={tasks} t={t} getStatus={getStatus} />
          </div>

          {shouldShowCloseDecision && (
            <div className={`min-w-0 rounded-md border p-3 ${
              hasClosedIntegrityIssue
                ? 'border-red-500/30 bg-red-500/5'
                : 'border-violet-500/25 bg-violet-500/5'
            }`}
            >
              <div className="mb-2 flex min-w-0 items-center gap-1.5">
                <ClipboardCheck size={13} className={`shrink-0 ${hasClosedIntegrityIssue ? 'text-red-400' : 'text-violet-400'}`} />
                <span className="ldvh-caption-strong min-w-0 truncate">{closeDecisionTitle}</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {visibleCloseFields.map((field) => (
                  <PlanRecordItem key={field.label} label={field.label} state={field.state} t={t} />
                ))}
              </div>
            </div>
          )}

          <div className="min-w-0 rounded-md border border-ldvh-border bg-ldvh-bg p-3">
            <div className="mb-2 flex min-w-0 items-center justify-between gap-2">
              <span className="ldvh-caption-strong inline-flex min-w-0 items-center gap-1.5 truncate">
                <GitBranch size={13} className="shrink-0 text-ldvh-accent" />
                {t('objectList.planTaskQueue')}
              </span>
            </div>
            <div className="min-w-0 divide-y divide-ldvh-border/60">
              {visibleTasks.length > 0 ? (
                visibleTasks.map((task) => (
                  <TaskQueueRow
                    key={task.id}
                    item={task}
                    locale={locale}
                    getStatus={getStatus}
                    t={t}
                    onOpen={openRelatedObject}
                  />
                ))
              ) : (
                <p className="ldvh-body-muted rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-3 py-4 text-center">
                  {t('objectList.noTasks')}
                </p>
              )}
            </div>
            {moreCount > 0 && (
              <span className="ldvh-caption mt-2 block">{t('objectList.moreTasks', { count: String(moreCount) })}</span>
            )}
          </div>
        </ObjectCardFrame>
      );
    }

    return (
      <ObjectCardFrame key={obj.id} obj={obj} locale={locale} onOpen={openObject}>
        <ObjectSignalBadges source={obj} locale={locale} />
      </ObjectCardFrame>
    );
  };

  return (
    <div className="ldvh-page-frame">
      <div className="mb-4 flex min-h-8 flex-wrap items-center justify-between gap-3">
        <ObjectStatusFilter
          type={currentType}
          activeStatus={activeStatus}
          onChange={handleStatusChange}
          options={statusOptions}
          total={statusTotal}
          loading={loading}
        />
        {currentType === 'taskplan' && (
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
