# Summarize Pattern Node — Implementation

Summarize synthesizes a response grounded in an attached document. Node type: `uipath.pattern.deep-rag`. BPMN service task with `serviceType: "ECS.DeepRag"`. No process bindings, no connection binding — inputs are the only source of configuration.

## Registry Validation

```bash
uip maestro flow registry get uipath.pattern.deep-rag --output json
```

Confirm:

- Input port: `input`
- Output ports: `output`, `error`
- `model.type` — `bpmn:ServiceTask`
- `model.serviceType` — `ECS.DeepRag`
- `inputDefinition.properties` — `attachment` (declared `string`; runtime wants the **full Flow Attachment object** `{ FullName, Id, Metadata, MimeType }` — Studio Web's file-picker form serializes the whole object into that slot, the engine deserializes it back), `prompt` (string), `returnCitations` (boolean)
- `outputDefinition.output.type` — `"object"`; `outputDefinition.output.source` — `"=response"` (the BPMN engine wraps the result under that key — same convention as every other ServiceTask)
- `outputDefinition.output.schema` — top-level fields `id` (string) and `content` (object|null) with PascalCase nested fields:
  - `content.Text` — string
  - `content.Citations` — array|null of `{ Ordinal: integer, PageNumber: integer, Source: string, Reference: string }`
- `outputDefinition.error.schema.required` — `code`, `message`, `detail`, `category`, `status`

If the command errors with **"Node type not found: uipath.pattern.deep-rag"**, the CLI build predates Summarize support or the tenant's `canvas.nodes.summarize` server flag is off. Run `uip tools update` and `uip maestro flow registry pull --force`; if it still errors, confirm with your UiPath admin that `canvas.nodes.summarize` is enabled on the tenant.

## Adding / Editing

Pattern nodes are OOTB BPMN service tasks — author them by editing the `.flow` JSON directly (Edit/Write). This is the canonical authoring path per [Author capability, rule 2](../../../CAPABILITY.md): the `uip maestro flow node add` / `edge add` carve-out is reserved for connectors, connector-triggers, and managed HTTP, where the CLI populates product-managed state. For OOTB structural edits — adding the Summarize node, wiring its edges, adding the `attachment` flow input — use Edit/Write against the `.flow` file. See [editing-operations.md](../../editing-operations.md) for the JSON authoring mechanics; the snippets below cover what is **specific** to Summarize.

## Wiring `attachment` — file variable bound to the trigger

The canonical canvas-produced shape is a flow `in` variable of `type: "file"` bound to the trigger via `triggerNodeId`, with the Summarize node's `attachment` referencing it through the trigger's output:

```json
"variables": {
  "globals": [
    {
      "id": "documentFile",
      "direction": "in",
      "type": "file",
      "triggerNodeId": "start"
    }
  ]
}
```

Then on the Summarize node:

```json
"inputs": {
  "attachment": "=js:$vars.start.output.documentFile",
  ...
}
```

`uip maestro flow debug --attachment documentFile=./path/to/doc.pdf` populates that variable as a `{ FullName, Id, Metadata, MimeType }` Attachment object at runtime. The flag is repeatable; `documentFile=` is required. **Invariant:** the LHS (`documentFile` here) MUST equal a `variables.globals[]` entry's `id` with `direction:"in"` AND `type:"file"`. Verify with `jq '.variables.globals[] | select(.direction=="in" and .type=="file") | .id' <flow>.flow` — a mismatch is not caught by the CLI today and faults silently at runtime. Do not declare the variable as `type: "object"`, do not reference it as `=js:$vars.documentFile` directly without the trigger output path, and do not pass a bare GUID/URL/path/`.Id`/`.FullName`.

## JSON Structure

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
                    "Ordinal":    { "type": "integer" },
                    "PageNumber": { "type": "integer" },
                    "Source":     { "type": "string" },
                    "Reference":  { "type": "string" }
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

Notes:

- **No instance-level `model` block.** BPMN type and `serviceType: "ECS.DeepRag"` live only in the corresponding `definitions[]` entry — copy that verbatim from `uip maestro flow registry get uipath.pattern.deep-rag --output json`. Per [Author capability, rule 16](../../../CAPABILITY.md), node instances normally have no `model` block.
- **`typeVersion` must match `definitions[<deep-rag>].version` exactly** — the registry currently emits `"1.0"` (one dot). Do not guess `"1.0.0"`.
- `outputs.output.source` is the literal **`=response`** (the convention every BPMN ServiceTask follows). Do not rewrite to `=deepRagResult` or similar.
- `outputs.output.type` is **`"object"`**, with the nested PascalCase schema above.
- Setting `returnCitations: true` populates `content.Citations`; setting `false` omits the array entirely (the downstream consumer should tolerate either).

## End-node output mapping

If the flow surfaces the synthesized text or citations as flow `out` variables, the End node must map them. Per [Author capability, rule 12](../../../CAPABILITY.md), value-field expressions need the `=js:` prefix. Note the **PascalCase** field names:

```json
{
  "id": "end",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "outputs": {
    "summary":   { "source": "=js:$vars.summarizeContract.output.content.Text" },
    "citations": { "source": "=js:$vars.summarizeContract.output.content.Citations" }
  }
}
```

Without `=js:`, the runtime stores the literal string (e.g. `"$vars.summarizeContract.output.content.Text"`) into the flow output instead of the real value. When `returnCitations: false`, drop the `citations` mapping rather than mapping a missing field. Lowercase variants (`.text`, `.citations`) do not exist in the response shape — they would resolve to `undefined`.

## Add via CLI (opt-in, not preferred)

The `uip maestro flow node add` / `edge add` CLI is **not** the canonical authoring path for OOTB pattern nodes (see rule 2 above). Reach for it only when scripting in a context where Edit/Write isn't available. The shape:

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

`attachment` must resolve to a **full Flow Attachment object** (`{ FullName, Id, Metadata, MimeType }`). Reference it through the trigger's output (`$vars.<triggerId>.output.<fileVarId>`) — that's how the canvas wires file-typed flow `in` variables. Do **not** pass a bare GUID, URL, byte stream, or path; even though the OOTB `inputDefinition` declares `type: "string"`, the engine wants the object. Set `returnCitations: false` (or omit) when downstream consumers do not need page-level provenance.

## Accessing Output

```javascript
// Downstream Script node
const result = $vars.summarizeContract.output;
const text = result.content.Text;                   // the synthesized prose
const citations = result.content.Citations ?? [];   // [{ Ordinal, PageNumber, Source, Reference }, ...]
return {
  summary: text,
  citationCount: citations.length,
};
```

Field names are **PascalCase** (`Text`, `Citations`, `Ordinal`, `PageNumber`, `Source`, `Reference`). If `returnCitations: false`, the `Citations` array is not present. Guard with `?? []` or check `result.content.Citations != null` before iterating.

## Validate

```bash
uip maestro flow validate <FlowName>.flow --output json
```

The validator checks that required inputs (`attachment`, `prompt`) are present and non-empty.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.deep-rag` | CLI predates Summarize support, or tenant flag `canvas.nodes.summarize` is off | `uip tools update`, `uip maestro flow registry pull --force`; check with admin that `canvas.nodes.summarize` is enabled if still missing |
| Runtime: synthesis returns empty `content.Text` | Prompt too vague, or attachment unreadable (image-only PDF with no OCR, corrupted file) | Tighten the prompt; confirm the attachment type is supported and has selectable text |
| `content.Citations` missing even though set `returnCitations: true` | Downstream consumer read the node's `inputDefaults` before the runtime produced the output | Reference `$vars.{nodeId}.output.content.Citations` only in nodes downstream of Summarize; do not precompute |
| Downstream `result.content.text` / `result.content.citations` is `undefined` | Used lowercase field names — the response shape is PascalCase | Switch to `result.content.Text` / `result.content.Citations` |
| Large documents time out | Synthesis cost scales with doc size; single call is bounded | Split the document upstream (per-section Summarize calls + a final merge step) or move to a published [Agent](../agent/impl.md) with a context-grounding resource |
| Wrong citations (pages off by one, wrong source) | The attached document's page numbering doesn't match the displayed page ordinal | Treat `Ordinal` and `PageNumber` as advisory — present `Source`/`Reference` alongside and let the reader verify |

## What NOT to Do

- **Do not hand-author `model.bindings`** on the node — Summarize has no process or connector binding. Adding a `bindings` block will be stripped or cause validate errors.
- **Do not pass `--source` on `uip maestro flow node add`** — `--source` is only for inline agent nodes. Summarize has no agent project behind it.
- **Do not chain Summarize for multi-turn chat.** It is single-turn; each call is independent. Use a published [Agent](../agent/impl.md) for conversational flows.
- **Do not stuff `prompt` with entire document text.** The attachment is already ingested — the prompt should describe **the task**, not the input.
- **Do not assume `content.Citations` is always present.** When `returnCitations: false`, the field is omitted; downstream code must guard.
- **Do not use lowercase field names** (`content.text`, `content.citations`, `.ordinal`, `.page`). The runtime emits PascalCase: `content.Text`, `content.Citations`, `Ordinal`, `PageNumber`, `Source`, `Reference`.
- **Do not pass `attachment` as a bare string id, GUID, URL, or path.** The OOTB schema and Studio Web's file-picker UI suggest a string, but the runtime needs the **full Flow Attachment object** `{ FullName, Id, Metadata, MimeType }`. The canonical wiring is a flow `in` variable of `type: "file"` bound to the trigger via `triggerNodeId`, referenced as `=js:$vars.<triggerId>.output.<fileVarId>` (see Key Inputs in `planning.md`). Bare-id mistakes pass `flow validate` cleanly and fault at runtime.
- **Do not write `outputs.output.source: "=deepRagResult"`.** The canonical value is `"=response"` (the convention every BPMN ServiceTask follows).
