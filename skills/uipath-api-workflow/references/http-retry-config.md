# Retry Configuration

API workflows retry at two levels:

| Level | Where | Studio Web control | Retries |
|---|---|---|---|
| Task-level | `catch.retry` on a `try` task | **Retry** section of a Try/Catch or an HTTP Request activity | Re-runs the whole `try` block; any method, any activity |
| Workflow-level | top-level `httpRetryConfig` | Workflow properties → **Retry on Failure** | Transport-level re-send of HTTP **GET** calls only |

Choose task-level retry when one activity needs its own policy, when the call is not a GET, or when the retry must cover several activities. Choose workflow-level retry for a blanket GET policy.

## Task-Level Retry (`catch.retry`)

A `try` task's `catch` may carry a `retry` policy next to `as` and `do`. On a caught error the executor re-runs the whole `try` list while the policy allows it, then hands the last error to `catch.do`.

### Policy Fields

| Field | Meaning | Executor default | Studio Web default when Retry is on |
|---|---|---|---|
| `limit.attempt.count` | Retries after the initial failure (`3` = up to four runs). `0` disables retrying. | `3` | `3` |
| `delay` | Base delay; `{ "milliseconds": N }` or ISO 8601 string | none | `{ "milliseconds": 1000 }` |
| `backoff` | `{ "constant": {} }`, `{ "linear": {} }` (`delay × attempt`), or `{ "exponential": {} }` (`delay × 2^(attempt − 1)`) | constant | `{ "constant": {} }` |
| `when` | String expression evaluated against `$<catch.as>`; retry only when truthy | retry every caught error | Try/Catch: absent, and dropped on save (no status filter). HTTP Request: status filter, see below |
| `exceptWhen` | Inverse gate of `when` | — | never written |
| `jitter` | `{ "from": <duration>, "to": <duration> }` random delay added to every wait | none | never written |
| `limit.duration` | Total retry time budget from first failure | none | never written |
| `backoff.exponential.multiplier` / `maxDelay` | Exponential growth factor (default `2`) and delay cap (also caps `Retry-After`) | `2` / 5 min cap on `Retry-After` | never written |

Studio Web edits only `limit.attempt.count`, `delay.milliseconds`, the backoff key, and (HTTP Request) the status list. Write those fields, in that shape, for a workflow that must stay editable in the designer. `limit.attempt.duration` (per-attempt timeout) is unsupported and ignored.

### Runtime Behavior

1. `$<catch.as>.status` holds the **real HTTP status** (`429`, `503`, …) for failed HTTP, Connector, and Connector-event calls; the full response sits under `$<catch.as>.data.cause`. Status filters therefore work directly.
2. A `Retry-After` header on the caught response raises the next delay to its value when larger than the computed backoff (capped at 5 minutes unless `maxDelay` is set).
3. Every retry emits a `task_retried` event (`attempt`, `maxAttempts`, `delayMs`, `failedTaskName`); run panels and traces show one entry per attempt.
4. After the last retry, or when `when` rejects the error:
   - **with `catch.do`**: `catch.do` runs with the error bound to `$<catch.as>`;
   - **without `catch.do`**: the error propagates, exactly as if the inner task had failed unwrapped.
5. Task-level retry is not GET-only. A retried POST / PUT / DELETE is sent again; retry it only when the endpoint is idempotent or the user accepts duplicate side effects.

### Try/Catch With Retry

Retry section on: the `catch` gets `retry` beside `as` and `do`. Studio Web's Try/Catch has no status filter: it writes no `when`, and every caught error is retried.

```json
"Try_Catch_1": {
  "try": [ { "HttpRequest_1": { "call": "UiPath.Http", "...": "registry stub, unchanged" } } ],
  "catch": {
    "as": "error",
    "retry": {
      "delay": { "milliseconds": 1000 },
      "backoff": { "constant": {} },
      "limit": { "attempt": { "count": 3 } }
    },
    "do": [ { "Assign_1": { "set": { "failedStatus": "${$error.status}" }, "...": "..." } } ]
  },
  "export": { "as": "{ ...$context, outputs: { ...$context?.outputs, \"Try_Catch_1\": $output } }" },
  "metadata": { "activityType": "TryCatch", "displayName": "Try Catch", "fullName": "TryCatch" }
}
```

Do not add a `when` to a Try/Catch that must stay editable in Studio Web. The executor honors it, but Studio Web reads back only the count, delay, and backoff, so its next save drops the filter and the Try/Catch retries every error again. To retry an HTTP call only on certain statuses, use the HTTP Request's own Retry section (the `#Retry` wrapper below). Complete example: [assets/templates/retry-http-request-example.json](../assets/templates/retry-http-request-example.json).

### HTTP Request With Retry (`<id>#Retry` Wrapper)

Retry section on the HTTP Request activity: Studio Web wraps the call in a `try` task keyed `<id>#Retry`. The display metadata moves from the call to the wrapper, its `catch` has `retry` and **no `do`**, the error name is `__retryError`, and **Retry on status codes** becomes the `when` condition (default `[408, 429, 500, 502, 503, 504]`). A disabled activity's `if` moves from the call to the wrapper.

```json
"HttpRequest_1#Retry": {
  "try": [
    {
      "HttpRequest_1": {
        "call": "UiPath.Http",
        "with": { "...": "registry stub, unchanged" },
        "export": { "as": "...registry stub, unchanged" },
        "metadata": {
          "configuration": "<stub metadata.configuration>",
          "uiPathActivityTypeId": "<stub metadata.uiPathActivityTypeId>",
          "assemblyQualifiedName": "Connector"
        }
      }
    }
  ],
  "catch": {
    "as": "__retryError",
    "retry": {
      "when": "${ [408, 429, 500, 502, 503, 504].includes($__retryError.status) }",
      "delay": { "milliseconds": 1000 },
      "backoff": { "constant": {} },
      "limit": { "attempt": { "count": 3 } }
    }
  },
  "metadata": {
    "activityType": "Connector",
    "displayName": "HTTP Request",
    "fullName": "Connector",
    "configuration": "<same as the call>",
    "uiPathActivityTypeId": "<same as the call>"
  }
}
```

Rules for the wrapper:

1. `try` holds exactly one task, the `call` task. To wrap a registry stub the way Studio Web does:
    - keep the call's key, `call`, `with`, `export`, and its other `metadata` (`configuration`, `uiPathActivityTypeId`, `assemblyQualifiedName`, …) unchanged; downstream reads stay `$context.outputs.<ExportBucketKey>`;
    - move `activityType`, `displayName`, and `fullName` from the call's `metadata` to the wrapper's;
    - copy `configuration` and `uiPathActivityTypeId` onto the wrapper as well, so they sit on both.

    A call that still has its own `activityType` / `displayName` (a stub wrapped as-is) restores the same: Studio Web reads both from the wrapper only and drops them from the call on its next save. Leave such a workflow as it is.
2. Never add `catch.do`: Studio Web reads a wrapper with `do` as a plain Try/Catch, and without `do` exhausted retries fail the workflow as the bare call would.
3. The wrapper key `<id>#Retry` is reserved and must be globally unique like `#Wrapper` / `#Body`.
4. Some `validate` releases reject this shape; see [Validation Gap](#validation-gap).
5. Edit an existing wrapper in place (count, delay, backoff, status list); do not unwrap or convert it.
6. Keep `when` in exactly the `${ [<codes>].includes($__retryError.status) }` form. It is the only `when` Studio Web reads back into **Retry on status codes**.

### Validation Gap

`uip api-workflow validate` releases without UiPath/cli#5785 reject two valid task-level retry forms:

1. A string `retry.when` or `retry.exceptWhen`, on a `#Retry` wrapper or a Try/Catch: three errors at `…/catch/retry/when` (or `…/catch/retry/exceptWhen`): `Expected type 'object' but got a different type`, `Expected type 'array' but got a different type`, and `Value must match exactly one of the allowed formats`.
2. An `<id>#Retry` wrapper: the error `Task '<id>#Retry' has activityType 'Connector' but must contain 'call'. Missing key: 'call'` at the wrapper path. The call inside a wrapper in Studio Web's shape also gets two warnings at `…#Retry/try/0/<id>/metadata`: `Task '<id>' is missing 'metadata.activityType'. Studio Web cannot restore this activity without it` and `Task '<id>' is missing 'metadata.displayName'`. Both are part of the same gap: the wrapper carries those fields, so do not put them back on the call. A wrapper with no `metadata.configuration` also gets `Connector task '<id>#Retry' is missing 'metadata.configuration'`; that one is real, so copy the call's `configuration` onto the wrapper (rule 1).

When those are the only errors and warnings, treat the workflow as valid and report the validator gap; otherwise fix normally. Do not reshape the workflow to silence them: leave `when` and the wrapper as they are. For a new retry that must validate clean on such a release and needs no status filter, write a Try/Catch whose `retry` has no `when`; it retries every caught error. A release with UiPath/cli#5785 reports none of these and adds its own retry messages; see [troubleshooting.md](troubleshooting.md#validate-warns-that-studio-web-drops-part-of-a-retry-policy).

### Precedence Over `httpRetryConfig`

A `try` with `catch.retry` **replaces** workflow-level `httpRetryConfig` for every call inside its `try` block; the two never stack. The decision is static: if the task policy's `when` rejects an error (retries only 401, call returns 500), the call is not retried at all, even when `httpRetryConfig` would have retried it. Calls inside `catch.do`, and calls outside any retrying `try`, still use `httpRetryConfig`. A nested `try` without its own policy inside a retrying `try` is covered by the outer policy.

### Verifying Retries at Runtime

<!--skill-flavor:task-retry-runtime:start-->
Task-level retry needs an executor that supports `catch.retry`. A `uip` release whose bundled executor predates it ignores `catch.retry`: the try block runs once, and a `#Retry` wrapper (no `catch.do`) then completes with the error object as its output instead of failing. When a local `uip api-workflow run` shows no `task_retried` events for a failing retried call, report the executor gap rather than changing the policy; verify retry behavior after publish.
<!--skill-flavor:task-retry-runtime:end-->

## Workflow-Level Retry (`httpRetryConfig`)

Configure workflow-level retries for HTTP calls with the optional top-level `httpRetryConfig` key, sibling to `document`, `do`, and `evaluate`. If absent, calls outside a retrying `try` make one attempt and fail fast.

### Scope

Only GET requests are retried. `HttpRetryPolicy.normalizeRetryConfig` defaults `methods` to `[GET]`, and StudioWeb does not expose `methods`. POST, PUT, PATCH, and DELETE are never retried, even when their failures match `statusCodes`, because request bodies may not be idempotent.

Applicable calls:

- `UiPath.Http` activities with `bodyParameters.method: "GET"` (HTTP Request curated activity).
- `UiPath.IntSvc` connector GET operations, including vendor list/get calls.

Not applicable: non-GET HTTP methods; non-connector activities such as Sequence, Assign, If, ForEach, DoWhile, TryCatch, Wait, Response, and JS_Invoke; vendor send, create, upload, update, and delete operations; or any call inside a `try` with `catch.retry` (see precedence above). A workflow containing only POST / PUT calls gains nothing from this setting; use task-level retry.

### Configuration

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

### Backoff and Retry Decisions

`HttpRetryPolicy.calculateDelay` uses `n` as the 1-based retry number (task-level backoff shares this arithmetic):

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

### Authoring Rules

1. Omit the whole key when retries are not desired. Do not emit `httpRetryConfig: null` or `{}`; StudioWeb writes either a complete object or nothing.
2. Include the configuration when at least one task is a `UiPath.Http` GET or an IntSvc list/get operation. Tune it for GET-heavy workflows.
3. `backoff.multiplier` MUST appear only with `strategy: "exponential"`; remove it when switching to `constant` or `linear`.
4. `statusCodes` MUST contain integers in `[100, 599]`. StudioWeb silently drops out-of-range values; the executor passes them to `Array.includes`, where they never match. Use `[408, 429, 500, 502, 503, 504]` unless the upstream API documents different transient codes.
5. Cap exponential growth with `maxDelayMs`. Without a cap, `delayMs: 1000`, `multiplier: 2`, and `maxRetries: 10` produce a 512-second wait before the last attempt. StudioWeb’s `36000` (36 s) default is sensible; align it with the workflow SLA.
6. `networkErrors: false` is rarely correct. Disable it only when the caller has its own outer retry or circuit breaker.

### Examples

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

- Do NOT put `retry` or `retryConfig` directly on an activity (`"HttpRequest_1": { "call": …, "retry": … }`). Retry lives only in `catch.retry` of a `try` task — a Try/Catch or an `<id>#Retry` wrapper.
- Do NOT add `catch.do` to an `<id>#Retry` wrapper, or put more than one task in its `try`. Studio Web then shows a Try/Catch, not the HTTP Request's Retry section.
- Do NOT expect `httpRetryConfig` to add retries inside a retrying `try`, or the two policies to multiply; the task-level policy replaces it there.
- Do NOT read `$error.message` or assume `$error.status` is always `500`; failed HTTP calls carry the real status.
- Do NOT retry a non-idempotent POST / PUT / DELETE without the user accepting duplicate side effects.
- Do NOT include `methods` in serialized `httpRetryConfig`. StudioWeb never writes it, and `normalizeRetryConfig` ignores values other than the default `[GET]` for GET-only enforcement. It does not enable POST retries.
- Do NOT set `httpRetryConfig.maxRetries` to `0`. It retains a serialized key but never retries, equivalent to omission while consuming designer-state cycles; drop the key instead.
- Do NOT include `backoff.multiplier` with `constant` or `linear` in `httpRetryConfig`. The discriminated union in `@uipath/api-workflow-commons/RetryConfig` rejects it, and StudioWeb prunes it on the next save.
- Do NOT expect `httpRetryConfig` to retry a `UiPath.IntSvc` POST / PUT operation. Connector send/create/update/delete calls are not GET; wrap them in a Try/Catch with `catch.retry`.

## Sources

- Task-level retry semantics: `@uipath/api-workflow-executor` README, "Error handling and retries (`try` / `catch` / `retry`)"
- Studio Web task-level shapes and defaults: `retry-policy-translators.ts` (`packages/api-workflows-common`), `retry-wrapper.ts` and `try-catch-translator.ts` (`packages/api-workflows`)
- Workflow extension type: `@uipath/api-workflow-executor/dist/models/workflow-extensions.d.ts` (`ExtendedWorkflow.httpRetryConfig?: RetryConfig`)
- `RetryConfig` shape + GET-only contract: `@uipath/api-workflow-commons/dist/activities/http/types/retry-config.d.ts`
- Backoff formulas + `shouldRetry` logic: `@uipath/api-workflow-commons/dist/activities/http/utils/http-retry-policy.js`
- StudioWeb defaults + UI bounds: `app/studio-web/main/features/designer/sidebar/properties-panel/api-workflow-properties/api-workflow-properties.component.ts`
- StudioWeb serializer (emits the key only when set): `app/packages/api-workflows/lib/translation/api-workflow-translator.ts`
- UI scope wording: `app/studio-web/main/assets/i18n/en.json` — `retry_description` and `retry_short_description`
