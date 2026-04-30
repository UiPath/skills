# Troubleshooting Failed Cases

Diagnostic workflow for failed debug runs and deployed case process runs. All commands require `uip login`.

> **`--folder-key` is required for `incident get`.** Most `instance` subcommands accept `--folder-key <FOLDER_KEY>` and auto-detect from the authenticated folder if omitted, but `incident get` requires it explicitly. Get the folder key from `uip orchestrator folder list --output json` or from the job/process context.

## Diagnostic priority

Investigate in this order — each step adds context, stop when you have enough to diagnose the root cause:

1. Incidents (error message + faulting element)
2. Runtime variables (data state at failure)
3. Case definition correlation (map element to `caseplan.json` node)
4. Traces (last resort — verbose full timeline)

## Step 1 — Get the instance ID

The debug output (`Data.instanceId`) or `job status` response contains the instance ID. If you only have a job key:

```bash
uip maestro case job status <JOB_KEY> --output json
```

Parse the instance ID and folder key from the response.

> **No instance ID / `job status` fails →** halt. Report job key to user; downstream steps need the instance ID.

## Step 2 — Fetch incidents

Failed cases always have an incident. Start here — incidents give you the error category, message, and the faulting element.

```bash
uip maestro case instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Drill into a specific incident for full detail:

```bash
uip maestro case incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
```

To get a cross-process incident overview:

```bash
uip maestro case incident summary --output json
```

For all incidents on a specific case process:

```bash
uip maestro case processes incidents <PROCESS_KEY> --folder-key <FOLDER_KEY> --output json
```

> **Empty incidents →** skip to Step 3. **Invalid instance ID error →** recheck Step 1 output.

## Step 3 — Fetch runtime variable state

Get the variable values at the time of failure to understand what data each stage/task was working with:

```bash
uip maestro case instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Scope to a specific element (stage or task):

```bash
uip maestro case instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

> **Empty variables →** skip to Step 4.

## Step 4 — Correlate with the case definition

Use the incident's faulting element ID and the variable state to locate the failure point in `caseplan.json`. Map the element ID to the corresponding stage, task, edges etc., check its `data.inputs[]`, upstream edges, and the variable values flowing into it.

If the local `caseplan.json` may differ from what was deployed, fetch the deployed case definition:

```bash
uip maestro case instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

> **`instance asset` fails →** fall back to local `caseplan.json`.

Additional instance inspection commands:

```bash
uip maestro case instance element-executions <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json  # per-element execution details
uip maestro case instance cursors <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json             # current execution cursor positions
```

## Step 5 — Traces (last resort)

Traces are verbose but contain the full execution timeline. Use them only when incidents and variables are insufficient:

```bash
uip maestro case job traces <JOB_KEY> --output json
uip maestro case job traces <JOB_KEY> --pretty                  # human-readable form
```

> **Always use CLI commands for troubleshooting — never call the underlying APIs directly.**

## Stop conditions

1. **Stop early on root cause.** Once a step yields actionable cause (error + faulting element + variable state), stop. Skip remaining steps.
2. **Empty result → next step.** If a step returns empty/missing data, move to the next step. Do not retry the same command.
3. **One retry on transient failure** (auth, network). Second failure: halt that step, continue.
4. **Max one full pass through Steps 1–5.** No looping.
5. **Escalate to user** if Steps 1–5 yield no root cause, or all paths blocked. Report: instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot. Do not propose `caseplan.json` edits without confirmed cause.

## CLI command reference

For full flag tables and all subcommands, see [case-commands.md](case-commands.md):

- `uip maestro case instance` — list/get/incidents/variables/asset/cursors/element-executions and lifecycle (pause/resume/cancel/retry/migrate/goto)
- `uip maestro case incident` — `summary`, `get`
- `uip maestro case processes incidents <PROCESS_KEY>` — all incidents on a process
- `uip maestro case job` — `status`, `traces`

Append `--output json` to any command whose output you parse.
