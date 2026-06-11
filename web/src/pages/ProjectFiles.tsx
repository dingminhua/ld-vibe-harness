import { useCallback, useEffect, useMemo, useState } from 'react';
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
  GitPullRequestArrow,
  Loader2,
  RefreshCcw,
  Rows3,
} from 'lucide-react';
import CopyPathButton from '@/components/CopyPathButton';
import MarkdownPreview from '@/components/MarkdownPreview';
import PageHeader from '@/components/PageHeader';
import { useI18n } from '@/i18n/context';
import {
  fetchProjectFileContent,
  fetchProjectFileEntries,
  fetchProjectFilesProjects,
  fetchProjectGitDiff,
  fetchProjectGitStatus,
  type GovernedProject,
  type ProjectFileContentData,
  type ProjectFileEntry,
  type ProjectGitDiffData,
  type ProjectGitStatusEntry,
} from '@/utils/api';
import { formatDateTime } from '@/utils/dateFormat';

type FilePanelState = {
  data: ProjectFileContentData | null;
  loading: boolean;
  error: string | null;
};

type DiffPanelState = {
  data: ProjectGitDiffData | null;
  loading: boolean;
  error: string | null;
};

type EntryKind = ProjectFileEntry['kind'];
type ActiveProjectFilesTab = 'files' | 'changes';
type DiffViewMode = 'unified' | 'split';

type SplitDiffCell = {
  kind: 'context' | 'delete' | 'add' | 'empty';
  lineNumber?: number;
  text?: string;
};

type SplitDiffRow =
  | { kind: 'meta' | 'hunk'; text: string }
  | { kind: 'line'; oldCell: SplitDiffCell; newCell: SplitDiffCell };

function pickCopy<T>(locale: string, zh: T, en: T): T {
  return locale === 'en' ? en : zh;
}

function formatBytes(size: number): string {
  if (!Number.isFinite(size) || size <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = size;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value >= 10 || unitIndex === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[unitIndex]}`;
}

function getFileName(filePath?: string): string {
  if (!filePath) return '';
  const parts = filePath.split('/').filter(Boolean);
  return parts[parts.length - 1] || filePath;
}

function isHiddenRelativePath(filePath: string): boolean {
  return filePath.split('/').some((part) => part.startsWith('.') && part.length > 1);
}

function getKindLabel(kind: EntryKind, locale: string): string {
  const labels: Record<EntryKind, { zh: string; en: string }> = {
    directory: { zh: '目录', en: 'Directory' },
    markdown: { zh: 'Markdown', en: 'Markdown' },
    yaml: { zh: 'YAML', en: 'YAML' },
    text: { zh: '文本', en: 'Text' },
    binary: { zh: '二进制', en: 'Binary' },
  };
  return locale === 'en' ? labels[kind].en : labels[kind].zh;
}

function getStatusLabel(status: string, locale: string): string {
  const trimmed = status.trim();
  const labels: Record<string, { zh: string; en: string }> = {
    '??': { zh: '未跟踪', en: 'Untracked' },
    M: { zh: '已修改', en: 'Modified' },
    A: { zh: '新增', en: 'Added' },
    D: { zh: '删除', en: 'Deleted' },
    R: { zh: '重命名', en: 'Renamed' },
    C: { zh: '复制', en: 'Copied' },
    U: { zh: '冲突', en: 'Conflict' },
  };
  const key = trimmed === '??' ? '??' : trimmed.replace(/\s/g, '').charAt(0);
  const label = labels[key];
  if (!label) return status;
  return locale === 'en' ? label.en : label.zh;
}

function getDiffLineClass(line: string): string {
  if (line.startsWith('+++') || line.startsWith('---')) return 'text-ldvh-text-secondary';
  if (line.startsWith('+')) return 'text-emerald-400';
  if (line.startsWith('-')) return 'text-red-400';
  if (line.startsWith('@@')) return 'text-ldvh-accent';
  if (line.startsWith('diff ') || line.startsWith('index ')) return 'text-sky-300';
  return 'text-ldvh-text-primary';
}

function getSplitDiffCellClass(cell: SplitDiffCell): string {
  if (cell.kind === 'delete') return 'bg-red-500/10 text-red-300';
  if (cell.kind === 'add') return 'bg-emerald-500/10 text-emerald-300';
  if (cell.kind === 'empty') return 'bg-ldvh-panel/60 text-ldvh-text-secondary';
  return 'text-ldvh-text-primary';
}

function parseSplitDiff(diff: string): SplitDiffRow[] {
  const rows: SplitDiffRow[] = [];
  let oldLineNumber: number | null = null;
  let newLineNumber: number | null = null;
  let pendingDeletes: SplitDiffCell[] = [];

  const flushDeletes = () => {
    if (pendingDeletes.length === 0) return;
    pendingDeletes.forEach((oldCell) => {
      rows.push({ kind: 'line', oldCell, newCell: { kind: 'empty' } });
    });
    pendingDeletes = [];
  };

  diff.split('\n').forEach((line) => {
    const hunkMatch = line.match(/^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
    if (hunkMatch) {
      flushDeletes();
      oldLineNumber = Number(hunkMatch[1]);
      newLineNumber = Number(hunkMatch[2]);
      rows.push({ kind: 'hunk', text: line });
      return;
    }

    if (oldLineNumber === null || newLineNumber === null) {
      flushDeletes();
      rows.push({ kind: 'meta', text: line });
      return;
    }

    if (line.startsWith('-') && !line.startsWith('---')) {
      pendingDeletes.push({ kind: 'delete', lineNumber: oldLineNumber, text: line.slice(1) });
      oldLineNumber += 1;
      return;
    }

    if (line.startsWith('+') && !line.startsWith('+++')) {
      const newCell: SplitDiffCell = { kind: 'add', lineNumber: newLineNumber, text: line.slice(1) };
      newLineNumber += 1;
      const oldCell = pendingDeletes.shift() ?? { kind: 'empty' };
      rows.push({ kind: 'line', oldCell, newCell });
      return;
    }

    flushDeletes();
    const text = line.startsWith(' ') ? line.slice(1) : line;
    rows.push({
      kind: 'line',
      oldCell: { kind: 'context', lineNumber: oldLineNumber, text },
      newCell: { kind: 'context', lineNumber: newLineNumber, text },
    });
    oldLineNumber += 1;
    newLineNumber += 1;
  });

  flushDeletes();
  return rows;
}

function FileIcon({ entry }: { entry: ProjectFileEntry }) {
  if (entry.type === 'directory') return <Folder size={15} className="text-ldvh-accent" />;
  if (entry.kind === 'markdown') return <FileText size={15} className="text-ldvh-accent" />;
  if (entry.kind === 'yaml' || entry.kind === 'text') return <FileCode2 size={15} className="text-ldvh-text-secondary" />;
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
  const { locale } = useI18n();
  const [projects, setProjects] = useState<GovernedProject[]>([]);
  const [projectId, setProjectId] = useState('');
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [currentDir, setCurrentDir] = useState('');
  const [entries, setEntries] = useState<ProjectFileEntry[]>([]);
  const [entriesLoading, setEntriesLoading] = useState(false);
  const [entriesError, setEntriesError] = useState<string | null>(null);
  const [filePanel, setFilePanel] = useState<FilePanelState>({ data: null, loading: false, error: null });
  const [gitEntries, setGitEntries] = useState<ProjectGitStatusEntry[]>([]);
  const [gitLoading, setGitLoading] = useState(false);
  const [gitError, setGitError] = useState<string | null>(null);
  const [diffPanel, setDiffPanel] = useState<DiffPanelState>({ data: null, loading: false, error: null });
  const [activeTab, setActiveTab] = useState<ActiveProjectFilesTab>('files');
  const [diffViewMode, setDiffViewMode] = useState<DiffViewMode>('unified');
  const [showHiddenFiles, setShowHiddenFiles] = useState(false);

  const copy = {
    title: pickCopy(locale, '项目文件', 'Project Files'),
    subtitle: pickCopy(
      locale,
      '按 LDVH 管辖项目浏览文件，预览 Markdown，并只读查看当前 Git 待提交差异。',
      'Browse governed project files, preview Markdown, and inspect pending Git changes in read-only mode.',
    ),
    project: pickCopy(locale, '管辖项目', 'Governed Project'),
    quickRoots: pickCopy(locale, '常用目录', 'Quick Roots'),
    showHiddenFiles: pickCopy(locale, '显示隐藏文件', 'Show hidden files'),
    filesTab: pickCopy(locale, '文件浏览', 'Files'),
    changesTab: pickCopy(locale, '待提交文件', 'Pending'),
    fileBrowser: pickCopy(locale, '项目文件浏览', 'Project File Browser'),
    preview: pickCopy(locale, '文件预览', 'File Preview'),
    pending: pickCopy(locale, '待提交文件', 'Pending Files'),
    diff: pickCopy(locale, '文件差异', 'File Diff'),
    diffMode: pickCopy(locale, '差异显示方式', 'Diff display mode'),
    unifiedDiff: pickCopy(locale, '统一', 'Unified'),
    splitDiff: pickCopy(locale, '分栏', 'Split'),
    reload: pickCopy(locale, '刷新', 'Refresh'),
    loading: pickCopy(locale, '加载中', 'Loading'),
    noProjects: pickCopy(locale, '没有读取到管辖项目。', 'No governed projects found.'),
    noEntries: pickCopy(locale, '当前目录没有可展示文件。', 'No displayable files in this directory.'),
    chooseFile: pickCopy(locale, '选择左侧文件后在这里阅读。', 'Select a file on the left to read it here.'),
    chooseDiff: pickCopy(locale, '选择待提交文件后在这里查看差异。', 'Select a pending file to view its diff here.'),
    noChanges: pickCopy(locale, '当前项目没有待提交文件。', 'This project has no pending files.'),
    binary: pickCopy(locale, '这是二进制文件，Web 仅展示路径和大小。', 'This is a binary file; the web view only shows path and size.'),
    truncated: pickCopy(locale, '内容已按安全上限截断。', 'Content was truncated at the safety limit.'),
    readOnly: pickCopy(locale, '只读', 'Read-only'),
    root: pickCopy(locale, '项目根目录', 'Project root'),
    docs: pickCopy(locale, 'docs', 'docs'),
    facts: pickCopy(locale, 'ldvh-base', 'ldvh-base'),
  };

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === projectId) ?? null,
    [projects, projectId],
  );

  const splitDiffRows = useMemo(
    () => (diffPanel.data ? parseSplitDiff(diffPanel.data.diff) : []),
    [diffPanel.data],
  );

  const loadProjects = useCallback(() => {
    setProjectsLoading(true);
    setProjectsError(null);
    fetchProjectFilesProjects()
      .then((result) => {
        setProjects(result.projects ?? []);
        setProjectId((current) => current || result.projects?.[0]?.id || '');
      })
      .catch((err) => setProjectsError(err instanceof Error ? err.message : String(err)))
      .finally(() => setProjectsLoading(false));
  }, []);

  const loadEntries = useCallback((nextDir: string, nextShowHidden: boolean) => {
    if (!projectId) return;
    setEntriesLoading(true);
    setEntriesError(null);
    fetchProjectFileEntries(projectId, nextDir, nextShowHidden)
      .then((result) => {
        setEntries(result.entries ?? []);
        setCurrentDir(result.dir ?? nextDir);
      })
      .catch((err) => setEntriesError(err instanceof Error ? err.message : String(err)))
      .finally(() => setEntriesLoading(false));
  }, [projectId]);

  const loadGitStatus = useCallback(() => {
    if (!projectId) return;
    setGitLoading(true);
    setGitError(null);
    fetchProjectGitStatus(projectId)
      .then((result) => setGitEntries(result.entries ?? []))
      .catch((err) => setGitError(err instanceof Error ? err.message : String(err)))
      .finally(() => setGitLoading(false));
  }, [projectId]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (!projectId) return;
    setCurrentDir('');
    setEntries([]);
    setShowHiddenFiles(false);
    setFilePanel({ data: null, loading: false, error: null });
    setDiffPanel({ data: null, loading: false, error: null });
    loadEntries('', false);
    loadGitStatus();
  }, [loadEntries, loadGitStatus, projectId]);

  const handleProjectChange = (nextProjectId: string) => {
    if (nextProjectId === projectId) return;
    setProjectId(nextProjectId);
  };

  const handleNavigateDir = (nextDir: string) => {
    setActiveTab('files');
    setFilePanel({ data: null, loading: false, error: null });
    loadEntries(nextDir, showHiddenFiles);
  };

  const handleOpenEntry = (entry: ProjectFileEntry) => {
    setActiveTab('files');
    if (entry.type === 'directory') {
      handleNavigateDir(entry.path);
      return;
    }

    setFilePanel({ data: null, loading: true, error: null });
    fetchProjectFileContent(projectId, entry.path, showHiddenFiles)
      .then((data) => setFilePanel({ data, loading: false, error: null }))
      .catch((err) => {
        setFilePanel({ data: null, loading: false, error: err instanceof Error ? err.message : String(err) });
      });
  };

  const handleOpenDiff = (entry: ProjectGitStatusEntry) => {
    setActiveTab('changes');
    setDiffPanel({ data: null, loading: true, error: null });
    fetchProjectGitDiff(entry.projectId, entry.path, entry.status)
      .then((data) => setDiffPanel({ data, loading: false, error: null }))
      .catch((err) => {
        setDiffPanel({ data: null, loading: false, error: err instanceof Error ? err.message : String(err) });
      });
  };

  const handleRefresh = () => {
    loadEntries(currentDir, showHiddenFiles);
    loadGitStatus();
  };

  const handleShowHiddenChange = (nextShowHidden: boolean) => {
    setShowHiddenFiles(nextShowHidden);
    setFilePanel({ data: null, loading: false, error: null });
    const nextDir = !nextShowHidden && isHiddenRelativePath(currentDir) ? '' : currentDir;
    loadEntries(nextDir, nextShowHidden);
  };

  const quickDirs = [
    { label: copy.root, path: '' },
    { label: copy.docs, path: 'docs' },
    { label: copy.facts, path: 'ldvh-base' },
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

      <section className="mb-6 min-w-0 shrink-0 rounded-lg border border-ldvh-border bg-ldvh-panel p-4">
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
            <p className="ldvh-caption-strong">{pickCopy(locale, '视图', 'View')}</p>
            <div role="tablist" aria-label={pickCopy(locale, '项目文件视图', 'Project file view')} className="grid max-w-md grid-cols-2 rounded-lg border border-ldvh-border bg-ldvh-bg p-1">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'files'}
                onClick={() => setActiveTab('files')}
                className={`ldvh-card-title flex min-w-0 items-center justify-center gap-2 rounded-md px-3 py-2 transition-colors ${
                  activeTab === 'files'
                    ? 'bg-ldvh-panel text-ldvh-accent shadow-sm shadow-black/10'
                    : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
                }`}
              >
                <FolderOpen size={15} className="shrink-0" />
                <span className="truncate">{copy.filesTab}</span>
                <span className="ldvh-meta-primary shrink-0">{entries.length}</span>
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'changes'}
                onClick={() => setActiveTab('changes')}
                className={`ldvh-card-title flex min-w-0 items-center justify-center gap-2 rounded-md px-3 py-2 transition-colors ${
                  activeTab === 'changes'
                    ? 'bg-ldvh-panel text-ldvh-accent shadow-sm shadow-black/10'
                    : 'text-ldvh-text-secondary hover:text-ldvh-text-primary'
                }`}
              >
                <GitPullRequestArrow size={15} className="shrink-0" />
                <span className="truncate">{copy.changesTab}</span>
                <span className="ldvh-meta-primary shrink-0">{gitEntries.length}</span>
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
                      <MarkdownPreview content={filePanel.data.content} />
                    </article>
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
      ) : (
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
                      <div className="border-r border-ldvh-border px-3 py-2">{pickCopy(locale, '旧内容', 'Before')}</div>
                      <div className="border-r border-ldvh-border px-2 py-2 text-right">+</div>
                      <div className="px-3 py-2">{pickCopy(locale, '新内容', 'After')}</div>
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
