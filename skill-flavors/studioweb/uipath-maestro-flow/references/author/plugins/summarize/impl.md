<!--skill-flavor:sum-node-not-found:start-->
If the command returns **"Node type not found: uipath.pattern.deep-rag"**, run `uip maestro flow registry pull --force`. If it still fails, confirm with a UiPath admin that the tenant's `canvas.nodes.summarize` server flag is enabled; the CLI version is fixed by the Studio Web host and cannot be probed or updated, so report the gap if the flag is on.
<!--skill-flavor:sum-node-not-found:end-->

<!--skill-flavor:sum-attachment-populate:start-->
`uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored). Keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample document from the designer's Debug panel or an upstream node that yields the attachment. At runtime the variable holds `{ ID, FullName, MimeType, Metadata }`.
<!--skill-flavor:sum-attachment-populate:end-->

<!--skill-flavor:sum-node-add-cli:start-->
```bash
uip maestro flow node add /solution/<FlowProject>/new.flow uipath.pattern.deep-rag \
  --label "<LABEL>" \
  --input '{
    "attachment": "=js:$vars.<triggerId>.output.<fileVarId>",
    "prompt": "<INSTRUCTION for the synthesis>",
    "returnCitations": true
  }' \
  --output json
```
<!--skill-flavor:sum-node-add-cli:end-->

<!--skill-flavor:sum-validate-command:start-->
```bash
uip maestro flow validate /solution/<FlowProject>/new.flow --output json
```
<!--skill-flavor:sum-validate-command:end-->

<!--skill-flavor:sum-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.deep-rag` | Tenant flag `canvas.nodes.summarize` is off, or the host's CLI predates Summarize support | Run `uip maestro flow registry pull --force`; if still missing, check with an admin that `canvas.nodes.summarize` is enabled (the CLI version is fixed by the Studio Web host — report the gap) |
| Runtime: synthesis returns empty `content.Text` | Prompt is vague, or attachment is unreadable, such as an image-only PDF with no OCR or a corrupted file | Tighten the prompt; confirm the attachment type is supported and has selectable text |
| `content.Citations` missing despite `returnCitations: true` | A downstream consumer read `inputDefaults` before runtime output existed | Reference `$vars.{nodeId}.output.content.Citations` only in nodes downstream of Summarize; do not precompute |
| Downstream `result.content.text` / `result.content.citations` is `undefined` | Lowercase field names were used | Use `result.content.Text` / `result.content.Citations` |
| Large documents time out | Synthesis cost scales with document size and one call is bounded | Split upstream into per-section Summarize calls plus a final merge, or use a published [Agent](../agent/impl.md) with a context-grounding resource |
| Wrong citations, such as pages off by one or wrong source | Document page numbering differs from displayed page ordinal | Treat `Ordinal` and `PageNumber` as advisory; present `Source`/`Reference` and let the reader verify |
<!--skill-flavor:sum-debug-table:end-->
