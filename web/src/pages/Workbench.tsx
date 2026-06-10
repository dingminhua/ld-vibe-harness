import MetricCard from '@/components/MetricCard';
import PageHeader from '@/components/PageHeader';
import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  GitBranch,
  GitCommit,
  Layers3,
  Link2,
  MousePointer2,
  Network,
  ShieldCheck,
  Sparkles,
  Target,
} from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
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

function getLocalizedTitle(item: { title?: string; title_en?: string; title_zh?: string }, locale: string): string {
  if (locale === 'en') return item.title_en || item.title || '';
  return item.title_zh || item.title || '';
}

export default function Workbench() {
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

  const taskStats = data?.stats.find((item) => item.type === 'task');
  const activeTasks = useMemo(
    () => data?.actionItems.filter((item) => item.type === 'task') ?? [],
    [data]
  );
  const recentTasks = useMemo(
    () => data?.recentItems.filter((item) => item.type === 'task') ?? [],
    [data]
  );
  const selectedTask = activeTasks[0] ?? recentTasks[0] ?? null;
  const relatedObjects = useMemo(
    () => data?.recentItems.filter((item) => selectedTask ? item.id !== selectedTask.id : item.type !== 'task').slice(0, 5) ?? [],
    [data, selectedTask]
  );

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

  if (!data) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-ldvh-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="ldvh-page-frame">
      <div className="ldvh-page-toolbar">
        <div>
          <div className="ldvh-chip mb-2 inline-flex items-center gap-2 rounded-full border border-ldvh-accent/30 bg-ldvh-accent/10 px-3 py-1 text-ldvh-accent">
            <Sparkles size={13} />
            {t('workbench.badge')}
          </div>
          <PageHeader title={t('workbench.title')} subtitle={t('workbench.subtitle')} />
        </div>
        <button
          onClick={() => navigate('/')}
          className="ldvh-body-muted rounded-md border border-ldvh-border px-3 py-2 transition-colors hover:bg-ldvh-border/40 hover:text-ldvh-text-primary"
        >
          {t('workbench.backToDashboard')}
        </button>
      </div>

      <div className="ldvh-metric-grid mb-6">
        <MetricCard icon={<Target size={16} className="text-ldvh-accent" />} label={t('workbench.openTasks')} value={taskStats?.total ?? 0} detail={t('workbench.taskSignal')} />
        <MetricCard icon={<ClipboardCheck size={16} className="text-ldvh-accent" />} label={t('workbench.actionItems')} value={data.actionItems.length} detail={t('workbench.actionSignal')} />
        <MetricCard icon={<GitCommit size={16} className="text-ldvh-accent" />} label={t('workbench.recentChanges')} value={data.recentChanges.length} detail={t('workbench.changeSignal')} />
        <MetricCard icon={<ShieldCheck size={16} className="text-ldvh-accent" />} label={t('workbench.validation')} value={data.validation.ok ? t('dashboard.pass') : t('dashboard.fail')} detail={`${data.validation.errors} ${t('dashboard.errors')} · ${data.validation.warnings} ${t('dashboard.warnings')}`} tone={data.validation.ok ? 'green' : 'red'} />
      </div>

      <div className="ldvh-panel-grid">
        <section className="rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Layers3 size={16} className="text-ldvh-accent" />
              <h2 className="ldvh-section-title">{t('workbench.caseFile')}</h2>
            </div>
            {selectedTask && <StatusBadge status={selectedTask.status} statusLabel={getStatus(selectedTask.status)} size="md" />}
          </div>

          {selectedTask ? (
            <div>
              <button
                onClick={() => navigate(`/objects/task/${selectedTask.id}`)}
                className="mb-5 block w-full rounded-lg border border-ldvh-border bg-ldvh-bg p-4 text-left transition-colors hover:border-ldvh-accent/40"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <p className="ldvh-meta">{selectedTask.id}</p>
                  <ArrowRight size={16} className="text-ldvh-text-secondary" />
                </div>
                <h3 className="ldvh-reading-title">{getLocalizedTitle(selectedTask, locale) || selectedTask.id}</h3>
                <p className="ldvh-caption mt-2">{selectedTask.relativeTime}</p>
              </button>

              <div className="ldvh-section-grid">
                <InfoPanel title={t('workbench.acceptance')} icon={<CheckCircle2 size={16} className="text-ldvh-accent" />}>
                  <ProgressRow label={t('workbench.known')} value={activeTasks.length > 0 ? 1 : 0} total={Math.max(activeTasks.length, 1)} />
                  <p className="ldvh-caption mt-3">{t('workbench.acceptanceHint')}</p>
                </InfoPanel>
                <InfoPanel title={t('workbench.evidence')} icon={<GitCommit size={16} className="text-ldvh-accent" />}>
                  <div className="flex flex-col gap-2">
                    {data.recentChanges.slice(0, 3).map((entry) => (
                      <button key={entry.hash} onClick={() => navigate('/changelog')} className="rounded-md bg-ldvh-bg px-3 py-2 text-left transition-colors hover:bg-ldvh-border/30">
                        <span className="ldvh-chip mb-1 inline-flex rounded px-1.5 py-0.5" style={{ backgroundColor: `${CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other}20`, color: CATEGORY_COLORS[entry.category] || CATEGORY_COLORS.other }}>
                          {getCategoryLocale(entry.category, locale)}
                        </span>
                        <p className="ldvh-body line-clamp-2">{entry.description}</p>
                      </button>
                    ))}
                  </div>
                </InfoPanel>
                <InfoPanel title={t('workbench.actions')} icon={<MousePointer2 size={16} className="text-ldvh-accent" />}>
                  <div className="flex flex-col gap-2">
                    {[t('workbench.actionAddEvidence'), t('workbench.actionLinkTask'), t('workbench.actionReview')].map((label) => (
                      <button key={label} disabled className="ldvh-caption cursor-not-allowed rounded-md border border-dashed border-ldvh-border px-3 py-2 text-left opacity-75">
                        {label}
                      </button>
                    ))}
                  </div>
                </InfoPanel>
              </div>
            </div>
          ) : (
            <div className="ldvh-body-muted rounded-lg border border-dashed border-ldvh-border bg-ldvh-bg p-6 text-center">
              {t('workbench.noTask')}
            </div>
          )}
        </section>

        <section className="rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
          <div className="mb-4 flex items-center gap-2">
            <Network size={16} className="text-ldvh-accent" />
            <h2 className="ldvh-section-title">{t('workbench.relationships')}</h2>
          </div>
          <div className="flex flex-col gap-3">
            {relatedObjects.length > 0 ? relatedObjects.map((item) => (
              <button
                key={`${item.type}-${item.id}`}
                onClick={() => openPanel({ type: 'object', title: getLocalizedTitle(item, locale) || item.id, objectType: item.type, objectId: item.id })}
                className="flex items-center gap-3 rounded-lg border border-ldvh-border bg-ldvh-bg p-3 text-left transition-colors hover:border-ldvh-accent/40"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ldvh-accent/10 text-ldvh-accent">
                  <Link2 size={14} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <span className="ldvh-chip rounded px-1.5 py-0.5" style={{ backgroundColor: `${item.typeColor}20`, color: item.typeColor }}>
                      {t(TYPE_LABEL_KEYS[item.type] || 'nav.dashboard')}
                    </span>
                    <StatusBadge status={item.status} statusLabel={getStatus(item.status)} />
                  </div>
                  <p className="ldvh-body truncate">{getLocalizedTitle(item, locale) || item.id}</p>
                  <p className="ldvh-meta mt-1">{item.id}</p>
                </div>
              </button>
            )) : (
              <p className="ldvh-body-muted rounded-lg border border-dashed border-ldvh-border bg-ldvh-bg p-4">{t('workbench.noRelationships')}</p>
            )}
          </div>
        </section>
      </div>

      <section className="mt-6 rounded-lg border border-ldvh-border bg-ldvh-panel p-5">
        <div className="mb-4 flex items-center gap-2">
          <GitBranch size={16} className="text-ldvh-accent" />
          <h2 className="ldvh-section-title">{t('workbench.traceability')}</h2>
        </div>
        <div className="ldvh-metric-grid">
          {[t('nav.intents'), t('nav.tasks'), t('nav.changelog'), t('workbench.evidence')].map((label, index) => (
            <div key={label} className="relative rounded-lg border border-ldvh-border bg-ldvh-bg p-4">
              <p className="ldvh-caption">{t('workbench.step')} {index + 1}</p>
              <p className="ldvh-card-title mt-1">{label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}


function InfoPanel({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-ldvh-border bg-ldvh-bg p-4">
      <div className="mb-3 flex items-center gap-2">
        {icon}
        <h3 className="ldvh-card-title">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function ProgressRow({ label, value, total }: { label: string; value: number; total: number }) {
  const percent = total === 0 ? 0 : Math.min(100, Math.round((value / total) * 100));
  return (
    <div>
      <div className="ldvh-caption mb-2 flex items-center justify-between">
        <span>{label}</span>
        <span className="font-mono text-ldvh-text-primary">{value}/{total}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-ldvh-border">
        <div className="h-full rounded-full bg-ldvh-accent" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
