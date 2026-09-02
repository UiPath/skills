# Troubleshooting Failed Flows

Diagnostic workflow for failed debug runs and deployed process runs. All commands require `uip login`.

> **`--folder-key` is required.** All `instance` and `incident get` commands require `--folder-key <FOLDER_KEY>`. Get the folder key from `uip or folders list --output json` or from the job/process context.

## Diagnostic priority

Investigate in this order — each step adds context, stop when you have enough to diagnose the root cause:

0. The failed `flow debug` response you already have (incident + fault detail, no extra call)
1. Incidents (error message + faulting element)
2. Runtime variables (data state at failure)
3. Flow definition correlation (map element to `.flow` node)
4. Traces (last resort — verbose full timeline)

## Step 0 — Read the cause in the debug output you already have

A faulted `uip maestro flow debug` response already carries the incident and the fault detail. **Do not re-run `flow debug` before you read them.** An unchanged re-run re-uploads the solution and repeats the same fault against real systems.

The response can exceed 200,000 characters. `"Result": "Failure"` and the numeric `ErrorCode` sit in the first 1,000 characters; the cause sits tens of thousands of characters deeper. Reading the head of the output and stopping tells you that the run failed, not why. A faulted run is a fault, never an "incomplete" run.

Two fields hold the cause:

| Field | JSON path |
|---|---|
| Fault code + faulting element | `Data.incidents[].dependentFaultCode`, `.elementId`, `.errorCode`, `.errorDetails` |
| Fault detail (the real message) | `Data.variables.elements[].outputs.Error.detail`, `.code` |

### For a fresh run — project them with `--output-filter`

`--output-filter` applies JMESPath to the `Data` envelope before printing (write expressions starting at `Data`, no `Data.` prefix). It collapses the response to the reporting fields plus the cause, so the fault never scrolls past you:

```bash
uip maestro flow debug <PROJECT_DIR> --output json --output-filter '{studioWebUrl: studioWebUrl, instanceId: instanceId, jobKey: jobKey, finalStatus: finalStatus, incidents: incidents[].{elementId: elementId, errorCode: errorCode, fault: dependentFaultCode, details: errorDetails}, faults: variables.elements[?outputs.Error].{elementId: elementId, code: outputs.Error.code, detail: outputs.Error.detail}}'
```

`studioWebUrl` and `instanceId` are kept because [operate/run.md — Reporting debug runs](../operate/run.md#reporting-debug-runs-to-the-user) requires both in the summary.

### For a response already saved to a file

Logs go to stderr and JSON to stdout, so redirect stdout to keep the full response:

```bash
uip maestro flow debug <PROJECT_DIR> --output json > debug.json
```

Extract both fields:

```bash
jq -r '.Data.incidents[] | "\(.elementId) \(.errorCode) \(.dependentFaultCode) \(.errorDetails)"' debug.json
jq -r '.Data.variables.elements[] | select(.outputs.Error) | "\(.elementId) \(.outputs.Error.code) \(.outputs.Error.detail)"' debug.json
```

Without `jq`:

```bash
python3 - debug.json <<'EOF'
import json, sys
data = json.load(open(sys.argv[1]))["Data"]
for incident in data.get("incidents", []):
    print(incident["elementId"], incident["errorCode"], incident["dependentFaultCode"], incident["errorDetails"])
for element in data["variables"]["elements"]:
    error = element.get("outputs", {}).get("Error")
    if error:
        print(element["elementId"], error["code"], error["detail"])
EOF
```

### Match the fault code

Match `dependentFaultCode` to a known cause:

| `dependentFaultCode` | Cause and fix |
|---|---|
| `AGENT_STARTUP.INPUT_VALIDATION_ERROR` | Declared `type` does not match the bound node's real output shape — the runtime strict-validates agent inputs. `detail` names the failing key and the real type (for example `input_type=list`). See [author/plugins/inline-agent/impl.md](../author/plugins/inline-agent/impl.md). |

No match, or `detail` is not enough → continue with Step 1.

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

> **Lifecycle commands** (`pause` / `resume` / `cancel` / `retry`) are operate concerns — see the [Operate manage guide](../operate/manage.md).

### uip maestro flow incident

Get incident details for failed flows. **Requires `uip login`.**

```bash
uip maestro flow incident summary --output json                                    # get incident summaries across all processes
uip maestro flow incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json # get full details for a specific incident
```

Use `instance incidents <INSTANCE_ID>` to get incidents scoped to a specific run, then `incident get <INCIDENT_ID>` for full detail on a specific incident.
