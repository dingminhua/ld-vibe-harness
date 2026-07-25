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
  const content = list.slice(list.indexOf('function WorkCasePlanConfirmationContent'), list.indexOf('function WorkCaseProgressSignal'));
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
