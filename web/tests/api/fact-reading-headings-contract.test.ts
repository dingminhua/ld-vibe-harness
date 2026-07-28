import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

test('ADR, Pitfall, and Spark detail headings use the central field and status vocabulary', () => {
  const source = fs.readFileSync(path.resolve('src/pages/object-detail/FactReadingLayouts.tsx'), 'utf8');
  const locales = fs.readFileSync(path.resolve('src/i18n/locales.ts'), 'utf8');

  for (const [field, heading] of [
    ['decision_question', '决策问题'], ['decision', '决策'], ['applicability', '适用范围'],
    ['rationale', '理由'], ['consequences', '影响'], ['disposition_summary', '处置说明'],
    ['symptoms', '问题现象'], ['trigger_conditions', '触发条件'], ['validation_summary', '验证说明'],
    ['root_cause', '根因'], ['resolution', '解决方案'], ['avoidance', '规避策略'],
    ['intent', '意图'], ['current_summary', '当前情况'], ['evolution', '演变记录'],
  ]) {
    assert.match(locales, new RegExp(`${field}: \\{ zh: '${heading}'`));
  }

  assert.match(source, /title={getFieldLabel\(node\.field, locale\)}/);
  assert.match(source, /getObjectStatusLocale\('spark'/);
  assert.doesNotMatch(source, /locale === 'en'/);
});
