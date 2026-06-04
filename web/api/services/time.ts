/**
 * 相对时间计算工具
 */

export function getRelativeTime(dateStr: string, locale: string = 'zh'): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  const diffWeek = Math.floor(diffDay / 7)
  const diffMonth = Math.floor(diffDay / 30)
  const diffYear = Math.floor(diffDay / 365)

  const isEn = locale === 'en'

  if (diffYear > 0) {
    return isEn ? `${diffYear}y ago` : `${diffYear}年前`
  }
  if (diffMonth > 0) {
    return isEn ? `${diffMonth}mo ago` : `${diffMonth}个月前`
  }
  if (diffWeek > 0) {
    return isEn ? `${diffWeek}w ago` : `${diffWeek}周前`
  }
  if (diffDay > 0) {
    return isEn ? `${diffDay}d ago` : `${diffDay}天前`
  }
  if (diffHour > 0) {
    return isEn ? `${diffHour}h ago` : `${diffHour}小时前`
  }
  // 小于1分钟也显示为1分钟前，不显示"刚刚"
  if (diffMin >= 0) {
    const min = Math.max(1, diffMin)
    return isEn ? `${min}m ago` : `${min}分钟前`
  }
  const min = Math.max(1, diffMin)
  return isEn ? `${min}m ago` : `${min}分钟前`
}
