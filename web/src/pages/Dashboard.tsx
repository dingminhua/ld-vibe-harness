import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, CheckCircle, AlertCircle, AlertTriangle, Shield, GitCommit, ArrowRightCircle,
  Layers, TrendingUp, Target,
} from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import StatusBadge from '@/components/StatusBadge';
import StatusBanner from '@/components/StatusBanner';
import MemoCreate from '@/components/MemoCreate';
import { fetchDashboard, type DashboardData } from '@/utils/api';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import type { LocaleKey } from '@/i18n/locales';
import { CATEGORY_COLORS, getCategoryLocale } from '@/utils/categoryColors';

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  intent: 'nav.intents',
  task: 'nav.tasks',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  memo: 'nav.memos',
  profile: 'nav.profiles',
};

const TYPE_ORDER = ['intent', 'task', 'adr', 'pitfall', 'memo', 'profile'];

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
          <p className="font-mono text-xs text-red-400">{error}</p>
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
    <div className="p-6">
      <h1 className="mb-2 text-xl font-semibold text-ldvh-text-primary">{t('dashboard.title')}</h1>

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
        <p className="mb-4 text-xs text-ldvh-text-secondary">{parts.join(locale === 'zh' ? '，' : ', ')}</p>
      )}

      {/* Profile card + Landing Health 引导卡片 */}
      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        {/* Profile card */}
        {data.profile && (
          <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-ldvh-text-primary">
                  {getLocalizedTitle(data.profile, locale)}
                </h2>
                <p className="font-mono text-xs text-ldvh-text-secondary">{data.profile.id}</p>
              </div>
              <StatusBadge status={data.profile.status} size="md" />
            </div>
          </div>
        )}

        {/* 42 Landing 健康度引导卡片 */}
        {landing && (
          <div className="rounded-lg border border-ldvh-accent/30 bg-ldvh-accent/5 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Target size={16} className="text-ldvh-accent" />
              <h2 className="text-sm font-semibold text-ldvh-text-primary">{t('dashboard.landingGuide')}</h2>
            </div>
            <p className="mb-3 text-xs text-ldvh-text-secondary">{t('dashboard.landingGuideDesc')}</p>

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
              <div className="mt-1.5 flex items-center gap-3 text-[10px] text-ldvh-text-secondary">
                <span className="text-emerald-300">{capClosedCount} closed</span>
                {capDegradedCount > 0 && <span className="text-yellow-300">{capDegradedCount} degraded</span>}
                {capOpenCount > 0 && <span className="text-red-300">{capOpenCount} open</span>}
              </div>
            </div>

            {hasLandingGaps ? (
              <p className="mb-3 text-xs font-medium text-orange-300">
                {t('dashboard.landingNeedsWork', { count: String(totalGaps) })}
              </p>
            ) : (
              <p className="mb-3 text-xs font-medium text-emerald-300">{t('dashboard.landingAllClosed')}</p>
            )}

            <button
              onClick={() => navigate('/validate')}
              className="w-full rounded-md border border-ldvh-accent/40 bg-ldvh-accent/10 px-3 py-1.5 text-xs text-ldvh-accent transition-colors hover:bg-ldvh-accent/20"
            >
              {t('dashboard.landingGuideAction')}
            </button>
          </div>
        )}
      </div>

      {/* Stats grid */}
      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-7">
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

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Action Items */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <ArrowRightCircle size={16} className="text-ldvh-accent" />
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.actionItems')}</h3>
          </div>
          {data.actionItems.length === 0 ? (
            <p className="text-sm text-ldvh-text-secondary">{t('dashboard.noActionItems')}</p>
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
                        className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
                        style={{
                          backgroundColor: `${item.typeColor}20`,
                          color: item.typeColor,
                        }}
                      >
                        {item.type}
                      </span>
                      <span className="truncate text-sm text-ldvh-text-primary">
                        {getLocalizedTitle(item, locale) || item.id}
                      </span>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                      <span className="whitespace-nowrap text-xs text-ldvh-text-secondary">
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
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.recentChanges')}</h3>
          </div>
          {data.recentChanges.length === 0 ? (
            <p className="text-sm text-ldvh-text-secondary">{t('dashboard.noRecentChanges')}</p>
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
                      className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
                      style={{
                        backgroundColor: `${CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other}20`,
                        color: CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other,
                      }}
                    >
                      {getCategoryLocale(entry.category, locale)}
                    </span>
                    <span className="truncate text-sm text-ldvh-text-primary">{entry.description}</span>
                  </div>
                  <span className="whitespace-nowrap text-xs text-ldvh-text-secondary">
                    {entry.relativeTime}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Recent activity + Validation status + Landing compliance */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Recent activity */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Activity size={16} className="text-ldvh-accent" />
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.recentActivity')}</h3>
          </div>
          {data.recentItems.length === 0 ? (
            <p className="text-sm text-ldvh-text-secondary">{t('dashboard.noRecentActivity')}</p>
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
                      className="shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium"
                      style={{
                        backgroundColor: `${item.typeColor}20`,
                        color: item.typeColor,
                      }}
                    >
                      {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                    </span>
                    <span className="truncate text-sm text-ldvh-text-primary">
                      {getLocalizedTitle(item, locale) || item.id}
                    </span>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                    <span className="whitespace-nowrap text-xs text-ldvh-text-secondary">
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
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.validationStatus')}</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className={`flex flex-col items-center rounded-md p-3 ${data.validation.ok ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
              {data.validation.ok ? (
                <CheckCircle size={20} className="mb-1 text-green-400" />
              ) : (
                <AlertCircle size={20} className="mb-1 text-red-400" />
              )}
              <span className={`font-mono text-xl font-semibold ${data.validation.ok ? 'text-green-400' : 'text-red-400'}`}>
                {data.validation.ok ? t('dashboard.pass') : t('dashboard.fail')}
              </span>
              <span className="text-xs text-ldvh-text-secondary">{t('dashboard.status')}</span>
            </div>
            <div className="flex flex-col items-center rounded-md bg-red-500/10 p-3">
              <AlertCircle size={20} className="mb-1 text-red-400" />
              <span className="font-mono text-xl font-semibold text-red-400">{data.validation.errors}</span>
              <span className="text-xs text-ldvh-text-secondary">{t('dashboard.errors')}</span>
            </div>
            <div className="flex flex-col items-center rounded-md bg-yellow-500/10 p-3">
              <AlertTriangle size={20} className="mb-1 text-yellow-400" />
              <span className="font-mono text-xl font-semibold text-yellow-400">{data.validation.warnings}</span>
              <span className="text-xs text-ldvh-text-secondary">{t('dashboard.warnings')}</span>
            </div>
          </div>
          {!data.validation.ok && (
            <p className="mt-3 text-xs font-medium text-red-400">
              {t('dashboard.validationErrorHint')}
            </p>
          )}
        </div>

        {/* P3: 规范落地合规标识 */}
        {landing && (
          <div className={`rounded-lg border bg-ldvh-panel p-4 ${compliancePercent >= 80 ? 'border-ldvh-border' : 'border-orange-500/50'}`}>
            <div className="mb-3 flex items-center gap-2">
              <Layers size={16} className="text-ldvh-accent" />
              <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.complianceHeader')}</h3>
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
                <span className="absolute font-mono text-lg font-semibold text-ldvh-text-primary">{compliancePercent}%</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 text-center text-xs">
              <div className="rounded-md bg-ldvh-bg p-2">
                <p className="font-mono text-ldvh-text-primary">{totalReqs}</p>
                <p className="text-ldvh-text-secondary">{t('dashboard.complianceTotal', { total: String(totalReqs) })}</p>
              </div>
              <div className="rounded-md bg-ldvh-bg p-2">
                <p className="font-mono text-emerald-300">{closedReqs}</p>
                <p className="text-ldvh-text-secondary">{t('dashboard.complianceClosed', { count: String(closedReqs) })}</p>
              </div>
            </div>
            {totalGaps > 0 && (
              <p className="mt-2 text-center text-xs text-orange-300">
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
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.landingHealth')}</h3>
          </div>
          <p className="mb-3 text-xs text-ldvh-text-secondary">{t('dashboard.landingHealthDesc')}</p>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{totalReqs}</p>
              <p className="text-xs text-ldvh-text-secondary">{t('dashboard.landingRequirements')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className={`font-mono text-xl font-semibold ${totalGaps > 0 ? 'text-red-300' : 'text-emerald-300'}`}>{totalGaps}</p>
              <p className="text-xs text-ldvh-text-secondary">{t('dashboard.landingGaps')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className="font-mono text-xl font-semibold text-ldvh-text-primary">{capOpenCount > 0 ? `${capOpenCount} open` : 'OK'}</p>
              <p className="text-xs text-ldvh-text-secondary">{t('dashboard.landingCapStatus')}</p>
            </div>
            <div className="rounded-md bg-ldvh-bg p-3">
              <p className={`font-mono text-xl font-semibold ${landing.humanGateStatus === 'closed' ? 'text-emerald-300' : landing.humanGateStatus === 'open' ? 'text-red-300' : 'text-yellow-300'}`}>
                {landing.humanGateStatus || '—'}
              </p>
              <p className="text-xs text-ldvh-text-secondary">{t('dashboard.landingHGStatus')}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
