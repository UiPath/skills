# Machine Monitoring Commands

The `machines` commands report on machine health: attended versus unattended runtime, per-machine status and slot inventory, availability intervals, faulted-job ranking, and runtime minutes. They answer "how are these machines doing", not "which machines exist"; use `filter-machines list` for discovery and for the exact machine names and type labels these commands filter on.

Every command needs a time range. Results are tenant-scoped: machine commands have no folder flag and no permission scoping, unlike the `queues` commands.

Keys inside `Data` are PascalCase in the CLI's JSON output. Read `MachineName`, not `machineName`.

## Shared Options

```text
--time-range <minutes>        Relative window ending now
--started-after <epoch-ms>    Absolute window start, needs --started-before
--started-before <epoch-ms>   Absolute window end, needs --started-after
--machine-name <names...>     Machine names to restrict to, space separated
--host-name <names...>        Host machine names to restrict to, space separated
--machine-type <types...>     Machine type labels to restrict to, space separated
--limit <number>              Rows to return, 1 to 10000 (default 50)
--offset <number>             Rows to skip before returning results (default 0)
--output <format>             Output format: table, json, yaml, plain (always use json)
```

`machines runtime-mix` returns a fixed two-row answer, so it takes no `--limit` or `--offset`. There is no `--folder-key` on any machine command.

`--machine-type` takes the exact labels `filter-machines list` reports, such as `Standard Machine` or `Cloud Robot - Serverless`. Quote labels containing spaces.

## Rules

1. **A time range is required and its units are minutes or epoch milliseconds.** Same two forms and units as `queues`: `--time-range <minutes>` (60 = 1h, 1440 = 24h, 43200 = 30d), or both `--started-after` and `--started-before` in epoch milliseconds. Passing both forms is rejected. Omitting a time range is rejected locally and exits 3.
2. **The server silently caps the window at 30 days**, the same clamping as `queues`. Never report a longer window as the window queried.
3. **Results are tenant-scoped, not folder-scoped.** The backend ignores folders entirely on these routes, so there is no `--folder-key` and no permission-bounded subset. Do not carry the queue commands' folder reasoning over.
4. **Repeat calls inside a minute return the same numbers, with no way around it.** The server caches each distinct request for 60 seconds and the machine routes expose no bypass at all. Say so before presenting a figure as current during a live incident.
5. **Every page repeats the whole backend request.** These commands page the CLI's own copy of the list; read `Pagination.Total` and `Pagination.HasMore`.
6. **A machine name and host pair is not a unique identity.** Two live machine keys can carry the same name, producing two rows that agree on `MachineName` and `HostMachineName`. Only `availability-timeline` returns `MachineKey`.
7. **An empty string is an answer, not an error.** `CurrentProcess` is empty when no job is running and `MachineType` is empty when the type cannot be classified. Report the meaning, not a blank.
8. **`top-errors` and `utilization` return at most ten rows**, ranked server-side. A machine missing from either list is not proof of zero; for `utilization` an omitted machine has no reconstructed runtime, which is not the same as a zero-minute row.
9. **Row order is the server's on `availability-timeline`, `top-errors`, and `utilization`.** The CLI sorts only `details` (by machine, then host) before paging. Timeline timestamps are culture-formatted `GMT` strings; never parse or re-sort them.
10. **These commands need a Cloud or Dedicated SaaS deployment.** On Automation Suite and Service Fabric they return `Result: ConfigError` with `ErrorCode: configuration_error` before the tenant is consulted. That is a deployment fact, not a permission or data answer, and retrying will not change it.

## Errors

`machines` failures use the same `Result` values and the same table as the `queues` guide: `ValidationError` exit 3 for local rejections, `AuthenticationError` exit 2, `ConfigError` for the deployment gate 404, and `Failure` with `permission_denied`, `rate_limited`, `timeout`, `server_error`, `network_error`, or `unknown_error`. One difference: a 403 here is a tenant-level Insights access boundary, never a folder answer, because machine routes have no folder scoping. Branch on `Retry` as described in SKILL.md Critical Rule 8.

## Commands

### machines runtime-mix

Unattended versus attended job runtime and average per-robot runtime. Two fixed rows, no pagination.

```bash
uip insights machines runtime-mix --time-range 1440 --output json
```

`Data[]`: exactly two rows, `Unattended` then `Attended`, each with `ExecutionType`, `JobDurationMs`, `AverageUtilizationMs`.

Both values are milliseconds. `AverageUtilizationMs` is the runtime divided by the distinct robot count, so it is also a duration, never a percentage. Do not compare either value against a percentage threshold.

### machines details

Per-machine and per-host status, current process, fault count, runtime, and slot inventory.

```bash
uip insights machines details --time-range 1440 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `Status`, `CurrentProcess`, `FaultedJobs`, `UtilizationMs`, `MachineType`, `RuntimeCount`, `InUseCount`, `NonProductionSlots`, `HeadlessSlots`, `AutomationCloudSlots`, `UnattendedSlots`, `TestAutomationSlots`, `AutomationCloudTestAutomationSlots`, `DevelopmentSlots`.

This row mixes two time windows. `FaultedJobs` and `UtilizationMs` count only events inside the requested window, but `Status`, `CurrentProcess`, and `InUseCount` come from a fixed 30-day scan ending now. Present the first two as window figures and the rest as recent state.

### machines availability-timeline

Availability intervals per machine and host, reconstructed server-side from machine-session and job events.

```bash
uip insights machines availability-timeline --time-range 1440 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `MachineKey`, `Status`, `StartTime`, `EndTime`, `RunningJobs`, plus `EventTime` on deployments whose backend sends it.

Four reading rules:

- `Status` includes the interval markers `Job Start` and `Job End` alongside session states such as `Available`, `Unresponsive`, and `Disconnected`.
- `RunningJobs` is the concurrent in-progress count for the interval and can be negative when a job started before the backend's 30-day lookback. Treat a negative value as unknown concurrency, not an error.
- A machine that stayed `Unresponsive` or `Disconnected` for the entire window returns no rows at all, so an empty result never proves availability.
- `StartTime` on an interval carried in from before the window is clamped to the window start. Where `EventTime` is present it is the real transition instant; prefer it when reporting when a state began.

Timestamps end in ` GMT` and follow the service host's own formatting. Quote them verbatim; never parse, convert, or re-sort them.

### machines top-errors

Machines ranked by faulted jobs.

```bash
uip insights machines top-errors --time-range 43200 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `FaultedJobs`. At most ten rows in the server's own ranking; equal counts have no stable order across pages. Serverless machines report `N/A` as the host.

Drill into a ranked machine's failures with the shipped Jobs commands: `uip insights jobs failures-by-reason --machine-name <name>` and `uip insights jobs failure-details --machine-name <name>` accept the `MachineName` value verbatim. Note the flag shape differs: `jobs` takes one repeatable `--machine-name` value, while `machines` commands take a space-separated list.

### machines utilization

Job runtime minutes per machine and host.

```bash
uip insights machines utilization --time-range 43200 --output json
```

`Data[]`: `MachineName`, `HostMachineName`, `UtilizationMinutes`. At most ten rows, minutes descending.

`UtilizationMinutes` is runtime inside the window, rounded to two decimals. It is not a utilization percentage: the response has no capacity denominator, so never divide it into one or compare it against a percentage threshold. A machine with no running-job interval in the window is omitted, not reported as zero.
