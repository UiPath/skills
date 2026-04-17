# Flow Editing Operations — Direct JSON Strategy

All flow file modifications via direct read-modify-write of the `.flow` JSON file. This strategy gives full control over every field but requires manual management of definitions, variables, and edge integrity.

> **When to use this strategy:** Use for operations the CLI does not support (variables, variableUpdates, subflows, output mapping) or when you prefer direct file control. See [flow-editing-operations.md](flow-editing-operations.md) for the strategy selection matrix.

---

## Key Differences from CLI

When editing the `.flow` file directly, **you** are responsible for everything the CLI normally handles:

| Concern | CLI handles | Direct JSON — you must |
|---------|------------|------------------------|
| Definitions | Auto-copied from registry cache | Copy `Data.Node` from `uip flow registry get` into `definitions` array |
| Node variables | Auto-added to `variables.nodes` | Add output variable entries manually (or accept that `variables.nodes` may need regeneration) |
| Edge cleanup on delete | Auto-removes connected edges | Find and remove all edges referencing the deleted node |
| Orphan cleanup | Auto-removes unused definitions and orphaned bindings | Remove definitions no longer referenced by any node; remove connector bindings only when no remaining node uses that connector |
| `targetPort` | Auto-set | Set `targetPort` on every edge (validate rejects without it) |
| `bindings_v2.json` | Auto-managed by `node configure` | Edit `bindings_v2.json` manually for connector nodes |

---

## Primitive Operations

### Add a node

1. Run `uip flow registry get <NODE_TYPE> --output json` and copy the `Data.Node` object
2. Add a node entry to the `nodes` array:

```json
{
  "id": "<UNIQUE_NODE_ID>",
  "type": "<NODE_TYPE>",
  "typeVersion": "1.0.0",
  "display": { "label": "<LABEL>" },
  "inputs": {},
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the <node type>",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the <node type> fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "<BPMN_TYPE>" }
}
```

> **Node outputs are required.** Every node that produces data for downstream `$vars` references must include an `outputs` block. See [flow-file-format.md — Node outputs](flow-file-format.md#node-outputs) for the standard patterns by node category (action nodes get `output` + `error`; trigger nodes get `output` only; end/terminate nodes do not use this pattern).

> **No `ui` block on nodes.** Do NOT put `position`, `size`, or `collapsed` on the node. Add a layout entry instead (step 5).

3. Add the definition to `definitions` (if this type is not already present):
   - Paste the `Data.Node` object from the registry response
   - One definition per unique `type` — not one per node instance

4. Add node output variables to `variables.nodes` (optional — the CLI regenerates these, but direct builds should include them for completeness):

```json
{
  "nodeId": "<NODE_ID>",
  "outputs": [
    { "id": "output", "type": "object" },
    { "id": "error", "type": "object" }
  ]
}
```

5. Add a layout entry for the node in the top-level `layout.nodes` object:

```json
"layout": {
  "nodes": {
    "<UNIQUE_NODE_ID>": {
      "position": { "x": <X>, "y": <Y> },
      "size": { "width": 96, "height": 96 },
      "collapsed": false
    }
  }
}
```

**Layout rule:** Use horizontal layout — increasing `x` values left-to-right, consistent `y` baseline (e.g., `y: 144`). Space nodes ~200px apart on the x-axis.

### Delete a node

1. Remove the node object from `nodes`
2. Remove **all edges** where `sourceNodeId` or `targetNodeId` equals the node's `id`
3. If no other node uses the same `type`, remove the definition from `definitions`
4. Remove the node's entry from `variables.nodes`
5. Remove any `variableUpdates` entries keyed by the node's `id`
6. If the node is a connector node, remove its binding from `bindings_v2.json` **only if no other node in the flow uses the same connector**. Bindings are shared at the connector level (keyed by `metadata.Connector`), not per node.

### Add an edge

Add an edge object to the `edges` array:

```json
{
  "id": "<UNIQUE_EDGE_ID>",
  "sourceNodeId": "<SOURCE_NODE_ID>",
  "sourcePort": "<SOURCE_PORT>",
  "targetNodeId": "<TARGET_NODE_ID>",
  "targetPort": "<TARGET_PORT>"
}
```

**Critical:** `targetPort` is required on every edge. Omitting it produces a validation error.

See each plugin's `planning.md` or [flow-file-format.md — Standard ports](flow-file-format.md) for port names by node type.

### Delete an edge

Remove the edge object from the `edges` array by its `id`.

### Update node inputs

Edit the `inputs` object of the target node in-place. No need to delete and re-add.

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  }
}
```

This is a key advantage of direct JSON editing — input updates are a single field edit, not the delete + re-add pattern required by the CLI.

---

## Variable Operations

These are the same regardless of strategy — the CLI does not support variable management.

### Add a workflow variable

Add an entry to `variables.globals`:

```json
{
  "id": "<VARIABLE_ID>",
  "direction": "in|out|inout",
  "type": "string|number|boolean|object|array",
  "defaultValue": "<OPTIONAL_DEFAULT>",
  "description": "<OPTIONAL_DESCRIPTION>"
}
```

For `out` variables: add output mapping to **every reachable End node** (see below).
For `inout` variables: add `variableUpdates` entries on nodes that modify the state.

See [variables-and-expressions.md](variables-and-expressions.md) for the full schema, type system, and scoping rules.

### Add output mapping on an End node

Every `out` variable in `variables.globals` must be mapped on every reachable End node:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "inputs": {},
  "outputs": {
    "<VARIABLE_ID>": {
      "source": "=js:<EXPRESSION>"
    }
  }
}
```

Each key in `outputs` must match a variable `id` from `variables.globals` where `direction: "out"`. Missing mappings cause silent runtime failures.

### Add a variable update

Add an entry to `variables.variableUpdates.<NODE_ID>`:

```json
{
  "variables": {
    "variableUpdates": {
      "<NODE_ID>": [
        {
          "variableId": "<INOUT_VARIABLE_ID>",
          "expression": "=js:<EXPRESSION>"
        }
      ]
    }
  }
}
```

Only `inout` variables can be updated. `in` variables are read-only.

---

## Composite Operations

### Insert a node between two existing nodes

1. Remove the edge connecting the two nodes from the `edges` array
2. Add the new node to `nodes` (with definition in `definitions`)
3. Add two new edges:
   - upstream → new node (using upstream's output port → new node's `input`)
   - new node → downstream (using new node's output port → downstream's `input`)

### Insert a decision branch

1. Remove the edge where the branch should go
2. Add the decision node to `nodes` with `inputs.expression`
3. Add three edges:
   - upstream → decision (target port: `input`)
   - decision → true branch (source port: `true`, target port: `input`)
   - decision → false branch (source port: `false`, target port: `input`)

### Remove a node and reconnect

1. Record the node's upstream and downstream connections from `edges`
2. Remove the node from `nodes`
3. Remove all edges referencing the node
4. Clean up orphaned definitions
5. Add a new edge connecting upstream directly to downstream

### Replace a mock with a real resource node

1. Run `uip flow registry get "<RESOURCE_NODE_TYPE>" --output json`
2. Record the mock node's connected edges
3. Remove the mock node from `nodes`
4. Remove all edges referencing the mock
5. Add the real resource node to `nodes` with:
   - Correct `type` and `typeVersion`
   - `inputs` with resolved field values
   - `model.bindings` with `resourceSubType`, `resourceKey`, etc.
6. Copy the definition from registry into `definitions`
7. Re-create all edges using the new node's `id`
8. Add node variables to `variables.nodes`
9. Validate: `uip flow validate <ProjectName>.flow --output json`

### Replace manual trigger with scheduled trigger

Edit the start node in-place (no delete/re-add needed):

1. Change `type` from `core.trigger.manual` to `core.trigger.scheduled`
2. Add timer inputs:
   ```json
   "inputs": {
     "timerType": "timeCycle",
     "timerPreset": "R/PT1H"
   }
   ```
3. Add `eventDefinition` to `model`:
   ```json
   "model": {
     "type": "bpmn:StartEvent",
     "eventDefinition": "bpmn:TimerEventDefinition"
   }
   ```
4. Update the definition in `definitions`:
   - Remove the `core.trigger.manual` definition
   - Add the `core.trigger.scheduled` definition from `uip flow registry get core.trigger.scheduled --output json`
5. Validate: `uip flow validate <ProjectName>.flow --output json`

### Create a subflow

1. Add a `core.subflow` parent node to `nodes`:
   ```json
   {
     "id": "<SUBFLOW_NODE_ID>",
     "type": "core.subflow",
     "typeVersion": "1.0.0",
     "display": { "label": "<LABEL>" },
     "inputs": {
       "<IN_VAR>": "=js:<EXPRESSION>"
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
     },
     "model": { "type": "bpmn:SubProcess" }
   }
   ```

2. Add a `subflows.<SUBFLOW_NODE_ID>` entry with its own nodes, edges, and variables:
   ```json
   {
     "subflows": {
       "<SUBFLOW_NODE_ID>": {
         "nodes": [
           { "id": "sfStart", "type": "core.trigger.manual", ... },
           { "id": "sfEnd", "type": "core.control.end", ... }
         ],
         "edges": [ ... ],
         "variables": {
           "globals": [
             { "id": "<IN_VAR>", "direction": "in", "type": "..." },
             { "id": "<OUT_VAR>", "direction": "out", "type": "..." }
           ],
           "nodes": []
         }
       }
     }
   }
   ```

3. Subflow's `in` variables must match the parent node's `inputs` keys
4. Map all `out` variables on the subflow's End node `outputs`
5. Parent-scope `$vars` are NOT visible inside the subflow — pass values via inputs

See [subflow/impl.md](plugins/subflow/impl.md) for the full JSON structure and rules.

---

## Connector Node Configuration (Direct JSON)

When not using `uip flow node configure`, you must manually set up:

### 1. `inputs.detail` on the node

```json
{
  "inputs": {
    "detail": {
      "connectionId": "<CONNECTION_UUID>",
      "folderKey": "<FOLDER_KEY>",
      "method": "<HTTP_METHOD>",
      "endpoint": "<API_PATH>",
      "bodyParameters": { "<FIELD>": "<VALUE>" },
      "queryParameters": { "<FIELD>": "<VALUE>" }
    }
  }
}
```

The `method` and `endpoint` come from `connectorMethodInfo` in the `registry get --connection-id` response.

### 2. Connection binding in `bindings_v2.json`

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "<CONNECTION_UUID>",
      "id": "Connection<CONNECTION_UUID>",
      "value": {
        "ConnectionId": {
          "defaultValue": "<CONNECTION_UUID>",
          "isExpression": false,
          "displayName": "<CONNECTOR_KEY> connection"
        }
      },
      "metadata": {
        "ActivityName": "<ACTIVITY_DISPLAY_NAME>",
        "BindingsVersion": "2.2",
        "DisplayLabel": "<CONNECTOR_KEY> connection",
        "UseConnectionService": "true",
        "Connector": "<CONNECTOR_KEY>"
      }
    }
  ]
}
```

See [connector/impl.md](plugins/connector/impl.md) for the full schema and multi-connector examples.
