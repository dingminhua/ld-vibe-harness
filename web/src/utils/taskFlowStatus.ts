import {
  BadgeCheck,
  CheckCircle2,
  CircleAlert,
  CircleDashed,
  CirclePlay,
  Clock3,
  ClipboardCheck,
  Hourglass,
  type LucideIcon,
} from 'lucide-react';
import type { LocaleKey } from '@/i18n/locales';
import type { RelatedObjectSummary } from '@/utils/api';

export type TaskFlowTranslate = (key: LocaleKey, params?: Record<string, string>) => string;

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'superseded']);
const PENDING_CLOSE_STATUSES = new Set(['review_needed']);
const TASK_RISK_STATUSES = new Set(['open', 'degraded', 'suspended', 'rejected', 'deprecated', 'unknown']);

export const taskFlowToneClass = {
  ready: 'border-sky-500/25 bg-sky-500/10 text-sky-500',
  executing: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  verifying: 'border-blue-500/30 bg-blue-500/10 text-blue-500',
  absorbing: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
  closed: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-500',
  blocked: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
  risk: 'border-red-500/30 bg-red-500/10 text-red-500',
  neutral: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
};

export type TaskFlowTone = keyof typeof taskFlowToneClass;

export const taskFlowRowClass: Record<TaskFlowTone, string> = {
  ready: 'border-sky-500/20 bg-sky-500/10 hover:bg-sky-500/15',
  executing: 'border-emerald-500/25 bg-emerald-500/10 hover:bg-emerald-500/15',
  verifying: 'border-blue-500/25 bg-blue-500/10 hover:bg-blue-500/15',
  absorbing: 'border-violet-500/25 bg-violet-500/10 hover:bg-violet-500/15',
  closed: 'border-zinc-500/25 bg-zinc-500/10 hover:bg-zinc-500/15',
  blocked: 'border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/15',
  risk: 'border-red-500/25 bg-red-500/10 hover:bg-red-500/15',
  neutral: 'border-ldvh-border bg-ldvh-bg hover:bg-ldvh-border/35',
};

export const TASK_FLOW_ORDER: TaskFlowTone[] = ['closed', 'absorbing', 'verifying', 'executing', 'blocked', 'risk', 'neutral'];
export const TASK_FLOW_LEGEND_ORDER: TaskFlowTone[] = ['closed', 'absorbing', 'verifying', 'executing', 'blocked'];
const TASK_FLOW_QUEUE_ORDER: TaskFlowTone[] = [...TASK_FLOW_ORDER].reverse();

export const taskFlowBarClass: Record<TaskFlowTone, string> = {
  ready: 'bg-sky-500',
  executing: 'bg-emerald-500',
  verifying: 'bg-blue-500',
  absorbing: 'bg-violet-500',
  closed: 'bg-zinc-500',
  blocked: 'bg-amber-500',
  risk: 'bg-red-500',
  neutral: 'bg-ldvh-border',
};

export const taskFlowIconClass: Record<TaskFlowTone, string> = {
  ready: 'text-sky-500',
  executing: 'text-emerald-500',
  verifying: 'text-blue-500',
  absorbing: 'text-violet-500',
  closed: 'text-zinc-500',
  blocked: 'text-amber-500',
  risk: 'text-red-500',
  neutral: 'text-ldvh-text-secondary',
};

export const taskFlowRowHoverTextClass: Record<TaskFlowTone, string> = {
  ready: 'group-hover/row:text-sky-500',
  executing: 'group-hover/row:text-emerald-500',
  verifying: 'group-hover/row:text-blue-500',
  absorbing: 'group-hover/row:text-violet-500',
  closed: 'group-hover/row:text-zinc-500',
  blocked: 'group-hover/row:text-amber-500',
  risk: 'group-hover/row:text-red-500',
  neutral: 'group-hover/row:text-ldvh-accent',
};

export const taskFlowDetailHoverTextClass: Record<TaskFlowTone, string> = {
  ready: 'group-hover/detail-task:text-sky-500',
  executing: 'group-hover/detail-task:text-emerald-500',
  verifying: 'group-hover/detail-task:text-blue-500',
  absorbing: 'group-hover/detail-task:text-violet-500',
  closed: 'group-hover/detail-task:text-zinc-500',
  blocked: 'group-hover/detail-task:text-amber-500',
  risk: 'group-hover/detail-task:text-red-500',
  neutral: 'group-hover/detail-task:text-ldvh-accent',
};

export const taskFlowActionClass: Record<TaskFlowTone, string> = {
  ready: 'bg-transparent text-sky-500 hover:bg-sky-500/10',
  executing: 'bg-transparent text-emerald-500 hover:bg-emerald-500/10',
  verifying: 'bg-transparent text-blue-500 hover:bg-blue-500/10',
  absorbing: 'bg-transparent text-violet-500 hover:bg-violet-500/10',
  closed: 'bg-transparent text-zinc-500 hover:bg-zinc-500/10',
  blocked: 'bg-transparent text-amber-500 hover:bg-amber-500/10',
  risk: 'bg-transparent text-red-500 hover:bg-red-500/10',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export function getTaskFlowIcon(tone: TaskFlowTone): LucideIcon {
  if (tone === 'ready') return CircleDashed;
  if (tone === 'executing') return CirclePlay;
  if (tone === 'verifying') return ClipboardCheck;
  if (tone === 'absorbing') return BadgeCheck;
  if (tone === 'blocked') return Hourglass;
  if (tone === 'closed') return CheckCircle2;
  if (tone === 'risk') return CircleAlert;
  return Clock3;
}

export function getTaskFlowTone(item: RelatedObjectSummary): TaskFlowTone {
  if (item.status === 'executing') return 'executing';
  if (item.status === 'verifying') return 'verifying';
  if (PENDING_CLOSE_STATUSES.has(item.status)) return 'absorbing';
  if (TERMINAL_STATUSES.has(item.status)) return 'closed';
  if (item.status === 'planned') return 'blocked';
  if (TASK_RISK_STATUSES.has(item.status)) return 'risk';
  return 'neutral';
}

export function getTaskFlowLabel(item: RelatedObjectSummary, t: TaskFlowTranslate, getStatus: (status: string) => string): string {
  const tone = getTaskFlowTone(item);
  if (tone === 'blocked') return t('objectList.taskFlowBlocked');
  if (tone === 'executing') return t('objectList.taskFlowExecuting');
  if (tone === 'verifying') return t('objectList.taskFlowVerifying');
  if (tone === 'absorbing') return t('objectList.taskFlowAbsorbing');
  if (tone === 'closed') return getStatus(item.status);
  return getStatus(item.status);
}

export function getTaskFlowToneLabel(tone: TaskFlowTone, t: TaskFlowTranslate, getStatus: (status: string) => string): string {
  if (tone === 'blocked') return t('objectList.taskFlowBlocked');
  if (tone === 'executing') return t('objectList.taskFlowExecuting');
  if (tone === 'verifying') return t('objectList.taskFlowVerifying');
  if (tone === 'absorbing') return t('objectList.taskFlowAbsorbing');
  if (tone === 'closed') return getStatus('closed');
  if (tone === 'risk') return t('objectList.taskFlowRisk');
  return t('objectList.taskFlowOther');
}

export function getTaskFlowCounts(tasks: RelatedObjectSummary[]): Record<TaskFlowTone, number> {
  return tasks.reduce<Record<TaskFlowTone, number>>((counts, task) => {
    const tone = getTaskFlowTone(task);
    counts[tone] += 1;
    return counts;
  }, {
    ready: 0,
    executing: 0,
    verifying: 0,
    absorbing: 0,
    blocked: 0,
    closed: 0,
    risk: 0,
    neutral: 0,
  });
}

function getTaskFlowPriority(item: RelatedObjectSummary): number {
  const tone = getTaskFlowTone(item);
  const priority = TASK_FLOW_QUEUE_ORDER.indexOf(tone);
  return priority === -1 ? TASK_FLOW_QUEUE_ORDER.length : priority;
}

export function sortPlanTasks(tasks: RelatedObjectSummary[]): RelatedObjectSummary[] {
  return [...tasks].sort((a, b) => {
    const priorityDelta = getTaskFlowPriority(a) - getTaskFlowPriority(b);
    if (priorityDelta !== 0) return priorityDelta;
    return a.id.localeCompare(b.id);
  });
}
