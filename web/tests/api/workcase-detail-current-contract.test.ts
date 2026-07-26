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
  assert.match(objectDetail, /customMetaEntries=\{readMeta\.observedAt/);
  assert.match(objectDetail, /objectDetail\.observedAt/);
  assert.match(objectDetail, /reconstructFactYaml\(obj\)/);
  assert.doesNotMatch(objectDetail, /function objectToYaml|objectToYaml\(obj\)/);

  const orderedMarkers = [
    'workcaseResponsibility',
    'workcaseCurrentSnapshot',
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
