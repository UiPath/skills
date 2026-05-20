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
- `inputDefinition.properties` — `attachment` (declared `string`; runtime wants the **full Flow Attachment object** `{ FullName, Id, Metadata, MimeType }` — Studio Web's file-picker form serializes the whole object into that slot, the engine deserializes it back), `prompt` (string), `enableWebSearchGrounding` (boolean), `outputColumns` (array of `{ name, description }`)
- `outputDefinition.output.type` — `"file"`; `outputDefinition.output.source` — `"=response"` (the BPMN engine wraps the result under that key — same convention as every other ServiceTask)
- `outputDefinition.error.schema.required` — `code`, `message`, `detail`, `category`, `status`

If the command errors with **"Node type not found: uipath.pattern.batch-transform"**, the CLI build predates Batch Transform support or the tenant's `canvas.nodes.batch-transform` server flag is off. Run `uip tools update` and `uip maestro flow registry pull --force`; if it still errors, confirm with your UiPath admin that the `canvas.nodes.batch-transform` flag is enabled on the tenant.

## Adding / Editing

Pattern nodes are OOTB BPMN service tasks — author them by editing the `.flow` JSON directly (Edit/Write). This is the canonical authoring path per [Author capability, rule 2](../../../CAPABILITY.md): the `uip maestro flow node add` / `edge add` carve-out is reserved for connectors, connector-triggers, and managed HTTP, where the CLI populates product-managed state. For OOTB structural edits — adding the BT node, wiring its edges, adding the `attachment` flow input — use Edit/Write against the `.flow` file. See [editing-operations.md](../../editing-operations.md) for the JSON authoring mechanics; the snippets below cover what is **specific** to Batch Transform.

## Wiring `attachment` — file variable bound to the trigger

The canonical canvas-produced shape is a flow `in` variable of `type: "file"` bound to the trigger via `triggerNodeId`, with the BT node's `attachment` referencing it through the trigger's output:

```json
"variables": {
  "globals": [
    {
      "id": "csvFile",
      "direction": "in",
      "type": "file",
      "triggerNodeId": "start"
    }
  ]
}
```

Then on the BT node:

```json
"inputs": {
  "attachment": "=js:$vars.start.output.csvFile",
  ...
}
```

`uip maestro flow debug --file csvFile=./path/to/data.csv` populates that variable as a `{ FullName, Id, Metadata, MimeType }` Attachment object at runtime. Do not declare the variable as `type: "object"`, do not reference it as `=js:$vars.csvFile` directly without the trigger output path, and do not pass a bare GUID/URL/path/`.Id`/`.FullName`.

## JSON Structure

```json
{
  "id": "categorizeRows",
  "type": "uipath.pattern.batch-transform",
  "typeVersion": "1.0",
  "display": { "label": "Categorize Invoices" },
  "inputs": {
    "attachment": "=js:$vars.start.output.csvFile",
    "prompt": "Classify each invoice by category and write a one-line summary.",
    "enableWebSearchGrounding": false,
    "outputColumns": [
      { "name": "Category", "description": "One of: Utility, Software, Travel, Other" },
      { "name": "Summary",  "description": "Plain-English one-line summary of the invoice" }
    ]
  },
  "outputs": {
    "output": {
      "type": "file",
      "source": "=response",
      "var": "output"
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

- **No instance-level `model` block.** BPMN type and `serviceType: "ECS.BatchTransform"` live only in the corresponding `definitions[]` entry — copy that verbatim from `uip maestro flow registry get uipath.pattern.batch-transform --output json`. Per [Author capability, rule 16](../../../CAPABILITY.md), node instances normally have no `model` block.
- **`typeVersion` must match `definitions[<batch-transform>].version` exactly** — the registry currently emits `"1.0"` (one dot). Do not guess `"1.0.0"`.
- `inputs.outputColumns` is an **array of objects** with exactly the keys `name` and `description`. Do not flatten to a map (`{ Category: "...", Summary: "..." }`) — the canvas editor and the BPMN serializer expect the array shape.
- `outputs.output.source` is the literal **`=response`** (the convention every BPMN ServiceTask follows; the engine wraps its result under that key). Do not rewrite to `=batchTransformResult`, `=result.output`, or similar.
- `outputs.output.type` is **`"file"`**; the result is a file handle (not a row array).

## End-node output mapping

If the flow surfaces the result file handle as a flow `out` variable (e.g. `result`), the End node must map it. Per [Author capability, rule 12](../../../CAPABILITY.md), value-field expressions need the `=js:` prefix:

```json
{
  "id": "end",
  "type": "core.control.end",
  "typeVersion": "1.0",
  "outputs": {
    "result": { "source": "=js:$vars.categorizeRows.output" }
  }
}
```

Without `=js:`, the runtime stores the literal string `"$vars.categorizeRows.output"` into the flow output instead of the real value.

## Add via CLI (opt-in, not preferred)

The `uip maestro flow node add` / `edge add` CLI is **not** the canonical authoring path for OOTB pattern nodes (see rule 2 above). Reach for it only when scripting in a context where Edit/Write isn't available. The shape:

```bash
uip maestro flow node add <FlowName>.flow uipath.pattern.batch-transform \
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

`attachment` must resolve to a **full Flow Attachment object** (`{ FullName, Id, Metadata, MimeType }`). Reference it through the trigger's output (`$vars.<triggerId>.output.<fileVarId>`) — that's how the canvas wires file-typed flow `in` variables. Do **not** pass a bare GUID, URL, byte stream, or path; even though the OOTB `inputDefinition` declares `type: "string"`, the engine wants the object.

## Accessing Output

The result is a file handle, not the transformed rows themselves. Pass `$vars.{nodeId}.output` to a downstream node that consumes files (another Batch Transform, a connector that uploads, a Script that fetches and parses):

```javascript
// Downstream Script node
const resultFile = $vars.categorizeRows.output; // file handle
// Use the handle as the `attachment` input on a downstream Pattern node, or
// pass it to an HTTP/connector step that uploads or downloads the file.
return { resultFile };
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
| `Node type not found: uipath.pattern.batch-transform` | CLI predates Batch Transform support, or tenant flag `canvas.nodes.batch-transform` is off | `uip tools update`, `uip maestro flow registry pull --force`; check with admin that `canvas.nodes.batch-transform` is enabled if still missing |
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
- **Do not pass `attachment` as a bare string id, GUID, URL, or path.** The OOTB schema and Studio Web's file-picker UI suggest a string, but the runtime needs the **full Flow Attachment object** `{ FullName, Id, Metadata, MimeType }`. The canonical wiring is a flow `in` variable of `type: "file"` bound to the trigger via `triggerNodeId`, referenced as `=js:$vars.<triggerId>.output.<fileVarId>` (see Key Inputs in `planning.md`). Bare-id mistakes pass `flow validate` cleanly and fault at runtime.
- **Do not write `outputs.output.source: "=batchTransformResult"`.** The canonical value is `"=response"` (the convention every BPMN ServiceTask follows).
