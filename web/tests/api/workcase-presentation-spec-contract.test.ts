import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { test } from 'node:test';

const repositoryRoot = path.resolve(import.meta.dirname, '../../..');

function source(relativePath: string): string {
  return fs.readFileSync(path.join(repositoryRoot, relativePath), 'utf8');
}

function workCaseCardSection(): string {
  const webSpec = source('specs/08-Web 呈现与交互规范.md');
  return webSpec.slice(
    webSpec.indexOf('### 7.4 WorkCase 外部卡片的进展分组投影'),
    webSpec.indexOf('## 8. Web 交互边界'),
  );
}

test('Specs define four progress groups and a four-step result track', () => {
  const cardSection = workCaseCardSection();

  assert.match(cardSection, /不是 WorkCase 的 `status`、`phase`、生命周期分类/);
  assert.match(cardSection, /不得显示为“生命周期”“生命周期分类”/);
  assert.match(cardSection, /每张 WorkCase 外部 Card 必须直接、可识别地显示其当前 `progress_group`/);
  assert.match(cardSection, /Dashboard 的 WorkCase 聚合键必须命名为 `byProgressGroup`/);
  assert.match(cardSection, /条目必须以 `progress_group` 承载这四个值/);
  assert.match(cardSection, /不得把派生分组写入名为 `status` 的字段/);
  assert.match(cardSection, /另以 `source_status` 原样承载/);
  assert.match(cardSection, /\| `plan_confirmation` \| 方案待确认 \|/);
  assert.match(cardSection, /\| `progressing` \| 推进中 \|/);
  assert.match(cardSection, /实际存在的 Human 等待或责任阻塞另行呈现，不改变进展分组/);
  assert.match(cardSection, /\| `closure_confirmation` \| 关闭待确认 \|/);
  assert.match(cardSection, /\| `closed` \| 已关闭 \|/);
  assert.match(cardSection, /Human 已依据完整关闭提案决定停止推进并接受相应责任处置/);
  assert.doesNotMatch(cardSection, /Human 已批准当前结果与报告/);
  assert.match(cardSection, /\| `item_execution` \| 工作项执行 \| `executing` \|/);
  assert.match(cardSection, /\| `controller_self_check` \| 主控自检 \| `controller_checking` \|/);
  assert.match(cardSection, /\| `independent_review` \| 独立复核 \| `independent_reviewing` \|/);
  assert.match(cardSection, /\| `controller_synthesis` \| 主控收敛 \| `closure_preparing` \|/);
});

test('Specs place plan revision outside the four-step track without losing current facts', () => {
  const cardSection = workCaseCardSection();

  assert.match(cardSection, /`plan_revising` 属于“推进中”/);
  assert.match(cardSection, /\| 活动期；`phase=plan_revising` \| `progressing` \| 省略；Card 显示轨迹外内部位置“方案修订中” \|/);
  assert.match(cardSection, /不得高亮四步中的任一项/);
  assert.match(cardSection, /不得新增第五个稳定 `progress_step`/);
  assert.match(cardSection, /真实 active item、`waiting_on` 与 `blocking_summary` 仍按当前事实显示/);
});

test('Specs fix plan-confirmation and progressing Card inputs to the latest fields', () => {
  const cardSection = workCaseCardSection();

  assert.match(cardSection, /`plan_confirmation` Card 在通用对象身份、标题和进展分组之外，\*\*计划判断输入区\*\*只显示以下两项 Human 计划判断输入/);
  assert.match(cardSection, /\*\*目标\*\*：直接读取当前 WorkCase 的 `goal`/);
  assert.match(cardSection, /\*\*成功标准\*\*：直接读取 `success_criterion_definitions\[\]\.statement`/);
  assert.match(cardSection, /目标与全部成功标准必须完整显示，不得截断、折叠、限制标准条数/);
  assert.match(cardSection, /成功标准是没有先后关系的并列集合，在 Card 中必须统一使用圆点/);
  assert.match(cardSection, /在计划判断输入区之外另设独立的当前状态提示区，完整显示顶层 `blocking_summary`/);
  assert.match(cardSection, /该提示不构成第三项计划判断输入/);
  assert.match(cardSection, /`progressing` Card 在相同通用对象身份、标题和进展分组之外，正文只显示“目标”和“当前进展”两个区域/);
  assert.match(cardSection, /不得引入全局轮次、返回次数、审核次数、完成比例或其它过程计数/);
  assert.match(cardSection, /当前环节为 `item_execution` 时，Card 必须完整列出全部当前 work item/);
  assert.match(cardSection, /不显示“已完成 N\/T”或其它进度比例/);
  assert.match(cardSection, /`completed` 项在前并使用完成勾选/);
  assert.match(cardSection, /`in_progress` 项随后，以当前强调样式突出/);
  assert.match(cardSection, /`pending` 项以弱化样式置于进行中\/阻塞项之后/);
  assert.match(cardSection, /`cancelled` 项也必须保留并明确标识/);
  assert.match(cardSection, /其它推进环节不展开完整工作项清单/);
  assert.match(cardSection, /渲染顺序不表示推进顺序/);
  assert.match(cardSection, /不得把 `item-03` 改写成“第三项”/);
  assert.match(cardSection, /当 `waiting_on` 实际存在时.*完整显示正在等待的对象或条件/);
  assert.match(cardSection, /附加完整显示顶层 `blocking_summary`/);
  assert.match(cardSection, /`progressing` Card 不显示成功标准、scope、依赖、方法、完整工作项计划中的预期结果或执行细节、执行态势条/);
  assert.doesNotMatch(cardSection, /progress_history|第 N 轮|轮次未记录/);
});

test('Specs define the closure-decision input zone and contributed-to section for closure confirmation cards', () => {
  const cardSection = workCaseCardSection();

  assert.match(cardSection, /`closure_confirmation` Card 在通用对象身份、标题、进展分组和更新时间之外，正文定义以下两区/);
  assert.match(cardSection, /\*\*关闭判断输入区\*\*：回答“当前请求确认的是哪一种关闭结论与责任处置”/);
  assert.match(cardSection, /\*\*目标\*\*：直接读取当前 WorkCase 的 `goal`/);
  assert.match(cardSection, /\*\*关闭结论（提议）\*\*：直接读取 `closure_proposal\.proposed_outcome`/);
  assert.match(cardSection, /`completed \/ partial \/ not-achieved \/ cancelled` 四值闭集的本地化标签/);
  assert.match(cardSection, /使用弱信号标签表达，不渲染为大面积实心色块或强告警色/);
  assert.match(cardSection, /\*\*处置摘要\*\*：直接读取 `closure_proposal\.proposed_disposition_summary`，完整显示/);
  assert.match(cardSection, /\*\*遗留事项处置建议\*\*：直接读取 `closure_proposal\.residual_decisions\[\]`/);
  assert.match(cardSection, /`route_existing`“路由到已有对象”、`suggest_spark`“建议后续建立 Spark”、`accept_stop`“接受停止”/);
  assert.match(cardSection, /各项是没有先后关系的并列集合，使用与处置语义相称的状态图标/);
  assert.match(cardSection, /route_existing 显示已回读目标的当前标题与类型/);
  assert.match(cardSection, /直接读取 `closure_proposal\.spark_suggestions\[\]`/);
  assert.match(cardSection, /`closure_proposal` 缺失、结构不符或其必要成员不可读时/);
  assert.match(cardSection, /Web 也不得为 `closure_proposal` 补写生成的占位提案/);
  assert.match(cardSection, /\*\*后续贡献\*\*区：该区逐项列出当前 WorkCase 实际声明的 `contributed-to` Pitfall 目标/);
  assert.match(cardSection, /`draft`“待确认”、`active`“已确认”、`discarded`“已废弃”、`retired`“已退出”/);
  assert.match(cardSection, /不以 object_id 冒充名称/);
  assert.match(cardSection, /不把该区表达为剩余责任去向/);
  assert.match(cardSection, /当前对象没有任何 `contributed-to` 时该区整体省略，不生成空态文案/);
  assert.match(cardSection, /不提供 promote、discard、批量审核或自动过期控件/);
  assert.match(cardSection, /`closure_confirmation` Card 不显示关闭完整性诊断/);
  assert.match(cardSection, /除上述两区外，不展开成功标准结果、结果与验证、主控自检、独立结果复核或执行统计/);
  assert.match(cardSection, /即使实际 `status=blocked` 也不在 Card 额外展示阻塞/);
  assert.match(cardSection, /关闭决定由专属事务消费，不持久化 approval 或关闭时间收据/);
  assert.match(cardSection, /`closed` Card 使用与上述关闭 Card 相同的扫读结构/);
  assert.match(cardSection, /route_existing 从 `routed-to` 与当前 target title 呈现/);
  assert.match(cardSection, /`related-to` 只在详情关系区呈现/);
  assert.doesNotMatch(cardSection, /control-contract|workcase_profile|closure_requested_at|review_requested_at|closure_approval/);
});

test('Current Web docs describe the same latest-only Card and detail boundaries', () => {
  const dashboardDoc = source('web/docs/02-Dashboard.md');
  const listDoc = source('web/docs/03-ObjectList.md');
  const detailDoc = source('web/docs/04-ObjectDetail.md');
  const baselineDoc = source('web/docs/10-Web开发现状与设计语言基线.md');
  const listSection = listDoc.slice(listDoc.indexOf('### 3.4 WorkCase 卡片'), listDoc.indexOf('### 3.5 Spark 卡片'));
  const detailSection = detailDoc.slice(detailDoc.indexOf('## 4. WorkCase 状态无关阅读契约'), detailDoc.indexOf('## 5. 非工作主线对象字段布局'));
  const baselineSection = baselineDoc.slice(baselineDoc.indexOf('### 4.2 WorkCase 人的阅读视角'), baselineDoc.indexOf('### 4.3 组件契约沉淀'));

  assert.match(dashboardDoc, /WorkCase 统计只使用 `byProgressGroup`，WorkCase 条目只使用 `progress_group`/);
  assert.match(dashboardDoc, /不得把派生进展分组放入名为 `status` 或 `byStatus` 的字段/);
  assert.match(dashboardDoc, /只能另设 `source_status`，不得复用 `status`/);
  assert.match(listDoc, /WorkCase 使用 `\?progress=<progress_group>`/);
  assert.match(listSection, /计划判断输入区只包含“目标”和“成功标准”/);
  assert.match(listSection, /在计划判断输入区之外完整显示独立的阻塞状态提示/);
  assert.match(listSection, /不是第三项计划判断输入/);
  assert.match(listSection, /轨迹外内部位置“方案修订中”/);
  assert.match(listSection, /“已关闭”Card 使用相同扫读结构/);
  assert.match(listDoc, /progress_group\?: 'plan_confirmation' \| 'progressing' \| 'closure_confirmation' \| 'closed'/);
  assert.match(listDoc, /progress_step\?: 'item_execution' \| 'controller_self_check' \| 'independent_review' \| 'controller_synthesis'/);
  assert.match(listDoc, /executionItems\?: Array<\{/);
  assert.match(listDoc, /id: string;/);
  assert.match(listDoc, /title: string;/);
  assert.match(listDoc, /status: 'pending' \| 'in_progress' \| 'blocked' \| 'completed' \| 'cancelled';/);
  assert.match(listDoc, /blockingReason\?: string;/);
  assert.match(listDoc, /`status` 始终保留事实责任状态/);
  assert.match(listDoc, /不得把 phase 填进 `status`/);
  assert.match(listDoc, /不得新增 `responsibilityStatus` 兼容别名/);
  assert.match(listDoc, /`executionItems` 只包含 Card 展示需要的 ID、目标、状态和阻塞说明/);
  assert.match(listDoc, /在 `item_execution` 时页面按状态显示全部成员/);
  assert.match(listDoc, /`closure_confirmation` 携带 `goal`、Pitfall `contributedTo` 和 `closureProposal`；`closed` 携带 `goal`、Pitfall `contributedTo` 和 `closureTerminal`/);
  assert.match(listDoc, /contributedTo\?: Array<\{/);
  assert.match(listDoc, /governedProjectId: string;/);
  assert.match(listDoc, /factTypeKey: string;/);
  assert.match(listDoc, /objectId: string;/);
  assert.match(listDoc, /closureProposal\?: \{/);
  assert.match(listDoc, /proposedOutcome: 'completed' \| 'partial' \| 'not-achieved' \| 'cancelled';/);
  assert.match(listDoc, /residualDecisions: Array<\{/);
  assert.match(listDoc, /proposedDisposition: 'route_existing' \| 'suggest_spark' \| 'accept_stop';/);
  assert.match(listDoc, /完整 `closure_proposal`/);
  assert.match(listDoc, /不设置列表级“观察时间”或“重新读取”控件/);
  assert.doesNotMatch(listSection, /control-contract|workcase_profile|closure_requested_at|review_requested_at|closure_approval/);

  assert.match(detailSection, /`human_plan_confirming`、`plan_revising`、`executing`/);
  assert.match(detailSection, /不得根据这些进展分组或推进环节切换、隐藏、重排字段/);
  assert.match(detailSection, /`goal` 与 `scope`/);
  assert.match(detailSection, /`creation_reviews`、`execution_approval`/);
  assert.match(detailSection, /关闭决定由专属事务消费，不作为 approval 收据保存在对象中/);
  assert.match(detailSection, /closed 不具有 phase、关闭 approval 或关闭时间字段/);
  assert.doesNotMatch(detailSection, /workcase_profile|closure_approval/);

  assert.match(baselineDoc, /WorkCase 不根据对象年代、缺失字段或实现版本切换结构/);
  assert.match(baselineSection, /`plan_revising` 同样归入“推进中”/);
  assert.match(baselineSection, /Card 在计划判断输入区之外完整显示独立的 `blocking_summary` 状态提示/);
  assert.match(baselineSection, /不是第三项计划判断输入/);
  assert.match(baselineSection, /closed 不保存关闭 approval 或关闭时间/);
  assert.match(baselineSection, /所有状态和 phase 下使用同一信息结构/);
  assert.match(baselineSection, /`pending \/ in_progress \/ blocked \/ completed \/ cancelled`/);
  assert.match(baselineSection, /Web 只消费这套当前状态闭集/);
  assert.doesNotMatch(baselineSection, /读取适配层兼容/);
  assert.doesNotMatch(baselineSection, /control-contract|workcase_profile|closure_requested_at|review_requested_at|closure_approval/);
});

test('Dashboard UI consumes WorkCase progress groups without relabeling them as status', () => {
  const dashboard = source('web/src/pages/Dashboard.tsx');
  const apiTypes = source('web/src/utils/api.ts');

  assert.match(dashboard, /item\.type === 'workcase'[\s\S]*item\.progress_group \?\? 'unknown'[\s\S]*item\.status \?\? 'unknown'/);
  assert.match(dashboard, /if \(item\.type !== 'workcase' \|\| !item\.progress_group\) continue/);
  assert.match(dashboard, /distribution=\{type === 'workcase' \? stat\?\.byProgressGroup \?\? \{\} : stat\?\.byStatus \?\? \{\}\}/);
  assert.match(dashboard, /<StatusBadge status=\{displayState\}/);
  assert.doesNotMatch(dashboard, /<StatusBadge status=\{item\.status\}/);
  assert.doesNotMatch(dashboard, /byStatus=\{/);

  assert.match(apiTypes, /type: 'workcase';[\s\S]*byProgressGroup: Partial<Record<DashboardWorkCaseProgressGroup, number>>;[\s\S]*byStatus\?: never/);
  assert.match(apiTypes, /type: 'workcase';[\s\S]*progress_group: DashboardWorkCaseProgressGroup;[\s\S]*status\?: never/);
});

test('Current Web WorkCase docs reject retired fields and states', () => {
  const currentDocuments = [
    'web/docs/01-全局设计约束.md',
    'web/docs/02-Dashboard.md',
    'web/docs/03-ObjectList.md',
    'web/docs/04-ObjectDetail.md',
    'web/docs/09-图标语义规范.md',
    'web/docs/10-Web开发现状与设计语言基线.md',
  ];
  const currentWorkCaseSources = [
    'web/shared/workcaseStatus.ts',
    'web/src/pages/object-detail/WorkCaseReadingLayout.tsx',
  ];
  const retiredTokens = /\b(?:orchestration|execution_items|success_criteria|verification_evidence|closure_evidence|review_needed|closure_approval|closure_requested_at|review_requested_at|done|skipped)\b/;

  for (const relativePath of [...currentDocuments, ...currentWorkCaseSources]) {
    assert.doesNotMatch(source(relativePath), retiredTokens, relativePath);
  }

  assert.equal(fs.existsSync(path.join(repositoryRoot, 'web/docs/07-内容可读性深度研究.md')), false);
  assert.equal(fs.existsSync(path.join(repositoryRoot, 'web/docs/08-网站整体性多角色审视研究.md')), false);

  const iconDoc = source('web/docs/09-图标语义规范.md');
  assert.match(iconDoc, /\| completed \| `CheckCircle2` \| 已完成 \|/);
  assert.match(iconDoc, /\| cancelled \| `CircleX` \| 已取消 \|/);
  assert.doesNotMatch(iconDoc, /已跳过/);
});

test('Global Web docs distinguish identity timestamps from WorkCase review events', () => {
  const globalDoc = source('web/docs/01-全局设计约束.md');

  assert.match(globalDoc, /普通对象身份的绝对时间统一使用 `formatDateTime\(\)`/);
  assert.match(globalDoc, /`reviewed_at`、`approved_at` 等复核或批准事件时间除外/);
  assert.match(globalDoc, /完整显示来源中的原始带时区 RFC 3339/);
  assert.match(globalDoc, /不得截断到分钟或丢失偏移量/);
});

test('Current WorkCase phases have direct labels and colors with no retired display keys', () => {
  const locales = source('web/src/i18n/locales.ts');
  const colors = source('web/src/utils/statusColors.ts');

  assert.match(locales, /plan_revising: \{ zh: '方案修订中', en: 'Plan Revision' \}/);
  assert.match(locales, /controller_checking: \{ zh: '主控自检中', en: 'Controller Self-check' \}/);
  assert.match(locales, /independent_reviewing: \{ zh: '独立复核中', en: 'Independent Review' \}/);
  assert.match(locales, /closure_preparing: \{ zh: '主控收敛中', en: 'Controller Synthesis' \}/);
  assert.match(colors, /plan_revising: \{ light:/);
  assert.match(colors, /controller_checking: \{ light:/);
  assert.match(colors, /independent_reviewing: \{ light:/);
  assert.match(colors, /closure_preparing: \{ light:/);
  assert.doesNotMatch(locales, /result_self_checking|subagents_result_reviewing/);
  assert.doesNotMatch(colors, /result_self_checking|subagents_result_reviewing/);
});
