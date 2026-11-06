# Run - Debug, process run, and status inspection

Use this journey to debug or run a BPMN Process Orchestration project and inspect execution status. Debug and deployed runs are side-effecting; status, incidents, variables, and deployed-asset reads are inspection operations.

## Consent gate

Before any debug or process run:

- Explain that execution can call connectors, start child processes, create human tasks, mutate queues, send messages, or update external systems.
- Confirm input arguments and target folder/context.
- Confirm the project passed validation and required CLI-owned enrichment.
- Ask for explicit consent for this run. Upload, validation, or packaging consent does not authorize execution.

## Debug - controlled Studio Web run

<!--skill-flavor:debug-intro:start-->
Use debug when the user wants to upload a local BPMN project to Studio Web and run a debug session with full Studio Web visibility.
<!--skill-flavor:debug-intro:end-->

<!--skill-flavor:local-debug-solution:start-->
For local debug, prefer a solution context so generated resources, bindings, and debug metadata are available. Initialize a solution, import the BPMN project, refresh resources, and run debug from the solution directory:

```bash
uip solution init <SolutionName> --output json
cd <SolutionName>
uip solution projects import <path-to-ProjectDir> --output json
uip solution resources refresh --output json
uip maestro bpmn debug <ProjectDirName> --output json
```

`<path-to-ProjectDir>` is relative to `<SolutionName>` (`../MyProject`) or absolute.
<!--skill-flavor:local-debug-solution:end-->

<!--skill-flavor:debug-command-usage:start-->
Run:

```bash
uip maestro bpmn debug [project-path] --output json
```

After confirming inputs, pass arguments with secrets redacted from summaries:

```bash
uip maestro bpmn debug [project-path] --inputs @inputs.json --output json
```

When needed, provide the CLI-exposed folder ID:

```bash
uip maestro bpmn debug [project-path] --folder-id <FOLDER_ID> --output json
```

Parse and report returned `Data.jobKey`, `Data.instanceId`, `Data.runId`, `Data.solutionId`, and `Data.finalStatus`. If no Studio Web URL is returned, print `Studio Web URL: <not returned by CLI>`.

**Debug output contains element statuses, not variable values:** `Completed`/`Faulted` element statuses and a completed final status with green elements prove execution, not expected output-variable values. To inspect runtime definitions and exposed values, run `uip maestro bpmn debug-instance variables-all <INSTANCE_ID> --output json` with the returned instance ID immediately in the same ephemeral debug session. Match keys case-insensitively (`finalStatus`/`FinalStatus`, `instanceId`/`InstanceId`, `elementExecutions`/`ElementExecutions`) because JSON key casing varies by CLI version.
<!--skill-flavor:debug-command-usage:end-->

## Process run - deployed process

Run a process only when it is already deployed to Orchestrator:

```bash
uip maestro bpmn process list --folder-key <FOLDER_KEY> --output json
uip maestro bpmn process get <PROCESS_KEY> --feed-id <FEED_ID> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn process run <PROCESS_KEY> --folder-key <FOLDER_KEY> --release-key <RELEASE_KEY> --inputs @inputs.json --output json
```

`get` requires `--feed-id`; `run` requires `--release-key`. Take `<FOLDER_KEY>` from the user or the `Key` of `uip or folders list --output json`. From `process list`, take `<RELEASE_KEY>` (`releaseKey`) and `<FEED_ID>` (`feedId`); `<PROCESS_KEY>` is `<processKey>:<processVersion>`, for example `MyProcess:1.0.0`. Add `--feed-id` or `--robot-ids` to `process run` only when the user provides them or they are needed.

## Job and instance inspection

Start with status, then inspect incidents and variables when status is faulted or ambiguous:

```bash
uip maestro bpmn job status <JOB_KEY> --folder-key <FOLDER_KEY> --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Pull traces only when status, incidents, variables, and deployed BPMN correlation are insufficient:

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

<!--skill-flavor:debug-instance-inspection:start-->
For debug instances, prefer `debug-instance` commands when standard deployed-instance commands lack debug-session context; use identifiers returned by the debug command as the source of truth:

```bash
uip maestro bpmn debug-instance incidents <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables <INSTANCE_ID> --output json
uip maestro bpmn debug-instance variables-all <INSTANCE_ID> --output json
```
<!--skill-flavor:debug-instance-inspection:end-->

## Execution summary

When a run starts, report the returned Studio Web URL; process key, job key, run ID, solution ID, or instance ID; known folder/context; a secrets-redacted input summary; final status if the command waited; and the next inspection command or status path.

When the user cares about a business result, final status is insufficient: report the relevant output-variable definition and any API-returned value. Current BPMN live debug may expose a root output definition while returning its computed root output as `null`; call out that runtime/debug API limitation when observed.

## Status and traces

Start with status and incidents before verbose traces; pull traces only when incidents and variables are insufficient. If execution faults, hand off to [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).

## Anti-patterns

- **Never run `uip maestro bpmn debug` as validation.** Use Author validation and packaging checks; debug executes the process.
- **Never reuse stale inputs silently.** Confirm every side-effecting run's input set and redact secrets from summaries.
- **Never skip folder context for deployed runs.** `process list`, `get`, and `run` require `--folder-key`; instance inspection requires `--folder-key` or `-f`.
- **Never start diagnosis from traces.** Check incidents, variables, the deployed BPMN asset, and element executions first.