// Request dedupe + short-TTL cache for the dashboard.
//
// Every widget fetches its own data on mount. When several widgets issue the
// same API call at once (and React StrictMode double-fires effects in dev),
// those identical requests pile up and trip the API's 429 rate limit. This
// wraps the global `fetch` so identical requests share a single in-flight
// network call and reuse the response for a short TTL.
//
// What gets deduped/cached:
// - All GET requests (keyed by URL).
// - POST requests to Insights RTM endpoints (URL contains `insightsrtm_`),
//   keyed by URL + body — these are read-only queries that the platform
//   exposes over POST (Agents, AgentMemory, Governance all query this way).
// Everything else — OAuth token POSTs, mutations, non-string bodies — passes
// straight through untouched. Failures are not cached (evicted so a later
// call can retry). Dashboards are read-only, so data at most `ttlMs` stale is fine.

const DEFAULT_TTL_MS = 15_000

/** Insights RTM path marker — its query endpoints are read-only POSTs. */
const INSIGHTS_RTM_MARKER = 'insightsrtm_'

interface CacheEntry {
  at: number
  response: Promise<Response>
}

let installed = false

/**
 * Install the fetch dedupe/cache once, before the app renders. Idempotent.
 * @param ttlMs how long an identical request is reused (default 15s)
 */
export function installFetchCache(ttlMs: number = DEFAULT_TTL_MS): void {
  if (installed) return
  installed = true

  const originalFetch = globalThis.fetch.bind(globalThis)
  const cache = new Map<string, CacheEntry>()

  /** Cache key for a request, or null when the request must not be cached. */
  function keyFor(input: RequestInfo | URL, init?: RequestInit): string | null {
    // Request objects can carry a stream body we can't key synchronously — pass through.
    if (input instanceof Request) return null
    const url = typeof input === 'string' ? input : input.href
    const method = (init?.method ?? 'GET').toUpperCase()
    if (method === 'GET') return `GET ${url}`
    if (method === 'POST' && url.includes(INSIGHTS_RTM_MARKER)) {
      const body = init?.body
      if (body === undefined || body === null) return `POST ${url}`
      if (typeof body === 'string') return `POST ${url} ${body}`
    }
    return null
  }

  globalThis.fetch = (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const key = keyFor(input, init)
    if (!key) return originalFetch(input, init)

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
