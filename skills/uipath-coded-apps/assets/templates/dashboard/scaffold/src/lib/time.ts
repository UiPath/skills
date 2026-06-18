// Relative time windows for dashboard queries, computed once at module load.
// Metric modules import the windows they need. Moved out of the build script's
// inline TIME_CONSTANTS splice so metric modules type-check in isolation.
export const NOW = new Date()
export const ONE_DAY_AGO = new Date(Date.now() - 86_400_000)
export const SEVEN_DAYS_AGO = new Date(Date.now() - 604_800_000)
export const THIRTY_DAYS_AGO = new Date(Date.now() - 2_592_000_000)
export const SIXTY_DAYS_AGO = new Date(Date.now() - 5_184_000_000)
export const NINETY_DAYS_AGO = new Date(Date.now() - 7_776_000_000)

/**
 * The equal-length window immediately before [start, end] — the correct
 * "previous period" for ANY dashboard window (7d, 30d, 90d, …), not a fixed
 * offset. Use for KPI metrics that return `{ value, previous }` so the delta
 * compares like-for-like regardless of the dashboard's time range.
 *
 *   const [pStart, pEnd] = priorWindow(THIRTY_DAYS_AGO, NOW)
 */
export function priorWindow(start: Date, end: Date): [Date, Date] {
  const span = end.getTime() - start.getTime()
  return [new Date(start.getTime() - span), new Date(start.getTime())]
}
