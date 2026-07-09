---
confidence: medium
---

# HTTP Request (NetHttpRequest) — Aggregate Exception

## Context

What this looks like:
- A `UiPath.Web.Activities.NetHttpRequest` (modern **HTTP Request**) activity faults with `System.AggregateException` and the message `One or more errors occurred. (<inner message>)`.
- `NetHttpRequest` runs an async pipeline over `System.Net.Http.HttpClient` with a retry policy; when the pipeline faults the task exception surfaces as an `AggregateException` **wrapper**. The real cause is the inner exception.
- Note: `NetHttpRequest` defaults `ContinueOnError = True`, so HTTP error statuses (4xx/5xx) normally do NOT fault — they return a response summary. A faulted job means either `ContinueOnError = False` or a transport/timeout/setup failure the pipeline could not turn into a response.

What can cause it (read the inner exception):
- **Inner `System.Net.Http.HttpRequestException`** — transport/HTTP failure after retries: DNS resolution failure, connection refused, SSL/TLS handshake failure, or (when `ContinueOnError = False`) a non-success status the retry policy exhausted.
- **Inner `System.Threading.Tasks.TaskCanceledException` / `TimeoutException`** — the request exceeded `TimeoutInMiliseconds` (default `10000` ms). See [http-request-timeout.md](./http-request-timeout.md) for the legacy analog.
- **Inner validation/setup exception** — bad `RequestUrl`, unresolved `ConnectionId`, or invalid auth configuration surfaced during input preprocessing.

What to look for:
- **`InnerException` / `InnerExceptions` type and message** — the decisive signal; the `AggregateException` text alone is not enough.
- **`RequestUrl`, `TimeoutInMiliseconds`, `RetryCount`, `ContinueOnError`, `AuthenticationType`** from the workflow source.
- **Trace spans** — expose the request URL, attempt count, and HTTP status across retries.

## Investigation

1. **Confirm the signature + activity.** `uip or jobs get <job-key> --output json` → `Info` shows `System.AggregateException`; `JobError.ActivityName` = the `NetHttpRequest` activity.
2. **Unwrap the inner exception.** Read the inner type/message from the `Info` stack (and from `uip or jobs traces <job-key> --output json` / `uip traces spans get --job-key <job-key> --output json`). This selects the branch.
3. **Branch on the inner exception:**
   - `HttpRequestException` → transport/status: apply [http-request-connection-failure.md](./http-request-connection-failure.md) (DNS / connection / TLS / status).
   - `TaskCanceledException` / `TimeoutException` → timeout: apply [http-request-timeout.md](./http-request-timeout.md) against `TimeoutInMiliseconds`.
   - validation/setup → fix the named input (`RequestUrl`, `ConnectionId`, auth).
4. **Read the request configuration from source** to confirm the branch (URL, timeout, retry, auth).

## Resolution

- **Resolve by inner cause, not the wrapper.** Map the unwrapped inner exception to its fix using the cross-referenced playbook above (connection/status, or timeout).
- **Validation/setup inner exception:** correct the offending input — fix `RequestUrl`, resolve/select a valid `ConnectionId`, or supply the credentials/token the chosen `AuthenticationType` requires.
- **Retry exhausted on a transient fault:** raise `RetryCount` / adjust the retry policy if the endpoint is intermittently slow, but only after confirming the inner cause is genuinely transient.
