# Run — Execute a Flow

Execute a flow on demand in three modes: **debug** (controlled re-run with Studio Web visibility), **process run** (trigger a deployed process), and **job inspection** (status and traces). All require `uip login`.

## Pre-flight

1. Run `uip login status --output json` and confirm success. See [shared/cli-conventions.md — Login state](../shared/cli-conventions.md#5-login-state).
2. Before every debug run, run:

   ```bash
   uip solution resources refresh --solution-folder <SolutionDir> --output json
   ```

This synchronizes connection and process resource declarations with project bindings.

## Debug — controlled end-to-end run

> **Confirm consent first.** `flow debug` executes the flow for real—it sends emails, posts messages, and calls APIs. See the consent-before-debug rule in [SKILL.md](../../SKILL.md). Do not run without explicit user authorization.

Run:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
```

Use the directory containing `project.uiproj`: `<ProjectName>/` from the solution directory, or `.` when already inside it.

Pass inputs with:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```

Bind file inputs with repeatable `--attachment <variableId>=<localPath>`:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --attachment <variableId>=<localPath> \
  --attachment <variableId>=<localPath>
```

Before binding, confirm each `<variableId>` exists in `variables.globals[]` with `direction:"in"` and `type:"file"`. See [shared/cli-commands.md — Pre-flight](../shared/cli-commands.md#pre-flight---attachment-binding).

At runtime, a `file` variable is an object. A Script node reads the uploaded name via `$vars.{triggerNodeId}.output.{id}.FullName`. See [shared/variables-and-expressions.md — Runtime shape of a `file` variable](../shared/variables-and-expressions.md#file-input).

### Reporting debug runs to the user

Parse the CLI JSON response for the Studio Web URL and instance ID, typically `Data.studioWebUrl` and `Data.instanceId`. Always make these the first two summary lines:

```text
Studio Web URL: <url>
Instance ID: <instanceId>

<run status, node traces, errors, etc.>
```

If either value is missing, emit its label with `<not returned by CLI>`; never omit or bury these lines. See [shared/cli-commands.md — uip maestro flow debug](../shared/cli-commands.md#uip-maestro-flow-debug).

## Process run — trigger a deployed process

<!--skill-flavor:ship-orchestrator-path-pointer:start-->
For flows already deployed to Orchestrator (via [ship.md](ship.md) → Orchestrator path):
<!--skill-flavor:ship-orchestrator-path-pointer:end-->

Run:

```bash
uip maestro flow process list --output json
uip maestro flow process run <process-key> <folder-key> --output json
```

Pass inputs and/or bind file inputs:

```bash
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5, "numberB": 7}' \
  --attachment <variableId>=<localPath>
```

Before binding, confirm each `<variableId>` exists in the flow's `variables.globals[]` with `direction:"in"` and `type:"file"`. See [shared/cli-commands.md — Pre-flight](../shared/cli-commands.md#pre-flight---attachment-binding). On `process run` only, `--attachment` overrides `--inputs` on key collisions; `--validate` accepts pre-uploaded attachment references for file-typed slots and passes the JSON-schema check even though the slot's nominal type is `string`.

Run `uip maestro flow process --help` for all subcommands and options.

## Job inspection — status and traces

Run:

```bash
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

Traces are verbose and contain the full execution timeline. Use them only when needed for diagnosis; start from incidents via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).

## What's next

- **Run failed?** Triage via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md), starting with incidents and escalating to traces only if needed.
- **Need to intervene in a running instance** (pause, resume, cancel, retry)? See [manage.md](manage.md).

## Anti-patterns

- **Never run `flow debug` as validation.** Run `uip maestro flow validate` for correctness checking; debug is for end-to-end execution.
- **Never skip `solution resources refresh` before debug.** Stale resource declarations can cause runtime binding failures even when the local `.flow` is correct.
- **Never start diagnosis from `job traces`.** Traces are last-resort; follow the priority ladder in [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).