# Orchestrator API Limits

Automation Cloud Orchestrator enforces per-tenant rate limits on the Jobs and QueueItems list endpoints, a daily quota on export endpoints, a page-size cap on queue items, and size caps on large queue-item fields. Several `uip or` commands sit directly on these endpoints, so a loop or poller built from them can exhaust the tenant's budget for every other caller — including the tenant's own external integrations and monitoring tools.

> The numbers below mirror the official page: [Orchestrator API Guide — Rate limits and large data field usage optimization](https://docs.uipath.com/orchestrator/automation-cloud/latest/api-Guide/rate-limits). That page is the source of truth. Re-read it before quoting a limit to a user. These limits apply to Automation Cloud only; standalone (on-premises) Orchestrator does not enforce them.

---

## Critical Rules

1. **Watch a known job with `uip or jobs get <job-key>`, never with a repeated `jobs list`.** `jobs get` looks up the job id and then reads `GET /odata/Jobs(<id>)`, which is not rate limited. `jobs list` is `GET /odata/Jobs` and is rate limited with or without filters.
2. **Prefer `jobs start --wait-for-completion` over a hand-written wait loop.** It polls through the same `Jobs(<id>)` path at `--poll-interval` (default 5s).
3. **Budget every `uip` call and external script at 100 requests per minute for the whole tenant.** Only calls made by the Get Jobs, Get Queue Items and Orchestrator HTTP Request activities inside a running job count as automation usage (1,000 per minute). The CLI, PowerShell scripts, monitoring tools and other integrations share the 100-per-minute budget.
4. **Do not use `--export` for routine log or audit reads.** `uip or jobs logs --export` and `uip or audit-logs list --export` call export endpoints capped at **100 requests per day per tenant**, resetting at 00:00 UTC and shared with everyone on the tenant. Read with `--output json` and paginate. Export only when the user explicitly asks for a CSV file.
5. **Keep `--limit` at 100 or below on `queue-items list`.** `GET /odata/QueueItems` rejects `$top` above 100 with HTTP 400. Paginate with `--offset` (see [orchestrator.md — Pagination pattern](orchestrator.md#common-flags)).
6. **The CLI does not retry a 429.** It returns `Result: Failure` with `ErrorCode: rate_limited` and a `Retry` hint. Handle it as described in [Handling a 429](#handling-a-429). Never retry immediately in a tight loop.

---

## Rate-Limited Endpoints

| Endpoint | `uip` commands that call it | Limit (per tenant) |
|---|---|---|
| `GET /odata/Jobs` (with or without filters) | `uip or jobs list` | 100 requests/min non-automation, 1,000 requests/min automation |
| `GET /odata/QueueItems` (with or without filters) | `uip or queue-items list` | 100 requests/min non-automation, 1,000 requests/min automation |
| `POST /odata/RobotLogs/UiPath.Server.Configuration.OData.Export` | `uip or jobs logs <job-key> --export` | 100 requests/day |
| `POST /odata/AuditLogs/UiPath.Server.Configuration.OData.Export` | `uip or audit-logs list --export` | 100 requests/day |
| `POST /odata/Jobs/UiPath.Server.Configuration.OData.Export` | none (REST only) | 100 requests/day |
| `POST /odata/QueueDefinitions({key})/UiPathODataSvc.Export` | none (REST only) | 100 requests/day |

- **Automation usage** means calls from the Get Jobs, Get Queue Items and Orchestrator HTTP Request activities. **Non-automation usage** means calls from outside processes: scripts, third-party monitoring tools, the `uip` CLI, external applications.
- **Not rate limited:** `GET /odata/Jobs(<id>)`, adding queue items, setting queue item status, and starting or processing jobs.
- **The per-minute window is rolling, counted to the second** — not aligned to clock minutes. 50 calls in the second half of one minute plus 60 in the first half of the next exceed the limit.
- **Exceeding an export quota** returns error `#4502` ("daily limit per tenant has been reached") until 00:00 UTC.
- Endpoints not listed here have no documented limit, but can still be throttled at the network edge under heavy load (see [Handling a 429](#handling-a-429)).

### Response headers

| Header | Meaning |
|---|---|
| `Retry-After` | Returned with HTTP 429. Seconds to wait; retries inside that window also get 429. |
| `X-RateLimit-Remaining` | Calls left in the current window. Reports `0` once fewer than 10 calls per minute remain. |

### Checking tenant usage

Tenant admins can see per-minute call volumes for these endpoints under **Monitoring → API audit** (requires Audit - View; data lags by up to 20 minutes), and can subscribe to the **API Rate Limits** alerts in alert settings. Point the user there when a 429 is recurring and the competing caller is unknown.

---

## Handling a 429

A rate-limited `uip` call fails with this shape:

```json
{
  "Result": "Failure",
  "ErrorCode": "rate_limited",
  "Retry": "<RETRY_HINT>",
  "Context": { "httpStatus": 429, "retryAfter": "<SECONDS>" }
}
```

`Retry` is `RetryAfter1Second`, `RetryAfter10Seconds`, `RetryAfter30Seconds` or `RetryAfter60Seconds` when the server sent `Retry-After`, and `RetryLater` when it did not.

1. Wait the number of seconds in `Retry-After` (surfaced in `Context`), or the `Retry` hint's duration, before the next call.
2. With no `Retry-After`, back off exponentially: start at 10s, double on each consecutive 429, and stop after 3 attempts.
3. After retries are exhausted, stop and report the 429 to the user. Name the command and the likely competing load — other scripts, dashboards, integrations or robots on the same tenant — and point to the API audit view. Do not keep retrying in the background.
4. Before retrying a loop, remove the cause. Replace `jobs list` polling with `jobs get`, raise the poll interval, or batch the work.

For direct REST calls, honor `Retry-After` the same way and read `X-RateLimit-Remaining` to slow down before it reaches 0. A 429 from the network edge (for example on `GET /odata/RobotLogs` under a burst of reads) may carry its wait time as `retry_after` in the response body instead of a header — honor it the same way, and pace bulk reads with a rolling per-minute budget rather than a fixed delay.

---

## Large Data Fields

### Queue item field size caps

Counted in UTF-16 characters (each character is 2 bytes in storage, so a UTF-8 byte count underestimates usage for non-ASCII text). A write above a cap returns an error.

| Queue item field | Limit |
|---|---|
| `Progress` | 104,857 characters |
| `AnalyticsData` / `Analytics` | 5,120 characters |
| `OutputData` / `Output` | 51,200 characters |
| `SpecificContent` / `SpecificData` | 256,000 characters |
| `ProcessingException` `Reason` | 102,400 characters |
| `ProcessingException` `Details` | 102,400 characters |

When a payload approaches a cap, store the bulk data in a storage bucket ([work-with-storage.md](work-with-storage.md)) or a Data Fabric entity, and put only a reference (bucket path, record id) into the field.

### Fields omitted from the Jobs list

`GET /odata/Jobs` (`uip or jobs list`) returns `InputArguments` and `OutputArguments` as `null`. Read them per job with `uip or jobs get <job-key> --output json`.

---

## Anti-Patterns

| Do not | Do instead |
|---|---|
| Loop `uip or jobs list --state Running` every few seconds to wait for a job | `uip or jobs get <job-key> --output json` on an interval, or `jobs start --wait-for-completion` |
| `uip or jobs logs <job-key> --export` to read errors for a diagnosis | `uip or jobs logs <job-key> --level Error --output json` |
| `uip or queue-items list --limit 500` | `--limit 100` and page with `--offset` until `HasMore` is `false` |
| Retry a `rate_limited` failure immediately | Wait `Retry-After` (or back off), then retry at most 3 times |
| Run several scripts or pollers against the same tenant, each assuming its own 100/min | Share one per-minute budget across all of them |
| Put a large DataTable or file content in `SpecificContent` or `OutputData` | Store it in a bucket or entity and pass a reference |
