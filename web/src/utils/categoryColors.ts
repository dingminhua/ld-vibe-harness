/** Conventional commit 分类颜色映射 */
export const CATEGORY_COLORS: Record<string, string> = {
  workarea: '#3b82f6',
  taskplan: '#14b8a6',
  task: '#22c55e',
  subtask: '#84cc16',
  adr: '#a855f7',
  pitfall: '#ef4444',
  memo: '#eab308',
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
