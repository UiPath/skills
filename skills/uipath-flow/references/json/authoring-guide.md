# JSON Authoring Guide

Algorithms and patterns for directly editing `.flow` JSON files. This guide covers ID generation, `variables.nodes` regeneration, definition deduplication, and common JSON editing operations.

For the full `.flow` file schema, see [../flow-schema.md](../flow-schema.md).

---

## 1. ID Generation Algorithms

### Node ID Algorithm

1. Take the display label (or custom label) of the node.
2. Split on non-alphanumeric characters.
3. Join as camelCase (first word lowercase, remaining words capitalized).
4. Strip the `"createNew"` prefix if present.
5. Append a numeric suffix starting at `1`, incrementing until the ID is unique within the workflow.
6. Result examples: `sendMessage1`, `httpRequest1`, `decision2`

Node IDs must match `/^[a-zA-Z_][a-zA-Z0-9_]*$/` and must not be a JavaScript or Python reserved word.

### Edge ID Algorithm

Format: `{sourceId}-{sourcePort}-{targetId}-{targetPort}`

- Use `"default"` if a port is null.
- Append `-2`, `-3`, etc. on collision with an existing edge ID.
- Example: `start-output-httpRequest1-input`

### Binding ID Algorithm

Format: `b` + 8 random alphanumeric characters.

Example: `bXk9mNpQr`

Used for entries in the `workflow.bindings` array when connecting resource nodes (RPA workflows, agents, API workflows, agentic processes) to their Orchestrator artifacts.

---

## 2. `variables.nodes` Regeneration (Critical)

> **Every time a node is added or removed, you MUST regenerate `workflow.variables.nodes` from scratch.** Failing to do this produces a broken flow that will not run. In CLI mode, `node add` does NOT update this array -- you must do it manually.

### Algorithm

1. For each node in `workflow.nodes`:
   a. Check if the node instance has `outputs` defined.
   b. If not, fall back to the matching definition's `outputDefinition`.
   c. For each output key, emit a `NodeVariable`:
      ```json
      {
        "id": "<NODE_ID>.<OUTPUT_KEY>",
        "type": "<OUTPUT_TYPE>",
        "description": "<FROM_OUTPUT_IF_PRESENT>",
        "schema": "<FROM_OUTPUT_IF_PRESENT>",
        "binding": { "nodeId": "<NODE_ID>", "outputId": "<OUTPUT_KEY>" }
      }
      ```
      Include `description` when the output source has one. Include `schema` when the output source has one (common on error outputs).
2. Replace `workflow.variables.nodes` entirely with the regenerated array.

### Concrete Example

Given a flow with:
- A manual trigger node (`start`) with one output (`output`)
- A script node (`myScript`) with two outputs (`output`, `error`)

The regenerated `variables.nodes` array:

```json
"nodes": [
  {
    "id": "start.output",
    "type": "object",
    "description": "Trigger output",
    "binding": { "nodeId": "start", "outputId": "output" }
  },
  {
    "id": "myScript.output",
    "type": "object",
    "description": "Script result",
    "binding": { "nodeId": "myScript", "outputId": "output" }
  },
  {
    "id": "myScript.error",
    "type": "object",
    "description": "Error information if the script fails",
    "schema": { "$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "..." : "..." },
    "binding": { "nodeId": "myScript", "outputId": "error" }
  }
]
```

> The `schema` field on `myScript.error` comes from the output definition's `schema` property. See `minimal-flow-template.json` for the full schema object.

### Where to find output keys

| Source | How to find outputs |
|--------|-------------------|
| Node instance `outputs` field | `node.outputs` object -- each key is an output |
| Definition `outputDefinition` | `definition.outputDefinition` -- each key is an output name |

If a node instance has explicit `outputs`, use those. Otherwise, fall back to the definition's `outputDefinition`.

---

## 3. Definition Deduplication

`workflow.definitions` is deduplicated by a `nodeType:version` composite key.

### When adding a node

Skip the definition insert if a definition with the same `nodeType` + `version` already exists in the array. Two script nodes share one definition. Two different connector node types each need their own definition.

### When removing a node

Remove the definition only if no other node in `workflow.nodes` uses the same `type:typeVersion` combination.

### Example

If the flow has two `core.action.script` nodes (v1.0.0), there is only ONE definition entry with `nodeType: "core.action.script"`, `version: "1.0.0"`. Removing one script node keeps the definition. Removing both removes it.

---

## 4. Where to Find Definition Blocks

Definition blocks must be copied verbatim. Never hand-write them.

> **Source of truth:** Node reference files (`../nodes/*.md`) and fresh `registry get` output are the authoritative definition sources. Template JSON files contain point-in-time snapshots of definitions for structural reference — when adding a node, always copy from the node reference file (OOTB) or fresh `registry get` output (dynamic), not from a template.

### OOTB nodes

Read the node's reference file in `../nodes/<type>.md`. Each file contains the full definition block ready to copy into `workflow.definitions`.

| Node | Reference file |
|------|---------------|
| Manual trigger | [../nodes/trigger-manual.md](../nodes/trigger-manual.md) |
| Scheduled trigger | [../nodes/trigger-scheduled.md](../nodes/trigger-scheduled.md) |
| Script | [../nodes/action-script.md](../nodes/action-script.md) |
| HTTP Request | [../nodes/action-http.md](../nodes/action-http.md) |
| Decision | [../nodes/logic-decision.md](../nodes/logic-decision.md) |
| Switch | [../nodes/logic-switch.md](../nodes/logic-switch.md) |
| Loop | [../nodes/logic-loop.md](../nodes/logic-loop.md) |
| For Each | [../nodes/logic-foreach.md](../nodes/logic-foreach.md) |
| While | [../nodes/logic-while.md](../nodes/logic-while.md) |
| Merge | [../nodes/logic-merge.md](../nodes/logic-merge.md) |
| Transform | [../nodes/action-transform.md](../nodes/action-transform.md) |
| Filter | [../nodes/action-transform-filter.md](../nodes/action-transform-filter.md) |
| Delay | [../nodes/logic-delay.md](../nodes/logic-delay.md) |
| End | [../nodes/control-end.md](../nodes/control-end.md) |
| Terminate | [../nodes/control-terminate.md](../nodes/control-terminate.md) |
| Mock | [../nodes/logic-mock.md](../nodes/logic-mock.md) |
| HITL | [../nodes/hitl.md](../nodes/hitl.md) |

### Dynamic nodes (connectors, resources)

Use `uip flow registry get` to fetch the definition at authoring time:

```bash
uip flow registry get <NODE_TYPE> --output json
```

The `Data.Node` object in the response is the definition block. Copy it verbatim into `workflow.definitions`.

For connector nodes, pass `--connection-id` for enriched metadata:

```bash
uip flow registry get <NODE_TYPE> --connection-id <CONNECTION_ID> --output json
```

See [../connectors/connector-guide.md](../connectors/connector-guide.md) for the full connector configuration workflow. See [../dynamic-nodes/resource-node-guide.md](../dynamic-nodes/resource-node-guide.md) for the resource node workflow.

---

## 5. JSON Editing Patterns

Common operations when editing `.flow` files directly.

### Adding to arrays

Nodes, edges, and definitions are stored as JSON arrays. To add a new entry, append to the end of the array.

**Add a node to `workflow.nodes`:**

```json
{
  "id": "myScript1",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  "display": { "label": "Process Data" },
  "inputs": {
    "script": "const items = $vars.start.output.items;\nreturn { count: items.length };"
  },
  "ui": { "position": { "x": 400, "y": 300 } }
}
```

**Add an edge to `workflow.edges`:**

```json
{
  "id": "start-output-myScript1-input",
  "sourceNodeId": "start",
  "sourcePort": "output",
  "targetNodeId": "myScript1",
  "targetPort": "input"
}
```

**Add a definition to `workflow.definitions`:**

Copy the full definition block from the node's reference file or registry output. Check deduplication first -- skip if `nodeType:version` already exists.

### Removing from arrays

**Remove a node:**

1. Delete the node object from `workflow.nodes`.
2. Delete ALL edges from `workflow.edges` where `sourceNodeId` or `targetNodeId` matches the removed node's `id`.
3. Delete the definition from `workflow.definitions` only if no other node uses the same `type:typeVersion`.
4. Regenerate `workflow.variables.nodes` (section 2 above).

**Remove an edge:**

Delete the edge object from `workflow.edges`. No other cleanup needed unless the edge removal orphans a node (check item 14 of the [validation checklist](../validation-guide.md)).

### Updating nested fields

**Change a script body:**

Locate the node in `workflow.nodes` by its `id`, then update `inputs.script`:

```json
{
  "id": "myScript1",
  "inputs": {
    "script": "const data = $vars.fetchData.output;\nreturn { total: data.items.reduce((a, b) => a + b.amount, 0) };"
  }
}
```

**Change an expression:**

Locate the node, update the relevant `inputs` field. All expressions must start with `=js:`:

```json
{
  "id": "decision1",
  "inputs": {
    "expression": "$vars.httpRequest1.output.statusCode === 200"
  }
}
```

**Add output mapping on an End node:**

Locate the End node, add or update the `outputs` object:

```json
{
  "id": "end1",
  "type": "core.control.end",
  "outputs": {
    "output": {
      "result": { "source": "=js:$vars.myScript1.output.total" }
    }
  }
}
```

Every `out` variable in `workflow.variables.globals` must have a corresponding `source` expression in every reachable End node's `outputs`.

**Add a variable update:**

Add to `workflow.variables.variableUpdates` keyed by node ID:

```json
{
  "variableUpdates": {
    "myScript1": [
      { "variableId": "counter", "expression": "=js:$vars.counter + 1" }
    ]
  }
}
```

The target variable must exist in `workflow.variables.globals` with `direction: "inout"`.
