import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  Archive,
  ArrowRightCircle,
  Boxes,
  CheckCircle2,
  Clock3,
  FlaskConical,
  ShieldAlert,
} from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import MetricCard from '@/components/MetricCard';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import PageHeader from '@/components/PageHeader';
import StatusBadge from '@/components/StatusBadge';
import { useI18n } from '@/i18n/context';
import type { LocaleKey } from '@/i18n/locales';
import { fetchDashboard, fetchObjects, type DashboardData, type ObjectItem } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import { usePanel } from '@/utils/panelContext';

type AttentionKind = 'review' | 'doing' | 'planned' | 'risk';

type AttentionItem = ObjectItem & {
  attentionKind: AttentionKind;
};

const ATTENTION_OBJECT_TYPES = ['workplan', 'adr', 'pitfall', 'memo', 'study'];

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  workarea: 'nav.workareas',
  workplan: 'nav.workplans',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  memo: 'nav.memos',
  study: 'nav.studies',
};

const TYPE_COLORS: Record<string, string> = {
  workarea: '#3b82f6',
  workplan: '#0ea5e9',
  adr: '#a855f7',
  pitfall: '#ef4444',
  memo: '#eab308',
  study: '#06b6d4',
};

const TERMINAL_STATUSES = new Set(['closed', 'rejected', 'superseded', 'deprecated', 'archived', 'discarded', 'resolved', 'accepted']);
const REVIEW_STATUSES = new Set(['review_needed', 'proposed', 'needs_human_gate']);
const DOING_STATUSES = new Set(['executing', 'verifying', 'active']);
const PLANNED_STATUSES = new Set(['planned', 'pending', 'draft']);
const RISK_STATUSES = new Set(['open', 'degraded', 'suspended']);

const ATTENTION_ORDER: Record<AttentionKind, number> = {
  risk: 0,
  review: 1,
  doing: 2,
  planned: 3,
};

function getLocalizedTitle(item: { id: string; title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  if (locale === 'en') return item.title_en || item.title || item.id;
  return item.title_zh || item.title || item.id;
}

function getAttentionKind(status: string): AttentionKind | null {
  if (TERMINAL_STATUSES.has(status)) return null;
  if (RISK_STATUSES.has(status)) return 'risk';
  if (REVIEW_STATUSES.has(status)) return 'review';
  if (DOING_STATUSES.has(status)) return 'doing';
  if (PLANNED_STATUSES.has(status)) return 'planned';
  return 'planned';
}

function compareAttentionItems(a: AttentionItem, b: AttentionItem): number {
  const byKind = ATTENTION_ORDER[a.attentionKind] - ATTENTION_ORDER[b.attentionKind];
  if (byKind !== 0) return byKind;
  return String(b.updated || '').localeCompare(String(a.updated || ''));
}

function groupItems(items: AttentionItem[]): Record<AttentionKind, AttentionItem[]> {
  return {
    review: items.filter((item) => item.attentionKind === 'review'),
    doing: items.filter((item) => item.attentionKind === 'doing'),
    planned: items.filter((item) => item.attentionKind === 'planned'),
    risk: items.filter((item) => item.attentionKind === 'risk'),
  };
}

function getCopy<T>(locale: string, zh: T, en: T): T {
  return locale === 'en' ? en : zh;
}

export default function AttentionTest() {
  const navigate = useNavigate();
  const { t, locale, getStatus } = useI18n();
  const { openPanel } = usePanel();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [items, setItems] = useState<AttentionItem[]>([]);
  const [terminalCount, setTerminalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      fetchDashboard(locale),
      Promise.all(ATTENTION_OBJECT_TYPES.map(async (type) => {
        const result = await fetchObjects(type);
        return (result.data?.items ?? []).map((item) => ({ ...item, type }));
      })),
    ])
      .then(([dashboardResult, objectGroups]) => {
        if (cancelled) return;
        const allObjects = objectGroups.flat();
        const nextItems: AttentionItem[] = [];
        let nextTerminalCount = 0;

        for (const item of allObjects) {
          const status = String(item.status || 'unknown');
          const attentionKind = getAttentionKind(status);
          if (!attentionKind) {
            nextTerminalCount += 1;
            continue;
          }
          nextItems.push({ ...item, attentionKind });
        }

        setDashboard(dashboardResult);
        setItems(nextItems.sort(compareAttentionItems));
        setTerminalCount(nextTerminalCount);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [locale]);

  const grouped = useMemo(() => groupItems(items), [items]);
  const landing = dashboard?.landing;
  const validationIssueCount = (dashboard?.validation.errors ?? 0) + (dashboard?.validation.warnings ?? 0);
  const landingRiskCount = (landing?.gapTotal ?? 0) + Object.values(landing?.capabilityStatus ?? {}).filter((status) => status === 'open' || status === 'degraded').length;
  const riskSignalCount = validationIssueCount + landingRiskCount;
  const primaryQueue = items.slice(0, 12);

  const copy = {
    badge: getCopy(locale, '测试视图 · 不替换主页', 'Test view · Dashboard unchanged'),
    title: getCopy(locale, '待处理测试台', 'Attention Test'),
    subtitle: getCopy(
      locale,
      '按“现在要处理什么”组织对象：先看待确认、执行中、计划项和风险信号。',
      'Organize objects by what needs attention now: review, in progress, planned work, and risk signals.'
    ),
    back: getCopy(locale, '返回当前仪表盘', 'Back to dashboard'),
    queue: getCopy(locale, '关注队列', 'Attention Queue'),
    lanes: getCopy(locale, '状态泳道', 'Status Lanes'),
    risks: getCopy(locale, '风险信号', 'Risk Signals'),
    empty: getCopy(locale, '当前没有需要处理的对象。', 'No objects currently need attention.'),
    hiddenTerminal: getCopy(locale, '已隐藏终态', 'Terminal hidden'),
    hiddenTerminalDetail: getCopy(locale, '已关闭、已拒绝、已替代等不进入主队列', 'Closed, rejected, superseded, and archived items stay out of the main queue'),
    currentDashboard: getCopy(locale, '当前主页', 'Current dashboard'),
    currentDashboardDetail: getCopy(locale, '保留原仪表盘作为稳定视图', 'Keep the existing dashboard as the stable view'),
    objectLists: getCopy(locale, '对象列表', 'Object lists'),
    objectListsDetail: getCopy(locale, '需要全量盘点时再进入对象页', 'Use object pages when full inventory is needed'),
    reviewLane: getCopy(locale, '待确认', 'Needs Review'),
    doingLane: getCopy(locale, '执行 / 验证中', 'Doing / Verifying'),
    plannedLane: getCopy(locale, '计划 / 草稿', 'Planned / Draft'),
    riskLane: getCopy(locale, '风险 / 阻塞', 'Risk / Blocked'),
    landingGaps: getCopy(locale, '落地缺口', 'Landing gaps'),
    validationIssues: getCopy(locale, '校验问题', 'Validation issues'),
    capabilityIssues: getCopy(locale, '能力缺口', 'Capability issues'),
    noLaneItems: getCopy(locale, '暂无对象', 'No objects'),
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="ldvh-body-muted">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ldvh-page-frame min-w-0 overflow-x-hidden">
      <div className="ldvh-page-toolbar mb-6 min-w-0">
        <div className="min-w-0">
          <div className="ldvh-chip mb-2 inline-flex items-center gap-2 rounded-full border border-ldvh-accent/30 bg-ldvh-accent/10 px-3 py-1 text-ldvh-accent">
            <FlaskConical size={13} />
            {copy.badge}
          </div>
          <PageHeader title={copy.title} subtitle={copy.subtitle} />
        </div>
        <button
          onClick={() => navigate('/')}
          className="ldvh-body-muted rounded-md border border-ldvh-border px-3 py-2 transition-colors hover:bg-ldvh-border/40 hover:text-ldvh-text-primary"
        >
          {copy.back}
        </button>
      </div>

      <div className="ldvh-metric-grid mb-6 min-w-0">
        <MetricCard icon={<ArrowRightCircle size={16} />} value={items.length} label={copy.queue} detail={getCopy(locale, '非终态对象', 'Non-terminal objects')} />
        <MetricCard icon={<CheckCircle2 size={16} />} value={grouped.review.length} label={copy.reviewLane} detail={getCopy(locale, '需要判断或关闭', 'Needs decision or close check')} tone={grouped.review.length > 0 ? 'red' : 'green'} />
        <MetricCard icon={<Clock3 size={16} />} value={grouped.doing.length} label={copy.doingLane} detail={getCopy(locale, '正在推进的工作', 'Work currently moving')} />
        <MetricCard icon={<ShieldAlert size={16} />} value={riskSignalCount} label={copy.risks} detail={getCopy(locale, '校验与落地风险', 'Validation and landing risk')} tone={riskSignalCount > 0 ? 'red' : 'green'} />
      </div>

      <div className="ldvh-panel-grid min-w-0">
        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <ArrowRightCircle size={16} className="text-ldvh-accent" />
              <h2 className="ldvh-section-title">{copy.queue}</h2>
            </div>
            <span className="ldvh-meta-primary">{items.length}</span>
          </div>
          {primaryQueue.length === 0 ? (
            <p className="ldvh-body-muted rounded-lg border border-dashed border-ldvh-border bg-ldvh-bg p-6 text-center">
              {copy.empty}
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {primaryQueue.map((item) => (
                <AttentionRow
                  key={`${item.type}-${item.id}`}
                  item={item}
                  typeLabel={t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                  typeColor={TYPE_COLORS[item.type] || '#6b7280'}
                  title={getLocalizedTitle(item, locale)}
                  statusLabel={getStatus(item.status)}
                  onOpen={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale), objectType: item.type, objectId: item.id })}
                />
              ))}
            </div>
          )}
        </section>

        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center gap-2">
            <Boxes size={16} className="text-ldvh-accent" />
            <h2 className="ldvh-section-title">{copy.lanes}</h2>
          </div>
          <div className="grid min-w-0 gap-3">
            <Lane title={copy.riskLane} items={grouped.risk} emptyText={copy.noLaneItems} locale={locale} getStatus={getStatus} openPanel={openPanel} />
            <Lane title={copy.reviewLane} items={grouped.review} emptyText={copy.noLaneItems} locale={locale} getStatus={getStatus} openPanel={openPanel} />
            <Lane title={copy.doingLane} items={grouped.doing} emptyText={copy.noLaneItems} locale={locale} getStatus={getStatus} openPanel={openPanel} />
            <Lane title={copy.plannedLane} items={grouped.planned} emptyText={copy.noLaneItems} locale={locale} getStatus={getStatus} openPanel={openPanel} />
          </div>
        </section>
      </div>

      <div className="ldvh-section-grid mt-6 min-w-0">
        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center gap-2">
            <ShieldAlert size={16} className="text-ldvh-accent" />
            <h2 className="ldvh-section-title">{copy.risks}</h2>
          </div>
          <div className="ldvh-mini-grid min-w-0">
            <RiskTile label={copy.landingGaps} value={landing?.gapTotal ?? 0} tone={(landing?.gapTotal ?? 0) > 0 ? 'red' : 'green'} />
            <RiskTile label={copy.validationIssues} value={validationIssueCount} tone={validationIssueCount > 0 ? 'red' : 'green'} />
            <RiskTile
              label={copy.capabilityIssues}
              value={Object.values(landing?.capabilityStatus ?? {}).filter((status) => status === 'open' || status === 'degraded').length}
              tone={Object.values(landing?.capabilityStatus ?? {}).some((status) => status === 'open' || status === 'degraded') ? 'red' : 'green'}
            />
          </div>
        </section>

        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center gap-2">
            <Archive size={16} className="text-ldvh-accent" />
            <h2 className="ldvh-section-title">{copy.hiddenTerminal}</h2>
          </div>
          <div className="ldvh-mini-grid min-w-0">
            <MetricCard value={terminalCount} label={copy.hiddenTerminal} detail={copy.hiddenTerminalDetail} size="compact" />
            <MetricCard value={copy.currentDashboard} label={copy.currentDashboardDetail} size="compact" onClick={() => navigate('/')} />
            <MetricCard value={copy.objectLists} label={copy.objectListsDetail} size="compact" onClick={() => navigate('/objects/task')} />
          </div>
        </section>
      </div>
    </div>
  );
}

function AttentionRow({
  item,
  typeLabel,
  typeColor,
  title,
  statusLabel,
  onOpen,
}: {
  item: AttentionItem;
  typeLabel: string;
  typeColor: string;
  title: string;
  statusLabel: string;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group flex w-full min-w-0 items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-bg p-3 text-left transition-colors hover:border-ldvh-accent/40"
    >
      <span className="h-9 w-1 shrink-0 rounded-full bg-ldvh-accent" />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-2">
          <span className="ldvh-chip rounded px-1.5 py-0.5" style={{ backgroundColor: `${typeColor}20`, color: typeColor }}>
            <ObjectTypeIcon type={item.type} size={12} className="mr-1.5 inline shrink-0 align-[-2px]" />
            {typeLabel}
          </span>
          <span className="ldvh-meta-primary">{item.id}</span>
        </div>
        <p className="ldvh-body truncate transition-colors group-hover:text-ldvh-accent">{title}</p>
        <p className="ldvh-meta mt-1">{formatDateTime(item.updated)}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <CopyPathButton path={item.path} />
        <StatusBadge status={item.status} statusLabel={statusLabel} />
      </div>
    </button>
  );
}

function Lane({
  title,
  items,
  emptyText,
  locale,
  getStatus,
  openPanel,
}: {
  title: string;
  items: AttentionItem[];
  emptyText: string;
  locale: string;
  getStatus: (status: string) => string;
  openPanel: (payload: { type: 'object'; title: string; objectType: string; objectId: string }) => void;
}) {
  return (
    <div className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-bg p-3">
      <div className="mb-2 flex min-w-0 items-center justify-between gap-2">
        <h3 className="ldvh-card-title min-w-0 truncate">{title}</h3>
        <span className="ldvh-meta-primary">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="ldvh-caption">{emptyText}</p>
      ) : (
        <div className="flex flex-col gap-1.5">
          {items.slice(0, 4).map((item) => {
            const titleText = getLocalizedTitle(item, locale);
            return (
              <button
                key={`${item.type}-${item.id}`}
                type="button"
                onClick={() => openPanel({ type: 'object', title: titleText, objectType: item.type, objectId: item.id })}
                className="flex min-w-0 items-center justify-between gap-3 rounded-md px-2 py-1.5 text-left transition-colors hover:bg-ldvh-border/30"
              >
                <span className="ldvh-body flex min-w-0 flex-1 items-center gap-2 truncate">
                  <ObjectTypeIcon type={item.type} size={13} className="shrink-0 text-ldvh-accent" />
                  <span className="min-w-0 truncate">{titleText}</span>
                </span>
                <span className="shrink-0">
                  <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                </span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RiskTile({ label, value, tone }: { label: string; value: number; tone: 'green' | 'red' }) {
  return (
    <div className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-bg p-4">
      <p className={`font-mono text-xl font-semibold ${tone === 'red' ? 'text-red-400' : 'text-emerald-400'}`}>{value}</p>
      <p className="ldvh-caption mt-1">{label}</p>
    </div>
  );
}
