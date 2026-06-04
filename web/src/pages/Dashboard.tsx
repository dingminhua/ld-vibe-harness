import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, CheckCircle, AlertCircle, AlertTriangle, Shield } from 'lucide-react';
import StatsCard from '@/components/StatsCard';
import StatusBadge from '@/components/StatusBadge';
import { fetchDashboard, type DashboardData } from '@/utils/api';
import { useI18n } from '@/i18n/context';
import type { LocaleKey } from '@/i18n/locales';

const TYPE_LABEL_KEYS: Record<string, LocaleKey> = {
  intent: 'nav.intents',
  task: 'nav.tasks',
  adr: 'nav.adrs',
  pitfall: 'nav.pitfalls',
  memo: 'nav.memos',
  profile: 'nav.profiles',
};

const TYPE_ORDER = ['intent', 'task', 'adr', 'pitfall', 'memo', 'profile'];

/** 根据语言获取标题（优先 title_en，回退 title 中文） */
function getLocalizedTitle(item: { title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  if (locale === 'en') {
    return (item as { title_en?: string }).title_en || item.title || '';
  }
  return (item as { title_zh?: string }).title_zh || item.title || '';
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t, locale, getStatus } = useI18n();

  useEffect(() => {
    fetchDashboard()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

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

  return (
    <div className="p-6">
      <h1 className="mb-6 text-xl font-semibold text-ldvh-text-primary">{t('dashboard.title')}</h1>

      {/* Profile card */}
      {data.profile && (
        <div className="mb-6 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
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
        {/* Recent activity */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
          <div className="mb-3 flex items-center gap-2">
            <Activity size={16} className="text-ldvh-accent" />
            <h3 className="text-sm font-medium text-ldvh-text-primary">{t('dashboard.recentActivity')}</h3>
          </div>
          {data.recentItems.length === 0 ? (
            <p className="text-sm text-ldvh-text-secondary">{t('dashboard.noRecentActivity')}</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {data.recentItems.map((item) => (
                <li
                  key={`${item.type}-${item.id}`}
                  className="flex cursor-pointer items-center justify-between rounded-md px-3 py-1.5 transition-colors hover:bg-ldvh-border/30"
                  onClick={() => navigate(`/objects/${item.type}/${item.id}`)}
                >
                  <div className="flex min-w-0 flex-1 items-center gap-2.5">
                    <span className="whitespace-nowrap font-mono text-xs text-ldvh-text-secondary">{t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}</span>
                    <span className="truncate text-sm text-ldvh-text-primary">
                      {getLocalizedTitle(item, locale) || item.id}
                    </span>
                  </div>
                  <div className="flex shrink-0 items-center gap-2.5">
                    <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                    <span className="whitespace-nowrap font-mono text-xs text-ldvh-text-secondary">
                      {item.updated}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Validation status */}
        <div className="rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
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
        </div>
      </div>
    </div>
  );
}
