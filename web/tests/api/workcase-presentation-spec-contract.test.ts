import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

const repositoryRoot = path.resolve(import.meta.dirname, '../../..');

function source(relativePath: string): string {
  return fs.readFileSync(path.join(repositoryRoot, relativePath), 'utf8');
}

test('Specs define four WorkCase progress groups and four progressing steps', () => {
  const webSpec = source('specs/08-Web 呈现与交互规范.md');

  assert.match(webSpec, /### 7\.4 WorkCase 外部卡片的进展分组投影/);
  assert.match(webSpec, /不是 WorkCase 的 `status`、`phase`、生命周期分类/);
  assert.match(webSpec, /不得显示为“生命周期”“生命周期分类”/);
  assert.match(webSpec, /每张 WorkCase 外部 Card 必须直接、可识别地显示其当前 `progress_group`/);
  assert.match(webSpec, /不能只在列表筛选、分组标题或 Dashboard 汇总中显示/);
  assert.match(webSpec, /\| `plan_confirmation` \| 方案待确认 \|/);
  assert.match(webSpec, /\| `progressing` \| 推进中 \|/);
  assert.match(webSpec, /\| `closure_confirmation` \| 关闭待确认 \|/);
  assert.match(webSpec, /\| `closed` \| 已关闭 \|/);
  assert.match(webSpec, /\| `item_execution` \| 工作项执行 \| `executing` \|/);
  assert.match(webSpec, /\| `controller_self_check` \| 主控自检 \| `controller_checking` \|/);
  assert.match(webSpec, /\| `independent_review` \| 独立复核 \| `independent_reviewing` \|/);
  assert.match(webSpec, /\| `controller_synthesis` \| 主控收敛 \| `closure_preparing` \|/);
});

test('Specs keep the card projection derived and detail-invariant while fixing plan-confirmation and progressing inputs', () => {
  const webSpec = source('specs/08-Web 呈现与交互规范.md');
  const workCaseSpec = source('specs/21-WorkCase-工作项.md');

  assert.match(webSpec, /不得把 blocked 改成第五个进展分组/);
  assert.match(webSpec, /`plan_confirmation` Card 在通用对象身份、标题和进展分组之外，正文只显示以下两项 Human 计划判断输入/);
  assert.match(webSpec, /\*\*目标\*\*：直接读取当前 WorkCase 的 `goal`/);
  assert.match(webSpec, /\*\*成功标准\*\*：current profile 直接读取 `success_criterion_definitions\[\]\.statement`/);
  assert.match(webSpec, /只有来源明确规定步骤先后、优先级、排名、依赖顺序或其它顺序语义，才可以使用数字序号/);
  assert.match(webSpec, /目标与全部成功标准必须完整显示，不得截断、折叠、限制标准条数/);
  assert.match(webSpec, /成功标准是没有先后关系的并列集合，在 Card 中必须统一使用圆点/);
  assert.match(webSpec, /该 Card 不显示 `scope` 中的覆盖、排除或限制，也不显示 work items、依赖、执行步骤、方法、模板、验证安排、创建审核详情、执行统计或关闭材料/);
  assert.match(webSpec, /`progressing` Card 在相同通用对象身份、标题和进展分组之外，正文只显示“目标”和“当前进展”两个区域/);
  assert.match(webSpec, /同时显示当前轮次、四个推进环节中的当前位置、工作项完成数和当前工作项/);
  assert.match(webSpec, /当 `coverage=full` 时显示“第 N 轮”；当 `coverage=partial` 时必须显示“自记录起第 N 轮”/);
  assert.match(webSpec, /不得从 `result_version`、审核次数、数组位置、更新时间、Git history 或当前 phase 补猜轮次/);
  assert.match(webSpec, /序号和位置强调只表达推进结构与当前所在环节，不是执行历史或环节完成事实/);
  assert.match(webSpec, /不得仅根据当前环节位于后方，就把任何前序环节标成“已完成”/);
  assert.match(webSpec, /工作项进度按 21 的确定性规则投影为“已完成 N\/T”/);
  assert.match(webSpec, /`cancelled` 必须另行显示数量，不能并入完成数/);
  assert.match(webSpec, /列出全部 `in_progress` 项的稳定 `item_id` 与完整 `goal`/);
  assert.match(webSpec, /不得把 `item-03` 改写成“第三项”/);
  assert.match(webSpec, /附加完整显示来源 `blocking_summary`/);
  assert.match(webSpec, /`progressing` Card 不显示成功标准、scope、依赖、方法、完整工作项计划、执行态势条/);
  assert.match(webSpec, /`closure_confirmation` 和 `closed` Card 的具体正文.*仍待 Human 后续设计判断/);
  assert.match(webSpec, /WorkCase 详情页不使用进展分组或推进环节切换、隐藏、重排或另建阅读结构/);
  assert.match(workCaseSpec, /web-presentation-interaction::7\.4 WorkCase 外部卡片的进展分组投影/);
  assert.match(workCaseSpec, /不反向规定每个 Card 展示哪些事实内容/);
});
