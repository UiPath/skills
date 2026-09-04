# Run — Execute a Flow

Execute a flow on demand and monitor progress. Three modes: **debug** (controlled re-run with full Studio Web visibility), **process run** (trigger a deployed process), **job inspection** (status and traces). All require `uip login`.

## Pre-flight

1. **Logged in.** `uip login status --output json` returns success. See [shared/cli-conventions.md — Login state](../shared/cli-conventions.md#5-login-state).
2. **For debug runs: solution resources refreshed.** Always run before `flow debug` so connection and process resource declarations are in sync with project bindings:

   ```bash
   uip solution resources refresh --solution-folder <SolutionDir> --output json
   ```

## Debug — controlled end-to-end run

> **Confirm consent first.** `flow debug` executes the flow for real — sends emails, posts messages, calls APIs. See the consent-before-debug rule in [SKILL.md](../../SKILL.md). Do not run without explicit user authorization.

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution dir, or `.` if already inside the project dir.

> **Never run `flow debug` in the background.** It takes 1 to 5 minutes and prints its JSON only at exit.
> 1. Run it in the foreground with a tool timeout of at least 10 minutes (most agent shells kill a command after 1 to 2 minutes).
> 2. If the tool returns "still running", poll that same process until it exits. Do not read the output file yet — empty means still running.
> 3. If stdout ends with `Debug polling timed out after <N>s`, the flow is still running on the server. Take the `instanceId` from stderr and run `uip maestro flow debug-instance status <INSTANCE_ID> --output json`.
> 4. Never start a second debug while the first is running — it uploads and executes the flow again.
> 5. Re-run debug only after you changed the flow.

> **Do not pass `--folder-path` or `--folder-key` to `flow debug`.** Debug provisions into your personal workspace. A shared or team folder fails with `HTTP 500` at `Stage: prepare-custom-debug` and no instance starts. Shared resources the flow uses (indexes, buckets, connections) reach the run through `uip solution resources refresh`, not through the debug folder. Use the flag only when your account has no personal workspace or the flow needs folder-scoped assets or queues that exist only in that folder.

Pass input arguments when the flow has input parameters:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --inputs '{"numberA": 5, "numberB": 7}'
```

Build those inputs from real records, never from invented values — an invented key matches no record, every lookup returns `[]`, and the run faults on empty data. Read the entity `Id` from `uip df entities list --output json`, then a live record from `uip df records list <ENTITY_ID> --output json`.

Bind local files to file-typed input variables with `--attachment <variableId>=<localPath>` (repeatable). `<variableId>` (left of `=`) must match the `id` of a `variables.globals[]` entry with `direction:"in"` and `type:"file"`:

```bash
# Replace <variableId> and <localPath> placeholders below with your own values.
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json \
  --attachment <variableId>=<localPath> \
  --attachment <variableId>=<localPath>
```

> **Pre-flight.** Confirm each `<variableId>` exists in the flow's `variables.globals[]` with `direction:"in"` and `type:"file"`. See [shared/cli-commands.md — Pre-flight](../shared/cli-commands.md#pre-flight---attachment-binding).

> **Reading the bound file.** At runtime a `file` variable is an object — a Script node reads the uploaded name via `$vars.{triggerNodeId}.output.{id}.FullName`. See [shared/variables-and-expressions.md — Runtime shape of a `file` variable](../shared/variables-and-expressions.md#file-input).

### Reporting debug runs to the user

The CLI response includes a **Studio Web URL** (where the user inspects the run) and an **instanceId** (for log/trace correlation). Parse both from the JSON output — typically `Data.studioWebUrl` and `Data.instanceId` — and **always show them as the first two lines of the summary**:

```text
Studio Web URL: <url>
Instance ID: <instanceId>

<run status, node traces, errors, etc.>
```

If either value is missing from the response, emit the label with `<not returned by CLI>` rather than dropping the line. Do not bury these values below the run summary — the user should see them immediately without scrolling.

### When the run faults

`Data.finalStatus: "Faulted"` means the run failed, and the cause is already in that same response — read it there. Redirect stdout to a file and extract the cause from the file; on a faulted run the CLI ignores `--output-filter` and prints the whole envelope, so the filter is not a way to shrink it:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <path-to-project-dir> --output json > /tmp/flow-debug.json
```

Extraction commands and fault-code lookup: [diagnose/troubleshooting-guide.md — Step 0](../diagnose/troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have).

See [shared/cli-commands.md — uip maestro flow debug](../shared/cli-commands.md#uip-maestro-flow-debug) for additional options.

## Process run — trigger a deployed process

<!--skill-flavor:ship-orchestrator-path-pointer:start-->
For flows already deployed to Orchestrator (via [ship.md](ship.md) → Orchestrator path):
<!--skill-flavor:ship-orchestrator-path-pointer:end-->

```bash
uip maestro flow process list --output json                           # discover deployed processes
uip maestro flow process run <process-key> <folder-key> --output json # trigger a run
```

Pass input arguments and/or bind file-typed input variables:

```bash
# Replace <variableId> and <localPath> placeholders below with your own values.
uip maestro flow process run <process-key> <folder-key> --output json \
  --inputs '{"numberA": 5, "numberB": 7}' \
  --attachment <variableId>=<localPath>
```

> **Pre-flight.** Confirm each `<variableId>` exists in the flow's `variables.globals[]` with `direction:"in"` and `type:"file"` — see [shared/cli-commands.md — Pre-flight](../shared/cli-commands.md#pre-flight---attachment-binding). On `process run` only: `--attachment` overrides `--inputs` on key collisions; `--validate` accepts pre-uploaded attachment references for file-typed slots (passes the JSON-schema check even though the slot's nominal type is `string`).

Run `uip maestro flow process --help` for all subcommands and options.

## Job inspection — status and traces

```bash
uip maestro flow job status <job-key> --output json   # check status of a running or completed job
uip maestro flow job traces <job-key> --output json   # stream the verbose execution timeline
```

> **Traces are verbose** and contain the full execution timeline. Use them only when needed for diagnosis — start from incidents first via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md).

## What's next

- **Run failed?** Triage via [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) — start with incidents, escalate to traces only if needed.
- **Need to intervene in a running instance** (pause, resume, cancel, retry)? See [manage.md](manage.md).

## Anti-patterns

- **Never run `flow debug` as a validation step.** Use `uip maestro flow validate` for correctness checking; debug is for end-to-end execution.
- **Never re-run a completed `flow debug` to re-read or reshape its output.** Each run re-uploads the solution and executes the flow again for real. Extract the report fields from the payload the completed run already returned — see [Reporting debug runs](#reporting-debug-runs-to-the-user). For a faulted run, read the cause first — see [When the run faults](#when-the-run-faults).
- **Never skip `solution resources refresh` before debug.** Stale resource declarations cause runtime binding failures even when the local `.flow` is correct.
- **Never start diagnosis from `job traces`.** Traces are last-resort — see [diagnose/CAPABILITY.md](../diagnose/CAPABILITY.md) for the priority ladder.
