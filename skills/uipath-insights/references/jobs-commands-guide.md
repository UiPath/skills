# Insights Jobs — Command Reference

Complete reference for `uip insights jobs` subcommands with response shapes and examples.

## Shared Options

Every subcommand accepts these filter options:

```text
--time-range <minutes>         Relative time range (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d), 1 to 527040
--started-after <epoch-ms>     Absolute start time as Unix epoch milliseconds, 0 to 253402300799000
--started-before <epoch-ms>    Absolute end time as Unix epoch milliseconds, 0 to 253402300799000
--folder-key <guid>            Folder key filter (repeatable)
--process-name <name>          Process name filter (repeatable)
--machine-name <name>          Machine name filter (repeatable)
--timezone-offset <minutes>    Client timezone offset from UTC, -1440 to 1440
```

A value outside those bounds, or one that is not a plain integer, is rejected at parse time with `Result: ValidationError`, `ErrorCode: invalid_argument`, and exit 3. The largest `--time-range` is one 366-day year in minutes, the epoch bound is 9999-12-31T23:59:59Z, and the offset bound is a day either way.

`--output <format>` is a global CLI option available on every command: `table`, `json`, `yaml`, `plain`. Always use `json`.

**Time range rule:** Either `--time-range` OR both `--started-after` and `--started-before` must be provided. Omitting both is rejected locally with a `Failure` envelope and exit 1.

**Window clamp:** the backend caps a relative range at 30 days, and it moves any absolute bound more than 30 whole days old to 30 days ago. Both happen with no signal in the response. The seven plain reads forward the window unchanged, so a 90-day request answers with 30 days of data and the envelope says nothing about the difference. Only the `jobs investigate` playbooks refuse a window the clamp would move.

Jobs commands take no `--limit` or `--offset`. A jobs response is complete for its time window.

**Repeatable options:** `--folder-key`, `--process-name`, and `--machine-name` can be specified multiple times:
```bash
uip insights jobs summary --time-range 1440 \
  --process-name "ProcessA" \
  --process-name "ProcessB" \
  --output json
```

## Response Envelope

All `jobs` subcommands return:
```json
{
  "Result": "Success",
  "Code": "<CommandCode>",
  "Data": { ... }
}
```

A successful jobs response never carries `Pagination`. It carries `Instructions` on `top-failures`, `failures-by-reason`, `process-details`, and `failure-details`, because each of those projections owes the caller a caveat. Any read invoked with `--output-file` carries one too. `summary`, `completed-timeline`, and `uncompleted-timeline` carry `Instructions` only in that `--output-file` form. Quote the text in the answer wherever it is present. The `filter-*` and alert commands carry `Instructions` as well, and their list subcommands also carry `Pagination`.

`Code` identifies the subcommand that produced the response:

| Subcommand | `Code` |
|---|---|
| `summary` | `InsightsJobsSummary` |
| `completed-timeline` | `InsightsJobsCompletedTimeline` |
| `uncompleted-timeline` | `InsightsJobsUncompletedTimeline` |
| `top-failures` | `InsightsJobsTopFailures` |
| `failures-by-reason` | `InsightsJobsFailuresByReason` |
| `process-details` | `InsightsJobsProcessDetails` |
| `failure-details` | `InsightsJobsFailureDetails` |

On error:
```json
{
  "Result": "Failure",
  "Message": "<error description>",
  "Instructions": "<how to fix>",
  "ErrorCode": "permission_denied",
  "Retry": "RetryWillNotFix"
}
```

Branch on `Result`, `ErrorCode`, and `Retry` as described in SKILL.md Critical Rule 8, never on the wording of `Message`. Every failure envelope carries both `ErrorCode` and `Retry`: the writer names them where it knows the failure mode, and the formatter fills the rest from the HTTP status and the `Result`. Every HTTP failure also carries `Context` with `httpStatus`, `endpoint`, and sometimes `requestId` and `retryAfter`. A failure raised before any request is sent carries no `Context`.

| `Result` | `ErrorCode` | Exit | Cause |
|---|---|---|---|
| `ValidationError` | `invalid_argument` | 3 | A flag the command does not accept, or a value outside the bounds under Shared Options. Commander rejects it before the command runs |
| `Failure` | `unknown_error` | 1 | A missing time range, no usable session, or no tenant selected. All are raised locally, so none carries `Context` |
| `Failure` | `local_permission_denied` | 1 | An `--output-file` write the OS refused. Another kind of write failure, such as a path that is a directory, reports `unknown_error`. `Message` names the path either way |
| `AuthenticationError` | `authentication_required` | 2 | 401. `Message` says the request was not authenticated |
| `Failure` | `permission_denied` | 1 | 403. The caller's folder map is empty, or it does not hold a folder key the request named |
| `Failure` | `rate_limited` | 1 | 429, with `Retry: RetryLater`. Report and stop |
| `ConfigError` | `configuration_error` | 1 | 404. The jobs routes are feature-gated to Cloud and Dedicated SaaS, so the only 404 they answer means the surface is off for this deployment. It says nothing about the tenant's data or the caller's permissions |
| `Failure` | derived from `Context.httpStatus` | 1 | Any other HTTP status, with `Message` reading `Insights request failed with HTTP <status> for <endpoint>`. A 5xx gets `server_error` and `Retry: RetryLater` |
| `Failure` | `network_error` | 1 | DNS, socket, proxy, or TLS failure. `Retry` is `RetryLater`, or `RetryWillNotFix` for a TLS trust failure, which needs a configuration change |
| `Failure` | `unknown_error` | 1 | A 200 body that fails the selected route's contract. The instructions say retrying cannot fix a malformed response, so report the endpoint instead |

A 401 is the only failure on these reads that exits 2. A logged-out session exits 1 here, where the alert and filter commands exit 2 for the same state.

The `filter-*`, alert, and `jobs investigate` commands share this writer, so a 401, 403, 429, or 404 reads the same way there as it does here.

## Response Data Shape

Null, empty, or zero across every field on a `Success` response means the query matched no rows. It is not a failure, and it does not on its own prove that no jobs ran. See the last row of Troubleshooting for the causes and what to report.

Every route answers with one wide DTO and fills only the fields its own query produces. **The CLI does not print that DTO.** Each read projects its response into named columns, so `Data` carries only what that route fills, and each series has a name instead of a position inside `jobCountByTime`.

**Keys inside `Data` are PascalCase in the CLI's JSON output.** Read `CompletedJobs`, not `completedJobs`.

Three shapes come back:

- **Scalars.** `summary` returns three numbers and nothing else.
- **Named columns.** `completed-timeline`, `uncompleted-timeline`, `top-failures`, `process-details`, and `failure-details` return arrays of equal length, one per column. `ProcessName[i]` and `FaultedJobs[i]` describe the same entity. An empty window returns `{}`, because there is no row to take column names from; that is not an error.
- **Scalars plus named columns.** `failures-by-reason` is a hybrid. It emits `CompletedJobs` and `AttributedFailures` on every response, then the `FailedJobs` and `Reason` columns from the same pivot the column reads use. When no reason row came back it keeps the two scalars and drops the two columns, so `Data` on an empty window is those two keys rather than `{}`.

Columns rather than one object per row on purpose: a row repeats every key name once per entity, which on a 30-day window costs about half again as many tokens as columns.

Two reads take `--output-file <path>`, which writes the backend's own body (camelCase keys, no `Result`/`Code`/`Data` wrapper) while stdout keeps the projected form. Use it on `failures-by-reason` to recover the untruncated exception text, and on `failure-details` when the row count is large. The two channels are not interchangeable: redirected stdout is PascalCase and wrapped. The file also keeps the backend's row order while `failures-by-reason` sorts stdout by count, so the same index is not the same row in both.

With `--output-file` the success envelope gains two keys beside `Data`: `OutputFile`, the absolute path written, and `Bytes`, the size of that file. Read `OutputFile` to find the artifact rather than assuming the path passed in. The file is written before the envelope, and a failed write emits a `Failure` envelope with exit 1, so a `Success` never names a file that is not on disk.

## Commands

### summary

Get job KPIs: total count, successful count, and average processing time.

```bash
uip insights jobs summary --time-range 1440 --output json
```

**Data:** `CompletedJobs`, `SuccessfulJobs`, `AverageProcessingTimeMs`. `CompletedJobs` counts jobs in a terminal state (`Faulted`, `Successful`, `Stopped`), so a running job is not in it. The average is milliseconds, from the `AVERAGE_PROCESSING_TIME_IN_MS` column. The query behind the average also requires a non-empty machine name, which the `CompletedJobs` query does not, so the average can cover fewer jobs than `CompletedJobs` counts.

**Use when:** User asks "how are my automations doing?" or "what's my job success rate?"

### completed-timeline

Get completed jobs over time, grouped by job state.

```bash
uip insights jobs completed-timeline --time-range 1440 --output json
```

**Columns:** `BucketStart`, `BucketEnd`, `Faulted`, `Successful`, `Stopped`

**Use when:** User asks for job completion trends or when most jobs run.

### uncompleted-timeline

Get running and pending jobs over time.

```bash
uip insights jobs uncompleted-timeline --time-range 1440 --output json
```

**Columns:** `BucketStart`, `Running`, `Pending`, `Resumed`, `Suspended`, `Other`. No `BucketEnd`: this handler declares it and never fills it.

**Use when:** User asks whether jobs are stuck or how many jobs are still running.

### top-failures

Get processes ranked by failure count.

```bash
uip insights jobs top-failures --time-range 43200 --output json
```

**Columns:** `ProcessName`, `FaultedJobs`. Counts `Faulted` only, not `Stopped`, and the backend caps the list at 10 ranked by that count.

**Use when:** User asks which processes fail most.

### failures-by-reason

Get job failures grouped by exception reason, with total job count for context.

```bash
uip insights jobs failures-by-reason --time-range 1440 --output json
```

**Data:** `CompletedJobs`, `AttributedFailures`, plus the columns `FailedJobs` and `Reason`. `CompletedJobs` is every terminal job in the window, not a failure count: the controller fills it from the same handler `summary` uses. `AttributedFailures` sums the per-reason counts and covers `Faulted` plus `Stopped` jobs that have a known machine, so it can sit below both. `Reason` is the first line of the exception text, capped at 200 characters and marked with `[…]`; pass `--output-file` for the whole trace.

**Use when:** User asks why jobs are failing or what the common error messages are.

### process-details

Get per-process job counts by state.

```bash
uip insights jobs process-details --time-range 1440 --output json
```

**Columns:** `ProcessName`, `FolderName`, the seven states (`Running`, `Pending`, `Resumed`, `Suspended`, `Faulted`, `Successful`, `Stopped`) and three durations (`AverageDurationMs`, `MedianDurationMs`, `P90DurationMs`, the 90th percentile). `FolderName` is the leaf folder, not the fully-qualified path `filter-folders list` reports.

**Use when:** User asks for per-process statistics or which process has the most faulted jobs.

### failure-details

Get detailed failure information for investigation.

```bash
uip insights jobs failure-details --time-range 1440 --output json
```

**Columns:** `ProcessName`, `JobKey`, `FolderId`, `CreatedAt`, `StartedAt`, `EndedAt`, `DurationMs`. This route reports no machine name and no exception type; it fills neither. The backend returns up to 1000 rows newest-first and does not dedupe, so one job can appear twice. `--output-file` writes the whole body.

**Use when:** User asks for recent failure details.

## Example: Summary

```bash
$ uip insights jobs summary --time-range 1440 --output json
{
  "Result": "Success",
  "Code": "InsightsJobsSummary",
  "Data": {
    "CompletedJobs": 142,
    "SuccessfulJobs": 135,
    "AverageProcessingTimeMs": 45700
  }
}
```

Three keys. `SuccessfulJobs` is always a number, because the summary handler cannot answer without it and a null there is reported as a contract failure. `CompletedJobs` and `AverageProcessingTimeMs` pass through from the backend and can be null, which is what an empty window prints. The other 23 fields of the wide DTO are not emitted.

Deriving metrics:
- **Failure rate:** `(CompletedJobs - SuccessfulJobs) / CompletedJobs * 100`. The remainder is `Faulted` plus `Stopped`, so a cancelled job counts against it.
- **Success rate:** `SuccessfulJobs / CompletedJobs * 100`

Check `CompletedJobs` for null and for zero before dividing by it. Report that no jobs completed in the window instead of a rate.

`uip insights jobs investigate health` returns both, already derived and banded.

## Example: Top Failures with Filter

```bash
$ uip insights jobs top-failures --time-range 43200 \
    --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
    --output json
{
  "Result": "Success",
  "Code": "InsightsJobsTopFailures",
  "Data": {
    "ProcessName": ["Invoice_Processing", "Email_Parser", "Data_Upload"],
    "FaultedJobs": [23, 15, 8]
  },
  "Instructions": "FaultedJobs counts JOBSTATE = 'Faulted' only, and the backend caps this list at 10 rows ranked by that count."
}
```

`Instructions` is the fourth top-level key here, because this route always attaches a note.

`ProcessName` and `FaultedJobs` are parallel: index 0 of both is the same process. Every column on every read pairs this way, and each one carries its own name, so nothing indexes into a position inside the wire's unnamed `jobCountByTime`.

## Absolute Time Ranges

**Treat `--started-before` as exclusive.** For "July 1 through July 5 inclusive", pass July 1 00:00:00 UTC and July 6 00:00:00 UTC. Resolve both boundaries before writing the command. The CLI forwards the value unchanged, so the boundary is a backend behavior and is not confirmed against a live tenant.

Resolve exact date boundaries to epoch milliseconds before running a Jobs command. Run the date conversion separately, read its output, then pass literal values to `uip`. Do not embed shell substitutions or variables in the Insights command. The `date` flags differ between macOS and Linux, so a substitution that fails silently turns the flag into garbage, queries the wrong window, and leaves the logged command showing a range that was never asked for.

```bash
# Linux
date -u -d "2026-07-01 00:00:00" +%s000
date -u -d "2026-07-06 00:00:00" +%s000

# macOS
date -u -j -f "%Y-%m-%d %H:%M:%S" "2026-07-01 00:00:00" +%s000
date -u -j -f "%Y-%m-%d %H:%M:%S" "2026-07-06 00:00:00" +%s000
```

Then use the literal results:

```bash
uip insights jobs summary \
  --started-after 1782864000000 \
  --started-before 1783296000000 \
  --output json
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Not logged in. …` | No active session, or it expired | Tell the user to run `uip login`, or follow the hint the message carries |
| `Tenant not provided and UIPATH_TENANT_NAME not set. …` | A session exists but no tenant is selected | Tell the user to run `uip login tenant set <tenant>`, or `uip login` to re-select one. The message names both |
| `A time range is required.` | Neither `--time-range` nor both halves of `--started-after`/`--started-before` was passed | Add `--time-range 1440`, or pass both absolute bounds |
| `Result: AuthenticationError` with exit 2 | A 401: the session is expired, missing, or scoped to another tenant | Tell the user to re-login, then confirm the active tenant |
| `ErrorCode: permission_denied` | A 403: the caller has no permission on the folders in scope | Check folder assignments in Orchestrator admin |
| `ErrorCode: server_error`, `Context.httpStatus` in the 500s | Backend fault | Report it with the time window and filters. Do not retry automatically |
| `Result: ConfigError` with `ErrorCode: configuration_error` | A 404: the jobs routes are not served on this deployment class | Report that these commands need a cloud deployment. Do not retry and do not re-login |
| `Result: Failure` whose instructions say retrying cannot fix a malformed response | The 200 body failed the route's contract: a null `successfulJobsCount`, or series whose lengths disagree | Report the endpoint and the window to the Insights owner. Do not retry; the same request returns the same body |
| Every `Data` field null, empty, or zero on a `Success` response | No rows matched: narrow window, no visible folders, or the wrong tenant | Widen `--time-range` (43200 covers 30 days), confirm the tenant, then report what the result does not prove |

A missing time range cannot reach the server. The command rejects it locally and exits 1 before it builds a session or sends a request, so the envelope is `Result: Failure` with `ErrorCode: unknown_error` and never an HTTP status.

## API Details

- **Base URL:** `{host}/{orgId}/{tenantName}/insightsrtm_/api/v1.0/InsightsJobs/{endpoint}`
- **Method:** POST (all endpoints)
- **Auth:** Bearer token + `X-UiPath-Internal-AccountName` + `X-UiPath-Internal-TenantName` headers
- **The CLI handles all of this.** Do not construct raw API calls — use `uip insights jobs <subcommand>`.
