# Orchestrator Investigation Guide

## Output Capture Pattern

Every `uip` data-gathering command below assumes two patterns to keep the agent's context lean AND preserve an audit trail:

1. **Filter at the source with `--output-filter`** — only pull the fields you actually need. Do NOT fetch the full response and truncate the output with `[:3000]` or similar post-hoc slicing — that silently drops information.
2. **Save AND inspect in one call with `| tee`** — pipe the filtered response through `tee` to `.local/investigations/raw/<command>.json`. The response is visible in the tool result for immediate use AND saved on disk for the hypothesis-tester to re-read later.

Reference shape:

```
uip or jobs list --folder-key <key> --state Faulted \
  --output json \
  --output-filter '[].{Key:Key,State:State,StartTime:StartTime,ReleaseName:ReleaseName}' \
  | tee .local/investigations/raw/triage-jobs-list.json
```

**Filter-failure fallback.** If `--output-filter '<jsonpath>'` returns an empty result, an error, or a shape the agent cannot interpret (likely cause: a field name in the documented filter has drifted from the current CLI response schema), retry the SAME command ONCE without `--output-filter` to see the actual response shape. Use that unfiltered response for the current call, and flag the mismatch in `evidence/notes.json` so the discrepancy gets fixed in the guide. Do NOT silently swallow filter errors — they mean the documented filter is stale.

Anti-patterns — do NOT do these:

- `uip <cmd> --output json > file.json` — redirect alone hides stdout; the agent then needs an extra turn running `python -c "json.load(...)"` just to see what it fetched.
- `uip <cmd> --output json | head -c 3000` or any byte/character slice — truncation silently drops fields that may be required by the playbook downstream.
- Fetching the unfiltered full response when only 2–3 fields are needed — bloats the agent's context and the cache-read budget on every subsequent turn.
- Inventing JSONpath field names on the fly. Use only the filter expressions documented in this guide for each command. If a documented filter fails, apply the filter-failure fallback above — do NOT guess different field names.

If the CLI's `--output-filter` cannot express the shape you need, see `scripts/` for skill-provided filter helpers, OR fetch with a minimal field set first and only re-fetch with more fields when a specific gap forces it.

## Data Correlation

Before fetching ANY job, queue, or asset data, resolve identity first:

1. **Folder** — resolve the folder key (GUID). All Orchestrator data is folder-scoped, so the folder MUST be pinned before any data fetch.

   **STOP. Before running ANY `uip` command, check the user's prompt for a folder name. The answer is binary:**

   - **(A) User named a folder explicitly in the prompt** (e.g., "the failed job in *Shared*", "in *PurchaseOrderProcessing* folder") → continue with step A below.
   - **(B) User did NOT name a folder** (e.g., "investigate my last failed job", "my automation broke") → **STOP and ask the user. Do NOT run `uip or jobs list` looking for the failed job. Do NOT iterate over folder keys hoping to find it. Do NOT infer the folder from `project.json` — that is a hint to surface in the ask, not a selector to commit on.** Go directly to step B below.

   The above is non-negotiable. The single most expensive triage failure mode is `jobs list` enumeration against arbitrary folders trying to "find" a job whose folder is unspecified — it burns 20–40 turns and an extra subagent dispatch before the orchestrator's sanity gate catches the wrong pick. Asking the user is 2 turns. Always cheaper.

   ---

   **Step A — User named a folder.** Resolve its key:
   ```
   uip or folders list --output json \
     --output-filter "[?DisplayName=='<name>'].{Key:Key,FullyQualifiedName:FullyQualifiedName}" \
     | tee .local/investigations/raw/triage-folders-list.json
   ```
   If the result is empty (no folder with that name), write `needs_input.json` listing the available folders and asking the user to confirm the correct one. Do NOT guess. Proceed once the key is resolved.

   ---

   **Step B — User did NOT name a folder. Ask, do not search.**

   1. Run folders list ONCE to get candidates:
      ```
      uip or folders list --output json \
        --output-filter "[].{Key:Key,DisplayName:DisplayName,FullyQualifiedName:FullyQualifiedName}" \
        | tee .local/investigations/raw/triage-folders-list.json
      ```
   2. Write `needs_input.json` with the candidate folder names as `options`. If `project.json` exists in the working directory and its `name` matches one of the folders, put that folder FIRST in the options list with the label `"<folder> (your current project)"` — surface the hint, do not select for the user. Ask: *"Which folder is the failing job in?"*
   3. Return to the orchestrator. Do NOT continue with any data fetch.
   4. On re-spawn with the user's answer, record the chosen folder in `state.json` and proceed to step 2 (Process).

   **Bounded fallback** — applies ONLY when the user explicitly answers step B.3 with "I don't know" / "no preference" / equivalent. Run ONCE without folder filter, pick the most-recent, record the folder, proceed:
   ```
   uip or jobs list --state <state> --output json \
     --output-filter "[].{Key:Key,State:State,StartTime:StartTime,FolderName:FolderName}" \
     | tee .local/investigations/raw/triage-jobs-cross-folder.json
   ```
   `<state>` is the state the user named (`Faulted` for "failed", `Pending` for "stuck", etc.). If this returns nothing, report and stop — do NOT relax the state filter and do NOT retry against per-folder keys.

   ---

   Use `uip or folders get <key-or-path>` to confirm details if needed. If the folder is inaccessible, STOP — nothing else will be valid without it.
2. **Process** — identify the process name (from user input, working directory `project.json`, or package name). All subsequent queries filter by this process.
3. **Time window** — establish the relevant period from the user's report.

Only after identity is resolved, fetch data and verify every result against it:

- **Process/Release** — job release name matches the identified process
- **Queue** — queue name matches what the user reported (if queue-related)
- **Robot/Machine** — if the user mentioned a specific robot or machine, verify the data belongs to it
- **Timestamps** — fall within the established time window

If data doesn't match: **discard it**. Do NOT fetch details for jobs or items from other processes. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

4. **Job selection** — if multiple jobs exist for the identified process, present the list to the user (showing state, timestamp, error summary) and ask which one to investigate. If the user said "latest" or didn't specify, default to the most recent faulted job and state this assumption explicitly. Do NOT fetch details for multiple jobs — investigate one at a time. **If the user gave no job key but described the job by state + folder** (e.g. "my pending job in Shared"), resolve it by enumeration: `uip or jobs list --folder-key <key> --state <State> --output json`. If exactly one candidate matches, proceed with it; if several, present them and ask. Do not ask the user for a key you can discover this way.
5. **Queue item** — if the issue is queue-related, resolve the queue and item. Use `uip or queues list --folder-key <key> --name <name>` to find the queue definition key. If the user provided a queue item key, use `uip or queue-items get <item-key> --folder-key <key>` to confirm it exists and extract the queue name, error details, and retry status. If the queue item is not found in the first folder, try other folders from `folders list`.

## Job Data Bundle

For every job under investigation, gather these in order. Follow the Output Capture Pattern above — pipe through `tee` and filter at the source.

1. **Job details** — state, input/output arguments, timing, machine info, error details
   ```
   uip or jobs get <key> --output json \
     --output-filter '{Key:Key,State:State,StartTime:StartTime,EndTime:EndTime,Info:Info,JobError:JobError,InputArguments:InputArguments,OutputArguments:OutputArguments}' \
     | tee .local/investigations/raw/triage-job-get.json
   ```
2. **Job logs** — robot execution logs, newest-first. Folder is inferred from the job key. Use `--level Error` to find errors quickly. `--limit` controls entry count (default 50).
   ```
   uip or jobs logs <key> --level Error --output json \
     --output-filter '[].{Level:Level,TimeStamp:TimeStamp,Message:Message}' \
     | tee .local/investigations/raw/triage-job-logs.json
   ```
3. **Job history** — state transition timestamps (Pending → Running → Faulted). Useful for delays and lifecycle issues.
   ```
   uip or jobs history <key> --output json \
     --output-filter '[].{State:State,CreationTime:CreationTime,Reason:Reason}' \
     | tee .local/investigations/raw/triage-job-history.json
   ```
4. **Job traces** — execution traces (activity states, variable snapshots, execution path). Available for all job types.
   ```
   uip or jobs traces <key> --output json \
     | tee .local/investigations/raw/triage-job-traces.json
   ```
   Traces are dense; consider filtering by activity name or error attribute when re-fetching for hypothesis testing.

This is the baseline. Domain-specific data gathering builds on it — see the investigation guide for each matched domain (UI Automation, Integration Service, Maestro) for additional steps after the baseline.

## Queue Item Data Bundle

For every queue item under investigation, gather these in order. Write each to `raw/` immediately.

1. **Resolve queue** — `uip or queues list --folder-key <key> --name <name>` — find the queue definition and its key
2. **Queue item details** — `uip or queue-items get <item-key> --folder-key <key>` — status, SpecificContent, processingException, retry count
3. **Queue item history** — `uip or queue-items get-history <item-key> --folder-key <key>` — state transitions with timestamps (New → InProgress → Failed/Retried)
4. **Last retry** — `uip or queue-items get-last-retry <item-key> --folder-key <key>` — details of the most recent retry attempt

For comparison investigations (e.g., queue-items-failing playbook), also gather successful items:

5. **List failed items** — `uip or queue-items list --queue-definition-key <queue-key> --folder-key <key> --status Failed` — all failed items for comparison
6. **List successful items** — `uip or queue-items list --queue-definition-key <queue-key> --folder-key <key> --status Successful --limit 3` — sample of successful items to compare SpecificContent

## Finding Related Jobs

When investigating service tasks, child jobs, or multi-job processes, use `jobs list` with `--state` ALWAYS set when the user named a state in their prompt ("failed" → `--state Faulted`, "stuck" → `--state Pending`, etc.). Filter at the source:

```
uip or jobs list --folder-key <folder-key> --state Faulted \
  --process-name <name> \
  --created-after <start> --created-before <end> \
  --output json \
  --output-filter '[].{Key:Key,State:State,StartTime:StartTime,ReleaseName:ReleaseName}' \
  | tee .local/investigations/raw/triage-jobs-list.json
```

Key flags (all optional, but `--folder-key` or `--folder-path` is required):
- `--folder-key <key>` — folder GUID (required, or use `--folder-path`)
- `--state <state>` — filter by state: Pending, Running, Successful, Faulted, Stopped, Stopping, Suspended, Resumed, Terminating. **Required when the user named a state in their prompt** — never `jobs list` without a state filter when the prompt says "failed" / "stuck" / "cancelled", or you will fetch unrelated jobs and pick the wrong one.
- `--process-name <name>` — filter by process name (contains match)
- `--created-after <datetime>` / `--created-before <datetime>` — narrow to a time window (ISO 8601)

Use this to find child jobs spawned by Maestro service tasks, or to identify other faulted jobs for the same process around the same time.

## Testing Prerequisites

When testing hypotheses for Orchestrator issues, gather and verify these before drawing conclusions:

1. **Folder context** — confirm the folder the process runs in; permissions, jobs and assets are folder-scoped
2. **Process version** — confirm the deployed package version matches what the user expects
3. **Robot assignment** — verify the robot/machine template is assigned to the folder and has capacity
4. **Execution logs** — use job traces/logs to reconstruct the actual execution path, don't infer from job status alone
5. **Timing** — check job start/end times, queue transaction durations, and trigger schedules against reported symptoms
6. **Dependencies** — check `## Dependencies` in `overview.md` for cross-product issues (e.g., Identity Server, Elasticsearch, SQL Server)
