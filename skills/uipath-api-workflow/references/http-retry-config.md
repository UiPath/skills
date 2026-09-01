# HTTP Retry Configuration

Configure workflow-level retries for HTTP calls with the optional top-level `httpRetryConfig` key, sibling to `document`, `do`, and `evaluate`. If absent, the workflow makes one attempt and fails fast. There is no per-activity override.

## Scope

Only GET requests are retried. `HttpRetryPolicy.normalizeRetryConfig` defaults `methods` to `[GET]`, and StudioWeb does not expose `methods`. POST, PUT, PATCH, and DELETE are never retried, even when their failures match `statusCodes`, because request bodies may not be idempotent.

Applicable calls:

- `UiPath.Http` activities with `bodyParameters.method: "GET"` (HTTP Request curated activity).
- `UiPath.IntSvc` connector GET operations, including vendor list/get calls.

Not applicable: non-GET HTTP methods; non-connector activities such as Sequence, Assign, If, ForEach, DoWhile, TryCatch, Wait, Response, and JS_Invoke; or vendor send, create, upload, update, and delete operations. A workflow containing only POST / PUT calls gains nothing from this setting.

## Configuration

```json
{
  "document": { /* … */ },
  "httpRetryConfig": {
    "maxRetries": 3,
    "delayMs": 1000,
    "networkErrors": true,
    "statusCodes": [408, 429, 500, 502, 503, 504],
    "backoff": { "strategy": "linear", "maxDelayMs": 120000 },
    "respectRetryAfter": true
  },
  "do": [ /* … */ ],
  "evaluate": { "mode": "strict", "language": "javascript" }
}
```

| Field | Type | Required | StudioWeb default when “Retry on Failure” is on | UI bounds |
|---|---|---:|---:|---:|
| `maxRetries` | number | yes | `3` | 1–30 |
| `delayMs` | number | yes | `1000` | 0–900000 (15 min) |
| `networkErrors` | boolean | yes | `true` | — |
| `statusCodes` | number[] | yes | `[408, 429, 500, 502, 503, 504]` | integers 100–599; duplicates rejected |
| `backoff.strategy` | `"constant"` \| `"linear"` \| `"exponential"` | yes | `"constant"` | — |
| `backoff.maxDelayMs` | number | optional | `36000` (UI-emitted; absent means uncapped) | 0–900000 |
| `backoff.multiplier` | number | required iff `strategy === "exponential"`; MUST be absent otherwise | `2` when exponential | 1–20 |
| `respectRetryAfter` | boolean | yes | `true` | — |

`maxRetries` counts retries, not total calls: `maxRetries: 3` permits one initial call plus three retries.

## Backoff and Retry Decisions

`HttpRetryPolicy.calculateDelay` uses `n` as the 1-based retry number:

| Strategy | Formula | With `delayMs: 1000`, `maxRetries: 4` |
|---|---|---|
| `constant` | `delay = delayMs` | 1000, 1000, 1000, 1000 |
| `linear` | `delay = delayMs * n` | 1000, 2000, 3000, 4000 |
| `exponential` | `delay = delayMs * multiplier^(n-1)` | with multiplier 2: 1000, 2000, 4000, 8000 |

When `maxDelayMs` is set, `actualDelay = min(delay, maxDelayMs)`; for example, 100ms, 200ms, and 400ms become 100ms, 200ms, and 250ms with `maxDelayMs: 250`.

`HttpRetryPolicy.shouldRetry` evaluates in this order:

1. If `attemptNumber > maxRetries`, stop and return failure.
2. If a response was received, retry only when its status is in `statusCodes`. With `Retry-After`, wait its seconds or HTTP-date value and ignore computed backoff for that attempt; without it, wait computed backoff. Other statuses are final responses.
3. If no response was received, retry only when `networkErrors: true` and the error matches `ECONNRESET`, `ECONNREFUSED`, `ENOTFOUND`, `ETIMEDOUT`, `timeout`, `fetch failed`, `network error`, or `aborted`; wait computed backoff. Otherwise, stop and propagate the error.

`respectRetryAfter` is UI-emitted, but the executor always honors `Retry-After` for response statuses in `statusCodes`; leave it `true` to match StudioWeb defaults.

## Authoring Rules

1. Omit the whole key when retries are not desired. Do not emit `httpRetryConfig: null` or `{}`; StudioWeb writes either a complete object or nothing.
2. Include the configuration when at least one task is a `UiPath.Http` GET or an IntSvc list/get operation. Tune it for GET-heavy workflows.
3. `backoff.multiplier` MUST appear only with `strategy: "exponential"`; remove it when switching to `constant` or `linear`.
4. `statusCodes` MUST contain integers in `[100, 599]`. StudioWeb silently drops out-of-range values; the executor passes them to `Array.includes`, where they never match. Use `[408, 429, 500, 502, 503, 504]` unless the upstream API documents different transient codes.
5. Cap exponential growth with `maxDelayMs`. Without a cap, `delayMs: 1000`, `multiplier: 2`, and `maxRetries: 10` produce a 512-second wait before the last attempt. StudioWeb’s `36000` (36 s) default is sensible; align it with the workflow SLA.
6. `networkErrors: false` is rarely correct. Disable it only when the caller has its own outer retry or circuit breaker.

## Examples

Constant backoff, fixed 2-second wait and 5 retries:

```json
"httpRetryConfig": {
  "maxRetries": 5,
  "delayMs": 2000,
  "networkErrors": true,
  "statusCodes": [429, 500, 502, 503, 504],
  "backoff": { "strategy": "constant" },
  "respectRetryAfter": true
}
```

Worst-case computed backoff is 5 × 2 s = 10 s; `maxDelayMs` is omitted because constant backoff cannot exceed `delayMs`.

Linear backoff:

```json
"httpRetryConfig": {
  "maxRetries": 3,
  "delayMs": 1000,
  "networkErrors": true,
  "statusCodes": [408, 429, 500, 502, 503, 504],
  "backoff": { "strategy": "linear", "maxDelayMs": 120000 },
  "respectRetryAfter": true
}
```

Backoff is 1 s, 2 s, and 3 s; `maxDelayMs: 120000` first matters beyond attempt 120.

Exponential backoff:

```json
"httpRetryConfig": {
  "maxRetries": 6,
  "delayMs": 500,
  "networkErrors": true,
  "statusCodes": [408, 429, 500, 502, 503, 504],
  "backoff": { "strategy": "exponential", "multiplier": 2, "maxDelayMs": 30000 },
  "respectRetryAfter": true
}
```

Backoff is 500, 1000, 2000, 4000, 8000, and 16000 ms; no computed delay reaches the 30000 ms cap.

## Anti-Patterns

- Do NOT include `methods` in serialized JSON. StudioWeb never writes it, and `normalizeRetryConfig` ignores values other than the default `[GET]` for GET-only enforcement. It does not enable POST retries.
- Do NOT add `retry` or `retryConfig` to an individual activity. StudioWeb does not render one and the runtime ignores it.
- Do NOT set `maxRetries` to `0`. It retains a serialized key but never retries, equivalent to omission while consuming designer-state cycles; drop the key instead.
- Do NOT include `backoff.multiplier` with `constant` or `linear`. The discriminated union in `@uipath/api-workflow-commons/RetryConfig` rejects it, and StudioWeb prunes it on the next save.
- Do NOT expect a `UiPath.IntSvc` POST / PUT operation to retry. Connector send/create/update/delete calls are not GET. For those operations, build retry into control flow with TryCatch + DoWhile and `$attempt`.

## Sources

- Workflow extension type: `@uipath/api-workflow-executor/dist/models/workflow-extensions.d.ts` (`ExtendedWorkflow.httpRetryConfig?: RetryConfig`)
- `RetryConfig` shape + GET-only contract: `@uipath/api-workflow-commons/dist/activities/http/types/retry-config.d.ts`
- Backoff formulas + `shouldRetry` logic: `@uipath/api-workflow-commons/dist/activities/http/utils/http-retry-policy.js`
- StudioWeb defaults + UI bounds: `app/studio-web/main/features/designer/sidebar/properties-panel/api-workflow-properties/api-workflow-properties.component.ts`
- StudioWeb serializer (emits the key only when set): `app/packages/api-workflows/lib/translation/api-workflow-translator.ts`
- UI scope wording: `app/studio-web/main/assets/i18n/en.json` — `retry_description` and `retry_short_description`