export const WORKCASE_CURRENT_STATUSES = [
  'subagents_plan_reviewing',
  'human_plan_confirming',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'human_closure_confirming',
  'closed',
] as const;

export const WORKCASE_DEFAULT_LIST_STATUS = null;

export const WORKCASE_STATUS_ORDER = [
  'subagents_plan_reviewing',
  'human_plan_confirming',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'human_closure_confirming',
  'closed',
] as const;

const WORKCASE_TERMINAL_STATUSES = new Set(['closed', 'archived', 'discarded', 'superseded']);
const WORKCASE_HUMAN_CONFIRMING_STATUSES = new Set([
  'human_plan_confirming',
  'human_closure_confirming',
  'review_needed',
]);
const WORKCASE_RESULT_REVIEW_STATUSES = new Set([
  'result_self_checking',
  'subagents_result_reviewing',
]);
const WORKCASE_ACTIVE_STATUSES = new Set([
  'subagents_plan_reviewing',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'draft',
  'active',
]);

export function isWorkCaseTerminalStatus(status: string): boolean {
  return WORKCASE_TERMINAL_STATUSES.has(status);
}

export function isWorkCaseHumanConfirmingStatus(status: string): boolean {
  return WORKCASE_HUMAN_CONFIRMING_STATUSES.has(status);
}

export function isWorkCaseResultReviewStatus(status: string): boolean {
  return WORKCASE_RESULT_REVIEW_STATUSES.has(status);
}

export function isWorkCaseActiveStatus(status: string): boolean {
  return WORKCASE_ACTIVE_STATUSES.has(status);
}

export function isWorkCaseClosureConfirmingStatus(status: string): boolean {
  return status === 'human_closure_confirming' || status === 'review_needed';
}
