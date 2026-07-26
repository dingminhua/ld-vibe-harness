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
  assert.match(webSpec, /Dashboard 的 WorkCase `byStatus` 键和条目 `status` 也必须使用这四个值/);
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
  assert.match(webSpec, /\*\*成功标准\*\*：`control-contract-v1` 与 `control-contract-v2` 直接读取 `success_criterion_definitions\[\]\.statement`/);
  assert.match(webSpec, /只有来源明确规定步骤先后、优先级、排名、依赖顺序或其它顺序语义，才可以使用数字序号/);
  assert.match(webSpec, /目标与全部成功标准必须完整显示，不得截断、折叠、限制标准条数/);
  assert.match(webSpec, /成功标准是没有先后关系的并列集合，在 Card 中必须统一使用圆点/);
  assert.match(webSpec, /该 Card 不显示 `scope` 中的覆盖、排除或限制，也不显示 work items、依赖、执行步骤、方法、模板、验证安排、创建审核详情、执行统计或关闭材料/);
  assert.match(webSpec, /`progressing` Card 在相同通用对象身份、标题和进展分组之外，正文只显示“目标”和“当前进展”两个区域/);
  assert.match(webSpec, /同时显示四个推进环节中的当前位置、工作项完成数、当前 active 工作项，以及实际存在的等待或阻塞/);
  assert.match(webSpec, /不得引入全局轮次、返回次数、审核次数或其它过程计数/);
  assert.match(webSpec, /不得改变阅读顺序或把四环节拆成会弱化连续关系的 2×2 宫格/);
  assert.match(webSpec, /序号和位置强调只表达推进结构与当前所在环节，不是执行历史或环节完成事实/);
  assert.match(webSpec, /不得仅根据当前环节位于后方，就把任何前序环节标成“已完成”/);
  assert.match(webSpec, /工作项进度按 21 的确定性规则投影为“已完成 N\/T”/);
  assert.match(webSpec, /`cancelled` 必须另行显示数量，不能并入完成数/);
  assert.match(webSpec, /全部 active 项，即 `in_progress` 与 `blocked` 项的稳定 `item_id`、完整 `goal` 和当前状态/);
  assert.match(webSpec, /`item_id` 与状态作为元信息，完整 `goal` 作为事实正文/);
  assert.match(webSpec, /不得把 `item-03` 改写成“第三项”/);
  assert.match(webSpec, /当 `waiting_on` 实际存在时.*完整显示正在等待的对象或条件/);
  assert.match(webSpec, /附加完整显示顶层 `blocking_summary`/);
  assert.match(webSpec, /`progressing` Card 不显示成功标准、scope、依赖、方法、完整工作项计划、执行态势条/);
  assert.match(webSpec, /`closed` 对象的 `closure_approval` 表示该 Human Gate 已经完成/);
  assert.match(webSpec, /不得因 `control-contract-v1` 或 `control-contract-v2` 没有 legacy `closure_requested_at` 或 `review_requested_at` 而报告“请求关闭未完成”/);
  assert.match(webSpec, /不生成请求时间，不把批准改写为请求/);
  assert.match(webSpec, /`closure_confirmation` 和 `closed` Card 的具体正文.*仍待 Human 后续设计判断/);
  assert.match(webSpec, /WorkCase 详情页不使用进展分组或推进环节切换、隐藏、重排或另建阅读结构/);
  assert.match(workCaseSpec, /web-presentation-interaction::7\.4 WorkCase 外部卡片的进展分组投影/);
  assert.match(workCaseSpec, /不反向规定每个 Card 展示哪些事实内容/);

  const cardSection = webSpec.slice(
    webSpec.indexOf('### 7.4 WorkCase 外部卡片的进展分组投影'),
    webSpec.indexOf('## 8. Web 交互边界'),
  );
  assert.doesNotMatch(cardSection, /progress_history|progressRound|第 N 轮|轮次未记录/);
});

test('Web docs keep the WorkCase list contract on four progress groups and current card inputs', () => {
  const listDoc = source('web/docs/03-ObjectList.md');
  const workCaseSection = listDoc.slice(
    listDoc.indexOf('### 3.4 WorkCase 卡片'),
    listDoc.indexOf('### 3.5 Spark 卡片'),
  );

  assert.match(listDoc, /WorkCase 使用 `\?progress=<progress_group>`/);
  assert.match(listDoc, /`plan_confirmation \/ progressing \/ closure_confirmation \/ closed` 四个进展分组/);
  assert.match(workCaseSection, /只显示“目标”和“成功标准”/);
  assert.match(workCaseSection, /第二个区域从“成功标准”替换为“当前进展”/);
  assert.match(workCaseSection, /全部 `in_progress` 和 `blocked` 项/);
  assert.match(workCaseSection, /“关闭待确认”和“已关闭”Card 的正文仍待后续设计/);
  assert.match(workCaseSection, /兼容诊断.*不构成“关闭待确认”或“已关闭”Card 的最终字段/);
  assert.match(listDoc, /progress_group\?: 'plan_confirmation' \| 'progressing' \| 'closure_confirmation' \| 'closed'/);
  assert.match(listDoc, /progress_step\?: 'item_execution' \| 'controller_self_check' \| 'independent_review' \| 'controller_synthesis'/);
  assert.match(listDoc, /goal\?: string/);
  assert.match(listDoc, /waiting_on\?: string/);
  assert.match(listDoc, /blocking_summary\?: string/);
  assert.match(listDoc, /executionItemsActive\?: RelatedObjectSummary\[\]/);
  assert.doesNotMatch(workCaseSection, /progress_history|轮次|orchestration|verification_evidence|closure_evidence|related_/);
});

test('Web docs define one state-invariant WorkCase detail contract from current spec 21 fields', () => {
  const detailDoc = source('web/docs/04-ObjectDetail.md');
  const baselineDoc = source('web/docs/10-Web开发现状与设计语言基线.md');
  const detailSection = detailDoc.slice(
    detailDoc.indexOf('## 4. WorkCase 状态无关阅读契约'),
    detailDoc.indexOf('## 5. 非工作主线对象字段布局'),
  );
  const baselineSection = baselineDoc.slice(
    baselineDoc.indexOf('### 4.2 WorkCase 人的阅读视角'),
    baselineDoc.indexOf('### 4.3 组件契约沉淀'),
  );

  assert.match(detailSection, /不得根据这些进展分组或推进环节切换、隐藏、重排字段/);
  assert.match(detailSection, /`goal` 与 `scope`/);
  assert.match(detailSection, /精确 `phase`、当前 `summary`/);
  assert.match(detailSection, /`success_criterion_definitions`/);
  assert.match(detailSection, /`work_items`/);
  assert.match(detailSection, /`creation_reviews`、`execution_approval`/);
  assert.match(detailSection, /`validation_summary`、`closure_outcome`、`disposition_summary` 与 `residual_responsibilities`/);
  assert.match(detailSection, /`urls` 与 `relations`/);
  assert.match(detailSection, /当前 `WorkCaseReadingLayout`.*尚未完整实现本节契约/);
  assert.doesNotMatch(detailSection, /progress_history|轮次|result_self_checking|subagents_result_reviewing|orchestration|verification_evidence|closure_evidence|related_/);

  assert.match(baselineSection, /所有状态和 phase 下使用同一信息结构/);
  assert.match(baselineDoc, /区分 `control-contract-v1`、`control-contract-v2` 与只读 legacy 兼容边界/);
  assert.match(baselineSection, /按事实数组顺序稳定呈现为没有额外先后关系的并列集合/);
  assert.match(baselineSection, /`pending \/ in_progress \/ blocked \/ completed \/ cancelled`/);
  assert.match(baselineSection, /当前 `WorkCaseReadingLayout` 尚未完整实现这一契约/);
  assert.doesNotMatch(baselineDoc, /current profile|按事实数组顺序作为无序集合显示/);
  assert.doesNotMatch(baselineSection, /progress_history|轮次|result_self_checking|subagents_result_reviewing|orchestration|verification_evidence|closure_evidence|related_/);
});

test('Historical Web studies defer to the current WorkCase and Web sources', () => {
  for (const path of [
    'web/docs/07-内容可读性深度研究.md',
    'web/docs/08-网站整体性多角色审视研究.md',
  ]) {
    const doc = source(path);
    const header = doc.slice(0, doc.indexOf('## 1.'));
    assert.match(header, /文档状态：历史研究输入/);
    assert.match(header, /不是当前规范、字段契约或实现符合性依据/);
    assert.match(header, /specs\/08-Web%20呈现与交互规范\.md/);
    assert.match(header, /specs\/21-WorkCase-工作项\.md/);
    assert.match(header, /03-ObjectList\.md/);
    assert.match(header, /04-ObjectDetail\.md/);
    assert.match(header, /10-Web开发现状与设计语言基线\.md/);
  }
});

test('Current WorkCase phases have direct labels and colors while old display keys stay legacy-only', () => {
  const locales = source('web/src/i18n/locales.ts');
  const colors = source('web/src/utils/statusColors.ts');

  assert.match(locales, /controller_checking: \{ zh: '主控自检中', en: 'Controller Self-check' \}/);
  assert.match(locales, /independent_reviewing: \{ zh: '独立复核中', en: 'Independent Review' \}/);
  assert.match(locales, /closure_preparing: \{ zh: '主控收敛中', en: 'Controller Synthesis' \}/);
  assert.match(locales, /旧 WorkCase 显示键只为 legacy 兼容保留[\s\S]*result_self_checking:[\s\S]*subagents_result_reviewing:/);
  assert.match(locales, /controller_checking: \{ zh: '主控正在自检当前结果'/);
  assert.match(locales, /independent_reviewing: \{ zh: '当前结果正在独立复核'/);
  assert.match(locales, /closure_preparing: \{ zh: '主控正在收敛关闭报告与分流建议'/);
  assert.match(locales, /workcase: \{ zh: '需要持续保存当前计划、推进状态、质量关口与关闭判断的工作责任'/);

  assert.match(colors, /controller_checking: \{ light:/);
  assert.match(colors, /independent_reviewing: \{ light:/);
  assert.match(colors, /closure_preparing: \{ light:/);
  assert.match(colors, /旧 WorkCase 显示键只为 legacy 兼容投影保留[\s\S]*result_self_checking:[\s\S]*subagents_result_reviewing:/);
});
