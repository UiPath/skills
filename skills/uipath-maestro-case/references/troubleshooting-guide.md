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

## Step 3 — Fetch runtime variable state

Get the variable values at the time of failure to understand what data each stage/task was working with:

```bash
uip maestro case instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Scope to a specific element (stage or task):

```bash
uip maestro case instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

## Step 4 — Correlate with the case definition

Use the incident's faulting element ID and the variable state to locate the failure point in `caseplan.json`. Map the element ID to the corresponding stage, task, edges etc., check its `data.inputs[]`, upstream edges, and the variable values flowing into it.

If the local `caseplan.json` may differ from what was deployed, fetch the deployed case definition:

```bash
uip maestro case instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

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

## CLI command reference

### uip maestro case instance

Inspect and manage Case process instances. **Requires `uip login`.** Most subcommands accept `--folder-key <FOLDER_KEY>` (`-f` shorthand) and auto-detect the folder when omitted.

```bash
uip maestro case instance list --output json                                                        # list all instances
uip maestro case instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json                           # get instance details
uip maestro case instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get incidents for a failed instance
uip maestro case instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get runtime variable values
uip maestro case instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json  # scope to a specific element
uip maestro case instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json            # get per-element execution details
uip maestro case instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # get the deployed Case JSON definition
uip maestro case instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json                       # get current execution cursor positions
```

Instance lifecycle commands:

```bash
uip maestro case instance pause <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # pause a running instance
uip maestro case instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json                        # resume a paused instance
uip maestro case instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json                        # cancel an instance
uip maestro case instance retry <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # retry a faulted instance
uip maestro case instance migrate <INSTANCE_ID> <NEW_VERSION> -f <FOLDER_KEY> --output json         # migrate to a new package version
uip maestro case instance goto <INSTANCE_ID> '[{"sourceElementId":"A","targetElementId":"B"}]' -f <FOLDER_KEY> --output json  # move execution cursor
```

### uip maestro case incident

Get incident details for failed cases. **Requires `uip login`.**

```bash
uip maestro case incident summary --output json                                     # get incident summaries across all processes
uip maestro case incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json # get full details for a specific incident
```

Use `instance incidents <INSTANCE_ID>` to get incidents scoped to a specific run, then `incident get <INCIDENT_ID>` for full detail on a specific incident. Use `processes incidents <PROCESS_KEY>` for all incidents on a process across all runs.

### uip maestro case job

Monitor case jobs. **Requires `uip login`.**

```bash
uip maestro case job status <JOB_KEY> --output json                                 # get job status (parse instanceId, folderKey)
uip maestro case job status <JOB_KEY> --detailed --output json                      # full response with all fields
uip maestro case job traces <JOB_KEY> --output json                                 # stream raw execution traces
uip maestro case job traces <JOB_KEY> --pretty                                      # human-readable trace output
uip maestro case job traces <JOB_KEY> --poll-interval 5000                          # adjust poll interval (ms)
```
