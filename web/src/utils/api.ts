const API_BASE = '/api';

export interface DashboardData {
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
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchDashboard(locale?: string): Promise<DashboardData> {
  const params = locale ? `?locale=${locale}` : '';
  return request<DashboardData>(`/dashboard${params}`);
}

export async function fetchObjects(type: string, status?: string): Promise<{ ok: boolean; summary: { count: number }; data: { items: ObjectItem[] } }> {
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

/** 更新对象指定字段 */
export async function patchObjectField(type: string, id: string, field: string, value: string): Promise<ObjectDetail> {
  const res = await fetch(`${API_BASE}/objects/${type}/${encodeURIComponent(id)}/field`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ field, value }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.error || `API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
