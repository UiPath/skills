# Summarize Pattern Node — Implementation

Summarize synthesizes a response grounded in an attached document. Node type: `uipath.pattern.deep-rag`; BPMN service task with `serviceType: "ECS.DeepRag"`. Inputs are the only configuration source; there are no process or connection bindings.

## Registry validation

Run:

```bash
uip maestro flow registry get uipath.pattern.deep-rag --output json
```

Confirm:

- Input port: `input`; output ports: `output`, `error`.
- `model.type`: `bpmn:ServiceTask`; `model.serviceType`: `ECS.DeepRag`.
- `inputDefinition.properties`: `attachment` (declared `string`, but runtime requires the full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`, with case-sensitive keys and uppercase `ID`), `prompt` (string), and `returnCitations` (boolean).
- `outputDefinition.output.type`: `"object"`; `outputDefinition.output.source`: `"=response"` (the BPMN engine wraps the result under that key, as for every ServiceTask).
- `outputDefinition.output.schema`: top-level `id` (string) and `content` (object|null), with `content.Text` (string) and `content.Citations` (array|null) containing `{ Ordinal: integer, PageNumber: integer, Source: string, Reference: string }`.
- `outputDefinition.error.schema.required`: `code`, `message`, `detail`, `category`, `status`.

If the command returns **"Node type not found: uipath.pattern.deep-rag"**, run `uip tools update` and `uip maestro flow registry pull --force`. If it still fails, confirm with a UiPath admin that the tenant's `canvas.nodes.summarize` server flag is enabled.

## Authoring and attachment wiring

Pattern nodes are OOTB BPMN service tasks and are **user-owned** per [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node). Author them by editing `.flow` JSON directly (Edit/Write). The `uip maestro flow node add` / `edge add` CLI is reserved for CLI-owned nodes (connectors, connector-triggers, managed HTTP), where the CLI populates product-managed state. Use Edit/Write for OOTB structural edits—adding Summarize, wiring edges, and adding the `attachment` flow input. See [editing-operations.md](../../editing-operations.md).

Declare a flow `in` variable with `type: "file"`, bound to the trigger with `triggerNodeId`, and reference it through the trigger output:

```json
"variables": {
  "globals": [{
    "id": "documentFile",
    "direction": "in",
    "type": "file",
    "triggerNodeId": "start"
  }]
}
```

```json
"inputs": {
  "attachment": "=js:$vars.start.output.documentFile",
  "...": "..."
}
```

Populate it by running `uip maestro flow debug --attachment <variableId>=<localPath>`, for example, `--attachment documentFile=./path/to/doc.pdf`. The CLI uploads the file and binds `{ ID, FullName, MimeType, Metadata }`. The flag is repeatable, and `<variableId>` must match a `variables.globals[]` `id`; see [cli-commands.md — Pre-flight](../../../../shared/cli-commands.md#pre-flight---attachment-binding).

Do not declare the variable as `type: "object"`; reference it without the trigger output path; or pass a bare GUID, URL, path, `.ID`, or `.FullName`.

## JSON structure and rules

```json
{
  "id": "summarizeContract",
  "type": "uipath.pattern.deep-rag",
  "typeVersion": "1.0",
  "display": { "label": "Summarize Contract" },
  "inputs": {
    "attachment": "=js:$vars.start.output.documentFile",
    "prompt": "Write a 5-bullet executive summary covering scope, term, SLAs, penalties, and termination.",
    "returnCitations": true
  },
  "outputs": {
    "output": {
      "type": "object",
      "source": "=response",
      "var": "output",
      "schema": {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "content": {
            "type": ["object", "null"],
            "properties": {
              "Text": { "type": "string" },
              "Citations": {
                "type": ["array", "null"],
                "items": {
                  "type": "object",
                  "properties": {
                    "Ordinal": { "type": "integer" },
                    "PageNumber": { "type": "integer" },
                    "Source": { "type": "string" },
                    "Reference": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

- Do not add an instance-level `model` block. BPMN type and `serviceType: "ECS.DeepRag"` belong only in the corresponding `definitions[]` entry; copy that entry verbatim from `uip maestro flow registry get uipath.pattern.deep-rag --output json`. Per [Author capability, rule 15](../../../CAPABILITY.md), node instances normally have no `model` block.
- Set `typeVersion` exactly to `definitions[<deep-rag>].version` from the registry. Do not guess; use the exact single-dot `x.y` form, such as `"1.0"`, not `"1.0.0"`.
- Set `outputs.output.source` literally to `=response`, not `=deepRagResult` or another name.
- Set `outputs.output.type` to `"object"` with the nested PascalCase schema shown above.
- `returnCitations: true` populates `content.Citations`; `false` omits it, so downstream consumers must tolerate either form.

## End-node output mapping

Expose results with `=js:` expressions as required by [Author capability, rule 11](../../../CAPABILITY.md):

```json
{
  "id": "end",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "outputs": {
    "summary": { "source": "=js:$vars.summarizeContract.output.content.Text" },
    "citations": { "source": "=js:$vars.summarizeContract.output.content.Citations" }
  }
}
```

Without `=js:`, the runtime stores the literal expression string. Use only `.Text` and `.Citations`; lowercase variants resolve to `undefined`. If `returnCitations: false`, omit the `citations` mapping.

## Add via CLI (opt-in, not preferred)

The `uip maestro flow node add` / `edge add` CLI is not canonical for OOTB pattern nodes; use it only when scripting where Edit/Write is unavailable. Run:

```bash
uip maestro flow node add <FlowName>.flow uipath.pattern.deep-rag \
  --label "<LABEL>" \
  --input '{
    "attachment": "=js:$vars.<triggerId>.output.<fileVarId>",
    "prompt": "<INSTRUCTION for the synthesis>",
    "returnCitations": true
  }' \
  --output json
```

`attachment` must resolve to `{ ID, FullName, MimeType, Metadata }` through `$vars.<triggerId>.output.<fileVarId>`. Do not pass a bare GUID, URL, byte stream, or path. Set `returnCitations: false` or omit it when provenance is unnecessary.

## Accessing output

```javascript
// Downstream Script node
const result = $vars.summarizeContract.output;
const text = result.content.Text;
const citations = result.content.Citations ?? [];
return { summary: text, citationCount: citations.length };
```

Use PascalCase: `Text`, `Citations`, `Ordinal`, `PageNumber`, `Source`, and `Reference`. When citations are disabled, guard with `?? []` or check `result.content.Citations != null` before iterating.

## Validate

Run:

```bash
uip maestro flow validate <FlowName>.flow --output json
```

The validator checks that required inputs (`attachment`, `prompt`) are present and non-empty. A bare attachment id can pass validation but fail at runtime.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.deep-rag` | CLI predates Summarize support, or tenant flag `canvas.nodes.summarize` is off | Run `uip tools update` and `uip maestro flow registry pull --force`; if still missing, check with an admin that `canvas.nodes.summarize` is enabled |
| Runtime: synthesis returns empty `content.Text` | Prompt is vague, or attachment is unreadable, such as an image-only PDF with no OCR or a corrupted file | Tighten the prompt; confirm the attachment type is supported and has selectable text |
| `content.Citations` missing despite `returnCitations: true` | A downstream consumer read `inputDefaults` before runtime output existed | Reference `$vars.{nodeId}.output.content.Citations` only in nodes downstream of Summarize; do not precompute |
| Downstream `result.content.text` / `result.content.citations` is `undefined` | Lowercase field names were used | Use `result.content.Text` / `result.content.Citations` |
| Large documents time out | Synthesis cost scales with document size and one call is bounded | Split upstream into per-section Summarize calls plus a final merge, or use a published [Agent](../agent/impl.md) with a context-grounding resource |
| Wrong citations, such as pages off by one or wrong source | Document page numbering differs from displayed page ordinal | Treat `Ordinal` and `PageNumber` as advisory; present `Source`/`Reference` and let the reader verify |

## What not to do

- Do not hand-author `model.bindings`; Summarize has no process or connector binding. Such a block may be stripped or cause validation errors.
- Do not pass `--source` to `uip maestro flow node add`; `--source` is only for inline agent nodes. Summarize has no agent project behind it.
- Do not chain Summarize for multi-turn chat. Calls are single-turn and independent; use a published [Agent](../agent/impl.md) for conversational flows.
- Do not put the entire document text in `prompt`; the attachment is already ingested. Describe the task instead.
- Do not assume `content.Citations` is always present; it is omitted when `returnCitations: false`.
- Do not use lowercase field names such as `content.text`, `content.citations`, `.ordinal`, or `.page`; the runtime emits `content.Text`, `content.Citations`, `Ordinal`, `PageNumber`, `Source`, and `Reference`.
- Do not pass `attachment` as a bare string id, GUID, URL, or path. The runtime requires `{ ID, FullName, MimeType, Metadata }`, with uppercase `ID`, referenced as `=js:$vars.<triggerId>.output.<fileVarId>` from a file-typed flow `in` variable bound with `triggerNodeId`; see Key Inputs in `planning.md`. Bare-id mistakes can pass `flow validate` and fault at runtime.
- Do not write `outputs.output.source: "=deepRagResult"`; the canonical value is `"=response"`.