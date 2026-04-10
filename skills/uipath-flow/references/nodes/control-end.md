# End (`core.control.end`)

**Type:** `core.control.end`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:EndEvent`

## When to Use

Use an End node for graceful workflow completion. Each terminal path in the flow needs its own End node.

| Situation | Use End? |
|-----------|----------|
| Normal completion of an execution path | Yes |
| Flow has multiple terminal paths (each needs one) | Yes |
| Fatal error -- abort everything immediately | No -- use Terminate (`core.logic.terminate`) |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| left | `input` | target, `handleType: input`. No right-side ports -- this is a terminal node. |

## Inputs

None.

## Outputs

None. End nodes carry workflow-level output mappings (not node outputs). Every variable in `variables.globals` with direction `out` or `inOut` must have an output mapping on every reachable End node. See Instance Example for the `outputs` block format.

## Definition

```json
{
  "nodeType": "core.control.end",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "end", "finish", "complete"],
  "sortOrder": 20,
  "display": {
    "label": "End",
    "icon": "circle-check",
    "shape": "circle"
  },
  "handleConfiguration": [
    {
      "position": "left",
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        }
      ]
    }
  ],
  "model": {
    "type": "bpmn:EndEvent"
  }
}
```

## Instance Example

Without output mapping:

```json
{
  "id": "end_1",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 900, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "End"
  },
  "inputs": {},
  "outputs": {},
  "model": {
    "type": "bpmn:EndEvent"
  }
}
```

With output mapping (when workflow declares `out` variables):

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 900, "y": 200 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Done"
  },
  "inputs": {},
  "outputs": {
    "processedCount": {
      "source": "=js:$vars.processData.output.count"
    },
    "resultSummary": {
      "source": "=js:$vars.formatOutput.output.summary"
    }
  },
  "model": {
    "type": "bpmn:EndEvent"
  }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`.

## Common Mistakes

1. Forgetting to map `out` variables on End nodes. Every variable in `variables.globals` with direction `out` or `inOut` must have an output mapping on every reachable End node. Missing mappings cause silent runtime failures where the workflow completes but returns no data.
2. Confusing End with Terminate. End (`core.control.end`) stops a single branch. Terminate (`core.logic.terminate`) stops the entire workflow immediately, killing all parallel branches. Use End when other branches should continue executing.
3. Adding right-side (source/output) ports. End is a terminal node with only one left-side target port. It has no outgoing connections.
4. Omitting `model.type` from the node instance. The instance must include `"model": { "type": "bpmn:EndEvent" }` to compile correctly.
5. Output expression pointing to an unreachable node. The `$vars` reference in an output mapping must point to a node that is upstream and connected via edges. Verify the node is on the same execution path as this End node.
