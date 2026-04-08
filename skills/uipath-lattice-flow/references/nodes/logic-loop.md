# Loop

**Type:** `core.logic.loop`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:SubProcess`

Supports error handling (`supportsErrorHandling: true`).

## Ports

| Position | Handle ID | Type | Notes |
|----------|-----------|------|-------|
| left | `input` | target | Main entry point. Custom top offset: 32px. |
| left | `loopBack` | target | Loop body wires back here to continue iteration. Custom top offset: 32px. |
| right | `success` | source | Exits the loop after all iterations complete. Custom top offset: -32px. |
| right | `output` | source | Label "loop". Connects to the loop body (first node inside the loop). Custom top offset: -32px. |

The `error` port appears when error handling is enabled on this node.

## Inputs

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection` | string | Yes | `""` | Expression resolving to the array to iterate (e.g., `$vars.scriptTask1.output`) |
| `parallel` | boolean | No | `false` | When true, execute all iterations concurrently |

## Outputs

| Key | Type | Scope | Description | Source Expression |
|-----|------|-------|-------------|------------------|
| `currentItem` | any | internal | The current item being iterated | `=loopContext.currentItem` |
| `currentIndex` | number | internal | The current iteration index (0-based) | `=loopContext.currentIndex` |
| `collection` | array | internal | The collection being iterated over | `=loopContext.collection` |
| `output` | array | external | Aggregated results from all loop iterations | `=loopContext.output` |

**Scope rules:**
- `internal` -- available only to nodes inside the loop body (between `output` port and `loopBack` port).
- `external` -- available to nodes downstream of the `success` port, after the loop completes.

## Definition Block

Copy this verbatim into the `definitions` array (do not modify):

```json
{
  "nodeType": "core.logic.loop",
  "version": "1.0.0",
  "tags": ["control-flow", "loop", "iteration"],
  "sortOrder": 4,
  "supportsErrorHandling": true,
  "display": {
    "label": "Loop",
    "icon": "repeat",
    "description": "Execute a sequence of actions repeatedly for each item in a collection"
  },
  "category": "control-flow",
  "handleConfiguration": [
    {
      "position": "left",
      "customPositionAndOffsets": {
        "top": 32
      },
      "handles": [
        {
          "id": "input",
          "type": "target",
          "handleType": "input"
        },
        {
          "id": "loopBack",
          "type": "target",
          "handleType": "input"
        }
      ]
    },
    {
      "position": "right",
      "customPositionAndOffsets": {
        "top": -32
      },
      "handles": [
        {
          "id": "success",
          "label": "success",
          "type": "source",
          "handleType": "output",
          "visible": true
        },
        {
          "id": "output",
          "label": "loop",
          "type": "source",
          "handleType": "output",
          "showButton": false
        }
      ]
    }
  ],
  "model": {
    "type": "bpmn:SubProcess"
  },
  "inputDefinition": {
    "type": "object",
    "properties": {
      "collection": { "type": "string", "minLength": 1, "errorMessage": "A collection is required for iteration" },
      "parallel": { "type": "boolean" }
    },
    "required": ["collection"]
  },
  "inputDefaults": {
    "collection": "",
    "parallel": false
  },
  "outputDefinition": {
    "currentItem": {
      "type": "any",
      "description": "The current item being iterated in the loop",
      "source": "=loopContext.currentItem",
      "var": "currentItem",
      "scope": "internal"
    },
    "currentIndex": {
      "type": "number",
      "description": "The current iteration index (0-based)",
      "source": "=loopContext.currentIndex",
      "var": "currentIndex",
      "scope": "internal"
    },
    "collection": {
      "type": "array",
      "description": "The collection being iterated over",
      "source": "=loopContext.collection",
      "var": "collection",
      "scope": "internal"
    },
    "output": {
      "type": "array",
      "description": "Aggregated results from all loop iterations",
      "source": "=loopContext.output",
      "var": "output",
      "scope": "external"
    }
  },
  "form": {
    "id": "loop-properties",
    "title": "Loop configuration",
    "sections": [
      {
        "id": "iteration",
        "title": "Iteration",
        "fields": [
          {
            "name": "inputs.collection",
            "type": "custom",
            "component": "code-editor",
            "label": "Collection",
            "description": "Array or collection to iterate over (e.g., $vars.scriptTask1.output)",
            "componentProps": {
              "singleLine": true,
              "mode": "expression",
              "toggleable": false,
              "placeholder": "e.g., $vars.scriptTask1.output",
              "showVariableButton": true,
              "language": "javascript"
            },
            "validation": {
              "required": true,
              "messages": {
                "required": "A collection is required for iteration"
              }
            }
          },
          {
            "name": "inputs.parallel",
            "type": "switch",
            "label": "Parallel",
            "description": "Execute all iterations at the same time."
          }
        ]
      }
    ]
  }
}
```

## Node Instance Example

```json
{
  "id": "loop_1",
  "type": "core.logic.loop",
  "position": { "x": 400, "y": 200 },
  "data": {
    "inputs": {
      "collection": "$vars.fetchRecords.output",
      "parallel": false
    }
  }
}
```

Wiring pattern for a loop with one body node:

```json
[
  { "source": "loop_1", "sourceHandle": "output", "target": "bodyNode_1", "targetHandle": "input" },
  { "source": "bodyNode_1", "sourceHandle": "output", "target": "loop_1", "targetHandle": "loopBack" },
  { "source": "loop_1", "sourceHandle": "success", "target": "nextNode_1", "targetHandle": "input" }
]
```

## Common Mistakes

- Wiring to the `success` port from inside the loop body instead of connecting back to `loopBack`. The loop body's last node must connect to `loopBack` to continue iteration; `success` is the exit port after all iterations finish.
- Accessing `currentItem`, `currentIndex`, or `collection` outputs outside the loop body. These have `internal` scope and are only available to nodes wired between the `output` and `loopBack` ports.
- Leaving the `collection` input empty. The node requires a non-empty expression that resolves to an iterable array.
- Confusing the `output` port (label "loop") with the `success` port. The `output` port starts the loop body; the `success` port continues the flow after the loop ends.
- Forgetting to wire the `success` port. After the loop finishes all iterations, execution continues through `success` -- without a connection, the flow dead-ends.
