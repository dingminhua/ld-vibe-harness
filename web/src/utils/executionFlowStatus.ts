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

export type ExecutionFlowTranslate = (key: LocaleKey, params?: Record<string, string>) => string;

const TERMINAL_STATUSES = new Set(['closed', 'resolved', 'accepted', 'archived', 'discarded', 'superseded']);
const PENDING_CLOSE_STATUSES = new Set(['review_needed']);
const EXECUTION_RISK_STATUSES = new Set(['open', 'degraded', 'suspended', 'rejected', 'deprecated', 'unknown']);

export const executionFlowToneClass = {
  ready: 'border-sky-500/25 bg-sky-500/10 text-sky-500',
  executing: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500',
  verifying: 'border-blue-500/30 bg-blue-500/10 text-blue-500',
  absorbing: 'border-violet-500/30 bg-violet-500/10 text-violet-500',
  closed: 'border-zinc-500/30 bg-zinc-500/10 text-zinc-500',
  blocked: 'border-amber-500/35 bg-amber-500/10 text-amber-500',
  risk: 'border-red-500/30 bg-red-500/10 text-red-500',
  neutral: 'border-ldvh-border bg-ldvh-bg text-ldvh-text-secondary',
};

export type ExecutionFlowTone = keyof typeof executionFlowToneClass;

export const executionFlowRowClass: Record<ExecutionFlowTone, string> = {
  ready: 'border-sky-500/20 bg-sky-500/10 hover:bg-sky-500/15',
  executing: 'border-emerald-500/25 bg-emerald-500/10 hover:bg-emerald-500/15',
  verifying: 'border-blue-500/25 bg-blue-500/10 hover:bg-blue-500/15',
  absorbing: 'border-violet-500/25 bg-violet-500/10 hover:bg-violet-500/15',
  closed: 'border-zinc-500/25 bg-zinc-500/10 hover:bg-zinc-500/15',
  blocked: 'border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/15',
  risk: 'border-red-500/25 bg-red-500/10 hover:bg-red-500/15',
  neutral: 'border-ldvh-border bg-ldvh-bg hover:bg-ldvh-border/35',
};

export const EXECUTION_FLOW_ORDER: ExecutionFlowTone[] = ['closed', 'absorbing', 'verifying', 'executing', 'ready', 'blocked', 'risk', 'neutral'];
export const EXECUTION_FLOW_LEGEND_ORDER: ExecutionFlowTone[] = ['closed', 'absorbing', 'verifying', 'executing', 'ready', 'blocked'];
const EXECUTION_FLOW_QUEUE_ORDER: ExecutionFlowTone[] = [...EXECUTION_FLOW_ORDER].reverse();

export const executionFlowBarClass: Record<ExecutionFlowTone, string> = {
  ready: 'bg-sky-500',
  executing: 'bg-emerald-500',
  verifying: 'bg-blue-500',
  absorbing: 'bg-violet-500',
  closed: 'bg-zinc-500',
  blocked: 'bg-amber-500',
  risk: 'bg-red-500',
  neutral: 'bg-ldvh-border',
};

export const executionFlowIconClass: Record<ExecutionFlowTone, string> = {
  ready: 'text-sky-500',
  executing: 'text-emerald-500',
  verifying: 'text-blue-500',
  absorbing: 'text-violet-500',
  closed: 'text-zinc-500',
  blocked: 'text-amber-500',
  risk: 'text-red-500',
  neutral: 'text-ldvh-text-secondary',
};

export const executionFlowRowHoverTextClass: Record<ExecutionFlowTone, string> = {
  ready: 'group-hover/row:text-sky-500',
  executing: 'group-hover/row:text-emerald-500',
  verifying: 'group-hover/row:text-blue-500',
  absorbing: 'group-hover/row:text-violet-500',
  closed: 'group-hover/row:text-zinc-500',
  blocked: 'group-hover/row:text-amber-500',
  risk: 'group-hover/row:text-red-500',
  neutral: 'group-hover/row:text-ldvh-accent',
};

export const executionFlowDetailHoverTextClass: Record<ExecutionFlowTone, string> = {
  ready: 'group-hover/detail-item:text-sky-500',
  executing: 'group-hover/detail-item:text-emerald-500',
  verifying: 'group-hover/detail-item:text-blue-500',
  absorbing: 'group-hover/detail-item:text-violet-500',
  closed: 'group-hover/detail-item:text-zinc-500',
  blocked: 'group-hover/detail-item:text-amber-500',
  risk: 'group-hover/detail-item:text-red-500',
  neutral: 'group-hover/detail-item:text-ldvh-accent',
};

export const executionFlowActionClass: Record<ExecutionFlowTone, string> = {
  ready: 'bg-transparent text-sky-500 hover:bg-sky-500/10',
  executing: 'bg-transparent text-emerald-500 hover:bg-emerald-500/10',
  verifying: 'bg-transparent text-blue-500 hover:bg-blue-500/10',
  absorbing: 'bg-transparent text-violet-500 hover:bg-violet-500/10',
  closed: 'bg-transparent text-zinc-500 hover:bg-zinc-500/10',
  blocked: 'bg-transparent text-amber-500 hover:bg-amber-500/10',
  risk: 'bg-transparent text-red-500 hover:bg-red-500/10',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export const executionFlowRowActionClass: Record<ExecutionFlowTone, string> = {
  ready: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-sky-500/10 hover:text-sky-500',
  executing: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-emerald-500/10 hover:text-emerald-500',
  verifying: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-blue-500/10 hover:text-blue-500',
  absorbing: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-violet-500/10 hover:text-violet-500',
  closed: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-500',
  blocked: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-amber-500/10 hover:text-amber-500',
  risk: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-red-500/10 hover:text-red-500',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export const executionFlowDetailActionClass: Record<ExecutionFlowTone, string> = {
  ready: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-sky-500/10 hover:text-sky-500',
  executing: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-emerald-500/10 hover:text-emerald-500',
  verifying: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-blue-500/10 hover:text-blue-500',
  absorbing: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-violet-500/10 hover:text-violet-500',
  closed: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-zinc-500/10 hover:text-zinc-500',
  blocked: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-amber-500/10 hover:text-amber-500',
  risk: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-red-500/10 hover:text-red-500',
  neutral: 'bg-transparent text-ldvh-text-secondary/70 hover:bg-ldvh-border/30 hover:text-ldvh-accent',
};

export function getExecutionFlowIcon(tone: ExecutionFlowTone): LucideIcon {
  if (tone === 'ready') return CircleDashed;
  if (tone === 'executing') return CirclePlay;
  if (tone === 'verifying') return ClipboardCheck;
  if (tone === 'absorbing') return BadgeCheck;
  if (tone === 'blocked') return Hourglass;
  if (tone === 'closed') return CheckCircle2;
  if (tone === 'risk') return CircleAlert;
  return Clock3;
}

export function getExecutionFlowTone(item: RelatedObjectSummary): ExecutionFlowTone {
  if (item.status === 'executing') return 'executing';
  if (item.status === 'verifying') return 'verifying';
  if (PENDING_CLOSE_STATUSES.has(item.status)) return 'absorbing';
  if (TERMINAL_STATUSES.has(item.status)) return 'closed';
  if (item.status === 'planned') return item.blockingReason ? 'blocked' : 'ready';
  if (EXECUTION_RISK_STATUSES.has(item.status)) return 'risk';
  return 'neutral';
}

export function getExecutionFlowLabel(item: RelatedObjectSummary, t: ExecutionFlowTranslate, getStatus: (status: string) => string): string {
  const tone = getExecutionFlowTone(item);
  if (tone === 'blocked') return t('objectList.executionFlowBlocked');
  if (tone === 'ready') return t('objectList.executionFlowReady');
  if (tone === 'executing') return t('objectList.executionFlowExecuting');
  if (tone === 'verifying') return t('objectList.executionFlowVerifying');
  if (tone === 'absorbing') return t('objectList.executionFlowAbsorbing');
  if (tone === 'closed') return getStatus(item.status);
  return getStatus(item.status);
}

export function getExecutionFlowToneLabel(tone: ExecutionFlowTone, t: ExecutionFlowTranslate, getStatus: (status: string) => string): string {
  if (tone === 'blocked') return t('objectList.executionFlowBlocked');
  if (tone === 'ready') return t('objectList.executionFlowReady');
  if (tone === 'executing') return t('objectList.executionFlowExecuting');
  if (tone === 'verifying') return t('objectList.executionFlowVerifying');
  if (tone === 'absorbing') return t('objectList.executionFlowAbsorbing');
  if (tone === 'closed') return getStatus('closed');
  if (tone === 'risk') return t('objectList.executionFlowRisk');
  return t('objectList.executionFlowOther');
}

export function getExecutionFlowCounts(items: RelatedObjectSummary[]): Record<ExecutionFlowTone, number> {
  return items.reduce<Record<ExecutionFlowTone, number>>((counts, item) => {
    const tone = getExecutionFlowTone(item);
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

function getExecutionFlowPriority(item: RelatedObjectSummary): number {
  const tone = getExecutionFlowTone(item);
  const priority = EXECUTION_FLOW_QUEUE_ORDER.indexOf(tone);
  return priority === -1 ? EXECUTION_FLOW_QUEUE_ORDER.length : priority;
}

export function sortPlanExecutionItems(items: RelatedObjectSummary[]): RelatedObjectSummary[] {
  return [...items].sort((a, b) => {
    const priorityDelta = getExecutionFlowPriority(a) - getExecutionFlowPriority(b);
    if (priorityDelta !== 0) return priorityDelta;
    return a.id.localeCompare(b.id);
  });
}
