import { getCategoryLabel } from '../i18n/locales.ts';

/** Conventional commit 分类颜色映射 */
export const CATEGORY_COLORS: Record<string, string> = {
  workcase: '#0ea5e9',
  adr: '#a855f7',
  pitfall: '#ef4444',
  spark: '#eab308',
  study: '#06b6d4',
  'file-asset': '#14b8a6',
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

export function getCategoryColor(category: string): string {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
}

export function getCategoryLocale(category: string, locale: string): string {
  return getCategoryLabel(category, locale);
}
