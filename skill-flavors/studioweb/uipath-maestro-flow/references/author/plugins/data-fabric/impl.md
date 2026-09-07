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
```bash
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```
<!--skill-flavor:df-validate-command:end-->

<!--skill-flavor:df-debug-table:start-->
| Symptom | Cause | Fix |
| --- | --- | --- |
| `Node not found: core.datafabric.*` on `registry get` | Tenant flag off, or the host's CLI predates the node | `uip maestro flow registry pull --force`; then confirm that node's flag with the admin (see the table above). The CLI version is fixed by the Studio Web host — report the gap if the flag is on |
| Node validates clean, runs green, nothing written | Most often a **selector** problem, not a binding one: `readEntityNodeId` names a missing node or a multi-record read, the read's filters do not compile, or the `fromRead` read matched more than one record at runtime | Check the Read node's `id` matches exactly and its `resultMode` is `single`; confirm the filter identifies exactly one record with `uip df records list` |
| Write runs green, row unchanged | The body was rejected and the rejection swallowed — a federated entity, a system or attachment column, a choice-set label instead of its numeric id, an uncoercible value, or a null into a non-nullable column | Re-check the entity is native and each column against `uip df entities get` |
| Downstream `$vars.<id>.output` is `undefined` | `variables.nodes[]` missing, or the read matched nothing | Run `uip maestro flow format`; if it persists, verify the filter matches a real record |
| A Loop over a multi-record read iterates nothing | Wired `output` instead of `output.results` | Use `=js:$vars.<readId>.output.results` |
| Multi-record read returns only some rows | The limit is always explicit and capped at 1000 | Page with `_skip`; raising `_recordLimit` past 1000 truncates silently |
| `404 Entity <name> does not exist` | Folder-scoped entity queried without folder qualification, or a related-field join | Set `_folderKey` and its bindings. Joins across a folder-scoped entity are not supported — the join request carries a bare name with no folder qualifier |
| Read returns every record | Filters compiled away — a blank expression row, or an `in` row in `single` mode | Check each row against [Filters](#filters) |
| Console warning `… has no name/folderKey binding — serializing a non-portable literal` | Folder-scoped entity missing a `bindings[]` row | Add both rows — see [Folder-scoped entities and bindings](#folder-scoped-entities-and-bindings) |
<!--skill-flavor:df-debug-table:end-->
