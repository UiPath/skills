<!--skill-flavor:bt-node-not-found:start-->
If the command reports **"Node type not found: uipath.pattern.batch-transform"**, run `uip maestro flow registry pull --force`. If it still fails, confirm with the UiPath admin that the tenant's `canvas.nodes.batch-transform` server flag is enabled; the CLI version is fixed by the Studio Web host and cannot be probed or updated, so report the gap if the flag is on.
<!--skill-flavor:bt-node-not-found:end-->

<!--skill-flavor:bt-attachment-populate:start-->
`uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored). Keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample CSV from the designer's Debug panel or an upstream node that yields the attachment. At runtime the variable holds a full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; `ID` is uppercase, not `Id`.
<!--skill-flavor:bt-attachment-populate:end-->

<!--skill-flavor:bt-node-add-cli:start-->
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.pattern.batch-transform \
<!--skill-flavor:bt-node-add-cli:end-->

<!--skill-flavor:bt-validate-command:start-->
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
<!--skill-flavor:bt-validate-command:end-->

<!--skill-flavor:bt-debug-table:start-->
| `Node type not found: uipath.pattern.batch-transform` | Tenant flag `canvas.nodes.batch-transform` is off, or the host's CLI predates Batch Transform support | Run `uip maestro flow registry pull --force`; if still missing, check with the admin that `canvas.nodes.batch-transform` is enabled (the CLI version is fixed by the Studio Web host — report the gap) |
<!--skill-flavor:bt-debug-table:end-->
