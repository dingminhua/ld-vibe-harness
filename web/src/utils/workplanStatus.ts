export const WORKPLAN_CURRENT_STATUSES = [
  'subagents_plan_reviewing',
  'human_plan_confirming',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'human_closure_confirming',
  'closed',
] as const;

export const WORKPLAN_LEGACY_STATUSES = [
  'draft',
  'active',
  'review_needed',
] as const;

export const WORKPLAN_DEFAULT_LIST_STATUS = 'executing';

export const WORKPLAN_STATUS_ORDER = [
  'human_closure_confirming',
  'human_plan_confirming',
  'subagents_result_reviewing',
  'result_self_checking',
  'executing',
  'subagents_plan_reviewing',
  'review_needed',
  'active',
  'draft',
  'closed',
] as const;

const WORKPLAN_TERMINAL_STATUSES = new Set(['closed', 'archived', 'discarded', 'superseded']);
const WORKPLAN_HUMAN_CONFIRMING_STATUSES = new Set([
  'human_plan_confirming',
  'human_closure_confirming',
  'review_needed',
  'needs_human_gate',
]);
const WORKPLAN_RESULT_REVIEW_STATUSES = new Set([
  'result_self_checking',
  'subagents_result_reviewing',
]);
const WORKPLAN_ACTIVE_STATUSES = new Set([
  'subagents_plan_reviewing',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'draft',
  'active',
]);

export function isWorkPlanTerminalStatus(status: string): boolean {
  return WORKPLAN_TERMINAL_STATUSES.has(status);
}

export function isWorkPlanHumanConfirmingStatus(status: string): boolean {
  return WORKPLAN_HUMAN_CONFIRMING_STATUSES.has(status);
}

export function isWorkPlanResultReviewStatus(status: string): boolean {
  return WORKPLAN_RESULT_REVIEW_STATUSES.has(status);
}

export function isWorkPlanActiveStatus(status: string): boolean {
  return WORKPLAN_ACTIVE_STATUSES.has(status);
}

export function isWorkPlanClosureConfirmingStatus(status: string): boolean {
  return status === 'human_closure_confirming' || status === 'review_needed';
}
