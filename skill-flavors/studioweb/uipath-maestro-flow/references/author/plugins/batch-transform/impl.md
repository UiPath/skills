<!--skill-flavor:bt-node-not-found:start-->
If the command reports **"Node type not found: uipath.pattern.batch-transform"**, run `uip maestro flow registry pull --force`. If it still fails, confirm with the UiPath admin that the tenant's `canvas.nodes.batch-transform` server flag is enabled; the CLI version is fixed by the Studio Web host and cannot be probed or updated, so report the gap if the flag is on.
<!--skill-flavor:bt-node-not-found:end-->

<!--skill-flavor:bt-attachment-populate:start-->
`uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored). Keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample CSV from the designer's Debug panel or an upstream node that yields the attachment. At runtime the variable holds a full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; `ID` is uppercase, not `Id`.
<!--skill-flavor:bt-attachment-populate:end-->

<!--skill-flavor:bt-node-add-cli:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.pattern.batch-transform \
  --label "<LABEL>" \
  --input '{
    "attachment": "=js:$vars.<triggerId>.output.<fileVarId>",
    "prompt": "<INSTRUCTION describing every output column>",
    "outputColumns": [
      { "name": "<COLUMN_NAME>", "description": "<WHAT TO PUT IN THIS COLUMN>" }
    ],
    "enableWebSearchGrounding": false
  }' \
  --output json
```
<!--skill-flavor:bt-node-add-cli:end-->

<!--skill-flavor:bt-validate-command:start-->
```bash
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```
<!--skill-flavor:bt-validate-command:end-->

<!--skill-flavor:bt-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.batch-transform` | Tenant flag `canvas.nodes.batch-transform` is off, or the host's CLI predates Batch Transform support | Run `uip maestro flow registry pull --force`; if still missing, check with the admin that `canvas.nodes.batch-transform` is enabled (the CLI version is fixed by the Studio Web host — report the gap) |
| Validate rejects `outputColumns` | Wrong shape, such as a map `{ name: description }` or string array | Use `[{ "name": "...", "description": "..." }, ...]` |
| Runtime error `exceeded maxColumns` | More than 10 output columns | Reduce to ≤10 or split across two Batch Transform nodes chained on the output file |
| All rows produce blank values for a column | `description` is vague or references fields absent from the source CSV | Name the source column(s) in the description and test with a small sample |
| Latency spikes / higher cost than expected | `enableWebSearchGrounding: true` is unnecessary | Set it to false unless rows need facts the LLM cannot infer from the row itself |
| Output file has the original row count but no new columns | Requested transformations duplicate source columns, so the LLM skipped them | Ensure every `outputColumns[].name` is new and not already in the source CSV |
<!--skill-flavor:bt-debug-table:end-->
