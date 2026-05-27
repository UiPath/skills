# HTTP Retry Configuration

Workflow-level retry policy for HTTP calls. Declared as an OPTIONAL top-level `httpRetryConfig` key (sibling to `document`, `do`, `evaluate`). When absent, no retry — single attempt, fail fast.

## Scope — What Gets Retried

**GET requests only.** The executor's `HttpRetryPolicy.normalizeRetryConfig` defaults `methods` to `[GET]` and StudioWeb does not expose `methods` in the UI. POST / PUT / PATCH / DELETE are NEVER retried even when their failure matches `statusCodes` — bodies may not be idempotent, so the executor refuses to repeat them.

In practice, retries fire on:

1. **`UiPath.Http` activities** with `bodyParameters.method: "GET"` (HTTP Request curated activity)
2. **`UiPath.IntSvc` connector GET operations** — vendor list/get calls (e.g., `getNewestEmail`, `listEmails`, `listRecords`). Anything that internally issues a GET against the vendor API.

NOT retried:

- Any non-GET HTTP method
- Non-connector activities (Sequence / Assign / If / ForEach / DoWhile / TryCatch / Wait / Response / JS_Invoke) — no HTTP happens
- Vendor write operations (`sendEmail`, `createIssue`, `uploadFile`, …) — they are POST / PUT / PATCH

The setting is **workflow-level only**. There is no per-activity retry override.

## Top-Level Shape

```json
{
  "document": { /* … */ },
  "httpRetryConfig": {
    "maxRetries": 3,
    "delayMs": 1000,
    "networkErrors": true,
    "statusCodes": [408, 429, 500, 502, 503, 504],
    "backoff": {
      "strategy": "linear",
      "maxDelayMs": 120000
    },
    "respectRetryAfter": true
  },
  "do": [ /* … */ ],
  "evaluate": { "mode": "strict", "language": "javascript" }
}
```

## Field Reference

| Field | Type | Required | Default (when StudioWeb's "Retry on Failure" toggle is on) | UI bounds |
|-------|------|----------|------------------------------------------------------------|-----------|
| `maxRetries` | number | yes | `3` | 1–30 |
| `delayMs` | number | yes | `1000` | 0–900000 (15 min) |
| `networkErrors` | boolean | yes | `true` | — |
| `statusCodes` | number[] | yes | `[408, 429, 500, 502, 503, 504]` | each code 100–599; duplicates rejected |
| `backoff.strategy` | `"constant"` \| `"linear"` \| `"exponential"` | yes | `"constant"` | — |
| `backoff.maxDelayMs` | number | optional | `36000` (UI-emitted default; absent → uncapped) | 0–900000 |
| `backoff.multiplier` | number | **required iff `strategy === "exponential"`**; MUST be absent otherwise | `2` (when exponential) | 1–20 |
| `respectRetryAfter` | boolean | yes | `true` | — |

`maxRetries` is **retry attempts** — `maxRetries: 3` means up to 4 total HTTP calls (1 initial + 3 retries).

## Backoff Strategies — Formulas

Compiled formulas from `@uipath/api-workflow-commons` `HttpRetryPolicy.calculateDelay`. `n` = attempt number (1-based, counting retries only — 1 is the first retry after the initial failure).

| Strategy | Formula | Example with `delayMs: 1000`, `maxRetries: 4` |
|----------|---------|-----------------------------------------------|
| `constant` | `delay = delayMs` | 1000, 1000, 1000, 1000 |
| `linear` | `delay = delayMs * n` | 1000, 2000, 3000, 4000 |
| `exponential` | `delay = delayMs * multiplier^(n-1)` | (multiplier=2) 1000, 2000, 4000, 8000 |

Every computed delay is then capped: `actualDelay = min(delay, maxDelayMs)` when `maxDelayMs` is set. Example: with intervals 100ms, 200ms, 400ms and `maxDelayMs: 250`, actual delays are 100ms, 200ms, 250ms.

## When Each Retry Fires

`HttpRetryPolicy.shouldRetry` decision order:

1. `attemptNumber > maxRetries` → stop, return failure
2. **Response received:**
    - If `response.statusCode ∈ statusCodes` AND a `Retry-After` header is present → wait the header value (seconds or HTTP-date), ignore the computed backoff for this attempt
    - If `response.statusCode ∈ statusCodes` AND no `Retry-After` → wait computed backoff
    - Otherwise → stop, return the response as final
3. **No response (network error):**
    - If `networkErrors: true` AND error matches `ECONNRESET` / `ECONNREFUSED` / `ENOTFOUND` / `ETIMEDOUT` / `timeout` / `fetch failed` / `network error` / `aborted` → wait computed backoff, retry
    - Otherwise → stop, propagate the error

`respectRetryAfter` is a UI-emitted flag; the executor's `HttpRetryPolicy` always honors the `Retry-After` header when the response status is in `statusCodes`. Leave it `true` to match StudioWeb defaults.

## Authoring Rules

1. **Omit the whole key when retry is not desired.** Do NOT emit `httpRetryConfig: null` or an empty object — StudioWeb writes either a complete object or nothing at all.
2. **`backoff.multiplier` MUST appear only with `strategy: "exponential"`.** Including it with `constant` / `linear` is type-invalid in `@uipath/api-workflow-commons/RetryConfig`. Removing it when switching away from exponential is required.
3. **`statusCodes` MUST be integers in `[100, 599]`.** StudioWeb's properties panel silently drops out-of-range values; the executor passes them through `Array.includes` so values outside HTTP range never match. Use the canonical retryable list — `[408, 429, 500, 502, 503, 504]` — unless the upstream API documents different transient codes.
4. **Tune for GET-heavy workflows.** A workflow that only POSTs / PUTs gains nothing from this config. Add it when at least one task is `UiPath.Http` GET or an IntSvc list/get operation.
5. **Cap exponential growth with `maxDelayMs`.** Without it, `delayMs: 1000` + `multiplier: 2` + `maxRetries: 10` produces a 512-second wait before the last attempt. StudioWeb's UI default (`36000` = 36 s) is sensible; align with the workflow's overall SLA.
6. **`networkErrors: false` is rarely correct.** Most cloud failures present as transient network errors before any HTTP response arrives. Disable only when the caller has its own outer retry/circuit-breaker.

## Worked Examples

### Constant — fixed 2-second wait, 5 retries

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

Total worst-case wait: 5 × 2 s = 10 s of backoff. `maxDelayMs` omitted because constant cannot exceed `delayMs`.

### Linear — verified from sample workflow

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

Backoff sequence: 1 s, 2 s, 3 s. `maxDelayMs: 120000` would only kick in beyond attempt 120.

### Exponential — aggressive backoff for rate-limited APIs

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

Backoff sequence: 500, 1000, 2000, 4000, 8000, 16000 ms. With `maxDelayMs: 30000`, none of the computed delays cap — attempt 7 would be the first capped at 30 s.

## Anti-patterns

- **Do NOT** include `methods` in the serialized JSON. StudioWeb never writes it, and the executor's `normalizeRetryConfig` ignores any value other than the default `[GET]` for GET-only enforcement. Authoring it manually does not enable POST retries.
- **Do NOT** add a `retry` / `retryConfig` field to an individual activity. There is no per-activity override surface; StudioWeb's properties panel does not render one and the runtime ignores it.
- **Do NOT** set `maxRetries` to `0`. `maxRetries: 0` keeps the key serialized but never retries — equivalent to omitting `httpRetryConfig` entirely, while consuming designer-state cycles. Just drop the key.
- **Do NOT** include `backoff.multiplier` when `strategy` is `constant` or `linear`. The union type in `@uipath/api-workflow-commons/RetryConfig` is discriminated — the extra field is invalid and the StudioWeb undo/redo state machine prunes it on the next save.
- **Do NOT** expect a `UiPath.IntSvc` POST/PUT operation to retry. Connector "send" / "create" / "update" / "delete" calls are not GET — `httpRetryConfig` does not apply. For those, build retry into control flow (TryCatch + DoWhile with `$attempt`).

## Sources

- Workflow extension type: `@uipath/api-workflow-executor/dist/models/workflow-extensions.d.ts` (`ExtendedWorkflow.httpRetryConfig?: RetryConfig`)
- `RetryConfig` shape + GET-only contract: `@uipath/api-workflow-commons/dist/activities/http/types/retry-config.d.ts`
- Backoff formulas + `shouldRetry` logic: `@uipath/api-workflow-commons/dist/activities/http/utils/http-retry-policy.js`
- StudioWeb defaults + UI bounds: `app/studio-web/main/features/designer/sidebar/properties-panel/api-workflow-properties/api-workflow-properties.component.ts`
- StudioWeb serializer (emits the key only when set): `app/packages/api-workflows/lib/translation/api-workflow-translator.ts`
- UI scope wording: `app/studio-web/main/assets/i18n/en.json` — `retry_description` and `retry_short_description`
