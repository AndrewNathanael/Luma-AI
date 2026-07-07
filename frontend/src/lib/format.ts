export function formatNumber(value: number | null | undefined, digits = 3) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '-'
  }
  return value.toFixed(digits)
}
