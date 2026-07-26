// ============================================================
// 状态词汇表 — 所有 LDVH 事实对象状态的中英对照
// 来源：specs/05-事实模型基础规范 §5 状态机
// ============================================================
export const STATUS_LOCALES: Record<string, { zh: string; en: string }> = {
  // WorkCase / ADR
  draft: { zh: '草稿', en: 'Draft' },
  proposed: { zh: '已提议', en: 'Proposed' },
  accepted: { zh: '已采纳', en: 'Accepted' },
  retired: { zh: '已退出', en: 'Retired' },
  rejected: { zh: '已拒绝', en: 'Rejected' },
  deprecated: { zh: '已废弃', en: 'Deprecated' },
  archived: { zh: '已归档', en: 'Archived' },
  active: { zh: '活跃', en: 'Active' },
  pending: { zh: '待处理', en: 'Pending' },
  in_progress: { zh: '进行中', en: 'In Progress' },
  blocked: { zh: '已阻塞', en: 'Blocked' },
  done: { zh: '已完成', en: 'Done' },
  skipped: { zh: '已跳过', en: 'Skipped' },
  suspended: { zh: '已暂停', en: 'Suspended' },
  planned: { zh: '计划中', en: 'Planned' },
  executing: { zh: '执行中', en: 'Executing' },
  verifying: { zh: '验证中', en: 'Verifying' },
  review_needed: { zh: '待关闭', en: 'Pending Close' },
  human_plan_confirming: { zh: '方案待确认', en: 'Plan Confirmation' },
  result_self_checking: { zh: '结果自检中', en: 'Self Check' },
  subagents_result_reviewing: { zh: '结果复核中', en: 'Result Review' },
  human_closure_confirming: { zh: '关闭待确认', en: 'Closure Confirmation' },
  plan_confirmation: { zh: '方案待确认', en: 'Plan Confirmation' },
  progressing: { zh: '推进中', en: 'In Progress' },
  closure_confirmation: { zh: '关闭待确认', en: 'Closure Confirmation' },
  closed: { zh: '已关闭', en: 'Closed' },
  open: { zh: '未关闭', en: 'Open' },
  routed: { zh: '已分流', en: 'Routed' },
  implemented: { zh: '已落实', en: 'Implemented' },
  degraded: { zh: '受限', en: 'Limited' },
  needs_human_gate: { zh: '需确认', en: 'Needs Gate' },
  pass: { zh: '通过', en: 'Pass' },
  pass_with_followups: { zh: '通过但有后续项', en: 'Pass with follow-ups' },
  fail: { zh: '不通过', en: 'Fail' },
  unknown: { zh: '未知', en: 'Unknown' },
  // Spark
  resolved: { zh: '已分流', en: 'Routed' },
  discarded: { zh: '已废弃', en: 'Discarded' },
};

export function getStatusLocale(status: string, locale: string): string {
  const entry = STATUS_LOCALES[status];
  if (!entry) return status;
  return locale === 'en' ? entry.en : entry.zh;
}

// 状态码可在不同事实对象中复用，但展示语义不必相同。Spark 的 `open`
// 表示「尚待判断或分流」，不是 WorkCase 式的「未关闭」。
const OBJECT_STATUS_LOCALES: Record<string, Record<string, { zh: string; en: string }>> = {
  spark: {
    open: { zh: '待处理', en: 'Pending' },
  },
};

export function getObjectStatusLocale(type: string, status: string, locale: string): string {
  const objectEntry = OBJECT_STATUS_LOCALES[type]?.[status];
  if (objectEntry) return locale === 'en' ? objectEntry.en : objectEntry.zh;
  return getStatusLocale(status, locale);
}

export const TYPE_DESCRIPTION_LOCALES: Record<string, { zh: string; en: string }> = {
  workcase: { zh: '人机编排和关闭判断的工作', en: 'WorkCase for orchestration and closure' },
  adr: { zh: '决策记录', en: 'Architecture Decision Record' },
  pitfall: { zh: '可复用经验', en: 'Reusable pitfalls' },
  spark: { zh: '待分流的火花', en: 'Spark pending routing' },
  study: { zh: '研究', en: 'Study' },
  change: { zh: '提交', en: 'Commit' },
};

export function getTypeDescription(type: string, locale: string): string {
  const entry = TYPE_DESCRIPTION_LOCALES[type];
  if (!entry) return '';
  return locale === 'en' ? entry.en : entry.zh;
}

// ============================================================
// 对象类型 / 字段名 / 字段枚举值 中英映射（显式 mapping 表）
// 来源：docs/01-全局设计约束 §1.3 — 字段名与枚举值必须经显式映射本地化
// 这些表集中维护于此，组件经下方 get*Label 函数读取，
// 不得在组件内用 locale === 'en' ? ... : ... 内联分支。
// ============================================================

/** 对象类型中英映射 */
export const TYPE_LOCALES: Record<string, { zh: string; en: string }> = {
  workcase: { zh: '工作', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  pitfall: { zh: '经验', en: 'Pitfall' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '研究', en: 'Study' },
  change: { zh: '提交', en: 'Commit' },
};

export function getTypeLabel(type: string, locale: string): string {
  const entry = TYPE_LOCALES[type];
  if (!entry) return type;
  return locale === 'en' ? entry.en : entry.zh;
}

export function getLocalizedObjectTitle(
  item: { id?: string; title?: string; title_en?: string; title_zh?: string },
  locale: string,
  fallback = '—',
): string {
  if (locale === 'en') return item.title_en || item.title || item.id || fallback;
  return item.title_zh || item.title || item.title_en || item.id || fallback;
}

export function getLocaleListSeparator(locale: string): string {
  return locale === 'zh' ? '，' : ', ';
}

export function getOppositeLocale(locale: Locale): Locale {
  return locale === 'zh' ? 'en' : 'zh';
}

export function getLanguageSwitchKey(locale: Locale): 'language.switchToEnglish' | 'language.switchToChinese' {
  return locale === 'zh' ? 'language.switchToEnglish' : 'language.switchToChinese';
}

export function getOppositeLanguageNameKey(locale: Locale): 'language.english' | 'language.chinese' {
  return locale === 'zh' ? 'language.english' : 'language.chinese';
}

/** 字段名中英映射 */
export const FIELD_LABEL_LOCALES: Record<string, { zh: string; en: string }> = {
  id: { zh: 'ID', en: 'ID' },
  type: { zh: '类型', en: 'Type' },
  title: { zh: '标题', en: 'Title' },
  title_en: { zh: '英文标题', en: 'English Title' },
  title_zh: { zh: '中文标题', en: 'Chinese Title' },
  status: { zh: '状态', en: 'Status' },
  created: { zh: '创建时间', en: 'Created' },
  updated: { zh: '更新时间', en: 'Updated' },
  date: { zh: '日期', en: 'Date' },
  source: { zh: '来源', en: 'Source' },
  source_detail: { zh: '来源说明', en: 'Source Detail' },
  relations: { zh: '事实对象关系', en: 'Fact Relations' },
  associated_materials: { zh: '关联材料', en: 'Associated Materials' },
  fact_associations: { zh: '关联', en: 'Related' },
  fact_relations: { zh: '事实对象关系', en: 'Fact Relations' },
  project_materials: { zh: '项目内材料', en: 'Project Materials' },
  external_inputs: { zh: '外部资料与输入', en: 'External Sources and Inputs' },
  evidence_materials: { zh: '证据材料', en: 'Evidence Materials' },
  associated_documents: { zh: '文档', en: 'Docs' },
unresolved_materials: { zh: '未解析材料', en: 'Unresolved Materials' },
  relation_routed_to: { zh: '分流到', en: 'Routed To' },
  relation_related_to: { zh: '关联到', en: 'Related To' },
  relation_depends_on: { zh: '依赖', en: 'Depends On' },
  user_intent: { zh: '用户意图', en: 'User Intent' },
  description: { zh: '描述', en: 'Description' },
  evolution: { zh: '演变记录', en: 'Evolution' },
  routing: { zh: '分流', en: 'Routing' },
  disposition_summary: { zh: '处置说明', en: 'Disposition' },
  research_question: { zh: '研究问题', en: 'Research Question' },
  research_intent: { zh: '意图', en: 'Intent' },
  abstract: { zh: '摘要', en: 'Abstract' },
  recommendation_summary: { zh: '建议', en: 'Recommendation' },
  validation_summary: { zh: '验证总结', en: 'Validation Summary' },
  body: { zh: '正文', en: 'Body' },
  report_body: { zh: '正文', en: 'Body' },
  summary: { zh: '摘要', en: 'Summary' },
  conclusion: { zh: '结论', en: 'Conclusion' },
  details: { zh: '详情', en: 'Details' },
  background: { zh: '背景', en: 'Background' },
  motivation: { zh: '动机', en: 'Motivation' },
  outcome: { zh: '结果', en: 'Outcome' },
  next_steps: { zh: '后续步骤', en: 'Next Steps' },
  lessons: { zh: '经验教训', en: 'Lessons' },
  success_criteria: { zh: '成功标准', en: 'Success Criteria' },
  constraints: { zh: '约束', en: 'Constraints' },
  acceptance: { zh: '验收标准', en: 'Acceptance' },
  verification: { zh: '验证', en: 'Verification' },
  notes: { zh: '备注', en: 'Notes' },
  symptoms: { zh: '问题现象', en: 'Symptoms' },
  trigger_conditions: { zh: '触发条件', en: 'Trigger Conditions' },
  root_cause: { zh: '根因', en: 'Root Cause' },
  avoidance: { zh: '规避策略', en: 'Avoidance' },
  applicability: { zh: '适用范围', en: 'Applicability' },
  archive_reason: { zh: '归档原因', en: 'Archive Reason' },
  rationale: { zh: '理由', en: 'Rationale' },
  decision_question: { zh: '决策问题', en: 'Decision Question' },
  context: { zh: '背景', en: 'Context' },
  consequences: { zh: '影响', en: 'Consequences' },
  observation: { zh: '观察', en: 'Observation' },
  analysis: { zh: '分析', en: 'Analysis' },
  mitigation: { zh: '缓解措施', en: 'Mitigation' },
  resolution: { zh: '解决方案', en: 'Resolution' },
  workcase: { zh: '工作', en: 'WorkCase' },
  orchestration: { zh: '编排', en: 'Orchestration' },
  execution_items: { zh: '执行项', en: 'Execution Items' },
  mode: { zh: '模式', en: 'Mode' },
  role: { zh: '角色', en: 'Role' },
  input_refs: { zh: '输入引用', en: 'Input Refs' },
  expected_output: { zh: '期望输出', en: 'Expected Output' },
  result_summary: { zh: '结果摘要', en: 'Result Summary' },
  blocking_reason: { zh: '阻塞原因', en: 'Blocking Reason' },
  closure_evidence: { zh: '关闭证据', en: 'Closure Evidence' },
  verification_evidence: { zh: '验证证据', en: 'Verification Evidence' },
  review_requested_at: { zh: '请求关闭确认时间', en: 'Review Requested At' },
  plan_confirmed_at: { zh: '方案确认时间', en: 'Plan Confirmed At' },
  closure_requested_at: { zh: '关闭确认请求时间', en: 'Closure Requested At' },
  closure_outcome: { zh: '关闭结果', en: 'Closure Outcome' },
  residual_responsibilities: { zh: '未完成事项与去向', en: 'Residual Responsibilities' },
  nonbinding_followups: { zh: '非约束后续建议', en: 'Non-binding Follow-ups' },
  revision_history: { zh: '修订记录', en: 'Revision History' },
  transition_reasons: { zh: '流转记录', en: 'Transition Reasons' },
  options: { zh: '选项', en: 'Options' },
  decision: { zh: '决策', en: 'Decision' },
  related_workcases: { zh: '关联工作', en: 'Related Work Cases' },
  related_adrs: { zh: '关联决策', en: 'Related ADRs' },
  related_sparks: { zh: '关联火花', en: 'Related Sparks' },
  related_studies: { zh: '关联研究', en: 'Related Studies' },
  related_pitfalls: { zh: '关联经验', en: 'Related Pitfalls' },
  source_objects: { zh: '来源对象', en: 'Source Objects' },
  related_objects: { zh: '关联对象', en: 'Related Objects' },
  source_sparks: { zh: '来源火花', en: 'Source Sparks' },
  resolved_to: { zh: '分流目标', en: 'Routed To' },
  resolved_at: { zh: '分流时间', en: 'Routed At' },
  discard_reason: { zh: '废弃原因', en: 'Discard Reason' },
  deprecated_reason: { zh: '废弃原因', en: 'Deprecated Reason' },
  aggregated_execution_refs: { zh: '执行引用', en: 'Execution Refs' },
  scope: { zh: '范围', en: 'Scope' },
  impact: { zh: '影响范围', en: 'Impact' },
  category: { zh: '分类', en: 'Category' },
  priority: { zh: '优先级', en: 'Priority' },
  importance: { zh: '重要程度', en: 'Importance' },
  assignee: { zh: '执行者', en: 'Assignee' },
  tags: { zh: '标签', en: 'Tags' },
  path: { zh: '路径', en: 'Path' },
  project_name: { zh: '项目名称', en: 'Project Name' },
  project_kind: { zh: '项目类型', en: 'Project Kind' },
  project_path: { zh: '项目路径', en: 'Project Path' },
  ldvh_base_path: { zh: '事实实例路径', en: 'LDVH Base Path' },
  docs_path: { zh: '文档路径', en: 'Docs Path' },
  governance_scope: { zh: '管辖范围', en: 'Governance Scope' },
  language: { zh: '语言', en: 'Language' },
  framework: { zh: '框架', en: 'Framework' },
  related_rules: { zh: '规范', en: 'Specs' },
  urls: { zh: '网址', en: 'URLs' },
  related_docs: { zh: '关联文档', en: 'Related Docs' },
  aggregated_related_docs: { zh: '聚合关联文档', en: 'Aggregated Related Docs' },
  aggregated_related_adrs: { zh: '聚合关联决策', en: 'Aggregated Related ADRs' },
  aggregated_related_sparks: { zh: '聚合关联火花', en: 'Aggregated Related Sparks' },
  aggregated_related_pitfalls: { zh: '聚合关联经验', en: 'Aggregated Related Pitfalls' },
  at: { zh: '时间', en: 'At' },
  from: { zh: '前状态', en: 'From' },
  to: { zh: '后状态', en: 'To' },
  actor: { zh: '执行者', en: 'Actor' },
  reason: { zh: '原因', en: 'Reason' },
};

export function getFieldLabel(fieldKey: string, locale: string): string {
  const entry = FIELD_LABEL_LOCALES[fieldKey];
  if (!entry) return fieldKey.replace(/_/g, ' ');
  return locale === 'en' ? entry.en : entry.zh;
}

/** 字段枚举值中英映射 */
export const FIELD_VALUE_LOCALES: Record<string, Record<string, { zh: string; en: string }>> = {
  category: {
    question: { zh: '问题', en: 'Question' },
    discovery: { zh: '发现', en: 'Discovery' },
    gap: { zh: '缺口', en: 'Gap' },
    reminder: { zh: '提醒', en: 'Reminder' },
    preference: { zh: '偏好', en: 'Preference' },
  },
  priority: {
    P0: { zh: 'P0', en: 'P0' },
    P1: { zh: 'P1', en: 'P1' },
    P2: { zh: 'P2', en: 'P2' },
    P3: { zh: 'P3', en: 'P3' },
  },
  importance: {
    high: { zh: '高', en: 'High' },
    medium: { zh: '中', en: 'Medium' },
    low: { zh: '低', en: 'Low' },
  },
};

export function getFieldValueLabel(fieldKey: string, value: string, locale: string): string {
  const entry = FIELD_VALUE_LOCALES[fieldKey]?.[value];
  if (!entry) return value;
  return locale === 'en' ? entry.en : entry.zh;
}

const PROJECT_FILE_KIND_LOCALES: Record<string, { zh: string; en: string }> = {
  directory: { zh: '目录', en: 'Directory' },
  markdown: { zh: 'Markdown', en: 'Markdown' },
  yaml: { zh: 'YAML', en: 'YAML' },
  svg: { zh: 'SVG', en: 'SVG' },
  text: { zh: '文本', en: 'Text' },
  binary: { zh: '二进制', en: 'Binary' },
};

const GIT_STATUS_LOCALES: Record<string, { zh: string; en: string }> = {
  '??': { zh: '未跟踪', en: 'Untracked' },
  M: { zh: '已修改', en: 'Modified' },
  A: { zh: '新增', en: 'Added' },
  D: { zh: '删除', en: 'Deleted' },
  R: { zh: '重命名', en: 'Renamed' },
  C: { zh: '复制', en: 'Copied' },
  U: { zh: '冲突', en: 'Conflict' },
};

export function getProjectFileKindLabel(kind: string, locale: string): string {
  const entry = PROJECT_FILE_KIND_LOCALES[kind];
  if (!entry) return kind;
  return locale === 'en' ? entry.en : entry.zh;
}

export function getGitStatusLabel(status: string, locale: string): string {
  const trimmed = status.trim();
  const key = trimmed === '??' ? '??' : trimmed.replace(/\s/g, '').charAt(0);
  const entry = GIT_STATUS_LOCALES[key];
  if (!entry) return status;
  return locale === 'en' ? entry.en : entry.zh;
}

export function getToggleLabel(title: string, nextState: 'collapsed' | 'expanded', locale: string): string {
  const action = nextState === 'collapsed'
    ? (locale === 'en' ? 'Collapse' : '收拢')
    : (locale === 'en' ? 'Expand' : '展开');
  return locale === 'en' ? `${action} ${title}` : `${action}${title}`;
}

export type CommitDetailLabels = {
  category: string;
  type: string;
  scope: string;
  commit: string;
  time: string;
  summary: string;
  files: string;
  insertions: string;
  deletions: string;
  commitBody: string;
  changedFiles: string;
  noFiles: string;
  raw: string;
  copyHash: string;
  copiedHash: string;
};

const COMMIT_DETAIL_LABELS: Record<string, CommitDetailLabels> = {
  zh: {
    category: '分类', type: '类型', scope: '范围', commit: '提交', time: '提交',
    summary: '变更统计', files: '文件', insertions: '新增', deletions: '删除',
    commitBody: '关键变更', changedFiles: '改动文件', noFiles: '没有可展示的文件统计',
    raw: '原始信息', copyHash: '复制提交 hash', copiedHash: '已复制提交 hash',
  },
  en: {
    category: 'Category', type: 'Type', scope: 'Scope', commit: 'Commit', time: 'Commit',
    summary: 'Change summary', files: 'Files', insertions: 'Insertions', deletions: 'Deletions',
    commitBody: 'Commit notes', changedFiles: 'Changed files', noFiles: 'No file stat available',
    raw: 'Original info', copyHash: 'Copy commit hash', copiedHash: 'Commit hash copied',
  },
};

export function getCommitDetailLabels(locale: string): CommitDetailLabels {
  return COMMIT_DETAIL_LABELS[locale === 'en' ? 'en' : 'zh'];
}

const CATEGORY_LABEL_LOCALES: Record<string, { zh: string; en: string }> = {
  feat: { zh: '功能', en: 'Feature' }, fix: { zh: '修复', en: 'Fix' },
  docs: { zh: '文档', en: 'Docs' }, style: { zh: '样式', en: 'Style' },
  refactor: { zh: '重构', en: 'Refactor' }, test: { zh: '测试', en: 'Test' },
  chore: { zh: '杂项', en: 'Chore' }, perf: { zh: '性能', en: 'Perf' },
  ci: { zh: 'CI', en: 'CI' }, build: { zh: '构建', en: 'Build' },
  spec: { zh: '规范', en: 'Spec' }, rule: { zh: '规则', en: 'Rule' },
  adr: { zh: '决策', en: 'ADR' }, other: { zh: '其他', en: 'Other' },
};

const COMMIT_TYPE_ZH: Record<string, string> = {
  feat: '新增功能', fix: '问题修复', docs: '文档修改', style: '格式调整',
  refactor: '代码重构', perf: '性能优化', test: '测试修改', build: '构建系统',
  ci: '持续集成', chore: '维护杂项', revert: '回退变更',
};

const COMMIT_SCOPE_LOCALES: Record<string, { zh: string; en: string }> = {
  specs: { zh: 'Specs', en: 'Specs' }, docs: { zh: '文档', en: 'Docs' },
  rules: { zh: '规则', en: 'Rules' }, runtime: { zh: '运行时', en: 'Runtime' },
  code: { zh: 'Code', en: 'Code' }, web: { zh: 'Web', en: 'Web' },
  tests: { zh: 'Tests', en: 'Tests' }, config: { zh: '配置', en: 'Config' },
  workcase: { zh: '工作', en: 'WorkCase' }, adr: { zh: '决策', en: 'ADR' },
  spark: { zh: '火花', en: 'Spark' }, study: { zh: '研究', en: 'Study' },
  pitfall: { zh: '经验', en: 'Pitfall' },
};

export function getCategoryLabel(category: string, locale: string): string {
  const entry = CATEGORY_LABEL_LOCALES[category];
  if (!entry) return category;
  return locale === 'en' ? entry.en : entry.zh;
}

export function getCommitTypeLocale(type: string | undefined, locale: string): string {
  if (!type) return '';
  return locale === 'en' ? type : (COMMIT_TYPE_ZH[type] ?? type);
}

export function getCommitScopeLocale(scope: string | undefined, locale: string): string {
  if (!scope) return '';
  const entry = COMMIT_SCOPE_LOCALES[scope];
  if (!entry) return scope;
  return locale === 'en' ? entry.en : entry.zh;
}

export const STATUS_HINT_LOCALES: Record<string, { zh: string; en: string }> = {
  planned: { zh: '等待执行', en: 'Waiting to start' },
  active: { zh: '进行中', en: 'In progress' },
  in_progress: { zh: '进行中', en: 'In progress' },
  blocked: { zh: '已阻塞', en: 'Blocked' },
  executing: { zh: '执行中', en: 'Executing' },
  verifying: { zh: '验证中', en: 'Verifying' },
  review_needed: { zh: '待后续处理', en: 'Needs follow-up' },
  human_plan_confirming: { zh: '等待 Human 确认方案', en: 'Waiting for human plan confirmation' },
  result_self_checking: { zh: '主控正在自检执行结果', en: 'Controller is checking the result' },
  subagents_result_reviewing: { zh: '结果正在由第三方复核', en: 'Result is under specialist review' },
  human_closure_confirming: { zh: '等待 Human 确认关闭', en: 'Waiting for human closure confirmation' },
  plan_confirmation: { zh: '等待 Human 确认方案', en: 'Waiting for human plan confirmation' },
  progressing: { zh: '工作正在推进', en: 'Work is progressing' },
  closure_confirmation: { zh: '等待 Human 确认关闭', en: 'Waiting for human closure confirmation' },
  draft: { zh: '草稿中', en: 'In draft' },
  pending: { zh: '待分流处理', en: 'Pending routing' },
  proposed: { zh: '提案中', en: 'Proposed' },
  closed: { zh: '已关闭', en: 'Closed' },
};

export function getStatusHint(status: string, locale: string): string {
  const entry = STATUS_HINT_LOCALES[status];
  if (!entry) return '';
  return locale === 'en' ? entry.en : entry.zh;
}

export function getObjectStatusHint(type: string, status: string, locale: string): string {
  if (type === 'adr' && status === 'active') {
    return locale === 'en'
      ? 'Current effective decision patch'
      : '当前有效的决策补丁';
  }
  if (status === 'review_needed') {
    if (type === 'workcase') {
      return locale === 'en'
        ? 'Verification and closure evidence are ready; confirm whether this WorkCase can close.'
        : '验证证据和关闭证据已就绪，待确认工作是否可关闭';
    }
  }
  return getStatusHint(status, locale);
}

export const UI_LOCALES = {
  zh: {
    'logo.tagline': '让 Vibe Coding 更高效、更稳定、更可控',

    'nav.dashboard': '仪表盘',
    'nav.projectFiles': '文件',
    'nav.workcases': '工作',
    'nav.adrs': '决策',
    'nav.pitfalls': '经验',
    'nav.sparks': '火花',
    'nav.studies': '研究',
    'nav.changes': '提交',
    'nav.changelog': '提交',
    'nav.collapseSidebar': '收起侧栏',
    'nav.expandSidebar': '展开侧栏',
    'theme.system': '跟随系统',
    'theme.light': '浅色模式',
    'theme.dark': '深色模式',
    'language.switchToEnglish': '切换到英文',
    'language.switchToChinese': '切换到中文',
    'language.english': 'English',
    'language.chinese': '中文',

    'dashboard.title': '仪表盘',
    'dashboard.recentActivity': '最近活动',
    'dashboard.recentChanges': '最近提交',
    'dashboard.noRecentActivity': '暂无最近活动',
    'dashboard.noRecentChanges': '暂无最近提交',
    'dashboard.noActionItems': '所有事项已完成',
    'dashboard.actionItems': '待推进',
    'dashboard.summary.executing': '{count} 个执行项运行中',
    'dashboard.summary.verifying': '{count} 个验证中',
    'dashboard.summary.reviewNeeded': '{count} 个待处理',
    'dashboard.summary.planned': '{count} 个计划中',
    'dashboard.summary.planConfirming': '{count} 个方案待确认',
    'dashboard.summary.progressing': '{count} 个推进中',
    'dashboard.summary.resultReview': '{count} 个结果复核中',
    'dashboard.summary.closureConfirming': '{count} 个关闭待确认',

    'objectList.noObjects': '未找到 {type} 对象',
    'objectList.typeNotIntegrated': '该事实类型尚未接入',
    'objectList.all': '全部',
    'objectList.statusFilter': '状态筛选',
    'objectList.lifecycleFilter': '生命周期',
    'objectList.progressGroupFilter': '进展分组',
    'objectList.priorityFilter': '优先级',
    'objectList.priorityNotApplicable': '终态对象不适用优先级。',
    'objectList.relatedPlans': '关联工作',
    'objectList.planCount': '{count} 个工作',
    'objectList.activePlanCount': '活跃工作',
    'objectList.humanConfirmPlanCount': '待确认工作',
    'objectList.closedPlanCount': '已闭合工作',
    'objectList.closeDecision': '关闭判断',
    'objectList.closureIssue': '收口异常',
    'objectList.planExecutionQueue': '执行队列',
    'objectList.planExecutionItems': '执行项',
    'objectList.executionItemCount': '{count} 个执行项',
    'objectList.planExecutionRisk': '风险',
    'objectList.executionFlowPending': '待执行',
    'objectList.executionFlowInProgress': '执行中',
    'objectList.executionFlowBlocked': '已阻塞',
    'objectList.executionFlowDone': '已完成',
    'objectList.executionFlowSkipped': '已跳过',
    'objectList.executionFlowRisk': '异常',
    'objectList.executionFlowOther': '其他',
    'objectList.executionFlowCount': '{status} {count} 个',
    'objectList.executionFlowLegend': '执行项态势图例',
    'objectList.activeCount': '{count} 进行中',
    'objectList.reviewCount': '{count} 待关闭',
    'objectList.riskCount': '{count} 有风险',
    'objectList.noPlans': '暂无关联工作',
    'objectList.noExecutionItems': '暂无执行项',
    'objectList.morePlans': '还有 {count} 个工作',
    'objectList.moreExecutionItems': '还有 {count} 个执行项',
    'objectList.successCriteria': '成功标准',
    'objectList.planConfirmedAt': '方案确认',
    'objectList.reviewRequestedAt': '请求确认',
    'objectList.closureRequestedAt': '请求关闭',
    'objectList.completionEvidence': '完成证据',
    'objectList.verificationEvidence': '验证证据',
    'objectList.closureEvidence': '关闭证据',
    'objectList.hasRecord': '已记录',
    'objectList.missingRecord': '未完成',
    'objectList.archiveReason': '归档原因',
    'objectList.deprecatedReason': '废弃原因',
    'objectList.discardReason': '废弃原因',
    'objectList.disposition': '处置说明',
    'objectList.closeReason': '关闭原因',
    'objectList.missingReason': '原因缺失',
    'objectList.missingReasonText': '该非活跃对象必须在事实源中记录原因。',
    'objectList.updated': '更新 {time}',
    'objectList.noRouteTarget': '未记录事实对象目标',
    'objectList.routed': '已分流',
    'objectList.target': '目标',
    'objectList.time': '时间',
    'objectList.dispositionMissing': '处置说明缺失。',
    'objectList.discarded': '已废弃',
    'objectList.reason': '原因',
    'objectList.workcaseStateDynamic': '正在推进',
    'objectList.workcaseStateWaiting': '等待 Human 处理',
    'objectList.workcaseStateClosed': '工作已关闭',
    'objectList.workcaseProgressUnavailable': '进展信息不可判定',
    'objectList.workcaseGoal': '目标',
    'objectList.workcaseCurrentProgress': '当前进展',
    'objectList.workcaseBlockingReason': '阻塞原因',
    'objectList.workcaseRoundFull': '第 {round} 轮',
    'objectList.workcaseRoundPartial': '自记录起第 {round} 轮',
    'objectList.workcaseRoundMissing': '轮次未记录',
    'objectList.workcaseRoundInvalid': '轮次不可判定',
    'objectList.workcaseItemProgress': '已完成 {done}/{total}',
    'objectList.workcaseItemsCancelled': '另有 {count} 项取消',
    'objectList.workcaseCurrentItems': '当前工作项',
    'objectList.workcaseNoCurrentItems': '当前无执行中工作项',
    'objectList.workcaseCriteriaCount': '{count} 项',
    'objectList.workcaseFieldMissing': '未记录',
    'objectList.workcaseDynamicStages': '推进环节',
    'objectList.workcaseStageExecute': '工作项执行',
    'objectList.workcaseStageSelfCheck': '主控自检',
    'objectList.workcaseStageResultReview': '独立复核',
    'objectList.workcaseStageSynthesis': '主控收敛',

    'objectDetail.back': '返回',
    'objectDetail.content': '内容',
    'objectDetail.yamlSource': 'YAML 源码',
    'objectDetail.id': 'ID',
    'objectDetail.type': '类型',
    'objectDetail.status': '状态',
    'objectDetail.created': '创建时间',
    'objectDetail.updated': '更新时间',
    'objectDetail.createdShort': '创建',
    'objectDetail.updatedShort': '更新',
    'objectDetail.expand': '展开',
    'objectDetail.collapse': '收起',
    'objectDetail.aggregatedDeliverables': '聚合产出',
    'objectDetail.aggregatedDocs': '聚合文档',
    'objectDetail.editStatus': '点击修改状态',
    'objectDetail.editAcceptance': '点击编辑验收标准',
    'objectDetail.goal': '目标',
    'objectDetail.noDescription': '未记录描述',
    'objectDetail.workPlan': '所属工作',
    'objectDetail.executionStatus': '执行状态',
    'objectDetail.currentState': '当前状态',
    'objectDetail.waitingFor': '等待对象',
    'objectDetail.acceptance': '验收标准',
    'objectDetail.verification': '验证方式',
    'objectDetail.verificationEvidence': '验证证据',
    'objectDetail.closureEvidence': '关闭证据',
    'objectDetail.noAcceptance': '未记录验收标准',
    'objectDetail.noVerification': '未记录验证方式',
    'objectDetail.noClosureEvidence': '尚未记录关闭证据',
    'objectDetail.relatedDocs': '关联文档',
    'objectDetail.related': '关联',
    'objectDetail.affectedDocs': '影响文档',
    'objectDetail.dependencies': '前置依赖',
    'objectDetail.otherFields': '其他字段',
    'objectDetail.emptyValue': '空',
    'objectDetail.planGoal': '工作目标',
    'objectDetail.planDescription': '工作描述',
    'objectDetail.noPlanGoal': '未记录工作目标',
    'objectDetail.noPlanDescription': '未记录工作描述',
    'objectDetail.planExecution': '执行队列',
    'objectDetail.workcaseProgress': '工作进度',
    'objectDetail.workcaseCloseout': '收口与未完成事项',
    'objectDetail.noWorkcaseCloseout': '尚未形成收口记录',
    'objectDetail.workcaseHumanOverview': '工作总览',
    'objectDetail.workcaseHumanContext': 'Human 视图',
    'objectDetail.workcaseAiContext': 'AI 上下文',
    'objectDetail.workcaseAiCore': '核心上下文',
    'objectDetail.workcaseAiReviewContext': '审核上下文',
    'objectDetail.executionReferences': '执行引用',
    'objectDetail.lifecycleStage': '推进阶段',
    'objectDetail.lifecycleDraft': '目标确认',
    'objectDetail.lifecyclePlanConfirming': '方案确认',
    'objectDetail.lifecycleActive': '执行中',
    'objectDetail.lifecycleBlocked': '阻塞处理',
    'objectDetail.lifecycleVerification': '验证整理',
    'objectDetail.lifecycleResultReview': '结果复核',
    'objectDetail.lifecycleReview': '关闭审查',
    'objectDetail.lifecycleClosed': '已关闭',
    'objectDetail.successCriteriaProgress': '成功标准',
    'objectDetail.executionItemProgress': '执行项',
    'objectDetail.workcaseExecution': '执行项',
    'objectDetail.executionItemsLoading': '正在读取执行项态势',
    'objectDetail.workcaseReview': '检查安排',
    'objectDetail.planReview': '方案审核',
    'objectDetail.resultReview': '结果复核',
    'objectDetail.reviewPolicy': '审核策略',
    'objectDetail.reviewItems': '审核条目',
    'objectDetail.controllerResolution': '主控处理',
    'objectDetail.humanPlanConfirmation': '方案确认',
    'objectDetail.humanClosureConfirmation': '关闭确认',
    'objectDetail.reviewConclusion': '结论',
    'objectDetail.controllerSelfCheck': '主控自检',
    'objectDetail.specialistReview': '专业复检',
    'objectDetail.humanClosureReview': '关闭审查',
    'objectDetail.reviewRequirement': '要求',
    'objectDetail.required': '需要',
    'objectDetail.notRequired': '不需要',
    'objectDetail.reviewRole': '角色',
    'objectDetail.expectedOutput': '预期输出',
    'objectDetail.noSuccessCriteria': '未记录成功标准',
    'objectDetail.planCloseReview': '关闭判断',
    'objectDetail.closeDecisionReady': '满足关闭条件',
    'objectDetail.closeDecisionReadyHint': '成功标准和完成证据均已确认。',
    'objectDetail.closeDecisionPending': '关闭条件尚未满足',
    'objectDetail.closeDecisionPendingHint': '仍有成功标准或完成证据需要确认，不能直接视为可关闭。',
    'objectDetail.closeDecisionPendingItems': '待确认项',
    'objectDetail.closeDecisionNoPendingItems': '暂无待确认项',
    'objectDetail.closeDecisionRecordState': '记录状态',
    'objectDetail.noCompletionEvidence': '尚未记录完成证据',
    'objectDetail.noVerificationEvidence': '尚未记录验证证据',
    'objectDetail.noClosureEvidenceForWorkCase': '尚未记录关闭证据',
    'objectDetail.planMaterials': '产出与文档',
    'objectDetail.relatedMaterials': '关联材料',

    'projectFiles.title': '项目文件',
    'projectFiles.subtitle': '按 LDVH 管辖项目浏览文件，预览 Markdown，并只读查看当前 Git 待提交差异。',
    'projectFiles.project': '管辖项目',
    'projectFiles.quickRoots': '常用目录',
    'projectFiles.showHiddenFiles': '显示隐藏文件',
    'projectFiles.filesTab': '文件浏览',
    'projectFiles.changesTab': '待提交文件',
    'projectFiles.historyTab': '提交历史',
    'projectFiles.fileBrowser': '项目文件浏览',
    'projectFiles.preview': '文件预览',
    'projectFiles.pending': '待提交文件',
    'projectFiles.history': '提交历史',
    'projectFiles.changeDetail': '差异详情',
    'projectFiles.selectedCommitFiles': '当前提交文件',
    'projectFiles.diff': '文件差异',
    'projectFiles.diffMode': '差异显示方式',
    'projectFiles.unifiedDiff': '统一',
    'projectFiles.splitDiff': '分栏',
    'projectFiles.reload': '刷新',
    'projectFiles.loading': '加载中',
    'projectFiles.noProjects': '没有读取到管辖项目。',
    'projectFiles.noEntries': '当前目录没有可展示文件。',
    'projectFiles.chooseFile': '选择左侧文件后在这里阅读。',
    'projectFiles.chooseDiff': '选择待提交文件后在这里查看差异。',
    'projectFiles.chooseCommit': '选择左侧提交后查看详情。',
    'projectFiles.chooseCommitFile': '选择改动文件后查看该提交中的差异。',
    'projectFiles.noChanges': '当前项目没有待提交文件。',
    'projectFiles.noCommits': '当前项目没有提交历史。',
    'projectFiles.mergeCommit': '合并提交',
    'projectFiles.binary': '这是二进制文件，Web 仅展示路径和大小。',
    'projectFiles.truncated': '内容已按安全上限截断。',
    'projectFiles.readOnly': '只读',
    'projectFiles.root': '项目根目录',
    'projectFiles.docs': 'docs',
    'projectFiles.ldvhBase': 'LDVH Base',
    'projectFiles.view': '视图',
    'projectFiles.viewAria': '项目文件视图',
    'projectFiles.before': '旧内容',
    'projectFiles.after': '新内容',

    'readingPanel.truncated': '内容已截断',
    'readingPanel.close': '关闭',
    'readingPanel.title': '扩展阅读',
    'readingPanel.previous': '上一个访问对象',
    'readingPanel.next': '下一个访问对象',
    'readingPanel.empty': '选择一个对象或文档以在此预览',
    'readingPanel.loadFailed': '加载失败',
    'readingPanel.docLoadFailed': '文档加载失败',
    'readingPanel.noEvidence': '暂无证据信息',
    'readingPanel.changeDetail': '提交详情',
    'readingPanel.openNewTab': '新标签',
    'objectDetail.humanGateTip': '此工作待关闭审查',
    'objectDetail.openReadingPanel': '扩展阅读',
    'objectDetail.reportBody': '报告正文',
    'objectDetail.readUnavailable': '无法读取对象',
    'objectDetail.readType': '对象',
    'objectDetail.readStatus': '读取状态',
    'objectDetail.expectedPath': '预期位置',
    'objectDetail.readIssue': '读取问题',

    'changelog.allTypes': '全部类型',
    'changelog.allScopes': '全部范围',
    'changelog.recentCount': '最近 {count}',
    'changelog.noMatches': '没有匹配的提交',
    'changelog.copyContext': '复制提交上下文',
    'changelog.copiedContext': '已复制提交上下文',
    'changelog.loadFailed': '加载提交失败',
    'changelog.detailFailed': '加载提交详情失败',
    'changelog.closeDetails': '收起详情',
    'changelog.openDetails': '展开详情',
    'changelog.commitAt': '提交 {time}',

    'common.loading': '加载中...',
    'common.loadFailed': '加载失败',
    'common.language': '语言',
    'common.true': '是',
    'common.false': '否',
    'common.empty': '空',
    'common.null': '—',
    'common.copyPath': '复制路径',
    'common.copiedPath': '已复制路径',
    'common.copyObjectPath': '复制对象路径',
    'common.copiedObjectPath': '已复制对象路径',
    'common.copyDocPath': '复制文档路径',
    'common.copiedDocPath': '已复制文档路径',
    'common.copyUrl': '复制链接',
    'common.copiedUrl': '已复制链接',
    'common.copyReference': '复制引用',
    'common.copiedReference': '已复制引用',
    'common.read': '阅读',
  },
  en: {
    'logo.tagline': 'Making Vibe Coding more efficient, stable, and controllable',

    'nav.dashboard': 'Dashboard',
    'nav.projectFiles': 'Files',
    'nav.workcases': 'Work Cases',
    'nav.adrs': 'ADRs',
    'nav.pitfalls': 'Pitfalls',
    'nav.sparks': 'Sparks',
    'nav.studies': 'External studies',
    'nav.changes': 'Commit Records',
    'nav.changelog': 'Commit Records',
    'nav.collapseSidebar': 'Collapse sidebar',
    'nav.expandSidebar': 'Expand sidebar',
    'theme.system': 'System theme',
    'theme.light': 'Light mode',
    'theme.dark': 'Dark mode',
    'language.switchToEnglish': 'Switch to English',
    'language.switchToChinese': 'Switch to Chinese',
    'language.english': 'English',
    'language.chinese': '中文',

    'dashboard.title': 'Dashboard',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.recentChanges': 'Recent Commits',
    'dashboard.noRecentActivity': 'No recent activity',
    'dashboard.noRecentChanges': 'No recent commits',
    'dashboard.noActionItems': 'All items completed',
    'dashboard.actionItems': 'Action Items',
    'dashboard.summary.executing': '{count} execution items running',
    'dashboard.summary.verifying': '{count} verifying',
    'dashboard.summary.reviewNeeded': '{count} need follow-up',
    'dashboard.summary.planned': '{count} planned',
    'dashboard.summary.planConfirming': '{count} awaiting plan confirmation',
    'dashboard.summary.progressing': '{count} progressing',
    'dashboard.summary.resultReview': '{count} in result review',
    'dashboard.summary.closureConfirming': '{count} awaiting closure confirmation',

    'objectList.noObjects': 'No {type} found',
    'objectList.typeNotIntegrated': 'This fact type is not integrated',
    'objectList.all': 'All',
    'objectList.statusFilter': 'Status filter',
    'objectList.lifecycleFilter': 'Lifecycle',
    'objectList.progressGroupFilter': 'Progress group',
    'objectList.priorityFilter': 'Priority',
    'objectList.priorityNotApplicable': 'Priority does not apply to terminal objects.',
    'objectList.relatedPlans': 'Related WorkCases',
    'objectList.planCount': '{count} WorkCases',
    'objectList.activePlanCount': 'Active WorkCases',
    'objectList.humanConfirmPlanCount': 'WorkCases awaiting confirmation',
    'objectList.closedPlanCount': 'Closed WorkCases',
    'objectList.closeDecision': 'Close Decision',
    'objectList.closureIssue': 'Closure Issue',
    'objectList.planExecutionQueue': 'Execution Queue',
    'objectList.planExecutionItems': 'Execution Items',
    'objectList.executionItemCount': '{count} execution items',
    'objectList.planExecutionRisk': 'Risk',
    'objectList.executionFlowPending': 'Pending',
    'objectList.executionFlowInProgress': 'In progress',
    'objectList.executionFlowBlocked': 'Blocked',
    'objectList.executionFlowDone': 'Done',
    'objectList.executionFlowSkipped': 'Skipped',
    'objectList.executionFlowRisk': 'Risk',
    'objectList.executionFlowOther': 'Other',
    'objectList.executionFlowCount': '{status}: {count}',
    'objectList.executionFlowLegend': 'Execution item flow legend',
    'objectList.activeCount': '{count} active',
    'objectList.reviewCount': '{count} pending close',
    'objectList.riskCount': '{count} at risk',
    'objectList.noPlans': 'No related WorkCases',
    'objectList.noExecutionItems': 'No execution items',
    'objectList.morePlans': '{count} more WorkCases',
    'objectList.moreExecutionItems': '{count} more execution items',
    'objectList.successCriteria': 'Success Criteria',
    'objectList.planConfirmedAt': 'Plan Confirmed',
    'objectList.reviewRequestedAt': 'Review Request',
    'objectList.closureRequestedAt': 'Closure Requested',
    'objectList.completionEvidence': 'Completion Evidence',
    'objectList.verificationEvidence': 'Verification Evidence',
    'objectList.closureEvidence': 'Closure Evidence',
    'objectList.hasRecord': 'Recorded',
    'objectList.missingRecord': 'Incomplete',
    'objectList.archiveReason': 'Archive reason',
    'objectList.deprecatedReason': 'Deprecated reason',
    'objectList.discardReason': 'Discard reason',
    'objectList.disposition': 'Disposition',
    'objectList.closeReason': 'Close reason',
    'objectList.missingReason': 'Missing reason',
    'objectList.missingReasonText': 'This non-active object must record a reason in its fact source.',
    'objectList.updated': 'Updated {time}',
    'objectList.noRouteTarget': 'No fact-object target recorded',
    'objectList.routed': 'Routed',
    'objectList.target': 'Target',
    'objectList.time': 'Time',
    'objectList.dispositionMissing': 'Disposition missing.',
    'objectList.discarded': 'Discarded',
    'objectList.reason': 'Reason',
    'objectList.workcaseStateDynamic': 'In progress',
    'objectList.workcaseStateWaiting': 'Waiting for Human',
    'objectList.workcaseStateClosed': 'WorkCase closed',
    'objectList.workcaseProgressUnavailable': 'Progress unavailable',
    'objectList.workcaseGoal': 'Goal',
    'objectList.workcaseCurrentProgress': 'Current progress',
    'objectList.workcaseBlockingReason': 'Blocking reason',
    'objectList.workcaseRoundFull': 'Round {round}',
    'objectList.workcaseRoundPartial': 'Round {round} since recording began',
    'objectList.workcaseRoundMissing': 'Round not recorded',
    'objectList.workcaseRoundInvalid': 'Round unavailable',
    'objectList.workcaseItemProgress': '{done}/{total} completed',
    'objectList.workcaseItemsCancelled': '{count} cancelled',
    'objectList.workcaseCurrentItems': 'Current work items',
    'objectList.workcaseNoCurrentItems': 'No work item is currently in progress',
    'objectList.workcaseCriteriaCount': '{count} criteria',
    'objectList.workcaseFieldMissing': 'Not recorded',
    'objectList.workcaseDynamicStages': 'Progress step',
    'objectList.workcaseStageExecute': 'Item execution',
    'objectList.workcaseStageSelfCheck': 'Controller self-check',
    'objectList.workcaseStageResultReview': 'Independent review',
    'objectList.workcaseStageSynthesis': 'Controller synthesis',

    'objectDetail.back': 'Back',
    'objectDetail.content': 'Content',
    'objectDetail.yamlSource': 'YAML Source',
    'objectDetail.id': 'ID',
    'objectDetail.type': 'Type',
    'objectDetail.status': 'Status',
    'objectDetail.created': 'Created',
    'objectDetail.updated': 'Updated',
    'objectDetail.createdShort': 'Created',
    'objectDetail.updatedShort': 'Updated',
    'objectDetail.expand': 'Expand',
    'objectDetail.collapse': 'Collapse',
    'objectDetail.aggregatedDeliverables': 'Aggregated Deliverables',
    'objectDetail.aggregatedDocs': 'Aggregated Docs',
    'objectDetail.editStatus': 'Click to change status',
    'objectDetail.editAcceptance': 'Click to edit acceptance criteria',
    'objectDetail.goal': 'Goal',
    'objectDetail.noDescription': 'No description recorded',
    'objectDetail.workPlan': 'WorkCase',
    'objectDetail.executionStatus': 'Execution Status',
    'objectDetail.currentState': 'Current State',
    'objectDetail.waitingFor': 'Waiting For',
    'objectDetail.acceptance': 'Acceptance',
    'objectDetail.verification': 'Verification',
    'objectDetail.verificationEvidence': 'Verification Evidence',
    'objectDetail.closureEvidence': 'Closure Evidence',
    'objectDetail.noAcceptance': 'No acceptance criteria recorded',
    'objectDetail.noVerification': 'No verification recorded',
    'objectDetail.noClosureEvidence': 'No closure evidence recorded',
    'objectDetail.relatedDocs': 'Related Docs',
    'objectDetail.related': 'Related',
    'objectDetail.affectedDocs': 'Affected Docs',
    'objectDetail.dependencies': 'Dependencies',
    'objectDetail.otherFields': 'Other Fields',
    'objectDetail.emptyValue': 'Empty',
    'objectDetail.planGoal': 'WorkCase Goal',
    'objectDetail.planDescription': 'WorkCase Description',
    'objectDetail.noPlanGoal': 'No WorkCase goal recorded',
    'objectDetail.noPlanDescription': 'No WorkCase description recorded',
    'objectDetail.planExecution': 'Execution Queue',
    'objectDetail.workcaseProgress': 'WorkCase Progress',
    'objectDetail.workcaseCloseout': 'Closeout and Remaining Responsibilities',
    'objectDetail.noWorkcaseCloseout': 'No closeout record is available',
    'objectDetail.workcaseHumanOverview': 'WorkCase Overview',
    'objectDetail.workcaseHumanContext': 'Human View',
    'objectDetail.workcaseAiContext': 'AI Context',
    'objectDetail.workcaseAiCore': 'Core Context',
    'objectDetail.workcaseAiReviewContext': 'Review Context',
    'objectDetail.executionReferences': 'Execution References',
    'objectDetail.lifecycleStage': 'Lifecycle Stage',
    'objectDetail.lifecycleDraft': 'Goal alignment',
    'objectDetail.lifecyclePlanConfirming': 'Plan confirmation',
    'objectDetail.lifecycleActive': 'Executing',
    'objectDetail.lifecycleBlocked': 'Blocked',
    'objectDetail.lifecycleVerification': 'Verification',
    'objectDetail.lifecycleResultReview': 'Result review',
    'objectDetail.lifecycleReview': 'Closure review',
    'objectDetail.lifecycleClosed': 'Closed',
    'objectDetail.successCriteriaProgress': 'Success criteria',
    'objectDetail.executionItemProgress': 'Execution items',
    'objectDetail.workcaseExecution': 'Execution Items',
    'objectDetail.executionItemsLoading': 'Loading execution item posture',
    'objectDetail.workcaseReview': 'Review Arrangement',
    'objectDetail.planReview': 'Plan Review',
    'objectDetail.resultReview': 'Result Review',
    'objectDetail.reviewPolicy': 'Review Policy',
    'objectDetail.reviewItems': 'Review Items',
    'objectDetail.controllerResolution': 'Controller Resolution',
    'objectDetail.humanPlanConfirmation': 'Plan Confirmation',
    'objectDetail.humanClosureConfirmation': 'Closure Confirmation',
    'objectDetail.reviewConclusion': 'Conclusion',
    'objectDetail.controllerSelfCheck': 'Controller self-check',
    'objectDetail.specialistReview': 'Specialist review',
    'objectDetail.humanClosureReview': 'Human closure review',
    'objectDetail.reviewRequirement': 'Requirement',
    'objectDetail.required': 'Required',
    'objectDetail.notRequired': 'Not required',
    'objectDetail.reviewRole': 'Role',
    'objectDetail.expectedOutput': 'Expected output',
    'objectDetail.noSuccessCriteria': 'No success criteria recorded',
    'objectDetail.planCloseReview': 'Close Decision',
    'objectDetail.closeDecisionReady': 'Ready to close',
    'objectDetail.closeDecisionReadyHint': 'Success criteria and completion evidence are confirmed.',
    'objectDetail.closeDecisionPending': 'Close conditions not met',
    'objectDetail.closeDecisionPendingHint': 'Some success criteria or completion evidence still needs confirmation.',
    'objectDetail.closeDecisionPendingItems': 'Pending confirmations',
    'objectDetail.closeDecisionNoPendingItems': 'No pending confirmations',
    'objectDetail.closeDecisionRecordState': 'Record state',
    'objectDetail.noCompletionEvidence': 'No completion evidence recorded',
    'objectDetail.noVerificationEvidence': 'No verification evidence recorded',
    'objectDetail.noClosureEvidenceForWorkCase': 'No closure evidence recorded',
    'objectDetail.planMaterials': 'Deliverables and Docs',
    'objectDetail.relatedMaterials': 'Related Materials',

    'projectFiles.title': 'Project Files',
    'projectFiles.subtitle': 'Browse governed project files, preview Markdown, and inspect pending Git changes in read-only mode.',
    'projectFiles.project': 'Governed Project',
    'projectFiles.quickRoots': 'Quick Roots',
    'projectFiles.showHiddenFiles': 'Show hidden files',
    'projectFiles.filesTab': 'Files',
    'projectFiles.changesTab': 'Pending',
    'projectFiles.historyTab': 'History',
    'projectFiles.fileBrowser': 'Project File Browser',
    'projectFiles.preview': 'File Preview',
    'projectFiles.pending': 'Pending Files',
    'projectFiles.history': 'Commit History',
    'projectFiles.changeDetail': 'Diff Detail',
    'projectFiles.selectedCommitFiles': 'Selected Commit Files',
    'projectFiles.diff': 'File Diff',
    'projectFiles.diffMode': 'Diff display mode',
    'projectFiles.unifiedDiff': 'Unified',
    'projectFiles.splitDiff': 'Split',
    'projectFiles.reload': 'Refresh',
    'projectFiles.loading': 'Loading',
    'projectFiles.noProjects': 'No governed projects found.',
    'projectFiles.noEntries': 'No displayable files in this directory.',
    'projectFiles.chooseFile': 'Select a file on the left to read it here.',
    'projectFiles.chooseDiff': 'Select a pending file to view its diff here.',
    'projectFiles.chooseCommit': 'Select a commit on the left to view details.',
    'projectFiles.chooseCommitFile': 'Select a changed file to view its diff in this commit.',
    'projectFiles.noChanges': 'This project has no pending files.',
    'projectFiles.noCommits': 'This project has no commit history.',
    'projectFiles.mergeCommit': 'Merge',
    'projectFiles.binary': 'This is a binary file; the web view only shows path and size.',
    'projectFiles.truncated': 'Content was truncated at the safety limit.',
    'projectFiles.readOnly': 'Read-only',
    'projectFiles.root': 'Project root',
    'projectFiles.docs': 'docs',
    'projectFiles.ldvhBase': 'LDVH Base',
    'projectFiles.view': 'View',
    'projectFiles.viewAria': 'Project file view',
    'projectFiles.before': 'Before',
    'projectFiles.after': 'After',

    'readingPanel.truncated': 'Content truncated',
    'readingPanel.close': 'Close',
    'readingPanel.title': 'Extended Reading',
    'readingPanel.previous': 'Previous visited object',
    'readingPanel.next': 'Next visited object',
    'readingPanel.empty': 'Select an object or document to preview here',
    'readingPanel.loadFailed': 'Failed to load',
    'readingPanel.docLoadFailed': 'Failed to load document',
    'readingPanel.noEvidence': 'No evidence available',
    'readingPanel.changeDetail': 'Commit Detail',
    'readingPanel.openNewTab': 'New Tab',
    'objectDetail.humanGateTip': 'This WorkCase is pending close review',
    'objectDetail.openReadingPanel': 'Open in reading panel',
    'objectDetail.reportBody': 'Report body',
    'objectDetail.readUnavailable': 'Object could not be read',
    'objectDetail.readType': 'Object',
    'objectDetail.readStatus': 'Read status',
    'objectDetail.expectedPath': 'Expected path',
    'objectDetail.readIssue': 'Read issue',

    'changelog.allTypes': 'All types',
    'changelog.allScopes': 'All scopes',
    'changelog.recentCount': 'Latest {count}',
    'changelog.noMatches': 'No matching commits',
    'changelog.copyContext': 'Copy commit context',
    'changelog.copiedContext': 'Commit context copied',
    'changelog.loadFailed': 'Failed to load commits',
    'changelog.detailFailed': 'Failed to load commit detail',
    'changelog.closeDetails': 'Close details',
    'changelog.openDetails': 'Open details',
    'changelog.commitAt': 'Commit {time}',

    'common.loading': 'Loading...',
    'common.loadFailed': 'Failed to load',
    'common.language': 'Language',
    'common.true': 'Yes',
    'common.false': 'No',
    'common.empty': 'Empty',
    'common.null': '—',
    'common.copyPath': 'Copy path',
    'common.copiedPath': 'Path copied',
    'common.copyObjectPath': 'Copy object path',
    'common.copiedObjectPath': 'Object path copied',
    'common.copyDocPath': 'Copy document path',
    'common.copiedDocPath': 'Document path copied',
    'common.copyUrl': 'Copy link',
    'common.copiedUrl': 'Link copied',
    'common.copyReference': 'Copy reference',
    'common.copiedReference': 'Reference copied',
    'common.read': 'Read',
  },
} as const;

export type Locale = keyof typeof UI_LOCALES;
export type LocaleKey = keyof typeof UI_LOCALES.zh;
