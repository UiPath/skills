# Queue Monitoring Commands

The `queues` commands report on queue item processing: totals, SLA risk, state over time, failures, per-queue detail, and retry outcomes. They answer "how is this queue doing", not "which queues exist"; use `filter-queues list` for discovery and for the exact queue names these commands filter on.

Every command needs a time range and returns rows scoped to the folders the caller can access.

Keys inside `Data` are PascalCase in the CLI's JSON output. Read `QueueName`, not `queueName`.

## Shared Options

```text
--time-range <minutes>        Relative window ending now
--started-after <epoch-ms>    Absolute window start, needs --started-before
--started-before <epoch-ms>   Absolute window end, needs --started-after
--folder-key <guids...>       Folder keys to restrict to, space separated
--queue-name <names...>       Queue names to restrict to, space separated
--limit <number>              Rows to return, 1 to 10000 (default 50)
--offset <number>             Rows to skip before returning results (default 0)
--output <format>             Output format: table, json, yaml, plain (always use json)
```

`queues summary` returns one object, so it takes no `--limit` or `--offset`. The two timeline commands add `--time-event` and `--timezone-offset`; nothing else does.

## Rules

1. **A time range is required and its units are minutes or epoch milliseconds.** Pass `--time-range <minutes>` (60 = 1h, 1440 = 24h, 43200 = 30d), or both `--started-after` and `--started-before` in epoch milliseconds. Passing both forms is rejected. Omitting a time range is rejected locally and exits 3. `uip insights alert-history` takes its bounds in epoch **seconds**, so do not carry a value between the two families: a seconds value here is rejected locally, with a message telling you to multiply by 1000.
2. **The server silently caps the window at 30 days.** A longer `--time-range` is clamped and an absolute bound older than 30 days is moved forward, with nothing in the response saying so. Never report a window longer than 30 days as the window queried.
3. **Results are permission-bounded.** Without `--folder-key` the backend substitutes every folder the caller can access, not every folder in the tenant. A `--folder-key` outside that set returns a 403 for the whole request.
4. **Repeat calls inside a minute return the same numbers.** The server caches each distinct request for 60 seconds. Say so before presenting a figure as current during a live incident.
5. **Every page repeats the whole backend request.** These commands page the CLI's own copy of the list. `--limit` defaults to 50, so a 50-row result is a full page rather than a complete list; read `Pagination.Total` and `Pagination.HasMore`.
6. **`--folder-key` takes a GUID, and no queue command returns one.** `queues details` returns `FolderName`, a display name. Map a name to its key with `uip insights filter-folders list` before filtering on it. `queues failure-details` returns `FolderId`, whose relationship to the folder key is not confirmed; map it the same way rather than feeding it back in.
7. **Some rows repeat a queue name legitimately.** `queues sla` is one row per queue and process pair, and `queues details` is one row per queue and folder pair.
8. **A null string field is an answer, not an error.** Several columns are null by construction, most often the SLA breach times. Report what the null means for that field rather than treating the row as broken or the value as blank.
9. **Row order is the server's on `top-failures`, `failure-details`, `operational-metrics`, and both timelines.** Those five queries order their own rows and the CLI does not re-sort them. `sla`, `details`, `failures-by-reason`, and `retry-outcomes` are sorted by the CLI before paging.
10. **These commands need a Cloud or Dedicated SaaS deployment.** On Automation Suite and Service Fabric they return `Result: ConfigError` with `ErrorCode: configuration_error` before the tenant is consulted. That is a deployment fact, not a permission or data answer, and retrying will not change it.

## Errors

`queues` failures use the same `Result` values as the other families, plus the deployment gate. Branch on `Result`, not on `ErrorCode` alone.

| `Result` | `ErrorCode` | Exit | Cause |
|---|---|---|---|
| `ValidationError` | `invalid_argument` | 3 | A missing or conflicting time range, a `--folder-key` that is not a GUID, an empty `--queue-name`, or a flag the command does not accept |
| `AuthenticationError` | `authentication_required` | 2 | 401, or no usable session before any request is sent |
| `ConfigError` | `configuration_error` | nonzero | 404. The queue routes are not served on this deployment |
| `Failure` | `permission_denied` | 1 | 403. The caller has no Insights access, or asked for a folder outside their set |
| `Failure` | `rate_limited` | 1 | 429. Report it and stop |
| `Failure` | `timeout` | 1 | The request was cancelled or timed out. Narrow the window or the filters |
| `Failure` | `server_error` | 1 | The warehouse behind Insights is degraded. The request itself was accepted |
| `Failure` | `network_error` | 1 | DNS, socket, proxy, or TLS failure |
| `Failure` | `unknown_error` | 1 | A malformed or misaligned response from the service |

Every failure also carries `Retry`; branch on it as described in SKILL.md Critical Rule 8.

## Commands

### queues summary

Total and successful queue item counts plus average processing time for the window. One object, no pagination.

```bash
uip insights queues summary --time-range 1440 --output json
```

`Data`: `SuccessfulQueueItems`, `TotalQueueItems`, `AverageProcessingTimeMs`. Each is a backend count from its own query, and each can be `null`. A `null` means the query returned no row for that value; report it as unavailable, never as zero. Start a queue investigation here, then drill down.

### queues sla

SLA bucket counts, first breach times, and robot demand, one row per queue and process pair.

```bash
uip insights queues sla --time-range 1440 --output json
```

`Data[]`: `QueueName`, `ProcessName`, `InSlaCount`, `AtRiskCount`, `OutOfSlaCount`, `FirstSlaBreachAt`, `FirstRiskBreachAt`, `AverageHandlingTimeMs`, `AveragePendingTimeMs`, `RunningRobots`, `NecessaryRobots`.

This row mixes two time windows. The SLA bucket counts, the two breach times, and `NecessaryRobots` use the range you asked for. `AverageHandlingTimeMs`, `AveragePendingTimeMs`, and `RunningRobots` come from queries with a fixed 30-day window and do not narrow with `--time-range`. Never present those three as figures for a shorter window.

`FirstSlaBreachAt`, `FirstRiskBreachAt`, and `ProcessName` are null when the query has no answer for that queue. A null breach time means nothing is predicted to breach, which is a result worth reporting, not missing data.

### queues completed-timeline and queues uncompleted-timeline

Queue item counts per time bucket. `completed-timeline` covers terminal states, `uncompleted-timeline` covers active ones.

```bash
uip insights queues completed-timeline --time-range 1440 --output json
uip insights queues uncompleted-timeline --time-range 1440 --output json
```

`completed-timeline` `Data[]`: `StartTime`, `EndTime`, `Failed`, `Successful`, `Abandoned`, `Deleted`.
`uncompleted-timeline` `Data[]`: `StartTime`, `EndTime`, `New`, `InProgress`, `Retried`.

`Failed` on the completed timeline counts failed and retried items together, so a retried item shows as failed there and again as `Retried` on the uncompleted timeline. Bucket width is chosen by the server from the window length and is not returned as a field; `StartTime` and `EndTime` are the authority, and rows arrive in the backend's chronological order.

Both take two extra flags. `--time-event <latest|creation|start|end>` picks which queue item timestamp the buckets are built from and defaults to `latest`. `--timezone-offset <minutes>` shifts the bucket boundaries from UTC. No other queue command accepts either.

### queues top-failures

Queues ranked by failed items.

```bash
uip insights queues top-failures --time-range 43200 --output json
```

`Data[]`: `QueueName`, `ApplicationExceptions`, `BusinessExceptions`, `ClassifiedFailures`.

The server returns at most ten queues, already ranked by its own failure total, and the rows stay in that order. A queue missing from this list is not proof it had no failures.

`ClassifiedFailures` is the sum of the two exception counts and is not the queue's failure total. The server ranks on a count that also includes failures with no exception type and never returns that count, so a queue can sit at the top of this list with a low `ClassifiedFailures`. Report the two typed counts, and do not present `ClassifiedFailures` as the number of failures.

### queues failures-by-reason

Failure counts grouped by exception reason and type.

```bash
uip insights queues failures-by-reason --time-range 43200 --output json
uip insights queues failures-by-reason --time-range 43200 --group-by queue --output json
```

`Data[]`: `ExceptionReason`, `ExceptionType`, `Count`, plus `QueueName` when `--group-by queue` was passed and `RobotName` when `--group-by robot` was. A column that was not requested is absent from the row rather than present and null. `--group-by` accepts only `queue` and `robot`, space separated for both.

### queues failure-details

The individual queue items that failed with one exact exception reason.

```bash
uip insights queues failure-details --time-range 43200 --error-message "Business rule failed" --output json
```

`Data[]`: `QueueName`, `QueueId`, `QueueItemId`, `QueueItemKey`, `FolderId`, `CreatedAt`, `StartedAt`, `EndedAt`, `DurationMs`.

`--error-message` is required and is an exact match, so take it verbatim from a `failures-by-reason` row rather than retyping it. `--robot-name` takes one name, not a list. The server returns at most 1000 items, newest processing end first.

### queues details

Per-queue and per-folder item counts across eight states, with duration aggregates.

```bash
uip insights queues details --time-range 1440 --output json
```

`Data[]`: `QueueName`, `FolderName`, `Successful`, `FailedBusiness`, `FailedApplication`, `Deleted`, `Abandoned`, `New`, `InProgress`, `Retried`, `AverageDurationMs`, `MedianDurationMs`, `PercentileDurationMs`.

Durations are milliseconds and `PercentileDurationMs` is the 90th percentile.

### queues retry-outcomes

Retried items and how many later succeeded, per queue.

```bash
uip insights queues retry-outcomes --time-range 43200 --output json
```

`Data[]`: `QueueName`, `RetriedItems`, `SuccessfulItems`, `SuccessRatePercent`.

`SuccessRatePercent` describes retried items only. It is not the queue's overall success rate; use `queues summary` for that. The backend computes it on a 0 to 100 scale rounded to two decimals and the CLI passes it through unchanged.

### queues operational-metrics

The Dedicated SaaS queue operations table.

```bash
uip insights queues operational-metrics --time-range 1440 --widget-type non-rda --output json
```

Rows stay in the server's own `RUN_DATE` order. `RunDate` is a date string whose format the backend does not declare, so do not re-sort or parse it.

`Data[]`: `TenantName`, `RunDate`, `L1FolderName`, `L2FolderName`, `L3FolderName`, `AirId`, `QueueName`, `OpeningBalance`, `Loaded`, `Completed`, `SystemException`, `BusinessException`, `Abandoned`, `Pending`, `Reconcile`, `SuccessPercentage`.

`--widget-type <rda|non-rda>` is required. This table is served only on Dedicated SaaS: on any other deployment the backend returns an empty list rather than an error, so an empty result cannot tell "no rows" from "not a Dedicated SaaS tenant". Say which of the two you can rule out and which you cannot.
