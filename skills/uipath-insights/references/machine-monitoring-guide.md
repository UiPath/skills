# Machine Monitoring Commands

The `machines` commands report on machine health: attended versus unattended runtime, per-machine status and slot inventory, availability intervals, faulted-job ranking, and runtime minutes. They answer "how are these machines doing", not "which machines exist"; use `filter-machines list` for discovery and for the exact machine names these commands filter on.

Every command needs a time range. Results are tenant-scoped, unlike the `queues` commands.

Keys inside `Data` are PascalCase in the CLI's JSON output. Read `MachineName`, not `machineName`.

On a window ending now, `details` answers what a machine is doing and `availability-timeline` answers how its state moved.

## Shared Options

```text
--time-range <minutes>          Relative window ending now
--started-after <epoch-ms>      Absolute window start, needs --started-before
--started-before <epoch-ms>     Absolute window end, needs --started-after
--machine-name <names...>       Machine names to restrict to, space separated
--host-machine-name <names...>  Host machine names to restrict to, space separated
--machine-type <types...>       Machine type labels to restrict to, space separated
--limit <number>                Rows to return, 1 to 10000 (default 50)
--offset <number>               Rows to skip before returning results (default 0)
--output <format>               Output format: table, json, yaml, plain, markdown (always use json)
```

`machines runtime-mix` returns a fixed two-row answer, so it takes no `--limit` or `--offset`. There is no `--folder-key` on any machine command.

The three name filters match whole values, exactly and case sensitively. Surrounding whitespace is trimmed before the value is sent, so it is not a spelling failure, but an empty or whitespace-only value is rejected locally and exits 3. Quote any value containing a space. A value that matches nothing returns `Success` with zero rows rather than an error, so an empty result never confirms that a filter value was spelled correctly.

Two different filters narrow to the rows satisfying both, and several values inside one filter widen to any of them. Two commands take less from a filter than that implies: on `details`, `--host-machine-name` narrows only the job-derived columns, and on `availability-timeline`, `--machine-type` narrows only the session intervals. Each command section says so.

`--machine-type` takes one or more of five labels the backend builds in SQL: `Standard Machine`, `Elastic Robot Pool`, `Cloud Robot - VM`, `Cloud Robot - Serverless`, `Machine Template`. All five contain spaces, so quote every label. A machine the backend could not classify, the kind that comes back with an empty `MachineType`, matches no label at all and drops out whenever the flag is passed.

Neither a type label nor a host name has a discovery command. `filter-machines list` projects machine names and keys only. Read host names from the `HostMachineName` column of `machines details` and type labels from its `MachineType` column, and confirm a guessed value by re-running without that filter rather than by trusting an empty result.

## Rules

1. **A time range is required and its units are minutes or epoch milliseconds.** Pass `--time-range <minutes>` (60 = 1h, 1440 = 24h, 10080 = 7d, 43200 = 30d), or both `--started-after` and `--started-before` in epoch milliseconds. `--time-range` together with either absolute bound is rejected, and so is one absolute bound without the other. Omitting a time range is rejected locally and exits 3. `uip insights alert-history` takes its bounds in epoch **seconds**, so do not carry a value between the two families: a seconds value here is rejected locally, with a message telling you to multiply by 1000.
2. **The server caps the window at 30 days, and the CLI tells you when it did.** A `--time-range` above 43200 is clamped to exactly 30 days. An absolute bound is queried as given until it is a full 31 days old, when the server moves it to the 30-day boundary; its test truncates to whole days, so a bound aged 30 days and 23 hours passes through untouched. Each bound clamps on its own and the server then adds a millisecond to the end, so a window whose end is also past the cap collapses to about a millisecond and comes back as an empty success. Read that as an artifact of the clamp rather than an absence of data, and keep the end of a historical window inside 30 days. The server announces neither clamp, but the CLI detects both and reports them in `Instructions`, so read those on any window near the cap and report the window they describe. Never report a longer window as the window queried.
3. **Results are tenant-scoped, not folder-scoped.** No machine query binds a folder clause, so there is no `--folder-key` and no permission-bounded subset. Do not carry the queue commands' folder reasoning over.
4. **Repeat calls inside a minute return the same numbers, and there is no bypass.** The server caches each distinct request for 60 seconds, keyed on a timestamp floored to the wall-clock minute. Change the time range or a filter to make it a different request. Say so before presenting a figure as current during a live incident.
5. **Every page repeats the whole backend request.** These commands page the CLI's own copy of the list. `--limit` defaults to 50, so a 50-row result is a full page rather than a complete list; read `Pagination.Total` and `Pagination.HasMore`.
6. **A machine name and host pair is not a unique identity.** Two live machine keys can carry the same name, producing two rows that agree on `MachineName` and `HostMachineName`. Only `availability-timeline` returns `MachineKey`, so that is the one command that can tell two same-named machines apart.
7. **An empty string is an answer, not an error.** An empty `CurrentProcess` means the backend found no job event at all, and an empty `MachineType` means it could not classify the machine. Report what the empty value means for that field rather than a blank.
8. **`top-failures` and `utilization` return at most ten machine-and-host groups**, ranked server-side. `--limit` can only shrink that page, never raise it, and an `--offset` at or past the row count the server returned comes back empty; read `Pagination.Total` for that count. A machine missing from either list is not proof of zero: it may rank eleventh, and for `utilization` it may instead have no reconstructed runtime at all, which is not the same as a zero-minute row.
9. **A page split is stable, but the data under it can move.** The CLI sorts only `details`, by machine then host, and breaks any remaining tie on the whole row, so one backend response always splits into the same pages. `availability-timeline`, `top-failures`, and `utilization` keep the server's own order. A machine that appeared or dropped out between two `--offset` calls still shifts the split, so raise `--limit` and read the table in a single call when that matters.
10. **Serverless machines report `N/A` as their host.** `details`, `availability-timeline`, `top-failures`, and `utilization` all print it in `HostMachineName`; it is the backend's placeholder rather than a hostname. Only `availability-timeline` compares the mapped value, so passing `N/A` to `--host-machine-name` on `top-failures` or `utilization` matches nothing and returns an empty success. Select serverless machines with `--machine-type "Cloud Robot - Serverless"` instead.
11. **These commands need a Cloud or Dedicated SaaS deployment.** On Automation Suite and Service Fabric they return `Result: ConfigError` with `ErrorCode: configuration_error` before the tenant is consulted. That is a deployment fact, not a permission or data answer, and retrying will not change it.

## Errors

`machines` failures use the same `Result` values as the other families, plus the deployment gate. Branch on `Result`, not on `ErrorCode` alone.

| `Result` | `ErrorCode` | Exit | Cause |
|---|---|---|---|
| `ValidationError` | `invalid_argument` | 3 | A missing or conflicting time range, an empty `--machine-name`, `--host-machine-name`, or `--machine-type` value, or a flag the command does not accept |
| `AuthenticationError` | `authentication_required` | 2 | 401, or no usable session before any request is sent |
| `ConfigError` | `configuration_error` | nonzero | 404 with no body. The machine routes are not served on this deployment |
| `Failure` | `permission_denied` | 1 | 403. The caller has no Insights access in the active tenant, or the tenant sits outside the organization the token covers. Never a folder answer, because machine routes have no folder scoping |
| `Failure` | `rate_limited` | 1 | 429. Report it and stop |
| `Failure` | `timeout` | 1 | The request was cancelled or timed out. Narrow the window or the filters |
| `Failure` | `server_error` | 1 | The warehouse behind Insights is degraded. The request itself was accepted |
| `Failure` | `network_error` | 1 | DNS, socket, proxy, or TLS failure |
| `Failure` | `unknown_error` | 1 | A malformed or misaligned response from the service |

No machine route produces a `not_found` of its own, because none of them runs an Orchestrator folder lookup. A 404 that arrives with a body therefore came from something in front of the service, and it reports `not_found`.

Every failure also carries `Retry`; branch on it as described in SKILL.md Critical Rule 8.

## Commands

### machines runtime-mix

Unattended versus attended job runtime and average per-robot runtime. Two fixed rows, no pagination.

```bash
uip insights machines runtime-mix --time-range 1440 --output json
```

`Data[]`: exactly two rows, `Unattended` then `Attended`, each with `ExecutionType`, `JobDurationMs`, `AverageUtilizationMs`.

Both values are milliseconds. `AverageUtilizationMs` divides the runtime by the window's distinct robot count, counted across attended and unattended robots together, so the `Unattended` row is not a per-unattended-robot average. It is a duration, never a percentage; do not compare either value against a percentage threshold, and do not divide either value by the window length to report how many robots were busy on average. Both cross the wire as single-precision floats, so treat the last few milliseconds of a large total as noise.

Both aggregates are coalesced to zero server-side, and the command returns its two rows whatever the filters matched. A `0`/`0` pair therefore means no job runtime matched, which a mistyped filter value produces just as an idle window does. Check machine names with `filter-machines list`, and check host names and type labels by re-running without that filter, before reporting zeros as a finding.

### machines details

Per-machine and per-host status, current process, fault count, runtime, and slot inventory.

```bash
uip insights machines details --time-range 1440 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `Status`, `CurrentProcess`, `FaultedJobs`, `UtilizationMs`, `MachineType`, `RuntimeCount`, `InUseCount`, `NonProductionSlots`, `HeadlessSlots`, `AutomationCloudSlots`, `UnattendedSlots`, `TestAutomationSlots`, `AutomationCloudTestAutomationSlots`, `DevelopmentSlots`.

This row mixes three spans, and the split is not the obvious one:

- `FaultedJobs` and `UtilizationMs` count only events inside the requested window.
- `CurrentProcess`, `InUseCount`, and a `Status` of `In Use` describe the window's job events, including a job that was still running when the window opened, which the server looks up to 30 days back to find. On a historical window they describe that window's end, not now.
- The other `Status` values read the machine session table on a fixed 30-day scan ending now, so they can report a state the window never saw.

`Status` is the field that says whether a job is running: `In Use` means one is. `CurrentProcess` names the process on the most recent job event whatever state that job ended in, so a faulted job fills it just as a running job does. Never read it as a claim that something is running now.

`Available` is also the query's fallback when no session row exists at all, which makes it the weakest value in the column. Do not report it as observed health without a second signal.

`--host-machine-name` narrows only the job-derived columns here. The 30-day session scan that lists machines per host carries no host predicate, so rows for another host of the same machine can still appear. `--machine-name` and `--machine-type` apply throughout.

`RuntimeCount` is the backend's own sum of the seven slot counts beside it, so the total and its parts are the same quantity. `UtilizationMs` crosses the wire as a single-precision float, like the `runtime-mix` durations, so treat the last few milliseconds of a large total as noise.

Every other command either ranks a top ten or returns intervals, so this is where a question that needs one row per machine, including machines with no runtime, gets answered.

### machines availability-timeline

Availability intervals per machine and host, reconstructed server-side from machine-session and job events.

```bash
uip insights machines availability-timeline --time-range 1440 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `MachineKey`, `Status`, `StartTime`, `EndTime`, `RunningJobs`, plus `EventTime` on deployments whose backend sends it.

Reading rules:

- `Status` carries the interval markers `Job Start` and `Job End` alongside session states such as `Available`, `Unresponsive`, and `Disconnected`. Only the two job markers are built by the query; the session states pass through from the machine session table, so treat the list as open.
- `RunningJobs` is the concurrent in-progress count for the interval and can be negative when a job started before the backend's 30-day lookback. Treat a negative value as unknown concurrency, not an error.
- A machine that stayed `Unresponsive` or `Disconnected` for the entire window returns no rows at all, so an empty result never proves availability.
- `StartTime` on an interval carried in from before the window is clamped to the window start. Where `EventTime` is present it is the real transition instant; prefer it when reporting when a state began.
- `--machine-name` filters on the name rather than the key, so a shared name returns rows for both machines. Pair the two with `filter-machines list`, which returns `MachineName` and `MachineKey` together, then split the rows on `MachineKey`.
- `--machine-type` reaches only the session intervals. The job markers are joined to the machine table without it, so a type-filtered timeline still carries `Job Start` and `Job End` rows for machines of every type.

Rows keep the backend's machine-key, host, and start-time order, so two machines sharing a name interleave by key rather than by name. Timestamps end in ` GMT` and follow the service host's own formatting. Quote them verbatim; never parse, convert, or re-sort them.

### machines top-failures

Machines ranked by faulted jobs.

```bash
uip insights machines top-failures --time-range 43200 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `FaultedJobs`. At most ten rows in the server's own ranking, and equal counts have no stable order, so which of several tied machines makes the cut can change between calls.

Drill into a ranked machine's failures with the shipped Jobs commands, substituting the row's `MachineName` and giving `jobs` its own time range:

```bash
uip insights jobs failures-by-reason --machine-name FinanceVM --time-range 43200 --output json
uip insights jobs failure-details --machine-name FinanceVM --time-range 43200 --output json
```

They accept the `MachineName` value verbatim. The flag shape differs: `jobs` takes one repeatable `--machine-name` value, while `machines` commands take a space-separated list.

### machines utilization

Job runtime minutes per machine and host.

```bash
uip insights machines utilization --time-range 43200 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `UtilizationMinutes`. At most ten rows, minutes descending.

`UtilizationMinutes` is runtime inside the window, rounded to two decimals. It is not a utilization percentage: the response carries no capacity denominator, so do not build one of your own out of the window length or the slot counts. The same goes for any figure that divides runtime by the window under another name: an average concurrency, an "active robot count", or a "robot-equivalent" is that missing denominator again, and the result is a number the backend never computed. When the user asks how busy the fleet was, answer with the minutes per machine and their ranking, and say that a share of capacity is not available from these commands. A machine with no running-job interval in the window is omitted, not reported as zero.
