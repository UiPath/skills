# Diagnose — why a BPMN run failed

Triage in priority order. Each step is cheaper and more specific than the next,
and starting at the wrong end is how a diagnosis turns into twenty tool calls —
or into twenty guesses at a command shape. The commands below are the CLI's
exact verbs; do not invent variants (`job get`, `incidents list`,
`instance asset get --instance-id`, hyphenated forms) — every one of those is
rejected, and the mocked harness answers them with an error too.

1. **Context** — the job, its instance, the folder.
2. **Incidents** on the instance — the faulting element id and category.
3. **Runtime variables** at the point of failure.
4. **The deployed BPMN asset** — what actually ran, not what is on disk.
5. **Element executions and cursors** — where the token went before it stopped.
6. **Generated package files** — when the failure is a binding, entry point or package fault.
7. **Traces**, last.

> **Read-only boundary.** This guide diagnoses. Retry, cancel, pause, resume,
> migrate and cursor movement are Operate actions ([operate.md](operate.md)) and
> need the user's explicit decision after the root cause is known.
>
> **Folder context.** Every `uip maestro bpmn instance` subcommand and
> `incident get` require `--folder-key <FOLDER_KEY>` or `-f <FOLDER_KEY>`; without
> it the command is rejected before it reaches the API.
>
> **The CLI is the diagnostic interface.** Read with the `uip maestro bpmn` commands below, always with `--output json`.
> In a test harness the `mocks/` and `fixtures/` directories are the CLI's backing
> data: do not read them by any means — no `cat`, `head`, `grep`, `jq`, `sed`, and
> no file-read tool. Capturing a CLI response to your own file and reading that
> back is fine; it is the CLI's own output.

## Step 1 — confirm context

Collect the public-safe identifiers: process or package name, job key, instance
id, folder key, approximate run time, and whether the run came from
`uip maestro bpmn debug` or a deployed `process run`. Do not record secrets,
tenant URLs, connection ids or payload data in notes.

From a deployed job key, start here and parse the instance id, folder, process
key and final status from the JSON:

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
```

For a **debug** run, the `instanceId` the debug command returned is the handle,
and the `debug-instance` commands read it (see below). Keep deployed-instance
reads and debug-session reads separate.

## Step 2 — read incidents

The incident carries the category, the message and the **faulting BPMN element
id**. With several incidents, start from the first root fault and ignore the
downstream cancellation noise.

```bash
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn incident summary --output json                      # across instances
uip maestro bpmn processes incidents <PROCESS_KEY> --output json     # one process, all runs
```

## Step 3 — inspect runtime variables

Inspect the variables around the faulting element, redacting private payloads.
Look for an expected output that is missing, malformed, or a literal string
where an evaluated expression was meant. Inspect variables even on a
`Completed` run when the user reports a wrong result: completion proves the
control flow finished, not that the values are right.

```bash
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

## Step 4 — correlate the deployed BPMN

Fetch the deployed asset **before writing the diagnosis, every time**, even when
incidents and variables already explain the failure. It proves which definition
ran, and it is where the faulting element id is looked up.

```bash
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Find the incident's element id in the deployed asset first, then compare with
the local `.bpmn.ts` and its compiled `.bpmn`: the element's mappings, its
binding expressions (`=bindings.<id>`), the connector's context rows, the
gateway's conditions and default. When they differ, diagnose what actually ran
and treat the local edit as a future fix, not as the executed definition. A
process edited but not re-uploaded is the most common explanation for "I fixed
that already".

## Step 5 — element executions and cursors

Where the runtime moved before it faulted or stalled:

```bash
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

- **Activity fault** — its inputs, mappings, context rows and upstream variables.
- **Gateway stall** — the outgoing conditions, the default flow, the variable values at the gateway.
- **Event wait** — the message or timer configuration, the subscription, whether the external signal ever arrived.
- **Sub-process or call fault** — the child dependency; do not invoke sibling skills on its behalf.

## Step 6 — generated package files

For a binding, entry-point or package fault, correlate the four generated files
with the deployed BPMN: `entry-points.json` names the BPMN file and the start
event (`/content/<Name>.bpmn#<start-id>`), `bindings_v2.json` holds the
resources the executable and connector elements need, `operate.json` names the
main file, `package-descriptor.json` lists everything under `content/`. These
are derived: regenerate them with `uip maestro bpmn refresh <project-path>
--output json` (`Data.WrittenFiles` names what was stale) rather than editing
them, and fix the source when the source is wrong.

## Step 7 — traces, last

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

Only when incidents, variables, the deployed asset and the package files do not
explain the failure. Traces are the whole timeline and rarely say more.

## Debug runs

A debug instance is ephemeral; read it in the same session, right after the run,
with the debug-instance commands. The debug command's own output lists each
element's status, never a variable's value.

```bash
uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables-all <INSTANCE_ID> --output json
```

## The diagnosis

Report, concisely:

- the faulting BPMN element id;
- the user-visible symptom;
- the likely root cause;
- **who owns the fix**, using these labels even when a category is not implicated:
  `BPMN source` (the `.bpmn.ts` — structure, variables, mappings, conditions),
  `Generated package metadata` (the four files `refresh` writes),
  `Integration Service enrichment` (connector metadata, connection binding, dynamic schemas),
  `Cloud configuration` (folder, process, release, connection state on the tenant);
- the safe next action — a read, a source fix and recompile, a package refresh, an
  operator hand-off — never a lifecycle mutation the user has not decided on.

Redact tenant, user, connection, folder, URL, payload and secret values.

## Failure modes that reach the runtime

The builder removes a class of BPMN defects at compile time — unparsable XML, an
element with no id, a flow to nowhere, a `vars.<id>` read of an undeclared
variable, a gateway with every flow conditioned (`NO_DEFAULT_FLOW`) — so a
compiled process does not carry them. These are the ones that survive:

- **Binding resolution** — a node reads `=bindings.<id>` and the resource the
  binding names is not reachable from the folder the process ran in, or the
  generated `bindings_v2.json` lacks the resource. Incident category
  `BindingResolution`, element id = the node. Owner: `Cloud configuration` when
  the resource exists in another folder or the connection is disabled;
  `Generated package metadata` when `refresh` was skipped after the source
  changed; `BPMN source` when the `.binding()` names the wrong resource.
- **A folder binding keyed by the folder.** A `folderKey` binding whose
  `resourceKey` is the folder's own key fails to resolve the connection
  (`MISSING_BINDING` at validate; a `BindingResolution` incident at run time).
  The compiler keys it by the companion connection; if the artifact was
  hand-edited, recompile.
- **Integration Service enrichment missing** — the connector node reached the
  runtime with draft context, no connection binding, or a stale dynamic schema.
  The incident points at the connector node; runtime variables show missing or
  malformed output. Owner: `Integration Service enrichment`; the fix is the
  CLI's enrichment path and `refresh`, never a hand-written connection id.
- **Stale generated package files** — `entry-points.json` names an old start
  event or file, `package-descriptor.json` omits the current BPMN,
  `bindings_v2.json` does not match the binding references in the BPMN. Owner:
  `Generated package metadata`; run `refresh`. The deprecated `update-metadata`
  does not materialize `Intsvc.*` connection bindings — a package it wrote
  validates and faults at run time.
- **Gateway takes the wrong branch or stalls** — the conditions are fine
  syntactically and wrong semantically, or the default flow points where the
  author did not mean. Read the variables at the gateway and the element
  executions before touching the conditions. Owner: `BPMN source`.
- **Expression treated as literal** — a field authored as a plain string where
  an `=` expression was meant, so the runtime saw the text. Owner: `BPMN source`.
- **Script task faults or returns nothing** — `vars` undefined inside the
  script, or a return the output row does not read: a v3 script returns a bare
  value and the row reads `=result.response`; `return { response: … }`
  double-wraps. Owner: `BPMN source`.
- **Message or event wait that never ends** — the message id, the correlation
  reference or the subscription does not match what the caller sends; cursors
  show the token parked at the event. Owner: `BPMN source` for the reference,
  `Cloud configuration` for the missing signal.
- **Multi-instance loop faults on the first item** — the collection or item
  variable is not declared where the loop reads it. Owner: `BPMN source`.
- **Deployed asset differs from local** — a republish, a branch switch or a
  local edit after deployment. Diagnose the deployed definition; the local
  change is the future fix.
- **Stuck with no incident** — a message or timer wait, a gateway whose
  conditions never evaluate true, an external dependency. Cursors and element
  executions show where; cursor movement is an Operate action.

## Anti-patterns

- **Never start with traces** when incidents are available.
- **Never run a lifecycle command while diagnosing** — retry, cancel, migrate and cursor movement mutate.
- **Never assume the local BPMN is the deployed asset.**
- **Never retry before the root cause is known.**
- **Never paste private incident payloads or connection details** into notes, commits or issues.
- **Never patch the generated package files as the only fix for a source defect** — fix the `.bpmn.ts`, recompile, `refresh`.

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
uip maestro bpmn processes incidents <PROCESS_KEY> --output json
uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables-all <INSTANCE_ID> --output json
```

Lifecycle commands are deliberately absent from this list; they are in
[operate.md](operate.md), for after the diagnosis and the user's decision.
