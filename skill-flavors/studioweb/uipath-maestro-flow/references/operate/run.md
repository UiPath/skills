<!--skill-flavor:run-preflight-steps:start-->
1. **Project saved.** `uip flow debug` runs the project as it is persisted: files written under `/solution/<ProjectName>/` are persisted; unsaved canvas edits the user made in the designer are not — ask them to save first.
2. **Validated.** Run `uip maestro flow validate /solution/<ProjectName>/new.flow --output json` first; debug is not a validation step.
3. **Tool timeout raised.** Call the shell tool with `timeoutSeconds: 600` — the host waits up to 5 minutes for a terminal state and prints only at exit.
<!--skill-flavor:run-preflight-steps:end-->

<!--skill-flavor:debug-run-body:start-->
> **Consent comes from the mandate.** `flow debug` executes the flow for real — sends emails, posts messages, calls APIs. Run it when the request is for a flow that works; ask when the request stops at build or validate. The mandate does not cover side effects that reach a third party (a real call, a message to someone who is not the user) — those need the run asked for explicitly. The target is always a project of the open solution; nothing is packed or uploaded. See rule #2 in [SKILL.md](../../SKILL.md).

```bash
uip flow debug                     # the active project
uip flow debug "<ProjectName>"     # another project of the open solution, by name
```

**The verb is the two-token `uip flow debug`.** `uip maestro flow debug` is not intercepted by the host and fails in the browser bundle (`… is not a constructor`). The positional is a project **name** in the open solution (defaults to the active project), not a directory path. Output is plain text, not JSON — `--output json` and `--output-filter` are ignored.

> **Run it in the foreground with `timeoutSeconds: 600`.** The host waits up to 5 minutes for a terminal state and prints only at exit.
> 1. If the tool times out before the host prints (it should not with `timeoutSeconds: 600` — the host gives up at 300 s), do not re-run debug: the run may still be going on the server. Ask the user to check the run in the designer; if a `Trace ID` was printed, use `uip maestro flow job status <TRACE_ID> --output json` instead.
> 2. **`TimedOut after 300s` together with `(no run logs emitted)` means the run never reached the runtime.** Do not retry in a loop — check that the project validates and has an End node, report it, and ask the user to run Debug from the designer's Debug button and paste the result (or a Trace ID) back.
> 3. Never start a second debug while the first is running — it executes the flow again.
> 4. Re-run debug only after you changed the flow.

> **Only `--inputs` is honoured.** The host accepts the project name and `-i` / `--inputs '<inline JSON>'`; `--folder-path`, `--folder-key`, `--attachment`, `--output`, `--timeout` and `@file` inputs are ignored or rejected. Debug runs in the user's own workspace — there is no folder to choose.
<!--skill-flavor:debug-run-body:end-->

<!--skill-flavor:debug-run-body-2:start-->
uip flow debug --inputs '{"numberA": 5, "numberB": 7}'
uip flow debug "<ProjectName>" --inputs '{"numberA": 5, "numberB": 7}'
<!--skill-flavor:debug-run-body-2:end-->

<!--skill-flavor:debug-run-body-3:start-->
**File-typed inputs cannot be bound from `uip flow debug` in Studio Web** — `--attachment` is ignored without warning. Tell the user, and test file inputs through a deployed process instead (see [Process run](#process-run--trigger-a-deployed-process)).
<!--skill-flavor:debug-run-body-3:end-->

<!--skill-flavor:debug-reporting-body:start-->
`uip flow debug` prints plain text: line 1 is the **status** (`Successful`, `Faulted`, `Failed`, `TimedOut after 300s`), then `Trace ID: <id>` when the host determined one, then `Run logs:` and `Execution trace:`. **Always show the status and the Trace ID as the first two lines of the summary:**

```text
Status: <status line>
Trace ID: <id>

<per-node outcome from Execution trace:, errors from Run logs:>
```

Write `Trace ID: <not returned>` when the line is absent rather than dropping it. Take the per-node outcome from `Execution trace:` (spans in execution order) and the error messages from `Run logs:`. The Trace ID is the job key for `uip maestro flow job status|traces <TRACE_ID>`. No URL is returned — the user is already in the designer.
<!--skill-flavor:debug-reporting-body:end-->

<!--skill-flavor:debug-fault-body:start-->
Exit code 1 and a first line of `Faulted`, `Failed` or `TimedOut after 300s` mean the run failed, and the cause is already in the same output — the error message and faulting node in `Run logs:`, the last non-successful span in `Execution trace:`. `TimedOut after 300s` with `(no run logs emitted)` means the run never reached the runtime: do not retry in a loop; report it and ask the user to run Debug from the designer's Debug button and paste the result (or a Trace ID) back. Capture the output once and read it from the file instead of re-running:

```bash
uip flow debug > /tmp/flow-debug.txt; echo "exit=$?"
```

Extraction commands and fault-marker lookup: [diagnose/troubleshooting-guide.md — Step 0](../diagnose/troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have).

See [shared/cli-commands.md — uip flow debug](../shared/cli-commands.md#uip-flow-debug) for the host's exact surface.
<!--skill-flavor:debug-fault-body:end-->

<!--skill-flavor:ship-orchestrator-path-pointer:start-->
For flows already deployed to Orchestrator:
<!--skill-flavor:ship-orchestrator-path-pointer:end-->

<!--skill-flavor:process-run-inputs-attachment:start-->
> **Pre-flight.** Confirm each `<variableId>` exists in the flow's `variables.globals[]` with `direction:"in"` and `type:"file"` — see [shared/cli-commands.md — Pre-flight](../shared/cli-commands.md#pre-flight---attachment-binding). On `process run` only: `--attachment` overrides `--inputs` on key collisions; `--validate` accepts pre-uploaded attachment references for file-typed slots (passes the JSON-schema check even though the slot's nominal type is `string`). `<localPath>` must be a file inside the iframe filesystem (`/solution/...` or `/tmp/...`); uploading it from the browser bundle is unverified — if the command rejects the attachment, report it and ask the user to start the process from Orchestrator.
<!--skill-flavor:process-run-inputs-attachment:end-->

<!--skill-flavor:job-inspection-commands:start-->

The `Trace ID` printed by `uip flow debug` is the job key. Only call `job status` / `job traces` with a real key — `job traces` on an unknown key hangs until the tool timeout — and give the shell call `timeoutSeconds: 120`.
<!--skill-flavor:job-inspection-commands:end-->

<!--skill-flavor:run-antipatterns:start-->
- **Never re-run a completed `flow debug` to re-read or reshape its output.** Each run executes the flow again for real (nothing is uploaded). Extract the report fields from the text the completed run already returned — see [Reporting debug runs](#reporting-debug-runs-to-the-user). For a faulted run, read the cause first — see [When the run faults](#when-the-run-faults).
- **Never run `uip solution resources refresh` in Studio Web.** It is unavailable (needs a local `.uipx`); the open solution's resources are managed live with `uip solution resources list|add|edit` or the designer's Resources panel.
<!--skill-flavor:run-antipatterns:end-->
