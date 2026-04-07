# Orchestrator Investigation Guide

## Data Correlation

Before fetching ANY job, queue, or asset data, resolve identity first:

1. **Folder** — resolve the folder key (GUID). All Orchestrator data is folder-scoped. Use `uip or folders list-current-user` to find all accessible folders (Personal, Solution, and Standard). `uip or folders list` only returns Standard folders — it misses Personal and Solution types. Use `uip or folders get <key-or-path>` to confirm details. If the folder is inaccessible, STOP — nothing else will be valid without it. **After resolving the folder, verify it contains the target entity** (e.g., run `uip or jobs get <key>` or a scoped query for the expected process/queue). If the target entity is not found in the resolved folder, try other folders from `folders list-current-user` before continuing. Do NOT proceed with a folder that returns empty results for the target entity.
2. **Process** — identify the process name (from user input, working directory `project.json`, or package name). All subsequent queries filter by this process.
3. **Time window** — establish the relevant period from the user's report.

Only after identity is resolved, fetch data and verify every result against it:

- **Process/Release** — job release name matches the identified process
- **Queue** — queue name matches what the user reported (if queue-related)
- **Robot/Machine** — if the user mentioned a specific robot or machine, verify the data belongs to it
- **Timestamps** — fall within the established time window

If data doesn't match: **discard it**. Do NOT fetch details for jobs or items from other processes. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

4. **Job selection** — if multiple jobs exist for the identified process, present the list to the user (showing state, timestamp, error summary) and ask which one to investigate. If the user said "latest" or didn't specify, default to the most recent faulted job and state this assumption explicitly. Do NOT fetch details for multiple jobs — investigate one at a time.

## Job Data Bundle

For every job under investigation, gather these in order. Write each to `raw/` immediately.

1. **Job details** — `uip or jobs get <key>` — state, input/output arguments, timing, machine info, error details
2. **Job logs** — `uip or jobs logs <key>` — robot execution logs, newest-first. Folder is inferred from the job key. Use `--level Error` to quickly find errors. Use `--limit` to control how many entries (default 50)
3. **Job history** — `uip or jobs history <key>` — job state transition history (timestamps for each state change: Pending → Running → Faulted). Useful for identifying delays and lifecycle issues.
4. **Job traces (agentic only)** — `uip or jobs traces <key>` — LlmOps execution traces for Agent-type processes only (LLM interactions, tool calls, agent decisions). Not available for standard RPA jobs.

This is the baseline. Domain-specific data gathering builds on it — see the investigation guide for each matched domain (UI Automation, Integration Service, Maestro) for additional steps after the baseline.

## Testing Prerequisites

When testing hypotheses for Orchestrator issues, gather and verify these before drawing conclusions:

1. **Folder context** — confirm the folder the process runs in; permissions, jobs and assets are folder-scoped
2. **Process version** — confirm the deployed package version matches what the user expects
3. **Robot assignment** — verify the robot/machine template is assigned to the folder and has capacity
4. **Execution logs** — use job traces/logs to reconstruct the actual execution path, don't infer from job status alone
5. **Timing** — check job start/end times, queue transaction durations, and trigger schedules against reported symptoms
6. **Dependencies** — check `## Dependencies` in `overview.md` for cross-product issues (e.g., Identity Server, Elasticsearch, SQL Server)
