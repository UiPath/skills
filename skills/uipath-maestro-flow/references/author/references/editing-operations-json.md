# Flow Editing Operations — Edit / Write Strategy

All flow file modifications via the `Edit` and `Write` tools (read-modify-write of the `.flow` JSON file). This strategy gives full control over every field but requires manual management of definitions, variables, and edge integrity.

> **Apply every recipe in this file with the `Edit` tool (default) or the `Write` tool (only when ≥70% of nodes change).** Each recipe shows the JSON payload that goes into the `new_string` parameter of an `Edit` call. **Never** use `python`, `node`, `jq`, `sed`, `awk`, or shell heredocs to mutate the `.flow` file — see SKILL.md rule on forbidden tools and [editing-operations.md — Why not Python / Node / jq / sed?](editing-operations.md#why-not-python--node--jq--sed).
>
> **When to use this strategy:** Edit / Write is the default for all `.flow` edits. Use CLI (see [editing-operations-cli.md](editing-operations-cli.md)) only for connector, connector-trigger, and inline-agent nodes, or when the user explicitly requests CLI. See [editing-operations.md](editing-operations.md) for the strategy selection matrix.

---

## Key Differences from CLI

When editing the `.flow` file with `Edit` / `Write`, **you** are responsible for everything the CLI normally handles:

| Concern | CLI handles | Edit / Write — you must |
|---------|------------|------------------------|
| Definitions | Auto-copied from registry cache | Copy `Data.Node` from `uip maestro flow registry get` into `definitions` array |
| Node variables | Auto-added to `variables.nodes` | Add output variable entries manually (or accept that `variables.nodes` may need regeneration) |
| Edge cleanup on delete | Auto-removes connected edges | Find and remove all edges referencing the deleted node |
| Orphan cleanup | Auto-removes unused definitions and orphaned bindings | Remove definitions no longer referenced by any node; remove connector bindings only when no remaining node uses that connector |
| `targetPort` | Auto-set | Set `targetPort` on every edge (validate rejects without it) |
| `bindings_v2.json` | Auto-managed by `node configure` | Edit `bindings_v2.json` manually for connector nodes |

---

## Pre-flight Checklist

Before editing the `.flow` file, ensure each of the following is handled. These are the concerns the CLI used to manage automatically; under the Edit / Write default, **you** are responsible for them.

1. **Locate the canonical `.flow` file.** Before any `Edit` / `Write`, find the flow project directory — it is the directory that contains `project.uiproj`. The canonical `.flow` lives **next to** that `project.uiproj`, not at the solution root. Commands like `uip solution new <Name>` + `uip maestro flow init <Name>` create nested paths (`<Name>/<Name>/project.uiproj`); the `.flow` you must edit is `<Name>/<Name>/<Name>.flow`, not `<Name>/<Name>.flow`. Run `find . -name project.uiproj -type f` and pin every `Edit` / `Write` call to the sibling file. `uip maestro flow validate <PATH>.flow` will accept a misplaced file, so validation alone does **not** confirm the right target — only the colocation with `project.uiproj` does.
2. **Definitions.** For every new node type, run `uip maestro flow registry get <type> --output json`. Copy the `Data.Node` object **verbatim** into `definitions[]` — one entry per unique `type:typeVersion`. Never hand-write or paraphrase (see "Every node type needs a `definitions` entry" in [the Author capability index](../CAPABILITY.md)).
3. **Unique node ID.** Pick a camelCase ID that does not collide with existing node IDs. Prefer meaningful names (`fetchUsers`, `filterActive`) since they become part of every `$vars.<nodeId>.*` expression.
4. **`targetPort` on every edge.** Omitting `targetPort` is the #1 validation error (see "`targetPort` is required on every edge" in [the Author capability index](../CAPABILITY.md)). Look up ports in the relevant plugin's `planning.md` or in [file-format.md — Standard ports](../../shared/file-format.md).
5. **Node outputs block.** Every data-producing node needs an `outputs` block on the node instance (not just in `definitions`). Action nodes: `output` + `error`. Trigger nodes: `output`. End/terminate: none. (See "Every node that produces data MUST have `outputs` on the node instance" in [the Author capability index](../CAPABILITY.md).)
6. **`variables.nodes`.** Add an entry for the new node's outputs. Optional under today's runtime, but expected for completeness and diff clarity.
7. **On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type. Then check `bindings_v2.json` — but only remove a connector binding if no remaining node uses the same connector (bindings are shared at the connector level).

> **Anti-pattern: editing a `.flow` that is not colocated with `project.uiproj`.**
> A `.flow` file outside the flow project directory is invisible to `uip maestro flow debug`, to the Studio solution, and to any checker that discovers the project via `**/project.uiproj`. It will still pass `uip maestro flow validate <PATH>.flow` because that command only checks JSON-schema correctness of the file you hand it — it does not verify the file is the project's canonical flow. Always edit the `.flow` that sits next to `project.uiproj`.

---

## Primitive Operations

### Add a node

**Tool:** `Edit` (insert into `nodes[]` + `definitions[]` + `variables.nodes` + `layout.nodes`)

1. Run `uip maestro flow registry get <NODE_TYPE> --output json` and copy the `Data.Node` object
2. Use `Edit` to add a node entry to the `nodes` array:

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
  }
}
```

> **Node outputs are required.** Every node that produces data for downstream `$vars` references must include an `outputs` block. See [file-format.md — Node outputs](../../shared/file-format.md#node-outputs) for the standard patterns by node category (action nodes get `output` + `error`; trigger nodes get `output` only; end/terminate nodes do not use this pattern).

> **No `model` block on nodes.** BPMN type, serviceType, event definition, and binding/context templates are provided by the definition in `definitions[]` (copied verbatim from the registry). Instance-specific identity fields live under `inputs`: `entryPointId`/`isDefaultEntryPoint` for triggers, `source` for inline agents, `color`/`content` for sticky notes. See [file-format.md — Instance-specific fields that live in `inputs`](../../shared/file-format.md#instance-specific-fields-that-live-in-inputs).

> **No `ui` block on nodes.** Do NOT put `position`, `size`, or `collapsed` on the node. Add a layout entry instead (step 5).

3. Add the definition to `definitions` (if this type is not already present):
   - Paste the `Data.Node` object from the registry response
   - One definition per unique `type` — not one per node instance

> **Resource nodes — extra step.** If the node type is one of `uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, `uipath.core.flow.*`, `uipath.core.agentic-process.*`, `uipath.core.api-workflow.*`, or `uipath.core.human-task.*`:
> 1. The instance stays minimal — just `inputs`/`outputs`/`display`.
> 2. Add matching entries to the top-level `bindings[]` array (sibling of `nodes`/`edges`/`definitions`): two entries per resource (`name` + `folderPath`) with `resourceKey` exactly matching the definition's `model.bindings.resourceKey`.
>
> The BPMN emit layer rewrites the definition's `<bindings.{name}>` placeholders to `=bindings.{id}` by matching on `(resourceKey, name)`. Without matching entries in top-level `bindings[]`, `uip maestro flow validate` passes but `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder." The definition stays verbatim from the registry — do NOT rewrite `<bindings.*>` placeholders inside it. See the relevant plugin's `impl.md` for the exact JSON.

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

5. Add a placeholder layout entry for the node in the top-level `layout.nodes` object — `flow tidy` rewrites both `position` and `size` on save:

```json
"layout": {
  "nodes": {
    "<UNIQUE_NODE_ID>": {
      "position": { "x": 0, "y": 0 },
      "size": { "width": 96, "height": 96 },
      "collapsed": false
    }
  }
}
```

**Layout rule:** Don't compute coordinates by hand — run `uip maestro flow tidy <ProjectName>.flow` after edits. Tidy arranges nodes horizontally, sets size to `{ "width": 96, "height": 96 }`, and recurses into subflows.

### Delete a node

**Tool:** `Edit` (remove from `nodes[]` + dependent edges + orphaned definitions + `variables.nodes` + `variableUpdates`)

1. Use `Edit` to remove the node object from `nodes`
2. Remove **all edges** where `sourceNodeId` or `targetNodeId` equals the node's `id`
3. If no other node uses the same `type`, remove the definition from `definitions`
4. Remove the node's entry from `variables.nodes`
5. Remove any `variableUpdates` entries keyed by the node's `id`
6. If the node is a connector node, remove its binding from `bindings_v2.json` **only if no other node in the flow uses the same connector**. Bindings are shared at the connector level (keyed by `metadata.Connector`), not per node.

### Add an edge

**Tool:** `Edit` (insert into `edges[]` with `targetPort`)

Use `Edit` to add an edge object to the `edges` array:

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

See each plugin's `planning.md` or [file-format.md — Standard ports](../../shared/file-format.md) for port names by node type.

### Delete an edge

**Tool:** `Edit`

Use `Edit` to remove the edge object from the `edges` array by its `id`.

### Update node inputs

**Tool:** `Edit` (in-place value tweak — preserves node ID and `$vars`)

Use `Edit` to modify the `inputs` object of the target node in-place. No need to delete and re-add.

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "inputs": {
    "expression": "$vars.fetchData.output.statusCode === 200"
  }
}
```

This is a key advantage of `Edit` — input updates are a single field edit, not the delete + re-add pattern required by the CLI.

---

## Variable Operations

These are `Edit`-only — the CLI does not support variable management. There is no fallback strategy.

### Add a workflow variable

**Tool:** `Edit`

Use `Edit` to add an entry to `variables.globals`:

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

See [variables-and-expressions.md](../../shared/variables-and-expressions.md) for the full schema, type system, and scoping rules.

### Add output mapping on an End node

**Tool:** `Edit`

Use `Edit` to map every `out` variable in `variables.globals` on every reachable End node:

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

**Tool:** `Edit`

Use `Edit` to add an entry to `variables.variableUpdates.<NODE_ID>`:

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

**Tool:** `Edit` × 3 (delete old edge, add new node, add 2 new edges)

1. Use `Edit` to remove the edge connecting the two nodes from the `edges` array
2. Use `Edit` to add the new node to `nodes` (with definition in `definitions`)
3. Use `Edit` to add two new edges:
   - upstream → new node (using upstream's output port → new node's `input`)
   - new node → downstream (using new node's output port → downstream's `input`)

### Insert a decision branch

**Tool:** `Edit` × 3 (delete old edge, add decision node, add 3 new edges)

1. Use `Edit` to remove the edge where the branch should go
2. Use `Edit` to add the decision node to `nodes` with `inputs.expression`
3. Use `Edit` to add three edges:
   - upstream → decision (target port: `input`)
   - decision → true branch (source port: `true`, target port: `input`)
   - decision → false branch (source port: `false`, target port: `input`)

### Remove a node and reconnect

**Tool:** `Edit` × 4 (delete node, sweep edges, prune orphan definitions, add reconnect edge)

1. Record the node's upstream and downstream connections from `edges`
2. Use `Edit` to remove the node from `nodes`
3. Use `Edit` to remove all edges referencing the node
4. Use `Edit` to clean up orphaned definitions
5. Use `Edit` to add a new edge connecting upstream directly to downstream

### Replace a mock with a real resource node

**Tool:** `Edit` (multiple calls — replace node, edges, definitions, bindings, variables)

1. Get the resource node manifest — check in-solution first, then tenant registry:
   ```bash
   # In-solution (preferred — no login required):
   uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --local --output json

   # Tenant registry (if not in solution):
   uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --output json
   ```
2. Record the mock node's connected edges
3. Remove the mock node from `nodes`
4. Remove all edges referencing the mock
5. Add the real resource node to `nodes` with:
   - Correct `type` and `typeVersion`
   - `inputs` with resolved field values
   - `outputs` block (action nodes: `output` + `error`)
   - No `model` block — binding/context templates come from the definition
6. Copy the definition from registry into `definitions`
7. Add entries to the top-level `bindings[]` array — two per resource (`name` + `folderPath`), with `resourceKey` matching the definition's `model.bindings.resourceKey`
8. Re-create all edges using the new node's `id`
9. Add node variables to `variables.nodes`
10. Validate: `uip maestro flow validate <ProjectName>.flow --output json`

### Replace manual trigger with scheduled trigger

**Tool:** `Edit` × 2 (start node in-place, swap definition)

Use `Edit` to modify the start node in-place (no delete/re-add needed):

1. Change `type` from `core.trigger.manual` to `core.trigger.scheduled`
2. Add timer inputs (keep the existing `entryPointId` in `inputs`):
   ```json
   "inputs": {
     "entryPointId": "<existing-uuid>",
     "timerType": "timeCycle",
     "timerPreset": "R/PT1H"
   }
   ```
3. Update the definition in `definitions`:
   - Remove the `core.trigger.manual` definition
   - Add the `core.trigger.scheduled` definition from `uip maestro flow registry get core.trigger.scheduled --output json` (the new definition carries the correct `model.type` and `model.eventDefinition`)
4. Validate: `uip maestro flow validate <ProjectName>.flow --output json`

### Create a subflow

**Tool:** `Edit` (or `Write` if scaffolding from template)

1. Use `Edit` to add a `core.subflow` parent node to `nodes`:
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
     }
   }
   ```

2. Use `Edit` to add a `subflows.<SUBFLOW_NODE_ID>` entry with its own nodes, edges, variables, and layout:
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
         },
         "layout": {
           "nodes": {
             "sfStart": { "position": { "x": 200, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false },
             "sfEnd":   { "position": { "x": 400, "y": 144 }, "size": { "width": 96, "height": 96 }, "collapsed": false }
           }
         }
       }
     }
   }
   ```

3. Subflow's `in` variables must match the parent node's `inputs` keys
4. Map all `out` variables on the subflow's End node `outputs`
5. Parent-scope `$vars` are NOT visible inside the subflow — pass values via inputs
6. Subflow node positions go in the **subflow's own** `layout.nodes` — not in the top-level `layout.nodes`. Each subflow has an independent layout scope.

See [subflow/impl.md](plugins/subflow/impl.md) for the full JSON structure and rules.

---

## Connector Node Configuration (Edit / Write fallback)

When not using `uip maestro flow node configure`, use `Edit` to set up the following manually:

### 1. `inputs.detail` on the node

**Tool:** `Edit`

```json
{
  "inputs": {
    "detail": {
      "connectionId": "<CONNECTION_UUID>",
      "folderKey": "<FOLDER_KEY>",
      "method": "<HTTP_METHOD>",
      "endpoint": "<API_PATH>",
      "bodyParameters": { "<FIELD>": "<VALUE>" },
      "queryParameters": { "<FIELD>": "<VALUE>" },
      "pathParameters": { "<PLACEHOLDER>": "<VALUE>" }
    }
  }
}
```

Source `method`, `endpoint`, and `bodyParameters` / `queryParameters` / `pathParameters` field names from either of these (both read the same upstream IS metadata):

From `uip maestro flow registry get <nodeType> --connection-id <id> --output json`:
- `method` ← `connectorMethodInfo.method`
- `endpoint` ← `connectorMethodInfo.path`
- `bodyParameters.<name>` ← `inputDefinition.fields[].name`
- `queryParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: query`
- `pathParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: path` (must match a `{placeholder}` in `endpoint`)

From `uip is resources describe <connector-key> <objectName> --connection-id <id> --operation <Op> --output json`:
- `method` ← `availableOperations[].method`
- `endpoint` ← `availableOperations[].path`
- `bodyParameters.<name>` ← `requestFields[].name`
- `queryParameters.<name>` ← `parameters[]` where `type: query`
- `pathParameters.<name>` ← `parameters[]` where `type: path` (must match a `{placeholder}` in `endpoint`)

### 2. Connection binding in `bindings_v2.json`

**Tool:** `Edit` (or `Write` for a fresh `bindings_v2.json`)

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
