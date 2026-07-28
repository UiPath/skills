---
name: uipath-insights
description: "UiPath Insights job monitoring via `uip insights` — query job execution metrics, failure analysis, and process performance. Covers job KPIs, failure reasons, completion trends, process breakdowns. For Orchestrator job start/stop/logs→uipath-platform, root-cause analysis of specific errors→uipath-troubleshoot, RPA workflow authoring→uipath-rpa."
when_to_use: "User says 'job failures', 'automation health', 'job success rate', 'processing time', 'which processes fail the most', 'failure reasons', 'job trends', 'how many jobs ran', 'insights dashboard', 'job metrics', 'job KPIs', 'job performance', 'uncompleted jobs', 'pending jobs', 'faulted jobs', 'job timeline', 'process details'. Also 'uip insights', 'insights jobs'. NOT for starting/stopping jobs (uipath-platform), NOT for root-cause debugging of a specific job error (uipath-troubleshoot), NOT for queue metrics (not yet supported)."
allowed-tools: Bash, Read
---

# UiPath Insights — Job Monitoring Agent Skill

Insights provides analytics and monitoring for UiPath automation execution. This skill covers **job monitoring** — querying aggregated job execution data for dashboards, health checks, and failure investigation.

All operations go through `uip insights jobs <subcommand> --output json`.

---

## When to Use

- Checking overall automation health (how many jobs ran, how many succeeded)
- Investigating job failures (which processes fail most, what are the failure reasons)
- Monitoring job execution trends over time (completed/uncompleted timelines)
- Getting per-process performance breakdowns
- Drilling into specific failure details for investigation

> **Not in scope:** Starting, stopping, or managing individual jobs (use `uip or jobs` via uipath-platform). Root-cause debugging of a specific job's error (use uipath-troubleshoot). Queue item metrics, robot utilization, or dashboard CRUD (not yet available in CLI).

---

## Login & Tenant Setup

**Default to Production. Only switch environment/org/tenant when explicitly stated in the request.**

- If the request mentions no environment, use the current session (defaults to prod `cloud.uipath.com`)
- If the request explicitly names an environment/org/tenant, check `uip login status` and re-login if needed

```bash
# Check current environment, org, and tenant
uip login status --output json

# Login to a specific environment (production cloud is the default)
uip login --authority https://cloud.uipath.com --tenant MyTenant

# Switch tenant within the same environment
uip login tenant set MyTenant
```

---

## Critical Rules

1. **A time range is always required.** Every `uip insights jobs` command needs either `--time-range <minutes>` (relative) or both `--started-after <epoch-ms>` and `--started-before <epoch-ms>` (absolute). Without one, the command fails. Common values:
   - `--time-range 60` — last 1 hour
   - `--time-range 1440` — last 24 hours
   - `--time-range 10080` — last 7 days
   - `--time-range 43200` — last 30 days

2. **Always use `--output json`.** All commands return a JSON envelope: `{ Result: "Success", Code: "<code>", Data: { ... } }`. Parse the `Data` field for the actual metrics.

3. **Filter options are repeatable.** `--folder-key`, `--process-name`, and `--machine-name` can be specified multiple times to filter by several values: `--process-name "ProcessA" --process-name "ProcessB"`.

4. **Empty data is normal.** If no jobs ran in the time window, the response will have `Data` with null/zero/empty fields. This is not an error.

5. **Start with summary, then drill down.** For any investigation, start with `summary` to get the big picture, then use specific subcommands to investigate areas of concern.

---

## Command Reference

All commands share these filter options:

| Option | Description |
|--------|-------------|
| `--time-range <minutes>` | Relative time range in minutes |
| `--started-after <epoch-ms>` | Absolute start time (Unix epoch ms) |
| `--started-before <epoch-ms>` | Absolute end time (Unix epoch ms) |
| `--folder-key <guid>` | Filter by folder key (repeatable) |
| `--process-name <name>` | Filter by process name (repeatable) |
| `--machine-name <name>` | Filter by machine name (repeatable) |
| `--timezone-offset <minutes>` | Client timezone offset from UTC |

### summary

Get job KPIs: total count, successful count, and average processing time.

```bash
uip insights jobs summary --time-range 1440 --output json
```

**Key Data fields:** `jobsCount`, `successfulJobsCount`, `averageProcessingTime`

**Use when:** User asks "how are my automations doing?" or "what's my job success rate?"

### completed-timeline

Get completed jobs over time, grouped by job state (successful, faulted, stopped, etc.).

```bash
uip insights jobs completed-timeline --time-range 1440 --output json
```

**Key Data fields:** `jobState`, `jobCountByTime`, `timestamp`

**Use when:** User asks "show me job completion trends" or "when do most jobs run?"

### uncompleted-timeline

Get running and pending jobs over time.

```bash
uip insights jobs uncompleted-timeline --time-range 1440 --output json
```

**Key Data fields:** `jobState`, `jobCountByTime`, `timestamp`

**Use when:** User asks "are there stuck jobs?" or "how many jobs are still running?"

### top-failures

Get processes ranked by failure count.

```bash
uip insights jobs top-failures --time-range 43200 --output json
```

**Key Data fields:** `processName`, `jobCountByTime`

**Use when:** User asks "which processes fail the most?" or "what's causing failures?"

### failures-by-reason

Get job failures grouped by exception reason, with total job count for context.

```bash
uip insights jobs failures-by-reason --time-range 1440 --output json
```

**Key Data fields:** `processExceptionReason`, `processName`, `robotName`, `jobsCount`

**Use when:** User asks "why are jobs failing?" or "what are the common error messages?"

### process-details

Get per-process job breakdown with counts by state.

```bash
uip insights jobs process-details --time-range 1440 --output json
```

**Key Data fields:** `processName`, `jobAggregate`

**Use when:** User asks "show me per-process stats" or "which process has the most faulted jobs?"

### failure-details

Get detailed failure information for drill-down investigation.

```bash
uip insights jobs failure-details --time-range 1440 --output json
```

**Key Data fields:** `processName`, `machineName`, `processExceptionReason`, `startTime`, `endTime`

**Use when:** User asks "show me the details of recent failures" or "which machines are failing?"

---

## Workflow: Investigate Job Health

Follow this pattern when a user asks about automation health or job failures:

```bash
# 1. Check login
uip login status --output json

# 2. Get the big picture — how many jobs ran? how many succeeded?
uip insights jobs summary --time-range 1440 --output json

# 3. If success rate is low, find which processes fail most
uip insights jobs top-failures --time-range 1440 --output json

# 4. Find out WHY they're failing
uip insights jobs failures-by-reason --time-range 1440 --output json

# 5. Drill into specific failure details
uip insights jobs failure-details --time-range 1440 --output json

# 6. For time-based trends, check timelines
uip insights jobs completed-timeline --time-range 10080 --output json
```

**Present findings clearly:** After gathering data, summarize for the user:
- Total jobs vs successful jobs (derive failure rate)
- Top failing processes by name
- Most common failure reasons
- Which machines are affected
- Whether failures are trending up or down

---

## Workflow: Filter by Folder or Process

When the user asks about a specific folder or process:

```bash
# Filter by folder
uip insights jobs summary --time-range 1440 --folder-key "abc-123-def" --output json

# Filter by process name
uip insights jobs top-failures --time-range 43200 --process-name "Invoice_Processing" --output json

# Combine filters
uip insights jobs failures-by-reason --time-range 1440 \
  --folder-key "abc-123-def" \
  --process-name "Invoice_Processing" \
  --output json
```

To discover available folder keys, use `uip or folders list --output json` (from the uipath-platform skill).

---

## Workflow: Absolute Time Range

When the user specifies an exact date range instead of "last N hours":

```bash
# Convert dates to epoch milliseconds
# Example: 2026-07-01 00:00:00 UTC to 2026-07-06 00:00:00 UTC
uip insights jobs summary \
  --started-after 1782691200000 \
  --started-before 1783123200000 \
  --output json
```

Compute epoch milliseconds in bash:
```bash
# macOS
START=$(date -j -f "%Y-%m-%d" "2026-07-01" +%s)000
END=$(date -j -f "%Y-%m-%d" "2026-07-06" +%s)000

# Linux
START=$(date -d "2026-07-01" +%s)000
END=$(date -d "2026-07-06" +%s)000

uip insights jobs summary --started-after "$START" --started-before "$END" --output json
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Not logged in` | Auth expired | `uip login` |
| `time range is required` | Missing `--time-range` or `--started-after`/`--started-before` | Add `--time-range 1440` (or your preferred window) |
| `API request failed: 401` | Token doesn't have Insights access | Re-login; ensure the org has Insights enabled |
| `API request failed: 403` | User has no folder permissions | Check folder assignments in Orchestrator Admin |
| `API request failed: 500` | Server error (often missing time range on older deployments) | Ensure time range is provided in the request body |
| All Data fields are null/zero | No jobs ran in the given time window | Widen the `--time-range` (try 43200 for 30 days) |

---

## What NOT to Do

- **Don't call `uip insights jobs` without a time range.** The server returns a 500 with a misleading success-shaped response. Always pass `--time-range` or `--started-after`/`--started-before`.
- **Don't start, stop, or manage individual jobs.** This skill is for monitoring and analytics only. Use `uip or jobs start/stop` via uipath-platform to manage jobs.
- **Don't construct raw API calls to the Insights endpoint.** The CLI handles auth headers (`X-UiPath-Internal-AccountName`, `X-UiPath-Internal-TenantName`), URL construction, and error handling. Hand-rolling `curl` or `fetch` calls will miss these.
- **Don't retry on auth errors.** If `uip insights jobs` returns 401 or "Not logged in", the fix is `uip login`, not retrying the same command.
- **Don't use this skill for root-cause debugging.** "Why did job X fail with error Y?" is a troubleshooting question — hand off to uipath-troubleshoot. This skill answers "which processes fail the most and what are the common reasons."

---

## References

For deeper guidance, read these files only when needed:

- [`references/jobs-commands-guide.md`](references/jobs-commands-guide.md) — Full command reference with all options, response shapes, and example outputs
- [`references/investigation-playbook-guide.md`](references/investigation-playbook-guide.md) — Step-by-step playbooks for common investigation scenarios
