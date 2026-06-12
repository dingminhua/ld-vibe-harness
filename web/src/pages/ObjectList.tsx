import { useEffect, useState, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, CheckCircle2, CircleDot, ClipboardCheck, Layers3, ListChecks, ShieldAlert } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import ObjectStatusFilter from '@/components/ObjectStatusFilter';
import CopyPathButton from '@/components/CopyPathButton';
import MemoCreate from '@/components/MemoCreate';
import ObjectSignalBadges from '@/components/ObjectSignalBadges';
import { fetchObjects, type ObjectItem, type RelatedObjectSummary } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { useI18n } from '@/i18n/context';
import { getObjectSignalAccent } from '@/utils/objectSignals';
import { getEffectiveListStatus, writeListStatusParam } from '@/utils/listStatus';

type LocalizedTitleItem = Pick<ObjectItem, 'id'> & Partial<Pick<ObjectItem, 'title' | 'title_en' | 'title_zh'>>;

type OpenEvent = MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>;

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'superseded']);
const PENDING_CLOSE_STATUSES = new Set(['review_needed']);

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

function getProgressPercent(closed: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((closed / total) * 100);
}

function handleKeyboardOpen(event: KeyboardEvent<HTMLElement>, onOpen: () => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    event.stopPropagation();
    onOpen();
  }
}

const pillToneClass: Record<string, string> = {
  neutral: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
  active: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  review: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
  risk: 'border-red-500/30 bg-red-500/10 text-red-500',
  done: 'border-zinc-500/30 bg-zinc-500/10 text-ldvh-text-secondary',
};

function SummaryPill({
  icon,
  label,
  tone = 'neutral',
}: {
  icon: ReactNode;
  label: string;
  tone?: keyof typeof pillToneClass;
}) {
  return (
    <span className={`ldvh-chip inline-flex min-w-0 items-center gap-1.5 rounded-full border px-2.5 py-1 ${pillToneClass[tone]}`}>
      <span className="shrink-0">{icon}</span>
      <span className="min-w-0 truncate">{label}</span>
    </span>
  );
}

function RecordPill({ label, recorded, t }: { label: string; recorded: boolean; t: (key: 'objectList.hasRecord' | 'objectList.missingRecord') => string }) {
  return (
    <span
      className={`ldvh-chip inline-flex min-w-0 items-center gap-1.5 rounded-full border px-2.5 py-1 ${
        recorded
          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
          : 'border-amber-500/30 bg-amber-500/10 text-amber-500'
      }`}
    >
      <ClipboardCheck size={12} className="shrink-0" />
      <span className="min-w-0 truncate">{label}</span>
      <span className="shrink-0 opacity-80">{recorded ? t('objectList.hasRecord') : t('objectList.missingRecord')}</span>
    </span>
  );
}

function ProgressBar({ closed, total }: { closed: number; total: number }) {
  const percent = getProgressPercent(closed, total);
  return (
    <div
      className="h-1.5 overflow-hidden rounded-full bg-ldvh-border/60"
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div className="h-full rounded-full bg-ldvh-accent transition-[width]" style={{ width: `${percent}%` }} />
    </div>
  );
}

function StatusCountChips({
  counts,
  getStatus,
}: {
  counts?: Record<string, number>;
  getStatus: (status: string) => string;
}) {
  const entries = Object.entries(counts ?? {}).sort((a, b) => b[1] - a[1]).slice(0, 4);
  if (entries.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {entries.map(([status, count]) => (
        <span
          key={status}
          className="ldvh-chip inline-flex max-w-full items-center gap-1 rounded-full border border-ldvh-border bg-ldvh-bg px-2 py-0.5 text-ldvh-text-secondary"
        >
          <span className="min-w-0 truncate">{getStatus(status)}</span>
          <span className="font-mono text-ldvh-text-primary">{count}</span>
        </span>
      ))}
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

function RelatedObjectRow({
  item,
  locale,
  getStatus,
  muted = false,
  onOpen,
}: {
  item: RelatedObjectSummary;
  locale: string;
  getStatus: (status: string) => string;
  muted?: boolean;
  onOpen: (event: OpenEvent, item: RelatedObjectSummary) => void;
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={(event) => onOpen(event, item)}
      onKeyDown={(event) => handleKeyboardOpen(event, () => onOpen(event, item))}
      className={`group/row flex min-w-0 cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/35 ${
        muted ? 'opacity-70' : ''
      }`}
    >
      <div className="min-w-0 flex-1">
        <span className="ldvh-card-title block min-w-0 truncate transition-colors group-hover/row:text-ldvh-accent">
          {getLocalizedTitle(item, locale)}
        </span>
        <span className="ldvh-meta-muted block min-w-0 truncate">{item.id}</span>
      </div>
      <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
      <CopyPathButton path={item.path} />
      <ArrowRight size={14} className="shrink-0 text-ldvh-text-secondary transition-colors group-hover/row:text-ldvh-accent" />
    </div>
  );
}

function ObjectCardFrame({
  obj,
  locale,
  getStatus,
  onOpen,
  children,
}: {
  obj: ObjectItem;
  locale: string;
  getStatus: (status: string) => string;
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
          <StatusBadge status={obj.status} statusLabel={getStatus(obj.status)} />
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
    fetchObjects(currentType, activeStatus ?? undefined)
      .then((result) => {
        setItems(result.data?.items ?? []);
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
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} getStatus={getStatus} onOpen={openObject}>
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
      const visibleTasks = tasks.slice(0, 5);
      const moreCount = Math.max(0, tasks.length - visibleTasks.length);
      const taskTotal = obj.taskTotal ?? tasks.length;
      const taskClosed = obj.taskClosed ?? 0;

      return (
        <ObjectCardFrame key={obj.id} obj={obj} locale={locale} getStatus={getStatus} onOpen={openObject}>
          <div className="flex flex-wrap gap-2">
            <SummaryPill icon={<ListChecks size={12} />} label={t('objectList.taskCount', { count: String(taskTotal) })} />
            {(obj.taskActive ?? 0) > 0 && (
              <SummaryPill icon={<CircleDot size={12} />} label={t('objectList.activeCount', { count: String(obj.taskActive) })} tone="active" />
            )}
            {(obj.taskReviewNeeded ?? 0) > 0 && (
              <SummaryPill icon={<CheckCircle2 size={12} />} label={t('objectList.reviewCount', { count: String(obj.taskReviewNeeded) })} tone="review" />
            )}
            {(obj.taskRisk ?? 0) > 0 && (
              <SummaryPill icon={<ShieldAlert size={12} />} label={t('objectList.riskCount', { count: String(obj.taskRisk) })} tone="risk" />
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <RecordPill label={t('objectList.successCriteria')} recorded={Boolean(obj.hasSuccessCriteria)} t={t} />
            <RecordPill label={t('objectList.completionEvidence')} recorded={Boolean(obj.hasCompletionEvidence)} t={t} />
          </div>
          <StatusCountChips counts={obj.taskByStatus} getStatus={getStatus} />
          <div className="min-w-0">
            <div className="mb-2 flex min-w-0 items-center justify-between gap-2">
              <span className="ldvh-caption-strong min-w-0 truncate">{t('objectList.relatedTasks')}</span>
              {taskTotal > 0 && (
                <span className="ldvh-meta shrink-0">
                  {t('objectList.closedProgress', { closed: String(taskClosed), total: String(taskTotal) })}
                </span>
              )}
            </div>
            <ProgressBar closed={taskClosed} total={taskTotal} />
            <div className="mt-2 min-w-0 divide-y divide-ldvh-border/60">
              {visibleTasks.length > 0 ? (
                visibleTasks.map((task) => (
                  <RelatedObjectRow
                    key={task.id}
                    item={task}
                    locale={locale}
                    getStatus={getStatus}
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
      <ObjectCardFrame key={obj.id} obj={obj} locale={locale} getStatus={getStatus} onOpen={openObject}>
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
        />
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
