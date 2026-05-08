# Troubleshooting Failed Flows

Diagnostic workflow for failed debug runs and deployed process runs. All commands require `uip login`.

> **`--folder-key` is required.** All `instance` and `incident get` commands require `--folder-key <FOLDER_KEY>`. Get the folder key from `uip or folders list --output json` or from the job/process context.

## Suggested initial todos

Pre-populate these via `TodoWrite` when entering this journey. The list mirrors the priority ladder — **leave unchecked rungs in place even if root cause is found early; they document where you stopped.** See [shared/ux-narration-and-todos.md](../../shared/ux-narration-and-todos.md) for granularity, narration cadence, and pivot rules.

- [ ] Resolve instance ID and folder key
- [ ] Fetch incidents for the failed run
- [ ] Identify error category, message, and faulting element
- [ ] Inspect runtime variable state at failure
- [ ] Correlate faulting element ID to a node in the `.flow` file
- [ ] Pull traces (only if previous steps insufficient)
- [ ] Classify root cause (known failure mode? new pattern?)
- [ ] Recommend next action via `AskUserQuestion` — **Re-author the flow** / **Retry the instance** / **Cancel the instance** / **Escalate** / **Something else** (see the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md))

## Diagnostic priority

Investigate in this order — each step adds context, stop when you have enough to diagnose the root cause:

1. Incidents (error message + faulting element)
2. Runtime variables (data state at failure)
3. Flow definition correlation (map element to `.flow` node)
4. Traces (last resort — verbose full timeline)

## Step 1 — Get the instance ID

The debug output (`Data.instanceId`) or `job status` response contains the instance ID. If you only have a job key:

```bash
uip maestro flow job status <JOB_KEY> --output json
```

Parse the instance ID and folder key from the response.

## Step 2 — Fetch incidents

Failed flows always have an incident. Start here — incidents give you the error category, message, and the faulting element.

```bash
uip maestro flow instance incidents <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Drill into a specific incident for full detail:

```bash
uip maestro flow incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
```

To get a cross-process incident overview:

```bash
uip maestro flow incident summary --output json
```

## Step 3 — Fetch runtime variable state

Get the variable values at the time of failure to understand what data each node was working with:

```bash
uip maestro flow instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Scope to a specific element (node or subflow):

```bash
uip maestro flow instance variables <INSTANCE_ID> --folder-key <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

## Step 4 — Correlate with the flow definition

Use the incident's faulting element ID and the variable state to locate the failure point in the `.flow` file. Map the element ID to the corresponding node, check its `inputs`, upstream edges, and the variable values flowing into it.

If the local `.flow` file may differ from what was deployed, fetch the deployed BPMN definition:

```bash
uip maestro flow instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json
```

Additional instance inspection commands:

```bash
uip maestro flow instance element-executions <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json  # per-element execution details
uip maestro flow instance cursors <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json             # current execution cursor positions
```

## Step 5 — Traces (last resort)

Traces are verbose but contain the full execution timeline. Use them only when incidents and variables are insufficient:

```bash
uip maestro flow job traces <JOB_KEY> --output json
```

> **Always use CLI commands for troubleshooting — never call the underlying APIs directly.**

## CLI command reference

### uip maestro flow instance

Inspect and manage Flow process instances. **Requires `uip login`.** All subcommands require `--folder-key <FOLDER_KEY>` (`-f` shorthand).

```bash
uip maestro flow instance list --output json                                                        # list all instances
uip maestro flow instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json                           # get instance details
uip maestro flow instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get incidents for a failed instance
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json                     # get runtime variable values
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json  # scope to a specific element
uip maestro flow instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json            # get per-element execution details
uip maestro flow instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json                         # get the deployed BPMN definition
uip maestro flow instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json                       # get current execution cursor positions
```

> **Lifecycle commands** (`pause` / `resume` / `cancel` / `retry`) are operate concerns — see the [Operate manage guide](../../operate/references/manage.md).

### uip maestro flow incident

Get incident details for failed flows. **Requires `uip login`.**

```bash
uip maestro flow incident summary --output json                                    # get incident summaries across all processes
uip maestro flow incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json # get full details for a specific incident
```

Use `instance incidents <INSTANCE_ID>` to get incidents scoped to a specific run, then `incident get <INCIDENT_ID>` for full detail on a specific incident.
