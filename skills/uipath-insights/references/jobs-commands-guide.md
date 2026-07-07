# Insights Jobs — Command Reference

Complete reference for `uip insights jobs` subcommands with response shapes and examples.

## Shared Options

Every subcommand accepts these filter options:

```
--time-range <minutes>         Relative time range (e.g. 1440 = 24h, 43200 = 30d)
--started-after <epoch-ms>     Absolute start time as Unix epoch milliseconds
--started-before <epoch-ms>    Absolute end time as Unix epoch milliseconds
--folder-key <guid>            Folder key filter (repeatable)
--process-name <name>          Process name filter (repeatable)
--machine-name <name>          Machine name filter (repeatable)
--timezone-offset <minutes>    Client timezone offset from UTC
--output <format>              Output format: json, yaml, table (always use json)
```

**Time range rule:** Either `--time-range` OR both `--started-after` and `--started-before` must be provided. Omitting both causes a validation error.

**Repeatable options:** `--folder-key`, `--process-name`, and `--machine-name` can be specified multiple times:
```bash
uip insights jobs summary --time-range 1440 \
  --process-name "ProcessA" \
  --process-name "ProcessB" \
  --output json
```

## Response Envelope

All commands return:
```json
{
  "Result": "Success",
  "Code": "<CommandCode>",
  "Data": { ... }
}
```

On error:
```json
{
  "Result": "Failure",
  "Message": "<error description>",
  "Instructions": "<how to fix>",
  "ErrorCode": "unknown_error"
}
```

## Response Data Shape

All endpoints return the same `JobsResponse` shape. Fields are populated or null depending on the endpoint:

```typescript
interface JobsResponse {
  jobState: string[] | null;
  robotName: string[] | null;
  processName: string[] | null;
  jobCount: number[] | null;
  jobCountByTime: number[][] | null;
  folderName: string[] | null;
  folderKey: string[] | null;
  machineName: string[] | null;
  hostMachineName: string[] | null;
  machineKey: string[] | null;
  machineStatus: string[] | null;
  timestamp: string[] | null;
  processExceptionType: string[] | null;
  processExceptionReason: string[] | null;
  startTime: string[] | null;
  endTime: string[] | null;
  utilizationTime: string[] | null;
  duration: number[] | null;
  successRate: number[] | null;
  averageProcessingTime: number | null;
  jobsCount: number | null;
  successfulJobsCount: number | null;
  jobAggregate: number[][] | null;
  creationTime: string[] | null;
  folderId: string[] | null;
  jobKey: string[] | null;
}
```

## Per-Endpoint Key Fields

| Endpoint | Code | Key Data Fields |
|----------|------|-----------------|
| `summary` | `InsightsJobsSummary` | `jobsCount`, `successfulJobsCount`, `averageProcessingTime` |
| `completed-timeline` | `InsightsJobsCompletedTimeline` | `jobState`, `jobCountByTime`, `timestamp` |
| `uncompleted-timeline` | `InsightsJobsUncompletedTimeline` | `jobState`, `jobCountByTime`, `timestamp` |
| `top-failures` | `InsightsJobsTopFailures` | `processName`, `jobCountByTime` |
| `failures-by-reason` | `InsightsJobsFailuresByReason` | `processExceptionReason`, `processName`, `robotName`, `jobsCount` |
| `process-details` | `InsightsJobsProcessDetails` | `processName`, `jobAggregate` |
| `failure-details` | `InsightsJobsFailureDetails` | `processName`, `machineName`, `processExceptionReason`, `startTime`, `endTime` |

## Example: Summary

```bash
$ uip insights jobs summary --time-range 1440 --output json
{
  "Result": "Success",
  "Code": "InsightsJobsSummary",
  "Data": {
    "jobsCount": 142,
    "successfulJobsCount": 135,
    "averageProcessingTime": 45.7,
    "jobState": null,
    "processName": null,
    ...
  }
}
```

Deriving metrics:
- **Failure rate:** `(jobsCount - successfulJobsCount) / jobsCount * 100`
- **Success rate:** `successfulJobsCount / jobsCount * 100`

## Example: Top Failures with Filter

```bash
$ uip insights jobs top-failures --time-range 43200 \
    --folder-key "a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
    --output json
{
  "Result": "Success",
  "Code": "InsightsJobsTopFailures",
  "Data": {
    "processName": ["Invoice_Processing", "Email_Parser", "Data_Upload"],
    "jobCountByTime": [[23, 15, 8]],
    ...
  }
}
```

The `processName` array and `jobCountByTime[0]` array are parallel — index 0 of both corresponds to the same process.

## API Details

- **Base URL:** `{host}/{orgId}/{tenantName}/insightsrtm_/api/v1.0/InsightsJobs/{endpoint}`
- **Method:** POST (all endpoints)
- **Auth:** Bearer token + `X-UiPath-Internal-AccountName` + `X-UiPath-Internal-TenantName` headers
- **The CLI handles all of this.** Do not construct raw API calls — use `uip insights jobs <subcommand>`.
