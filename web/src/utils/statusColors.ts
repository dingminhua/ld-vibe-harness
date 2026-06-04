export const STATUS_COLORS: Record<string, string> = {
  active: '#00d4aa',
  executing: '#00d4aa',
  accepted: '#00d4aa',
  completed: '#6b7280',
  closed: '#6b7280',
  implemented: '#6b7280',
  resolved: '#6b7280',
  draft: '#f59e0b',
  proposed: '#f59e0b',
  planned: '#f59e0b',
  verifying: '#a78bfa',
  review_needed: '#a78bfa',
  rejected: '#ef4444',
  deprecated: '#ef4444',
  superseded: '#ef4444',
  archived: '#ef4444',
  suspended: '#ef4444',
};

export function getStatusColor(status: string): string {
  return STATUS_COLORS[status] ?? '#71717a';
}
