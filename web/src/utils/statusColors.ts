export const STATUS_COLORS: Record<string, { light: string; dark: string }> = {
  active: { light: '#059669', dark: '#00d4aa' },
  human_plan_confirming: { light: '#8b5cf6', dark: '#a78bfa' },
  executing: { light: '#059669', dark: '#00d4aa' },
  result_self_checking: { light: '#3b82f6', dark: '#60a5fa' },
  subagents_result_reviewing: { light: '#6366f1', dark: '#818cf8' },
  human_closure_confirming: { light: '#8b5cf6', dark: '#a78bfa' },
  plan_confirmation: { light: '#8b5cf6', dark: '#a78bfa' },
  progressing: { light: '#0284c7', dark: '#38bdf8' },
  closure_confirmation: { light: '#8b5cf6', dark: '#a78bfa' },
  accepted: { light: '#059669', dark: '#00d4aa' },
  closed: { light: '#6b7280', dark: '#6b7280' },
  resolved: { light: '#6b7280', dark: '#6b7280' },
  routed: { light: '#6b7280', dark: '#6b7280' },
  implemented: { light: '#059669', dark: '#00d4aa' },
  open: { light: '#d97706', dark: '#f59e0b' },
  pending: { light: '#d97706', dark: '#f59e0b' },
  draft: { light: '#d97706', dark: '#f59e0b' },
  proposed: { light: '#d97706', dark: '#f59e0b' },
  planned: { light: '#d97706', dark: '#f59e0b' },
  verifying: { light: '#3b82f6', dark: '#3b82f6' },
  limited: { light: '#d97706', dark: '#f59e0b' },
  input_issue: { light: '#d97706', dark: '#f59e0b' },
  capability_gap: { light: '#ca8a04', dark: '#eab308' },
  evidence_gap: { light: '#ca8a04', dark: '#eab308' },
  fact_conflict: { light: '#ea580c', dark: '#fb923c' },
  review_needed: { light: '#8b5cf6', dark: '#8b5cf6' },
rejected: { light: '#dc2626', dark: '#ef4444' },
  deprecated: { light: '#dc2626', dark: '#ef4444' },
  discarded: { light: '#dc2626', dark: '#ef4444' },
  archived: { light: '#6b7280', dark: '#6b7280' },
  suspended: { light: '#dc2626', dark: '#ef4444' },
};

function isDarkMode(): boolean {
  return document.documentElement.classList.contains('dark');
}

export function getStatusColor(status: string): string {
  const entry = STATUS_COLORS[status];
  if (!entry) return isDarkMode() ? '#71717a' : '#9ca3af';
  return isDarkMode() ? entry.dark : entry.light;
}
