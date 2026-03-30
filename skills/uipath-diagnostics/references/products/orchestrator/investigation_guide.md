# Orchestrator Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Process/Release** — job release name matches the user's project or process name
- **Queue** — queue name matches what the user reported (if queue-related)
- **Folder** — data comes from the correct Orchestrator folder
- **Time window** — timestamps fall within the relevant period the user described
- **Robot/Machine** — if the user mentioned a specific robot or machine, verify the data belongs to it

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for Orchestrator issues, gather and verify these before drawing conclusions:

1. **Folder context** — confirm the folder the process runs in; permissions, jobs and assets are folder-scoped
2. **Process version** — confirm the deployed package version matches what the user expects
3. **Robot assignment** — verify the robot/machine template is assigned to the folder and has capacity
4. **Execution logs** — use job traces/logs to reconstruct the actual execution path, don't infer from job status alone
5. **Timing** — check job start/end times, queue transaction durations, and trigger schedules against reported symptoms
6. **Dependencies** — check `## Dependencies` in `overview.md` for cross-product issues (e.g., Identity Server, Elasticsearch, SQL Server)
