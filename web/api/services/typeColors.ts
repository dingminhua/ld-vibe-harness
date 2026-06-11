/**
 * 对象类型颜色映射
 */

export const TYPE_COLORS: Record<string, string> = {
  workarea: '#3b82f6',  // blue
  taskplan: '#14b8a6',  // teal
  task: '#22c55e',      // green
  subtask: '#84cc16',   // lime
  adr: '#a855f7',       // purple
  pitfall: '#ef4444',   // red
  memo: '#eab308',      // yellow
  profile: '#06b6d4',   // cyan
  default: '#6b7280',   // gray
}

export function getTypeColor(type: string): string {
  return TYPE_COLORS[type] || TYPE_COLORS.default
}
