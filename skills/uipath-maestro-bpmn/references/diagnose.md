# Diagnose — why a BPMN run failed

Triage in order: context, incidents, runtime variables, deployed BPMN asset, element executions/cursors, generated package files, then traces. Use only the CLI verbs below; do not invent variants (`job get`, `incidents list`, `instance asset get --instance-id`, hyphenated forms).

> **Read-only boundary.** This guide diagnoses. Retry, cancel, pause, resume, migrate, and cursor movement are Operate actions ([operate.md](operate.md)) requiring the user's explicit decision after the root cause is known.
>
> **Folder context.** Every `uip maestro bpmn instance` subcommand and `incident get` requires `--folder-key <FOLDER_KEY>` or `-f <FOLDER_KEY>`. `processes incidents` accepts `--folder-key` only, not `-f`; without it the command is rejected before the API.
>
> **CLI interface.** Run each `uip maestro bpmn` read with `--output json`. In a test harness the `mocks/` and `fixtures/` directories are the CLI's backing data: do not read them by any means, including with `cat`, `head`, `grep`, `jq`, `sed`, or a file-read tool. You may capture CLI output to your own file and read it back.
>
> **One literal command per read, never a loop.** Write every read in full. No loop, function, alias or shell variable stands in for the verb, the id or the folder key. To batch, chain the literal reads in one Bash call, one per line.

## Step 1 — confirm context

Collect only public-safe identifiers: process/package name, job key, instance id, folder key, approximate run time, and whether the run came from `uip maestro bpmn debug` or a deployed `process run`. Do not record secrets, tenant URLs, connection ids, or payload data.

From a deployed job key, run and parse the instance id, folder, process key, and final status from JSON:

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
```

<!--skill-flavor:debug-handle:start-->
For a **debug** run, use the `instanceId` returned by the debug command as the handle and read it with `debug-instances` (see [uip version note](operate.md#debug--a-controlled-studio-web-run)); keep deployed-instance and debug-session reads separate.
<!--skill-flavor:debug-handle:end-->

## Step 2 — read incidents

Run:

```bash
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn incident summary --output json                      # across instances
uip maestro bpmn processes incidents <PROCESS_DEFINITION_KEY> --folder-key <FOLDER_KEY> --output json  # one process, all runs
```

Use the incident category, message, and **faulting BPMN element id**. For several incidents, start from the first root fault and ignore downstream cancellation noise. `<PROCESS_DEFINITION_KEY>` is the bare process definition key, without the `:<processVersion>` suffix accepted by `process run`.

## Step 3 — inspect runtime variables

Run both as applicable and redact private payloads:

```bash
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

Inspect values around the faulting element for missing/malformed output or a literal where an expression was intended. Inspect variables even for `Completed` runs with wrong results: completion proves control flow, not correctness.

## Step 4 — correlate the deployed BPMN

Fetch the deployed asset **before writing the diagnosis, every time**, even when incidents and variables explain the failure:

```bash
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Find the incident element id in the deployed asset first, then compare with the local `.bpmn.ts` and its compiled `.bpmn`: mappings, `=bindings.<id>` expressions, connector context rows, gateway conditions, and default. Diagnose what ran; treat local differences as future fixes. An edited but not re-uploaded process commonly causes "I fixed that already".

## Step 5 — element executions and cursors

Run:

```bash
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Interpret the stopped path:

- **Activity fault:** inputs, mappings, context rows, and upstream variables.
- **Gateway stall:** outgoing conditions, default flow, and gateway-time variables.
- **Event wait:** message/timer configuration, subscription, and whether the external signal arrived.
- **Sub-process or call fault:** inspect the child dependency; do not invoke sibling skills on its behalf.

## Step 6 — generated package files

For binding, entry-point, or package faults, correlate generated files with the deployed BPMN: `entry-points.json` names the BPMN file and start event (`/content/<Name>.bpmn#<start-id>`); `bindings_v2.json` holds executable and connector resources; `operate.json` names the main file and start event; and the `files` map in `package-descriptor.json` names each packaged file. Regenerate rather than edit them: run `uip maestro bpmn refresh <project-path> --output json`; `Data.WrittenFiles` identifies stale files. Fix the source when it is wrong.

## Step 7 — traces, last

Run only when incidents, variables, the deployed asset, and package files do not explain the failure:

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

Traces contain the whole timeline and rarely add more.

## Debug runs

A debug instance is ephemeral. Read it immediately in the same session; the debug command's output lists element status, never variable values.

<!--skill-flavor:debug-reads:start-->
```bash
uip maestro bpmn debug-instances incidents <INSTANCE_ID> --output json
uip maestro bpmn debug-instances variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instances variables-all <INSTANCE_ID> --output json
```
<!--skill-flavor:debug-reads:end-->

## The diagnosis

Report concisely:

- faulting BPMN element id;
- user-visible symptom;
- likely root cause;
- **who owns the fix**, using these labels even when a category is not implicated: `BPMN source` (the `.bpmn.ts`: structure, variables, mappings, conditions), `Generated package metadata` (the four files `refresh` writes), `Integration Service enrichment` (connector metadata, connection binding, dynamic schemas), `Cloud configuration` (folder, process, release, connection state on the tenant);
- the safe next action: owner and repair (source fix rebuilt through the validation loop, package refresh, or operator hand-off), followed by the one read-only command that shows run state before any Operate decision, for example "`BPMN source` fixes `<ELEMENT_ID>`, then re-read `uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json`". Name the read; do not run it now. For debug, use the `incidents` read under [Debug runs](#debug-runs). If no repair is needed, the read alone is the next action.

Retry, cancel, pause, resume, migrate, cursor movement, debug, process run, upload, publish and deploy are never the next action. If one may fit later, name it on its own line as an Operate decision outside the diagnosis. When the request says not to ask for approval, do not ask. Redact tenant, user, connection, folder, URL, payload, and secret values.

## Failure modes that reach the runtime

The builder catches some defects before execution: `compile` refuses unparsable XML, an element with no id, and a flow to nowhere. `check` reports undeclared `vars.<id>` reads as `EXPR_UNDECLARED_REF` (error), declared-variable reads without `vars.` as `EXPR_BARE_VAR_REF` (error), and gateways whose every flow is conditioned as `NO_DEFAULT_FLOW` (warning). `compile` writes these as authored, so a process compiled without clean `check` can carry them. A run reading undefined `vars.<id>` requires re-running `bpmn check --source` on authored source and fixing its report. This behavior is from the SDK release with UiPath/builder-sdk#1712; an older `compile` refuses the undeclared read itself. These are the ones that survive both:

- **Binding resolution:** A node reads `=bindings.<id>` but its resource is unreachable from the run's folder or absent from `bindings_v2.json`. Incident category: `BindingResolution`; element id: the node. Owner is `Cloud configuration` when the resource is in another folder or the connection is disabled; `Generated package metadata` when `refresh` was skipped after the source changed; `BPMN source` when `.binding()` names the wrong resource.
- **A folder binding keyed by the folder:** A `folderKey` binding whose `resourceKey` is the folder's own key fails connection resolution (`MISSING_BINDING` at validate; `BindingResolution` at runtime). The compiler keys it by the companion connection. If hand-edited, fix `.bpmn.ts` and rebuild through the validation loop.
- **Integration Service enrichment missing:** A connector reaches runtime with draft context, no connection binding, or stale dynamic schema. The incident points to the connector and variables show missing/malformed output. Owner: `Integration Service enrichment`; use the CLI enrichment path and `refresh`, never a hand-written connection id.
- **Stale generated package files:** `entry-points.json` names an old start event/file, `package-descriptor.json` omits current BPMN, or `bindings_v2.json` disagrees with BPMN references. Owner: `Generated package metadata`; run `refresh`. Deprecated `update-metadata` does not materialize `Intsvc.*` connection bindings; its package validates and faults at runtime.
- **Gateway takes the wrong branch or stalls:** Conditions are syntactically valid but semantically wrong, or the default points incorrectly. Read gateway variables and element executions before changing conditions. Owner: `BPMN source`.
- **Expression treated as literal:** A plain string was authored where an `=` expression was intended. Owner: `BPMN source`.
- **Script task faults or returns nothing:** `vars` is undefined in the script, or the output row reads the wrong return shape: a v3 script returns a bare value while the row reads `=result.response`; `return { response: … }` double-wraps. Owner: `BPMN source`. A brownfield script shape differing from `.scriptTask()` output is not itself a fault; propose a rewrite only when run evidence names that task, and show the user that evidence before editing.
- **Message or event wait never ends:** Message id, correlation reference, or subscription mismatches the caller; cursors show the token parked at the event. Owner: `BPMN source` for the reference, `Cloud configuration` for the missing signal.
- **Multi-instance loop faults on the first item:** Collection or item variable is undeclared where read. Owner: `BPMN source`.
- **Deployed asset differs from local:** Republish, branch switch, or local edit after deployment. Diagnose the deployed definition; local change is the future fix.
- **Stuck with no incident:** Message/timer wait, gateway conditions never true, or external dependency. Cursors and element executions locate it; cursor movement is an Operate action.

## Anti-patterns

- **Never start with traces** when incidents are available.
- **Never run a lifecycle command while diagnosing** — retry, cancel, migrate, and cursor movement mutate.
- **Never assume the local BPMN is the deployed asset.**
- **Never retry before the root cause is known.**
- **Never paste private incident payloads or connection details** into notes, commits, or issues.
- **Never patch generated package files as the only fix for a source defect** — fix `.bpmn.ts`, rebuild through the validation loop, and `refresh`.

## Command reference

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn job traces <JOB_KEY> --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn incident summary --output json
uip maestro bpmn processes incidents <PROCESS_DEFINITION_KEY> --folder-key <FOLDER_KEY> --output json
```

<!--skill-flavor:debug-reference:start-->
```bash
uip maestro bpmn debug-instances incidents <INSTANCE_ID> --output json
uip maestro bpmn debug-instances variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instances variables-all <INSTANCE_ID> --output json
```
<!--skill-flavor:debug-reference:end-->

Lifecycle commands are deliberately absent; they are in [operate.md](operate.md), for after diagnosis and the user's decision.
