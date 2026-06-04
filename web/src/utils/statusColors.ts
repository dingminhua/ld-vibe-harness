export const STATUS_COLORS: Record<string, { light: string; dark: string }> = {
  active: { light: '#059669', dark: '#00d4aa' },
  executing: { light: '#059669', dark: '#00d4aa' },
  accepted: { light: '#059669', dark: '#00d4aa' },
  completed: { light: '#6b7280', dark: '#6b7280' },
  closed: { light: '#6b7280', dark: '#6b7280' },
  implemented: { light: '#6b7280', dark: '#6b7280' },
  resolved: { light: '#6b7280', dark: '#6b7280' },
  draft: { light: '#d97706', dark: '#f59e0b' },
  proposed: { light: '#d97706', dark: '#f59e0b' },
  planned: { light: '#d97706', dark: '#f59e0b' },
  verifying: { light: '#7c3aed', dark: '#a78bfa' },
  review_needed: { light: '#7c3aed', dark: '#a78bfa' },
  rejected: { light: '#dc2626', dark: '#ef4444' },
  deprecated: { light: '#dc2626', dark: '#ef4444' },
  superseded: { light: '#dc2626', dark: '#ef4444' },
  archived: { light: '#dc2626', dark: '#ef4444' },
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
