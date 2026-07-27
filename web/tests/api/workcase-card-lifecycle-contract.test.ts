import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import {
  WORKCASE_CURRENT_PHASES,
  WORKCASE_PROGRESS_GROUP_ORDER,
  WORKCASE_PROGRESS_STEP_ORDER,
  deriveWorkCaseProgressProjection,
  getWorkCaseProgressProjection,
} from '../../shared/workcaseStatus.ts';
import { projectWorkCaseCard } from '../../api/services/facts.ts';

const webRoot = path.resolve(import.meta.dirname, '../..');

function source(relativePath: string): string {
  return fs.readFileSync(path.join(webRoot, relativePath), 'utf8');
}

function currentWorkCase(overrides: Record<string, unknown> = {}) {
  return {
    id: 'workcase-0099',
    object_id: 'workcase-0099',
    type: 'workcase',
    fact_type_key: 'workcase',
    status: 'open',
    phase: 'executing',
    progress_group: 'progressing',
    progress_step: 'item_execution',
    title: '当前 WorkCase 投影',
    path: 'ldvh-base/workcases/workcase-0099.yaml',
    created_at: '2026-07-26T08:00:00+08:00',
    updated_at: '2026-07-26T12:00:00+08:00',
    updated: '2026-07-26T12:00:00+08:00',
    goal: '只消费当前字段。',
    scope: '只测试当前 Card 投影。',
    success_criterion_definitions: [
      { criterion_id: 'criterion-visible-result', statement: '完整显示当前成功标准。' },
    ],
    plan_version: 1,
    work_items: [
      {
        item_id: 'item-done',
        goal: '保留已完成项',
        expected_result: '形成已完成结果',
        status: 'completed',
        result_summary: '已形成结果。',
      },
      {
        item_id: 'item-running',
        goal: '继续当前推进',
        expected_result: '形成当前结果',
        status: 'in_progress',
        current_summary: '已完成基础修改。',
        resume_from: '继续运行当前验证。',
        depends_on: ['item-done'],
      },
      {
        item_id: 'item-blocked',
        goal: '等待外部输入',
        expected_result: '取得外部输入',
        status: 'blocked',
        current_summary: '输入尚未取得。',
        blocking_summary: '等待 Human 提供输入。',
        depends_on: ['item-done'],
      },
      {
        item_id: 'item-cancelled',
        goal: '停止不再适用的局部工作',
        expected_result: '清楚记录停止范围',
        status: 'cancelled',
        result_summary: '该局部工作已经停止。',
      },
    ],
    ...overrides,
  };
}

test('WorkCase cards use four progress groups over the single current phase set', () => {
  assert.deepEqual(WORKCASE_PROGRESS_GROUP_ORDER, ['plan_confirmation', 'progressing', 'closure_confirmation', 'closed']);
  assert.deepEqual(WORKCASE_PROGRESS_STEP_ORDER, ['item_execution', 'controller_self_check', 'independent_review', 'controller_synthesis']);
  assert.deepEqual(WORKCASE_CURRENT_PHASES, [
    'human_plan_confirming',
    'plan_revising',
    'executing',
    'controller_checking',
    'independent_reviewing',
    'closure_preparing',
    'human_closure_confirming',
  ]);
  assert.deepEqual(getWorkCaseProgressProjection('closure_preparing'), {
    progressGroup: 'progressing',
    progressStep: 'controller_synthesis',
  });
  assert.equal(getWorkCaseProgressProjection('human_closure_confirming')?.progressGroup, 'closure_confirmation');
  assert.equal(getWorkCaseProgressProjection('closed'), null);
  assert.deepEqual(deriveWorkCaseProgressProjection('closed', undefined), { progressGroup: 'closed' });
  assert.equal(deriveWorkCaseProgressProjection('closed', 'executing'), null);
  assert.equal(deriveWorkCaseProgressProjection('open', undefined), null);
  assert.equal(deriveWorkCaseProgressProjection('blocked', 'not-a-current-phase'), null);
  assert.deepEqual(deriveWorkCaseProgressProjection('open', 'executing'), {
    progressGroup: 'progressing',
    progressStep: 'item_execution',
  });
});

test('plan revision is progressing but remains outside the four-step track', () => {
  const list = source('src/pages/ObjectList.tsx');
  const locales = source('src/i18n/locales.ts');

  assert.deepEqual(getWorkCaseProgressProjection('plan_revising'), { progressGroup: 'progressing' });
  assert.equal(getWorkCaseProgressProjection('plan_revising')?.progressStep, undefined);
  assert.match(list, /const planRevising = phase === 'plan_revising'/);
  assert.match(list, /objectList\.workcasePlanRevising/);
  assert.match(list, /objectList\.workcaseOutsideProgressTrack/);
  assert.match(list, /\{!planRevising && \(/);
  assert.match(locales, /plan_revising: \{ zh: '方案修订中'/);
  assert.match(locales, /'objectList\.workcaseOutsideProgressTrack': '四步轨迹之外'/);
});

test('plan confirmation keeps goal and criteria as the only plan-decision inputs', () => {
  const list = source('src/pages/ObjectList.tsx');
  const branchStart = list.indexOf("if (progressGroup === 'plan_confirmation')");
  const branchEnd = list.indexOf("if (progressGroup === 'progressing')", branchStart);
  const branch = list.slice(branchStart, branchEnd);
  const contentStart = list.indexOf('function WorkCasePlanConfirmationContent');
  const contentEnd = list.indexOf('function WorkCaseGoalSection', contentStart);
  const content = list.slice(contentStart, contentEnd);
  const noticeStart = list.indexOf('function WorkCaseBlockingNotice');
  const noticeEnd = list.indexOf('function WorkCaseProgressingContent', noticeStart);
  const notice = list.slice(noticeStart, noticeEnd);

  assert.ok(branchStart >= 0 && branchEnd > branchStart);
  assert.ok(contentStart >= 0 && contentEnd > contentStart);
  assert.ok(noticeStart >= 0 && noticeEnd > noticeStart);
  assert.match(branch, /<WorkCasePlanConfirmationContent goal=\{obj\.goal\} successCriteria=\{obj\.successCriteria\}/);
  assert.match(branch, /prominentTitle/);
  assert.doesNotMatch(branch, /executionItem|waiting_on/);
  assert.match(branch, /obj\.status === 'blocked'/);
  assert.match(branch, /WorkCaseBlockingNotice blockingSummary=\{obj\.blocking_summary\}/);
  assert.ok(branch.indexOf('<WorkCasePlanConfirmationContent') < branch.indexOf("obj.status === 'blocked'"));
  assert.ok(branch.indexOf("obj.status === 'blocked'") < branch.indexOf('<WorkCaseBlockingNotice'));
  assert.match(content, /ldvh-card-title/);
  assert.match(content, /ldvh-caption/);
  assert.match(content, /className="text-xs leading-5 text-ldvh-text-secondary"/);
  assert.match(content, /flex h-5 w-2 shrink-0 items-center justify-center/);
  assert.match(content, /h-1\.5 w-1\.5 rounded-full bg-ldvh-text-secondary\/60/);
  assert.doesNotMatch(content, /list-disc/);
  assert.doesNotMatch(content, /<ol|line-clamp|slice\(0,|scope|blockingSummary|BlockingNotice/);
  assert.match(notice, /role="status"/);
  assert.match(notice, /aria-label=\{t\('objectList\.workcaseBlockingReason'\)\}/);
});

test('progressing cards show only goal and current progress facts', () => {
  const list = source('src/pages/ObjectList.tsx');
  const branchStart = list.indexOf("if (progressGroup === 'progressing')");
  const terminalStatus = list.indexOf("displayStatus={progressGroup ?? 'unknown'}", branchStart);
  const branchEnd = list.lastIndexOf('      return (', terminalStatus);
  const branch = list.slice(branchStart, branchEnd);
  const content = list.slice(list.indexOf('function WorkCaseProgressingContent'), list.indexOf('function sortObjectsForList'));

  assert.ok(branchStart >= 0 && branchEnd > branchStart);
  assert.match(branch, /<WorkCaseProgressingContent/);
  assert.match(branch, /goal=\{obj\.goal\}/);
  assert.match(branch, /phase=\{obj\.phase\}/);
  assert.match(branch, /executionItemsActive=\{obj\.executionItemsActive \?\? \[\]\}/);
  assert.match(branch, /waitingOn=\{obj\.waiting_on\}/);
  assert.match(branch, /blockingSummary=\{obj\.blocking_summary\}/);
  assert.doesNotMatch(branch, /successCriteria|closure|approval/);
  assert.match(content, /objectList\.workcaseItemProgress/);
  assert.match(content, /executionItemsActive\.map/);
  assert.match(content, /objectList\.workcaseWaitingOn/);
  assert.match(content, /<WorkCaseBlockingNotice blockingSummary=\{blockingSummary\}/);
  assert.doesNotMatch(content, /progressHistory|roundLabel|workcaseRound/);
});

test('list ordering follows updated time and never groups WorkCases by progress position', () => {
  const list = source('src/pages/ObjectList.tsx');
  const start = list.indexOf('function sortObjectsForList');
  const end = list.indexOf('function sparkViewItem', start);
  const sorting = list.slice(start, end);

  assert.ok(start >= 0 && end > start);
  assert.match(sorting, /Date\.parse\(b\.updated/);
  assert.match(sorting, /a\.id\.localeCompare\(b\.id\)/);
  assert.doesNotMatch(sorting, /progress_group|progress_step|PROGRESS_GROUP_INDEX|PROGRESS_STEP_INDEX/);
});

test('closure confirmation and closed cards keep only the common identity and progress group', () => {
  const list = source('src/pages/ObjectList.tsx');
  const terminalStatus = list.indexOf("displayStatus={progressGroup ?? 'unknown'}");
  const progressingEnd = list.lastIndexOf('      return (', terminalStatus);
  const adrStart = list.indexOf("if (currentType === 'adr')");
  const terminalBranch = list.slice(progressingEnd, adrStart);

  assert.match(terminalBranch, /<ObjectCardFrame/);
  assert.match(terminalBranch, /displayStatus=\{progressGroup \?\? 'unknown'\}/);
  assert.match(terminalBranch, /workcaseProgressGroupUnavailable/);
  assert.doesNotMatch(terminalBranch, /executionItems|successCriteria|CloseDecision|RecordItem|Integrity|Evidence|BlockingNotice|blocking_summary/);
  assert.doesNotMatch(list, /hasClosureRequestedAt|hasClosureEvidence|hasClosedIntegrityIssue|WorkCaseRecordItem/);
});

test('closure confirmation and closed public Card projections contain no blocked or detail body', () => {
  const closure = projectWorkCaseCard({
    object_id: 'workcase-0100',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'blocked',
    phase: 'human_closure_confirming',
    priority: 'P0',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '不得进入关闭确认 Card 正文',
    blocking_summary: '详情仍应保留的阻塞事实',
    success_criterion_definitions: [{ criterion_id: 'criterion-hidden', statement: '不得透传' }],
    work_items: [{ item_id: 'item-hidden', goal: '不得透传', status: 'completed' }],
  });
  const closed = projectWorkCaseCard({
    object_id: 'workcase-0101',
    fact_type_key: 'workcase',
    title: '已经关闭',
    status: 'closed',
    priority: 'P0',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '不得进入已关闭 Card 正文',
    disposition_summary: '仅详情可读',
  });

  assert.deepEqual(Object.keys(closure).sort(), [
    'fact_type_key', 'object_id', 'phase', 'status', 'title', 'updated_at',
  ]);
  assert.deepEqual(Object.keys(closed).sort(), [
    'fact_type_key', 'object_id', 'status', 'title', 'updated_at',
  ]);
});

test('current list projection preserves real item identities, statuses, and active members', () => {
  const summary = projectWorkCaseCard(currentWorkCase());

  assert.equal(summary.executionItemsProjectionValid, true);
  assert.equal(summary.executionItemTotal, 4);
  assert.equal(summary.executionItemDone, 1);
  assert.equal(summary.executionItemCancelled, 1);
  assert.equal(summary.executionItemOpen, 2);
  const active = summary.executionItemsActive as Array<Record<string, unknown>>;
  assert.deepEqual(active.map((item) => item.id), ['item-running', 'item-blocked']);
  assert.equal(active[1]?.blockingReason, '等待 Human 提供输入。');
  assert.equal('successCriteria' in summary, false);
});

test('public progressing projection keeps counts and active items without the complete item plan', () => {
  const facts = source('api/services/facts.ts');
  const projectionStart = facts.indexOf('export function projectWorkCaseCard');
  const projectionEnd = facts.indexOf('export async function listObjects', projectionStart);
  const publicProjection = facts.slice(projectionStart, projectionEnd);

  assert.ok(projectionStart >= 0 && projectionEnd > projectionStart);
  assert.match(publicProjection, /projectCardWorkItems\(fact\.work_items\)/);
  assert.doesNotMatch(publicProjection, /projected\.work_items|projected\.executionItems/);
});

test('public active-item projection exposes only fields consumed by the Card', () => {
  const projected = projectWorkCaseCard(currentWorkCase());
  const active = projected.executionItemsActive as Array<Record<string, unknown>>;

  assert.deepEqual(Object.keys(active[0] ?? {}).sort(), ['id', 'status', 'title']);
  assert.deepEqual(Object.keys(active[1] ?? {}).sort(), ['blockingReason', 'id', 'status', 'title']);
});

test('malformed current items and criteria become unavailable without generated replacements', () => {
  const summary = projectWorkCaseCard(currentWorkCase({
    success_criterion_definitions: [{ criterion_id: 'criterion-visible-result' }],
    success_criteria: ['不得读取的已退出标准'],
    work_items: [
      {
        goal: '缺少稳定 item_id',
        expected_result: '不应形成投影',
        status: 'in_progress',
        current_summary: '正在执行。',
        resume_from: '继续执行。',
      },
    ],
  }));

  assert.equal(summary.executionItemsProjectionValid, false);
  assert.equal(summary.executionItemTotal, 0);
  assert.deepEqual(summary.executionItemsActive, []);
  assert.equal('successCriteria' in summary, false);
});

test('closed summaries do not reconstruct removed process fields or completeness diagnostics', () => {
  const summary = projectWorkCaseCard(currentWorkCase({
    status: 'closed',
    phase: undefined,
    progress_group: 'closed',
    progress_step: undefined,
    priority: undefined,
    plan_version: undefined,
    work_items: undefined,
    closure_outcome: 'completed',
    disposition_summary: '责任已经关闭。',
  }));

  assert.equal('executionItemsProjectionValid' in summary, false);
  assert.equal('executionItems' in summary, false);
  assert.equal('hasClosureRequestedAt' in summary, false);
  assert.equal('hasPlanConfirmedAt' in summary, false);
  assert.equal('hasVerificationEvidence' in summary, false);
  assert.equal('hasClosureEvidence' in summary, false);
  assert.equal('successCriteria' in summary, false);
});

test('plan confirmation projection preserves every criterion statement without truncation', () => {
  const summary = projectWorkCaseCard(currentWorkCase({
    phase: 'human_plan_confirming',
    progress_group: 'plan_confirmation',
    progress_step: undefined,
  }));

  assert.deepEqual(summary.successCriteria, ['完整显示当前成功标准。']);
  assert.equal('executionItems' in summary, false);
});

test('blocked plan confirmation projects a separate complete state-alert fact', () => {
  const summary = projectWorkCaseCard(currentWorkCase({
    status: 'blocked',
    phase: 'human_plan_confirming',
    progress_group: 'plan_confirmation',
    progress_step: undefined,
    blocking_summary: '等待 Human 明确当前计划边界。',
  }));

  assert.equal(summary.goal, '只消费当前字段。');
  assert.deepEqual(summary.successCriteria, ['完整显示当前成功标准。']);
  assert.equal(summary.blocking_summary, '等待 Human 明确当前计划边界。');
  assert.equal('executionItems' in summary, false);
  assert.equal('waiting_on' in summary, false);
});

test('WorkCase list code has no profile, date-boundary, or historical item projection path', () => {
  const route = source('api/routes/objects.ts');
  const shared = source('shared/workcaseStatus.ts');

  assert.doesNotMatch(route, /WorkCaseProfileKind|WORKCASE_CURRENT_BOUNDARY|WORKCASE_V2_BOUNDARY|workcase_profile/);
  assert.doesNotMatch(route, /parseStrictRfc3339|execution-item-|orchestration\.execution_items/);
  assert.doesNotMatch(route, /closure_requested_at|review_requested_at|closure_approval/);
  assert.doesNotMatch(route, /hasClosureRequestedAt|hasPlanConfirmedAt|hasVerificationEvidence|hasClosureEvidence/);
  assert.doesNotMatch(shared, /result_self_checking|subagents_result_reviewing|review_needed|draft|active/);
});

test('detail copy actions never fall back from an exact canonical path to a list or route path', () => {
  const detail = source('src/pages/ObjectDetail.tsx');

  assert.doesNotMatch(detail, /canonical_path\s*\?\?\s*(?:obj\.)?path/);
  assert.doesNotMatch(detail, /CopyPathButton path=\{item\?\.path\}/);
  assert.doesNotMatch(detail, /function DetailObjectRow|function buildCurrentFlowItem/);
});

test('WorkCase list does not expose list-level observation or reread controls', () => {
  const list = source('src/pages/ObjectList.tsx');

  assert.doesNotMatch(list, /WorkCaseObservationControls|coverageObservedAt|reloadVersion|setReloadVersion|RefreshCw/);
  assert.match(list, /currentType === 'workcase' \? \(/);
});

test('WorkCase list reports field-level issues without restoring the V4 machine transport', () => {
  const facts = source('api/services/facts.ts');
  const listStart = facts.indexOf('export async function listObjects');
  const listEnd = facts.indexOf('export async function showObject', listStart);
  const diagnostics = facts.slice(listStart, listEnd);
  const list = source('src/pages/ObjectList.tsx');

  assert.ok(listStart >= 0 && listEnd > listStart);
  assert.match(diagnostics, /item\.field_issues/);
  assert.doesNotMatch(facts, /v4FactReader|v4FactsTransport|machine\.py/);
  assert.match(list, /workcaseProgressGroupUnavailable/);
});
