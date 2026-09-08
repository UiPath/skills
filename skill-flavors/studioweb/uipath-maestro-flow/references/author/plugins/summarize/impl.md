<!--skill-flavor:sum-node-not-found:start-->
If the command returns **"Node type not found: uipath.pattern.deep-rag"**, run `uip maestro flow registry pull --force`. If it still fails, confirm with a UiPath admin that the tenant's `canvas.nodes.summarize` server flag is enabled; the CLI version is fixed by the Studio Web host and cannot be probed or updated, so report the gap if the flag is on.
<!--skill-flavor:sum-node-not-found:end-->

<!--skill-flavor:sum-attachment-populate:start-->
`uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored). Keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample document from the designer's Debug panel or an upstream node that yields the attachment. At runtime the variable holds `{ ID, FullName, MimeType, Metadata }`.
<!--skill-flavor:sum-attachment-populate:end-->

<!--skill-flavor:sum-node-add-cli:start-->
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.pattern.deep-rag \
<!--skill-flavor:sum-node-add-cli:end-->

<!--skill-flavor:sum-validate-command:start-->
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
<!--skill-flavor:sum-validate-command:end-->

<!--skill-flavor:sum-debug-table:start-->
| `Node type not found: uipath.pattern.deep-rag` | Tenant flag `canvas.nodes.summarize` is off, or the host's CLI predates Summarize support | Run `uip maestro flow registry pull --force`; if still missing, check with an admin that `canvas.nodes.summarize` is enabled (the CLI version is fixed by the Studio Web host — report the gap) |
<!--skill-flavor:sum-debug-table:end-->
