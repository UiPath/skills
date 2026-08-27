# Subflow Node — Implementation

## Node Type and Registry Validation

`core.subflow`

Run:

```bash
uip maestro flow registry get core.subflow --output json
```

Confirm input port `input` and output ports `output` and `error`. Set the node instance `typeVersion` to the response's `version` field; do not hardcode it.

## Parent Node JSON

```json
{
  "id": "subflow1",
  "type": "core.subflow",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Add Numbers", "icon": "layers" },
  "inputs": { "a": 2, "b": 3 },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the subflow fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

Declare `error` only; `output` is derived. Do not author `output`: the converter copies its `source` verbatim, so `"=result.response"` resolves to null at runtime although `flow validate` passes. See [file-format.md § Node outputs](../../../../shared/file-format.md#node-outputs).

## Subflow Definition

Store definitions in a top-level `subflows` object keyed by the parent node ID. Each definition contains `nodes`, `edges`, `variables`, and `layout`:

```json
{
  "subflows": {
    "subflow1": {
      "nodes": [
        {
          "id": "subflow1Start",
          "type": "core.trigger.manual",
          "typeVersion": "1.0",
          "display": { "label": "Start" },
          "inputs": { "entryPointId": "<unique-uuid>", "isDefaultEntryPoint": true },
          "outputs": {
            "output": {
              "type": "object",
              "description": "Data passed when manually triggering the workflow.",
              "source": "null",
              "var": "output"
            }
          }
        },
        {
          "id": "script1",
          "type": "core.action.script",
          "typeVersion": "1.0",
          "display": { "label": "Add Numbers" },
          "inputs": { "script": "return { result: $vars.subflow1Start.output.a + $vars.subflow1Start.output.b };" },
          "outputs": {
            "output": { "type": "object", "description": "The return value of the script", "source": "=result.response", "var": "output" },
            "error": { "type": "object", "description": "Error information if the script fails", "source": "=Error", "var": "error" }
          }
        },
        {
          "id": "subflow1End",
          "type": "core.control.end",
          "typeVersion": "1.0",
          "display": { "label": "End" },
          "inputs": {},
          "outputs": { "result": { "source": "=js:$vars.script1.output.result" } }
        }
      ],
      "edges": [
        { "id": "sf-e1", "sourceNodeId": "subflow1Start", "sourcePort": "output", "targetNodeId": "script1", "targetPort": "input" },
        { "id": "sf-e2", "sourceNodeId": "script1", "sourcePort": "success", "targetNodeId": "subflow1End", "targetPort": "input" }
      ],
      "variables": {
        "globals": [
          { "id": "a", "direction": "in", "type": "number", "defaultValue": 0, "triggerNodeId": "subflow1Start" },
          { "id": "b", "direction": "in", "type": "number", "defaultValue": 0, "triggerNodeId": "subflow1Start" },
          { "id": "result", "direction": "out", "type": "number", "defaultValue": 0 }
        ],
        "nodes": []
      },
      "layout": {
        "nodes": {
          "subflow1Start": { "position": { "x": 200, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "script1": { "position": { "x": 400, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "subflow1End": { "position": { "x": 600, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false }
        }
      }
    }
  }
}
```

## Passing a Flow Input Into the Subflow

Set `triggerNodeId` on the parent's `in` variable when forwarding trigger input. Run `uip maestro flow validate`; do not treat **Valid** as proof that this is configured. Without `triggerNodeId`, `flow debug` shows an empty trigger output, forwards `null`, and may fault in the subflow (for example, `Cannot read property 'split' of null`).

```json
{
  "variables": {
    "globals": [
      { "id": "text", "direction": "in", "type": "string", "defaultValue": "", "triggerNodeId": "start" },
      { "id": "reversedText", "direction": "out", "type": "string", "defaultValue": "" }
    ]
  },
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0",
      "inputs": { "entryPointId": "<uuid>", "isDefaultEntryPoint": true },
      "outputs": { "output": { "type": "object", "description": "Data passed when manually triggering the process.", "source": "null", "var": "output" } }
    },
    {
      "id": "reverseSubflow",
      "type": "core.subflow",
      "typeVersion": "<DEFINITION_VERSION>",
      "inputs": { "text": "=js:$vars.start.output.text" }
    }
  ]
}
```

Value flow is: caller input `text` → parent `start` through the parent's `triggerNodeId` → `$vars.start.output.text` → subflow input `text` → the subflow's `in` variable → `$vars.<subflowStart>.output.text`. Parent and subflow `in` variables are independent; set `triggerNodeId` for each.

## Subflow Rules

1. Every subflow must have its own Start node (`core.trigger.manual`) and End node (`core.control.end`).
2. Subflow `variables.globals` with `direction: "in"` map to parent node `inputs`.
3. Subflow `in` variables must set `triggerNodeId` to the subflow Start node ID, enabling `$vars.{startNodeId}.output.{varId}`.
4. Subflow `variables.globals` with `direction: "out"` map to parent node outputs and are accessible as `$vars.{subflowNodeId}.output` in the parent.
5. Parent-scope `$vars` are not visible inside the subflow; pass values explicitly through inputs.
6. Define inline `outputs` on every subflow node: Start needs `outputs.output`; Script nodes need `outputs.output` and `outputs.error`.
7. Subflows may be nested up to 3 levels.
8. Each subflow has its own `nodes`, `edges`, `variables`, and `layout` sections.
9. Put subflow node positions in that subflow's `layout.nodes`, not the top-level `layout.nodes`; scopes are independent.
10. When the parent forwards an external input, its `in` variable must also set `triggerNodeId` to the parent trigger node ID. `uip maestro flow validate` does not detect this omission; the value silently arrives `null`. See [Passing a Flow Input Into the Subflow](#passing-a-flow-input-into-the-subflow).

## Creating a Subflow

For the procedure, see [Edit/Write: Create a subflow](../../editing-operations-json.md#create-a-subflow). Use the structures above for node-specific fields.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `$vars.inputData` undefined inside subflow script | Missing `triggerNodeId` on a subflow `in` variable, or direct use of `$vars.{varId}` | Set `triggerNodeId: "{startNodeId}"` on each `in` variable and use `$vars.{startNodeId}.output.{varId}` |
| Subflow script receives `null`, such as `Cannot read property 'split' of null` | Parent `in` variable lacks `triggerNodeId`, leaving parent trigger output empty | Set `triggerNodeId: "{parentStartNodeId}"` on the parent flow's `in` variable |
| `$vars.parentNode` undefined inside subflow | Parent scope is inaccessible | Pass values through subflow `in` variables |
| Subflow output is null | End node lacks output mapping | Map all `out` variables in the End node's `outputs` |
| Script output is null | Script lacks inline `outputs` | Add `outputs.output` and `outputs.error` inline |
| Missing Start/End node | Required trigger or end is absent | Add `core.trigger.manual` with `outputs` and `entryPointId`, plus `core.control.end` |
| Nesting limit exceeded | More than 3 levels of nesting | Flatten the structure or use resource nodes for deeper composition |