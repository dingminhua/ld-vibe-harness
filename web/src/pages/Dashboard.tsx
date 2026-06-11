import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, CheckCircle, AlertCircle, AlertTriangle, Shield, GitCommit, ArrowRightCircle,
  Layers, TrendingUp, Target,
} from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import StatusBadge from '@/components/StatusBadge';
import StatusBanner from '@/components/StatusBanner';
import PageHeader from '@/components/PageHeader';
import CopyPathButton from '@/components/CopyPathButton';
import { fetchDashboard, type DashboardData } from '@/utils/api';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import type { LocaleKey } from '@/i18n/locales';
import { CATEGORY_COLORS, getCategoryLocale } from '@/utils/categoryColors';

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  workarea: 'nav.workareas',
  taskplan: 'nav.taskplans',
  task: 'nav.tasks',
  subtask: 'nav.subtasks',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  memo: 'nav.memos',
};

const TYPE_ORDER = ['workarea', 'taskplan', 'task', 'subtask', 'adr', 'pitfall', 'memo'];

const HIGHLIGHT_STATUSES = new Set(['executing', 'verifying', 'review_needed']);

function getLocalizedTitle(item: { title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  if (locale === 'en') return (item as { title_en?: string }).title_en || item.title || '';
  return (item as { title_zh?: string }).title_zh || item.title || '';
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t, locale, getStatus } = useI18n();
  const { openPanel } = usePanel();

  useEffect(() => {
    fetchDashboard(locale)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [locale]);

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="text-ldvh-text-secondary">{t('common.loadFailed')}</p>
          <p className="ldvh-meta text-red-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  // 计算规范落地合规摘要
  const landing = (data as DashboardData & { landing?: {
    totalRequirements: number
    gapTotal: number
    gapByArea: Record<string, number>
    capabilityStatus: Record<string, string>
    humanGateStatus: string
    validationPlanStatus: Record<string, string>
  } | null }).landing;

  const totalReqs = landing?.totalRequirements ?? 0;
  const totalGaps = landing?.gapTotal ?? 0;
  const closedReqs = totalReqs - totalGaps;
  const compliancePercent = totalReqs > 0 ? Math.round((closedReqs / totalReqs) * 100) : 0;
  const hasLandingGaps = totalGaps > 0;

  // 能力状态汇总
  const capStatuses = landing?.capabilityStatus || {};
  const capOpenCount = Object.values(capStatuses).filter(s => s === 'open').length;
  const capClosedCount = Object.values(capStatuses).filter(s => s === 'closed').length;
  const capDegradedCount = Object.values(capStatuses).filter(s => s === 'degraded').length;

  // 态势摘要
  const statusCounts: Record<string, number> = {};
  for (const item of data.actionItems) {
    statusCounts[item.status] = (statusCounts[item.status] || 0) + 1;
  }
  const parts: string[] = [];
  const statusKeys: Array<{ status: string; key: 'dashboard.summary.executing' | 'dashboard.summary.verifying' | 'dashboard.summary.reviewNeeded' | 'dashboard.summary.planned' }> = [
    { status: 'executing', key: 'dashboard.summary.executing' },
    { status: 'verifying', key: 'dashboard.summary.verifying' },
    { status: 'review_needed', key: 'dashboard.summary.reviewNeeded' },
    { status: 'planned', key: 'dashboard.summary.planned' },
  ];
  for (const { status, key } of statusKeys) {
    const count = statusCounts[status];
    if (count) {
      parts.push(t(key, { count: String(count) }));
    }
  }
  if (data.validation.errors > 0) {
    parts.push(t('dashboard.summary.validationErrors', { count: String(data.validation.errors) }));
  }

  return (
    <div className="p-4 sm:p-6">
      <PageHeader title={t('dashboard.title')} />

      {/* 关键状态信号 */}
      {data.validation.errors > 0 && (
        <div className="mb-4">
          <StatusBanner
            status="open"
            title={t('dashboard.validationErrorHint')}
            description={t('dashboard.summary.validationErrors', { count: String(data.validation.errors) })}
            action={{ label: t('dashboard.landingGuideAction'), onClick: () => navigate('/validate') }}
          />
        </div>
      )}

      {/* 态势摘要行 */}
      {parts.length > 0 && (
        <p className="ldvh-caption mb-4">{parts.join(locale === 'zh' ? '，' : ', ')}</p>
      )}

      {/* Profile card + Landing Health 引导卡片 */}
      <div className="ldvh-dashboard-lead-grid mb-6">
        {/* Profile card */}
        {data.profile && (
          <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="ldvh-section-title">
                  {getLocalizedTitle(data.profile, locale)}
                </h2>
                <p className="ldvh-meta">{data.profile.id}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <CopyPathButton path={data.profile.path} />
                <StatusBadge status={data.profile.status} size="md" />
              </div>
            </div>
          </div>
        )}

        {/* 42 Landing 健康度引导卡片 */}
        {landing && (
          <div className="rounded-lg border border-ldvh-accent/30 bg-ldvh-accent/5 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Target size={16} className="text-ldvh-accent" />
              <h2 className="ldvh-section-title">{t('dashboard.landingGuide')}</h2>
            </div>
            <p className="ldvh-caption mb-3">{t('dashboard.landingGuideDesc')}</p>

            {/* 能力状态条 */}
            <div className="mb-3">
              <div className="flex h-1.5 overflow-hidden rounded-full bg-ldvh-border">
                {capClosedCount > 0 && (
                  <div className="h-full bg-emerald-500/70" style={{ width: `${(capClosedCount / (capClosedCount + capOpenCount + capDegradedCount || 1)) * 100}%` }} />
                )}
                {capDegradedCount > 0 && (
                  <div className="h-full bg-yellow-500/70" style={{ width: `${(capDegradedCount / (capClosedCount + capOpenCount + capDegradedCount || 1)) * 100}%` }} />
                )}
                {capOpenCount > 0 && (
                  <div className="h-full bg-red-500/70" style={{ width: `${(capOpenCount / (capClosedCount + capOpenCount + capDegradedCount || 1)) * 100}%` }} />
                )}
              </div>
              <div className="ldvh-caption mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
                <span className="text-emerald-300">{capClosedCount} {getStatus('closed')}</span>
                {capDegradedCount > 0 && <span className="text-yellow-300">{capDegradedCount} {getStatus('degraded')}</span>}
                {capOpenCount > 0 && <span className="text-red-300">{capOpenCount} {getStatus('open')}</span>}
              </div>
            </div>

            {hasLandingGaps ? (
              <p className="ldvh-caption-strong mb-3 text-orange-300">
                {t('dashboard.landingNeedsWork', { count: String(totalGaps) })}
              </p>
            ) : (
              <p className="ldvh-caption-strong mb-3 text-emerald-300">{t('dashboard.landingAllClosed')}</p>
            )}

            <button
              onClick={() => navigate('/validate')}
              className="ldvh-chip w-full rounded-md border border-ldvh-accent/40 bg-ldvh-accent/10 px-3 py-1.5 text-ldvh-accent transition-colors hover:bg-ldvh-accent/20"
            >
              {t('dashboard.landingGuideAction')}
            </button>
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="ldvh-dashboard-stats-grid mb-6">
        {TYPE_ORDER.map((type) => {
          const stat = data.stats.find(s => s.type === type);
          return (
            <StatsCard
              key={type}
              type={type}
              label={t(TYPE_LABEL_KEYS[type] || 'nav.dashboard')}
              count={stat?.total ?? 0}
              byStatus={stat?.byStatus ?? {}}
              getStatus={getStatus}
              onClick={() => navigate(`/objects/${type}`)}
            />
          );
        })}
      </div>

      <div className="ldvh-dashboard-panel-grid">
        {/* Action Items */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <ArrowRightCircle size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.actionItems')}</h3>
          </div>
          {data.actionItems.length === 0 ? (
            <p className="ldvh-body-muted">{t('dashboard.noActionItems')}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.actionItems.map((item) => {
                const isHighlight = HIGHLIGHT_STATUSES.has(item.status);
                return (
                  <li
                    key={`${item.type}-${item.id}`}
                    className={`flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-ldvh-border/30 ${isHighlight ? 'border-l-2 border-ldvh-accent' : ''}`}
                    onClick={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale) || item.id, objectType: item.type, objectId: item.id })}
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <span
                        className="ldvh-chip shrink-0 rounded px-1.5 py-0.5"
                        style={{
                          backgroundColor: `${item.typeColor}20`,
                          color: item.typeColor,
                        }}
                      >
                        {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                      </span>
                      <span className="ldvh-body truncate">
                        {getLocalizedTitle(item, locale) || item.id}
                      </span>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <CopyPathButton path={item.path} />
                      <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                      <span className="ldvh-caption whitespace-nowrap">
                        {item.relativeTime}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Recent Changes */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <GitCommit size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.recentChanges')}</h3>
          </div>
          {data.recentChanges.length === 0 ? (
            <p className="ldvh-body-muted">{t('dashboard.noRecentChanges')}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.recentChanges.map((entry) => (
                <li
                  key={entry.hash}
                  className="flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-ldvh-border/30"
                  onClick={() => navigate('/changelog')}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <span
                      className="ldvh-chip shrink-0 rounded px-1.5 py-0.5"
                      style={{
                        backgroundColor: `${CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other}20`,
                        color: CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other,
                      }}
                    >
                      {getCategoryLocale(entry.category, locale)}
                    </span>
                    <span className="ldvh-body truncate">{entry.description}</span>
                  </div>
                  <span className="ldvh-caption whitespace-nowrap">
                    {entry.relativeTime}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Recent activity + Validation status + Landing compliance */}
      <div className="ldvh-dashboard-section-grid mt-6">
        {/* Recent activity */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Activity size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.recentActivity')}</h3>
          </div>
          {data.recentItems.length === 0 ? (
            <p className="ldvh-body-muted">{t('dashboard.noRecentActivity')}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.recentItems.map((item) => (
                <li
                  key={`${item.type}-${item.id}`}
                  className="flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-ldvh-border/30"
                  onClick={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale) || item.id, objectType: item.type, objectId: item.id })}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-3">
                    <span
                      className="ldvh-chip shrink-0 rounded px-1.5 py-0.5"
                      style={{
                        backgroundColor: `${item.typeColor}20`,
                        color: item.typeColor,
                      }}
                    >
                      {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                    </span>
                    <span className="ldvh-body truncate">
                      {getLocalizedTitle(item, locale) || item.id}
                    </span>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <CopyPathButton path={item.path} />
                    <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                    <span className="ldvh-caption whitespace-nowrap">
                      {item.relativeTime}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Validation status */}
        <div className={`rounded-lg border bg-ldvh-panel p-4 ${data.validation.ok ? 'border-ldvh-border' : 'border-red-500'}`}>
          <div className="mb-3 flex items-center gap-2">
            <Shield size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.validationStatus')}</h3>
          </div>
          <div className="ldvh-dashboard-mini-grid">
            <div className={`flex flex-col items-center rounded-md p-3 ${data.validation.ok ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
              {data.validation.ok ? (
                <CheckCircle size={20} className="mb-1 text-green-400" />
              ) : (
                <AlertCircle size={20} className="mb-1 text-red-400" />
              )}
              <span className={`font-mono text-xl font-semibold ${data.validation.ok ? 'text-green-400' : 'text-red-400'}`}>
                {data.validation.ok ? t('dashboard.pass') : t('dashboard.fail')}
              </span>
              <span className="ldvh-caption">{t('dashboard.status')}</span>
            </div>
            <div className="flex flex-col items-center rounded-md bg-red-500/10 p-3">
              <AlertCircle size={20} className="mb-1 text-red-400" />
              <span className="font-mono text-xl font-semibold text-red-400">{data.validation.errors}</span>
              <span className="ldvh-caption">{t('dashboard.errors')}</span>
            </div>
            <div className="flex flex-col items-center rounded-md bg-yellow-500/10 p-3">
              <AlertTriangle size={20} className="mb-1 text-yellow-400" />
              <span className="font-mono text-xl font-semibold text-yellow-400">{data.validation.warnings}</span>
              <span className="ldvh-caption">{t('dashboard.warnings')}</span>
            </div>
          </div>
          {!data.validation.ok && (
            <p className="ldvh-caption-strong mt-3 text-red-400">
              {t('dashboard.validationErrorHint')}
            </p>
          )}
        </div>

        {/* P3: 规范落地合规标识 */}
        {landing && (
          <div className={`rounded-lg border bg-ldvh-panel p-4 ${compliancePercent >= 80 ? 'border-ldvh-border' : 'border-orange-500/50'}`}>
            <div className="mb-3 flex items-center gap-2">
              <Layers size={16} className="text-ldvh-accent" />
              <h3 className="ldvh-section-title">{t('dashboard.complianceHeader')}</h3>
            </div>
            {/* 合规百分比环 */}
            <div className="mb-3 flex items-center justify-center">
              <div className="relative flex h-20 w-20 items-center justify-center">
                <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.5" fill="none" stroke="currentColor" className="text-ldvh-border" strokeWidth="3" />
                  <circle
                    cx="18" cy="18" r="15.5"
                    fill="none"
                    stroke={compliancePercent >= 80 ? '#34d399' : compliancePercent >= 50 ? '#fbbf24' : '#f87171'}
                    strokeWidth="3"
                    strokeDasharray={`${compliancePercent} ${100 - compliancePercent}`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className="ldvh-card-title absolute font-mono text-ldvh-text-primary">{compliancePercent}%</span>
              </div>
            </div>
            <div className="ldvh-dashboard-mini-grid text-center">
              <div className="rounded-md bg-ldvh-bg p-2">
                <p className="font-mono text-ldvh-text-primary">{totalReqs}</p>
                <p className="ldvh-caption">{t('dashboard.complianceTotal', { total: String(totalReqs) })}</p>
              </div>
              <div className="rounded-md bg-ldvh-bg p-2">
                <p className="font-mono text-emerald-300">{closedReqs}</p>
                <p className="ldvh-caption">{t('dashboard.complianceClosed', { count: String(closedReqs) })}</p>
              </div>
            </div>
            {totalGaps > 0 && (
              <p className="ldvh-caption mt-2 text-center text-orange-300">
                {t('dashboard.complianceDegraded', { count: String(totalGaps) })}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Landing Health mini section (only if landing data but not shown in card above) */}
      {landing && (
        <div className="mt-6 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <TrendingUp size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.landingHealth')}</h3>
          </div>
          <p className="ldvh-caption mb-3">{t('dashboard.landingHealthDesc')}</p>
          <div className="ldvh-dashboard-metric-grid">
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{totalReqs}</p>
              <p className="ldvh-caption">{t('dashboard.landingRequirements')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className={`font-mono text-xl font-semibold ${totalGaps > 0 ? 'text-red-300' : 'text-emerald-300'}`}>{totalGaps}</p>
              <p className="ldvh-caption">{t('dashboard.landingGaps')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{capOpenCount > 0 ? `${capOpenCount} ${getStatus('open')}` : getStatus('closed')}</p>
              <p className="ldvh-caption">{t('dashboard.landingCapStatus')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className={`font-mono text-xl font-semibold ${landing.humanGateStatus === 'closed' ? 'text-emerald-300' : landing.humanGateStatus === 'open' ? 'text-red-300' : 'text-yellow-300'}`}>
                {landing.humanGateStatus ? getStatus(landing.humanGateStatus) : '—'}
              </p>
              <p className="ldvh-caption">{t('dashboard.landingHGStatus')}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
