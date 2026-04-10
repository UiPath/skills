# Loop (`core.logic.loop`)

**Type:** `core.logic.loop`  **Version:** `1.0.0`  **Category:** control-flow
**BPMN Model:** `bpmn:SubProcess`

`supportsErrorHandling: true`

## When to Use

Use a Loop node to iterate over a collection of items. Supports sequential and parallel execution.

| Situation | Use Loop? |
|-----------|-----------|
| Process each item in an array | Yes |
| Run the same operation on multiple inputs concurrently | Yes (with `parallel: true`) |
| Simple data transformation on a collection (filter/map/groupBy) | No -- use a Transform node |
| Distribute work items to robots | No -- use a Queue node |

## Ports

| Direction | Port ID | Notes |
|-----------|---------|-------|
| input | `input` | Main entry point. Custom top offset: 32px. |
| input | `loopBack` | Loop body wires back here to continue iteration. Custom top offset: 32px. |
| output | `success` | Exits the loop after all iterations complete. Custom top offset: -32px. |
| output | `output` | Label "loop". Connects to the loop body (first node inside the loop). Custom top offset: -32px. |

The `error` port appears when error handling is enabled on this node.

## Inputs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `collection` | string | Yes | Default `""`. Expression resolving to the array to iterate (e.g., `$vars.fetchRecords.output`). |
| `parallel` | boolean | No | Default `false`. When true, execute all iterations concurrently. |

## Outputs

| Key | Type | Scope | Source Expression |
|-----|------|-------|-------------------|
| `currentItem` | any | internal | `=loopContext.currentItem` -- the current item being iterated |
| `currentIndex` | number | internal | `=loopContext.currentIndex` -- the current iteration index (0-based) |
| `collection` | array | internal | `=loopContext.collection` -- the collection being iterated over |
| `output` | array | external | `=loopContext.output` -- aggregated results from all loop iterations |

**Scope rules:**
- `internal` -- available only to nodes inside the loop body (between the `output` port and the `loopBack` port).
- `external` -- available to nodes downstream of the `success` port, after the loop completes.

## Definition

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

## Instance Example

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

1. Wiring to the `success` port from inside the loop body instead of connecting back to `loopBack`. The loop body's last node must connect to `loopBack` to continue iteration; `success` is the exit port after all iterations finish.
2. Accessing `currentItem`, `currentIndex`, or `collection` outputs outside the loop body. These have `internal` scope and are only available to nodes wired between the `output` and `loopBack` ports.
3. Leaving the `collection` input empty. The node requires a non-empty expression that resolves to an iterable array.
4. Confusing the `output` port (label "loop") with the `success` port. The `output` port starts the loop body; the `success` port continues the flow after the loop ends.
5. Forgetting to wire the `success` port. After the loop finishes all iterations, execution continues through `success` -- without a connection, the flow dead-ends.
6. Referencing `iterator` outside the loop body. The `iterator` / loop context variables (`currentItem`, `currentIndex`, `collection`) are only available inside the loop body.
7. Creating cycles through arbitrary edges rather than using the `loopBack` mechanism. Only the `loopBack` port should create the iteration cycle.
8. Collection evaluating to null or undefined at runtime. Verify the `collection` expression points to a valid upstream output that produces an array.
