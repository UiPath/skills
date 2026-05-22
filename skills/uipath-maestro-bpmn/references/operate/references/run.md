# Run - Debug, process run, and status inspection

Use this journey to debug or run a BPMN Process Orchestration project and inspect execution status.
Debug and deployed process runs are side-effecting operations.
Status, incidents, variables, and deployed-asset reads are inspection operations.

## Consent gate

Before any debug or process run:

- Explain that execution can call connectors, start child processes, create human tasks, mutate queues, send messages,
  or update external systems.
- Confirm input arguments and target folder/context.
- Confirm the project has passed validation and required CLI-owned enrichment.
- Ask for explicit consent for this run. Prior consent for upload, validation, or packaging is not consent to execute.

## Debug - controlled Studio Web run

Use debug when the user wants to upload a local BPMN project to Studio Web and run a debug session with full Studio Web
visibility.

```bash
uip maestro bpmn debug [project-path] --output json
```

Pass input arguments only after confirming the values and redacting secrets from summaries:

```bash
uip maestro bpmn debug [project-path] --inputs @inputs.json --output json
```

If a target folder is needed, provide the folder ID exposed by the CLI:

```bash
uip maestro bpmn debug [project-path] --folder-id <FOLDER_ID> --output json
```

Parse and report returned identifiers such as `Data.jobKey`, `Data.instanceId`, `Data.runId`, `Data.solutionId`,
and `Data.finalStatus`.
If Studio Web URL is not returned, print `Studio Web URL: <not returned by CLI>`.

## Process run - deployed process

Use process run only for a process already deployed to Orchestrator.

```bash
uip maestro bpmn process list --output json
uip maestro bpmn process get <PROCESS_KEY> <FEED_ID> --output json
uip maestro bpmn process run <PROCESS_KEY> <FOLDER_KEY> --inputs @inputs.json --validate --output json
```

`process run` requires the folder key as a positional argument.
Use `--release-key`, `--feed-id`, or `--robot-ids` only when the user provides those deployment-specific choices
or the process discovery output clearly identifies them.

## Job and instance inspection

Use status first, then incidents and variables if the status is faulted or ambiguous:

```bash
uip maestro bpmn job status <JOB_KEY> --output json
uip maestro bpmn instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro bpmn instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
```

Use traces only when status, incidents, variables, and deployed BPMN correlation are insufficient:

```bash
uip maestro bpmn job traces <JOB_KEY> --output json
```

## Execution summary

When a run starts, report:

- Studio Web URL, if returned.
- Process key, job key, run ID, solution ID, or instance ID, if returned.
- Folder/context, if known.
- Input summary, with secrets redacted.
- Final status if the command waited for completion.
- Next inspection command or status path.

When the user cares about a business result, final status alone is insufficient.
Also report the relevant output variable or the reason it could not be
inspected.

## Status and traces

Start with status and incidents before verbose traces.
Traces can be large and should be pulled only when incidents and variables are insufficient.

If execution faults, hand off to [diagnose/CAPABILITY.md](../../diagnose/CAPABILITY.md).

## Anti-patterns

- **Never run `uip maestro bpmn debug` as validation.** Use Author validation and packaging checks for correctness;
  debug executes the process.
- **Never reuse stale inputs silently.** Confirm every side-effecting run's input set and redact secrets from summaries.
- **Never skip folder context for deployed runs.** `process run` requires `<FOLDER_KEY>` and instance inspection commands
  require `--folder-key` or `-f`.
- **Never start diagnosis from traces.** Use incidents, variables, deployed BPMN asset, and element executions first.
