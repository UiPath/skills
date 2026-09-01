# Diagnose — Investigate failed or misbehaving flow runs

<!--skill-flavor:single-nested-intro:start-->
Capability index for postmortem on a failed `flow debug` or deployed process run. Diagnose owns the diagnostic priority ladder (incidents → runtime variables → flow correlation → traces) and the catalog of known recurring failure modes (missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, single-nested layout). Requires `uip login`.
<!--skill-flavor:single-nested-intro:end-->

> **Where you came from / where to go next.** Diagnose is downstream of Operate (run faulted → diagnose) and points back to Author for the underlying fix (diagnose → re-author → re-ship). Re-running and lifecycle live in [operate/CAPABILITY.md](../operate/CAPABILITY.md); building/editing the `.flow` file lives in [author/CAPABILITY.md](../author/CAPABILITY.md).
>
> **Inherits universal rules from [SKILL.md](../../SKILL.md)** — `--output json` + prefer `--output-filter` for extraction, no `flow debug` without consent, never invoke other skills automatically, dropdown question pattern, **plain-English narration + granular progress list (opt-in — silent by default; engage when the user asks for verbosity)**. The rules below are diagnose-scoped and apply on top.

## When to use this capability

- Triage a failed `flow debug` or deployed process run
- Read incidents to identify the error category, message, and faulting element
- Inspect runtime variable state at the time of failure
- Map a faulting element ID back to a node in the `.flow` file
- Stream verbose traces for execution timeline
- Recognize known failure modes (missing `=js:` prefix, `flow format` skipped, etc.)

## Critical rules

1. **Investigate in priority order — incidents → variables → flow correlation → traces.** Each step adds context; stop when you have enough to identify the root cause. Skipping ahead to traces is the most common mistake — they are verbose and last-resort. See [troubleshooting-guide.md](troubleshooting-guide.md).
2. **Always include `--folder-key <FOLDER_KEY>` (`-f` shorthand) on `instance` and `incident get` commands.** Without it the command rejects the request before reaching the API. Get the folder key from `uip or folders list --output json` or from the job/process context. See [shared/cli-conventions.md](../shared/cli-conventions.md#6---folder-key-requirement).
3. **Never call the underlying APIs directly — always use `uip` CLI commands.** The `instance` and `incident` subcommands are the supported diagnostic surface; direct API calls are not.
4. **When the local `.flow` may differ from the deployed BPMN, fetch the deployed asset.** Use `uip maestro flow instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json` to see what actually ran. Do not assume your local file matches.

## Workflow

| Journey | Read |
| --- | --- |
| Triage a failed run (priority ladder) | [troubleshooting-guide.md](troubleshooting-guide.md) |
| Look up a known failure mode | [failure-modes.md](failure-modes.md) |

## Common tasks

| I need to... | Read these |
| --- | --- |
| **Triage a failed flow run** | [troubleshooting-guide.md](troubleshooting-guide.md) |
| **Find the error message and faulting element** | [troubleshooting-guide.md — Step 2 Fetch incidents](troubleshooting-guide.md#step-2--fetch-incidents) |
| **See data state at the time of failure** | [troubleshooting-guide.md — Step 3 Fetch runtime variable state](troubleshooting-guide.md#step-3--fetch-runtime-variable-state) |
| **Map a faulting element ID to a `.flow` node** | [troubleshooting-guide.md — Step 4 Correlate with the flow definition](troubleshooting-guide.md#step-4--correlate-with-the-flow-definition) |
| **Pull verbose execution timeline** | [troubleshooting-guide.md — Step 5 Traces](troubleshooting-guide.md#step-5--traces-last-resort) |
| **Identify a `vars.X.output.Y` literal-string failure** | [failure-modes.md — `=js:` prefix missing](failure-modes.md#js-prefix-missing) |
| **Identify misshapen Studio Web nodes** | [failure-modes.md — Misshapen nodes](failure-modes.md#misshapen-rectangle-nodes-in-studio-web) |
| **Diagnose a hung HITL node** | [failure-modes.md — HITL `completed` port unwired](failure-modes.md#hitl-completed-port-unwired) |
| **Diagnose a connector silent fault** | [failure-modes.md — Reused reference ID](failure-modes.md#reused-reference-id--cross-connection-id-leakage) |
<!--skill-flavor:single-nested-task-row:start-->
| **Diagnose a publish/upload structural error** | [failure-modes.md — Single-nested layout](failure-modes.md#single-nested-layout) |
<!--skill-flavor:single-nested-task-row:end-->
| **Diagnose `Folder does not exist` on a resource node** | [failure-modes.md — Missing `bindings[]` on resource node](failure-modes.md#missing-bindings-on-resource-node) |
| **Triage "validate passes, debug faults"** | [failure-modes.md — `flow validate` passes, `flow debug` faults](failure-modes.md#flow-validate-passes-flow-debug-faults) |
| **Look up `instance` / `incident` CLI syntax** | [shared/cli-commands.md](../shared/cli-commands.md) + [troubleshooting-guide.md — CLI command reference](troubleshooting-guide.md#cli-command-reference) |

## Anti-patterns

- **Never start with traces.** They are verbose and contain the full execution timeline — useful only when incidents and variables are insufficient. Start with incidents (Step 2 of the priority ladder).
- **Never call the underlying APIs directly.** Always use `uip maestro flow instance` / `incident` / `job` subcommands. Direct API calls bypass the supported diagnostic surface.
- **Never assume the local `.flow` matches the deployed BPMN.** If there's any chance the deployed flow differs (a republish since the local edit, a different branch, a different solution version), fetch `instance asset` to see what actually ran. Otherwise your correlation between faulting element and `.flow` node will mislead you.
- **Never skip the `--folder-key` flag** on `instance` or `incident get` commands. The command rejects the request before reaching the API; the failure looks like a CLI error but is really a missing argument.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](troubleshooting-guide.md) — diagnostic priority ladder (incidents → variables → flow correlation → traces) and full `instance` / `incident` CLI reference
<!--skill-flavor:single-nested-reference-entry:start-->
- [failure-modes.md](failure-modes.md) — pattern catalog for known recurring failures: missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, single-nested layout, "validate passes / debug faults"
<!--skill-flavor:single-nested-reference-entry:end-->

### Cross-capability (shared)

- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `instance` / `incident` / `job` subcommands
- [shared/cli-conventions.md](../shared/cli-conventions.md) — `--folder-key` requirement, login state, JSON output shape
- [shared/file-format.md](../shared/file-format.md) — to correlate faulting element IDs back to `.flow` nodes
- [shared/node-output-wiring.md](../shared/node-output-wiring.md) — referenced from the missing-`=js:` failure mode
