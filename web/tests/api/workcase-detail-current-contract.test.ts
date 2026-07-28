import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import { projectCurrentWorkCaseDetail } from '../../shared/workcaseDetailProjection.ts';

const repositoryRoot = path.resolve(import.meta.dirname, '../../..');

function common(objectId: string): Record<string, unknown> {
  return {
    object_id: objectId,
    fact_type_key: 'workcase',
    title: `当前详情 ${objectId}`,
    created_at: '2026-07-20T08:00:00+08:00',
    updated_at: '2026-07-20T09:00:00+08:00',
    goal: '完整读取当前 WorkCase 责任。',
    scope: '覆盖当前字段；不生成历史、证明或流程结论。',
  };
}

test('WorkCase detail source consumes only the single current shape in one fixed order', () => {
  const layout = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/WorkCaseReadingLayout.tsx'),
    'utf8',
  );
  const objectDetail = fs.readFileSync(path.join(repositoryRoot, 'web/src/pages/ObjectDetail.tsx'), 'utf8');

  assert.match(layout, /contentVariant === "semantic" \? "grid gap-3" : "ldvh-study-node-content"/);
  assert.match(layout, /contentVariant === "semantic" \? "grid gap-3" : "divide-y divide-ldvh-border\/60"/);
  const panel = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/components/reading-panel/PanelContent.tsx'),
    'utf8',
  );

  assert.doesNotMatch(
    layout,
    /\borchestration\b|execution_items|\bplan_review\b|\bresult_review\b|revision_history|\bsuccess_criteria\b|verification_evidence|closure_evidence|\bdraft\b|review_needed|execution-item-|slice\(0,\s*4\)|sortWorkCaseExecutionItems|progress_group|progress_step/,
  );
  assert.doesNotMatch(layout, /obj\.(?:status|phase)\s*===|switch\s*\([^)]*(?:status|phase)/);
  assert.doesNotMatch(objectDetail, /fetchObjects\(['"]workcase['"]\)/);
  assert.doesNotMatch(panel, /fetchObjects\(['"]workcase['"]\)/);
  assert.doesNotMatch(layout, /summary:\s*ObjectItem|loading:\s*boolean|getStatus:/);
  assert.doesNotMatch(layout, /EmptyHint|missingRecord|recorded|recordState/);
  assert.match(objectDetail, /customMetaEntries=\{\[\]\}/);
  assert.doesNotMatch(objectDetail, /readMeta\.observedAt|meta\.observedAt/);
  assert.match(objectDetail, /reconstructFactYaml\(obj\)/);
  assert.doesNotMatch(objectDetail, /function objectToYaml|objectToYaml\(obj\)/);

  const orderedMarkers = [
    'workcaseCurrentSnapshot',
    'workcaseResponsibility',
    'workcaseSuccessCriteria',
    'workcasePlanAndItems',
    'workcaseCreationReviews',
    'workcaseExecutionApproval',
    'workcaseResultAndValidation',
    'workcaseControllerCheck',
    'workcaseResultReviews',
    'workcaseClosureProposal',
    'workcaseTerminalDisposition',
  ];
  let previous = -1;
  for (const marker of orderedMarkers) {
    const current = layout.indexOf(marker);
    assert.ok(current > previous, `${marker} must remain in the fixed detail order`);
    previous = current;
  }
  const relations = layout.indexOf('<FactAssociationsSection', previous);
  const urls = layout.indexOf('<RelatedContentSection', relations);
  assert.ok(relations > previous, 'formal relations must follow the terminal node');
  assert.ok(urls > relations, 'external URLs must follow formal relations');
});

test('blocked detail shows actual waiting and blocking facts without record-completeness noise', () => {
  const source = {
    ...common('workcase-1001'),
    status: 'blocked',
    priority: 'P1',
    phase: 'executing',
    success_criterion_definitions: [
      { criterion_id: 'criterion-blocked', statement: '阻塞解除后可以继续当前执行项。' },
    ],
    plan_version: 1,
    work_items: [{
      item_id: 'item-blocked',
      goal: '完成受阻工作项',
      expected_result: '形成可复核结果。',
      status: 'blocked',
      current_summary: '已定位到外部输入边界。',
      blocking_summary: '缺少实际输入，当前工作项无法继续。',
    }],
    execution_approval: {
      subject_version: 1,
      approved_at: '2026-07-20T08:10:00+08:00',
      summary: 'Human 批准在既定边界内执行。',
    },
    waiting_on: '等待 Human 提供实际输入。',
    blocking_summary: '全部可继续活动都依赖该输入；提供后可恢复。',
  };
  const detail = projectCurrentWorkCaseDetail(source);

  assert.equal(detail.currentSnapshot, true);
  assert.equal(detail.planAndItems, true);
  assert.equal(source.waiting_on, '等待 Human 提供实际输入。');
  assert.equal(source.blocking_summary, '全部可继续活动都依赖该输入；提供后可恢复。');
  assert.equal(detail.workItems[0]?.blocking_summary, '缺少实际输入，当前工作项无法继续。');
});

test('closure-confirming detail preserves tri-state results and separates every decision role', () => {
  const source = {
    ...common('workcase-1002'),
    status: 'open',
    priority: 'P1',
    phase: 'human_closure_confirming',
    success_criterion_definitions: [
      { criterion_id: 'criterion-pass', statement: '已形成目标产物。' },
      { criterion_id: 'criterion-fail', statement: '全部边界均已满足。' },
      { criterion_id: 'criterion-unknown', statement: '外部环境已经覆盖。' },
    ],
    success_criterion_results: [
      { criterion_id: 'criterion-pass', outcome: 'satisfied', summary: '实际产物已经形成。' },
      { criterion_id: 'criterion-fail', outcome: 'not_satisfied', summary: '一个明确边界尚未满足。' },
      { criterion_id: 'criterion-unknown', outcome: 'not_verified', summary: '外部环境未执行，不能判断。' },
    ],
    plan_version: 1,
    work_items: [{
      item_id: 'item-current',
      goal: '形成当前结果',
      expected_result: '结果可供自检和复核。',
      status: 'completed',
      result_summary: '当前结果已经形成。',
    }],
    execution_approval: {
      subject_version: 1,
      approved_at: '2026-07-20T08:10:00+08:00',
      summary: 'Human 批准执行当前计划版本。',
      source_refs: ['human-input:plan-approval'],
    },
    result_version: 1,
    result_summary: '形成了主要产物，仍有一项未满足和一项未验证。',
    controller_check_summary: 'Controller 检查了字段闭集并保留未验证边界。',
    result_reviews: [{
      reviewer: 'independent-reviewer',
      reviewed_at: '2026-07-20T08:40:00+08:00',
      subject_version: 1,
      scope: '独立检查当前结果与未验证边界。',
      conclusion: 'pass_with_followups',
      feedback: ['不得把未验证改写为已满足。'],
      controller_resolution: 'Controller 保留 not_verified 并在提案中处置。',
    }],
    validation_summary: '本地检查通过；外部环境明确未覆盖。',
    closure_proposal: {
      proposed_outcome: 'partial',
      proposed_disposition_summary: '建议在部分完成分类下停止，并接受一项剩余责任。',
      residual_decisions: [{
        residual_id: 'residual-external',
        summary: '外部环境覆盖仍未确认。',
        proposed_disposition: 'accept_stop',
      }],
    },
    waiting_on: '等待 Human 判断是否按当前提案停止。',
  };
  const detail = projectCurrentWorkCaseDetail(source);

  assert.deepEqual(
    detail.criterionResults.map((result) => result.outcome),
    ['satisfied', 'not_satisfied', 'not_verified'],
  );
  assert.equal(detail.criterionResults[2]?.summary, '外部环境未执行，不能判断。');
  assert.equal(detail.executionApproval?.summary, 'Human 批准执行当前计划版本。');
  assert.equal(detail.controllerCheck, true);
  assert.equal(detail.resultReviews.length, 1);
  assert.equal(detail.closureProposal?.proposed_outcome, 'partial');
  assert.equal(detail.terminalDisposition, false);

  const locales = fs.readFileSync(path.join(repositoryRoot, 'web/src/i18n/locales.ts'), 'utf8');
  assert.match(locales, /workcaseExecutionApprovalBoundary[^\n]+不表示技术结果、验证或关闭已经成立/);
  assert.match(locales, /workcaseControllerCheckBoundary[^\n]+不等于独立复核或 Human 验收/);
  assert.match(locales, /workcaseClosureProposalBoundary[^\n]+不是既成终态或关闭批准/);
});

test('closed detail naturally contracts to the current closed whitelist', () => {
  const source = {
    ...common('workcase-1003'),
    status: 'closed',
    success_criterion_definitions: [
      { criterion_id: 'criterion-closed-a', statement: '主要结果已经形成。' },
      { criterion_id: 'criterion-closed-b', statement: '全部责任均已完成。' },
    ],
    success_criterion_results: [
      { criterion_id: 'criterion-closed-a', outcome: 'satisfied', summary: '主要结果已经形成。' },
      { criterion_id: 'criterion-closed-b', outcome: 'not_satisfied', summary: '一项责任由 Human 接受停止。' },
    ],
    result_summary: '当前责任形成部分结果后停止。',
    validation_summary: '已验证主要结果；剩余责任没有完成。',
    closure_outcome: 'partial',
    disposition_summary: 'Human 决定停止当前 WorkCase，并接受明确剩余责任。',
    residual_responsibilities: [{
      residual_id: 'residual-accepted',
      summary: '未完成的外部覆盖由 Human 接受停止。',
    }],
  };
  const detail = projectCurrentWorkCaseDetail(source);

  assert.equal(detail.responsibility, true);
  assert.equal(detail.criteria.length, 2);
  assert.equal(detail.resultAndValidation, true);
  assert.equal(detail.terminalDisposition, true);
  assert.equal(detail.terminalResiduals.length, 1);
  assert.equal(detail.currentSnapshot, false);
  assert.equal(detail.planAndItems, false);
  assert.equal(detail.executionApproval, null);
  assert.equal(detail.controllerCheck, false);
  assert.equal(detail.resultReviews.length, 0);
  assert.equal(detail.closureProposal, null);
});


test('field-level issues surface in place inside each WorkCase reading node', () => {
  const layout = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/WorkCaseReadingLayout.tsx'),
    'utf8',
  );
  const factReadingLayouts = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/FactReadingLayouts.tsx'),
    'utf8',
  );
  const fieldIssues = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/fieldIssues.ts'),
    'utf8',
  );

  // WC 复用其它事实类型同一套字段问题组件，不另起一套问题呈现。
  assert.match(fieldIssues, /export function fieldIssue\(/);
  assert.match(factReadingLayouts, /export function FieldProblem\(/);
  assert.match(layout, /from "@\/pages\/object-detail\/fieldIssues"/);
  assert.match(layout, /from "@\/pages\/object-detail\/FactReadingLayouts"/);
  assert.match(layout, /\bfieldIssue\b/);
  assert.match(layout, /function FieldIssueRow\(/);
  assert.match(layout, /<FieldProblem issue=\{issue\} \/>/);

  // 每个页面消费字段都能在自己的阅读节点内就地标明缺失或类型不符。
  const consumedFields = [
    'goal', 'scope',
    'phase', 'summary', 'resume_from', 'waiting_on', 'blocking_summary',
    'success_criterion_definitions', 'success_criterion_results',
    'plan_version', 'work_items',
    'creation_reviews', 'execution_approval',
    'result_version', 'result_summary', 'validation_summary',
    'controller_check_summary', 'result_reviews',
    'closure_proposal',
    'closure_outcome', 'disposition_summary', 'residual_responsibilities', 'spark_suggestions',
    'relations', 'urls',
  ];
  for (const field of consumedFields) {
    assert.ok(
      layout.includes(`issueFor("${field}")`),
      `layout must surface the in-node field issue for ${field}`,
    );
  }

  // 节点只按字段实际内容省略；整组字段缺席但存在字段问题时节点仍然保留。
  assert.match(layout, /detail\.responsibility \|\| Boolean\(issueFor\("goal"\)/);
  assert.match(layout, /detail\.currentSnapshot \|\|/);
  assert.match(layout, /detail\.planAndItems \|\|/);
  assert.match(layout, /detail\.terminalDisposition \|\|/);

  // 字段问题就地呈现不引入状态或阶段分支。
  assert.doesNotMatch(layout, /obj\.(?:status|phase)\s*===|switch\s*\([^)]*(?:status|phase)/);
});

test('narrative fields read as prose while structured records keep label rows', () => {
  const layout = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/WorkCaseReadingLayout.tsx'),
    'utf8',
  );

  // 叙述字段与其它事实对象一致：小字题注 + 下方 Markdown 正文，不用标签列。
  assert.match(layout, /function ProseField\(/);
  const narrativeFields = [
    'result_summary', 'validation_summary', 'controller_check_summary',
  ];
  for (const field of narrativeFields) {
    assert.match(
      layout,
      new RegExp(`<ProseField[\\s\\S]{0,160}fieldKey="${field}"`),
      `narrative field ${field} must read as prose`,
    );
  }
  assert.match(layout, /function ClosureOutcomeSummary\(/);
  assert.match(layout, /outcomeFieldKey="proposed_outcome"[\s\S]{0,180}summaryFieldKey="proposed_disposition_summary"/);
  assert.match(layout, /outcomeFieldKey="closure_outcome"[\s\S]{0,180}summaryFieldKey="disposition_summary"/);

  // 目标与范围仍按完整散文读取，但使用职责节点专属的语义色块建立首屏层级。
  assert.match(layout, /function ResponsibilityField\(/);
  assert.match(layout, /fieldKey="goal"[\s\S]{0,160}tone="goal"/);
  assert.match(layout, /fieldKey="scope"[\s\S]{0,160}tone="scope"/);
  assert.match(layout, /contentVariant="semantic"/);

  // 当前情况前置于目标与边界，并按阶段、摘要、恢复、等待和阻塞的职责建立语义层级。
  assert.ok(layout.indexOf('workcaseCurrentSnapshot') < layout.indexOf('workcaseResponsibility'));
  assert.match(layout, /function SnapshotPhaseField\(/);
  assert.match(layout, /function SnapshotProseField\(/);
  for (const field of ['summary', 'resume_from', 'waiting_on', 'blocking_summary']) {
    assert.match(
      layout,
      new RegExp(`<SnapshotProseField[\\s\\S]{0,160}fieldKey="${field}"`),
      `snapshot field ${field} must use the semantic current-state reader`,
    );
  }

  // 单字段节点省略与节点标题重复的题注（与其它对象的单字段散文节点一致）。
  assert.match(layout, /fieldKey="controller_check_summary"[\s\S]{0,120}showLabel=\{false\}/);

  // 当前计划版本进入节点标题栏，正文从工作项开始；字段问题仍在节点内就地显示。
  assert.match(layout, /title=\{t\("objectDetail\.workcasePlanAndItems"\)\}[\s\S]{0,160}headerMeta=\{<PlanVersionMeta value=\{obj\.plan_version\}/);
  assert.match(layout, /headerMeta=\{<PlanVersionMeta[\s\S]{0,140}contentVariant="semantic"/);
  assert.match(layout, /function PlanVersionMeta\(/);
  assert.doesNotMatch(layout, /<NumberField[\s\S]{0,100}fieldKey="plan_version"/);
  assert.match(layout, /FieldIssueRow fieldKey="plan_version"/);

  // 结果版本与计划版本一样进入节点标题栏，结果、验证和主控自检使用不同的语义正文层级。
  assert.match(layout, /title=\{t\("objectDetail\.workcaseResultAndValidation"\)\}[\s\S]{0,160}headerMeta=\{<ResultVersionMeta value=\{obj\.result_version\}/);
  assert.match(layout, /function ResultVersionMeta\(/);
  assert.match(layout, /fieldKey="result_summary"[\s\S]{0,160}variant="result"/);
  assert.match(layout, /fieldKey="validation_summary"[\s\S]{0,160}variant="validation"/);
  assert.match(layout, /fieldKey="controller_check_summary"[\s\S]{0,180}variant="controller"/);

  // 散文正文仍完整渲染 Markdown，不截断、不折叠。
  assert.match(layout, /collapseThreshold=\{Number\.MAX_SAFE_INTEGER\}/);

  // 仍需字段定位的辅助字段保留标签行；核心结构化记录使用稳定身份、结论和正文的专属阅读结构。
  assert.match(layout, /<TextField/);
  assert.match(layout, /<DetailInlineField/);
  assert.match(layout, /function CriterionOutcomeChip\(/);
  assert.match(layout, /function CriterionResultSummary\(/);
  assert.match(layout, /workcaseCriterionResultSummary/);

  // 工作项复用成功标准的卡片语法：标题栏承载稳定 ID 与状态，目标为主正文，预期结果为次级语义块。
  assert.match(layout, /function WorkItem\(/);
  assert.match(layout, /overflow-hidden rounded-lg border border-cyan-400\/30/);
  assert.match(
    layout,
    /<ObjectTypeIcon[\s\S]*?<WorkItemDependencyMeta value=\{item\.depends_on\}[\s\S]*?<WorkItemStatusChip value=\{item\.status\}/,
  );
  assert.match(layout, /<ObjectTypeIcon[\s\S]{0,160}type="workcase"/);
  assert.match(layout, /value=\{item\.goal\}[\s\S]{0,320}<WorkItemTextBlock[\s\S]{0,120}fieldKey="expected_result"[\s\S]{0,160}variant="expectation"/);
  assert.match(layout, /<WorkItemDependencyMeta value=\{item\.depends_on\} locale=\{locale\}/);
  assert.match(layout, /function WorkItemDependencyMeta\(/);
  assert.match(layout, /fieldKey="approach_summary"[\s\S]{0,160}variant="boundary"/);
  assert.match(layout, /fieldKey="work_item_result_summary"[\s\S]{0,160}variant="result"/);
  assert.match(layout, /function WorkItemDetailBlock\(/);
  assert.match(layout, /function WorkItemTextBlock\(/);
  assert.doesNotMatch(layout, /WorkItemArrayBlock/);
  assert.match(layout, /function WorkItemStatusChip\(/);

  // 复核、批准与关闭处置不再是同权值对表：身份和结论进入标题栏，反馈、主控处置和责任去向分层呈现。
  assert.match(layout, /function ReviewConclusionChip\(/);
  assert.match(layout, /function ReviewFeedbackBlock\(/);
  assert.match(layout, /function ReviewProseBlock\(/);
  assert.match(layout, /function ExecutionApproval\([\s\S]*?border-violet-400\/30/);
  assert.match(layout, /function ReadingBoundaryNote\(/);
  assert.match(layout, /<Info size=\{14\}/);
  assert.match(layout, /items-center gap-2 rounded-md bg-ldvh-border/);
  assert.doesNotMatch(layout.slice(layout.indexOf('function ReadingBoundaryNote'), layout.indexOf('function PlanVersionMeta')), /CircleHelp/);
  assert.match(layout, /getFieldValueLabel\("reviewer", reviewer, locale\)/);
  assert.match(layout, /getFieldLabel\("subject_version", locale\)[\s\S]{0,500}getFieldLabel\("reviewed_at", locale\)/);
  assert.ok(layout.indexOf('getFieldLabel("subject_version", locale)') < layout.indexOf('<ReviewConclusionChip value={conclusion}'));
  assert.match(layout, /function ResidualDispositionChip\(/);
  assert.match(layout, /function SuggestionDetail\(/);
  assert.doesNotMatch(layout, /function (?:NumberField|MonoField|EnumField|DateField|TextValueField)\(/);
});

test('WorkCase identity uses the active phase as its single Human-facing header status', () => {
  const objectDetail = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/ObjectDetail.tsx'),
    'utf8',
  );
  const panel = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/components/reading-panel/PanelContent.tsx'),
    'utf8',
  );

  // Active WorkCases use their precise phase as the only header badge; closed
  // WorkCases retain the terminal source status. Main detail and panel agree.
  assert.match(objectDetail, /function getObjectHeaderStatus\(/);
  assert.match(objectDetail, /objectType !== 'workcase' \|\| status === 'closed'/);
  assert.match(objectDetail, /return phase \?\? status/);
  assert.match(objectDetail, /status=\{headerStatus\}/);
  assert.match(objectDetail, /statusLabel=\{headerStatus \? getObjectStatusLocale\(objType, headerStatus, locale\) : undefined\}/);
  assert.match(panel, /const headerStatus = getObjectHeaderStatus\(objectType \|\| '', status, obj \|\| \{\}\)/);
  assert.doesNotMatch(objectDetail, /secondaryStatus/);
});

test('closure route target resolves the current target like formal relations', () => {
  const layout = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/WorkCaseReadingLayout.tsx'),
    'utf8',
  );
  const model = fs.readFileSync(
    path.join(repositoryRoot, 'web/src/pages/object-detail/model.ts'),
    'utf8',
  );

  // 与关联区同一规则：项目身份来自共享实现，不做第二份项目解析。
  assert.match(model, /export function getCurrentProjectId\(/);
  assert.match(layout, /getCurrentProjectId/);

  // 同项目目标按需解析当前标题并进入右侧扩展阅读；不以 object_id 冒充名称。
  assert.match(layout, /function ResolvedRouteTargetRow\(/);
  assert.match(layout, /fetchObjectDetail\(factTypeKey, objectId\)/);
  assert.match(layout, /openPanel\(\{ type: "object", title, objectType: factTypeKey, objectId \}\)/);
  assert.match(layout, /CopyPathButton/);
  assert.match(layout, /projectId === currentProjectId/);

  // 跨项目或身份不完整的目标只如实显示已知稳定身份，不猜测标题。
  assert.match(layout, /function UnresolvedRouteTargetRow\(/);
  assert.match(layout, /\{objectId \|\| "—"\}/);

  // 项目身份与内容 fingerprint 作为次级定位事实保留，不冒充当前标题。
  assert.match(layout, /fieldKey="governed_project_id"/);
  assert.match(layout, /fieldKey="content_fingerprint"/);
});
