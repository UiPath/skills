# Triggers & Webhooks

Automate jobs with time, queue, and API triggers, and notify external systems through webhooks.

> For full option details, run `uip or triggers create --help` (or `--help` for any command).

## When to Use

- Schedule recurring jobs with cron.
- Start jobs when queue items exceed a threshold.
- Expose HTTP endpoints that start jobs.
- Notify external systems of Orchestrator events.

## Prerequisites

- Run `uip login status`; if unauthenticated, ask the user to run `uip login` (it opens an interactive browser flow).
- Ensure the target folder exists and has machines assigned (see [setup-environment.md](setup-environment.md)).
- Create the process/release and obtain its release key with `uip or processes list`.

## Trigger Types

Select `--type`; it defaults to `time`.

| Type | Purpose | Required options |
|---|---|---|
| `time` | Cron scheduling | `--cron`, `--time-zone` |
| `queue` | Fire above a queue threshold | `--queue-key` |
| `api` | HTTP job endpoint | `--slug`, `--method` |

Quartz cron has 6 fields (`sec min hour day month weekday`), not Unix 5 fields; use `?` in either day-of-month or day-of-week:

| Schedule | Quartz cron | Unix mistake |
|---|---|---|
| Daily at noon | `0 0 12 * * ?` | `0 12 * * *` |
| Weekdays 9 AM | `0 0 9 ? * MON-FRI` | `0 9 * * 1-5` |
| Every 30 min | `0 0/30 * * * ?` | `*/30 * * * *` |

`RuntimeType` values: `Serverless`, `Unattended`, `Headless`, `NonProduction`, `AgentService`.

## Step 1: Get the Release Key

Run:

```bash
uip or processes list --folder-path "Finance" --output json
# Copy the Key field -- this is the --release-key for triggers
```

## Step 2: Create a Trigger

Triggers bind to a release. `triggers create` therefore does not accept `--folder-path` or `--folder-key`; the release determines the folder for all types.

### Time Trigger

Run:

```bash
uip or triggers create --type time \
  --name "WeekdayInvoiceRun" --release-key <process-key> \
  --cron "0 0 9 ? * MON-FRI" --time-zone "Europe/Bucharest" \
  --runtime-type Unattended --job-priority Normal --output json
```

`--time-zone` takes an IANA ID such as `UTC`, `Europe/Bucharest`, or `America/Los_Angeles`. Use `--disabled` to stage a disabled trigger; later run `triggers update <key> --enabled`. Use `--stop-strategy <SoftStop|Kill>` to control stopping at the next firing. `--kill-process-expression <cron>` schedules enforcement for `Kill` when clean stop fails; without it, `Kill` waits indefinitely. Use `--input-arguments <json>` for a JSON-encoded input-arguments map.

Repeatable `--target <spec>` pins execution with `'machine=<machine-guid>,user=<user-guid>,session=<session-id>'`. In default `dynamic` mapping any combination is valid, but `session` requires `machine`. Use `--mapping-mode <dynamic|strict>` for validation: `dynamic` permits any mix; `strict` requires `machine` and `user` on every target and suits environments where “Enable account-machine mappings” is enabled. `--run-as-me` uses the creator's identity. `--resume-on-same-context` resumes suspended jobs on the original machine. Use `--calendar-key <guid>` to select excluded days from `uip or calendars list`.

### Queue Trigger

Run:

```bash
uip or queues list --folder-path "Finance" --output json  # get queue key

uip or triggers create --type queue \
  --name "InvoiceQueueTrigger" --release-key <process-key> \
  --queue-key <queue-key> --items-threshold 1 --max-jobs 3 \
  --runtime-type Unattended --job-priority Normal --output json
```

Use `--items-per-job` (default `1`) and `--activate-on-complete` to re-trigger on job completion.

### API Trigger

Run:

```bash
uip or triggers create --type api \
  --name "InvoiceEndpoint" --release-key <process-key> \
  --slug "process-invoice" --method Post \
  --calling-mode AsyncRequestReply --runtime-type Unattended \
  --job-priority Normal --output json
```

`CallingMode` values: `AsyncRequestReply`, `AsyncCallback`, `LongPolling`, `FireAndForget`.

## Step 3: List, Inspect, Update

Run:

```bash
uip or triggers list --type time --folder-path "Finance" --output json
uip or triggers list --type queue --folder-path "Finance" --enabled --name "Invoice" --output json
uip or triggers get <trigger-key> --type time --folder-path "Finance" --output json
uip or triggers update <trigger-key> --type time \
  --cron "0 30 8 ? * MON-FRI" --folder-path "Finance" --output json
```

Always pass the correct `--type` to `get`, `update`, and `delete`; it defaults to `time`. An API or queue key without `--type api` or `--type queue` queries ProcessSchedules and returns `HTTP 404: ProcessSchedule does not exist.` The error hint identifies the correct type. `list --type time` and `list --type queue` return time and queue triggers; both use ProcessSchedules. Curated output has canonical `Type`: `Time`, `Queue`, or `Api`; raw `--all-fields` output reports API triggers as `Http`. `get` also returns `StartProcessCronSummary`.

Enum flag values are case-insensitive and normalized to PascalCase: `--method POST`, `--runtime-type SERVERLESS`, and `--job-priority HIGH` are valid. This also applies to `queue-items` (`--priority high` = `High`) and `processes update` (`--retention-action delete`, `--robot-size standard`).

## Step 4: Toggle, Delete

`triggers update` performs get plus patch. Dedicated enable/disable commands are folded into mutually exclusive `--enabled` and `--disabled` flags for all trigger types.

Run:

```bash
uip or triggers update <trigger-key> --type time --folder-path "Finance" --disabled --output json
uip or triggers update <trigger-key> --type time --folder-path "Finance" --enabled --output json
uip or triggers delete <trigger-key> --type time --folder-path "Finance" --yes --output json
```

## Step 5: View Trigger History

Run this before changing configuration when a trigger does not fire:

```bash
uip or triggers history <trigger-key> --folder-path "Finance" --output json
```

Curated entries contain `TimeStamp`, `EventType` (`Fired`, `Failed`, `Skipped`, `DisabledDueToConsecutiveFailures`, ...), `Level`, `Message` (for example, “No machines available”, “License limit reached”, or “Calendar exclusion”), and `TriggerKey`. The response includes `Pagination`; use `--all-fields` for the raw DTO.

## Webhooks

Webhooks are tenant-scoped, require no `--folder-path`, and POST to a URL when Orchestrator events occur.

### Discover Event Types

Run:

```bash
uip or webhooks event-types --output json
```

Use returned names such as `job.completed`, `job.faulted`, and `queueItem.failed` with `--events`. The response includes `Pagination`; enumeration is complete in one call and `HasMore` is always false.

### Create a Webhook

The webhook name is positional. Run:

```bash
uip or webhooks create "JobFailureAlert" \
  --url "https://hooks.example.com/uipath" \
  --events "job.faulted,job.stopped" \
  --secret "my-signing-secret" --output json

uip or webhooks create "AuditHook" \
  --url "https://hooks.example.com/audit" --output json
```

Omit `--events` for all events; provide it for specific events. `--secret` signs each delivery in `X-UiPath-Signature` as `sha256=<HMAC_SHA256(secret, raw_body)>`; receivers should recompute the HMAC over the unmodified body and compare in constant time. Without a secret, accept unsigned payloads only on private, trusted network paths. `--allow-insecure-ssl` skips TLS verification and is only for HTTPS endpoints with self-signed certificates in non-production. Reverse it with `webhooks update --no-allow-insecure-ssl`; verify the flag with `--help` for the installed CLI version.

### List, Get, Update, Test, Delete

Run:

```bash
uip or webhooks list --enabled --output json
uip or webhooks get <webhook-key> --output json

uip or webhooks update <webhook-key> \
  --url "https://new.example.com/hook" \
  --events "job.faulted,queueItem.failed" --output json

uip or webhooks update <webhook-key> --disabled --output json
uip or webhooks update <webhook-key> --enabled --output json

uip or webhooks ping <webhook-key> --output json
uip or webhooks delete <webhook-key> --yes --output json
```

`ping` reports dispatch, not delivery: success means the event was queued in the asynchronous pipeline, not that the endpoint responded. Confirm receipt at the endpoint or in its logs. Supplying `--events` on update changes an all-events webhook to specific events.

## Complete Example

Run:

```bash
uip or processes list --folder-path "Finance" --output json
uip or calendars list --output json
uip or triggers create --type time \
  --name "WeekdayInvoiceRun" --release-key "c3d4e5f6-..." \
  --cron "0 0 9 ? * MON-FRI" --time-zone "UTC" \
  --calendar-key "<calendar-key>" --runtime-type Unattended \
  --job-priority Normal --output json
uip or queues list --folder-path "Finance" --output json
uip or triggers create --type queue \
  --name "InvoiceOverflowTrigger" --release-key "c3d4e5f6-..." \
  --queue-key "d4e5f6a7-..." --items-threshold 10 --max-jobs 5 \
  --activate-on-complete --runtime-type Unattended \
  --job-priority High --output json
uip or webhooks create "InvoiceFailureAlert" \
  --url "https://hooks.slack.com/services/T00/B00/xxx" \
  --events "job.faulted,job.stopped" --secret "webhook-signing-key" \
  --output json
uip or triggers list --type time --folder-path "Finance" --enabled --output json
uip or webhooks list --enabled --output json
```

## Variations and Gotchas

- Quartz cron has 6 fields, not 5; use `?` in day-of-month or day-of-week.
- `--type` defaults to `time`; omitting it for queue or API triggers causes misleading errors.
- `--release-key` is the process key from `uip or processes list`, not the package ID from `uip or packages list`.
- Calendar keys come from `uip or calendars list`; align calendar and trigger timezones.
- Use `triggers history` to diagnose no machines, license exhaustion, calendar exclusion, or auto-disable before changing configuration.
- Triggers are folder-scoped and require `--folder-path` or `--folder-key`; webhooks are tenant-scoped and do not.
- `Triggers.DisableWhenFailedCount`, configurable with `uip or settings`, controls consecutive-failure auto-disable. Check it with `uip or settings get "Triggers.DisableWhenFailedCount"`.

## Related

- [resources.md](resources.md) — Orchestrator resources overview and common flags
- Get the release key for `--release-key` → [`uipath-orchestrator`](run-jobs.md)
- Calendar management + tenant settings affecting trigger behavior → [`uipath-orchestrator`](tenant-admin.md)
- [process-queues.md](process-queues.md) — Queue setup required before creating queue triggers