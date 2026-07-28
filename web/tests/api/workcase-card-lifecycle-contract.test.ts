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
import { getObjectStatusLocale } from '../../src/i18n/locales.ts';

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

test('Pitfall lifecycle labels remain type-specific across all four states', () => {
  assert.equal(getObjectStatusLocale('pitfall', 'draft', 'zh'), '待确认');
  assert.equal(getObjectStatusLocale('pitfall', 'active', 'zh'), '已确认');
  assert.equal(getObjectStatusLocale('pitfall', 'discarded', 'zh'), '已废弃');
  assert.equal(getObjectStatusLocale('pitfall', 'retired', 'zh'), '已退出');
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
  assert.match(content, /className="text-\[13px\] leading-5 text-blue-700\/80 dark:text-blue-200\/80"/);
  assert.match(content, /mt-2 h-1 w-1 shrink-0 rounded-full bg-blue-400\/70 dark:bg-blue-400\/80/);
  assert.doesNotMatch(content, /list-disc/);
  assert.doesNotMatch(content, /<ol|line-clamp|slice\(0,|scope|blockingSummary|BlockingNotice/);
  assert.match(notice, /role="status"/);
  assert.match(notice, /aria-label=\{t\('objectList\.workcaseBlockingReason'\)\}/);
  assert.match(notice, /border-l-2 border-l-amber-400 bg-amber-500\/5/);
  assert.match(notice, /flex min-w-0 items-center gap-2/);
});

test('semantic WorkCase cards share one title-to-body spacing token', () => {
  const list = source('src/pages/ObjectList.tsx');
  const goal = list.slice(list.indexOf('function WorkCaseGoalSection'), list.indexOf('function WorkCaseBlockingNotice'));
  const outcome = list.slice(list.indexOf('function WorkCaseOutcomeNotice'), list.indexOf('function WorkCaseSparkSuggestions'));
  const suggestions = list.slice(list.indexOf('function WorkCaseSparkSuggestions'), list.indexOf('function WorkCaseClosureConfirmationContent'));
  const closure = list.slice(list.indexOf('function WorkCaseClosureConfirmationContent'), list.indexOf('function WorkCaseContributionsContent'));
  const closed = list.slice(list.indexOf('function WorkCaseClosedContent'), list.indexOf('function WorkCaseContributionsContent'));

  assert.match(list, /const WORKCASE_CARD_TITLE_BODY_GAP_CLASS = 'mt-1\.5'/);
  for (const section of [goal, outcome, suggestions, closure, closed]) {
    assert.match(section, /WORKCASE_CARD_TITLE_BODY_GAP_CLASS/);
  }
  assert.match(closure, /showStatus=\{false\} compact/);
  assert.match(closed, /showStatus=\{false\} compact/);
});

test('Only Card titles navigate; routed targets remain plain relationship facts', () => {
  const list = source('src/pages/ObjectList.tsx');
  const target = list.slice(list.indexOf('function WorkCaseContributionTargetRow'), list.indexOf('function contributionTargetTitle'));
  const frame = list.slice(list.indexOf('function ObjectCardFrame'), list.indexOf('function hasSparkResolvedFact'));

  assert.match(target, /<ObjectTypeIcon type=\{target\.factTypeKey\}/);
  assert.match(target, /flex min-w-0 items-center gap-2/);
  assert.match(target, /size=\{13\} className="-translate-y-0\.5 shrink-0"/);
  assert.match(target, /<span className="ldvh-meta-primary min-w-0 flex-1 whitespace-normal break-words text-left">[\s\S]*\{title\}/);
  assert.match(target, /\{target\.objectId\}/);
  assert.doesNotMatch(target, /role="button"|tabIndex=\{0\}|onKeyDown|onClick=\{open\}|<button/);
  assert.match(frame, /<button[\s\S]*onClick=\{\(\) => onOpen\(obj\.id\)\}[\s\S]*getLocalizedObjectTitle/);
  assert.doesNotMatch(frame, /role="button"|tabIndex=\{0\}|onClick=\{\(\) => onOpen\(obj\.id\)\}\n\s*onKeyDown/);
  assert.doesNotMatch(frame, /<ArrowRight size=\{14\}/);
});

test('progressing cards show only goal and current progress facts', () => {
  const list = source('src/pages/ObjectList.tsx');
  const branchStart = list.indexOf("if (progressGroup === 'progressing')");
  const branchEnd = list.indexOf("if (progressGroup === 'closure_confirmation')", branchStart);
  const branch = list.slice(branchStart, branchEnd);
  const content = list.slice(list.indexOf('function WorkCaseProgressingContent'), list.indexOf('function sortObjectsForList'));

  assert.ok(branchStart >= 0 && branchEnd > branchStart);
  assert.match(branch, /<WorkCaseProgressingContent/);
  assert.match(branch, /goal=\{obj\.goal\}/);
  assert.match(branch, /phase=\{obj\.phase\}/);
  assert.match(branch, /executionItems=\{obj\.executionItems \?\? \[\]\}/);
  assert.match(branch, /waitingOn=\{obj\.waiting_on\}/);
  assert.match(branch, /blockingSummary=\{obj\.blocking_summary\}/);
  assert.doesNotMatch(branch, /successCriteria|closure|approval/);
  assert.match(content, /<h3 className="ldvh-card-title text-sky-700 dark:text-sky-200">\{t\('objectList\.workcaseCurrentProgress'\)\}<\/h3>/);
  assert.doesNotMatch(content, /currentExecutionPosition|currentExecutionItem|workcaseItemProgress/);
  assert.match(content, /const displayedExecutionItems = itemExecution/);
  assert.match(content, /completed: 0, in_progress: 1, blocked: 2, pending: 3, cancelled: 4/);
  assert.match(content, /displayedExecutionItems\.map/);
  assert.match(content, /<CircleCheck size=\{14\}/);
  assert.match(content, /<CirclePlay size=\{14\}/);
  assert.match(content, /<CircleAlert size=\{14\}/);
  assert.match(content, /<CircleMinus size=\{14\}/);
  assert.match(content, /<Circle size=\{14\}/);
  assert.match(content, /flex min-w-0 items-center gap-2/);
  assert.match(content, /<div className="mt-0\.5">/);
  assert.match(content, /\[&_p\]:my-0 text-\[13px\] leading-5/);
  assert.match(content, /bg-emerald-500\/5/);
  assert.match(content, /bg-ldvh-bg\/60/);
  assert.match(content, /top-2\.5 z-0 h-px bg-ldvh-border/);
  assert.match(content, /bg-sky-100 font-semibold text-sky-600/);
  assert.match(content, /text-sky-700 dark:text-sky-200/);
  assert.match(content, /text-sky-600\/70 dark:text-sky-300\/70/);
  assert.match(content, /text-emerald-700 dark:text-emerald-200/);
  assert.match(content, /text-slate-600 dark:text-slate-300/);
  assert.doesNotMatch(content, /grid-cols-\[1rem_minmax\(0,1fr\)\]/);
  assert.doesNotMatch(content, /workcaseItemCompleted|workcaseItemInProgress|workcaseItemBlocked|workcaseItemPending|workcaseItemCancelled/);
  assert.match(content, /objectList\.workcaseWaitingOn/);
  assert.match(content, /border-l-2 border-l-ldvh-text-secondary\/35 bg-ldvh-bg\/60/);
  assert.match(content, /\[&_p\]:my-0 text-\[13px\] leading-5 text-slate-600/);
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

test('closure confirmation cards render the closure-decision input zone and declared contributed-to targets', () => {
  const list = source('src/pages/ObjectList.tsx');
  const branchStart = list.indexOf("if (progressGroup === 'closure_confirmation')");
  const terminalStatus = list.indexOf("displayStatus={progressGroup ?? 'unknown'}", branchStart);
  const branchEnd = list.lastIndexOf('      return (', terminalStatus);
  const branch = list.slice(branchStart, branchEnd);
  const content = list.slice(list.indexOf('function WorkCaseClosureConfirmationContent'), list.indexOf('function WorkCaseContributionsContent'));
  const contributions = list.slice(list.indexOf('function WorkCaseContributionsContent'), list.indexOf('function sortObjectsForList'));

  assert.ok(branchStart >= 0 && branchEnd > branchStart);
  assert.match(branch, /displayStatus=\{progressGroup\}/);
  assert.match(branch, /prominentTitle/);
  assert.match(branch, /<WorkCaseClosureConfirmationContent goal=\{obj\.goal\} closureProposal=\{obj\.closureProposal\} \/>/);
  assert.match(branch, /<WorkCaseContributionsContent contributions=\{obj\.contributedTo\} locale=\{locale\} \/>/);
  assert.ok(branch.indexOf('<WorkCaseClosureConfirmationContent') < branch.indexOf('<WorkCaseContributionsContent'));
  assert.doesNotMatch(branch, /executionItems|successCriteria|blocking_summary/);

  assert.match(content, /<WorkCaseGoalSection goal=\{goal\} t=\{t\} \/>/);
  assert.match(content, /closureProposal \? \(/);
  assert.match(content, /<WorkCaseOutcomeNotice outcome=\{closureProposal\.proposedOutcome\} dispositionSummary=\{closureProposal\.dispositionSummary\} \/>/);
  assert.match(content, /closureProposal\.residualDecisions\.map/);
  assert.match(content, /getFieldValueLabel\('proposed_disposition', decision\.proposedDisposition, locale\)/);
  assert.match(content, /objectList\.workcaseClosureProposalMissing/);
  assert.match(content, /WorkCaseSparkSuggestions suggestions=\{closureProposal\.sparkSuggestions\}/);
  assert.match(list, /PROPOSED_OUTCOME_NOTICE_CLASS\[outcome\]/);
  assert.match(content, /PROPOSED_DISPOSITION_NOTICE_CLASS\[decision\.proposedDisposition\]/);
  assert.match(content, /rounded-md border border-l-2 px-3\.5 py-3/);
  assert.match(list, /function WorkCaseSparkSuggestions/);
  assert.match(list, /const WORKCASE_SECTION_ICON_SIZE = 16/);
  assert.match(content, /Lightbulb size=\{WORKCASE_SECTION_ICON_SIZE\}/);
  assert.match(content, /ArrowRight size=\{WORKCASE_SECTION_ICON_SIZE\}/);
  assert.match(list, /function QuarterCircle/);
  assert.match(list, /<QuarterCircle className="shrink-0 text-amber-500/);
  assert.match(content, /decision\.proposedDisposition === 'accept_stop'/);
  assert.match(list, /ldvh-card-title min-w-0 \$\{tone\}/);
  assert.match(content, /ldvh-card-title min-w-0 \$\{PROPOSED_DISPOSITION_TEXT_CLASS/);
  assert.match(content, /decision\.routeTarget/);
  assert.doesNotMatch(content, /<ol|successCriterionResults|controller_check|validation_summary/);

  assert.match(contributions, /if \(!contributions \|\| contributions\.length === 0\) return null;/);
  assert.match(contributions, /objectList\.workcaseContributions/);
  assert.match(contributions, /fetchObjectDetail\(target\.factTypeKey, target\.objectId\)/);
  assert.match(contributions, /<ObjectTypeIcon type=\{target\.factTypeKey\}/);
  assert.match(contributions, /\{target\.objectId\}/);
  assert.doesNotMatch(contributions, /getTypeLabel\(target\.factTypeKey, locale\)/);
  assert.match(contributions, /if \(!detail \|\| !isReadableFact\(readMeta\)\) return '—';/);
  assert.match(contributions, /objectList\.workcaseTargetReading/);
  assert.match(contributions, /getFieldValueLabel\('read_status', readMeta\.readStatus \?\? 'unreadable', locale\)/);
  assert.match(contributions, /whitespace-normal break-words/);
  assert.doesNotMatch(contributions, /flex-1 truncate/);
});

test('closed cards use terminal closure content while unclassified cards stay minimal', () => {
  const list = source('src/pages/ObjectList.tsx');
  const closedContent = list.slice(list.indexOf('function WorkCaseClosedContent'), list.indexOf('function WorkCaseContributionsContent'));
  const terminalStatus = list.indexOf("displayStatus={progressGroup ?? 'unknown'}");
  const progressingEnd = list.lastIndexOf('      return (', terminalStatus);
  const adrStart = list.indexOf("if (currentType === 'adr')");
  const terminalBranch = list.slice(progressingEnd, adrStart);

  assert.match(terminalBranch, /<ObjectCardFrame/);
  assert.match(terminalBranch, /displayStatus=\{progressGroup \?\? 'unknown'\}/);
  assert.match(terminalBranch, /workcaseProgressGroupUnavailable/);
  assert.match(list, /<WorkCaseClosedContent goal=\{obj\.goal\} terminal=\{obj\.closureTerminal\} \/>/);
  assert.match(list, /<WorkCaseContributionsContent contributions=\{obj\.contributedTo\}/);
  assert.match(list, /getFieldValueLabel\('proposed_disposition', 'route_existing', locale\)/);
  assert.match(list, /getFieldValueLabel\('proposed_disposition', 'suggest_spark', locale\)/);
  assert.match(closedContent, /<WorkCaseOutcomeNotice outcome=\{terminal\.outcome\} dispositionSummary=\{terminal\.dispositionSummary\} \/>/);
  assert.match(closedContent, /terminal\.routedTo\.map/);
  assert.match(closedContent, /terminal\.acceptedStop\.map/);
  assert.match(closedContent, /<WorkCaseSparkSuggestions suggestions=\{terminal\.sparkSuggestions\} \/>/);
  assert.match(closedContent, /CircleMinus size=\{WORKCASE_SECTION_ICON_SIZE\}/);
  assert.match(closedContent, /ArrowRight size=\{WORKCASE_SECTION_ICON_SIZE\}/);
  assert.doesNotMatch(closedContent, /border-t border-ldvh-border\/45/);
  assert.doesNotMatch(terminalBranch, /executionItems|successCriteria|RecordItem|Integrity|Evidence|BlockingNotice|blocking_summary/);
  assert.doesNotMatch(list, /hasClosureRequestedAt|hasClosureEvidence|hasClosedIntegrityIssue|WorkCaseRecordItem/);
});

test('closure confirmation and closed public Card projections carry goal but no blocked notice or detail body', () => {
  const closure = projectWorkCaseCard({
    object_id: 'workcase-0100',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'blocked',
    phase: 'human_closure_confirming',
    priority: 'P0',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '关闭 Card 正文可读的目标',
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
    goal: '进入已关闭 Card 正文的目标',
    closure_outcome: 'completed',
    disposition_summary: '当前责任已经完成。',
  });

  assert.deepEqual(Object.keys(closure).sort(), [
    'fact_type_key', 'goal', 'object_id', 'phase', 'status', 'title', 'updated_at',
  ]);
  assert.equal(closure.goal, '关闭 Card 正文可读的目标');
  assert.equal('blocking_summary' in closure, false);
  assert.equal('closureProposal' in closure, false);
  assert.equal('successCriteria' in closure, false);
  assert.equal('executionItemsActive' in closure, false);
  assert.equal('contributedTo' in closure, false);
  assert.deepEqual(Object.keys(closed).sort(), [
    'closureTerminal', 'fact_type_key', 'goal', 'object_id', 'status', 'title', 'updated_at',
  ]);
  assert.equal(closed.goal, '进入已关闭 Card 正文的目标');
  assert.equal('contributedTo' in closed, false);
});

test('closure confirmation projects a stable closure-proposal subset only when well-formed', () => {
  const valid = projectWorkCaseCard({
    object_id: 'workcase-0110',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '完成当前责任。',
    closure_proposal: {
      proposed_outcome: 'partial',
      proposed_disposition_summary: '接受部分完成并分流剩余责任。',
      residual_decisions: [
        { residual_id: 'residual-a', summary: '后续验证', proposed_disposition: 'route_existing', route_target: { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0111', content_fingerprint: 'a'.repeat(64) } },
        { residual_id: 'residual-b', summary: '放弃试验分支', proposed_disposition: 'accept_stop' },
      ],
      spark_suggestions: [{ suggestion_id: 'suggestion-next', suggestion_kind: 'follow_up_opportunity', summary: '保留后续机会', follow_up_summary: '由 Human 日后判断是否建立 Spark。' }],
    },
  });

  assert.equal(valid.goal, '完成当前责任。');
  assert.deepEqual(valid.closureProposal, {
    proposedOutcome: 'partial',
    dispositionSummary: '接受部分完成并分流剩余责任。',
    residualDecisions: [
      { residualId: 'residual-a', summary: '后续验证', proposedDisposition: 'route_existing', routeTarget: { governedProjectId: 'sample', factTypeKey: 'workcase', objectId: 'workcase-0111' } },
      { residualId: 'residual-b', summary: '放弃试验分支', proposedDisposition: 'accept_stop' },
    ],
    sparkSuggestions: [{ suggestionId: 'suggestion-next', suggestionKind: 'follow_up_opportunity', summary: '保留后续机会', followUpSummary: '由 Human 日后判断是否建立 Spark。' }],
  });
});

test('closure confirmation rejects route targets without an exact fingerprint and proposals with unknown members', () => {
  const base = {
    object_id: 'workcase-0115',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '目标仍应保留。',
  };
  const proposal = {
    proposed_outcome: 'partial',
    proposed_disposition_summary: '将责任路由至已有对象。',
    residual_decisions: [{
      residual_id: 'residual-route',
      summary: '路由责任',
      proposed_disposition: 'route_existing',
      route_target: {
        governed_project_id: 'sample',
        fact_type_key: 'workcase',
        object_id: 'workcase-0111',
        content_fingerprint: 'b'.repeat(64),
      },
    }],
  };

  const missingFingerprint = structuredClone(proposal);
  delete (missingFingerprint.residual_decisions[0].route_target as { content_fingerprint?: string }).content_fingerprint;
  const badFingerprint = structuredClone(proposal);
  badFingerprint.residual_decisions[0].route_target.content_fingerprint = 'not-a-sha256';
  const unknownProposalMember = { ...proposal, generated_hint: 'must not be ignored' };
  const unknownTargetMember = structuredClone(proposal);
  Object.assign(unknownTargetMember.residual_decisions[0].route_target, { title: 'must be reread, not trusted' });

  for (const closureProposal of [missingFingerprint, badFingerprint, unknownProposalMember, unknownTargetMember]) {
    const projected = projectWorkCaseCard({ ...base, closure_proposal: closureProposal });
    assert.equal('closureProposal' in projected, false);
    assert.equal(projected.goal, '目标仍应保留。');
  }
});

test('closure confirmation rejects malformed proposal-local IDs and type-mismatched route object IDs', () => {
  const base = {
    object_id: 'workcase-0116',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '目标仍应保留。',
  };
  const validRoute = {
    proposed_outcome: 'partial',
    proposed_disposition_summary: '将责任路由至已有对象。',
    residual_decisions: [{
      residual_id: 'residual-route',
      summary: '路由责任',
      proposed_disposition: 'route_existing',
      route_target: {
        governed_project_id: 'sample',
        fact_type_key: 'spark',
        object_id: 'spark-0111',
        content_fingerprint: 'c'.repeat(64),
      },
    }],
  };
  const malformedResidual = structuredClone(validRoute);
  malformedResidual.residual_decisions[0].residual_id = 'residual_bad';
  const mismatchedTarget = structuredClone(validRoute);
  mismatchedTarget.residual_decisions[0].route_target.object_id = 'workcase-0111';
  const malformedSuggestion = {
    proposed_outcome: 'completed',
    proposed_disposition_summary: '没有剩余责任。',
    spark_suggestions: [{
      suggestion_id: 'suggestion_bad',
      suggestion_kind: 'follow_up_opportunity',
      summary: '后续机会',
      follow_up_summary: '由 Human 日后判断。',
    }],
  };

  for (const closureProposal of [malformedResidual, mismatchedTarget, malformedSuggestion]) {
    const projected = projectWorkCaseCard({ ...base, closure_proposal: closureProposal });
    assert.equal('closureProposal' in projected, false);
  }
});

test('closure confirmation drops the whole proposal when any residual member is malformed', () => {
  const projected = projectWorkCaseCard({
    object_id: 'workcase-0113',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '目标仍应保留。',
    closure_proposal: {
      proposed_outcome: 'partial',
      proposed_disposition_summary: '不能静默忽略坏成员。',
      residual_decisions: [
        { residual_id: 'residual-a', summary: '有效责任', proposed_disposition: 'accept_stop' },
        { summary: '缺少稳定 residual_id', proposed_disposition: 'accept_stop' },
      ],
    },
  });

  assert.equal('closureProposal' in projected, false);
  assert.equal(projected.goal, '目标仍应保留。');
});

test('completed closure proposal rejects constrained-responsibility Spark suggestions', () => {
  const projected = projectWorkCaseCard({
    object_id: 'workcase-0114',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '目标仍应保留。',
    closure_proposal: {
      proposed_outcome: 'completed',
      proposed_disposition_summary: '错误地遗留了受限责任。',
      spark_suggestions: [{
        suggestion_id: 'suggestion-blocked',
        suggestion_kind: 'constrained_responsibility',
        summary: '受限责任',
        restriction_reason: '缺少外部条件。',
        impact_summary: '责任尚未完成。',
        resume_condition: '条件恢复。',
        follow_up_summary: '由 Human 判断是否建立 Spark。',
      }],
    },
  });

  assert.equal('closureProposal' in projected, false);
});

test('closure confirmation drops the whole proposal when outcome or disposition summary is invalid', () => {
  const base = {
    object_id: 'workcase-0112',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    goal: '目标仍应保留。',
  };
  const missingOutcome = projectWorkCaseCard({ ...base, closure_proposal: { proposed_disposition_summary: '只有摘要。' } });
  const emptySummary = projectWorkCaseCard({ ...base, closure_proposal: { proposed_outcome: 'completed', proposed_disposition_summary: '   ' } });
  const unknownOutcome = projectWorkCaseCard({ ...base, closure_proposal: { proposed_outcome: 'done', proposed_disposition_summary: '摘要。' } });

  assert.equal('closureProposal' in missingOutcome, false);
  assert.equal('closureProposal' in emptySummary, false);
  assert.equal('closureProposal' in unknownOutcome, false);
  assert.equal(missingOutcome.goal, '目标仍应保留。');
});

test('closure confirmation projection carries only stable contributed-to target triples', () => {
  const closure = projectWorkCaseCard({
    object_id: 'workcase-0102',
    fact_type_key: 'workcase',
    title: '等待关闭确认',
    status: 'open',
    phase: 'human_closure_confirming',
    updated_at: '2026-07-27T00:00:00+08:00',
    relations: [
      { relation_key: 'contributed-to', target: { governed_project_id: 'sample', fact_type_key: 'adr', object_id: 'adr-0007' } },
      { relation_key: 'contributed-to', target: { governed_project_id: 'sample', fact_type_key: 'pitfall', object_id: 'pitfall-0003' } },
      { relation_key: 'routed-to', target: { governed_project_id: 'sample', fact_type_key: 'workcase', object_id: 'workcase-0103' } },
      { relation_key: 'contributed-to', target: { fact_type_key: 'spark' } },
      { relation_key: 'contributed-to' },
    ],
  });

  assert.deepEqual(closure.contributedTo, [
    { governedProjectId: 'sample', factTypeKey: 'pitfall', objectId: 'pitfall-0003' },
  ]);
});

test('closed projection carries only Pitfall contributions', () => {
  const closed = projectWorkCaseCard({
    object_id: 'workcase-0104',
    fact_type_key: 'workcase',
    title: '已经关闭',
    status: 'closed',
    updated_at: '2026-07-27T00:00:00+08:00',
    relations: [
      { relation_key: 'contributed-to', target: { governed_project_id: 'sample', fact_type_key: 'pitfall', object_id: 'pitfall-0009' } },
    ],
  });

  assert.deepEqual(closed.contributedTo, [{ governedProjectId: 'sample', factTypeKey: 'pitfall', objectId: 'pitfall-0009' }]);
});

test('relation labels include contributed-to and the detail chip resolves it by key', () => {
  const locales = source('src/i18n/locales.ts');
  const associations = source('src/pages/object-detail/FactAssociationsSection.tsx');

  assert.match(locales, /relation_contributed_to: \{ zh: '贡献了', en: 'Contributed To' \}/);
  assert.match(locales, /'objectList\.workcaseContributions': '后续贡献'/);
  assert.match(locales, /'objectList\.workcaseContributions': 'Follow-up contributions'/);
  assert.match(associations, /relation_\$\{relationKey\.replace\(\/-\/g, '_'\)\}/);
});

test('current list projection preserves every real work-item identity and current status', () => {
  const summary = projectWorkCaseCard(currentWorkCase());

  assert.equal(summary.executionItemsProjectionValid, true);
  const items = summary.executionItems as Array<Record<string, unknown>>;
  assert.deepEqual(items.map((item) => item.id), ['item-done', 'item-running', 'item-blocked', 'item-cancelled']);
  assert.deepEqual(items.map((item) => item.status), ['completed', 'in_progress', 'blocked', 'cancelled']);
  assert.equal(items[2]?.blockingReason, '等待 Human 提供输入。');
  assert.equal('successCriteria' in summary, false);
});

test('public progressing projection keeps counts and active items without the complete item plan', () => {
  const facts = source('api/services/facts.ts');
  const projectionStart = facts.indexOf('export function projectWorkCaseCard');
  const projectionEnd = facts.indexOf('export async function listObjects', projectionStart);
  const publicProjection = facts.slice(projectionStart, projectionEnd);

  assert.ok(projectionStart >= 0 && projectionEnd > projectionStart);
  assert.match(publicProjection, /projectCardWorkItems\(fact\.work_items\)/);
  assert.doesNotMatch(publicProjection, /projected\.work_items/);
});

test('public work-item projection exposes only fields consumed by the Card', () => {
  const projected = projectWorkCaseCard(currentWorkCase());
  const items = projected.executionItems as Array<Record<string, unknown>>;

  assert.deepEqual(Object.keys(items[0] ?? {}).sort(), ['id', 'status', 'title']);
  assert.deepEqual(Object.keys(items[2] ?? {}).sort(), ['blockingReason', 'id', 'status', 'title']);
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
  assert.deepEqual(summary.executionItems, []);
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
