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

test('progressing cards fully show goal and one truthful four-step current-progress projection', () => {
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
  assert.match(branch, /progressHistoryCoverage=\{obj\.progressHistoryCoverage\}/);
  assert.match(branch, /progressRound=\{obj\.progressRound\}/);
  assert.match(branch, /executionItemDone=\{obj\.executionItemDone \?\? 0\}/);
  assert.match(branch, /executionItemCancelled=\{obj\.executionItemCancelled \?\? 0\}/);
  assert.match(branch, /executionItemsInProgress=\{obj\.executionItemsInProgress \?\? \[\]\}/);
  assert.match(branch, /isBlocked=\{obj\.responsibilityStatus === 'blocked'\}/);
  assert.match(branch, /blockingSummary=\{obj\.blocking_summary\}/);
  assert.match(branch, /prominentTitle/);
  assert.doesNotMatch(branch, /successCriteria|WorkCaseProgressSignal|WorkCaseCardSummary|ExecutionFlowBar|visibleExecutionItems/);

  const content = list.slice(list.indexOf('function WorkCaseProgressingContent'), list.indexOf('function WorkCaseProgressSignal'));
  assert.match(content, /<WorkCaseGoalSection goal=\{goal\}/);
  assert.match(content, /objectList\.workcaseCurrentProgress/);
  assert.match(content, /objectList\.workcaseRoundFull/);
  assert.match(content, /objectList\.workcaseRoundPartial/);
  assert.match(content, /objectList\.workcaseRoundMissing/);
  assert.match(content, /objectList\.workcaseItemProgress/);
  assert.match(content, /objectList\.workcaseItemsCancelled/);
  assert.match(content, /objectList\.workcaseCurrentItems/);
  assert.match(content, /executionItemsInProgress\.map/);
  assert.match(content, /\{item\.id\}/);
  assert.match(content, /formatReasonText\(item\.title\)/);
  assert.match(content, /<ol/);
  assert.match(content, /grid-cols-2/);
  assert.doesNotMatch(content, /sm:grid-cols-4/);
  assert.match(content, /WORKCASE_PROGRESS_STEP_ORDER\.map/);
  assert.match(content, /aria-current=\{isCurrent \? 'step'/);
  assert.match(content, /\{index \+ 1\}/);
  assert.match(content, /objectList\.workcaseBlockingReason/);
  assert.doesNotMatch(content, /isPast|CheckCircle2|successCriteria|ExecutionFlowBar|slice\(0,/);
  assert.doesNotMatch(content, /text-\[\d+px\]/);
  assert.match(locales, /'objectList\.workcaseCurrentProgress': '当前进展'/);
  assert.match(locales, /'objectList\.workcaseBlockingReason': '阻塞原因'/);
  assert.match(locales, /'objectList\.workcaseRoundPartial': '自记录起第 \{round\} 轮'/);
  assert.match(locales, /'objectList\.workcaseItemProgress': '已完成 \{done\}\/\{total\}'/);
});

test('WorkCase list projection preserves partial rounds and non-linear item progress', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0099',
    object_id: 'workcase-0099',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    phase: 'executing',
    title: '并行推进投影',
    path: 'ldvh-base/workcases/workcase-0099.yaml',
    created_at: '2026-07-25T12:00:00+08:00',
    updated_at: '2026-07-26T12:00:00+08:00',
    updated: '2026-07-26T12:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 2,
    result_version: 99,
    progress_history: {
      coverage: 'partial',
      entries: [
        {
          event_id: 'progress-001',
          plan_version: 2,
          round: 1,
          phase: 'executing',
          entered_at: '2026-07-26T08:00:00+08:00',
          transition_kind: 'baseline',
          transition_summary: '从当前可确认位置开始记录。',
        },
        {
          event_id: 'progress-002',
          plan_version: 2,
          round: 1,
          phase: 'controller_checking',
          entered_at: '2026-07-26T09:00:00+08:00',
          transition_kind: 'advanced',
          transition_summary: '进入主控自检。',
        },
        {
          event_id: 'progress-003',
          plan_version: 2,
          round: 2,
          phase: 'executing',
          entered_at: '2026-07-26T10:00:00+08:00',
          transition_kind: 'returned',
          transition_summary: '自检后返回执行修正。',
        },
        {
          event_id: 'progress-004',
          plan_version: 2,
          round: 3,
          phase: 'executing',
          entered_at: '2026-07-26T11:00:00+08:00',
          transition_kind: 'repeated',
          transition_summary: '执行环节开始新一轮修正。',
        },
      ],
    },
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
        item_id: 'item-04', goal: '并行当前项 B', expected_result: '形成结果 D', approach_summary: '执行 D',
        status: 'in_progress', current_summary: '正在执行 D', resume_from: '继续 D',
      },
    ],
  }]);

  assert.equal(summary.progressHistoryCoverage, 'partial');
  assert.equal(summary.progressHistoryState, 'valid');
  assert.equal(summary.progressRound, 3);
  assert.equal(summary.progressEventId, 'progress-004');
  assert.equal(summary.executionItemTotal, 4);
  assert.equal(summary.executionItemDone, 1);
  assert.equal(summary.executionItemCancelled, 1);
  assert.equal(summary.executionItemsProjectionValid, true);
  assert.deepEqual(summary.executionItemsInProgress?.map((item) => item.id), ['item-03', 'item-04']);
});

test('WorkCase list projection does not present a stale progress round as current', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0100',
    object_id: 'workcase-0100',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    phase: 'controller_checking',
    title: '不投影失配轮次',
    path: 'ldvh-base/workcases/workcase-0100.yaml',
    updated: '2026-07-26T13:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 1,
    progress_history: {
      coverage: 'full',
      entries: [{
        event_id: 'progress-001',
        plan_version: 1,
        round: 1,
        phase: 'executing',
      }],
    },
    work_items: [],
  }]);

  assert.equal(summary.progressHistoryCoverage, undefined);
  assert.equal(summary.progressHistoryState, 'invalid');
  assert.equal(summary.progressRound, undefined);
  assert.equal(summary.progressEventId, undefined);
});

test('current WorkCase item projection never invents missing IDs or goals', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0101',
    object_id: 'workcase-0101',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
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
  assert.equal(summary.executionItems?.some((item) => item.id.startsWith('execution-item-')), false);
});

test('a boundary-new WorkCase without the required profile cannot use legacy card fallbacks', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0102',
    object_id: 'workcase-0102',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
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
  assert.equal(summary.hasSuccessCriteria, false);
  assert.deepEqual(summary.successCriteria, []);
  assert.equal(summary.progressHistoryState, 'invalid');
});

test('a boundary-new current WorkCase in progress must not present absent history as legacy missing data', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0103',
    object_id: 'workcase-0103',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    phase: 'executing',
    title: '缺失必需推进历史',
    path: 'ldvh-base/workcases/workcase-0103.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T10:00:00+08:00',
    updated: '2026-07-26T10:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 1,
    work_items: [{
      item_id: 'item-01', goal: '执行目标', expected_result: '执行结果', approach_summary: '执行方法',
      status: 'in_progress', current_summary: '执行中', resume_from: '继续执行',
    }],
  }]);

  assert.equal(summary.progressHistoryState, 'invalid');
  assert.equal(summary.progressRound, undefined);
});

test('absence remains truthful before first execution and for pre-boundary current compatibility', async () => {
  const common = {
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    path: 'ldvh-base/workcases/workcase-0107.yaml',
    updated_at: '2026-07-26T10:00:00+08:00',
    updated: '2026-07-26T10:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 1,
    work_items: [{
      item_id: 'item-01', goal: '执行目标', expected_result: '执行结果', approach_summary: '执行方法',
      status: 'pending',
    }],
  };
  const [waiting, olderCurrent] = await buildWorkCaseSummaries([
    {
      ...common,
      id: 'workcase-0107',
      object_id: 'workcase-0107',
      title: '首次执行前不建空历史',
      phase: 'human_plan_confirming',
      created_at: '2026-07-26T08:00:00+08:00',
    },
    {
      ...common,
      id: 'workcase-0108',
      object_id: 'workcase-0108',
      title: '边界前 current 兼容缺失历史',
      phase: 'executing',
      created_at: '2026-07-24T08:00:00+08:00',
      work_items: [{
        item_id: 'item-01', goal: '执行目标', expected_result: '执行结果', approach_summary: '执行方法',
        status: 'in_progress', current_summary: '执行中', resume_from: '继续执行',
      }],
    },
  ]);

  assert.equal(waiting.progressHistoryState, 'missing');
  assert.equal(olderCurrent.progressHistoryState, 'missing');
});

test('legacy WorkCase compatibility remains bounded and rejects current-only progress history', async () => {
  const base = {
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    phase: 'executing',
    path: 'ldvh-base/workcases/workcase-0104.yaml',
    created_at: '2026-07-19T08:00:00+08:00',
    updated_at: '2026-07-19T10:00:00+08:00',
    updated: '2026-07-19T10:00:00+08:00',
    plan_version: 1,
    success_criteria: ['旧版标准'],
    work_items: [{ title: '旧版执行项', status: 'done' }],
  };
  const [legacy, forbiddenHistory] = await buildWorkCaseSummaries([
    { ...base, id: 'workcase-0104', object_id: 'workcase-0104', title: '合法旧版兼容' },
    {
      ...base,
      id: 'workcase-0105',
      object_id: 'workcase-0105',
      title: '旧版禁止推进历史',
      progress_history: {
        coverage: 'partial',
        entries: [{
          event_id: 'progress-001', plan_version: 1, round: 1, phase: 'executing',
          entered_at: '2026-07-19T09:00:00+08:00', transition_kind: 'baseline', transition_summary: '错误结构。',
        }],
      },
    },
  ]);

  assert.equal(legacy.executionItemsProjectionValid, true);
  assert.equal(legacy.executionItems?.[0].id, 'execution-item-1');
  assert.equal(legacy.executionItemDone, 1);
  assert.equal(legacy.progressHistoryState, 'missing');
  assert.equal(forbiddenHistory.progressHistoryState, 'invalid');
});

test('progress history timestamps require the same strict RFC 3339 lexical form as the fact validator', async () => {
  const [summary] = await buildWorkCaseSummaries([{
    id: 'workcase-0106',
    object_id: 'workcase-0106',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'progressing',
    phase: 'executing',
    title: '拒绝宽松时间解析',
    path: 'ldvh-base/workcases/workcase-0106.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T10:00:00+08:00',
    updated: '2026-07-26T10:00:00+08:00',
    workcase_profile: 'control-contract-v1',
    plan_version: 1,
    progress_history: {
      coverage: 'full',
      entries: [{
        event_id: 'progress-001', plan_version: 1, round: 1, phase: 'executing',
        entered_at: '2026-07-26 09:00:00+08:00', transition_kind: 'started', transition_summary: '错误时间格式。',
      }],
    },
    work_items: [{
      item_id: 'item-01', goal: '执行目标', expected_result: '执行结果', approach_summary: '执行方法',
      status: 'in_progress', current_summary: '执行中', resume_from: '继续执行',
    }],
  }]);

  assert.equal(summary.progressHistoryState, 'invalid');
  assert.equal(summary.progressRound, undefined);
});
