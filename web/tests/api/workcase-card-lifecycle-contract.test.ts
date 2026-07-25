import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';
import {
  WORKCASE_CURRENT_STATUSES,
  WORKCASE_STATUS_ORDER,
  getWorkCaseDisplayStatus,
  getWorkCaseDynamicStageIndex,
} from '../../shared/workcaseStatus.ts';

const webRoot = path.resolve(import.meta.dirname, '../..');

function source(relativePath: string): string {
  return fs.readFileSync(path.join(webRoot, relativePath), 'utf8');
}

test('WorkCase cards distinguish progressing, waiting, and closed states', () => {
  const status = source('shared/workcaseStatus.ts');
  const list = source('src/pages/ObjectList.tsx');
  const locales = source('src/i18n/locales.ts');

  assert.match(status, /export const WORKCASE_DYNAMIC_STATUSES = \[/);
  assert.match(status, /'executing',\s*'result_self_checking',\s*'subagents_result_reviewing'/s);
  assert.match(status, /export type WorkCaseCardState = 'dynamic' \| 'waiting' \| 'closed'/);
  assert.match(status, /if \(status === 'closed'\) return 'closed';/);
  assert.match(list, /function WorkCaseLifecycleSignal/);
  assert.match(list, /WORKCASE_DYNAMIC_STATUSES\.map/);
  assert.match(list, /showNonActiveReason=\{false\}/);
  assert.match(locales, /human_plan_confirming: \{ zh: '方案待确认'/);
  assert.match(locales, /human_closure_confirming: \{ zh: '关闭待确认'/);
});

test('pre-creation plan review is not exposed as a current WorkCase status', () => {
  assert.equal(WORKCASE_CURRENT_STATUSES.includes('subagents_plan_reviewing' as never), false);
  assert.equal(WORKCASE_STATUS_ORDER.includes('subagents_plan_reviewing' as never), false);
  assert.equal(WORKCASE_CURRENT_STATUSES[0], 'human_plan_confirming');
});

test('closure preparation stays in result review until the Human close gate begins', () => {
  const displayStatus = getWorkCaseDisplayStatus('closure_preparing', 'open');

  assert.equal(displayStatus, 'subagents_result_reviewing');
  assert.equal(
    getWorkCaseDynamicStageIndex(displayStatus),
    getWorkCaseDynamicStageIndex('subagents_result_reviewing'),
  );
  assert.notEqual(displayStatus, 'result_self_checking');
  assert.notEqual(displayStatus, 'human_closure_confirming');
});
