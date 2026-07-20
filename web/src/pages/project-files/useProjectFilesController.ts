import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  fetchProjectFileContent,
  fetchProjectFileEntries,
  fetchProjectFilesProjects,
  fetchProjectGitCommitDetail,
  fetchProjectGitCommitFileDiff,
  fetchProjectGitCommits,
  fetchProjectGitDiff,
  fetchProjectGitStatus,
  type GovernedProject,
  type ProjectFileEntry,
  type ProjectGitCommitEntry,
  type ProjectGitCommitFile,
  type ProjectGitStatusEntry,
} from '@/utils/api';
import {
  isHiddenRelativePath,
  parseSplitDiff,
  type ActiveProjectFilesTab,
  type CommitPanelState,
  type DiffPanelState,
  type DiffViewMode,
  type FilePanelState,
} from '@/pages/project-files/model';

export function useProjectFilesController() {
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
  const [commitEntries, setCommitEntries] = useState<ProjectGitCommitEntry[]>([]);
  const [commitsLoading, setCommitsLoading] = useState(false);
  const [commitsError, setCommitsError] = useState<string | null>(null);
  const [selectedCommitHash, setSelectedCommitHash] = useState('');
  const [commitPanel, setCommitPanel] = useState<CommitPanelState>({ data: null, loading: false, error: null });
  const [diffPanel, setDiffPanel] = useState<DiffPanelState>({ data: null, loading: false, error: null });
  const [activeTab, setActiveTab] = useState<ActiveProjectFilesTab>('files');
  const [diffViewMode, setDiffViewMode] = useState<DiffViewMode>('unified');
  const [showHiddenFiles, setShowHiddenFiles] = useState(false);

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

  const loadCommits = useCallback(() => {
    if (!projectId) return;
    setCommitsLoading(true);
    setCommitsError(null);
    fetchProjectGitCommits(projectId, 80)
      .then((result) => setCommitEntries(result.entries ?? []))
      .catch((err) => setCommitsError(err instanceof Error ? err.message : String(err)))
      .finally(() => setCommitsLoading(false));
  }, [projectId]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (!projectId) return;
    setCurrentDir('');
    setEntries([]);
    setCommitEntries([]);
    setSelectedCommitHash('');
    setShowHiddenFiles(false);
    setFilePanel({ data: null, loading: false, error: null });
    setCommitPanel({ data: null, loading: false, error: null });
    setDiffPanel({ data: null, loading: false, error: null });
    loadEntries('', false);
    loadGitStatus();
    loadCommits();
  }, [loadCommits, loadEntries, loadGitStatus, projectId]);

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

  const handleOpenCommit = (entry: ProjectGitCommitEntry) => {
    setActiveTab('history');
    setSelectedCommitHash(entry.hash);
    setCommitPanel({ data: null, loading: true, error: null });
    setDiffPanel({ data: null, loading: false, error: null });
    fetchProjectGitCommitDetail(projectId, entry.hash)
      .then((result) => setCommitPanel({ data: result.commit, loading: false, error: null }))
      .catch((err) => {
        setCommitPanel({ data: null, loading: false, error: err instanceof Error ? err.message : String(err) });
      });
  };

  const handleOpenCommitFileDiff = (file: ProjectGitCommitFile) => {
    if (!commitPanel.data) return;
    setActiveTab('history');
    setDiffPanel({ data: null, loading: true, error: null });
    fetchProjectGitCommitFileDiff(projectId, commitPanel.data.hash, file.path)
      .then((data) => setDiffPanel({ data, loading: false, error: null }))
      .catch((err) => {
        setDiffPanel({ data: null, loading: false, error: err instanceof Error ? err.message : String(err) });
      });
  };

  const handleRefresh = () => {
    loadEntries(currentDir, showHiddenFiles);
    loadGitStatus();
    loadCommits();
  };

  const handleShowHiddenChange = (nextShowHidden: boolean) => {
    setShowHiddenFiles(nextShowHidden);
    setFilePanel({ data: null, loading: false, error: null });
    const nextDir = !nextShowHidden && isHiddenRelativePath(currentDir) ? '' : currentDir;
    loadEntries(nextDir, nextShowHidden);
  };


  return {
    projects, projectId, projectsLoading, projectsError, currentDir, entries, entriesLoading, entriesError,
    filePanel, gitEntries, gitLoading, gitError, commitEntries, commitsLoading, commitsError,
    selectedCommitHash, commitPanel, diffPanel, activeTab, diffViewMode, showHiddenFiles,
    selectedProject, splitDiffRows, setActiveTab, setDiffViewMode,
    handleProjectChange, handleNavigateDir, handleOpenEntry, handleOpenDiff, handleOpenCommit,
    handleOpenCommitFileDiff, handleRefresh, handleShowHiddenChange,
  };
}
