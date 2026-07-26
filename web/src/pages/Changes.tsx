import { useState } from 'react';
import {
  AlertCircle,
  Columns2,
  Diff,
  GitPullRequestArrow,
  Loader2,
  RefreshCcw,
  Rows3,
} from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import PageHeader from '@/components/PageHeader';
import { useI18n } from '@/i18n/context';
import { getGitStatusLabel } from '@/i18n/locales';
import {
  getDiffLineClass,
  getFileName,
  getSplitDiffCellClass,
  type DiffViewMode,
} from '@/pages/project-files/model';
import { useWorkspaceChanges } from '@/pages/changes/useWorkspaceChanges';
import { useProjectScope } from '@/utils/projectContext';

function EmptyState({ text }: { text: string }) {
  return (
    <div className="ldvh-body-muted flex min-h-56 items-center justify-center rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-6 text-center">
      {text}
    </div>
  );
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="flex min-h-56 items-center justify-center gap-2 text-ldvh-text-secondary">
      <Loader2 size={16} className="animate-spin" />
      <span className="ldvh-body-muted">{text}</span>
    </div>
  );
}

export default function Changes() {
  const { locale, t } = useI18n();
  const {
    projects,
    selectedProject,
    loading: projectsLoading,
    error: projectsError,
  } = useProjectScope();
  const projectId = selectedProject?.id ?? '';
  const {
    entries,
    entriesLoading,
    entriesError,
    selectedEntry,
    diff,
    splitDiffRows,
    openDiff,
    reload,
  } = useWorkspaceChanges(projectId);
  const [diffViewMode, setDiffViewMode] = useState<DiffViewMode>('unified');

  if (projectsLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 size={22} className="animate-spin text-ldvh-accent" />
      </div>
    );
  }

  if (projectsError) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <AlertCircle size={32} className="mx-auto mb-2 text-red-400" />
          <p className="ldvh-body-muted">{projectsError}</p>
        </div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="ldvh-page-frame">
        <PageHeader title={t('changes.title')} subtitle={t('changes.subtitle')} />
        <EmptyState text={t('changes.noProjects')} />
      </div>
    );
  }

  if (!projectId) {
    return (
      <div className="ldvh-page-frame">
        <PageHeader title={t('changes.title')} subtitle={t('changes.subtitle')} />
        <EmptyState text={t('changes.noProject')} />
      </div>
    );
  }

  return (
    <div className="ldvh-page-frame flex min-h-full min-w-0 flex-col overflow-x-hidden xl:h-full">
      <div className="ldvh-page-toolbar mb-4 min-w-0 shrink-0">
        <PageHeader title={t('changes.title')} subtitle={t('changes.subtitle')} compact />
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="ldvh-page-toolbar-badge">{t('changes.readOnly')}</span>
          <button
            type="button"
            onClick={reload}
            disabled={!projectId || entriesLoading}
            className="ldvh-page-toolbar-action"
          >
            <RefreshCcw size={14} className={entriesLoading ? 'animate-spin' : ''} />
            {t('changes.reload')}
          </button>
        </div>
      </div>

      <div className="grid min-w-0 gap-6 xl:min-h-0 xl:flex-1 xl:grid-cols-[minmax(18rem,28rem)_minmax(0,1fr)]">
        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
          <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
            <div className="flex min-w-0 items-center gap-2">
              <GitPullRequestArrow size={16} className="shrink-0 text-ldvh-accent" />
              <h2 className="ldvh-section-title">{t('changes.files')}</h2>
            </div>
            <span className="ldvh-meta-primary">{entries.length}</span>
          </div>
          <div className="min-w-0 overflow-y-auto p-3 xl:min-h-0 xl:flex-1">
            {!projectId ? (
              <EmptyState text={t('changes.noProject')} />
            ) : entriesLoading ? (
              <LoadingState text={t('changes.loading')} />
            ) : entriesError ? (
              <EmptyState text={entriesError} />
            ) : entries.length === 0 ? (
              <EmptyState text={t('changes.noChanges')} />
            ) : (
              <div className="space-y-1">
                {entries.map((entry) => {
                  const selected = selectedEntry?.projectId === entry.projectId
                    && selectedEntry.path === entry.path
                    && selectedEntry.status === entry.status;
                  return (
                    <div
                      key={`${entry.projectId}:${entry.status}:${entry.path}`}
                      className={`group flex w-full min-w-0 items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/30 ${
                        selected ? 'bg-ldvh-accent/10 text-ldvh-accent' : ''
                      }`}
                    >
                      <button
                        type="button"
                        aria-pressed={selected}
                        onClick={() => openDiff(entry)}
                        className="flex min-w-0 flex-1 items-center gap-3 text-left"
                      >
                        <span className="ldvh-meta-primary w-8 shrink-0 rounded bg-ldvh-bg px-1.5 py-0.5 text-center">
                          {entry.status}
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="ldvh-card-title block truncate transition-colors group-hover:text-ldvh-accent">
                            {getFileName(entry.path)}
                          </span>
                          <span className="ldvh-meta block truncate">
                            {getGitStatusLabel(entry.status, locale)} · {entry.path}
                          </span>
                        </span>
                      </button>
                      <CopyPathButton path={entry.absolutePath} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>

        <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
          <div className="flex min-w-0 flex-wrap items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
            <div className="flex min-w-0 items-center gap-2">
              <Diff size={16} className="shrink-0 text-ldvh-accent" />
              <div className="min-w-0">
                <h2 className="ldvh-section-title">{t('changes.diff')}</h2>
                {selectedEntry && <p className="ldvh-meta truncate">{selectedEntry.path}</p>}
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <div
                role="group"
                aria-label={t('changes.diffMode')}
                className="grid grid-cols-2 rounded-md border border-ldvh-border bg-ldvh-bg p-0.5"
              >
                <button
                  type="button"
                  aria-pressed={diffViewMode === 'unified'}
                  onClick={() => setDiffViewMode('unified')}
                  className={`ldvh-chip inline-flex items-center justify-center gap-1 rounded px-2 py-1 transition-colors ${
                    diffViewMode === 'unified'
                      ? 'bg-ldvh-panel text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
                  }`}
                >
                  <Rows3 size={13} />
                  {t('changes.unifiedDiff')}
                </button>
                <button
                  type="button"
                  aria-pressed={diffViewMode === 'split'}
                  onClick={() => setDiffViewMode('split')}
                  className={`ldvh-chip inline-flex items-center justify-center gap-1 rounded px-2 py-1 transition-colors ${
                    diffViewMode === 'split'
                      ? 'bg-ldvh-panel text-ldvh-accent'
                      : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
                  }`}
                >
                  <Columns2 size={13} />
                  {t('changes.splitDiff')}
                </button>
              </div>
              <CopyPathButton path={diff.data?.absolutePath} />
            </div>
          </div>
          <div className="min-h-[36rem] min-w-0 p-4 xl:min-h-0 xl:flex-1 xl:overflow-hidden">
            {!projectId ? (
              <EmptyState text={t('changes.noProject')} />
            ) : diff.loading ? (
              <LoadingState text={t('changes.loadingDiff')} />
            ) : diff.error ? (
              <EmptyState text={diff.error} />
            ) : !diff.data ? (
              <EmptyState text={t('changes.chooseFile')} />
            ) : diffViewMode === 'unified' ? (
              <pre className="ldvh-meta-primary h-full min-w-0 overflow-auto rounded-md bg-ldvh-bg p-4">
                {diff.data.diff.split('\n').map((line, index) => (
                  <span key={`${index}-${line.slice(0, 12)}`} className={`${getDiffLineClass(line)} block min-w-max whitespace-pre`}>
                    {line || ' '}
                  </span>
                ))}
              </pre>
            ) : (
              <div className="h-full min-w-0 overflow-y-auto overflow-x-hidden rounded-md bg-ldvh-bg">
                <div className="min-w-0">
                  <div className="ldvh-meta sticky top-0 z-10 grid grid-cols-[3rem_minmax(0,1fr)_3rem_minmax(0,1fr)] border-b border-ldvh-border bg-ldvh-panel/95 sm:grid-cols-[4rem_minmax(0,1fr)_4rem_minmax(0,1fr)]">
                    <div className="border-r border-ldvh-border px-2 py-2 text-right">-</div>
                    <div className="border-r border-ldvh-border px-3 py-2">{t('changes.before')}</div>
                    <div className="border-r border-ldvh-border px-2 py-2 text-right">+</div>
                    <div className="px-3 py-2">{t('changes.after')}</div>
                  </div>
                  <div className="ldvh-meta-primary">
                    {splitDiffRows.map((row, index) => {
                      if (row.kind !== 'line') {
                        return (
                          <div
                            key={`${row.kind}-${index}-${row.text.slice(0, 12)}`}
                            className={`whitespace-pre-wrap break-words border-b border-ldvh-border/40 px-3 py-1 ${
                              row.kind === 'hunk' ? 'bg-ldvh-accent/10 text-ldvh-accent' : 'text-sky-300'
                            }`}
                          >
                            {row.text || ' '}
                          </div>
                        );
                      }

                      return (
                        <div
                          key={`line-${index}-${row.oldCell.lineNumber ?? 'x'}-${row.newCell.lineNumber ?? 'x'}`}
                          className="grid grid-cols-[3rem_minmax(0,1fr)_3rem_minmax(0,1fr)] border-b border-ldvh-border/20 sm:grid-cols-[4rem_minmax(0,1fr)_4rem_minmax(0,1fr)]"
                        >
                          <div className="border-r border-ldvh-border/40 px-2 py-1 text-right text-ldvh-text-secondary">
                            {row.oldCell.lineNumber ?? ''}
                          </div>
                          <div className={`${getSplitDiffCellClass(row.oldCell)} border-r border-ldvh-border/40 px-3 py-1`}>
                            <span className="block whitespace-pre-wrap break-words">{row.oldCell.text ?? ' '}</span>
                          </div>
                          <div className="border-r border-ldvh-border/40 px-2 py-1 text-right text-ldvh-text-secondary">
                            {row.newCell.lineNumber ?? ''}
                          </div>
                          <div className={`${getSplitDiffCellClass(row.newCell)} px-3 py-1`}>
                            <span className="block whitespace-pre-wrap break-words">{row.newCell.text ?? ' '}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
