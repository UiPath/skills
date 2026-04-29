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
- `inputDefinition.properties` — `attachment` (string — Orchestrator Attachment Id), `prompt` (string), `returnCitations` (boolean)
- `outputDefinition.output.schema.properties.content` contains `text` (and `citations` when enabled)
- `outputDefinition.error.schema.required` — `code`, `message`, `detail`, `category`, `status`

If the command errors with **"Node type not found: uipath.pattern.deep-rag"**, the CLI build predates Patterns support or the tenant's `canvas.nodes.patterns` server flag is off. Run `uip cli update` and `uip maestro flow registry pull --force`; if it still errors, confirm with your UiPath admin that Patterns are enabled on the tenant.

## Adding / Editing

For general add, delete, and wiring mechanics, see [flow-editing-operations.md](../../flow-editing-operations.md). The snippets below cover what is **specific** to Summarize.

### Add the node via CLI

```bash
uip maestro flow node add <FlowName>.flow uipath.pattern.deep-rag \
  --label "<LABEL>" \
  --position <X>,<Y> \
  --input '{
    "attachment": "$vars.<upstreamNode>.output.<attachmentIdField>",
    "prompt": "<INSTRUCTION for the synthesis>",
    "returnCitations": true
  }' \
  --output json
```

`--input` accepts a JSON object; the CLI merges it into the node's `inputs`. `attachment` must resolve to an **Orchestrator Attachment Id** string (a GUID) — point it at the field on the upstream node's output that carries the attachment id (not a file URL, file bytes, or a path). Set `returnCitations: false` (or omit) when downstream consumers do not need page-level provenance.

**Save the returned node ID** — needed for wiring edges and downstream `$vars.{nodeId}.output` references.

### Wire edges

```bash
uip maestro flow node list <FlowName>.flow --output json

# Upstream file producer (e.g., HTTP download, connector) → Summarize
uip maestro flow edge add <FlowName>.flow <upstreamNodeId> <drNodeId> \
  --source-port <upstreamOutputPort> --target-port input --output json

# Summarize success → downstream consumer
uip maestro flow edge add <FlowName>.flow <drNodeId> <nextNodeId> \
  --source-port output --target-port input --output json

# Optional: error branch
uip maestro flow edge add <FlowName>.flow <drNodeId> <errorHandlerId> \
  --source-port error --target-port input --output json
```

## JSON Structure

```json
{
  "id": "summarizeContract",
  "type": "uipath.pattern.deep-rag",
  "typeVersion": "1.0.0",
  "display": { "label": "Summarize Contract" },
  "inputs": {
    "attachment": "$vars.uploadContract.output.attachmentId",
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
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "ECS.DeepRag"
  }
}
```

Notes:

- `model.bindings` is **absent** — Summarize is not a process or connector node; there is nothing to bind.
- `outputs.output.source` is the literal `=deepRagResult` — do not rewrite.
- Setting `returnCitations: true` populates `content.citations`; setting `false` omits the array entirely (the downstream consumer should tolerate either).

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
| `Node type not found: uipath.pattern.deep-rag` | CLI predates Patterns support, or tenant flag `canvas.nodes.patterns` is off | `uip cli update`, `uip maestro flow registry pull --force`; check with admin if still missing |
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
