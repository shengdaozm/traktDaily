export function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr.substring(0, 10)
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  } catch {
    return dateStr?.substring(0, 10) || ''
  }
}

export function relativeDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr.substring(0, 10)
    const now = new Date()
    const diffMs = now - d
    const diffDay = Math.floor(diffMs / 86400000)
    if (diffDay === 0) return '今天'
    if (diffDay === 1) return '昨天'
    if (diffDay < 7) return `${diffDay} 天前`
    if (diffDay < 30) return `${Math.floor(diffDay / 7)} 周前`
    if (diffDay < 365) return `${Math.floor(diffDay / 30)} 个月前`
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')
  } catch {
    return ''
  }
}

export function formatMinutes(minutes) {
  if (!minutes || minutes <= 0) return '0 分钟'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h > 0 && m > 0) return `${h} 小时 ${m} 分`
  if (h > 0) return `${h} 小时`
  return `${m} 分钟`
}
