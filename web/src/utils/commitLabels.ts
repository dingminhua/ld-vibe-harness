export const CURRENT_COMMIT_TYPES = [
  'feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert',
] as const;

export const CURRENT_COMMIT_SCOPES = [
  'specs', 'docs', 'rules', 'runtime', 'code', 'web', 'tests', 'config',
  'workcase', 'adr', 'spark', 'study', 'pitfall',
] as const;

const COMMIT_TYPE_ZH: Record<(typeof CURRENT_COMMIT_TYPES)[number], string> = {
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
};

const COMMIT_SCOPE_LABELS: Record<(typeof CURRENT_COMMIT_SCOPES)[number], { zh: string; en: string }> = {
  specs: { zh: 'Specs', en: 'Specs' },
  docs: { zh: '文档', en: 'Docs' },
  rules: { zh: '规则', en: 'Rules' },
  runtime: { zh: '运行时', en: 'Runtime' },
  code: { zh: 'Code', en: 'Code' },
  web: { zh: 'Web', en: 'Web' },
  tests: { zh: 'Tests', en: 'Tests' },
  config: { zh: '配置', en: 'Config' },
  workcase: { zh: '工作', en: 'WorkCase' },
  adr: { zh: '决策', en: 'ADR' },
  spark: { zh: '火花', en: 'Spark' },
  study: { zh: '研究', en: 'Study' },
  pitfall: { zh: '经验', en: 'Pitfall' },
};

export function getCommitTypeLabel(type: string | undefined, locale: string) {
  if (!type) return '';
  if (locale === 'en') return type;
  return Object.prototype.hasOwnProperty.call(COMMIT_TYPE_ZH, type)
    ? COMMIT_TYPE_ZH[type as keyof typeof COMMIT_TYPE_ZH]
    : type;
}

export function getCommitScopeLabel(scope: string | undefined, locale: string) {
  if (!scope) return '';
  const labels = Object.prototype.hasOwnProperty.call(COMMIT_SCOPE_LABELS, scope)
    ? COMMIT_SCOPE_LABELS[scope as keyof typeof COMMIT_SCOPE_LABELS]
    : undefined;
  if (!labels) return scope;
  return locale === 'en' ? labels.en : labels.zh;
}
