import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import {
  WORKCASE_CURRENT_STATUSES,
  WORKCASE_STATUS_ORDER,
  WORKCASE_PROGRESS_GROUP_ORDER,
  WORKCASE_PROGRESS_STEP_ORDER,
  getWorkCaseProgressProjection,
} from '../../shared/workcaseStatus.ts';
import { buildWorkCaseSummaries } from '../../api/routes/objects.ts';

const webRoot = path.resolve(import.meta.dirname, '../..');

function source(relativePath: string): string {
  return fs.readFileSync(path.join(webRoot, relativePath), 'utf8');
}

test('WorkCase cards present four progress groups instead of lifecycle categories', () => {
  const status = source('shared/workcaseStatus.ts');
  const list = source('src/pages/ObjectList.tsx');
  const locales = source('src/i18n/locales.ts');

  assert.deepEqual(WORKCASE_PROGRESS_GROUP_ORDER, ['plan_confirmation', 'progressing', 'closure_confirmation', 'closed']);
  assert.deepEqual(WORKCASE_PROGRESS_STEP_ORDER, ['item_execution', 'controller_self_check', 'independent_review', 'controller_synthesis']);
  assert.match(status, /export function getWorkCaseProgressProjection/);
  assert.match(list, /function WorkCaseProgressSignal/);
  assert.match(list, /WORKCASE_PROGRESS_STEP_ORDER\.map/);
  assert.doesNotMatch(list, /const isPast|isPast \?/);
  assert.match(list, /objectList\.progressGroupFilter/);
  assert.match(list, /displayStatus=\{progressGroup \?\? 'unknown'\}/);
  assert.match(list, /<WorkCaseProgressSignal progressGroup=\{progressGroup\}/);
  assert.match(list, /showNonActiveReason=\{false\}/);
  assert.match(locales, /plan_confirmation: \{ zh: '方案待确认'/);
  assert.match(locales, /progressing: \{ zh: '推进中'/);
  assert.match(locales, /closure_confirmation: \{ zh: '关闭待确认'/);
});

test('pre-creation plan review is not exposed as a current WorkCase status', () => {
  assert.equal(WORKCASE_CURRENT_STATUSES.includes('subagents_plan_reviewing' as never), false);
  assert.equal(WORKCASE_STATUS_ORDER.includes('subagents_plan_reviewing' as never), false);
  assert.equal(WORKCASE_CURRENT_STATUSES[0], 'human_plan_confirming');
});

test('closure preparation remains progressing and is identified as controller synthesis', () => {
  assert.deepEqual(getWorkCaseProgressProjection('closure_preparing'), {
    progressGroup: 'progressing',
    progressStep: 'controller_synthesis',
  });
  assert.equal(getWorkCaseProgressProjection('human_closure_confirming')?.progressGroup, 'closure_confirmation');
});

test('plan confirmation cards fully show only goal and success criteria as Human decision inputs', () => {
  const list = source('src/pages/ObjectList.tsx');
  const locales = source('src/i18n/locales.ts');
  const branchStart = list.indexOf("if (progressGroup === 'plan_confirmation')");
  const otherStateBodyStart = list.indexOf('const executionItems = obj.executionItems', branchStart);
  const branch = list.slice(branchStart, otherStateBodyStart);

  assert.ok(branchStart >= 0);
  assert.ok(otherStateBodyStart > branchStart);
  assert.match(branch, /<WorkCasePlanConfirmationContent goal=\{obj\.goal\} successCriteria=\{obj\.successCriteria\}/);
  assert.doesNotMatch(branch, /WorkCaseProgressSignal|WorkCaseCardSummary|ExecutionFlowBar|visibleExecutionItems/);
  assert.match(branch, /prominentTitle/);
  const content = list.slice(list.indexOf('function WorkCasePlanConfirmationContent'), list.indexOf('function WorkCaseProgressingContent'));
  assert.match(content, /ldvh-card-decision-title/);
  assert.match(content, /ldvh-card-decision-body/);
  assert.match(content, /<ul className=/);
  assert.match(content, /rounded-full bg-ldvh-text-secondary\/60/);
  assert.doesNotMatch(content, /<ol|\{index \+ 1\}\.\s*<\/span>/);
  assert.doesNotMatch(content, /scope|Coverage|Exclusion|line-clamp|slice\(0,/);
  assert.doesNotMatch(content, /text-\[\d+px\]/);
  assert.doesNotMatch(content, /stopPropagation|cursor-default/);
  assert.match(locales, /'objectList\.workcaseGoal': '目标'/);
});

test('progressing cards show current step, item progress, active items, waiting, and blocking without rounds', () => {
  const list = source('src/pages/ObjectList.tsx');
  const locales = source('src/i18n/locales.ts');
  const branchStart = list.indexOf("if (progressGroup === 'progressing')");
  const otherStateBodyStart = list.indexOf('const executionItems = obj.executionItems', branchStart);
  const branch = list.slice(branchStart, otherStateBodyStart);

  assert.ok(branchStart >= 0);
  assert.ok(otherStateBodyStart > branchStart);
  assert.match(branch, /<WorkCaseProgressingContent/);
  assert.match(branch, /goal=\{obj\.goal\}/);
  assert.match(branch, /progressStep=\{progressStep\}/);
  assert.match(branch, /executionItemDone=\{obj\.executionItemDone \?\? 0\}/);
  assert.match(branch, /executionItemCancelled=\{obj\.executionItemCancelled \?\? 0\}/);
  assert.match(branch, /executionItemOpen=\{obj\.executionItemOpen \?\? 0\}/);
  assert.match(branch, /executionItemsActive=\{obj\.executionItemsActive \?\? \[\]\}/);
  assert.match(branch, /waitingOn=\{obj\.waiting_on\}/);
  assert.match(branch, /isBlocked=\{obj\.responsibilityStatus === 'blocked'\}/);
  assert.match(branch, /blockingSummary=\{obj\.blocking_summary\}/);
  assert.match(branch, /prominentTitle/);
  assert.doesNotMatch(branch, /progressHistory|progressRound|successCriteria|WorkCaseProgressSignal|WorkCaseCardSummary|ExecutionFlowBar|visibleExecutionItems/);

  const content = list.slice(list.indexOf('function WorkCaseProgressingContent'), list.indexOf('function WorkCaseProgressSignal'));
  assert.match(content, /<WorkCaseGoalSection goal=\{goal\}/);
  assert.match(content, /objectList\.workcaseCurrentProgress/);
  assert.match(content, /objectList\.workcaseStageUnavailable/);
  assert.match(content, /objectList\.workcaseItemsUnavailable/);
  assert.match(content, /objectList\.workcaseItemProgress/);
  assert.match(content, /objectList\.workcaseItemsCancelled/);
  assert.match(content, /objectList\.workcaseCurrentItems/);
  assert.match(content, /executionItemsActive\.map/);
  assert.match(content, /item\.status === 'blocked'/);
  assert.match(content, /item\.blockingReason/);
  assert.match(content, /objectList\.workcaseWaitingOn/);
  assert.match(content, /objectList\.workcaseBlockingReason/);
  assert.match(content, /<ol/);
  assert.match(content, /grid-cols-4/);
  assert.doesNotMatch(content, /grid-cols-2/);
  assert.match(content, /WORKCASE_PROGRESS_STEP_ORDER\.map/);
  assert.match(content, /aria-current=\{isCurrent \? 'step'/);
  assert.match(content, /\{index \+ 1\}/);
  assert.match(content, /ldvh-card-decision-title min-w-0 break-words text-current/);
  assert.match(content, /ldvh-meta-muted break-all/);
  assert.doesNotMatch(content, /roundLabel|workcaseRound|progressHistory|ldvh-chip|isPast|CheckCircle2|successCriteria|ExecutionFlowBar|slice\(0,/);
  assert.doesNotMatch(content, /text-\[\d+px\]/);
  assert.match(locales, /'objectList\.workcaseCurrentProgress': '当前进展'/);
  assert.match(locales, /'objectList\.workcaseWaitingOn': '正在等待'/);
  assert.match(locales, /'objectList\.workcaseBlockingReason': '阻塞原因'/);
  assert.match(locales, /'objectList\.workcaseItemProgress': '已完成 \{done\}\/\{total\}'/);
  assert.doesNotMatch(locales, /objectList\.workcaseRound/);
});

test('WorkCase list projection preserves non-linear active items and ignores progress history', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0099',
    object_id: 'workcase-0099',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    title: '并行推进投影',
    path: 'ldvh-base/workcases/workcase-0099.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T12:00:00+08:00',
    updated: '2026-07-26T12:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 2,
    progress_history: { malformed: 'Web must not consume this field' },
    work_items: [
      {
        item_id: 'item-01', goal: '已完成项', expected_result: '形成结果 A', approach_summary: '执行 A',
        status: 'completed', result_summary: 'A 已完成',
      },
      {
        item_id: 'item-02', goal: '已取消项', expected_result: '形成结果 B', approach_summary: '执行 B',
        status: 'cancelled', result_summary: 'B 已取消',
      },
      {
        item_id: 'item-03', goal: '并行当前项 A', expected_result: '形成结果 C', approach_summary: '执行 C',
        status: 'in_progress', current_summary: '正在执行 C', resume_from: '继续 C',
      },
      {
        item_id: 'item-04', goal: '并行阻塞项 B', expected_result: '形成结果 D', approach_summary: '执行 D',
        status: 'blocked', current_summary: 'D 正在等待', resume_from: '条件解除后继续 D',
        blocking_summary: '等待外部输入。',
      },
      {
        item_id: 'item-05', goal: '待执行项', expected_result: '形成结果 E', approach_summary: '执行 E',
        status: 'pending',
      },
    ],
  }]);

  assert.equal(summary.executionItemTotal, 5);
  assert.equal(summary.executionItemDone, 1);
  assert.equal(summary.executionItemCancelled, 1);
  assert.equal(summary.executionItemOpen, 3);
  assert.equal(summary.executionItemsProjectionValid, true);
  assert.deepEqual(summary.executionItemsInProgress?.map((item) => item.id), ['item-03']);
  assert.deepEqual(summary.executionItemsActive?.map((item) => item.id), ['item-03', 'item-04']);
  assert.equal(summary.executionItemsActive?.[1].blockingReason, '等待外部输入。');
  assert.equal('progressHistoryState' in summary, false);
  assert.equal('progressRound' in summary, false);
  assert.equal('progressEventId' in summary, false);
});

test('current WorkCase item projection never invents missing IDs or goals', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0101',
    object_id: 'workcase-0101',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    title: '拒绝补造当前工作项',
    path: 'ldvh-base/workcases/workcase-0101.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T10:00:00+08:00',
    updated: '2026-07-26T10:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 1,
    work_items: [
      {
        goal: '缺少稳定 ID', expected_result: '结果一', approach_summary: '方法一', status: 'in_progress',
        current_summary: '执行中', resume_from: '继续执行',
      },
      { item_id: 'item-02', expected_result: '结果二', approach_summary: '方法二', status: 'pending' },
    ],
  }]);

  assert.equal(summary.executionItemsProjectionValid, false);
  assert.equal(summary.executionItemTotal, 0);
  assert.deepEqual(summary.executionItemsInProgress, []);
  assert.deepEqual(summary.executionItemsActive, []);
  assert.equal(summary.executionItems?.some((item) => item.id.startsWith('execution-item-')), false);
});

test('a boundary-new WorkCase without the required profile cannot use legacy card fallbacks', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0102',
    object_id: 'workcase-0102',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    title: '拒绝错误兼容',
    path: 'ldvh-base/workcases/workcase-0102.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T10:00:00+08:00',
    updated: '2026-07-26T10:00:00+08:00',
    plan_version: 1,
    success_criteria: ['不应作为 legacy 成功标准显示'],
    work_items: [{ title: '不应补造身份', status: 'done' }],
  }]);

  assert.equal(summary.executionItemsProjectionValid, false);
  assert.equal(summary.executionItemTotal, 0);
  assert.deepEqual(summary.executionItems, []);
  assert.deepEqual(summary.executionItemsActive, []);
  assert.equal(summary.hasSuccessCriteria, false);
  assert.deepEqual(summary.successCriteria, []);
});

test('Web accepts v2 work items without approach summaries and rejects v1 objects after the v2 boundary', async () => {
  const common = {
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    path: 'ldvh-base/workcases/workcase-0110.yaml',
    created_at: '2026-07-26T12:45:00+08:00',
    updated_at: '2026-07-26T13:00:00+08:00',
    updated: '2026-07-26T13:00:00+08:00',
    plan_version: 1,
    success_criterion_definitions: [{ criterion_id: 'criterion-01', statement: '形成结果。' }],
    work_items: [{
      item_id: 'item-01', goal: '执行目标', expected_result: '执行结果', status: 'in_progress',
      current_summary: '执行中', resume_from: '继续执行',
    }],
  };
  const [v2, lateV1] = await buildWorkCaseSummaries([
    {
      ...common,
      id: 'workcase-0110', object_id: 'workcase-0110', title: 'V2 结构化对象',
      workcase_profile: 'control-contract-v2',
    },
    {
      ...common,
      id: 'workcase-0111', object_id: 'workcase-0111', title: '边界后 V1 对象',
      workcase_profile: 'control-contract-v1',
    },
  ]);

  assert.equal(v2.executionItemsProjectionValid, true);
  assert.deepEqual(v2.executionItemsActive?.map((item) => item.id), ['item-01']);
  assert.equal(v2.hasSuccessCriteria, true);
  assert.equal(lateV1.executionItemsProjectionValid, false);
  assert.deepEqual(lateV1.executionItemsActive, []);
  assert.equal(lateV1.hasSuccessCriteria, false);
});

test('closed current WorkCases recognize closure approval without inventing a request timestamp', async () => {
  const currentBase = {
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'closed',
    phase: 'closed',
    plan_version: 1,
    result_version: 1,
    execution_approval: {
      subject_version: 1,
      approved_at: '2026-07-26T13:05:00+08:00',
      summary: 'Human 已批准执行。',
    },
    success_criterion_definitions: [{ criterion_id: 'criterion-01', statement: '形成可观察结果。' }],
    success_criterion_results: [{ criterion_id: 'criterion-01', outcome: 'satisfied', summary: '标准已满足。' }],
    controller_check_summary: '主控自检完成。',
    validation_summary: '当前结果已经验证。',
    closure_outcome: 'completed',
    disposition_summary: '没有残余责任。',
    work_items: [{
      item_id: 'item-01', goal: '完成目标', expected_result: '形成结果', status: 'completed', result_summary: '已完成。',
    }],
  };
  const [v2, v1, missingApproval, legacyReviewRequested, legacyClosureRequested] = await buildWorkCaseSummaries([
    {
      ...currentBase,
      id: 'workcase-0120', object_id: 'workcase-0120', title: 'V2 已关闭对象',
      path: 'ldvh-base/workcases/workcase-0120.yaml',
      created_at: '2026-07-26T13:00:00+08:00', updated_at: '2026-07-26T14:00:00+08:00', updated: '2026-07-26T14:00:00+08:00',
      workcase_profile: 'control-contract-v2',
      closure_approval: {
        subject_version: 1,
        approved_at: '2026-07-26T14:00:00+08:00',
        summary: 'Human 已批准关闭。',
      },
    },
    {
      ...currentBase,
      id: 'workcase-0121', object_id: 'workcase-0121', title: 'V1 已关闭对象',
      path: 'ldvh-base/workcases/workcase-0121.yaml',
      created_at: '2026-07-25T08:00:00+08:00', updated_at: '2026-07-25T10:00:00+08:00', updated: '2026-07-25T10:00:00+08:00',
      workcase_profile: 'control-contract-v1',
      work_items: [{
        item_id: 'item-01', goal: '完成目标', expected_result: '形成结果', approach_summary: '按计划执行。',
        status: 'completed', result_summary: '已完成。',
      }],
      closure_approval: {
        subject_version: 1,
        approved_at: '2026-07-25T10:00:00+08:00',
        summary: 'Human 已批准关闭。',
      },
    },
    {
      ...currentBase,
      id: 'workcase-0122', object_id: 'workcase-0122', title: '缺少关闭批准的 V2 对象',
      path: 'ldvh-base/workcases/workcase-0122.yaml',
      created_at: '2026-07-26T13:00:00+08:00', updated_at: '2026-07-26T14:00:00+08:00', updated: '2026-07-26T14:00:00+08:00',
      workcase_profile: 'control-contract-v2',
    },
    {
      id: 'workcase-0123', object_id: 'workcase-0123', title: 'Legacy 已关闭对象',
      type: 'workcase', fact_type_key: 'workcase', status: 'closed', phase: 'closed',
      path: 'ldvh-base/workcases/workcase-0123.yaml',
      created_at: '2026-07-19T08:00:00+08:00', updated_at: '2026-07-19T10:00:00+08:00', updated: '2026-07-19T10:00:00+08:00',
      review_requested_at: '2026-07-19T09:00:00+08:00',
    },
    {
      id: 'workcase-0124', object_id: 'workcase-0124', title: 'Legacy 关闭请求对象',
      type: 'workcase', fact_type_key: 'workcase', status: 'closed', phase: 'closed',
      path: 'ldvh-base/workcases/workcase-0124.yaml',
      created_at: '2026-07-19T08:00:00+08:00', updated_at: '2026-07-19T10:00:00+08:00', updated: '2026-07-19T10:00:00+08:00',
      closure_requested_at: '2026-07-19T09:00:00+08:00',
    },
  ]);

  assert.equal(v2.hasClosureRequestedAt, true);
  assert.equal(v2.hasSuccessCriteria, true);
  assert.equal(v2.hasPlanConfirmedAt, true);
  assert.equal(v2.hasVerificationEvidence, true);
  assert.equal(v2.hasClosureEvidence, true);
  assert.equal(v1.hasClosureRequestedAt, true);
  assert.equal(missingApproval.hasClosureRequestedAt, false);
  assert.equal(legacyReviewRequested.hasClosureRequestedAt, true);
  assert.equal(legacyClosureRequested.hasClosureRequestedAt, true);
});

test('legacy WorkCase compatibility remains bounded for item identities and active states', async () => {
  const [legacy] = await buildWorkCaseSummaries([{
    id: 'workcase-0104',
    object_id: 'workcase-0104',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    title: '合法旧版兼容',
    path: 'ldvh-base/workcases/workcase-0104.yaml',
    created_at: '2026-07-19T08:00:00+08:00',
    updated_at: '2026-07-19T10:00:00+08:00',
    updated: '2026-07-19T10:00:00+08:00',
    plan_version: 1,
    success_criteria: ['旧版标准'],
    work_items: [
      { title: '旧版完成项', status: 'done' },
      { title: '旧版进行项', status: 'executing' },
      { title: '旧版阻塞项', status: 'blocked', blocking_summary: '旧版阻塞。' },
    ],
  }]);

  assert.equal(legacy.executionItemsProjectionValid, true);
  assert.deepEqual(legacy.executionItems?.map((item) => item.id), ['execution-item-2', 'execution-item-1', 'execution-item-3']);
  assert.equal(legacy.executionItemDone, 1);
  assert.deepEqual(legacy.executionItemsActive?.map((item) => item.id), ['execution-item-2', 'execution-item-3']);
});
