# Batch Transform Pattern Node — Implementation

Batch Transform runs an LLM row-by-row over an attached CSV and appends LLM-generated columns. Node type: `uipath.pattern.batch-transform`; BPMN service task with `serviceType: "ECS.BatchTransform"`. It has no process or connection bindings; inputs are the only configuration source.

## Registry validation

Run:

```bash
uip maestro flow registry get uipath.pattern.batch-transform --output json
```

Confirm:

- Input port: `input`.
- Output ports: `output`, `error`.
- `model.type`: `bpmn:ServiceTask`.
- `model.serviceType`: `ECS.BatchTransform`.
- `inputDefinition.properties`: `attachment` (declared `string`, but runtime requires the full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; keys are case-sensitive and `ID` is uppercase), `prompt` (string), `enableWebSearchGrounding` (boolean), and `outputColumns` (array of `{ name, description }`). Studio Web's file-picker form serializes the whole object into `attachment` and the engine deserializes it back.
- `outputDefinition.output.type`: `"file"`.
- `outputDefinition.output.source`: `"=response"` (the BPMN engine wraps the result under that key, as for every ServiceTask).
- `outputDefinition.error.schema.required`: `code`, `message`, `detail`, `category`, `status`.

If the command reports **"Node type not found: uipath.pattern.batch-transform"**, run `uip tools update` and `uip maestro flow registry pull --force`. If it still fails, confirm with the UiPath admin that the tenant's `canvas.nodes.batch-transform` server flag is enabled.

## Add or edit the node

Pattern nodes are OOTB BPMN service tasks and are **user-owned** per [Author capability — Node ownership](../../../CAPABILITY.md#node-ownership--who-authors-the-node). Author them by editing the `.flow` JSON directly with Edit/Write. The `uip maestro flow node add` / `edge add` CLI is reserved for CLI-owned nodes such as connectors, connector-triggers, and managed HTTP. Use Edit/Write for OOTB structural edits—adding the node, wiring edges, and adding the `attachment` flow input. See [editing-operations.md](../../editing-operations.md) for JSON authoring mechanics.

## Attachment wiring

Declare a flow `in` variable of `type: "file"` bound to the trigger by `triggerNodeId`:

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

Reference it through the trigger output:

```json
"attachment": "=js:$vars.start.output.csvFile"
```

Populate it by running `uip maestro flow debug --attachment <variableId>=<localPath>` (for example, `--attachment csvFile=./path/to/data.csv`). The flag is repeatable; `<variableId>` must match a `variables.globals[]` entry's `id`. See [cli-commands.md — Pre-flight](../../../../shared/cli-commands.md#pre-flight---attachment-binding). The CLI uploads the file and binds a full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`; `ID` is uppercase, not `Id`.

Do not declare the variable as `type: "object"`, reference it directly as `=js:$vars.<variableId>` without the trigger output path, or pass a bare GUID, URL, path, `.ID`, or `.FullName`.

## JSON structure

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
      { "name": "Summary", "description": "Plain-English one-line summary of the invoice" }
    ]
  },
  "outputs": {
    "output": { "type": "file", "source": "=response", "var": "output" },
    "error": {
      "type": "object",
      "description": "Error information if the node fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Rules:

- Do not add an instance-level `model` block. BPMN type and `serviceType: "ECS.BatchTransform"` belong only in the corresponding `definitions[]` entry; copy that entry verbatim from `uip maestro flow registry get uipath.pattern.batch-transform --output json`. Per [Author capability, rule 15](../../../CAPABILITY.md), node instances normally have no `model` block.
- Set `typeVersion` exactly to `definitions[<batch-transform>].version` from the registry response. Do not guess; use the registry's exact single-dot `x.y` form, such as `"1.0"`, not `"1.0.0"`.
- `inputs.outputColumns` must be an array of objects with exactly `name` and `description`; do not use a map or string array.
- Set `outputs.output.source` to the literal `=response`, not `=batchTransformResult`, `=result.output`, or another value.
- Set `outputs.output.type` to `"file"`; the result is a file handle, not a row array.

## End-node output mapping

When exposing the result through a flow `out` variable, map the file handle with an `=js:` value expression. Per [Author capability, rule 11](../../../CAPABILITY.md), use:

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

Without `=js:`, the runtime stores the literal string `"$vars.categorizeRows.output"`.

## Add via CLI (opt-in, not preferred)

The `uip maestro flow node add` / `edge add` CLI is not canonical for OOTB pattern nodes because they are user-owned. Use it only when scripting where Edit/Write is unavailable:

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

`attachment` must resolve through `$vars.<triggerId>.output.<fileVarId>` to the full Flow Attachment object `{ ID, FullName, MimeType, Metadata }`, with case-sensitive keys and uppercase `ID`. Do not pass a bare GUID, URL, byte stream, or path, even though the OOTB `inputDefinition` declares `type: "string"`.

## Output access

`$vars.{nodeId}.output` is a file handle, not transformed rows. Pass it to a downstream file-consuming node, such as another Batch Transform, an upload/download HTTP or connector step, or a Script that fetches and parses it:

```javascript
const resultFile = $vars.categorizeRows.output;
return { resultFile };
```

To obtain rows as JSON, add a downstream step that fetches and parses the file. Batch Transform never materializes rows into `$vars`.

## Validate

Run:

```bash
uip maestro flow validate <FlowName>.flow --output json
```

The validator checks that `attachment`, `prompt`, and `outputColumns` are present and non-empty, and that each `outputColumns` entry has `name` and `description`. It may not catch a bare attachment identifier; such mistakes can pass validation and fail at runtime.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `Node type not found: uipath.pattern.batch-transform` | CLI predates Batch Transform support, or tenant flag `canvas.nodes.batch-transform` is off | Run `uip tools update`, then `uip maestro flow registry pull --force`; if still missing, check with the admin that `canvas.nodes.batch-transform` is enabled |
| Validate rejects `outputColumns` | Wrong shape, such as a map `{ name: description }` or string array | Use `[{ "name": "...", "description": "..." }, ...]` |
| Runtime error `exceeded maxColumns` | More than 10 output columns | Reduce to ≤10 or split across two Batch Transform nodes chained on the output file |
| All rows produce blank values for a column | `description` is vague or references fields absent from the source CSV | Name the source column(s) in the description and test with a small sample |
| Latency spikes / higher cost than expected | `enableWebSearchGrounding: true` is unnecessary | Set it to false unless rows need facts the LLM cannot infer from the row itself |
| Output file has the original row count but no new columns | Requested transformations duplicate source columns, so the LLM skipped them | Ensure every `outputColumns[].name` is new and not already in the source CSV |

## What not to do

- Do not hand-author `model.bindings`; Batch Transform has no process or connector binding. A `bindings` block may be stripped or cause validation errors.
- Do not pass `--source` to `uip maestro flow node add`; `--source` is only for inline agent nodes (`uipath.agent.autonomous`).
- Do not reshape `outputColumns` into a map; the array of `{name, description}` is contractual with the canvas property panel and BPMN `ECS.BatchTransform` serializer.
- Do not reference downstream rows inside the prompt; rows are processed independently and sibling rows are unavailable. Pre-aggregate or use [Summarize](../summarize/impl.md) on a synthesized document instead.
- Do not chain `$vars.{nodeId}.output` directly into a Script expecting rows; it is a file handle.
- Do not pass `attachment` as a bare string id, GUID, URL, or path. The runtime requires `{ ID, FullName, MimeType, Metadata }`, with uppercase `ID`; use a `type: "file"` flow `in` variable bound by `triggerNodeId` and reference it as `=js:$vars.<triggerId>.output.<fileVarId>` (see Key Inputs in `planning.md).
- Do not write `outputs.output.source: "=batchTransformResult"`; the canonical value is `"=response"`, as for every BPMN ServiceTask.