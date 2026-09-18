# Queue Monitoring Commands

The `queues` commands report on queue item processing: totals, SLA risk, state over time, failures, per-queue detail, and retry outcomes. They answer "how is this queue doing", not "which queues exist"; use [`filter-discovery-guide.md`](filter-discovery-guide.md)'s `filter-queues list` for discovery and for the exact queue names these commands filter on.

Every command needs a time range. Every result covers only the folders the caller can access.

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
--output <format>             table, json, yaml, plain, markdown (always use json)
```

`queues summary` returns one object, so it takes no `--limit` or `--offset`. Each flag below is accepted by the one or two commands named beside it and by nothing else in the family:

```text
--time-event <event>          both timelines; choices differ per command
--timezone-offset <minutes>   both timelines; -1440 to 1440
--group-by <dimensions...>    failures-by-reason only; queue and robot
--error-message <text>        failure-details only, and one of these two is required
--null-error-message          failure-details only, for the null-reason row
--robot-name <name>           failure-details only, one name
--widget-type <rda|non-rda>   operational-metrics only, and mandatory there
```

## Rules

1. **A time range is required and its units are minutes or epoch milliseconds.** Pass `--time-range <minutes>` (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d), or both `--started-after` and `--started-before` in epoch milliseconds. Passing both forms is rejected. Omitting a time range is rejected locally and exits 3. `uip insights alert-history` takes its bounds in epoch **seconds**, so do not carry a value between the two families: a seconds value here is rejected locally, with a message telling you to multiply by 1000.
2. **The server caps the window at 30 days, and the CLI tells you when it did.** A `--time-range` above 43200 is clamped to exactly 30 days. An absolute bound is queried as given until it is a full 31 days old, when the server moves it to the 30-day boundary; its test truncates to whole days, so a bound aged 30 days and 23 hours passes through untouched. Each bound clamps on its own and the server then adds a millisecond to the end, so a window whose end is also past the cap collapses to about a millisecond and comes back as an empty success. Read that as an artifact of the clamp rather than an absence of data, and keep the end of a historical window inside 30 days. The server announces neither clamp, but the CLI detects both and reports them in `Instructions`, so read those on any window near the cap and report the window they describe. Never report a longer window as the window queried.
3. **Results are permission-bounded.** Without `--folder-key` the backend substitutes every folder the caller can access, not every folder in the tenant. A `--folder-key` outside that set returns a 403 for the whole request. A caller with no folder access at all gets an empty success instead of a 403, so run `uip insights filter-folders list` before reporting an empty result as no activity.
4. **Figures are cached in 60-second buckets.** The server floors each request's timestamp to a 60-second boundary to build its cache key, and the CLI sends no bypass flag. Two calls in the same bucket return identical numbers; two calls seconds apart that straddle a boundary need not. Say so before presenting a figure as current during a live incident.
5. **Prefer one high-limit call over walking `--offset`.** These commands page the CLI's own copy of the list, so every offset page re-fetches the whole list from the backend. `--limit` defaults to 50, so a 50-row result is a full page rather than a complete list. Read `Pagination.Total`, which counts the rows the server returned for this request rather than a tenant-wide total, and `Pagination.HasMore`. Stop after ten pages and report how many rows you retrieved.
6. **`--folder-key` takes a GUID, and no queue command returns one.** `queues details` returns `FolderName`, a display name; map it to a key with [`filter-discovery-guide.md`](filter-discovery-guide.md)'s `uip insights filter-folders list` before filtering on it. `queues failure-details` returns `FolderId`, Orchestrator's numeric folder id, which is a different column from the GUID `FolderKey` that `--folder-key` takes. It can never be passed to `--folder-key`, and `filter-folders list` returns nothing to join it against, so resolve folder scope up front instead.
7. **`--queue-name` is an exact match.** The backend compares the name literally, with no case folding and no partial match, so a caller-supplied name that differs from the real one by a suffix or a case returns zero rows. On an empty page with a name you did not read from `filter-queues list`, suspect the name before the window.
8. **Rows are keyed on display names, which merges some of them.** `queues details` is one row per queue and folder pair, keyed on both display names, so two folders sharing a name become one row and so do two queues sharing a name inside one folder. `queues sla` is one row per queue name, so two same-named queues in different folders also arrive as one row. Never present such a row as one queue's figures without saying the name may cover more than one, and do not match these rows one to one against `filter-queues list`.
9. **A null is an answer, and what it means depends on the field.** Read the field's own meaning in its command's section rather than treating the row as broken or the value as blank. A null count on `queues summary` means the value is unavailable, never zero.
10. **Do not re-sort, and do not assume an order means a ranking.** `top-failures`, `failure-details`, `operational-metrics`, and both timelines arrive in the server's own order and the CLI passes it through. `sla`, `details`, `failures-by-reason`, and `retry-outcomes` are sorted by the CLI before paging, so their order is not the server's. Only `top-failures` is a ranking the server computed, and its section explains what it ranks on.
11. **Empty is never proof.** An empty queue result can reflect the 30-day clamp (Rule 2), a caller with no folder access (Rule 3), an inexact `--queue-name` (Rule 7), a warehouse that returned nothing, or real absence. Each command's section names its own extra causes. Say what the result rules out and what it leaves open.
12. **These commands need a Cloud or Dedicated SaaS deployment.** On Automation Suite and Service Fabric they return `Result: ConfigError` with `ErrorCode: configuration_error` before the tenant is consulted. That is a deployment fact, not a permission or data answer, and retrying will not change it.

## Errors

`queues` failures use the same `Result` values and the same error mapping as the other families. Branch on `Result`, not on `ErrorCode` alone, because `ConfigError` and `Failure` share exit 1.

| `Result` | `ErrorCode` | Exit | Cause |
|---|---|---|---|
| `ValidationError` | `invalid_argument` | 3 | A missing or conflicting time range, a `--folder-key` that is not a GUID, an empty `--queue-name`, or a flag the command does not accept |
| `AuthenticationError` | `authentication_required` | 2 | 401, or no usable session before any request is sent |
| `ConfigError` | `configuration_error` | 1 | 404 with no body. The queue routes are not served on this deployment |
| `Failure` | `not_found` | 1 | 404 with a body. Not expected from the queue routes: a failed Orchestrator folder lookup comes back as an empty success instead, so read an empty result with that in mind |
| `Failure` | `permission_denied` | 1 | 403. The caller has no Insights access, or asked for a folder outside their set |
| `Failure` | `rate_limited` | 1 | 429. Report it and stop |
| `Failure` | `timeout` | 1 | The request was cancelled or timed out. Narrow the window or the filters |
| `Failure` | `server_error` | 1 | 503 means the warehouse behind Insights is degraded and the request was accepted. Any other 5xx lands here too, including the `queues sla` 500 |
| `Failure` | `network_error` | 1 | DNS, socket, proxy, or TLS failure |
| `Failure` | `unknown_error` | 1 | A malformed response, a broken `UIPATH_*` environment, or any failure the CLI could not classify. Read `Message` before concluding the service is at fault |

Every failure also carries `Retry`; branch on it as described in SKILL.md Critical Rule 8.

## Commands

### queues summary

Total and successful queue item counts plus average processing time for the window. One object, no pagination.

```bash
uip insights queues summary --time-range 1440 --output json
```

`Data`: `SuccessfulQueueItems`, `TotalQueueItems`, `AverageProcessingTimeMs`. Each comes from its own backend query. `TotalQueueItems` and `AverageProcessingTimeMs` can be `null`, meaning the query returned no row for that value; report a null as unavailable, never as zero. `SuccessfulQueueItems` is never null, because its handler starts the count at zero, which means a `0` there cannot be told apart from a query that returned no row.

### queues sla

SLA bucket counts, first breach times, and robot demand, one row per queue name.

```bash
uip insights queues sla --time-range 1440 --output json
```

`Data[]`: `QueueName`, `ProcessName`, `InSlaCount`, `AtRiskCount`, `OutOfSlaCount`, `FirstSlaBreachAt`, `FirstRiskBreachAt`, `AverageHandlingTimeMs`, `AveragePendingTimeMs`, `RunningRobots`, `NecessaryRobots`.

`ProcessName` is one process picked out of the queue's work, not a second key. Do not report a row as that queue's SLA for that process, and do not sum counts across rows expecting each to cover one process. A null `ProcessName` means the query found no process for that queue.

`NecessaryRobots` is `-1` when the backend cannot compute a demand, and its computed branch floors to `0` because the backend mixes seconds and milliseconds in that expression. Treat neither value as a robot count and never report it as a staffing number.

`AverageHandlingTimeMs` and `AveragePendingTimeMs` are milliseconds.

This row mixes two time windows. The SLA bucket counts, the two breach times, and `NecessaryRobots` use the range you asked for. `AverageHandlingTimeMs`, `AveragePendingTimeMs`, and `RunningRobots` come from queries with a fixed 30-day window that ignores `--time-range`. Never present those three as figures for a shorter window.

A null `FirstSlaBreachAt` or `FirstRiskBreachAt` means nothing is predicted to breach. That is a result worth reporting, not missing data.

A queue appears here only while its most recent executor job is still resolvable, so a queue whose last job has aged out drops off the list rather than reporting as not at risk.

A 500 from this command can mean one queue has new items but no completed-with-timings history. That is a backend defect rather than the outage the Errors table describes, and retrying will not clear it.

### queues completed-timeline and queues uncompleted-timeline

Queue item counts per time bucket. `completed-timeline` covers terminal states, `uncompleted-timeline` covers active ones.

```bash
uip insights queues completed-timeline --time-range 1440 --output json
```

```bash
uip insights queues uncompleted-timeline --time-range 1440 --output json
```

`completed-timeline` `Data[]`: `StartTime`, `EndTime`, `Failed`, `Successful`, `Abandoned`, `Deleted`.
`uncompleted-timeline` `Data[]`: `StartTime`, `EndTime`, `New`, `InProgress`, `Retried`.

`Failed` counts the Failed and Retried states together, and it counts events rather than items: an item retried twice and then successful adds two to `Failed`, possibly in earlier buckets, and one to `Successful`. `Successful`, `Abandoned`, and `Deleted` each count one per item. So `Failed` plus `Successful` can exceed the number of items in the bucket, and `Failed` is never an item count. `Retried` on the uncompleted timeline is a latest-state count, so an item that was retried and then finished is not on it at all.

Bucket width is chosen by the server from the window length and is not returned as a field, so `StartTime` and `EndTime` are the authority.

Every bucket in the window comes back, including ones where every count is zero, oldest bucket first. The default `--limit 50` therefore keeps the oldest end, and a wide window answers with data that stops well before the present. Read `Pagination.Total` for the bucket count, then re-run with `--limit` at or above it. Rule 5 is why: prefer that one call to walking `--offset`.

The first and last bucket each cover only the part of their interval inside the window, so their counts are low by construction. Compare the interior buckets.

Because every bucket comes back even when its counts are zero, an empty `Data[]` here is not a quiet window. It means the warehouse returned nothing at all, which is the one extra cause Rule 11 asks for on these two commands.

Both take two extra flags, and no other queue command accepts either.

`--time-event` picks which queue item timestamp the buckets are built from and defaults to `latest`. The choices differ per command: `completed-timeline` takes `latest`, `creation`, `start`, or `end`, and `uncompleted-timeline` takes `latest`, `creation`, or `start`. Passing `--time-event end` to `uncompleted-timeline` is rejected before any request, because `end` maps to the end-of-processing column that a New or InProgress item has not reached.

`--timezone-offset <minutes>` relabels the reported `StartTime` and `EndTime` and leaves the bucket edges UTC-aligned, so it never regroups the rows. The server subtracts the value, in the JavaScript `getTimezoneOffset` convention, so pass `-120` to label buckets in UTC+2.

### queues top-failures

Queues ranked by failed items.

```bash
uip insights queues top-failures --time-range 43200 --output json
```

`Data[]`: `QueueName`, `ApplicationExceptions`, `BusinessExceptions`, `ClassifiedFailures`.

The server returns at most ten queues, already ranked by its own failure total, and the rows stay in that order. A queue missing from this list is not proof it had no failures.

`ClassifiedFailures` is the sum of the two exception counts. It is not the queue's failure total, and it is not what the server ranked on. A failure carrying no exception type counts toward the ranking and not toward this sum, so a queue can rank high here with `ClassifiedFailures` well below its real failure count. Report the two typed counts, and do not present `ClassifiedFailures` as the number of failures.

Items in the `Failed` and `Retried` states both count as failures here, and the same holds for `failures-by-reason` and `failure-details`. A count from this family therefore runs higher than the `FailedBusiness` plus `FailedApplication` pair on `queues details`.

### queues failures-by-reason

Failure counts grouped by exception reason and type.

```bash
uip insights queues failures-by-reason --time-range 43200 --output json
```

```bash
uip insights queues failures-by-reason --time-range 43200 --group-by queue --output json
```

`Data[]`: `ExceptionReason`, `ExceptionType`, `Count`, plus `QueueName` when `--group-by queue` was passed and `RobotName` when `--group-by robot` was. A column that was not requested is absent from the row instead of present and null. `--group-by` accepts `queue` and `robot` and nothing else, and takes both space separated.

`--group-by` is appended to the backend's own grouping, so grouped counts subdivide the ungrouped ones instead of repeating them. Do not report a difference between a grouped and an ungrouped run as nondeterminism. A null grouping value makes one column shorter than the others, which the CLI rejects with a message naming the sparse dimension; re-run without that `--group-by` to get the same failure counts ungrouped.

`ExceptionReason` can be null. That row is a real failure group, and `failure-details` reaches it with `--null-error-message`.

### queues failure-details

The individual queue items that failed with one exact exception reason.

```bash
uip insights queues failure-details --time-range 43200 --error-message "Business rule failed" --output json
```

`Data[]`: `QueueName`, `QueueId`, `QueueItemId`, `QueueItemKey`, `FolderId`, `CreatedAt`, `StartedAt`, `EndedAt`, `DurationMs`.

Exactly one of `--error-message` or `--null-error-message` is required, and passing both is rejected with exit 3. `--error-message` is an exact match and is trimmed before it is sent, so take it verbatim from a `failures-by-reason` row rather than retyping it. Use `--null-error-message` for the row that command returns with a null `ExceptionReason`.

`--robot-name` takes one name, not a list, and it selects items that robot failed at least once rather than filtering the rows. The returned rows include those items' failures by every other robot and carry no robot column, so never attribute a returned failure to the robot you filtered on.

The server returns at most 1000 items, newest processing end first.

### queues details

Per-queue and per-folder item counts across eight states, with duration aggregates.

```bash
uip insights queues details --time-range 1440 --output json
```

`Data[]`: `QueueName`, `FolderName`, `Successful`, `FailedBusiness`, `FailedApplication`, `Deleted`, `Abandoned`, `New`, `InProgress`, `Retried`, `AverageDurationMs`, `MedianDurationMs`, `PercentileDurationMs`.

`Retried` counts every retry event. The other seven read an item at most once, at its latest state in the window, and an item whose latest state is `Retried`, or a failure carrying no exception type, lands in none of them. So the eight do not sum to the items with activity in the window.

Durations are milliseconds and `PercentileDurationMs` is the 90th percentile. The backend coalesces a missing duration aggregate to `0`, so a `0` can mean no item in the window carried both a start and an end timestamp rather than that processing was instant.

### queues retry-outcomes

Retried items and how many later succeeded, per queue.

```bash
uip insights queues retry-outcomes --time-range 43200 --output json
```

`Data[]`: `QueueName`, `RetriedItems`, `SuccessfulItems`, `SuccessRatePercent`.

`SuccessRatePercent` describes retried items only. It is not the queue's overall success rate; use `queues summary` for that. The backend computes it on a 0 to 100 scale rounded to two decimals and the CLI passes it through unchanged.

`RetriedItems` sums every retry event while `SuccessfulItems` counts each item at most once, so the two are not the same unit and dividing one by the other does not reproduce `SuccessRatePercent`. Whether one item can raise more than one retry event is not confirmed against a live tenant.

A queue with no retry in the window is absent from the list rather than present with zeros.

### queues operational-metrics

The Dedicated SaaS queue operations table.

```bash
uip insights queues operational-metrics --time-range 1440 --widget-type non-rda --output json
```

`RunDate` is a calendar day cut in US Eastern time, which lines up with neither UTC days nor the caller's local days, and the command takes no timezone flag to change that. Never present a `RunDate` total as a UTC or local day, and expect it to disagree with a timeline query, which buckets in UTC.

`Data[]`: `TenantName`, `RunDate`, `L1FolderName`, `L2FolderName`, `L3FolderName`, `AirId`, `QueueName`, `OpeningBalance`, `Loaded`, `Completed`, `SystemException`, `BusinessException`, `Abandoned`, `Pending`, `Reconcile`, `SuccessPercentage`.

`OpeningBalance`, `Abandoned`, and `Pending` are `0` when the selected query did not compute them. The `rda` query never computes any of the three, and the `non-rda` query computes `Abandoned` and `Pending` only for unattended tenants. Read a `0` in those three as "not computed" unless the deployment is known to produce them.

The backend declares no scale for `SuccessPercentage`. Name the scale you assumed and say it is unverified. Do not assume it matches `retry-outcomes`.

`--widget-type <rda|non-rda>` is required. This table is served only on Dedicated SaaS. On Cloud the backend returns an empty list rather than an error, so an empty result cannot tell "no rows" from "not a Dedicated SaaS tenant"; on Automation Suite and Service Fabric Rule 12 applies instead. Say which cause you can rule out and which you cannot.

`rda` selects a different table. Its rows come from Attended-tenant robot logs tagged as RDA transactions rather than from queue items, and `QueueName` holds a process name.

`--queue-name` is refused with `--widget-type rda` (exit 3, `ValidationError`), because the RDA query filters by folder only and would otherwise return the whole table labelled as filtered. Narrow with `--folder-key`, or use `non-rda`.

An empty `rda` result has a third cause on top of the two the `--widget-type` paragraph names: no attended robot logged an RDA transaction in the window, which can be true while queue items exist.

## Investigation Workflow: Explain Why a Queue Is Failing

1. Resolve the exact queue name with `uip insights filter-queues list` when the user named a queue. Rule 7 is why: a paraphrased name returns zero rows.
2. Run `uip insights queues summary` for the window's item totals. `TotalQueueItems` can be null, in which case there is no total to report against.
3. Run `uip insights queues top-failures` to see which queues carry the failures. Then run `uip insights queues failures-by-reason --queue-name "<exact name>"` for the reasons inside one queue, taking the name from step 1 rather than from a `top-failures` row, because a row's `QueueName` can cover two merged queues (Rule 8).
4. Run `uip insights queues failure-details` with `--error-message` copied verbatim from the `failures-by-reason` row, or `--null-error-message` for the null-reason row. Retyping the reason is the step that most often returns nothing.
5. Report each count with its own unit. Do not divide a failure count by `TotalQueueItems`: this family counts events and the summary counts items, so the ratio can exceed 1. Quote the `Instructions`, which carry the window clamp, the row-key merges, and the empty-result causes for the commands you ran.

Run each command as its own shell invocation. SKILL.md Critical Rule 2 forbids chaining or batching them.
