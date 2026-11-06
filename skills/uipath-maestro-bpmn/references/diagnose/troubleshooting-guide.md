# Troubleshooting Guide

Use this priority ladder for failed or misbehaving BPMN runs.

> **Read-only boundary:** this guide diagnoses. Retry, cancel, migrate, and cursor movement are Operate actions requiring explicit user consent after root cause is known.
>
> **Folder context:** `uip maestro bpmn instance ...` commands require `--folder-key <FOLDER_KEY>` or `-f <FOLDER_KEY>`; `uip maestro bpmn incident get` requires `--folder-key <FOLDER_KEY>`.

## Step 1 - Confirm context

Collect public-safe identifiers: process/package name, instance/job ID, folder/context label, approximate run time, local commit/package version if known, and whether the run came from `uip maestro bpmn debug` or `uip maestro bpmn process run`. Do not record secrets, tenant URLs, connection IDs, or payload data in public notes.

If only a deployed-process job key is available, run:

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
```

Parse JSON for instance ID, folder context, process key, final status, and trace/run identifiers.
<!--skill-flavor:debug-instance-source:start-->
For debug runs, prefer the `instanceId` returned by `uip maestro bpmn debug` and inspect it with `debug-instance` commands. Keep deployed-instance status reads separate from debug-session inspection.
<!--skill-flavor:debug-instance-source:end-->

## Step 2 - Read incidents

Find the incident category, message, and faulting BPMN element ID. For multiple incidents, start with the first root fault, not downstream cancellation noise. Run:

```bash
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn incident summary --output json
```

For a process-level overview, run:

```bash
uip maestro bpmn processes incidents <PROCESS_DEFINITION_KEY> --folder-key <FOLDER_KEY> --output json
```

`<PROCESS_DEFINITION_KEY>` is the bare process definition key, without the `:<processVersion>` suffix accepted by `process run`.

## Step 3 - Inspect runtime variables

Inspect variables around the faulting element and redact private payloads. Check for missing or malformed expected outputs and literal strings instead of evaluated expressions. For behavioral mismatches, inspect variables even when final status is `Completed`: completion proves control-flow completion, not semantic correctness.

```bash
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

Before changing source, confirm affected elements' runtime inputs and outputs match the modeled contract.

## Step 4 - Correlate deployed BPMN

When local source may differ, run:

```bash
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

For failed-run triage, always run this before final diagnosis, even when incidents and variables explain the failure. The deployed asset proves which BPMN definition actually ran and keeps the priority ladder observable in command logs. Compare deployed asset with local `.bpmn`: faulting element ID; root variables and mappings; binding expressions; Integration Service extension content; and diagram/sequence-flow structure for import or package failures. Locate the incident's faulting element in the deployed asset first. If definitions differ, diagnose what ran and treat local edits as a future fix.

## Step 5 - Inspect element executions and cursors

Run:

```bash
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Use these to distinguish modeling from runtime-state problems:

- Activity fault: inspect activity inputs, mappings, extension payload, and upstream variables.
- Gateway stall: inspect outgoing sequence-flow conditions, default flow, and variable values.
- Event wait: inspect message/timer configuration, subscriptions, and whether the expected external signal exists.
- Subprocess or call activity fault: identify the child dependency; do not invoke sibling skills automatically.

## Step 6 - Check generated package files

For binding, entry point, package, or runtime-metadata failures, inspect `bindings_v2.json`, `entry-points.json`, `operate.json`, and `package-descriptor.json`. Generated-file mismatches usually mean Author should fix BPMN or rerun CLI generation/enrichment. Correlate files to the deployed BPMN:

- `entry-points.json` should reference the intended BPMN file and start event.
- `bindings_v2.json` should contain generated resources required by executable resource and connector elements.
- `operate.json` should identify the intended main file/runtime metadata.
- `package-descriptor.json` should include BPMN and generated JSON files under `content/`.

## Step 7 - Pull traces last

Run verbose traces only when incidents, variables, deployed asset, and package files do not explain the issue:

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

## Output

Return a concise diagnosis containing:

- Faulting element ID.
- User-visible symptom.
- Likely root cause.
- Whether the fix belongs in BPMN source, CLI enrichment, generated package files, or cloud configuration.
- Safe next action: name the repair owner from the line above and the read-only command that shows the run's state before any Operate decision, e.g. "`<OWNER>` fixes `<ELEMENT_ID>`, then re-read
<!--skill-flavor:safe-next-read:start-->
  `uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json`" (for a debug run,
  `uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json`). Name the read; do not run it now. If no repair is needed, the read alone is the next
  action.
<!--skill-flavor:safe-next-read:end-->

Retry, cancel, pause, resume, migrate, cursor movement, debug, process run, upload, publish, and deploy are never the next action. If one may fit later, name it on its own line as an Operate decision outside this diagnosis. When the request says not to ask for approval, do not.

## CLI command reference

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

Lifecycle commands are intentionally absent from this diagnostic command list. Use [operate/manage.md](../operate/manage.md) only after diagnosis supports a side-effecting action and the user consents.