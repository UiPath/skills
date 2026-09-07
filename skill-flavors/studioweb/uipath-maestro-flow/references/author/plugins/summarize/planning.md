<!--skill-flavor:sum-key-inputs-table:start-->
| Input | Required | Type | Description |
| --- | --- | --- | --- |
| `attachment` | Yes | full Flow Attachment | Supply the full case-sensitive Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; `ID` is uppercase, not `Id`. Define it as a flow-level `in` variable with `type: "file"`, bound to the trigger using `triggerNodeId: "<triggerId>"`. In Studio Web `uip flow debug` cannot upload a file for it (`--attachment` is ignored) — test with a sample document from the designer's Debug panel or an upstream node that yields the attachment. Reference it on the node as `=js:$vars.<triggerId>.output.<fileVarId>`, which resolves to the whole Attachment object. Although the OOTB `inputDefinition.attachment` declares `type: "string"` because Studio Web serializes the object into that slot when saving, the engine deserializes it back. Never wire a bare GUID, URL, byte stream, file path, or `.ID`/`.FullName` subfield. |
| `prompt` | Yes | string | Task instruction, such as an executive summary, a list of SLA penalty clauses, or an answer about a termination notice period. |
| `returnCitations` | No | boolean | Set to `true` to populate `content.Citations` with per-claim page references; default is `false`. |
<!--skill-flavor:sum-key-inputs-table:end-->
