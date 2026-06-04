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

export interface ValidationData {
  ok: boolean;
  command: string;
  action: string;
  summary: { files: number; errors: number; warnings: number };
  issues: ValidationIssue[];
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
