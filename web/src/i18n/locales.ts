// ============================================================
// 状态词汇表 — 所有 LDVH 事实对象状态的中英对照
// 来源：specs/13-LDVH事实模型基础规范 §5 状态机
// ============================================================
export const STATUS_LOCALES: Record<string, { zh: string; en: string }> = {
  // Intent
  draft: { zh: '草稿', en: 'Draft' },
  proposed: { zh: '已提议', en: 'Proposed' },
  accepted: { zh: '已采纳', en: 'Accepted' },
  superseded: { zh: '已替代', en: 'Superseded' },
  rejected: { zh: '已拒绝', en: 'Rejected' },
  deprecated: { zh: '已废弃', en: 'Deprecated' },
  archived: { zh: '已归档', en: 'Archived' },
  active: { zh: '活跃', en: 'Active' },
  suspended: { zh: '已暂停', en: 'Suspended' },
  completed: { zh: '已完成', en: 'Completed' },
  // Task
  planned: { zh: '计划中', en: 'Planned' },
  executing: { zh: '执行中', en: 'Executing' },
  verifying: { zh: '验证中', en: 'Verifying' },
  review_needed: { zh: '待审核', en: 'Review Needed' },
  closed: { zh: '已关闭', en: 'Closed' },
  // ADR
  pending_review: { zh: '待评审', en: 'Pending Review' },
  implemented: { zh: '已实施', en: 'Implemented' },
  // Pitfall
  observed: { zh: '已观测', en: 'Observed' },
  confirmed: { zh: '已确认', en: 'Confirmed' },
  resolved: { zh: '已解决', en: 'Resolved' },
  // Memo
  filed: { zh: '已归档', en: 'Filed' },
  // Profile
  // Change
  proposed_change: { zh: '提议中', en: 'Proposed' },
  approved: { zh: '已批准', en: 'Approved' },
  applied: { zh: '已应用', en: 'Applied' },
  cancelled: { zh: '已取消', en: 'Cancelled' },
};

/** 根据状态返回当前语言的翻译，未知状态回退到原值 */
export function getStatusLocale(status: string, locale: string): string {
  const entry = STATUS_LOCALES[status];
  if (!entry) return status;
  return locale === 'en' ? entry.en : entry.zh;
}

// ============================================================
// UI 文案词汇表
// ============================================================
export const UI_LOCALES = {
  zh: {
    // Logo
    'logo.tagline': '让 Vibe Coding 更高效、更稳定、更可控',

    // Sidebar
    'nav.dashboard': '仪表盘',
    'nav.intents': '意图',
    'nav.tasks': '任务',
    'nav.adrs': 'ADR',
    'nav.pitfalls': 'BUG',
    'nav.memos': '备忘',
    'nav.profiles': '画像',
    'nav.changes': '变更',
    'nav.validate': '校验',
    'nav.changelog': '变更',
    'nav.workbench': '工作台',
    'nav.switchLayout': '切换布局',

    // Dashboard
    'dashboard.title': '仪表盘',
    'dashboard.recentActivity': '最近活动',
    'dashboard.recentChanges': '最近变更',
    'dashboard.validationStatus': '校验状态',
    'dashboard.noRecentActivity': '暂无最近活动',
    'dashboard.noRecentChanges': '暂无最近变更',
    'dashboard.noActionItems': '所有事项已完成',
    'dashboard.actionItems': '待推进',
    'dashboard.status': '状态',
    'dashboard.errors': '错误',
    'dashboard.warnings': '警告',
    'dashboard.pass': '通过',
    'dashboard.fail': '未通过',

    // Workbench
    'workbench.badge': '实验视图 · 不替换主页',
    'workbench.title': 'LDVH 工作台',
    'workbench.subtitle': '把事实对象组织成任务、关系、证据和动作的只读实验入口，用来验证交互结构。',
    'workbench.backToDashboard': '返回仪表盘',
    'workbench.openTasks': '任务总数',
    'workbench.taskSignal': '来自任务事实对象统计',
    'workbench.actionItems': '待推进',
    'workbench.actionSignal': '需要优先关注的对象',
    'workbench.recentChanges': '近期变更',
    'workbench.changeSignal': '可作为证据线索',
    'workbench.validation': '校验',
    'workbench.caseFile': '任务案卷',
    'workbench.acceptance': '验收',
    'workbench.known': '已识别',
    'workbench.acceptanceHint': '第一版只展示工作流信号，后续可接入真实验收项。',
    'workbench.evidence': '证据',
    'workbench.actions': '动作',
    'workbench.actionAddEvidence': '添加证据（实验占位）',
    'workbench.actionLinkTask': '关联任务（实验占位）',
    'workbench.actionReview': '发起审查（实验占位）',
    'workbench.noTask': '当前没有可展示的任务案卷。',
    'workbench.relationships': '关联对象',
    'workbench.noRelationships': '暂无关联对象线索。',
    'workbench.traceability': '追踪链路',
    'workbench.step': '步骤',

    // Object List
    'objectList.noObjects': '未找到 {type} 对象',
    'objectList.all': '全部',

    // Object Detail
    'objectDetail.back': '返回',
    'objectDetail.content': '内容',
    'objectDetail.yamlSource': 'YAML 源码',
    'objectDetail.id': 'ID',
    'objectDetail.type': '类型',
    'objectDetail.status': '状态',
    'objectDetail.created': '创建时间',
    'objectDetail.updated': '更新时间',
    'objectDetail.closedAt': '关闭时间',

    // Validate
    'validate.title': '校验',
    'validate.filesChecked': '已检查文件',
    'validate.errors': '错误',
    'validate.warnings': '警告',
    'validate.allPassed': '所有校验通过',
    'validate.noIssues': '未发现错误或警告',
    'validate.error': '错误',
    'validate.warning': '警告',
    'validate.byFile': '按文件分组',

    // Changelog
    'changelog.title': '变更',
    'changelog.subtitle': 'Git 提交历史记录，点击查看详情',
    'changelog.loadFailed': '加载变更日志失败',
    'changelog.detailFailed': '加载提交详情失败',

    // Common
    'common.loading': '加载中...',
    'common.loadFailed': '加载失败',
    'common.language': '语言',
    'common.true': '是',
    'common.false': '否',
    'common.empty': '空',
    'common.null': '—',
  },
  en: {
    // Logo
    'logo.tagline': 'Making Vibe Coding more efficient, stable, and controllable',

    // Sidebar
    'nav.dashboard': 'Dashboard',
    'nav.intents': 'Intents',
    'nav.tasks': 'Tasks',
    'nav.adrs': 'ADRs',
    'nav.pitfalls': 'Bugs',
    'nav.memos': 'Memos',
    'nav.profiles': 'Profiles',
    'nav.changes': 'Changes',
    'nav.validate': 'Validate',
    'nav.changelog': 'Changes',
    'nav.workbench': 'Workbench',
    'nav.switchLayout': 'Switch Layout',

    // Dashboard
    'dashboard.title': 'Dashboard',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.recentChanges': 'Recent Changes',
    'dashboard.validationStatus': 'Validation Status',
    'dashboard.noRecentActivity': 'No recent activity',
    'dashboard.noRecentChanges': 'No recent changes',
    'dashboard.noActionItems': 'All items completed',
    'dashboard.actionItems': 'Action Items',
    'dashboard.status': 'Status',
    'dashboard.errors': 'Errors',
    'dashboard.warnings': 'Warnings',
    'dashboard.pass': 'PASS',
    'dashboard.fail': 'FAIL',

    'workbench.badge': 'Experimental · Dashboard unchanged',
    'workbench.title': 'LDVH Workbench',
    'workbench.subtitle': 'A read-only experiment that organizes facts into tasks, relationships, evidence, and actions.',
    'workbench.backToDashboard': 'Back to Dashboard',
    'workbench.openTasks': 'Total Tasks',
    'workbench.taskSignal': 'From task fact statistics',
    'workbench.actionItems': 'Action Items',
    'workbench.actionSignal': 'Objects that need attention',
    'workbench.recentChanges': 'Recent Changes',
    'workbench.changeSignal': 'Evidence candidates',
    'workbench.validation': 'Validation',
    'workbench.caseFile': 'Task Case File',
    'workbench.acceptance': 'Acceptance',
    'workbench.known': 'Known',
    'workbench.acceptanceHint': 'The first version shows workflow signals only; real acceptance items can be connected later.',
    'workbench.evidence': 'Evidence',
    'workbench.actions': 'Actions',
    'workbench.actionAddEvidence': 'Add evidence (placeholder)',
    'workbench.actionLinkTask': 'Link task (placeholder)',
    'workbench.actionReview': 'Start review (placeholder)',
    'workbench.noTask': 'No task case file is available.',
    'workbench.relationships': 'Related Objects',
    'workbench.noRelationships': 'No relationship signals yet.',
    'workbench.traceability': 'Traceability Chain',
    'workbench.step': 'Step',

    // Object List
    'objectList.noObjects': 'No {type} found',
    'objectList.all': 'All',

    // Object Detail
    'objectDetail.back': 'Back',
    'objectDetail.content': 'Content',
    'objectDetail.yamlSource': 'YAML Source',
    'objectDetail.id': 'ID',
    'objectDetail.type': 'Type',
    'objectDetail.status': 'Status',
    'objectDetail.created': 'Created',
    'objectDetail.updated': 'Updated',
    'objectDetail.closedAt': 'Closed',

    // Validate
    'validate.title': 'Validation',
    'validate.filesChecked': 'Files Checked',
    'validate.errors': 'Errors',
    'validate.warnings': 'Warnings',
    'validate.allPassed': 'All validations passed',
    'validate.noIssues': 'No errors or warnings found',
    'validate.error': 'Error',
    'validate.warning': 'Warning',
    'validate.byFile': 'Grouped by file',

    // Changelog
    'changelog.title': 'Changes',
    'changelog.subtitle': 'Git commit history, click to view details',
    'changelog.loadFailed': 'Failed to load changes',
    'changelog.detailFailed': 'Failed to load commit detail',

    // Common
    'common.loading': 'Loading...',
    'common.loadFailed': 'Failed to load',
    'common.language': 'Language',
    'common.true': 'Yes',
    'common.false': 'No',
    'common.empty': 'Empty',
    'common.null': '—',
  },
} as const;

export type Locale = keyof typeof UI_LOCALES;
export type LocaleKey = keyof typeof UI_LOCALES.zh;
