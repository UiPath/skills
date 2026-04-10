# Terminate (`core.logic.terminate`)

**Type:** `core.logic.terminate`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:EndEvent` with `eventDefinition: "bpmn:TerminateEventDefinition"`

## When to Use

Use a Terminate node to abort the entire flow immediately on a fatal error. Unlike End, Terminate kills all branches.

| Situation | Use Terminate? |
|-----------|----------------|
| Fatal error -- continuing other branches would be harmful | Yes |
| Unrecoverable failure on an error-handling path | Yes |
| Normal completion of one execution path | No -- use End (`core.control.end`) |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| left | `input` | target, `handleType: input`. No right-side ports -- this is a terminal node. |

## Inputs

None.

## Outputs

None. Terminate does not produce workflow outputs. Use End for paths that need output mapping.

## Definition

```json
{
  "nodeType": "core.logic.terminate",
  "version": "1.0.0",
  "category": "control-flow",
  "tags": ["control-flow", "end", "stop"],
  "sortOrder": 99,
  "display": {
    "label": "Terminate",
    "icon": "circle-x",
    "shape": "square"
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
    "type": "bpmn:EndEvent",
    "eventDefinition": "bpmn:TerminateEventDefinition"
  }
}
```

## Instance Example

```json
{
  "id": "terminate_1",
  "type": "core.logic.terminate",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 900, "y": 400 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": {
    "label": "Terminate"
  },
  "inputs": {},
  "outputs": {},
  "model": {
    "type": "bpmn:EndEvent",
    "eventDefinition": "bpmn:TerminateEventDefinition"
  }
}
```

## Common Mistakes

1. Using Terminate when End is intended. Terminate kills the entire workflow immediately, including all parallel branches. If other branches should continue running, use End (`core.control.end`) instead.
2. Forgetting `eventDefinition` in the model. The node instance must include `"model": { "type": "bpmn:EndEvent", "eventDefinition": "bpmn:TerminateEventDefinition" }`. Without `eventDefinition`, the runtime treats it as a regular End event and only stops the current branch.
3. Adding right-side (source/output) ports. Terminate is a terminal node with only one left-side target port. It has no outgoing connections.
4. Placing Terminate in a subprocess. Terminate ends the top-level process. Placing it inside a subprocess may produce unexpected behavior -- use End to terminate a subprocess branch.
5. Expecting workflow outputs from a Terminate path. Terminate does not produce outputs. If the workflow needs to return data, route the path through an End node with output mapping instead.
