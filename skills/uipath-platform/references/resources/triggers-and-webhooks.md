# Triggers & Webhooks

Automate job execution with time, queue, and API triggers, and set up webhooks for external event notifications.

> For full option details on any command, use `--help` (e.g., `uip resource triggers create --help`).

## When to Use

- Scheduling recurring jobs on a cron schedule (nightly reports, weekday processing)
- Auto-processing queue items when they exceed a threshold
- Exposing HTTP endpoints so external systems can start jobs via API call
- Notifying external systems when Orchestrator events occur (job faulted, queue item failed, etc.)

## Prerequisites

- Authenticated (`uip login`)
- Target folder exists with machines assigned (see [setup-environment.md](../orchestrator/setup-environment.md))
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
| Weekdays 9 AM | `0 0 9 ? * 1-5` | `0 9 * * 1-5` |
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
uip resource triggers create --type time \
  --name "WeekdayInvoiceRun" \
  --release-key <process-key> \
  --cron "0 0 9 ? * 1-5" \
  --time-zone "UTC" \
  --runtime-type Unattended \
  --job-priority Normal \
  --folder-path "Finance" --output json
```

Additional options: `--calendar-key` (skip holidays, from `uip or calendars list`), `--stop-strategy` (`SoftStop`|`Kill`), `--input-arguments` (JSON).

### Queue Trigger

```bash
uip resource queues list --folder-path "Finance" --output json  # get queue key

uip resource triggers create --type queue \
  --name "InvoiceQueueTrigger" \
  --release-key <process-key> \
  --queue-key <queue-key> \
  --items-threshold 1 --max-jobs 3 \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json
```

Additional options: `--items-per-job` (default 1), `--activate-on-complete` (re-trigger on job completion).

### API Trigger

```bash
uip resource triggers create --type api \
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
uip resource triggers list --type time --folder-path "Finance" --output json

# Filter: only enabled, by name
uip resource triggers list --type queue --folder-path "Finance" --enabled --name "Invoice" --output json

# Get details
uip resource triggers get <trigger-key> --type time --folder-path "Finance" --output json

# Update (only provided fields change)
uip resource triggers update <trigger-key> --type time \
  --cron "0 30 8 ? * 1-5" --folder-path "Finance" --output json
```

---

## Step 4: Enable, Disable, Delete

```bash
uip resource triggers disable <trigger-key> --type time --folder-path "Finance" --output json
uip resource triggers enable <trigger-key> --type time --folder-path "Finance" --output json
uip resource triggers delete <trigger-key> --type time --folder-path "Finance" --output json
```

---

## Step 5: View Trigger History

Shows every activation attempt and why it succeeded or failed. Check this before assuming broken config.

```bash
uip resource triggers history <trigger-key> --folder-path "Finance" --output json
```

Entries include `logEventType` (Fired, Failed, Skipped) and `message` ("No machines available", "License limit reached", "Calendar exclusion").

---

## Webhooks

Webhooks are **tenant-scoped** -- no `--folder-path` needed. They POST to your URL when Orchestrator events occur.

### Discover Event Types

```bash
uip resource webhooks event-types --output json
```

Returns names like `job.completed`, `job.faulted`, `queueItem.failed`. Use these with `--events`.

### Create a Webhook

```bash
# Subscribe to specific events
uip resource webhooks create \
  --name "JobFailureAlert" \
  --url "https://hooks.example.com/uipath" \
  --events "job.faulted,job.stopped" \
  --secret "my-signing-secret" --output json

# Subscribe to ALL events (omit --events)
uip resource webhooks create \
  --name "AuditHook" \
  --url "https://hooks.example.com/audit" --output json
```

Options: `--secret` (HMAC signature validation), `--allow-insecure-ssl` (skip TLS verification).

### List, Get, Update, Test, Delete

```bash
uip resource webhooks list --enabled --output json
uip resource webhooks get <webhook-key> --output json

uip resource webhooks update <webhook-key> \
  --url "https://new.example.com/hook" \
  --events "job.faulted,queueItem.failed" --output json

uip resource webhooks ping <webhook-key> --output json     # test connectivity
uip resource webhooks delete <webhook-key> --output json
```

---

## Complete Example

Set up weekday processing with overflow handling and failure notifications.

```bash
# 1. Get the release key
uip or processes list --folder-path "Finance" --output json
# -> Key: "c3d4e5f6-..."

# 2. Time trigger: weekdays at 9 AM, skip US holidays
uip or calendars list --output json   # get calendar key
uip resource triggers create --type time \
  --name "WeekdayInvoiceRun" \
  --release-key "c3d4e5f6-..." \
  --cron "0 0 9 ? * 1-5" --time-zone "UTC" \
  --calendar-key "<calendar-key>" \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json

# 3. Queue trigger: fire when 10+ items accumulate
uip resource queues list --folder-path "Finance" --output json   # get queue key
uip resource triggers create --type queue \
  --name "InvoiceOverflowTrigger" \
  --release-key "c3d4e5f6-..." \
  --queue-key "d4e5f6a7-..." \
  --items-threshold 10 --max-jobs 5 --activate-on-complete \
  --runtime-type Unattended --job-priority High \
  --folder-path "Finance" --output json

# 4. Webhook: notify on job failures
uip resource webhooks create \
  --name "InvoiceFailureAlert" \
  --url "https://hooks.slack.com/services/T00/B00/xxx" \
  --events "job.faulted,job.stopped" \
  --secret "webhook-signing-key" --output json

# 5. Verify everything is active
uip resource triggers list --type time --folder-path "Finance" --enabled --output json
uip resource webhooks list --enabled --output json
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

- [resources.md](resources.md) -- Resource tool overview and common flags
- [../orchestrator/run-jobs.md](../orchestrator/run-jobs.md) -- Create processes, get the release key needed for triggers
- [../orchestrator/tenant-admin.md](../orchestrator/tenant-admin.md) -- Calendar management, tenant settings affecting trigger behavior
- [process-queues.md](process-queues.md) -- Queue setup required before creating queue triggers
