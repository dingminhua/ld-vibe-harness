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

    // Dashboard
    'dashboard.title': '仪表盘',
    'dashboard.recentActivity': '最近活动',
    'dashboard.validationStatus': '校验状态',
    'dashboard.noRecentActivity': '暂无最近活动',
    'dashboard.status': '状态',
    'dashboard.errors': '错误',
    'dashboard.warnings': '警告',
    'dashboard.pass': '通过',
    'dashboard.fail': '未通过',

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

    // Dashboard
    'dashboard.title': 'Dashboard',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.validationStatus': 'Validation Status',
    'dashboard.noRecentActivity': 'No recent activity',
    'dashboard.status': 'Status',
    'dashboard.errors': 'Errors',
    'dashboard.warnings': 'Warnings',
    'dashboard.pass': 'PASS',
    'dashboard.fail': 'FAIL',

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
  },
} as const;

export type Locale = keyof typeof UI_LOCALES;
export type LocaleKey = keyof typeof UI_LOCALES.zh;
