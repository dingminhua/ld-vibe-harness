import {
  CheckCircle2,
  CircleAlert,
  CircleDashed,
  CirclePlay,
  Clock3,
  Hourglass,
  CircleX,
  type LucideIcon,
} from 'lucide-react';
import type { LocaleKey } from '@/i18n/locales';
import type { RelatedObjectSummary } from '@/utils/api';

export type ExecutionFlowTranslate = (key: LocaleKey, params?: Record<string, string>) => string;

const EXECUTION_RISK_STATUSES = new Set(['unknown']);

export const executionFlowToneClass = {
  pending: 'border-sky-500/25 bg-sky-500/10 text-sky-500',
  inProgress: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  blocked: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
  completed: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-500',
  cancelled: 'border-zinc-500/25 bg-zinc-500/5 text-zinc-400',
  risk: 'border-red-500/30 bg-red-500/10 text-red-500',
  neutral: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
};

export type ExecutionFlowTone = keyof typeof executionFlowToneClass;

export const executionFlowRowClass: Record<ExecutionFlowTone, string> = {
  pending: 'border-sky-500/20 bg-sky-500/10 hover:bg-sky-500/15',
  inProgress: 'border-emerald-500/25 bg-emerald-500/10 hover:bg-emerald-500/15',
  blocked: 'border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/15',
  completed: 'border-zinc-500/25 bg-zinc-500/10 hover:bg-zinc-500/15',
  cancelled: 'border-zinc-500/20 bg-zinc-500/5 hover:bg-zinc-500/10',
  risk: 'border-red-500/25 bg-red-500/10 hover:bg-red-500/15',
  neutral: 'border-ldvh-border bg-ldvh-bg hover:bg-ldvh-border/35',
};

export const EXECUTION_FLOW_ORDER: ExecutionFlowTone[] = ['completed', 'cancelled', 'blocked', 'inProgress', 'pending', 'risk', 'neutral'];
const EXECUTION_FLOW_QUEUE_ORDER: ExecutionFlowTone[] = ['blocked', 'inProgress', 'pending', 'cancelled', 'completed', 'risk', 'neutral'];

export const executionFlowBarClass: Record<ExecutionFlowTone, string> = {
  pending: 'bg-sky-500',
  inProgress: 'bg-emerald-500',
  blocked: 'bg-amber-500',
  completed: 'bg-zinc-500',
  cancelled: 'bg-zinc-400',
  risk: 'bg-red-500',
  neutral: 'bg-ldvh-border',
};

export const executionFlowIconClass: Record<ExecutionFlowTone, string> = {
  pending: 'text-sky-500',
  inProgress: 'text-emerald-500',
  blocked: 'text-amber-500',
  completed: 'text-zinc-500',
  cancelled: 'text-zinc-400',
  risk: 'text-red-500',
  neutral: 'text-ldvh-text-secondary',
};

export const executionFlowRowHoverTextClass: Record<ExecutionFlowTone, string> = {
  pending: 'group-hover/row:text-sky-500',
  inProgress: 'group-hover/row:text-emerald-500',
  blocked: 'group-hover/row:text-amber-500',
  completed: 'group-hover/row:text-zinc-500',
  cancelled: 'group-hover/row:text-zinc-400',
  risk: 'group-hover/row:text-red-500',
  neutral: 'group-hover/row:text-ldvh-accent',
};

export const executionFlowDetailHoverTextClass: Record<ExecutionFlowTone, string> = {
  pending: 'group-hover/detail-item:text-sky-500',
  inProgress: 'group-hover/detail-item:text-emerald-500',
  blocked: 'group-hover/detail-item:text-amber-500',
  completed: 'group-hover/detail-item:text-zinc-500',
  cancelled: 'group-hover/detail-item:text-zinc-400',
  risk: 'group-hover/detail-item:text-red-500',
  neutral: 'group-hover/detail-item:text-ldvh-accent',
};

export const executionFlowActionClass: Record<ExecutionFlowTone, string> = {
  pending: 'bg-transparent text-sky-500 hover:bg-sky-500/10',
  inProgress: 'bg-transparent text-emerald-500 hover:bg-emerald-500/10',
  blocked: 'bg-transparent text-amber-500 hover:bg-amber-500/10',
  completed: 'bg-transparent text-zinc-500 hover:bg-zinc-500/10',
  cancelled: 'bg-transparent text-zinc-400 hover:bg-zinc-500/10',
  risk: 'bg-transparent text-red-500 hover:bg-red-500/10',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export const executionFlowRowActionClass: Record<ExecutionFlowTone, string> = {
  pending: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-sky-500/10 hover:text-sky-500',
  inProgress: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-emerald-500/10 hover:text-emerald-500',
  blocked: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-amber-500/10 hover:text-amber-500',
  completed: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-500',
  cancelled: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-400',
  risk: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-red-500/10 hover:text-red-500',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export const executionFlowDetailActionClass: Record<ExecutionFlowTone, string> = {
  pending: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-sky-500/10 hover:text-sky-500',
  inProgress: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-emerald-500/10 hover:text-emerald-500',
  blocked: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-amber-500/10 hover:text-amber-500',
  completed: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-500',
  cancelled: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-400',
  risk: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-red-500/10 hover:text-red-500',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export function getExecutionFlowIcon(tone: ExecutionFlowTone): LucideIcon {
  if (tone === 'pending') return CircleDashed;
  if (tone === 'inProgress') return CirclePlay;
  if (tone === 'blocked') return Hourglass;
  if (tone === 'completed') return CheckCircle2;
  if (tone === 'cancelled') return CircleX;
  if (tone === 'risk') return CircleAlert;
  return Clock3;
}

export function getExecutionFlowTone(item: RelatedObjectSummary): ExecutionFlowTone {
  if (item.status === 'blocked') return 'blocked';
  if (item.status === 'in_progress') return 'inProgress';
  if (item.status === 'pending') return item.blockingReason ? 'blocked' : 'pending';
  if (item.status === 'completed') return 'completed';
  if (item.status === 'cancelled') return 'cancelled';
  if (EXECUTION_RISK_STATUSES.has(item.status)) return 'risk';
  return 'neutral';
}

export function getExecutionFlowLabel(item: RelatedObjectSummary, t: ExecutionFlowTranslate, getStatus: (status: string) => string): string {
  const tone = getExecutionFlowTone(item);
  if (tone === 'blocked') return t('objectList.executionFlowBlocked');
  if (tone === 'pending') return t('objectList.executionFlowPending');
  if (tone === 'inProgress') return t('objectList.executionFlowInProgress');
  if (tone === 'completed') return t('objectList.executionFlowCompleted');
  if (tone === 'cancelled') return t('objectList.executionFlowCancelled');
  if (tone === 'risk') return t('objectList.executionFlowRisk');
  return getStatus(item.status);
}

export function getExecutionFlowToneLabel(tone: ExecutionFlowTone, t: ExecutionFlowTranslate, _getStatus: (status: string) => string): string {
  if (tone === 'blocked') return t('objectList.executionFlowBlocked');
  if (tone === 'pending') return t('objectList.executionFlowPending');
  if (tone === 'inProgress') return t('objectList.executionFlowInProgress');
  if (tone === 'completed') return t('objectList.executionFlowCompleted');
  if (tone === 'cancelled') return t('objectList.executionFlowCancelled');
  if (tone === 'risk') return t('objectList.executionFlowRisk');
  return t('objectList.executionFlowOther');
}

export function getExecutionFlowCounts(items: RelatedObjectSummary[]): Record<ExecutionFlowTone, number> {
  return items.reduce<Record<ExecutionFlowTone, number>>((counts, item) => {
    const tone = getExecutionFlowTone(item);
    counts[tone] += 1;
    return counts;
  }, {
    pending: 0,
    inProgress: 0,
    blocked: 0,
    completed: 0,
    cancelled: 0,
    risk: 0,
    neutral: 0,
  });
}

function getExecutionFlowPriority(item: RelatedObjectSummary): number {
  const tone = getExecutionFlowTone(item);
  const priority = EXECUTION_FLOW_QUEUE_ORDER.indexOf(tone);
  return priority === -1 ? EXECUTION_FLOW_QUEUE_ORDER.length : priority;
}

export function sortWorkCaseExecutionItems(items: RelatedObjectSummary[]): RelatedObjectSummary[] {
  return [...items].sort((a, b) => {
    const priorityDelta = getExecutionFlowPriority(a) - getExecutionFlowPriority(b);
    if (priorityDelta !== 0) return priorityDelta;
    return a.id.localeCompare(b.id);
  });
}
