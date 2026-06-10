// Widget compute helpers — headline aggregates, deltas, and rate series.
// Templates call these so the big number and the delta badge reflect the whole
// series, not just the last data point.

export type Rows = Record<string, unknown>[]
export type HeadlineMode = 'sum' | 'avg' | 'latest' | 'count' | 'max' | 'min'
export type DeltaPolarity = 'up-good' | 'up-bad' | 'neutral'
export type DeltaDirection = 'up-good' | 'up-bad' | 'down-good' | 'down-bad' | 'neutral'

function nums(rows: Rows, key: string): number[] {
  return rows.map((r) => Number(r[key])).filter((n) => !Number.isNaN(n))
}

/** Aggregate a series down to the single headline number. */
export function headline(rows: Rows, key: string, mode: HeadlineMode = 'latest'): number {
  if (mode === 'count') return rows.length
  const ns = nums(rows, key)
  if (ns.length === 0) return 0
  switch (mode) {
    case 'sum': return ns.reduce((a, b) => a + b, 0)
    case 'avg': return ns.reduce((a, b) => a + b, 0) / ns.length
    case 'max': return Math.max(...ns)
    case 'min': return Math.min(...ns)
    case 'latest':
    default: return ns[ns.length - 1]
  }
}

/**
 * Change between the most recent value and the one before it, expressed as a
 * percentage, mapped to a coloured badge direction via the metric's polarity.
 * Returns an empty text when there isn't enough data to compute a real delta.
 */
export function delta(rows: Rows, key: string, polarity: DeltaPolarity = 'neutral'): { text: string; direction: DeltaDirection } {
  const ns = nums(rows, key)
  if (ns.length < 2) return { text: '', direction: 'neutral' }
  const recent = ns[ns.length - 1]
  const prior = ns[ns.length - 2]
  if (prior === 0) return { text: recent === 0 ? '0%' : 'new', direction: 'neutral' }
  const pct = Math.round(((recent - prior) / Math.abs(prior)) * 100)
  if (pct === 0 || polarity === 'neutral') return { text: `${pct > 0 ? '+' : ''}${pct}%`, direction: 'neutral' }
  const direction: DeltaDirection = pct > 0
    ? (polarity === 'up-good' ? 'up-good' : 'up-bad')
    : (polarity === 'up-good' ? 'down-bad' : 'down-good')
  return { text: `${pct > 0 ? '+' : ''}${pct}%`, direction }
}

/**
 * Tailwind text-colour class for a numeric cell.
 * `goodHigh` — higher is better (e.g. success rate). `goodLow` — lower is better (e.g. error rate).
 */
export function toneClass(n: number, kind: 'goodHigh' | 'goodLow'): string {
  const good = 'text-[hsl(var(--chart-3))]'
  const bad = 'text-destructive'
  const mid = 'text-foreground'
  if (Number.isNaN(n)) return mid
  if (kind === 'goodHigh') return n >= 90 ? good : n >= 70 ? mid : bad
  return n <= 5 ? good : n <= 20 ? mid : bad
}

/** Per-bucket percentage series for a rate metric: num/den * 100, keyed on xKey. */
export function rateSeries(rows: Rows, numKey: string, denKey: string, xKey: string): Rows {
  return rows.map((r) => {
    const num = Number(r[numKey]) || 0
    const den = Number(r[denKey]) || 0
    return { [xKey]: r[xKey], rate: den > 0 ? (num / den) * 100 : 0 }
  })
}

/** Overall rate across the whole window: Σnum / Σden * 100. */
export function overallRate(rows: Rows, numKey: string, denKey: string): number {
  const num = rows.reduce((a, r) => a + (Number(r[numKey]) || 0), 0)
  const den = rows.reduce((a, r) => a + (Number(r[denKey]) || 0), 0)
  return den > 0 ? (num / den) * 100 : 0
}

/** Delta for a rate series, expressed in percentage points (pp), not relative %. */
export function rateDelta(rateRows: Rows, polarity: DeltaPolarity = 'up-bad'): { text: string; direction: DeltaDirection } {
  const ns = nums(rateRows, 'rate')
  if (ns.length < 2) return { text: '', direction: 'neutral' }
  const pp = Math.round((ns[ns.length - 1] - ns[ns.length - 2]) * 10) / 10
  if (pp === 0 || polarity === 'neutral') return { text: `${pp > 0 ? '+' : ''}${pp}pp`, direction: 'neutral' }
  const direction: DeltaDirection = pp > 0
    ? (polarity === 'up-good' ? 'up-good' : 'up-bad')
    : (polarity === 'up-good' ? 'down-bad' : 'down-good')
  return { text: `${pp > 0 ? '+' : ''}${pp}pp`, direction }
}
