# Diagnose — Investigate failed or misbehaving flow runs

<!--skill-flavor:single-nested-intro:start-->
Capability index for postmortem on a failed `flow debug` or deployed process run. Diagnose owns the diagnostic priority ladder (incidents → runtime variables → flow correlation → traces) and recurring failure modes (missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, single-nested layout). Requires `uip login`.
<!--skill-flavor:single-nested-intro:end-->

> **Navigation.** Diagnose follows Operate when a run faults and points to Author for the fix. Re-running and lifecycle are in [operate/CAPABILITY.md](../operate/CAPABILITY.md); building or editing `.flow` files is in [author/CAPABILITY.md](../author/CAPABILITY.md).
>
> **Inherited rules:** use `--output json` and prefer `--output-filter` for extraction; do not run `flow debug` without consent; never invoke other skills automatically; use the dropdown question pattern; provide plain-English narration and a granular progress list only when the user asks for verbosity, and remain silent by default. These rules apply in addition to the rules below.

## When to use this capability

- Triage a failed `flow debug` or deployed process run.
- Read incidents for the error category, message, and faulting element.
- Inspect runtime variables at failure time.
- Map a faulting element ID to a `.flow` node.
- Stream verbose execution traces.
- Recognize known failures, including missing `=js:` and format skips.

## Critical rules

0. **Read the faulted `flow debug` response before any other call — never re-run debug to "see the error again".** See [troubleshooting-guide.md — Step 0](troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have).
1. **Investigate in order: incidents → variables → flow correlation → traces.** Stop when the root cause is identified; traces are verbose and last-resort. See [troubleshooting-guide.md](troubleshooting-guide.md).
2. **Always include `--folder-key <FOLDER_KEY>` (`-f` shorthand) on `instance` and `incident get` commands.** Run `uip or folders list --output json` to obtain the folder key, or obtain it from the job/process context. See [shared/cli-conventions.md](../shared/cli-conventions.md#6---folder-key-requirement).
3. **Never call underlying APIs directly.** Run supported `uip` CLI commands; `instance` and `incident` are the diagnostic surface.
4. **When the local `.flow` may differ from the deployed BPMN, fetch the deployed asset.** Run `uip maestro flow instance asset <INSTANCE_ID> --folder-key <FOLDER_KEY> --output json` and correlate against what actually ran.

## Workflow

| Journey | Read |
| --- | --- |
| Triage a failed run (priority ladder) | [troubleshooting-guide.md](troubleshooting-guide.md) |
| Look up a known failure mode | [failure-modes.md](failure-modes.md) |

## Common tasks

| Need | Read |
| --- | --- |
| Triage a failed flow run | [troubleshooting-guide.md](troubleshooting-guide.md) |
| An in-solution chat agent shows as autonomous | The registry builds that node from the sibling project's `agent.json` and falls back to autonomous when it cannot read it. `--log-level debug` names the reason ("Unparseable agent.json" / "No readable agent.json"); nothing else reports it. See [conversational-agent/impl.md](../author/plugins/conversational-agent/impl.md#resolve-the-agent) |
| A chat flow "hangs" or times out during debug | Not a fault. `flow debug` hands a `core.trigger.conversation` flow off rather than running it, and a flow parked on `wait-for-message` is waiting for a user message that no headless run will send. Drive it from a chat UI — Studio Web or the UiPath Maestro VS Code extension. See [conversational-agent/impl.md](../author/plugins/conversational-agent/impl.md#debug--the-cli-hands-off) |
| Read the cause out of a faulted `flow debug` response | [troubleshooting-guide.md — Step 0](troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have) |
| Find the error message and faulting element | [troubleshooting-guide.md — Step 2 Fetch incidents](troubleshooting-guide.md#step-2--fetch-incidents) |
| See data state at failure time | [troubleshooting-guide.md — Step 3 Fetch runtime variable state](troubleshooting-guide.md#step-3--fetch-runtime-variable-state) |
| Map a faulting element ID to a `.flow` node | [troubleshooting-guide.md — Step 4 Correlate with the flow definition](troubleshooting-guide.md#step-4--correlate-with-the-flow-definition) |
| Pull verbose execution timeline | [troubleshooting-guide.md — Step 5 Traces](troubleshooting-guide.md#step-5--traces-last-resort) |
| Identify a `vars.X.output.Y` literal-string failure | [failure-modes.md — `=js:` prefix missing](failure-modes.md#js-prefix-missing) |
| Identify misshapen Studio Web nodes | [failure-modes.md — misshapen nodes](failure-modes.md#misshapen-rectangle-nodes-in-studio-web) |
| Diagnose a hung HITL node | [failure-modes.md — HITL `completed` port unwired](failure-modes.md#hitl-completed-port-unwired) |
| Diagnose a connector silent fault | [failure-modes.md — Reused reference ID](failure-modes.md#reused-reference-id--cross-connection-id-leakage) |
<!--skill-flavor:single-nested-task-row:start-->
| Diagnose a publish/upload structural error | [failure-modes.md — Single-nested layout](failure-modes.md#single-nested-layout) |
<!--skill-flavor:single-nested-task-row:end-->
| Diagnose `Folder does not exist` on a resource node | [failure-modes.md — Missing `bindings[]` on resource node](failure-modes.md#missing-bindings-on-resource-node) |
| Triage "validate passes, debug faults" | [failure-modes.md — `flow validate` passes, `flow debug` faults](failure-modes.md#flow-validate-passes-flow-debug-faults) |
| Look up `instance` / `incident` CLI syntax | [shared/cli-commands.md](../shared/cli-commands.md) + [troubleshooting-guide.md — CLI command reference](troubleshooting-guide.md#cli-command-reference) |

## Anti-patterns

- **Do not start with traces.** Start with incidents (Step 2), then variables, flow correlation, and traces only if needed.
- **Do not call underlying APIs directly.** Run `uip maestro flow instance` / `incident` / `job` subcommands.
- **Do not assume the local `.flow` matches the deployed BPMN.** If a republish, branch, or solution-version difference is possible, run `instance asset` before correlating IDs.
- **Do not omit `--folder-key`** from `instance` or `incident get`; the command rejects the request before reaching the API.

## References

### Diagnose-scoped

- [troubleshooting-guide.md](troubleshooting-guide.md) — diagnostic priority ladder (incidents → variables → flow correlation → traces) and full `instance` / `incident` CLI reference
<!--skill-flavor:single-nested-reference-entry:start-->
- [failure-modes.md](failure-modes.md) — recurring failures: missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, single-nested layout, and "validate passes / debug faults"
<!--skill-flavor:single-nested-reference-entry:end-->

### Cross-capability (shared)

- [shared/cli-commands.md](../shared/cli-commands.md) — flat CLI lookup including `instance` / `incident` / `job` subcommands
- [shared/cli-conventions.md](../shared/cli-conventions.md) — `--folder-key` requirement, login state, JSON output shape
- [shared/file-format.md](../shared/file-format.md) — correlate faulting element IDs to `.flow` nodes
- [shared/node-output-wiring.md](../shared/node-output-wiring.md) — referenced from the `=js:` prefix-missing failure mode