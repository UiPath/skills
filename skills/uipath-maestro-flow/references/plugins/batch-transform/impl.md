# Batch Transform Pattern Node — Implementation

Batch Transform runs an LLM row-by-row over an attached CSV and appends LLM-generated columns. Node type: `uipath.pattern.batch-transform`. BPMN service task with `serviceType: "ECS.BatchTransform"`. No process bindings, no connection binding — inputs are the only source of configuration.

## Registry Validation

```bash
uip maestro flow registry get uipath.pattern.batch-transform --output json
```

Confirm:

- Input port: `input`
- Output ports: `output`, `error`
- `model.type` — `bpmn:ServiceTask`
- `model.serviceType` — `ECS.BatchTransform`
- `inputDefinition.properties` — `attachment` (string — Orchestrator Attachment Id), `prompt` (string), `enableWebSearchGrounding` (boolean), `outputColumns` (array of `{ name, description }`)
- `outputDefinition.output.schema.properties` — `id`, `fileName`, `mimeType`
- `outputDefinition.error.schema.required` — `code`, `message`, `detail`, `category`, `status`

If the command errors with **"Node type not found: uipath.pattern.batch-transform"**, the CLI build predates Patterns support or the tenant's `canvas.nodes.patterns` server flag is off. Run `uip cli update` and `uip maestro flow registry pull --force`; if it still errors, confirm with your UiPath admin that Patterns are enabled on the tenant.

## Adding / Editing

For general add, delete, and wiring mechanics, see [flow-editing-operations.md](../../flow-editing-operations.md). The snippets below cover what is **specific** to Batch Transform.

### Add the node via CLI

```bash
uip maestro flow node add <FlowName>.flow uipath.pattern.batch-transform \
  --label "<LABEL>" \
  --position <X>,<Y> \
  --input '{
    "attachment": "$vars.<upstreamNode>.output.<attachmentIdField>",
    "prompt": "<INSTRUCTION describing every output column>",
    "outputColumns": [
      { "name": "<COLUMN_NAME>", "description": "<WHAT TO PUT IN THIS COLUMN>" }
    ],
    "enableWebSearchGrounding": false
  }' \
  --output json
```

`--input` accepts a JSON object; the CLI merges it into the node's `inputs`. `attachment` must resolve to an **Orchestrator Attachment Id** string (a GUID) — point it at the field on the upstream node's output that carries the attachment id (not a file URL, file bytes, or a path). The `outputColumns` array can have up to 10 entries. Omit `enableWebSearchGrounding` unless rows genuinely require web-fetched facts.

**Save the returned node ID** — needed for wiring edges and downstream `$vars.{nodeId}.output` references.

### Wire edges

```bash
uip maestro flow node list <FlowName>.flow --output json

# Upstream file producer (e.g., HTTP, connector, agent) → Batch Transform
uip maestro flow edge add <FlowName>.flow <upstreamNodeId> <btNodeId> \
  --source-port <upstreamOutputPort> --target-port input --output json

# Batch Transform success → downstream consumer
uip maestro flow edge add <FlowName>.flow <btNodeId> <nextNodeId> \
  --source-port output --target-port input --output json

# Optional: error branch
uip maestro flow edge add <FlowName>.flow <btNodeId> <errorHandlerId> \
  --source-port error --target-port input --output json
```

## JSON Structure

```json
{
  "id": "categorizeRows",
  "type": "uipath.pattern.batch-transform",
  "typeVersion": "1.0.0",
  "display": { "label": "Categorize Invoices" },
  "inputs": {
    "attachment": "$vars.fetchRows.output.attachmentId",
    "prompt": "Classify each invoice by category and write a one-line summary.",
    "enableWebSearchGrounding": false,
    "outputColumns": [
      { "name": "Category", "description": "One of: Utility, Software, Travel, Other" },
      { "name": "Summary",  "description": "Plain-English one-line summary of the invoice" }
    ]
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "Result file handle",
      "source": "=batchTransformResult",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the batch job fails",
      "source": "=Error",
      "var": "error"
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "ECS.BatchTransform"
  }
}
```

Notes:

- `inputs.outputColumns` is an **array of objects** with exactly the keys `name` and `description`. Do not flatten to a map (`{ Category: "...", Summary: "..." }`) — the canvas editor and the BPMN serializer expect the array shape.
- `model.bindings` is **absent** — Batch Transform is not a process or connector node; there is nothing to bind.
- `outputs.output.source` is the literal `=batchTransformResult` — do not rewrite to `=result.output` or similar.

## Accessing Output

The result is a file handle, not the transformed rows themselves. To use the new columns downstream, feed the handle to another node that consumes files (another Batch Transform, a connector that uploads, a Script that parses):

```javascript
// Downstream Script node
const resultFile = $vars.categorizeRows.output; // { id, fileName, mimeType }
return { resultFileId: resultFile.id };
```

If you need the rows as JSON inside the flow, add a downstream step that fetches and parses the file — Batch Transform itself never materializes rows into `$vars`.

## Validate

```bash
uip maestro flow validate <FlowName>.flow --output json
```

The validator checks that required inputs (`attachment`, `prompt`, `outputColumns`) are present and non-empty, and that `outputColumns` entries each have `name` and `description`.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.batch-transform` | CLI predates Patterns support, or tenant flag `canvas.nodes.patterns` is off | `uip cli update`, `uip maestro flow registry pull --force`; check with admin if still missing |
| Validate rejects `outputColumns` | Wrong shape — e.g., passed a map `{ name: description }` or string array | Rewrite to `[{ "name": "...", "description": "..." }, ...]` |
| Runtime error `exceeded maxColumns` | More than 10 output columns | Reduce to ≤10 or split into two Batch Transform nodes chained on the output file |
| All rows produce blank values for a column | `description` is too vague or references fields not in the source CSV | Tighten the `description` — name the source column(s) the LLM should read from; test with a small sample first |
| Latency spikes / higher cost than expected | `enableWebSearchGrounding: true` unnecessarily | Turn web search off unless rows need facts the LLM cannot infer from the row itself |
| Output file has original row count but no new columns | Prompt asked for transformations that duplicate source columns — the LLM skipped them | Make sure every `outputColumns[].name` is **new** (not already in the source CSV) |

## What NOT to Do

- **Do not hand-author `model.bindings`** on the node — Batch Transform has no process or connector binding. Adding a `bindings` block will be stripped or cause validate errors.
- **Do not pass `--source` on `uip maestro flow node add`** — `--source` is only for inline agent nodes (`uipath.agent.autonomous`). Batch Transform has no agent project behind it.
- **Do not reshape `outputColumns` to a map** — the array-of-`{name, description}` shape is contractual with the canvas property panel and the BPMN `ECS.BatchTransform` serializer.
- **Do not reference downstream rows inside the prompt** — each row is processed independently; there is no way to see sibling rows. Pre-aggregate or use [Summarize](../summarize/impl.md) on a synthesized document instead.
- **Do not chain a Batch Transform's `$vars.{nodeId}.output` directly into a Script expecting rows** — it is a file handle, not a row array.
