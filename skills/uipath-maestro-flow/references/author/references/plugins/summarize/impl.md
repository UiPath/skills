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
- `inputDefinition.properties` — `attachment` (object — full Flow Attachment, **not** a bare id), `prompt` (string), `returnCitations` (boolean). The schema declares `string` because Studio Web's file picker serializes the whole Attachment object into that slot at save time; the runtime parses it back as an object — pass the **whole** `{ FullName, Id, Metadata, MimeType }` object, not a GUID, URL, or path.
- `outputDefinition.output.schema.properties.content` contains `text` (and `citations` when enabled)
- `outputDefinition.error.schema.required` — `code`, `message`, `detail`, `category`, `status`

If the command errors with **"Node type not found: uipath.pattern.deep-rag"**, the CLI build predates Summarize support or the tenant's `canvas.nodes.summarize` server flag is off. Run `uip cli update` and `uip maestro flow registry pull --force`; if it still errors, confirm with your UiPath admin that `canvas.nodes.summarize` is enabled on the tenant.

## Adding / Editing

Pattern nodes are OOTB BPMN service tasks — author them by editing the `.flow` JSON directly (Edit/Write). This is the canonical authoring path per [author/CAPABILITY.md rule 2](../../CAPABILITY.md): the `uip maestro flow node add` / `edge add` carve-out is reserved for connectors, connector-triggers, and managed HTTP, where the CLI populates product-managed state. For OOTB structural edits — adding the Summarize node, wiring its edges, adding the `attachment` flow input — use Edit/Write against the `.flow` file. See [editing-operations.md](../../editing-operations.md) for the JSON authoring mechanics; the snippets below cover what is **specific** to Summarize.

## JSON Structure

```json
{
  "id": "summarizeContract",
  "type": "uipath.pattern.deep-rag",
  "typeVersion": "1.0",
  "display": { "label": "Summarize Contract" },
  "inputs": {
    "attachment": "=js:$vars.contractDoc",
    "prompt": "Write a 5-bullet executive summary covering scope, term, SLAs, penalties, and termination.",
    "returnCitations": true
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Synthesis result",
      "source": "=deepRagResult",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the synthesis fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Notes:

- **No instance-level `model` block.** BPMN type and `serviceType: "ECS.DeepRag"` live only in the corresponding `definitions[]` entry — copy that verbatim from `uip maestro flow registry get uipath.pattern.deep-rag --output json`. Per [author/CAPABILITY.md rule 16](../../CAPABILITY.md), node instances normally have no `model` block.
- **`typeVersion` must match `definitions[<deep-rag>].version` exactly** — the registry currently emits `"1.0"` (one dot). Do not guess `"1.0.0"`.
- `outputs.output.source` is the literal `=deepRagResult` — do not rewrite.
- Setting `returnCitations: true` populates `content.citations`; setting `false` omits the array entirely (the downstream consumer should tolerate either).

## End-node output mapping

If the flow surfaces the synthesized text or citations as flow `out` variables, the End node must map them. Per [author/CAPABILITY.md rule 12](../../CAPABILITY.md), value-field expressions need the `=js:` prefix:

```json
{
  "id": "end",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "outputs": {
    "summary":   { "source": "=js:$vars.summarizeContract.output.content.text" },
    "citations": { "source": "=js:$vars.summarizeContract.output.content.citations" }
  }
}
```

Without `=js:`, the runtime stores the literal string (e.g. `"$vars.summarizeContract.output.content.text"`) into the flow output instead of the real value. When `returnCitations: false`, drop the `citations` mapping rather than mapping a missing field.

## Add via CLI (opt-in, not preferred)

The `uip maestro flow node add` / `edge add` CLI is **not** the canonical authoring path for OOTB pattern nodes (see rule 2 above). Reach for it only when scripting in a context where Edit/Write isn't available. The shape:

```bash
uip maestro flow node add <FlowName>.flow uipath.pattern.deep-rag \
  --label "<LABEL>" \
  --input '{
    "attachment": "=js:$vars.<inputAttachmentVar>",
    "prompt": "<INSTRUCTION for the synthesis>",
    "returnCitations": true
  }' \
  --output json
```

`attachment` must resolve to a **full Flow Attachment object** with shape `{ FullName, Id, Metadata, MimeType }` — point it at an upstream variable holding the whole object (typically a flow `in` variable populated by `uip maestro flow debug --file <name>=<path>`, or an upstream node that emits a Flow Attachment). **Not** a bare id, URL, byte stream, or path; even though Studio Web's form metadata calls this a `file` field and the OOTB schema says `type: "string"`, the engine wants the object. Set `returnCitations: false` (or omit) when downstream consumers do not need page-level provenance.

## Accessing Output

```javascript
// Downstream Script node
const result = $vars.summarizeContract.output;
const text = result.content.text;                   // the synthesized prose
const citations = result.content.citations ?? [];    // [{ ordinal, page, source }, ...]
return {
  summary: text,
  citationCount: citations.length,
};
```

If `returnCitations: false`, the `citations` array is not present. Guard with `?? []` or check `result.content.citations != null` before iterating.

## Validate

```bash
uip maestro flow validate <FlowName>.flow --output json
```

The validator checks that required inputs (`attachment`, `prompt`) are present and non-empty.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.deep-rag` | CLI predates Summarize support, or tenant flag `canvas.nodes.summarize` is off | `uip cli update`, `uip maestro flow registry pull --force`; check with admin that `canvas.nodes.summarize` is enabled if still missing |
| Runtime: synthesis returns empty `content.text` | Prompt too vague, or attachment unreadable (image-only PDF with no OCR, corrupted file) | Tighten the prompt; confirm the attachment type is supported and has selectable text |
| `content.citations` missing even though set `returnCitations: true` | Downstream consumer read the node's `inputDefaults` before the runtime produced the output | Reference `$vars.{nodeId}.output.content.citations` only in nodes downstream of Summarize; do not precompute |
| Large documents time out | Synthesis cost scales with doc size; single call is bounded | Split the document upstream (per-section Summarize calls + a final merge step) or move to a published [Agent](../agent/impl.md) with a context-grounding resource |
| Wrong citations (pages off by one, wrong source) | The attached document's page numbering doesn't match the displayed page ordinal | Treat `ordinal` and `page` as advisory — present the source identifier alongside and let the reader verify |

## What NOT to Do

- **Do not hand-author `model.bindings`** on the node — Summarize has no process or connector binding. Adding a `bindings` block will be stripped or cause validate errors.
- **Do not pass `--source` on `uip maestro flow node add`** — `--source` is only for inline agent nodes. Summarize has no agent project behind it.
- **Do not chain Summarize for multi-turn chat.** It is single-turn; each call is independent. Use a published [Agent](../agent/impl.md) for conversational flows.
- **Do not stuff `prompt` with entire document text.** The attachment is already ingested — the prompt should describe **the task**, not the input.
- **Do not assume `content.citations` is always present.** When `returnCitations: false`, the field is omitted; downstream code must guard.
- **Do not pass `attachment` as a bare string id, GUID, URL, or path.** The OOTB schema and Studio Web's file-picker UI suggest a string, but the runtime needs the **full Flow Attachment object** `{ FullName, Id, Metadata, MimeType }`. Always pass the whole object via `=js:$vars.<name>` (see Key Inputs in `planning.md`). Bare-id mistakes pass `flow validate` cleanly and fault at runtime.
