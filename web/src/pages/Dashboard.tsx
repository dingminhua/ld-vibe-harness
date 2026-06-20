import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, AlertCircle, GitCommit, ArrowRightCircle,
} from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import StatusBadge from '@/components/StatusBadge';
import PageHeader from '@/components/PageHeader';
import CopyPathButton from '@/components/CopyPathButton';
import { ObjectTypeIcon } from '@/components/SemanticIcon';
import { fetchDashboard, type DashboardData } from '@/utils/api';
import { usePanel } from '@/utils/panelContext';
import { useI18n } from '@/i18n/context';
import { getObjectStatusLocale, type LocaleKey } from '@/i18n/locales';
import { CATEGORY_COLORS, getCategoryLocale } from '@/utils/categoryColors';
import { WORKPLAN_CURRENT_STATUSES } from '@/utils/workplanStatus';

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  workarea: 'nav.workareas',
  workplan: 'nav.workplans',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  memo: 'nav.memos',
  study: 'nav.studies',
};

const TYPE_ORDER = ['workarea', 'workplan', 'adr', 'pitfall', 'memo', 'study'];

const HIGHLIGHT_STATUSES = new Set([...WORKPLAN_CURRENT_STATUSES.filter((status) => status !== 'closed'), 'verifying', 'review_needed']);

function getLocalizedTitle(item: { id: string; title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  if (locale === 'zh') return item.title_zh || item.title || item.title_en || item.id;
  return item.title_en || item.title || item.title_zh || item.id;
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
  const statusCounts: Record<string, number> = {};
  for (const item of data.actionItems) {
    statusCounts[item.status] = (statusCounts[item.status] || 0) + 1;
  }
  const parts: string[] = [];
  const statusKeys: Array<{ status: string; key: LocaleKey }> = [
    { status: 'subagents_plan_reviewing', key: 'dashboard.summary.planReview' },
    { status: 'human_plan_confirming', key: 'dashboard.summary.planConfirming' },
    { status: 'executing', key: 'dashboard.summary.executing' },
    { status: 'result_self_checking', key: 'dashboard.summary.verifying' },
    { status: 'subagents_result_reviewing', key: 'dashboard.summary.resultReview' },
    { status: 'human_closure_confirming', key: 'dashboard.summary.closureConfirming' },
    { status: 'review_needed', key: 'dashboard.summary.reviewNeeded' },
    { status: 'planned', key: 'dashboard.summary.planned' },
  ];
  for (const { status, key } of statusKeys) {
    const count = statusCounts[status];
    if (count) {
      parts.push(t(key, { count: String(count) }));
    }
  }

  return (
    <div className="p-4 sm:p-6">
      <PageHeader title={t('dashboard.title')} />

      {/* 态势摘要行 */}
      {parts.length > 0 && (
        <p className="ldvh-caption mb-4">{parts.join(locale === 'zh' ? '，' : ', ')}</p>
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
                      <CopyPathButton path={item.path} label={t('common.copyObjectPath')} copiedLabel={t('common.copiedObjectPath')} />
                      <StatusBadge status={item.status} statusLabel={getObjectStatusLocale(item.type, item.status, locale)} objectType={item.type} />
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
              {data.recentItems.map((item) => (
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
                    <CopyPathButton path={item.path} label={t('common.copyObjectPath')} copiedLabel={t('common.copiedObjectPath')} />
                    <StatusBadge status={item.status} statusLabel={getObjectStatusLocale(item.type, item.status, locale)} objectType={item.type} />
                    <span className="ldvh-caption whitespace-nowrap">
                      {item.relativeTime}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
