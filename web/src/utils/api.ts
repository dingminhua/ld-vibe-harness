const API_BASE = '/api';
const inFlightRequests = new Map<string, Promise<unknown>>();

export interface DashboardData {
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
    body: string;
    category: string;
    scope: string;
    description: string;
    isBreaking: boolean;
    relativeTime: string;
  }>;
}

export interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  path: string;
  created?: string;
  updated: string;
  kind?: 'type_not_integrated';
  message?: string;
  priority?: string;
  importance?: string;
  executionItems?: RelatedObjectSummary[];
  executionItemTotal?: number;
  executionItemDone?: number;
  executionItemBlocked?: number;
  executionItemOpen?: number;
  executionItemByStatus?: Record<string, number>;
  successCriteriaTotal?: number;
  successCriteriaDone?: number;
  hasSuccessCriteria?: boolean;
  hasPlanConfirmedAt?: boolean;
  hasClosureRequestedAt?: boolean;
  hasVerificationEvidence?: boolean;
  hasClosureEvidence?: boolean;
  hasClosedAt?: boolean;
  archive_reason?: string;
  deprecated_reason?: string;
  discard_reason?: string;
  closure_evidence?: string;
  /** ADR-specific fields */
  date?: string;
  decision?: string;
  consequences?: string;
  related_rules?: string[];
  /** Spark-specific */
  source?: string;
  description?: string;
  evolution?: Array<Record<string, unknown>>;
  source_detail?: string;
  resolved_to?: string | { type?: string; ref?: string };
  resolved_at?: string;
  related_studies?: string[];
  /** V4-native Spark fields. */
  object_id?: string;
  fact_type_key?: string;
  canonical_path?: string;
  absolute_path?: string;
  created_at?: string;
  updated_at?: string;
  disposition_summary?: string;
  closed_at?: string;
  relations?: Array<Record<string, unknown>>;
  /** Study-specific */
  summary?: string;
  conclusion?: string;
  urls?: Array<string | UrlItem>;
  report_body?: string;
  /** Pitfall-specific */
  resolution?: string;
  source_sparks?: string[];
}

export interface UrlItem {
  ref: string;
  title?: string;
  summary?: string;
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
  priority?: string;
  role?: string;
  mode?: string;
  expectedOutput?: string;
  resultSummary?: string;
  blockingReason?: string;
  inputRefs?: string[];
  evidenceRefs?: string[];
}

export interface RelatedWorkCaseSummary extends RelatedObjectSummary {
  executionItems?: RelatedObjectSummary[];
  executionItemTotal?: number;
  executionItemDone?: number;
  executionItemBlocked?: number;
  executionItemOpen?: number;
  successCriteriaTotal?: number;
  successCriteriaDone?: number;
  hasSuccessCriteria: boolean;
  hasPlanConfirmedAt: boolean;
  hasClosureRequestedAt: boolean;
  hasVerificationEvidence?: boolean;
  hasClosureEvidence?: boolean;
  hasClosedAt: boolean;
}

export interface ObjectDetail {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status: string };
  data: Record<string, unknown>;
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
  status?: string,
  priority?: string,
): Promise<{ ok: boolean; summary: { count: number }; data: { items: ObjectItem[]; statusOptions?: ObjectStatusOption[]; priorityOptions?: ObjectStatusOption[]; statusTotal?: number } }> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (priority) params.set('priority', priority);
  const qs = params.toString();
  return request(`/objects/${type}${qs ? `?${qs}` : ''}`);
}

export async function fetchObjectDetail(type: string, id: string): Promise<ObjectDetail> {
  return request<ObjectDetail>(`/objects/${type}/${encodeURIComponent(id)}`);
}

export interface ChangelogEntry {
  hash: string;
  shortHash: string;
  author: string;
  date: string;
  message: string;
  body: string;
  category: string;
  scope: string;
  description: string;
  isBreaking: boolean;
  relativeTime: string;
}

export interface CommitDetailPanelData {
  entry: ChangelogEntry;
  stat: string;
}

export async function fetchChangelog(count?: number, locale?: string): Promise<ChangelogEntry[]> {
  const params = new URLSearchParams();
  if (count) params.set('count', String(count));
  if (locale) params.set('locale', locale);
  const qs = params.toString();
  return request<ChangelogEntry[]>(`/changelog${qs ? `?${qs}` : ''}`);
}

export async function fetchCommitDetail(hash: string, locale?: string): Promise<{ hash: string; stat: string; body: string; entry?: ChangelogEntry }> {
  const params = new URLSearchParams();
  if (locale) params.set('locale', locale);
  const qs = params.toString();
  return request<{ hash: string; stat: string; body: string; entry?: ChangelogEntry }>(`/changelog/${hash}${qs ? `?${qs}` : ''}`);
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
  kind: 'directory' | 'markdown' | 'yaml' | 'svg' | 'text' | 'binary';
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
  kind: 'markdown' | 'yaml' | 'svg' | 'text' | 'binary';
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
  message: string;
  body: string;
  category: string;
  scope: string;
  description: string;
  isBreaking: boolean;
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
