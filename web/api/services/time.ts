/**
 * 相对时间计算工具
 */

/** 纯日期格式 YYYY-MM-DD */
const DATE_ONLY_RE = /^\d{4}-\d{2}-\d{2}$/

export function getRelativeTime(dateStr: string, locale: string = 'zh'): string {
  // 纯日期字符串（如 "2026-06-05"）追加 T00:00:00 强制按本地时区解析，
  // 避免 ECMAScript 规范将纯日期解析为 UTC 午夜导致跨时区偏差
  const normalized = DATE_ONLY_RE.test(dateStr) ? `${dateStr}T00:00:00` : dateStr
  const date = new Date(normalized)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()

  // 未来时间（时钟偏差或时区问题）统一显示为"1分钟前"
  if (diffMs <= 0) {
    return locale === 'en' ? '1m ago' : '1分钟前'
  }

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
  // 小于1小时也显示为分钟，最小1分钟前
  const min = Math.max(1, diffMin)
  return isEn ? `${min}m ago` : `${min}分钟前`
}
