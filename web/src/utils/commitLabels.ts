const COMMIT_TYPE_ZH: Record<string, string> = {
  feat: '新增功能',
  fix: '问题修复',
  docs: '文档修改',
  style: '格式调整',
  refactor: '代码重构',
  perf: '性能优化',
  test: '测试修改',
  build: '构建系统',
  ci: '持续集成',
  chore: '维护杂项',
  revert: '回退变更',
  spec: '规范',
  rule: '规则',
  adr: '决策',
  other: '其他',
};

const COMMIT_SCOPE_LABELS: Record<string, { zh: string; en: string }> = {
  specs: { zh: 'Specs', en: 'Specs' },
  docs: { zh: '文档', en: 'Docs' },
  rules: { zh: '规则', en: 'Rules' },
  code: { zh: 'Code', en: 'Code' },
  web: { zh: 'Web', en: 'Web' },
  tests: { zh: 'Tests', en: 'Tests' },
  config: { zh: '配置', en: 'Config' },
  workcase: { zh: '工作项', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '研究', en: 'Study' },
  pitfall: { zh: '踩坑', en: 'Pitfall' },
  studies: { zh: '研究材料', en: 'Studies' },
  sources: { zh: '来源材料', en: 'Sources' },
};

export function getCommitTypeLabel(type: string | undefined, locale: string) {
  if (!type) return '';
  if (locale === 'en') return type;
  return COMMIT_TYPE_ZH[type] || type;
}

export function getCommitScopeLabel(scope: string | undefined, locale: string) {
  if (!scope) return '';
  const labels = COMMIT_SCOPE_LABELS[scope];
  if (!labels) return scope;
  return locale === 'en' ? labels.en : labels.zh;
}
