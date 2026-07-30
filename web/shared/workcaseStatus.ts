export const WORKCASE_CURRENT_PHASES = [
  'human_plan_confirming',
  'plan_revising',
  'executing',
  'controller_checking',
  'independent_reviewing',
  'closure_preparing',
  'human_closure_confirming',
] as const;

export const WORKCASE_DEFAULT_LIST_STATUS = null;

/**
 * WorkCase 列表和项目认知中心面向 Human 使用的进展分组。它们由当前 phase
 * 确定性派生，不是 WorkCase 的 status、phase 或生命周期分类。
 */
export const WORKCASE_PROGRESS_GROUP_ORDER = [
  'plan_confirmation',
  'progressing',
  'closure_confirmation',
  'closed',
] as const;

export type WorkCaseProgressGroup = typeof WORKCASE_PROGRESS_GROUP_ORDER[number];

/**
 * 只有结果推进主链使用这四个稳定环节。plan_revising 属于 progressing，
 * 但它是轨迹外的当前内部位置，不新增第五个 progress_step。
 */
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
  plan_revising: { progressGroup: 'progressing' },
  executing: { progressGroup: 'progressing', progressStep: 'item_execution' },
  controller_checking: { progressGroup: 'progressing', progressStep: 'controller_self_check' },
  independent_reviewing: { progressGroup: 'progressing', progressStep: 'independent_review' },
  closure_preparing: { progressGroup: 'progressing', progressStep: 'controller_synthesis' },
  human_closure_confirming: { progressGroup: 'closure_confirmation' },
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

/**
 * Terminality comes only from status; non-terminal progress comes only from
 * a current phase. Missing or invalid phase is deliberately not guessed.
 */
export function deriveWorkCaseProgressProjection(
  status: string,
  phase: string | null | undefined,
): WorkCaseProgressProjection | null {
  if (status === 'closed') {
    return phase === undefined || phase === null || phase === ''
      ? { progressGroup: 'closed' }
      : null;
  }
  if (status !== 'open' && status !== 'blocked') return null;
  return typeof phase === 'string' ? getWorkCaseProgressProjection(phase) : null;
}

export function isWorkCaseProgressGroup(value: string | null | undefined): value is WorkCaseProgressGroup {
  return WORKCASE_PROGRESS_GROUP_ORDER.includes(value as WorkCaseProgressGroup);
}
