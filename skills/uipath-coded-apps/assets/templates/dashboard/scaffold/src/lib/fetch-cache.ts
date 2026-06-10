// Request dedupe + short-TTL cache for the dashboard.
//
// Every widget fetches its own data on mount. When several widgets issue the
// same API call at once (and React StrictMode double-fires effects in dev),
// those identical requests pile up and trip the API's 429 rate limit. This
// wraps the global `fetch` so that identical GET requests — same method + URL —
// share a single in-flight network call and reuse the response for a short TTL.
//
// Scope: GET only. Mutations and other methods pass straight through. Dashboards
// are read-only, so caching reads for a few seconds is safe; data is at most
// `ttlMs` stale. Failures are not cached (evicted so a later call can retry).

const DEFAULT_TTL_MS = 15_000

interface CacheEntry {
  at: number
  response: Promise<Response>
}

let installed = false

/**
 * Install the fetch dedupe/cache once, before the app renders. Idempotent.
 * @param ttlMs how long an identical GET is reused (default 15s)
 */
export function installFetchCache(ttlMs: number = DEFAULT_TTL_MS): void {
  if (installed) return
  installed = true

  const originalFetch = globalThis.fetch.bind(globalThis)
  const cache = new Map<string, CacheEntry>()

  globalThis.fetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const method = (init?.method ?? (input instanceof Request ? input.method : 'GET')).toUpperCase()
    // Only dedupe idempotent reads — never cache mutations or auth/token POSTs.
    if (method !== 'GET') return originalFetch(input, init)

    const key = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    const now = Date.now()

    const hit = cache.get(key)
    if (hit && now - hit.at < ttlMs) {
      // Clone so each caller gets its own readable body.
      return hit.response.then((r) => r.clone())
    }

    const response = originalFetch(input, init)
    cache.set(key, { at: now, response })
    // Don't keep failed responses around — let the next call retry.
    response.then(
      (r) => { if (!r.ok) cache.delete(key) },
      () => cache.delete(key),
    )
    return response.then((r) => r.clone())
  }
}
