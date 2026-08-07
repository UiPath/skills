# Troubleshooting Failed Cases

Diagnostic workflow for failed debug runs and deployed case process runs. All commands require `uip login`.

> **`--folder-key` is required for `incident get`.** Most `instance` subcommands accept `--folder-key <FOLDER_KEY>` and auto-detect from the authenticated folder if omitted, but `incident get` requires it explicitly. Get the folder key from `uip or folders list --output json` or from the job/process context.

Use this guide only after a debug or deployed Case run fails. One troubleshooting round contains at most one pass through Steps 1–5. Stop the pass as soon as the cause is confirmed; later rounds must add evidence or apply a different targeted fix, never repeat an identical command or unconfirmed edit.

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

> **No instance ID after `job status` succeeds, or `job status` still fails after its permitted transient retry →** end the round and report the job key; downstream steps need the instance ID.

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

Use the incident's faulting element ID and the variable state to locate the failure point in `caseplan.json`. Map the element ID to the corresponding stage or task, check its `data.inputs[]`, the entry/exit conditions that route into it, and the variable values flowing into it.

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

## Classify and act

After the pass, classify the result exactly once:

1. **Caseplan-fixable** — a confirmed wrong binding, condition, expression, or input value. Read only the plugin that owns the confirmed fault, apply a targeted fix, then run `uip maestro case validate <caseplan.json> --output json`. If Phase 5 had published the build and the fix changed it, re-enter the complete [Phase 5 publish contract](phased-execution.md#phase-5--publish) before Phase 6; otherwise re-enter the consent-gated [Phase 6 debug path](phased-execution.md#phase-6--debug). Never bypass either gate or debug before the Phase 5 choice.
2. **External-resource** — a missing/expired connection, unregistered task type, missing asset, or permission problem. Do not edit Case artifacts. Report the exact resource and remediation, then AskUserQuestion: `Resource fixed, return to Phase 6` / `Abort`. On `Resource fixed`, re-enter the Phase 6 debug path so `uip solution resources refresh` runs before debug.
3. **Inconclusive** — no confirmed actionable cause. Do not edit. Start another round only with a new evidence path; if none remains, use the escalation below immediately.

### Inline API workflow incident `170007`

Incident `170007` with "job's associated process could not be found" on an inline-built API-workflow sibling is expected under `case debug`: debug does not provision that sibling. Do not spend another troubleshooting round or edit `caseplan.json`. Runtime verification requires a full solution deploy (`uip solution pack` → `uip solution publish` → `uip solution deploy run`), which installs in Orchestrator. AskUserQuestion: `Run full solution deploy` / `Skip (mark debug-unverifiable)`. Never deploy without that explicit consent; if skipped, report the task as debug-unverifiable.

## Round limits and escalation

- Run at most three progressive diagnose/fix/debug rounds for one failed run. A round that applies a fix must validate before the debug rerun.
- In Steps 2–5, empty data advances to the next step. Retry a transient auth/network failure once; after a second failure, record it and advance. A second Step-1 failure instead ends the round and reports the job key because later steps require an instance ID.
- Ten minutes is an advisory per-round debug limit. If exceeded, record the round as inconclusive; do not hard-kill the subprocess or start another debug while it remains active. Wait for it to exit or for the user to resolve the live run before continuing.
- After round three, regardless of its mix of inconclusive and post-fix failures, end this failed-run loop and AskUserQuestion: `Provide context for a later run` / `Pause for manual investigation` / `Abort`. Report the instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, and what changed or was learned in each round. Never run a fourth debug round in this loop or propose a `caseplan.json` edit without a confirmed cause; a later debug attempt requires fresh user consent.

## CLI command reference

For full flag tables and all subcommands, see [case-commands.md](case-commands.md):

- `uip maestro case instance` — list/get/incidents/variables/asset/cursors/element-executions and lifecycle (pause/resume/cancel/retry/migrate/goto)
- `uip maestro case incident` — `summary`, `get`
- `uip maestro case processes incidents <PROCESS_KEY>` — all incidents on a process
- `uip maestro case job` — `status`, `traces`

Append `--output json` to any command whose output you parse.
