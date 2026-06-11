---
confidence: medium
---

# O365 — Transient service error / timeout (5xx)

## Context

What this looks like — the job faults on a server-side or transport-level failure that is generally **not** caused by the workflow configuration. The message is one of:

- `The server is unable to process the current request.` — Microsoft Graph service unavailable (HTTP 503).
- `Request time out.`
- A raw inner message surfaced verbatim from a 500 / 504 or an HTTP request timeout (e.g. a `TaskCanceledException` / `HttpRequestException` message).
- `There was an error on the email server. Please try modifying your Query or Top values to continue.` — a Mail read (**Get Email List** (`GetEmailListConnections`), **Get Email By Id** (`GetEmailByIdConnections`)) caught a Microsoft Graph error whose code is `UnknownError` (keyed on the Graph error code, **not** a specific HTTP status); the advice is to narrow the query / lower `Top`.
- `(HTTP Status Code: <status>) Batching request failed with an unknown reason.` — a sub-request inside a batched operation failed (any non-success status — 5xx, or even 4xx / 429) and its error body couldn't be parsed.
- `Automation Cloud cannot be reached. It may be a network fluctuation on the Runtime machine.` — the Runtime machine couldn't reach the connection service.

What activities can produce this:
- **Any** Mail, Files/OneDrive, or Excel Online activity — the failure originates at the Microsoft Graph service or the network path, which every activity shares.

What can cause it:
- **Transient Microsoft Graph service errors** — 503 service-unavailable, 500 internal error, 504 gateway timeout. These usually clear on their own.
- **Request / transport timeout** — the HTTP call exceeded its timeout (slow Graph response, large payload, or a network stall).
- **Network fluctuation** reaching Automation Cloud / the connection service from the Runtime machine.
- **(Mail only) a too-broad query or a transient server-side error** surfaces the Graph `UnknownError` advisory above (narrow the query / lower `Top`). A genuinely *malformed* OData filter is a different, deterministic error — `Invalid Query. Please use OData format for filter queries. Press F1 for examples.` — not a transient, so it doesn't belong in this playbook.

What to look for:
- Intermittence — the same workflow succeeds on a later run. A consistent, repeatable failure usually points elsewhere (auth, scope, or a real not-found), not a transient.
- Design-time note: a transient failure while a Studio file/folder picker loads surfaces as `The items could not be retrieved...` in the picker (re-open it to retry) — that is the picker's own error, not the activity's runtime fault.

> **Different cause, do not apply this playbook:**
> - `Too many requests.` / `The app or user has been throttled.` (429) — rate limiting, not a service/transport error. Use **request-throttled**. (Exception: inside a *batched* operation, a throttled sub-request whose body can't be parsed can surface the same `Batching request failed with an unknown reason` text as a 5xx — check the embedded status code, not the sentence alone.)
> - 401 / 403 / 404 messages — authentication, permission, or not-found; these are deterministic, not transient. Use the matching playbook.

## Investigation

1. Read the exact message and decide whether it is intermittent (service/transport transient) or consistent (look elsewhere).
2. Re-run the workflow. If it now succeeds, the cause was transient and the fix is a retry strategy.
3. If the message is the Mail `... modify your Query or Top values ...` text, review the activity's filter/query and `Top`/`MaxResults`.
4. If `Automation Cloud cannot be reached`, check the Runtime machine's network connectivity to Automation Cloud.

## Resolution

- **Transient 503 / 500 / 504 / timeout:** retry with backoff — wrap the operation in a Retry scope (a few attempts with increasing waits). These failures typically clear without any configuration change.
- **Mail `modify your Query or Top values`:** simplify or correct the filter query and reduce `Top` / `MaxResults` so the server can process the request.
- **Network (`Automation Cloud cannot be reached`):** restore connectivity on the Runtime machine and re-run.

If a 503 / timeout reproduces consistently across retries over a sustained period, it is no longer transient — escalate (a Microsoft 365 service incident, or a proxy/firewall on the Runtime machine blocking Graph).
