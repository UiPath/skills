# Insights Jobs — Command Reference

Complete reference for `uip insights jobs` subcommands with response shapes and examples.

## Shared Options

Every subcommand accepts these filter options:

```text
--time-range <minutes>         Relative time range (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d)
--started-after <epoch-ms>     Absolute start time as Unix epoch milliseconds
--started-before <epoch-ms>    Absolute end time as Unix epoch milliseconds
--folder-key <guid>            Folder key filter (repeatable)
--process-name <name>          Process name filter (repeatable)
--machine-name <name>          Machine name filter (repeatable)
--timezone-offset <minutes>    Client timezone offset from UTC
```

`--output <format>` is a global CLI option available on every command: `table`, `json`, `yaml`, `plain`. Always use `json`.

**Time range rule:** Either `--time-range` OR both `--started-after` and `--started-before` must be provided. Omitting both is rejected locally with a `Failure` envelope and exit 1.

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

There is no `Pagination` field and no `Instructions` field on a successful jobs response. The `filter-*` and alert commands carry `Instructions`, and their list subcommands also carry `Pagination`.

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
  "ErrorCode": "unknown_error",
  "Retry": "RetryWillNotFix"
}
```

Branch on `Retry` as described in SKILL.md Critical Rule 8, rather than on the wording of `Message`.

On a failure the command emits itself, `ErrorCode` is always `unknown_error`, including auth and permission failures, because the HTTP status never reaches the field. Read the status out of `Message`, which carries it as `API request failed: <status> <statusText> - <body>`. Do not branch on `ErrorCode` here. A jobs `Message` without that prefix carries no HTTP status: it is local validation, a session problem, or a transport failure such as `fetch failed` or an unparseable body.

A rejected flag is a different shape. Commander catches it before the command runs and returns `Result: ValidationError` with `ErrorCode: invalid_argument` and exit 3.

`filter-*` HTTP failures report a specific `ErrorCode` such as `authentication_required` or `permission_denied`. A malformed `filter-*` response still reports `unknown_error`.

## Response Data Shape

Null, empty, or zero across every field on a `Success` response means the query matched no rows. It is not a failure, and it does not on its own prove that no jobs ran. See the last row of Troubleshooting for the causes and what to report.

All endpoints return the same shape. Which fields are populated depends on the endpoint.

**Keys inside `Data` are PascalCase in the CLI's JSON output.** The CLI PascalCases every `Data` key before printing, so read `JobsCount`, not `jobsCount`. The type below is the SDK's `JobsResponse` in its camelCase source form. Every field is optional, so a field the endpoint does not populate may be absent or null.

```typescript
interface JobsResponse {
  jobState?: string[];
  robotName?: string[];
  processName?: string[];
  jobCount?: number[];
  jobCountByTime?: number[][];
  folderName?: string[];
  folderKey?: string[];
  machineName?: string[];
  hostMachineName?: string[];
  machineKey?: string[];
  machineStatus?: string[];
  timestamp?: string[];
  processExceptionType?: string[];
  processExceptionReason?: string[];
  startTime?: string[];
  endTime?: string[];
  utilizationTime?: string[];
  duration?: number[];
  successRate?: number[];
  averageProcessingTime?: number;
  jobsCount?: number;
  successfulJobsCount?: number;
  jobAggregate?: number[][];
  creationTime?: string[];
  folderId?: string[];
  jobKey?: string[];
}
```

## Commands

### summary

Get job KPIs: total count, successful count, and average processing time.

```bash
uip insights jobs summary --time-range 1440 --output json
```

**Key Data fields:** `JobsCount`, `SuccessfulJobsCount`, `AverageProcessingTime`

**Use when:** User asks "how are my automations doing?" or "what's my job success rate?"

### completed-timeline

Get completed jobs over time, grouped by job state.

```bash
uip insights jobs completed-timeline --time-range 1440 --output json
```

**Key Data fields:** `JobState`, `JobCountByTime`, `Timestamp`

**Use when:** User asks for job completion trends or when most jobs run.

### uncompleted-timeline

Get running and pending jobs over time.

```bash
uip insights jobs uncompleted-timeline --time-range 1440 --output json
```

**Key Data fields:** `JobState`, `JobCountByTime`, `Timestamp`

**Use when:** User asks whether jobs are stuck or how many jobs are still running.

### top-failures

Get processes ranked by failure count.

```bash
uip insights jobs top-failures --time-range 43200 --output json
```

**Key Data fields:** `ProcessName`, `JobCountByTime`

**Use when:** User asks which processes fail most.

### failures-by-reason

Get job failures grouped by exception reason, with total job count for context.

```bash
uip insights jobs failures-by-reason --time-range 1440 --output json
```

**Key Data fields:** `ProcessExceptionReason`, `ProcessName`, `RobotName`, `JobsCount`

**Use when:** User asks why jobs are failing or what the common error messages are.

### process-details

Get per-process job counts by state.

```bash
uip insights jobs process-details --time-range 1440 --output json
```

**Key Data fields:** `ProcessName`, `JobAggregate`

**Use when:** User asks for per-process statistics or which process has the most faulted jobs.

### failure-details

Get detailed failure information for investigation.

```bash
uip insights jobs failure-details --time-range 1440 --output json
```

**Key Data fields:** `ProcessName`, `MachineName`, `ProcessExceptionReason`, `StartTime`, `EndTime`

**Use when:** User asks for recent failure details or which machines are affected.

## Example: Summary

```bash
$ uip insights jobs summary --time-range 1440 --output json
{
  "Result": "Success",
  "Code": "InsightsJobsSummary",
  "Data": {
    "JobsCount": 142,
    "SuccessfulJobsCount": 135,
    "AverageProcessingTime": 45.7,
    "JobState": null,
    "ProcessName": null,
    ...
  }
}
```

Deriving metrics:
- **Failure rate:** `(JobsCount - SuccessfulJobsCount) / JobsCount * 100`
- **Success rate:** `SuccessfulJobsCount / JobsCount * 100`

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
    "JobCountByTime": [[23, 15, 8]],
    ...
  }
}
```

The `ProcessName` array and `JobCountByTime[0]` array are parallel: index 0 of both corresponds to the same process.

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
| `API request failed: 401 …` | The session is expired, missing, or scoped to another tenant | Tell the user to re-login, then confirm the active tenant |
| `API request failed: 403 …` | The caller has no permission on the folders in scope | Check folder assignments in Orchestrator admin |
| `API request failed: 5xx …` | Backend fault | Report it with the time window and filters. Do not retry automatically |
| Every `Data` field null, empty, or zero on a `Success` response | No rows matched: narrow window, no visible folders, or the wrong tenant | Widen `--time-range` (43200 covers 30 days), confirm the tenant, then report what the result does not prove |

A missing time range cannot reach the server. The command rejects it locally and exits 1 before it builds a session or sends a request, so the envelope is `Result: Failure` with `ErrorCode: unknown_error` and never an HTTP status.

## API Details

- **Base URL:** `{host}/{orgId}/{tenantName}/insightsrtm_/api/v1.0/InsightsJobs/{endpoint}`
- **Method:** POST (all endpoints)
- **Auth:** Bearer token + `X-UiPath-Internal-AccountName` + `X-UiPath-Internal-TenantName` headers
- **The CLI handles all of this.** Do not construct raw API calls — use `uip insights jobs <subcommand>`.
