# Triggers & Webhooks

Automate job execution with time, queue, and API triggers, and set up webhooks for external event notifications.

> For full option details on any command, use `--help` (e.g., `uip or triggers create --help`).

## When to Use

- Scheduling recurring jobs on a cron schedule (nightly reports, weekday processing)
- Auto-processing queue items when they exceed a threshold
- Exposing HTTP endpoints so external systems can start jobs via API call
- Notifying external systems when Orchestrator events occur (job faulted, queue item failed, etc.)

## Prerequisites

- Authenticated (`uip login`)
- Target folder exists with machines assigned (see [setup-environment.md](setup-environment.md))
- Process (release) created -- you need the release key from `uip or processes list`

---

## Trigger Types

The CLI uses `--type` to select the trigger kind. Defaults to `time` if omitted.

| Type | Purpose | Required options |
|------|---------|-----------------|
| `time` | Cron-based scheduling | `--cron`, `--time-zone` |
| `queue` | Fire when queue items exceed threshold | `--queue-key` |
| `api` | HTTP endpoint that starts a job | `--slug`, `--method` |

**Cron format**: Quartz 6-field -- `sec min hour day month weekday` -- NOT Unix 5-field. Use `?` in day-of-month or day-of-week.

| Schedule | Quartz cron | Common mistake (Unix 5-field) |
|----------|------------|-------------------------------|
| Daily at noon | `0 0 12 * * ?` | `0 12 * * *` |
| Weekdays 9 AM | `0 0 9 ? * MON-FRI` | `0 9 * * 1-5` |
| Every 30 min | `0 0/30 * * * ?` | `*/30 * * * *` |

**RuntimeType values**: `Serverless`, `Unattended`, `Headless`, `NonProduction`, `AgentService`

---

## Step 1: Get the Release Key

```bash
uip or processes list --folder-path "Finance" --output json
# Copy the Key field -- this is the --release-key for triggers
```

---

## Step 2: Create a Trigger

### Time Trigger

```bash
uip or triggers create --type time \
  --name "WeekdayInvoiceRun" \
  --release-key <process-key> \
  --cron "0 0 9 ? * MON-FRI" \
  --time-zone "Europe/Bucharest" \
  --runtime-type Unattended \
  --job-priority Normal --output json
```

`triggers create` does not take `--folder-path` / `--folder-key` — the
folder is derived from the release the trigger is bound to. Same for all
three trigger types.

`--time-zone` takes an IANA time zone ID (e.g. `UTC`, `Europe/Bucharest`, `America/Los_Angeles`).

Additional options:
- `--disabled` — create the trigger in disabled state (default is enabled). Useful when you want to stage triggers ahead of activation, then flip them on later via `triggers update <key> --enabled`.
- `--stop-strategy <SoftStop|Kill>` — how to stop running jobs when the next firing happens. `SoftStop` requests the workflow to stop cleanly; `Kill` terminates the runtime process.
- `--kill-process-expression <cron>` — when `--stop-strategy=Kill`, this 6-field Quartz cron schedules **when** the kill is enforced if the workflow ignores the soft-stop request. Without it, Kill mode waits indefinitely.
- `--input-arguments <json>` — JSON-encoded input arguments map.
- `--target <spec>` (repeatable) — pin the trigger to one or more specific runtime targets. Format: `'machine=<machine-guid>,user=<user-guid>,session=<session-id>'`. Any combination is allowed in `dynamic` mapping mode (default), but `session` requires `machine`. Repeat the flag for multiple targets.
- `--mapping-mode <dynamic|strict>` — validation rule for `--target`. `dynamic` (default) lets you pass any mix of machine/user/session. `strict` requires both `machine` and `user` on every target — use this when the folder has "Enable account-machine mappings" turned on.
- `--run-as-me` — run jobs under the trigger creator's identity instead of resolving an unattended robot from the folder.
- `--resume-on-same-context` — resume suspended jobs on the same machine that originally ran them.
- `--calendar-key <guid>` — calendar to consult for excluded days (holidays). From `uip or calendars list`.

### Queue Trigger

```bash
uip or queues list --folder-path "Finance" --output json  # get queue key

uip or triggers create --type queue \
  --name "InvoiceQueueTrigger" \
  --release-key <process-key> \
  --queue-key <queue-key> \
  --items-threshold 1 --max-jobs 3 \
  --runtime-type Unattended --job-priority Normal --output json
```

Additional options: `--items-per-job` (default 1), `--activate-on-complete` (re-trigger on job completion).

### API Trigger

```bash
uip or triggers create --type api \
  --name "InvoiceEndpoint" \
  --release-key <process-key> \
  --slug "process-invoice" \
  --method Post \
  --calling-mode AsyncRequestReply \
  --runtime-type Unattended --job-priority Normal \
  --output json
```

CallingMode values: `AsyncRequestReply`, `AsyncCallback`, `LongPolling`, `FireAndForget`

---

## Step 3: List, Inspect, Update

```bash
# List time triggers in a folder
uip or triggers list --type time --folder-path "Finance" --output json

# Filter: only enabled, by name
uip or triggers list --type queue --folder-path "Finance" --enabled --name "Invoice" --output json

# Get details
uip or triggers get <trigger-key> --type time --folder-path "Finance" --output json

# Update (only provided fields change)
uip or triggers update <trigger-key> --type time \
  --cron "0 30 8 ? * MON-FRI" --folder-path "Finance" --output json
```

> **`--type` matters on get/update/delete.** Default is `time`. If you pass an api or queue trigger key without `--type api` / `--type queue`, the command hits ProcessSchedules and returns `HTTP 404: ProcessSchedule does not exist.` The error instructions surface a hint pointing at the right `--type` — re-run with the correct one. (`triggers list` shows the type per entry.)

> **`--type` filters the list.** `triggers list --type time` returns only time triggers, `--type queue` only queue triggers (both live in ProcessSchedules, so the CLI discriminates by queue binding). The curated output carries a canonical `Type` field with one of `Time`, `Queue`, or `Api` across `create`/`get`/`list` (use `--all-fields` for the raw entity, where api triggers report `Http`). `get` also returns `StartProcessCronSummary` (a human-readable cron, e.g. "At 12:00 PM").

> **Enum flag values are case-insensitive.** `--method POST`, `--runtime-type SERVERLESS`, `--job-priority HIGH` all work and are normalized to canonical PascalCase before the API call. Same on `queue-items` (`--priority high` ≡ `High`) and `processes update` (`--retention-action delete`, `--robot-size standard`).

---

## Step 4: Toggle, Delete

`triggers update` already does a get + patch internally, so the dedicated
`enable` / `disable` subcommands have been folded into it via mutually
exclusive `--enabled` / `--disabled` flags. Same applies to all three
trigger types (time, queue, api).

```bash
uip or triggers update <trigger-key> --type time --folder-path "Finance" --disabled --output json
uip or triggers update <trigger-key> --type time --folder-path "Finance" --enabled --output json
uip or triggers delete <trigger-key> --type time --folder-path "Finance" --yes --output json
```

---

## Step 5: View Trigger History

Shows every activation attempt and why it succeeded or failed. Check this before assuming broken config.

```bash
uip or triggers history <trigger-key> --folder-path "Finance" --output json
```

Entries are curated rows with `TimeStamp`, `EventType` (Fired, Failed, Skipped, DisabledDueToConsecutiveFailures, ...), `Level`, `Message` ("No machines available", "License limit reached", "Calendar exclusion") and `TriggerKey`. The response includes a `Pagination` block; pass `--all-fields` for the raw DTO.

---

## Webhooks

Webhooks are **tenant-scoped** -- no `--folder-path` needed. They POST to your URL when Orchestrator events occur.

### Discover Event Types

```bash
uip or webhooks event-types --output json
```

Returns names like `job.completed`, `job.faulted`, `queueItem.failed`. Use these with `--events`. The response carries the standard `Pagination` block (full enumeration in one call, `HasMore` always false).

### Create a Webhook

The webhook name is a **positional argument**, aligned with `calendars create <name>` and `queues create <name>`:

```bash
# Subscribe to specific events
uip or webhooks create "JobFailureAlert" \
  --url "https://hooks.example.com/uipath" \
  --events "job.faulted,job.stopped" \
  --secret "my-signing-secret" --output json

# Subscribe to ALL events (omit --events)
uip or webhooks create "AuditHook" \
  --url "https://hooks.example.com/audit" --output json
```

Options:

- `--secret <secret>` — shared secret used to sign every webhook delivery. Orchestrator includes the signature in the `X-UiPath-Signature` header of each POST as `sha256=<HMAC_SHA256(secret, raw_body)>`. The receiving server should recompute the HMAC over the unmodified request body and compare in constant time. Without `--secret`, payloads are sent without a signature — accept those only if the endpoint is private and you trust the network path.
- `--allow-insecure-ssl` — skip TLS verification on the webhook URL. Only set when targeting an HTTPS endpoint with a self-signed cert in non-production. Production targets should use a real cert; flipping this off after-the-fact requires `webhooks update --no-allow-insecure-ssl` (verify the flag exists in your CLI version with `--help`).

### List, Get, Update, Test, Delete

```bash
uip or webhooks list --enabled --output json
uip or webhooks get <webhook-key> --output json

uip or webhooks update <webhook-key> \
  --url "https://new.example.com/hook" \
  --events "job.faulted,queueItem.failed" --output json

# Toggle without renaming or changing other fields:
uip or webhooks update <webhook-key> --disabled --output json
uip or webhooks update <webhook-key> --enabled --output json

uip or webhooks ping <webhook-key> --output json     # dispatch a test ping event
uip or webhooks delete <webhook-key> --yes --output json
```

> **`ping` reports dispatch, not delivery.** The ping event goes through the asynchronous event pipeline; Success means the ping was queued, not that the endpoint answered. The API exposes no delivery result, so confirm receipt on the receiving endpoint (or its logs).

---

## Complete Example

Set up weekday processing with overflow handling and failure notifications.

```bash
# 1. Get the release key
uip or processes list --folder-path "Finance" --output json
# -> Key: "c3d4e5f6-..."

# 2. Time trigger: weekdays at 9 AM, skip US holidays
uip or calendars list --output json   # get calendar key
uip or triggers create --type time \
  --name "WeekdayInvoiceRun" \
  --release-key "c3d4e5f6-..." \
  --cron "0 0 9 ? * MON-FRI" --time-zone "UTC" \
  --calendar-key "<calendar-key>" \
  --runtime-type Unattended --job-priority Normal --output json

# 3. Queue trigger: fire when 10+ items accumulate
uip or queues list --folder-path "Finance" --output json   # get queue key
uip or triggers create --type queue \
  --name "InvoiceOverflowTrigger" \
  --release-key "c3d4e5f6-..." \
  --queue-key "d4e5f6a7-..." \
  --items-threshold 10 --max-jobs 5 --activate-on-complete \
  --runtime-type Unattended --job-priority High --output json

# 4. Webhook: notify on job failures
uip or webhooks create "InvoiceFailureAlert" \
  --url "https://hooks.slack.com/services/T00/B00/xxx" \
  --events "job.faulted,job.stopped" \
  --secret "webhook-signing-key" --output json

# 5. Verify everything is active
uip or triggers list --type time --folder-path "Finance" --enabled --output json
uip or webhooks list --enabled --output json
```

---

## Variations and Gotchas

- **Cron is Quartz 6-field, NOT Unix 5-field.** If a trigger never fires, check for 6 fields and `?` in day-of-month or day-of-week.
- **`--type` defaults to `time`.** Omitting it when you mean queue or API causes confusing errors.
- **`--release-key` is the process key** from `uip or processes list` (a GUID), NOT the package ID from `uip or packages list`.
- **Calendar keys come from `uip or calendars list`** -- an Orchestrator resource. Keep calendar and trigger timezones aligned.
- **Trigger history is the debugging tool.** When a trigger doesn't fire, `triggers history` shows why (no machines, license exhausted, calendar exclusion, auto-disabled). Check history before changing config.
- **Triggers are folder-scoped** -- every command needs `--folder-path` or `--folder-key`. **Webhooks are tenant-scoped** -- no folder flags.
- **Webhook `--events` behavior:** omit to subscribe to ALL events; provide to subscribe to specific events only. On update, adding `--events` switches from all-events to specific.
- **Auto-disable setting:** `Triggers.DisableWhenFailedCount` (via `uip or settings`) controls consecutive-failure auto-disable. Check with `uip or settings get "Triggers.DisableWhenFailedCount"`.

---

## Related

- [resources.md](resources.md) — Orchestrator resources overview and common flags
- Get the release key for `--release-key` → [`uipath-orchestrator`](run-jobs.md)
- Calendar management + tenant settings affecting trigger behavior → [`uipath-orchestrator`](tenant-admin.md)
- [process-queues.md](process-queues.md) -- Queue setup required before creating queue triggers
