import { useState, useEffect } from 'react'
import { useAuth } from './useAuth'
import type { UiPath } from '@uipath/uipath-typescript/core'

/**
 * Hook for fetching data from any SDK service method (Insights or otherwise).
 * The fetcher receives both sdk and getToken so fnBody can use either.
 *
 * Usage:
 *   const { data, loading, error } = useInsightsSDK(customDataFn, [])
 *
 * where customDataFn is:
 *   async (sdk: any, getToken: () => Promise<string>) => { ... }
 *
 * @template T - The response type returned by the fetcher
 * @param fetcher - Function that calls the SDK service method; receives sdk and getToken
 * @param deps - Dependency array for re-fetching (defaults to empty — runs once)
 */
export function useInsightsSDK<T>(
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
