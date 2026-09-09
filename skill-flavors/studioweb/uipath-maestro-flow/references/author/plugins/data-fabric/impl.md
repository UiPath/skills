<!--skill-flavor:df-node-not-found:start-->
If `registry get` reports **"Node not found"**, the node is not available to you. Run `uip maestro flow registry pull --force` and retry (the CLI version is fixed by the Studio Web host and cannot be probed or updated). If it still fails, that node's tenant feature flag is off:
<!--skill-flavor:df-node-not-found:end-->

<!--skill-flavor:df-unavailable-switch:start-->
**When the node is unavailable, switch to the connector and stop.** `AvailableOnTenant: false` is a decision, not an obstacle: build the flow with the `uipath-uipath-dataservice` activities ([connector/impl.md](../connector/impl.md)) and say in the final report that the native nodes were unavailable. Do not retry `registry get` (the host's CLI cannot be updated for a newer manifest), and above all **do not hand-author a `definitions[]` entry from this doc's field list to stand in for the missing one** — a hand-written definition carries the wrong port schema, passes `flow validate`, and fails at runtime.
<!--skill-flavor:df-unavailable-switch:end-->

<!--skill-flavor:df-format-step:start-->
Run `uip maestro flow format /solution/<FlowProject>/new.flow` after adding nodes. Format regenerates `variables.nodes[]`, which is what makes `$vars.<nodeId>.output` resolve at runtime; skipping it produces a flow that validates but resolves the reference to `undefined` ([Author capability, rule 14](../../CAPABILITY.md#critical-rules)).
<!--skill-flavor:df-format-step:end-->

<!--skill-flavor:df-validate-command:start-->
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
<!--skill-flavor:df-validate-command:end-->

<!--skill-flavor:df-debug-table:start-->
| `Node not found: core.datafabric.*` on `registry get` | Tenant flag off, or the host's CLI predates the node | `uip maestro flow registry pull --force`; then confirm that node's flag with the admin (see the table above). The CLI version is fixed by the Studio Web host — report the gap if the flag is on |
<!--skill-flavor:df-debug-table:end-->
