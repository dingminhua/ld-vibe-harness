/** Conventional commit 分类颜色映射 */
export const CATEGORY_COLORS: Record<string, string> = {
  workcase: '#0ea5e9',
  adr: '#a855f7',
  pitfall: '#ef4444',
  spark: '#eab308',
  study: '#06b6d4',
  feat: '#3b82f6',      // blue
  fix: '#ef4444',       // red
  docs: '#6b7280',      // gray
  style: '#a855f7',     // purple
  refactor: '#06b6d4',  // cyan
  test: '#eab308',      // yellow
  chore: '#6b7280',     // gray
  perf: '#22c55e',      // green
  ci: '#ec4899',        // pink
  build: '#92400e',     // brown
  spec: '#14b8a6',       // teal
  rule: '#f97316',       // orange
  other: '#6b7280',     // gray
};

/** Conventional commit 分类双语词汇表 */
export const CATEGORY_LOCALES: Record<string, { zh: string; en: string }> = {
  feat: { zh: '功能', en: 'Feature' },
  fix: { zh: '修复', en: 'Fix' },
  docs: { zh: '文档', en: 'Docs' },
  style: { zh: '样式', en: 'Style' },
  refactor: { zh: '重构', en: 'Refactor' },
  test: { zh: '测试', en: 'Test' },
  chore: { zh: '杂项', en: 'Chore' },
  perf: { zh: '性能', en: 'Perf' },
  ci: { zh: 'CI', en: 'CI' },
  build: { zh: '构建', en: 'Build' },
  spec: { zh: '规范', en: 'Spec' },
  rule: { zh: '规则', en: 'Rule' },
  adr: { zh: '决策', en: 'ADR' },
  other: { zh: '其他', en: 'Other' },
};

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
}

export function getCategoryLocale(category: string, locale: string): string {
  const entry = CATEGORY_LOCALES[category];
  if (!entry) return category;
  return locale === 'en' ? entry.en : entry.zh;
}
