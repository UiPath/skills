# Subflow Node — Implementation

## Node Type

`core.subflow`

## Registry Validation

```bash
uip maestro flow registry get core.subflow --output json
```

Confirm: input port `input`, output ports `output` and `error`. Set the node instance `typeVersion` to the `version` field from this response — do not hardcode it.

## Parent Node JSON

```json
{
  "id": "subflow1",
  "type": "core.subflow",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "Add Numbers", "icon": "layers" },
  "inputs": {
    "a": 2,
    "b": 3
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the subflow",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the subflow fails",
      "source": "=result.Error",
      "var": "error"
    }
  }
}
```

## Subflow Definition

Subflow contents are stored in a top-level `subflows` object keyed by the parent node's ID:

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
          "inputs": {
            "entryPointId": "unique-uuid-here",
            "isDefaultEntryPoint": true
          },
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
          "inputs": {
            "script": "return { result: $vars.subflow1Start.output.a + $vars.subflow1Start.output.b };"
          },
          "outputs": {
            "output": {
              "type": "object",
              "description": "The return value of the script",
              "source": "=result.response",
              "var": "output"
            },
            "error": {
              "type": "object",
              "description": "Error information if the script fails",
              "source": "=result.Error",
              "var": "error",
              "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["code", "message", "detail", "category", "status"],
                "properties": {
                  "code": { "type": "string" },
                  "message": { "type": "string" },
                  "detail": { "type": "string" },
                  "category": { "type": "string" },
                  "status": { "type": "integer" }
                },
                "additionalProperties": false
              }
            }
          },
          "outputs": {
            "output": {
              "type": "object",
              "description": "The return value of the script",
              "source": "=result.response",
              "var": "output"
            },
            "error": {
              "type": "object",
              "description": "Error information if the script fails",
              "source": "=result.Error",
              "var": "error"
            }
          }
        },
        {
          "id": "subflow1End",
          "type": "core.control.end",
          "typeVersion": "1.0",
          "display": { "label": "End" },
          "inputs": {},
          "outputs": {
            "result": { "source": "=js:$vars.script1.output.result" }
          }
        }
      ],
      "edges": [
        {
          "id": "sf-e1",
          "sourceNodeId": "subflow1Start",
          "sourcePort": "output",
          "targetNodeId": "script1",
          "targetPort": "input"
        },
        {
          "id": "sf-e2",
          "sourceNodeId": "script1",
          "sourcePort": "success",
          "targetNodeId": "subflow1End",
          "targetPort": "input"
        }
      ],
      "variables": {
        "globals": [
          {
            "id": "a",
            "direction": "in",
            "type": "number",
            "defaultValue": 0,
            "triggerNodeId": "subflow1Start"
          },
          {
            "id": "b",
            "direction": "in",
            "type": "number",
            "defaultValue": 0,
            "triggerNodeId": "subflow1Start"
          },
          {
            "id": "result",
            "direction": "out",
            "type": "number",
            "defaultValue": 0
          }
        ],
        "nodes": []
      },
      "layout": {
        "nodes": {
          "subflow1Start": { "position": { "x": 200, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "script1":       { "position": { "x": 400, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
          "subflow1End":   { "position": { "x": 600, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false }
        }
      }
    }
  }
}
```

## Passing a Flow Input Into the Subflow

When the **parent flow** itself takes an input the caller supplies at trigger time (e.g. a
`text` to reverse) and forwards it into the subflow, the parent's `in` variable needs the
**same `triggerNodeId` treatment as a subflow `in` variable** (rule #3) — set it to the
parent's trigger node ID. Omitting it is a silent trap: `uip maestro flow validate` still
reports **Valid**, but at `flow debug` the trigger output is empty, the value arrives as
`null`, and the subflow script faults (e.g. `Cannot read property 'split' of null`).

**Parent flow `variables.globals`** — note `triggerNodeId` on the `in` variable:
```json
{
  "variables": {
    "globals": [
      { "id": "text", "direction": "in", "type": "string", "defaultValue": "", "triggerNodeId": "start" },
      { "id": "reversedText", "direction": "out", "type": "string", "defaultValue": "" }
    ]
  }
}
```

**Parent trigger + subflow node** — the subflow node reads the trigger output and maps it to
the subflow's `in` variable:
```json
{
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0",
      "inputs": { "entryPointId": "<uuid>", "isDefaultEntryPoint": true },
      "outputs": { "output": { "type": "object", "source": "=result.response", "var": "output" } }
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

Value flow: caller input `text` → (bound to `start` via the parent global's `triggerNodeId`)
→ `$vars.start.output.text` → subflow node input `text` → the subflow's own `in` variable
(with its **own** `triggerNodeId: "<subflowStart>"`) → `$vars.<subflowStart>.output.text`
inside the subflow. The parent `in` var and the subflow `in` var are **independent variables
in separate scopes**, joined only by the subflow node's `inputs` mapping; each needs its own
`triggerNodeId` pointing at its respective Start node.

## Subflow Rules

1. Every subflow **must** have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
2. Subflow `variables.globals` with `direction: "in"` map to the parent node's `inputs`
3. Subflow `in` variables **must** have `triggerNodeId` set to the subflow's Start node ID — this makes them accessible via `$vars.{startNodeId}.output.{varId}`
4. Subflow `variables.globals` with `direction: "out"` map to the parent node's outputs, accessible via `$vars.{subflowNodeId}.output` in the parent flow
5. Parent-scope `$vars` are **not** visible inside the subflow — pass values explicitly via inputs
6. Subflow nodes must have inline `outputs` defined on them (Start node needs `outputs.output`, Script nodes need `outputs.output` and `outputs.error`)
7. Subflows can be nested (subflow inside subflow), up to 3 levels
8. Each subflow has its own `nodes`, `edges`, `variables`, and `layout` sections
9. Subflow node positions go in the subflow's own `layout.nodes` — NOT in the top-level `layout.nodes`. Each subflow scope is independent.
10. When the **parent flow** takes an external input and forwards it to a subflow, the parent's `in` variable **must** also have `triggerNodeId` set to the parent's trigger node ID — the same rule as #3, one scope up. `uip maestro flow validate` does **not** catch its absence; the forwarded value silently arrives as `null` at runtime. See [Passing a Flow Input Into the Subflow](#passing-a-flow-input-into-the-subflow).

## Creating a Subflow

For the step-by-step procedure, see [Edit/Write: Create a subflow](../../editing-operations-json.md#create-a-subflow). Use the parent node JSON and subflow definition structures above for the node-specific fields.

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `$vars.inputData` undefined inside subflow script | Missing `triggerNodeId` on subflow `in` variable, or using `$vars.{varId}` directly | Add `triggerNodeId: "{startNodeId}"` to each `in` variable and access via `$vars.{startNodeId}.output.{varId}` |
| Subflow script sees `null` for a value forwarded from the parent (e.g. `Cannot read property 'split' of null`) | Parent flow's `in` variable is missing `triggerNodeId`, so the parent trigger output is empty and `null` is forwarded into the subflow | Add `triggerNodeId: "{parentStartNodeId}"` to the parent flow's `in` variable (same fix as the row above, but for the root flow) |
| `$vars.parentNode` undefined inside subflow | Parent scope not accessible | Pass values via subflow `in` variables |
| Subflow output is null | Missing output mapping on subflow's End node | Map all `out` variables in the End node's `outputs` |
| Script output is null | Missing inline `outputs` on script node | Add `outputs.output` and `outputs.error` inline on the script node |
| Missing Start/End node | Subflow lacks required trigger or end | Add `core.trigger.manual` (with `outputs` and `entryPointId`) and `core.control.end` to the subflow |
| Nesting limit exceeded | Subflow nested more than 3 levels deep | Flatten the structure or use resource nodes for deeper composition |
