# Troubleshooting Guide

Use this priority ladder for failed or misbehaving BPMN runs.

> **Read-only boundary:** this guide diagnoses.
> Retry, cancel, migrate, and cursor movement are Operate actions and require explicit user consent after root cause is known.
>
> **Folder context:** `uip maestro bpmn instance ...` commands require `--folder-key <FOLDER_KEY>` or
> `-f <FOLDER_KEY>`.
> `uip maestro bpmn incident get` requires `--folder-key <FOLDER_KEY>`.

## Step 1 - Confirm context

Collect public-safe identifiers:

- Process or package name.
- Instance/job ID.
- Folder/context label.
- Approximate run time.
- Local commit or package version, if known.
- Whether the run came from `uip maestro bpmn debug` or `uip maestro bpmn process run`.

Do not record secrets, tenant URLs, connection IDs, or payload data in public notes.

If you only have a deployed-process job key, start with:

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
```

Parse the instance ID, folder context, process key, final status, and any trace/run identifiers from the JSON output.
For debug runs, prefer the `instanceId` returned by
`uip maestro bpmn debug` and inspect it with `debug-instance` commands. Keep
deployed-instance status reads and debug-session inspection separate.

## Step 2 - Read incidents

Find the incident category, message, and faulting BPMN element ID.
If multiple incidents exist, start with the first root fault and avoid chasing downstream cancellation noise.

```bash
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn incident get <INCIDENT_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn incident summary --output json
```

For process-level incident overview:

```bash
uip maestro bpmn processes incidents <PROCESS_KEY> --output json
```

## Step 3 - Inspect runtime variables

Inspect variables around the faulting element.
Redact private payloads.
Check whether expected outputs were missing, malformed, or literal strings instead of evaluated expressions.
If the user reports a behavioral mismatch, inspect variables even when the final
run status is `Completed`; a completed run only proves control-flow completion,
not semantic correctness.

```bash
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance variables <INSTANCE_ID> -f <FOLDER_KEY> --parent-element-id <ELEMENT_ID> --output json
```

For affected elements, confirm runtime inputs and outputs match the modeled
contract before changing source.

## Step 4 - Correlate deployed BPMN

Fetch the deployed BPMN asset when local source may differ. Compare:

- Faulting element ID.
- Root variables and mappings.
- Binding expressions.
- Integration Service extension content.
- Diagram and sequence-flow structure when the failure is import or package related.

```bash
uip maestro bpmn instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Use the incident's faulting element ID to locate the BPMN element in the deployed asset first, then compare to local
`.bpmn`.
If they differ, diagnose what actually ran and treat local edits as a future fix, not as the executed definition.

## Step 5 - Inspect element executions and cursors

Element executions and cursors show where the runtime moved before it faulted or hung:

```bash
uip maestro bpmn instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Use these to distinguish a modeling problem from a runtime-state problem:

- Activity fault: inspect the activity's inputs, mappings, extension payload, and upstream variables.
- Gateway stall: inspect outgoing sequence-flow conditions, default flow, and variable values.
- Event wait: inspect message/timer configuration, subscriptions, and whether the expected external signal exists.
- Subprocess or call activity fault: identify the child dependency, but do not invoke sibling skills automatically.

## Step 6 - Check generated package files

If the failure is binding, entry point, package, or runtime metadata related, inspect generated JSON:

- `bindings_v2.json`
- `entry-points.json`
- `operate.json`
- `package-descriptor.json`

Generated-file mismatch usually means Author should fix BPMN or rerun CLI generation/enrichment.

Correlate package files to the deployed BPMN:

- `entry-points.json` should reference the intended BPMN file and start event.
- `bindings_v2.json` should contain generated resources required by executable resource and connector elements.
- `operate.json` should identify the intended main file/runtime metadata.
- `package-descriptor.json` should include BPMN and generated JSON files under `content/`.

## Step 7 - Pull traces last

Use verbose traces only when incidents, variables, deployed asset, and package files do not explain the issue.

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

## Output

Return a concise diagnosis:

- Faulting element ID.
- User-visible symptom.
- Likely root cause.
- Whether the fix belongs in BPMN source, CLI enrichment, generated package files, or cloud configuration.
- Safe next action.

## CLI command reference

```bash
uip maestro bpmn job status <JOB_KEY> --output json
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
```

Lifecycle commands are intentionally absent from this diagnostic command list.
Use [operate/references/manage.md](../../operate/references/manage.md) only after the diagnosis supports a
side-effecting action and the user consents.
