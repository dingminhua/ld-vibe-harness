import {
  AlertCircle,
  ChevronRight,
  Code2,
  Columns2,
  Diff,
  FileCode2,
  FileText,
  Folder,
  FolderOpen,
  GitCommit,
  GitPullRequestArrow,
  Loader2,
  RefreshCcw,
  Rows3,
} from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import MarkdownPreview from '@/components/MarkdownPreview';
import PageHeader from '@/components/PageHeader';
import { useI18n } from '@/i18n/context';
import { getGitStatusLabel, getProjectFileKindLabel } from '@/i18n/locales';
import { type ProjectFileEntry } from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';
import {
  formatBytes,
  getDiffLineClass,
  getFileName,
  getSplitDiffCellClass,
  getSvgDataUrl,
  type ProjectFileEntryKind as EntryKind,
} from '@/pages/project-files/model';
import { useProjectFilesController } from '@/pages/project-files/useProjectFilesController';

function getKindLabel(kind: EntryKind, locale: string): string {
  return getProjectFileKindLabel(kind, locale);
}

function getStatusLabel(status: string, locale: string): string {
  return getGitStatusLabel(status, locale);
}

function getCommitFileStatusLabel(status: string, locale: string): string {
  return getGitStatusLabel(status, locale);
}

function FileIcon({ entry }: { entry: ProjectFileEntry }) {
  if (entry.type === 'directory') return <Folder size={15} className="text-ldvh-accent" />;
  if (entry.kind === 'markdown') return <FileText size={15} className="text-ldvh-accent" />;
  if (entry.kind === 'yaml' || entry.kind === 'svg' || entry.kind === 'text') {
    return <FileCode2 size={15} className="text-ldvh-text-secondary" />;
  }
  return <Code2 size={15} className="text-ldvh-text-secondary" />;
}

function Breadcrumbs({
  dir,
  onNavigate,
}: {
  dir: string;
  onNavigate: (nextDir: string) => void;
}) {
  const parts = dir ? dir.split('/').filter(Boolean) : [];
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1">
      <button
        type="button"
        onClick={() => onNavigate('')}
        className="ldvh-caption-strong rounded px-1.5 py-0.5 text-ldvh-accent transition-colors hover:bg-ldvh-border/40"
      >
        /
      </button>
      {parts.map((part, index) => {
        const nextDir = parts.slice(0, index + 1).join('/');
        return (
          <span key={nextDir} className="flex min-w-0 items-center gap-1">
            <ChevronRight size={12} className="text-ldvh-text-secondary" />
            <button
              type="button"
              onClick={() => onNavigate(nextDir)}
              className="ldvh-caption-strong max-w-40 truncate rounded px-1.5 py-0.5 text-ldvh-text-primary transition-colors hover:bg-ldvh-border/40"
            >
              {part}
            </button>
          </span>
        );
      })}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="ldvh-body-muted flex min-h-40 items-center justify-center rounded-md border border-dashed border-ldvh-border bg-ldvh-bg px-4 text-center">
      {text}
    </div>
  );
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center gap-2 text-ldvh-text-secondary">
      <Loader2 size={16} className="animate-spin" />
      <span className="ldvh-body-muted">{text}</span>
    </div>
  );
}

export default function ProjectFiles() {
  const { locale, t } = useI18n();
  const {
    projects, projectId, projectsLoading, projectsError, currentDir, entries, entriesLoading, entriesError,
    filePanel, gitEntries, gitLoading, gitError, commitEntries, commitsLoading, commitsError,
    selectedCommitHash, commitPanel, diffPanel, activeTab, diffViewMode, showHiddenFiles,
    selectedProject, splitDiffRows, setActiveTab, setDiffViewMode,
    handleProjectChange, handleNavigateDir, handleOpenEntry, handleOpenDiff, handleOpenCommit,
    handleOpenCommitFileDiff, handleRefresh, handleShowHiddenChange,
  } = useProjectFilesController();
  const copy = {
    title: t('projectFiles.title'),
    subtitle: t('projectFiles.subtitle'),
    project: t('projectFiles.project'),
    quickRoots: t('projectFiles.quickRoots'),
    showHiddenFiles: t('projectFiles.showHiddenFiles'),
    filesTab: t('projectFiles.filesTab'),
    changesTab: t('projectFiles.changesTab'),
    historyTab: t('projectFiles.historyTab'),
    fileBrowser: t('projectFiles.fileBrowser'),
    preview: t('projectFiles.preview'),
    pending: t('projectFiles.pending'),
    history: t('projectFiles.history'),
    changeDetail: t('projectFiles.changeDetail'),
    selectedCommitFiles: t('projectFiles.selectedCommitFiles'),
    diff: t('projectFiles.diff'),
    diffMode: t('projectFiles.diffMode'),
    unifiedDiff: t('projectFiles.unifiedDiff'),
    splitDiff: t('projectFiles.splitDiff'),
    reload: t('projectFiles.reload'),
    loading: t('projectFiles.loading'),
    noProjects: t('projectFiles.noProjects'),
    noEntries: t('projectFiles.noEntries'),
    chooseFile: t('projectFiles.chooseFile'),
    chooseDiff: t('projectFiles.chooseDiff'),
    chooseCommit: t('projectFiles.chooseCommit'),
    chooseCommitFile: t('projectFiles.chooseCommitFile'),
    noChanges: t('projectFiles.noChanges'),
    noCommits: t('projectFiles.noCommits'),
    mergeCommit: t('projectFiles.mergeCommit'),
    binary: t('projectFiles.binary'),
    truncated: t('projectFiles.truncated'),
    readOnly: t('projectFiles.readOnly'),
    root: t('projectFiles.root'),
    docs: t('projectFiles.docs'),
    ldvhBase: t('projectFiles.ldvhBase'),
  };

  const quickDirs = [
    { label: copy.root, path: '' },
    { label: copy.docs, path: 'docs' },
    { label: copy.ldvhBase, path: 'ldvh-base' },
  ];

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
        <PageHeader title={copy.title} subtitle={copy.subtitle} />
        <EmptyState text={copy.noProjects} />
      </div>
    );
  }

  return (
    <div className="ldvh-page-frame flex min-h-full min-w-0 flex-col overflow-x-hidden xl:h-full">
      <div className="ldvh-page-toolbar mb-6 min-w-0 shrink-0">
        <PageHeader title={copy.title} subtitle={copy.subtitle} />
        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <span className="ldvh-chip rounded-full border border-ldvh-accent/30 bg-ldvh-accent/10 px-3 py-1 text-ldvh-accent">
            {copy.readOnly}
          </span>
          <button
            type="button"
            onClick={handleRefresh}
            className="ldvh-body-muted inline-flex items-center gap-2 rounded-md border border-ldvh-border px-3 py-2 transition-colors hover:bg-ldvh-border/40 hover:text-ldvh-text-primary"
          >
            <RefreshCcw size={14} />
            {copy.reload}
          </button>
        </div>
      </div>

      <section className="sticky top-0 z-20 mb-6 min-w-0 shrink-0 rounded-lg border border-ldvh-border bg-ldvh-panel/95 p-4 shadow-sm shadow-black/10 backdrop-blur">
        <div className="grid min-w-0 gap-4 lg:grid-cols-[minmax(16rem,26rem)_minmax(0,1fr)]">
          <label className="min-w-0">
            <span className="ldvh-caption-strong mb-1 block">{copy.project}</span>
            <select
              value={projectId}
              onChange={(event) => handleProjectChange(event.target.value)}
              className="ldvh-body w-full rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-2"
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name || project.id}
                </option>
              ))}
            </select>
            {selectedProject && (
              <div className="mt-2 flex min-w-0 items-center gap-2">
                <p className="ldvh-meta min-w-0 truncate">{selectedProject.path}</p>
                <CopyPathButton path={selectedProject.path} />
              </div>
            )}
          </label>
          <div className="flex min-w-0 flex-col justify-end gap-2">
            <p className="ldvh-caption-strong">{t('projectFiles.view')}</p>
            <div role="tablist" aria-label={t('projectFiles.viewAria')} className="ldvh-tab-list max-w-2xl">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'files'}
                onClick={() => setActiveTab('files')}
                className={`ldvh-tab-button ${activeTab === 'files' ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
              >
                <FolderOpen size={15} className="shrink-0" />
                <span className="truncate">{copy.filesTab}</span>
                <span className="ldvh-tab-count">{entries.length}</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'changes'}
                onClick={() => setActiveTab('changes')}
                className={`ldvh-tab-button ${activeTab === 'changes' ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
              >
                <GitPullRequestArrow size={15} className="shrink-0" />
                <span className="truncate">{copy.changesTab}</span>
                <span className="ldvh-tab-count">{gitEntries.length}</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'history'}
                onClick={() => setActiveTab('history')}
                className={`ldvh-tab-button ${activeTab === 'history' ? 'ldvh-tab-button-active' : 'ldvh-tab-button-idle'}`}
              >
                <GitCommit size={15} className="shrink-0" />
                <span className="truncate">{copy.historyTab}</span>
                <span className="ldvh-tab-count">{commitEntries.length}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {activeTab === 'files' ? (
        <div className="grid min-w-0 gap-6 xl:min-h-0 xl:flex-1 xl:grid-cols-[minmax(18rem,28rem)_minmax(0,1fr)]">
          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <FolderOpen size={16} className="shrink-0 text-ldvh-accent" />
                <h2 className="ldvh-section-title shrink-0">{copy.fileBrowser}</h2>
              </div>
              <span className="ldvh-meta-primary shrink-0">{entries.length}</span>
            </div>
            <div className="space-y-2 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-3">
                <div className="flex min-w-0 flex-wrap gap-2">
                  {quickDirs.map((item) => (
                    <button
                      key={item.path || 'root'}
                      type="button"
                      onClick={() => handleNavigateDir(item.path)}
                      className={`ldvh-chip rounded-md border px-3 py-1.5 transition-colors ${
                        currentDir === item.path
                          ? 'border-ldvh-accent/40 bg-ldvh-accent/10 text-ldvh-accent'
                          : 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary hover:border-ldvh-accent/40 hover:text-ldvh-text-primary'
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
                <label className="ldvh-chip inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-md border border-ldvh-border bg-ldvh-bg px-3 py-1.5 text-ldvh-text-secondary transition-colors hover:text-ldvh-text-primary">
                  <input
                    type="checkbox"
                    checked={showHiddenFiles}
                    onChange={(event) => handleShowHiddenChange(event.target.checked)}
                    className="h-3.5 w-3.5 accent-ldvh-accent"
                  />
                  {copy.showHiddenFiles}
                </label>
              </div>
              <Breadcrumbs dir={currentDir} onNavigate={handleNavigateDir} />
            </div>
            <div className="min-w-0 overflow-y-auto p-3 xl:min-h-0 xl:flex-1">
              {entriesLoading ? (
                <LoadingState text={copy.loading} />
              ) : entriesError ? (
                <EmptyState text={entriesError} />
              ) : entries.length === 0 ? (
                <EmptyState text={copy.noEntries} />
              ) : (
                <div className="space-y-1">
                  {entries.map((entry) => (
                    <div
                      key={entry.path || entry.name}
                      className={`group flex w-full min-w-0 items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/30 ${
                        filePanel.data?.path === entry.path ? 'bg-ldvh-accent/10 text-ldvh-accent' : ''
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => handleOpenEntry(entry)}
                        className="flex min-w-0 flex-1 items-center gap-3 text-left"
                      >
                        <FileIcon entry={entry} />
                        <span className="min-w-0 flex-1">
                          <span className="ldvh-card-title block truncate transition-colors group-hover:text-ldvh-accent">
                            {entry.name}
                          </span>
                          <span className="ldvh-meta block truncate">
                            {getKindLabel(entry.kind, locale)}
                            {entry.type === 'file' ? ` · ${formatBytes(entry.size)}` : ''}
                            {' · '}
                            {formatDateTime(entry.updated)}
                          </span>
                        </span>
                      </button>
                      <CopyPathButton path={entry.absolutePath} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <FileText size={16} className="shrink-0 text-ldvh-accent" />
                <div className="min-w-0">
                  <h2 className="ldvh-section-title">{copy.preview}</h2>
                  {filePanel.data && <p className="ldvh-meta truncate">{filePanel.data.path}</p>}
                </div>
              </div>
              <CopyPathButton path={filePanel.data?.absolutePath} />
            </div>
            <div className="min-h-[36rem] min-w-0 p-4 xl:min-h-0 xl:flex-1 xl:overflow-hidden">
              {filePanel.loading ? (
                <LoadingState text={copy.loading} />
              ) : filePanel.error ? (
                <EmptyState text={filePanel.error} />
              ) : !filePanel.data ? (
                <EmptyState text={copy.chooseFile} />
              ) : filePanel.data.kind === 'binary' ? (
                <EmptyState text={`${copy.binary} ${formatBytes(filePanel.data.size)}`} />
              ) : (
                <div className="min-w-0 xl:flex xl:h-full xl:flex-col">
                  <div className="mb-3 flex min-w-0 flex-wrap items-center gap-2">
                    <span className="ldvh-chip rounded-md border border-ldvh-border bg-ldvh-bg px-2 py-1 text-ldvh-text-secondary">
                      {getKindLabel(filePanel.data.kind, locale)}
                    </span>
                    <span className="ldvh-meta">{formatBytes(filePanel.data.size)}</span>
                    {filePanel.data.truncated && (
                      <span className="ldvh-chip rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-amber-300">
                        {copy.truncated}
                      </span>
                    )}
                  </div>
                  {filePanel.data.kind === 'markdown' ? (
                    <article className="min-w-0 overflow-auto rounded-md bg-ldvh-bg px-4 py-4 xl:min-h-0 xl:flex-1">
                      <MarkdownPreview content={filePanel.data.content} renderSvgBlocks />
                    </article>
                  ) : filePanel.data.kind === 'svg' ? (
                    <div className="flex min-w-0 items-center justify-center overflow-auto rounded-md bg-ldvh-bg p-4 xl:min-h-0 xl:flex-1">
                      <img
                        src={getSvgDataUrl(filePanel.data.content)}
                        alt={getFileName(filePanel.data.path)}
                        className="max-h-full max-w-full object-contain"
                      />
                    </div>
                  ) : (
                    <pre className="ldvh-meta-primary min-w-0 overflow-auto whitespace-pre-wrap rounded-md bg-ldvh-bg p-4 xl:min-h-0 xl:flex-1">
                      {filePanel.data.content}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </section>
        </div>
      ) : activeTab === 'changes' ? (
        <div className="grid min-w-0 gap-6 xl:min-h-0 xl:flex-1 xl:grid-cols-[minmax(18rem,28rem)_minmax(0,1fr)]">
          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <GitPullRequestArrow size={16} className="shrink-0 text-ldvh-accent" />
                <h2 className="ldvh-section-title">{copy.pending}</h2>
              </div>
              <span className="ldvh-meta-primary">{gitEntries.length}</span>
            </div>
            <div className="min-w-0 overflow-y-auto p-3 xl:min-h-0 xl:flex-1">
              {gitLoading ? (
                <LoadingState text={copy.loading} />
              ) : gitError ? (
                <EmptyState text={gitError} />
              ) : gitEntries.length === 0 ? (
                <EmptyState text={copy.noChanges} />
              ) : (
                <div className="space-y-1">
                  {gitEntries.map((entry) => (
                    <div
                      key={`${entry.projectId}:${entry.status}:${entry.path}`}
                      className={`group flex w-full min-w-0 items-center gap-3 rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/30 ${
                        diffPanel.data?.path === entry.path ? 'bg-ldvh-accent/10 text-ldvh-accent' : ''
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => handleOpenDiff(entry)}
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
                            {getStatusLabel(entry.status, locale)} · {entry.path}
                          </span>
                        </span>
                      </button>
                      <CopyPathButton path={entry.absolutePath} />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <Diff size={16} className="shrink-0 text-ldvh-accent" />
                <div className="min-w-0">
                  <h2 className="ldvh-section-title">{copy.diff}</h2>
                  {diffPanel.data && <p className="ldvh-meta truncate">{diffPanel.data.path}</p>}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <div
                  role="group"
                  aria-label={copy.diffMode}
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
                    {copy.unifiedDiff}
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
                    {copy.splitDiff}
                  </button>
                </div>
                <CopyPathButton path={diffPanel.data?.absolutePath} />
              </div>
            </div>
            <div className="min-h-[36rem] min-w-0 p-4 xl:min-h-0 xl:flex-1 xl:overflow-hidden">
              {diffPanel.loading ? (
                <LoadingState text={copy.loading} />
              ) : diffPanel.error ? (
                <EmptyState text={diffPanel.error} />
              ) : !diffPanel.data ? (
                <EmptyState text={copy.chooseDiff} />
              ) : diffViewMode === 'unified' ? (
                <pre className="ldvh-meta-primary h-full min-w-0 overflow-auto rounded-md bg-ldvh-bg p-4">
                  {diffPanel.data.diff.split('\n').map((line, index) => (
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
                      <div className="border-r border-ldvh-border px-3 py-2">{t('projectFiles.before')}</div>
                      <div className="border-r border-ldvh-border px-2 py-2 text-right">+</div>
                      <div className="px-3 py-2">{t('projectFiles.after')}</div>
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
      ) : (
        <div className="grid min-w-0 gap-6 xl:min-h-0 xl:flex-1 xl:grid-cols-[minmax(18rem,28rem)_minmax(0,1fr)]">
          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <GitCommit size={16} className="shrink-0 text-ldvh-accent" />
                <h2 className="ldvh-section-title">{copy.history}</h2>
              </div>
              <span className="ldvh-meta-primary">{commitEntries.length}</span>
            </div>
            <div className="min-w-0 overflow-y-auto p-3 xl:min-h-0 xl:flex-1">
              {commitsLoading ? (
                <LoadingState text={copy.loading} />
              ) : commitsError ? (
                <EmptyState text={commitsError} />
              ) : commitEntries.length === 0 ? (
                <EmptyState text={copy.noCommits} />
              ) : (
                <div className="space-y-0">
                  {commitEntries.map((entry, index) => {
                    const isSelected = selectedCommitHash === entry.hash;
                    const selectedCommit = isSelected && commitPanel.data?.hash === entry.hash ? commitPanel.data : null;
                    const selectedFiles = selectedCommit?.files ?? [];
                    return (
                      <div key={entry.hash} className="relative min-w-0 pl-8">
                        {index < commitEntries.length - 1 && (
                          <span className="absolute left-[0.875rem] top-7 bottom-0 w-px bg-ldvh-accent/50" aria-hidden="true" />
                        )}
                        <span
                          className={`absolute left-1.5 top-3 flex h-4 w-4 items-center justify-center rounded-full border ${
                            isSelected
                              ? 'border-ldvh-accent bg-ldvh-accent shadow-sm shadow-ldvh-accent/30'
                              : 'border-ldvh-accent bg-ldvh-panel'
                          }`}
                          aria-hidden="true"
                        >
                          <span className={`h-1.5 w-1.5 rounded-full ${isSelected ? 'bg-ldvh-panel' : 'bg-ldvh-accent'}`} />
                        </span>
                        <button
                          type="button"
                          onClick={() => handleOpenCommit(entry)}
                          className={`group flex w-full min-w-0 items-start rounded-md px-2 py-2 text-left transition-colors hover:bg-ldvh-border/30 ${
                            isSelected ? 'bg-ldvh-accent/10 text-ldvh-accent' : ''
                          }`}
                        >
                          <span className="min-w-0 flex-1">
                            <span className="ldvh-card-title block truncate transition-colors group-hover:text-ldvh-accent">
                              {entry.description || entry.message}
                            </span>
                            <span className="ldvh-meta block truncate">
                              {entry.shortHash} · {entry.author} · {formatDateTime(entry.date)}
                            </span>
                            <span className="mt-1 flex min-w-0 flex-wrap gap-1">
                              {entry.isMerge && (
                                <span className="ldvh-chip rounded border border-ldvh-border bg-ldvh-bg px-1.5 py-0.5 text-ldvh-text-secondary">
                                  {copy.mergeCommit}
                                </span>
                              )}
                            </span>
                          </span>
                        </button>
                        {isSelected && (
                          <div className="mb-2 ml-2 min-w-0 space-y-3 rounded-md border border-ldvh-border/70 bg-ldvh-bg/80 p-3">
                            {commitPanel.loading ? (
                              <div className="ldvh-meta px-1 py-2">{copy.loading}</div>
                            ) : commitPanel.error ? (
                              <div className="ldvh-meta px-1 py-2 text-red-300">{commitPanel.error}</div>
                            ) : !selectedCommit ? (
                              <div className="ldvh-meta px-1 py-2">{copy.chooseCommit}</div>
                            ) : selectedFiles.length === 0 ? (
                              <>
                                <div className="min-w-0">
                                  <div className="mb-1 flex min-w-0 items-center justify-between gap-2">
                                    <span className="ldvh-caption-strong text-ldvh-text-secondary">{copy.changeDetail}</span>
                                    <span className="ldvh-meta-primary">{selectedCommit.shortHash}</span>
                                  </div>
                                  <p className="ldvh-body font-medium text-ldvh-text-primary">{selectedCommit.description || selectedCommit.message || selectedCommit.shortHash}</p>
                                  <div className="ldvh-meta mt-2 flex min-w-0 flex-wrap gap-x-3 gap-y-1">
                                    <span>{selectedCommit.author}</span>
                                    <span>{formatDateTime(selectedCommit.date)}</span>
                                  </div>
                                </div>
                                <div className="ldvh-meta px-1 py-2">{copy.chooseCommitFile}</div>
                              </>
                            ) : (
                              <>
                                <div className="min-w-0">
                                  <div className="mb-1 flex min-w-0 items-center justify-between gap-2">
                                    <span className="ldvh-caption-strong text-ldvh-text-secondary">{copy.changeDetail}</span>
                                    <span className="ldvh-meta-primary">{selectedCommit.shortHash}</span>
                                  </div>
                                  <p className="ldvh-body font-medium text-ldvh-text-primary">{selectedCommit.description || selectedCommit.message || selectedCommit.shortHash}</p>
                                  {selectedCommit.body.trim() && (
                                    <div className="mt-2 rounded-md border border-ldvh-border/60 bg-ldvh-bg/50 px-2.5 py-2">
                                      <MarkdownPreview
                                        content={selectedCommit.body.trim()}
                                        className="ldvh-inline-markdown ldvh-commit-body-markdown max-w-none"
                                      />
                                    </div>
                                  )}
                                  <div className="ldvh-meta mt-2 flex min-w-0 flex-wrap gap-x-3 gap-y-1">
                                    <span>{selectedCommit.author}</span>
                                    <span>{formatDateTime(selectedCommit.date)}</span>
                                  </div>
                                </div>
                                <div className="min-w-0">
                                  <div className="mb-1 flex min-w-0 items-center justify-between gap-2">
                                    <span className="ldvh-caption-strong text-ldvh-text-secondary">{copy.selectedCommitFiles}</span>
                                    <span className="ldvh-meta-primary">{selectedFiles.length}</span>
                                  </div>
                                  <div className="max-h-72 space-y-1 overflow-y-auto pr-1">
                                    {selectedFiles.map((file) => (
                                      <button
                                        key={`${entry.hash}:graph:${file.status}:${file.path}`}
                                        type="button"
                                        onClick={() => handleOpenCommitFileDiff(file)}
                                        className={`flex w-full min-w-0 items-center gap-2 rounded px-1.5 py-1 text-left transition-colors hover:bg-ldvh-border/30 ${
                                          diffPanel.data?.hash === entry.hash && diffPanel.data?.path === file.path
                                            ? 'bg-ldvh-accent/10 text-ldvh-accent'
                                            : ''
                                        }`}
                                      >
                                        <span className="ldvh-meta-primary w-7 shrink-0 text-center">{file.status}</span>
                                        <span className="min-w-0 flex-1">
                                          <span className="ldvh-card-title block truncate">{getFileName(file.path)}</span>
                                          <span className="ldvh-meta block truncate">
                                            {getCommitFileStatusLabel(file.status, locale)} · {file.path}
                                          </span>
                                        </span>
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </section>

          <section className="min-w-0 rounded-lg border border-ldvh-border bg-ldvh-panel xl:flex xl:min-h-0 xl:flex-col">
            <div className="flex min-w-0 items-center justify-between gap-3 border-b border-ldvh-border px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <Diff size={16} className="shrink-0 text-ldvh-accent" />
                <div className="min-w-0">
                  <h2 className="ldvh-section-title">{copy.diff}</h2>
                  {diffPanel.data && commitPanel.data && diffPanel.data.hash === commitPanel.data.hash && (
                    <p className="ldvh-meta truncate">{diffPanel.data.path}</p>
                  )}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <div
                  role="group"
                  aria-label={copy.diffMode}
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
                    {copy.unifiedDiff}
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
                    {copy.splitDiff}
                  </button>
                </div>
                <CopyPathButton path={diffPanel.data?.absolutePath} />
              </div>
            </div>
            <div className="min-h-[36rem] min-w-0 p-4 xl:min-h-0 xl:flex-1 xl:overflow-hidden">
              {commitPanel.loading ? (
                <LoadingState text={copy.loading} />
              ) : commitPanel.error ? (
                <EmptyState text={commitPanel.error} />
              ) : !commitPanel.data ? (
                <EmptyState text={copy.chooseCommit} />
              ) : diffPanel.loading ? (
                <LoadingState text={copy.loading} />
              ) : diffPanel.error ? (
                <EmptyState text={diffPanel.error} />
              ) : !diffPanel.data || diffPanel.data.hash !== commitPanel.data.hash ? (
                <EmptyState text={copy.chooseCommitFile} />
              ) : diffViewMode === 'unified' ? (
                <pre className="ldvh-meta-primary h-full min-w-0 overflow-auto rounded-md bg-ldvh-bg p-4">
                  {diffPanel.data.diff.split('\n').map((line, index) => (
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
                      <div className="border-r border-ldvh-border px-3 py-2">{t('projectFiles.before')}</div>
                      <div className="border-r border-ldvh-border px-2 py-2 text-right">+</div>
                      <div className="px-3 py-2">{t('projectFiles.after')}</div>
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
      )}
    </div>
  );
}
