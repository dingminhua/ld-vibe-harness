const API_BASE = '/api';
const inFlightRequests = new Map<string, Promise<unknown>>();

export interface DashboardData {
  landing?: {
    totalRequirements: number;
    gapTotal: number;
    gapByArea: Record<string, number>;
    capabilityStatus: Record<string, string>;
    humanGateStatus: string;
    validationPlanStatus: Record<string, string>;
  } | null;
  profile: {
    id: string;
    title: string;
    status: string;
    path: string;
  } | null;
  stats: Array<{
    type: string;
    total: number;
    byStatus: Record<string, number>;
  }>;
  recentItems: Array<{
    id: string;
    type: string;
    title: string;
    title_en?: string;
    title_zh?: string;
    status: string;
    path: string;
    updated: string;
    relativeTime: string;
    typeColor: string;
  }>;
  actionItems: Array<{
    id: string;
    type: string;
    title: string;
    title_en?: string;
    title_zh?: string;
    status: string;
    path: string;
    updated: string;
    relativeTime: string;
    typeColor: string;
  }>;
  recentChanges: Array<{
    hash: string;
    shortHash: string;
    author: string;
    date: string;
    message: string;
    category: string;
    description: string;
    relativeTime: string;
  }>;
  validation: {
    ok: boolean;
    errors: number;
    warnings: number;
  };
}

export interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  path: string;
  updated: string;
  category?: string;
  priority?: string;
  severity?: string;
  repeatability?: string;
  plans?: RelatedPlanSummary[];
  planTotal?: number;
  planClosed?: number;
  planReviewNeeded?: number;
  planActive?: number;
  planRisk?: number;
  planByStatus?: Record<string, number>;
  tasks?: RelatedObjectSummary[];
  taskTotal?: number;
  taskClosed?: number;
  taskReviewNeeded?: number;
  taskActive?: number;
  taskRisk?: number;
  taskByStatus?: Record<string, number>;
  hasSuccessCriteria?: boolean;
  hasCompletionEvidence?: boolean;
  workarea?: string;
}

export interface ObjectStatusOption {
  status: string;
  count: number;
}

export interface RelatedObjectSummary {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  path: string;
  updated: string;
}

export interface RelatedPlanSummary extends RelatedObjectSummary {
  workarea?: string;
  taskTotal: number;
  taskClosed: number;
  taskReviewNeeded: number;
  taskActive: number;
  taskRisk: number;
  tasks: RelatedObjectSummary[];
  hasSuccessCriteria: boolean;
  hasCompletionEvidence: boolean;
}

export interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;
}

export interface ValidationIssue {
  level: 'error' | 'warning';
  code: string;
  message: string;
  path: string;
  field?: string;
  suggestion?: string;
}

export interface LdvhReportError {
  ok: false;
  error: string;
  stderr: string;
  exitCode: number | string | null;
}

export interface LdvhLandingCheckReport {
  metadata: {
    generated_at?: string;
    status_source?: string;
    scope?: string;
  };
  summary: {
    status?: string;
    remaining_gap_count?: number;
    by_status: Record<string, number>;
  };
  checks: Array<{
    id?: string;
    status?: string;
    issue_count?: number;
    evidence?: string;
    suggested_writeback?: string;
  }>;
  remaining_gaps: Array<{
    id?: string;
    status?: string;
    message?: string;
    suggested_writeback?: string;
  }>;
}

export interface LdvhLandingReport {
  metadata: {
    generated_at?: string;
    requirement_count?: number;
    human_gate_record_count?: number;
    runtime_projection_issue_count?: number;
    human_gate_issue_count?: number;
    status_source?: string;
  };
  summary: {
    by_status: Record<string, number>;
    gap_total?: number;
    runtime_projection_status?: string;
    human_gate_status?: string;
    gap_by_owner_area: Record<string, number>;
  };
  capability_gaps: Array<{
    id?: string;
    capability?: string;
    status?: string;
    owner_area?: string;
    suggested_writeback?: string;
    evidence?: string;
  }>;
  gap_categories: Array<{
    key: string;
    label?: string;
    total?: number;
    by_status: Record<string, number>;
    examples: Array<{
      source?: string;
      status?: string;
      title?: string;
      suggested_writeback?: string;
    }>;
  }>;
}

export interface LdvhHumanGateReport {
  metadata: {
    generated_at?: string;
    checked_file_count?: number;
    record_count?: number;
    issue_count?: number;
    status_source?: string;
    scope?: string;
  };
  summary: {
    status?: string;
  };
  issues: ValidationIssue[];
}

export interface ValidationData {
  ok: boolean;
  command: string;
  action: string;
  summary: { files: number; errors: number; warnings: number };
  issues: ValidationIssue[];
  reports?: {
    landingCheck?: LdvhLandingCheckReport | LdvhReportError;
    landingReport?: LdvhLandingReport | LdvhReportError;
    humanGateReport?: LdvhHumanGateReport | LdvhReportError;
  };
}

async function request<T>(url: string): Promise<T> {
  const fullUrl = `${API_BASE}${url}`;
  const existing = inFlightRequests.get(fullUrl);
  if (existing) return existing as Promise<T>;

  const promise = fetch(fullUrl)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`API error: ${res.status} ${res.statusText}`);
      }
      return res.json() as Promise<T>;
    })
    .finally(() => {
      inFlightRequests.delete(fullUrl);
    });

  inFlightRequests.set(fullUrl, promise);
  return promise;
}

export async function fetchDashboard(locale?: string): Promise<DashboardData> {
  const params = locale ? `?locale=${locale}` : '';
  return request<DashboardData>(`/dashboard${params}`);
}

export async function fetchObjects(
  type: string,
  status?: string
): Promise<{ ok: boolean; summary: { count: number }; data: { items: ObjectItem[]; statusOptions?: ObjectStatusOption[]; statusTotal?: number } }> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  const qs = params.toString();
  return request(`/objects/${type}${qs ? `?${qs}` : ''}`);
}

export async function fetchObjectDetail(type: string, id: string): Promise<ObjectDetail> {
  return request<ObjectDetail>(`/objects/${type}/${encodeURIComponent(id)}`);
}

export async function fetchValidation(): Promise<ValidationData> {
  return request<ValidationData>('/validate');
}

export interface ChangelogEntry {
  hash: string;
  shortHash: string;
  author: string;
  date: string;
  message: string;
  category: string;
  description: string;
  relativeTime: string;
}

export async function fetchChangelog(count?: number, locale?: string): Promise<ChangelogEntry[]> {
  const params = new URLSearchParams();
  if (count) params.set('count', String(count));
  if (locale) params.set('locale', locale);
  const qs = params.toString();
  return request<ChangelogEntry[]>(`/changelog${qs ? `?${qs}` : ''}`);
}

export async function fetchCommitDetail(hash: string): Promise<{ hash: string; stat: string }> {
  return request<{ hash: string; stat: string }>(`/changelog/${hash}`);
}

export interface DocContent {
  path: string;
  content: string;
  truncated: boolean;
}

export async function fetchDocContent(docPath: string): Promise<DocContent> {
  return request<DocContent>(`/docs?path=${encodeURIComponent(docPath)}`);
}

export interface GovernedProject {
  id: string;
  name: string;
  description: string;
  path: string;
  docsPath: string;
  ldvhBasePath: string;
}

export interface ProjectFilesProjectsData {
  ok: boolean;
  workspaceRoot: string;
  projects: GovernedProject[];
}

export interface ProjectFileEntry {
  name: string;
  path: string;
  absolutePath: string;
  type: 'directory' | 'file';
  kind: 'directory' | 'markdown' | 'yaml' | 'text' | 'binary';
  size: number;
  updated: string;
}

export interface ProjectFileEntriesData {
  ok: boolean;
  project: GovernedProject;
  dir: string;
  parent: string;
  showHidden: boolean;
  truncated: boolean;
  entries: ProjectFileEntry[];
}

export interface ProjectFileContentData {
  ok: boolean;
  project: GovernedProject;
  path: string;
  absolutePath: string;
  kind: 'markdown' | 'yaml' | 'text' | 'binary';
  size: number;
  content: string;
  truncated: boolean;
}

export interface ProjectGitStatusEntry {
  projectId: string;
  status: string;
  path: string;
  absolutePath: string;
  staged: boolean;
  unstaged: boolean;
}

export interface ProjectGitStatusData {
  ok: boolean;
  entries: ProjectGitStatusEntry[];
}

export interface ProjectGitDiffData {
  ok: boolean;
  project: GovernedProject;
  hash?: string;
  path: string;
  absolutePath: string;
  status: string;
  diff: string;
}

export interface ProjectGitCommitEntry {
  hash: string;
  shortHash: string;
  parents: string[];
  author: string;
  date: string;
  refs: string;
  message: string;
  isMerge: boolean;
}

export interface ProjectGitCommitFile {
  status: string;
  path: string;
  absolutePath: string;
}

export interface ProjectGitCommitDetail extends ProjectGitCommitEntry {
  files: ProjectGitCommitFile[];
}

export interface ProjectGitCommitsData {
  ok: boolean;
  project: GovernedProject;
  entries: ProjectGitCommitEntry[];
}

export interface ProjectGitCommitDetailData {
  ok: boolean;
  project: GovernedProject;
  commit: ProjectGitCommitDetail;
}

export async function fetchProjectFilesProjects(): Promise<ProjectFilesProjectsData> {
  return request<ProjectFilesProjectsData>('/project-files/projects');
}

export async function fetchProjectFileEntries(projectId: string, dir = '', showHidden = false): Promise<ProjectFileEntriesData> {
  const params = new URLSearchParams({ projectId });
  if (dir) params.set('dir', dir);
  if (showHidden) params.set('showHidden', 'true');
  return request<ProjectFileEntriesData>(`/project-files/entries?${params.toString()}`);
}

export async function fetchProjectFileContent(projectId: string, filePath: string, showHidden = false): Promise<ProjectFileContentData> {
  const params = new URLSearchParams({ projectId, path: filePath });
  if (showHidden) params.set('showHidden', 'true');
  return request<ProjectFileContentData>(`/project-files/content?${params.toString()}`);
}

export async function fetchProjectGitStatus(projectId?: string): Promise<ProjectGitStatusData> {
  const params = new URLSearchParams();
  if (projectId) params.set('projectId', projectId);
  const qs = params.toString();
  return request<ProjectGitStatusData>(`/project-files/git/status${qs ? `?${qs}` : ''}`);
}

export async function fetchProjectGitDiff(projectId: string, filePath: string, status: string): Promise<ProjectGitDiffData> {
  const params = new URLSearchParams({ projectId, path: filePath, status });
  return request<ProjectGitDiffData>(`/project-files/git/diff?${params.toString()}`);
}

export async function fetchProjectGitCommits(projectId: string, count = 50): Promise<ProjectGitCommitsData> {
  const params = new URLSearchParams({ projectId, count: String(count) });
  return request<ProjectGitCommitsData>(`/project-files/git/commits?${params.toString()}`);
}

export async function fetchProjectGitCommitDetail(projectId: string, hash: string): Promise<ProjectGitCommitDetailData> {
  const params = new URLSearchParams({ projectId });
  return request<ProjectGitCommitDetailData>(`/project-files/git/commit/${encodeURIComponent(hash)}?${params.toString()}`);
}

export async function fetchProjectGitCommitFileDiff(projectId: string, hash: string, filePath: string): Promise<ProjectGitDiffData> {
  const params = new URLSearchParams({ projectId, path: filePath });
  return request<ProjectGitDiffData>(`/project-files/git/commit/${encodeURIComponent(hash)}/diff?${params.toString()}`);
}
