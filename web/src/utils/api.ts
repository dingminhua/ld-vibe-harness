import type { FactCarrier, FactReadStatus } from '@/utils/factReadMeta';

const API_BASE = '/api';
const inFlightRequests = new Map<string, Promise<unknown>>();

export interface DashboardData {
  stats: DashboardStat[];
  recentItems: DashboardFactItem[];
  actionItems: DashboardFactItem[];
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

export type DashboardObjectType = 'workcase' | 'adr' | 'pitfall' | 'spark' | 'study';
export type DashboardWorkCaseProgressGroup = 'plan_confirmation' | 'progressing' | 'closure_confirmation' | 'closed';

interface DashboardStatBase {
  total: number;
  coverageStatus?: FactCoverageStatus;
}

export type DashboardStat =
  | DashboardStatBase & {
    type: 'workcase';
    byProgressGroup: Partial<Record<DashboardWorkCaseProgressGroup, number>>;
    byStatus?: never;
  }
  | DashboardStatBase & {
    type: Exclude<DashboardObjectType, 'workcase'>;
    byStatus: Record<string, number>;
    byProgressGroup?: never;
  };

interface DashboardFactItemBase {
  id: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  relativeTime: string;
  typeColor: string;
}

export type DashboardFactItem =
  | DashboardFactItemBase & {
    type: 'workcase';
    progress_group: DashboardWorkCaseProgressGroup;
    status?: never;
  }
  | DashboardFactItemBase & {
    type: Exclude<DashboardObjectType, 'workcase'>;
    status: string;
    progress_group?: never;
  };

export interface ObjectItem {
  id: string;
  type: string;
  title: string;
  title_en?: string;
  title_zh?: string;
  status: string;
  progress_group?: string;
  progress_step?: string;
  phase?: string;
  goal?: string;
  scope?: string;
  waiting_on?: string;
  blocking_summary?: string;
  path: string;
  created?: string;
  updated: string;
  kind?: 'type_not_integrated';
  message?: string;
  priority?: string;
  importance?: string;
  executionItemsProjectionValid?: boolean;
  executionItemTotal?: number;
  executionItemDone?: number;
  executionItemCancelled?: number;
  executionItemOpen?: number;
  executionItemsActive?: WorkCaseActiveItem[];
  successCriteria?: string[];
  /** ADR-specific fields */
  decision?: string;
  consequences?: string;
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
  carrier?: FactCarrier;
  check_status?: FactReadStatus;
  read_issues?: Array<Record<string, unknown>>;
  created_at?: string;
  updated_at?: string;
  disposition_summary?: string;
  relations?: Array<Record<string, unknown>>;
  /** Study-specific */
  research_intent?: string;
  research_question?: string;
  abstract?: string;
  recommendation_summary?: string;
  summary?: string;
  conclusion?: string;
  urls?: Array<string | UrlItem>;
  report_body?: string;
  /** Pitfall-specific */
  resolution?: string;
}

export interface WorkCaseActiveItem {
  id: string;
  title: string;
  status: 'in_progress' | 'blocked';
  blockingReason?: string;
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

export interface WorkCaseProgressOption {
  group: string;
  count: number;
}

export type FactCoverageStatus = 'complete' | 'partial' | 'unavailable';

export interface FactListProblem {
  code?: string;
  error?: string;
  object_ref?: {
    governed_project_id?: string;
    fact_type_key?: string;
    object_id?: string;
  };
  scope?: 'workcase_collection';
  check_status?: string;
  issues?: Array<Record<string, unknown>>;
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

export interface WorkCaseCriterionDefinition {
  criterion_id: string;
  statement: string;
}

export interface WorkCaseCriterionResult {
  criterion_id: string;
  outcome: 'satisfied' | 'not_satisfied' | 'not_verified';
  summary: string;
}

export interface WorkCaseItem {
  item_id: string;
  goal: string;
  expected_result: string;
  status: 'pending' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';
  depends_on?: string[];
  approach_summary?: string;
  template_keys?: string[];
  template_deviation_summary?: string;
  current_summary?: string;
  resume_from?: string;
  blocking_summary?: string;
  result_summary?: string;
}

export interface WorkCaseReview {
  reviewer: string;
  reviewed_at: string;
  subject_version: number;
  scope: string;
  conclusion: 'pass' | 'pass_with_followups' | 'changes_required' | 'blocked';
  feedback?: string[];
  controller_resolution?: string;
}

export interface WorkCaseExecutionApproval {
  subject_version: number;
  approved_at: string;
  summary: string;
  source_refs?: string[];
}

export interface WorkCaseRouteTarget {
  governed_project_id: string;
  fact_type_key: 'workcase';
  object_id: string;
  content_fingerprint: string;
}

export interface WorkCaseRelationTarget {
  governed_project_id: string;
  fact_type_key: 'workcase';
  object_id: string;
}

export interface WorkCaseRelation {
  relation_key: 'depends-on' | 'routed-to';
  target: WorkCaseRelationTarget;
}

export interface WorkCaseResidualDecision {
  residual_id: string;
  summary: string;
  proposed_disposition: 'route' | 'accept_stop';
  route_target?: WorkCaseRouteTarget;
}

export interface WorkCaseClosureProposal {
  proposed_outcome: 'completed' | 'partial' | 'not-achieved' | 'cancelled';
  proposed_disposition_summary: string;
  residual_decisions?: WorkCaseResidualDecision[];
}

export interface WorkCaseResidualResponsibility {
  residual_id: string;
  summary: string;
}

/** Exact-detail fields from the single current WorkCase contract. */
export interface WorkCaseDetailData extends Record<string, unknown> {
  object_id: string;
  fact_type_key: 'workcase';
  title: string;
  status: 'open' | 'blocked' | 'closed';
  created_at: string;
  updated_at: string;
  goal: string;
  scope: string;
  success_criterion_definitions: WorkCaseCriterionDefinition[];
  phase?: 'human_plan_confirming' | 'plan_revising' | 'executing' | 'controller_checking' | 'independent_reviewing' | 'closure_preparing' | 'human_closure_confirming';
  priority?: 'P0' | 'P1' | 'P2' | 'P3';
  summary?: string;
  resume_from?: string;
  waiting_on?: string;
  blocking_summary?: string;
  plan_version?: number;
  work_items?: WorkCaseItem[];
  creation_reviews?: WorkCaseReview[];
  execution_approval?: WorkCaseExecutionApproval;
  result_version?: number;
  success_criterion_results?: WorkCaseCriterionResult[];
  result_summary?: string;
  controller_check_summary?: string;
  result_reviews?: WorkCaseReview[];
  validation_summary?: string;
  closure_proposal?: WorkCaseClosureProposal;
  closure_outcome?: 'completed' | 'partial' | 'not-achieved' | 'cancelled';
  disposition_summary?: string;
  residual_responsibilities?: WorkCaseResidualResponsibility[];
  relations?: WorkCaseRelation[];
  urls?: UrlItem[];
}

export interface ObjectDetail<TData extends Record<string, unknown> = Record<string, unknown>> {
  ok: boolean;
  action: string;
  target: string;
  summary: { id: string; type: string; status?: string; phase?: string; read_status?: FactReadStatus };
  data: TData;
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(status: number, message: string, code?: string) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.code = code;
  }
}

async function request<T>(url: string): Promise<T> {
  const fullUrl = `${API_BASE}${url}`;
  const existing = inFlightRequests.get(fullUrl);
  if (existing) return existing as Promise<T>;

  const promise = fetch(fullUrl)
    .then(async (res) => {
      const body = await res.json().catch(() => null) as Record<string, unknown> | null;
      if (!res.ok) {
        const message = typeof body?.error === 'string' && body.error.trim()
          ? body.error
          : `API error: ${res.status} ${res.statusText}`;
        const code = typeof body?.exitCode === 'string' ? body.exitCode : undefined;
        throw new ApiRequestError(res.status, message, code);
      }
      return body as T;
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
  progress?: string,
): Promise<{
  ok: boolean;
  summary: { count: number; coverage_status?: FactCoverageStatus };
  data: {
    items: ObjectItem[];
    coverage_status?: FactCoverageStatus;
    observed_at?: string;
    object_read_problems?: FactListProblem[];
    coverage_problems?: FactListProblem[];
    statusOptions?: ObjectStatusOption[];
    progressOptions?: WorkCaseProgressOption[];
    priorityOptions?: ObjectStatusOption[];
    statusTotal?: number;
  };
}> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (priority) params.set('priority', priority);
  if (progress) params.set('progress', progress);
  const qs = params.toString();
  return request(`/objects/${type}${qs ? `?${qs}` : ''}`);
}

export async function fetchObjectDetail<TData extends Record<string, unknown> = Record<string, unknown>>(
  type: string,
  id: string,
): Promise<ObjectDetail<TData>> {
  return request<ObjectDetail<TData>>(`/objects/${type}/${encodeURIComponent(id)}`);
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
