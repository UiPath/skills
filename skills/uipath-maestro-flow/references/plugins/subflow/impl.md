# Subflow Node — Implementation

## Node Type

`core.subflow`

## Registry Validation

```bash
uip flow registry get core.subflow --output json
```

Confirm: input port `input`, output ports `output` and `error`.

## Parent Node JSON

```json
{
  "id": "subflow1",
  "type": "core.subflow",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 432, "y": 144 },
    "size": { "width": 96, "height": 96 }
  },
  "display": { "label": "Validate & Transform" },
  "inputs": {
    "inputData": "=js:$vars.fetchData.output.body",
    "threshold": 100
  },
  "model": { "type": "bpmn:SubProcess" }
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
          "typeVersion": "1.0.0",
          "display": { "label": "Start" },
          "inputs": {},
          "model": { "type": "bpmn:StartEvent" }
        },
        {
          "id": "validate",
          "type": "core.action.script",
          "typeVersion": "1.0.0",
          "display": { "label": "Validate" },
          "inputs": {
            "script": "const data = $vars.inputData;\nif (!data || !data.items) throw new Error('Invalid data');\nreturn { valid: true, count: data.items.length };"
          },
          "model": { "type": "bpmn:ScriptTask" }
        },
        {
          "id": "subflow1End",
          "type": "core.control.end",
          "typeVersion": "1.0.0",
          "display": { "label": "End" },
          "inputs": {},
          "outputs": {
            "result": { "source": "=js:$vars.validate.output" }
          },
          "model": { "type": "bpmn:EndEvent" }
        }
      ],
      "edges": [
        {
          "id": "sf-e1",
          "sourceNodeId": "subflow1Start",
          "sourcePort": "output",
          "targetNodeId": "validate",
          "targetPort": "input"
        },
        {
          "id": "sf-e2",
          "sourceNodeId": "validate",
          "sourcePort": "success",
          "targetNodeId": "subflow1End",
          "targetPort": "input"
        }
      ],
      "variables": {
        "globals": [
          {
            "id": "inputData",
            "direction": "in",
            "type": "object"
          },
          {
            "id": "threshold",
            "direction": "in",
            "type": "number",
            "defaultValue": 50
          },
          {
            "id": "result",
            "direction": "out",
            "type": "object"
          }
        ],
        "nodes": []
      }
    }
  }
}
```

## Subflow Rules

1. Every subflow **must** have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
2. Subflow `variables.globals` with `direction: "in"` map to the parent node's `inputs`
3. Subflow `variables.globals` with `direction: "out"` map to the parent node's outputs, accessible via `$vars.{subflowNodeId}.output`
4. Parent-scope `$vars` are **not** visible inside the subflow — pass values explicitly via inputs
5. Subflows can be nested (subflow inside subflow), up to 3 levels
6. Each subflow has its own `nodes`, `edges`, and `variables` sections

## Creating a Subflow Step-by-Step

1. Add a `core.subflow` node to the parent flow's `nodes` array with `inputs` matching the subflow's `in` variables
2. Add a `subflows.{nodeId}` entry with its own `nodes`, `edges`, and `variables`
3. The subflow must have its own Start node (`core.trigger.manual`) and End node (`core.control.end`)
4. Define subflow inputs (`direction: "in"`) and outputs (`direction: "out"`) in `subflows.{nodeId}.variables.globals`
5. Map outputs on the subflow's End node
6. Validate: `uip flow validate`

## Debug

| Error | Cause | Fix |
| --- | --- | --- |
| `$vars.parentNode` undefined inside subflow | Parent scope not accessible | Pass values via subflow `in` variables |
| Subflow output is null | Missing output mapping on subflow's End node | Map all `out` variables in the End node's `outputs` |
| Missing Start/End node | Subflow lacks required trigger or end | Add `core.trigger.manual` and `core.control.end` to the subflow |
| Nesting limit exceeded | Subflow nested more than 3 levels deep | Flatten the structure or use resource nodes for deeper composition |
