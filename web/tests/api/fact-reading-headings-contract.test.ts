import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('ADR, Pitfall, and Spark detail headings use their source-defined two-character Chinese vocabulary', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactReadingLayouts.tsx'), 'utf8');

  for (const [field, heading] of [
    ['decision_question', '问题'], ['decision', '决策'], ['applicability', '范围'],
    ['rationale', '理由'], ['consequences', '影响'], ['disposition_summary', '处置'],
    ['symptoms', '现象'], ['trigger_conditions', '触发'], ['validation_summary', '验证'],
    ['root_cause', '根因'], ['resolution', '方案'], ['avoidance', '规避'],
    ['intent', '意图'], ['summary', '摘要'], ['evolution', '演变'],
  ]) {
    assert.match(source, new RegExp(`field: '${field}', zh: '${heading}'`));
  }

  assert.match(source, /obj\.status === 'implemented'.*'落实'/);
  assert.match(source, /obj\.status === 'discarded'.*'废弃'/);
  assert.match(source, /zh: '分流', en: 'Routing'/);
  assert.doesNotMatch(source, /field: 'decision_question', zh: '决策问题'/);
});
