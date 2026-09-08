<!--skill-flavor:single-nested-intro:start-->
Capability index for postmortem on a failed `flow debug` or deployed process run. Diagnose owns the diagnostic priority ladder (incidents → runtime variables → flow correlation → traces) and the catalog of known recurring failure modes (missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs).
<!--skill-flavor:single-nested-intro:end-->

<!--skill-flavor:diagnose-inherited-rules:start-->
> **Navigation.** Diagnose follows Operate when a run faults and points to Author for the fix. Re-running and lifecycle are in [operate/CAPABILITY.md](../operate/CAPABILITY.md); building or editing `.flow` files is in [author/CAPABILITY.md](../author/CAPABILITY.md).
>
> **Inherited rules:** use `--output json` and prefer `--output-filter` for extraction (bundle commands only — `uip flow debug` returns plain text); do not run `flow debug` without consent; never invoke other skills automatically; use the dropdown question pattern; provide plain-English narration and a granular progress list only when the user asks for verbosity, and remain silent by default. These rules apply in addition to the rules below.
<!--skill-flavor:diagnose-inherited-rules:end-->

<!--skill-flavor:single-nested-task-row:start-->
| Need | Read |
| --- | --- |
| Triage a failed flow run | [troubleshooting-guide.md](troubleshooting-guide.md) |
| Read the cause out of a faulted `flow debug` response | [troubleshooting-guide.md — Step 0](troubleshooting-guide.md#step-0--read-the-cause-in-the-debug-output-you-already-have) |
| Find the error message and faulting element | [troubleshooting-guide.md — Step 2 Fetch incidents](troubleshooting-guide.md#step-2--fetch-incidents) |
| See data state at failure time | [troubleshooting-guide.md — Step 3 Fetch runtime variable state](troubleshooting-guide.md#step-3--fetch-runtime-variable-state) |
| Map a faulting element ID to a `.flow` node | [troubleshooting-guide.md — Step 4 Correlate with the flow definition](troubleshooting-guide.md#step-4--correlate-with-the-flow-definition) |
| Pull verbose execution timeline | [troubleshooting-guide.md — Step 5 Traces](troubleshooting-guide.md#step-5--traces-last-resort) |
| Identify a `vars.X.output.Y` literal-string failure | [failure-modes.md — `=js:` prefix missing](failure-modes.md#js-prefix-missing) |
| Identify misshapen Studio Web nodes | [failure-modes.md — misshapen nodes](failure-modes.md#misshapen-rectangle-nodes-in-studio-web) |
| Diagnose a hung HITL node | [failure-modes.md — HITL `completed` port unwired](failure-modes.md#hitl-completed-port-unwired) |
| Diagnose a connector silent fault | [failure-modes.md — Reused reference ID](failure-modes.md#reused-reference-id--cross-connection-id-leakage) |
| Diagnose `Folder does not exist` on a resource node | [failure-modes.md — Missing `bindings[]` on resource node](failure-modes.md#missing-bindings-on-resource-node) |
| Triage "validate passes, debug faults" | [failure-modes.md — `flow validate` passes, `flow debug` faults](failure-modes.md#flow-validate-passes-flow-debug-faults) |
| Look up `instance` / `incident` CLI syntax | [shared/cli-commands.md](../shared/cli-commands.md) + [troubleshooting-guide.md — CLI command reference](troubleshooting-guide.md#cli-command-reference) |
<!--skill-flavor:single-nested-task-row:end-->

<!--skill-flavor:single-nested-reference-entry:start-->
- [failure-modes.md](failure-modes.md) — pattern catalog for known recurring failures: missing `=js:`, misshapen nodes, HITL-stuck, reused reference IDs, "validate passes / debug faults"
<!--skill-flavor:single-nested-reference-entry:end-->

<!--skill-flavor:diagnose-conventions-reference-entry:start-->
- [shared/cli-conventions.md](../shared/cli-conventions.md) — `--folder-key` requirement, JSON output shape
<!--skill-flavor:diagnose-conventions-reference-entry:end-->
