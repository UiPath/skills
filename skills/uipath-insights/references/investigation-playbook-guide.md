# Insights — Investigation Playbooks

Step-by-step playbooks for common job monitoring scenarios. Each playbook shows the exact commands to run and how to interpret the results.

## Playbook 1: "How healthy are my automations?"

User asks about overall automation health, success rates, or general status.

```bash
# Step 1: Get the summary KPIs
uip insights jobs summary --time-range 1440 --output json

# Step 2: Interpret the results (Data keys are PascalCase)
# - JobsCount: total jobs in the time window
# - SuccessfulJobsCount: jobs that completed successfully
# - AverageProcessingTime: mean execution time. The CLI passes this through
#   unchanged and does not label a unit, so do not state one to the user.
#
# Failure rate = (JobsCount - SuccessfulJobsCount) / JobsCount * 100
#
# Thresholds (rules of thumb):
#   < 5% failure rate  → healthy
#   5-15% failure rate → needs attention
#   > 15% failure rate → investigate immediately
```

If the failure rate is concerning, move to Playbook 2.

## Playbook 2: "Which processes are failing?"

User wants to know what's breaking.

```bash
# Step 1: Get processes ranked by failure count (use 30 days for a broader view)
uip insights jobs top-failures --time-range 43200 --output json

# Step 2: Get the failure reasons
uip insights jobs failures-by-reason --time-range 43200 --output json

# Step 3: Present findings as a table:
# | Process Name | Failure Count | Top Reason |
# |---|---|---|
# | Invoice_Processing | 23 | ApplicationException: File not found |
# | Email_Parser | 15 | TimeoutException: SMTP server unreachable |
```

## Playbook 3: "Why did this specific process fail?"

User asks about failures in a specific process.

```bash
# Step 1: Filter failures to that process
uip insights jobs failures-by-reason --time-range 1440 \
  --process-name "Invoice_Processing" --output json

# Step 2: Get detailed failure info (machine, timestamps, error messages)
uip insights jobs failure-details --time-range 1440 \
  --process-name "Invoice_Processing" --output json

# Step 3: Check if it's a recent regression with the timeline
uip insights jobs completed-timeline --time-range 10080 \
  --process-name "Invoice_Processing" --output json

# Step 4: Present findings:
# - Most common error reason
# - Which machines are affected
# - When failures started (trend direction)
# - Recommended next steps
```

## Playbook 4: "Are there stuck or long-running jobs?"

User asks about jobs that haven't completed.

```bash
# Step 1: Check uncompleted jobs
uip insights jobs uncompleted-timeline --time-range 1440 --output json

# Step 2: Get the summary to compare completed vs uncompleted
uip insights jobs summary --time-range 1440 --output json

# Step 3: If many uncompleted, check per-process breakdown
uip insights jobs process-details --time-range 1440 --output json
```

## Playbook 5: "Compare this week vs last week"

User wants to see if things are getting better or worse.

Resolve both week boundaries to epoch milliseconds first, with the platform-specific `date` recipes under Absolute Time Ranges in [`jobs-commands-guide.md`](jobs-commands-guide.md). Treat `--started-before` as exclusive: pass this Monday 00:00:00 UTC as the upper bound so the window covers all of last week.

```bash
# This week (last 7 days)
uip insights jobs summary --time-range 10080 --output json

# Last week: absolute boundaries, resolved per Absolute Time Ranges
# in jobs-commands-guide.md, passed as literal numbers
uip insights jobs summary \
  --started-after <last-monday-epoch-ms> \
  --started-before <this-monday-epoch-ms> \
  --output json

# Compare JobsCount, SuccessfulJobsCount, and AverageProcessingTime
# between the two results
```

## Playbook 6: "Show me jobs for a specific folder"

User asks about a specific Orchestrator folder.

Follow [`filter-discovery-guide.md`](filter-discovery-guide.md) for pagination, exact-match handling, and the limits of the 30-day activity window.

```bash
# Step 1: Find the folder key
uip insights filter-folders list --output json

# Step 2: Query insights with folder filter
uip insights jobs summary --time-range 1440 \
  --folder-key "<FOLDER_KEY_FROM_STEP_1>" --output json

uip insights jobs top-failures --time-range 1440 \
  --folder-key "<FOLDER_KEY_FROM_STEP_1>" --output json
```

A folder with no recent Insights activity will not appear. Hand off to `uipath-platform` for the full visible inventory.

To scope by several folders or processes at once, repeat the flag once per value; see the repeatable-options rule in [`jobs-commands-guide.md`](jobs-commands-guide.md).

## Interpreting Array Data

Several endpoints return parallel arrays. The same index across arrays corresponds to the same entity:

```json
{
  "ProcessName": ["ProcessA", "ProcessB", "ProcessC"],
  "JobCountByTime": [[10, 5, 2]]
}
```

This means:
- ProcessA had 10 failures
- ProcessB had 5 failures
- ProcessC had 2 failures

## When to Hand Off to Other Skills

| Situation | Hand off to |
|---|---|
| User wants to start/stop/restart a specific job | `uipath-platform` (`uip or jobs start`) |
| User wants to read the logs of a failed job | `uipath-platform` (`uip or jobs logs`) |
| User wants to debug why a specific job error happened | `uipath-troubleshoot` |
| User wants to find a folder key to filter by | `uip insights filter-folders list` (see [`filter-discovery-guide.md`](filter-discovery-guide.md)) |
| User wants to fix the code that's causing failures | `uipath-rpa` or `uipath-agents` |
