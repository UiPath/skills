import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import type { UiPath } from '@uipath/uipath-typescript/core'

/**
 * Generic data hook for a dashboard widget. Runs the widget's own data function
 * — whatever SDK calls it makes (Jobs, Queues, Cases, …) — and manages the
 * loading / error / data state. Not tied to any specific service or API.
 *
 * Usage:
 *   const { data, loading, error } = useWidgetData(customDataFn, [])
 *
 * where customDataFn is:
 *   async (sdk: any, getToken: () => Promise<string>) => { ... }
 *
 * @template T - The row/array type the fetcher returns
 * @param fetcher - Calls the SDK; receives the authenticated sdk and a getToken helper
 * @param deps - Re-fetch dependency array (defaults to empty — runs once)
 */
export function useWidgetData<T>(
  fetcher: (sdk: UiPath, getToken: () => Promise<string>) => Promise<T>,
  deps: unknown[] = []
) {
  const { sdk, getToken } = useAuth()
  const [data, setData]       = useState<T | null>(null)
  const [error, setError]     = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sdk) return

    let cancelled = false
    setLoading(true)
    setError(null)

    fetcher(sdk, getToken)
      .then(result => { if (!cancelled) { setData(result); setLoading(false) } })
      .catch(err   => { if (!cancelled) { setError(err instanceof Error ? err : new Error(String(err))); setLoading(false) } })

    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps.length > 0 ? deps : [])

  return { data, error, loading }
}
