# Tenant Administration

Configure tenant settings, manage calendars for scheduling, export audit logs, and work with credential stores, feeds, and job attachments.

> For full option details on any command, use `--help` (e.g., `uip or settings list --help`).

---

## When to Use

- Configuring tenant-level settings (timezone, email, deployment URLs, trigger behavior)
- Setting up calendars to exclude non-working days from trigger schedules
- Auditing user actions for compliance or debugging
- Inspecting credential stores used by assets and unattended execution
- Listing package feeds to target specific repositories
- Downloading attachments from completed or failed jobs

## Prerequisites

- Authenticated (`uip login`)
- Tenant selected (`uip login tenant set "<tenant>"`)
- Appropriate admin permissions (Settings and Audit Logs require tenant admin; other commands vary by role)

---

## Settings

Tenant settings are dot-notation key-value pairs that control tenant behavior. Use `settings list` to discover keys and `settings execution` for structured settings with allowed values.

| Command | What it does |
|---------|--------------|
| `uip or settings list` | List all settings. Filter with `--scope Application\|Tenant\|User\|All`. |
| `uip or settings get <key>` | Get a single setting value by key. |
| `uip or settings update <key> <value>` | Update a setting value. |
| `uip or settings execution` | Get execution settings with display names, types, and allowed values. Use `--scope 0` (Global) or `--scope 1` (Robot). |
| `uip or settings timezones` | List all valid timezone IDs (for use with `Abp.Timing.TimeZone`). |

**Common setting keys:**

| Key | Category | Example value |
|-----|----------|---------------|
| `Abp.Timing.TimeZone` | General | `UTC`, `Europe/Bucharest` |
| `Abp.Localization.DefaultLanguageName` | General | `en`, `fr`, `de` |
| `Alerts.Email.Enabled` | Email | `true` / `false` |
| `Triggers.DisableWhenFailedCount` | Triggers | `10` (consecutive failures to auto-disable) |
| `Triggers.JobsCountStrategy` | Triggers | `PERPROCESS` / `PERTRIGGER` |
| `Jobs.TerminatingJobsTimeout` | Jobs | `1440` (minutes) |

```bash
# Check current timezone
uip or settings get "Abp.Timing.TimeZone" --output json

# Change tenant timezone
uip or settings timezones --output json   # find valid ID first
uip or settings update "Abp.Timing.TimeZone" "Europe/Bucharest" --output json

# View execution settings with allowed values
uip or settings execution --scope 0 --output json
```

---

## Calendars

Calendars define non-working days (holidays, company shutdowns). Time triggers reference a calendar to skip runs on excluded dates.

**Workflow: create calendar, then use its key in trigger creation.**

| Command | What it does |
|---------|--------------|
| `uip or calendars list` | List calendars (returns Id, Name, TimeZoneId). |
| `uip or calendars get <key>` | Get calendar details including excluded dates. |
| `uip or calendars create <name>` | Create a calendar. Use `--time-zone` (defaults to UTC). |
| `uip or calendars update <key>` | Update name or timezone (`--name`, `--time-zone`). |
| `uip or calendars delete <key>` | Delete a calendar. |

```bash
# Create a calendar for US holidays
uip or calendars create "US Holidays" --time-zone "America/New_York" --output json
# Save the returned Key (GUID)

# Use the calendar key when creating a time trigger
uip resource triggers create --type time --name "WeekdayReport" \
  --release-key <process-key> --cron "0 9 * * 1-5" \
  --calendar-key <calendar-key> --time-zone "America/New_York" \
  --runtime-type Unattended --job-priority Normal \
  --folder-path "Finance" --output json
```

---

## Audit Logs

Audit logs record who did what and when across the tenant. Filter by component, action, user, or date range. Export to CSV for compliance reporting.

| Command | What it does |
|---------|--------------|
| `uip or audit-logs list` | List audit entries with filters (see below). |
| `uip or audit-logs list --export` | Export logs to CSV instead of terminal output. Use `-o <path>` to set the file path. |

**Filter options for `audit-logs list`:**

| Option | Description | Examples |
|--------|-------------|---------|
| `--component` | Entity type | `Users`, `Assets`, `Processes`, `Queues`, `Jobs`, `Folders`, `Machines`, `Roles`, `Settings`, `Schedules` |
| `--action` | Action performed | `Create`, `Update`, `Delete`, `StartJob`, `StopJob`, `Upload`, `Download` |
| `--user` | Username | `admin@company.com` |
| `--created-after` | Entries after date (ISO 8601) | `2026-04-01`, `2026-04-01T00:00:00Z` |
| `--created-before` | Entries before date (ISO 8601) | `2026-04-15` |

```bash
# List recent job-related audit entries
uip or audit-logs list --component "Jobs" --output json

# Export last week's audit logs to CSV
uip or audit-logs list \
  --created-after "2026-04-14" --created-before "2026-04-22" \
  --export -o audit-week.csv
```

---

## Credential Stores

Credential stores are tenant-scoped backends that hold secrets used by Credential and Secret assets. The default store is Orchestrator's built-in database; external stores (Azure Key Vault, CyberArk, etc.) can be added via Orchestrator UI.

| Command | What it does |
|---------|--------------|
| `uip or credential-stores list` | List stores. Filter with `--name` (contains match) or `--id` (exact numeric key). |
| `uip or credential-stores get <key>` | Get full details for a store (type, host, configuration). |

```bash
# List all credential stores
uip or credential-stores list --output json

# Get details for a specific store
uip or credential-stores get 42 --output json
```

Credential store keys are referenced when:
- Creating `Credential` or `Secret` type assets (the asset is stored in the specified credential store)
- Configuring unattended user execution with external secret references

---

## Feeds

Feeds are NuGet repositories that store automation packages (.nupkg) and libraries. Each tenant has a default feed; additional feeds can be configured.

| Command | What it does |
|---------|--------------|
| `uip or feeds list` | List available feeds (returns Id, Name, FeedType, FeedUrl). |

```bash
uip or feeds list --output json
```

Feed IDs are used with:
- `uip or packages list --feed-id <id>` -- browse packages in a specific feed
- `uip resource libraries list --feed-id <id>` -- browse libraries in a specific feed
- Omit `--feed-id` to use the default tenant feed

---

## Attachments

Attachments are files associated with jobs -- screenshots, reports, data exports, or files passed as input. They are tenant-scoped (no folder context needed).

| Command | What it does |
|---------|--------------|
| `uip or attachments list --job-key <key>` | List attachments for a job (returns AttachmentId, Name, Category). |
| `uip or attachments download <attachment-id>` | Download an attachment to disk. Use `-o <path>` to set the output file. |

```bash
# List attachments from a completed job
uip or attachments list --job-key "abc12345-..." --output json

# Download a specific attachment
uip or attachments download "def67890-..." -o report.pdf
```

Attachments from previous jobs can be reused as input: `uip or jobs start <process-key> --attachment-id <id>`.

---

## Complete Example

Export last week's audit logs for user-related actions, then download attachments from a failed job.

```bash
# 1. Export audit logs for the past week, filtered to user actions
uip or audit-logs list \
  --component "Users" \
  --created-after "2026-04-14" --created-before "2026-04-22" \
  --export -o user-audit-week.csv

# 2. Find the failed job (inspect audit logs or list jobs directly)
uip or jobs list --state Faulted \
  --created-after "2026-04-14" --folder-path "Finance" --output json

# 3. List attachments from the faulted job
uip or attachments list --job-key "<faulted-job-key>" --output json

# 4. Download the attachment for investigation
uip or attachments download "<attachment-id>" -o error-screenshot.png
```

---

## Gotchas

- **Settings keys are dot-notation.** Use `settings list` to discover valid keys -- do not guess. Example: `Abp.Timing.TimeZone`, not `timezone` or `TimeZone`.
- **Calendar timezone affects trigger scheduling.** A trigger using a calendar will skip dates according to the calendar's timezone, which may differ from the trigger's own timezone. Keep them aligned.
- **Audit log export is async.** The `--export` flag triggers a server-side export job. The CLI polls until the CSV is ready, then downloads it. Large exports may take a few seconds.
- **Credential store keys are numeric**, not GUIDs. This is an exception to the usual GUID convention in the Orchestrator CLI.
- **Feed IDs are optional.** Most `packages` and `libraries` commands default to the tenant feed. Only specify `--feed-id` when you have multiple feeds configured.
- **Attachments are tenant-scoped.** You do not need `--folder-path` or `--folder-key` -- the `list` command resolves the folder from the job key automatically.

---

## Related

- [setup-environment.md](setup-environment.md) -- Credential stores are used during unattended user setup.
- [Triggers & Webhooks](../resources/triggers-and-webhooks.md) -- Calendars are referenced by `--calendar-key` when creating time triggers.
- [orchestrator.md](orchestrator.md) -- Parent reference with common flags and pagination patterns.
