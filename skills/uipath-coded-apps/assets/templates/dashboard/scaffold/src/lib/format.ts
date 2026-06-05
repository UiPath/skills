export function fmtNumber(n: number | null | undefined, decimals?: number): string {
  if (n == null) return '—'
  if (decimals !== undefined) return n.toFixed(decimals)
  // Auto precision: show 1 decimal for small values
  if (Math.abs(n) < 10) return n.toFixed(1)
  if (Math.abs(n) < 1000) return Math.round(n).toString()
  if (Math.abs(n) < 1_000_000) return (Math.round(n / 100) / 10).toFixed(1) + 'k'
  return (Math.round(n / 100_000) / 10).toFixed(1) + 'M'
}

export function fmtPercent(n: number | null | undefined, decimals = 1): string {
  if (n == null) return '—'
  return `${n.toFixed(decimals)}%`
}

export function fmtDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${Math.round(seconds)}s`
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`
  return `${(seconds / 3600).toFixed(1)}h`
}

export function fmtTimeAgo(iso: string | null | undefined): string {
  if (!iso) return '—'
  const diffMs = Date.now() - new Date(iso).getTime()
  const diffM = Math.floor(diffMs / 60000)
  if (diffM < 1) return 'just now'
  if (diffM < 60) return `${diffM}m ago`
  const diffH = Math.floor(diffM / 60)
  if (diffH < 24) return `${diffH}h ago`
  return `${Math.floor(diffH / 24)}d ago`
}
