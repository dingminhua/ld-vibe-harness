export const WORKCASE_CURRENT_STATUSES = [
  'human_plan_confirming',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'human_closure_confirming',
  'closed',
] as const;

export const WORKCASE_DEFAULT_LIST_STATUS = null;

/**
 * WorkCase 列表和 Dashboard 面向 Human 使用的进展分组。它们是由 phase
 * 确定性派生的浏览视图，不是 WorkCase 的 status 或生命周期阶段。
 */
export const WORKCASE_PROGRESS_GROUP_ORDER = [
  'plan_confirmation',
  'progressing',
  'closure_confirmation',
  'closed',
] as const;

export type WorkCaseProgressGroup = typeof WORKCASE_PROGRESS_GROUP_ORDER[number];

export const WORKCASE_PROGRESS_STEP_ORDER = [
  'item_execution',
  'controller_self_check',
  'independent_review',
  'controller_synthesis',
] as const;

export type WorkCaseProgressStep = typeof WORKCASE_PROGRESS_STEP_ORDER[number];

export interface WorkCaseProgressProjection {
  progressGroup: WorkCaseProgressGroup;
  progressStep?: WorkCaseProgressStep;
}

const WORKCASE_PHASE_PROGRESS: Record<string, WorkCaseProgressProjection> = {
  human_plan_confirming: { progressGroup: 'plan_confirmation' },
  executing: { progressGroup: 'progressing', progressStep: 'item_execution' },
  controller_checking: { progressGroup: 'progressing', progressStep: 'controller_self_check' },
  independent_reviewing: { progressGroup: 'progressing', progressStep: 'independent_review' },
  closure_preparing: { progressGroup: 'progressing', progressStep: 'controller_synthesis' },
  human_closure_confirming: { progressGroup: 'closure_confirmation' },
  closed: { progressGroup: 'closed' },
};

export function getWorkCaseProgressProjection(phase: string): WorkCaseProgressProjection | null {
  return WORKCASE_PHASE_PROGRESS[phase] ?? null;
}

export function getWorkCaseProgressGroup(phase: string): WorkCaseProgressGroup | null {
  return getWorkCaseProgressProjection(phase)?.progressGroup ?? null;
}

export function getWorkCaseProgressStep(phase: string): WorkCaseProgressStep | null {
  return getWorkCaseProgressProjection(phase)?.progressStep ?? null;
}

export function isWorkCaseProgressGroup(value: string | null | undefined): value is WorkCaseProgressGroup {
  return WORKCASE_PROGRESS_GROUP_ORDER.includes(value as WorkCaseProgressGroup);
}

export const WORKCASE_STATUS_ORDER = [
  'human_plan_confirming',
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
  'human_closure_confirming',
  'closed',
] as const;

/**
 * WorkCase 卡片只把实际还在推进的阶段视为动态态。等待 Human 决定和已关闭
 * 都是稳定停留点：前者不应被画成仍在执行，后者也不应被画成可继续推进。
 */
export const WORKCASE_DYNAMIC_STATUSES = [
  'executing',
  'result_self_checking',
  'subagents_result_reviewing',
] as const;

export type WorkCaseCardState = 'dynamic' | 'waiting' | 'closed';

const WORKCASE_DYNAMIC_STATUS_SET = new Set<string>(WORKCASE_DYNAMIC_STATUSES);

export function getWorkCaseCardState(status: string): WorkCaseCardState {
  if (status === 'closed') return 'closed';
  if (WORKCASE_DYNAMIC_STATUS_SET.has(status) || status === 'active' || status === 'draft') return 'dynamic';
  return 'waiting';
}

/** 仅动态态具有连续的四步推进轨迹；非当前阶段返回 -1。 */
export function getWorkCaseDynamicStageIndex(status: string): number {
  return WORKCASE_DYNAMIC_STATUSES.indexOf(status as typeof WORKCASE_DYNAMIC_STATUSES[number]);
}

const WORKCASE_PHASE_DISPLAY_STATUS: Record<string, string> = {
  human_plan_confirming: 'human_plan_confirming',
  executing: 'executing',
  controller_checking: 'result_self_checking',
  independent_reviewing: 'subagents_result_reviewing',
  // 关闭材料仍由 Controller 在质量复核链中准备；只有真正提交 Human 后，
  // 才进入 human_closure_confirming。这里继续显示结果复核，避免生命周期
  // 在复核后倒退成“结果自检中”，也避免提前制造“关闭待确认”的 Human 待办。
  closure_preparing: 'subagents_result_reviewing',
  human_closure_confirming: 'human_closure_confirming',
  closed: 'closed',
};

export function getWorkCaseDisplayStatus(phase: string, status: string): string {
  return WORKCASE_PHASE_DISPLAY_STATUS[phase] ?? status;
}

const WORKCASE_TERMINAL_STATUSES = new Set(['closed']);
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
