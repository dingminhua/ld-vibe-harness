import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, AlertCircle, GitCommit, ArrowRightCircle,
} from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import StatusBadge from '@/components/StatusBadge';
import PageHeader from '@/components/PageHeader';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import {
  fetchDashboard,
  type DashboardData,
  type DashboardFactItem,
  type DashboardObjectType,
} from '@/utils/api';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import { getLocaleListSeparator, getLocalizedObjectTitle } from '@/i18n/locales';
import { getObjectStatusLocale, type LocaleKey } from '@/i18n/locales';
import { CATEGORY_COLORS, getCategoryLocale } from '@/utils/categoryColors';

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  workcase: 'nav.workcases',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  spark: 'nav.sparks',
  study: 'nav.studies',
};

const TYPE_ORDER: DashboardObjectType[] = ['spark', 'workcase', 'adr', 'pitfall', 'study'];

const HIGHLIGHT_PROGRESS_GROUPS = new Set(['plan_confirmation', 'progressing', 'closure_confirmation']);

function getLocalizedTitle(item: { id: string; title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  return getLocalizedObjectTitle(item, locale, item.id);
}

function getDashboardDisplayState(item: DashboardFactItem): string {
  return item.type === 'workcase'
    ? item.progress_group ?? 'unknown'
    : item.status ?? 'unknown';
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

  // 态势摘要
  const progressGroupCounts: Record<string, number> = {};
  for (const item of data.actionItems) {
    if (item.type !== 'workcase' || !item.progress_group) continue;
    progressGroupCounts[item.progress_group] = (progressGroupCounts[item.progress_group] || 0) + 1;
  }
  const parts: string[] = [];
  const progressGroupKeys: Array<{ progressGroup: string; key: LocaleKey }> = [
    { progressGroup: 'plan_confirmation', key: 'dashboard.summary.planConfirming' },
    { progressGroup: 'progressing', key: 'dashboard.summary.progressing' },
    { progressGroup: 'closure_confirmation', key: 'dashboard.summary.closureConfirming' },
  ];
  for (const { progressGroup, key } of progressGroupKeys) {
    const count = progressGroupCounts[progressGroup];
    if (count) {
      parts.push(t(key, { count: String(count) }));
    }
  }

  return (
    <div className="p-4 sm:p-6">
      <PageHeader title={t('dashboard.title')} />

      {/* 态势摘要行 */}
      {parts.length > 0 && (
        <p className="ldvh-caption mb-4">{parts.join(getLocaleListSeparator(locale))}</p>
      )}

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
              distribution={type === 'workcase' ? stat?.byProgressGroup ?? {} : stat?.byStatus ?? {}}
              coverageStatus={stat?.coverageStatus}
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
                const displayState = getDashboardDisplayState(item);
                const isHighlight = item.type === 'workcase' && HIGHLIGHT_PROGRESS_GROUPS.has(displayState);
                return (
                  <li
                    key={`${item.type}-${item.id}`}
                    className={`flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-ldvh-border/30 ${isHighlight ? 'border-l-2 border-ldvh-accent' : ''}`}
                    onClick={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale) || item.id, objectType: item.type, objectId: item.id })}
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <span
                        className="ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded px-1.5 py-0.5"
                        style={{
                          backgroundColor: `${item.typeColor}20`,
                          color: item.typeColor,
                        }}
                      >
                        <ObjectTypeIcon type={item.type} size={12} className="shrink-0" />
                        {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                      </span>
                      <span className="ldvh-body truncate">
                        {getLocalizedTitle(item, locale) || item.id}
                      </span>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <StatusBadge status={displayState} statusLabel={getObjectStatusLocale(item.type, displayState, locale)} objectType={item.type} />
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

        {/* Recent commits */}
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

      {/* Recent activity */}
      <div className="ldvh-dashboard-section-grid mt-6">
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Activity size={16} className="text-ldvh-accent" />
            <h3 className="ldvh-section-title">{t('dashboard.recentActivity')}</h3>
          </div>
          {data.recentItems.length === 0 ? (
            <p className="ldvh-body-muted">{t('dashboard.noRecentActivity')}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.recentItems.map((item) => {
                const displayState = getDashboardDisplayState(item);
                return (
                  <li
                    key={`${item.type}-${item.id}`}
                    className="flex cursor-pointer items-center justify-between gap-4 rounded-md px-3 py-2 transition-colors hover:bg-ldvh-border/30"
                    onClick={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale) || item.id, objectType: item.type, objectId: item.id })}
                  >
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <span
                        className="ldvh-chip inline-flex shrink-0 items-center gap-1.5 rounded px-1.5 py-0.5"
                        style={{
                          backgroundColor: `${item.typeColor}20`,
                          color: item.typeColor,
                        }}
                      >
                        <ObjectTypeIcon type={item.type} size={12} className="shrink-0" />
                        {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                      </span>
                      <span className="ldvh-body truncate">
                        {getLocalizedTitle(item, locale) || item.id}
                      </span>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <StatusBadge status={displayState} statusLabel={getObjectStatusLocale(item.type, displayState, locale)} objectType={item.type} />
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
      </div>
    </div>
  );
}
