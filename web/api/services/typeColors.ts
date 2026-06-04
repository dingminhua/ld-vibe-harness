/**
 * 对象类型颜色映射
 */

export const TYPE_COLORS: Record<string, string> = {
  intent: '#3b82f6',    // blue
  task: '#22c55e',      // green
  adr: '#a855f7',       // purple
  pitfall: '#ef4444',   // red
  memo: '#eab308',      // yellow
  profile: '#06b6d4',   // cyan
  default: '#6b7280',   // gray
}

export function getTypeColor(type: string): string {
  return TYPE_COLORS[type] || TYPE_COLORS.default
}
