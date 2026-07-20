/**
 * 数值格式化工具函数
 * 用于前端展示：千分位、百分比、文件大小等
 */

/**
 * 千分位格式化整数
 * 例：1234567 → "1,234,567"
 */
export function formatNumber(value: number | string | undefined | null): string {
  if (value == null) return '0'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0'
  return num.toLocaleString('zh-CN', { maximumFractionDigits: 0 })
}

/**
 * 金额格式化（带两位小数 + 千分位）
 * 例：12345.5 → "12,345.50"
 */
export function formatAmount(value: number | string | undefined | null): string {
  if (value == null) return '0.00'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0.00'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/**
 * 百分比格式化（CTR 等）
 * 后端存储的是百分比数值（如 5.49 表示 5.49%），直接追加 %
 * 例：5.49 → "5.49%"
 */
export function formatPercent(value: number | string | undefined | null): string {
  if (value == null) return '0.00%'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '0.00%'
  return num.toFixed(2) + '%'
}

/**
 * 文件大小格式化
 * 例：2097152 → "2.0 MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
