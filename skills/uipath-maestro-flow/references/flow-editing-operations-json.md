# Flow Editing Operations — Direct JSON Strategy

All flow file modifications via direct read-modify-write of the `.flow` JSON file. This strategy gives full control over every field but requires manual management of definitions, variables, and edge integrity.

> **When to use this strategy:** Direct JSON is the default for all `.flow` edits. Use CLI (see [flow-editing-operations-cli.md](flow-editing-operations-cli.md)) only for connector, connector-trigger, and inline-agent nodes, or when the user explicitly requests CLI. See [flow-editing-operations.md](flow-editing-operations.md) for the strategy selection matrix.

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
| Resource bindings (agent, rpa-workflow, api-workflow) | Auto-added to top-level `bindings[]` by `node add`; `model.context[]` references auto-wired | Add two entries to top-level `bindings[]` per node (name + folderPath) and wire `model.context[]` with `=bindings.<id>` refs — see [Resource Node Bindings](#resource-node-bindings-direct-json). `flow validate` passes without them, but `flow debug` faults at runtime. |
| Connector bindings | Auto-added to top-level `bindings[]` by `node configure`; `model.context[].connection` reference auto-wired | Add one `resource: "Connection"` entry per unique connection to top-level `bindings[]` and wire `model.context[].connection` with `=bindings.<id>` — see [Connector Node Configuration](#connector-node-configuration-direct-json). |
| `bindings_v2.json` | Regenerated from top-level `bindings[]` at `flow debug`/`flow pack` time | **Never edit this file directly** — any manual edits are overwritten on the next debug/pack. All binding authoring goes through the `.flow` file's top-level `bindings[]`. |

---

## Pre-flight Checklist

Before editing the `.flow` file, ensure each of the following is handled. These are the concerns the CLI used to manage automatically; under the Direct JSON default, **you** are responsible for them.

1. **Locate the canonical `.flow` file.** Before any Write/Edit, find the flow project directory — it is the directory that contains `project.uiproj`. The canonical `.flow` lives **next to** that `project.uiproj`, not at the solution root. Commands like `uip solution new <Name>` + `uip flow init <Name>` create nested paths (`<Name>/<Name>/project.uiproj`); the `.flow` you must edit is `<Name>/<Name>/<Name>.flow`, not `<Name>/<Name>.flow`. Run `find . -name project.uiproj -type f` and pin every `.flow` Write/Edit to the sibling file. `uip flow validate <PATH>.flow` will accept a misplaced file, so validation alone does **not** confirm the right target — only the colocation with `project.uiproj` does.
2. **Definitions.** For every new node type, run `uip flow registry get <type> --output json`. Copy the `Data.Node` object **verbatim** into `definitions[]` — one entry per unique `type:typeVersion`. Never hand-write or paraphrase (Critical Rule #7).
3. **Unique node ID.** Pick a camelCase ID that does not collide with existing node IDs. Prefer meaningful names (`fetchUsers`, `filterActive`) since they become part of every `$vars.<nodeId>.*` expression.
4. **`targetPort` on every edge.** Omitting `targetPort` is the #1 validation error (Critical Rule #6). Look up ports in the relevant plugin's `planning.md` or in [flow-file-format.md — Standard ports](flow-file-format.md).
5. **Node outputs block.** Every data-producing node needs an `outputs` block on the node instance (not just in `definitions`). Action nodes: `output` + `error`. Trigger nodes: `output`. End/terminate: none. (Critical Rule #18.)
6. **`variables.nodes`.** Add an entry for the new node's outputs. Optional under today's runtime, but expected for completeness and diff clarity.
7. **On delete — cascade manually.** Remove the node from `nodes`. Then sweep `edges[]` for any with matching `sourceNodeId`/`targetNodeId`. Then prune `definitions[]` if this was the last user of the type. Then sweep the flow's top-level `bindings[]` — only remove a binding if no remaining node uses the same `resourceKey` (bindings are shared at the connector/resource level, not per node). Do not edit `bindings_v2.json` directly; it is regenerated from `bindings[]` at debug/pack.

> **Anti-pattern: editing a `.flow` that is not colocated with `project.uiproj`.**
> A `.flow` file outside the flow project directory is invisible to `uip flow debug`, to the Studio solution, and to any checker that discovers the project via `**/project.uiproj`. It will still pass `uip flow validate <PATH>.flow` because that command only checks JSON-schema correctness of the file you hand it — it does not verify the file is the project's canonical flow. Always edit the `.flow` that sits next to `project.uiproj`.

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

6. **If the node type is `uipath.core.agent.*`, `uipath.core.rpa-workflow.*`, or `uipath.core.api-workflow.*`** — follow [Resource Node Bindings](#resource-node-bindings-direct-json) below to append two entries to the top-level `bindings[]` and wire `model.context[]` on the node. Skipping this step makes the flow pass `flow validate` but fault at `flow debug` (the generated `bindings_v2.json` ends up empty, so the runtime can't resolve the Orchestrator resource).

### Delete a node

1. Remove the node object from `nodes`
2. Remove **all edges** where `sourceNodeId` or `targetNodeId` equals the node's `id`
3. If no other node uses the same `type`, remove the definition from `definitions`
4. Remove the node's entry from `variables.nodes`
5. Remove any `variableUpdates` entries keyed by the node's `id`
6. If the node is a connector node, remove its binding from `bindings_v2.json` **only if no other node in the flow uses the same connector**. Bindings are shared at the connector level (keyed by `metadata.Connector`), not per node.
7. If the node is a resource node (`uipath.core.agent.*`, `uipath.core.rpa-workflow.*`, `uipath.core.api-workflow.*`), remove its two entries from the top-level `bindings[]` (the `name` and `folderPath` entries whose `resourceKey` matches the deleted node's `model.bindings.resourceKey`) **only if no other node in the flow uses the same `resourceKey`**. Bindings are shared across nodes that invoke the same Orchestrator resource.

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
9. **If the real node is `uipath.core.agent.*`, `uipath.core.rpa-workflow.*`, or `uipath.core.api-workflow.*`** — follow [Resource Node Bindings](#resource-node-bindings-direct-json) to add two top-level `bindings[]` entries and wire `model.context[]`. `flow validate` passes without these; `flow debug` faults.
10. Validate: `uip flow validate <ProjectName>.flow --output json`

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

When not using `uip flow node configure`, a connector node needs three pieces in the `.flow` file: the `inputs.detail` block, two entries in the top-level `bindings[]`, and the node's `model.context[]` must keep the placeholder format so it matches the bindings.

> **Never edit `bindings_v2.json` directly.** That file is regenerated from the flow's top-level `bindings[]` at `flow debug` / `flow pack` time — any manual edits are overwritten.

### 1. `inputs.detail` on the node

```json
{
  "inputs": {
    "detail": {
      "connector": "<CONNECTOR_KEY>",
      "connectionId": "<CONNECTION_UUID>",
      "connectionResourceId": "<CONNECTION_UUID>",
      "connectionFolderKey": "<FOLDER_KEY>",
      "method": "<HTTP_METHOD>",
      "endpoint": "<API_PATH>",
      "bodyParameters": { "<FIELD>": "<VALUE>" },
      "queryParameters": { "<FIELD>": "<VALUE>" },
      "errorState": { "issues": [] }
    }
  }
}
```

The `method` and `endpoint` come from `connectorMethodInfo` in the `registry get --connection-id` response. `configuration`, `multipartParameters`, and `inputMetadata` also need to be populated for activities to run — see [connector/impl.md](plugins/connector/impl.md) for the full `inputs.detail` structure.

### 2. Keep `model.context[]` placeholders

The registry manifest returns `model.context[]` with placeholder values like `<bindings.<CONNECTOR_KEY> connection>` and `<bindings.FolderKey>`. **Leave these placeholders in place** — do not rewrite them to `=bindings.<id>`. The runtime matches bindings to nodes by name via the placeholder form.

```json
"model": {
  "context": [
    { "name": "connectorKey", "type": "string", "value": "<CONNECTOR_KEY>" },
    { "name": "connection", "type": "string", "value": "<bindings.<CONNECTOR_KEY> connection>" },
    { "name": "folderKey", "type": "string", "value": "<bindings.FolderKey>" }
  ]
}
```

### 3. Connection bindings in top-level `.flow` `bindings[]`

Append these two entries to the flow's top-level `bindings[]` array (sibling of `nodes`, `edges`, `definitions`):

```json
{
  "id": "<CONN_BINDING_ID>",
  "name": "<CONNECTOR_KEY> connection",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<CONNECTION_UUID>",
  "default": "<CONNECTION_UUID>",
  "propertyAttribute": "ConnectionId"
},
{
  "id": "<FOLDER_BINDING_ID>",
  "name": "FolderKey",
  "type": "string",
  "resource": "Connection",
  "resourceKey": "<CONNECTION_UUID>",
  "default": "<FOLDER_KEY>",
  "propertyAttribute": "FolderKey"
}
```

- `resource: "Connection"` is capital-C (not `"connection"`). The runtime is case-sensitive here.
- Both bindings share the same `resourceKey` (the connection UUID).
- The `name: "<CONNECTOR_KEY> connection"` value must exactly match what's inside the node's `model.context[].connection` placeholder (without the `<bindings.` prefix and `>` suffix).
- **Share bindings across nodes using the same connection:** if two connector nodes use the same connection, reuse the same two binding entries — do not add duplicates.

At `flow debug`/`flow pack` time the CLI maps each binding to a `Connection` resource in `bindings_v2.json` (adding `id = "Connection<resourceKey>"`, `metadata.Connector`, etc.). See [connector/impl.md](plugins/connector/impl.md) for the generated `bindings_v2.json` shape (reference only).

---

## Resource Node Bindings (Direct JSON)

Resource nodes — `uipath.core.agent.*`, `uipath.core.rpa-workflow.*`, `uipath.core.api-workflow.*` — invoke a published Orchestrator resource. They need **two entries per node in the flow's top-level `bindings[]` array** (one for `name`, one for `folderPath`) plus a matching `model.context[]` on the node. The CLI's `uip flow node add` creates these automatically; when hand-writing JSON, you must create them yourself.

**Why it matters.** At `flow debug` and `flow pack` time the CLI regenerates `bindings_v2.json` from the flow's top-level `bindings[]`. An empty top-level `bindings[]` produces an empty `bindings_v2.json`, and the runtime faults on "resource not found" even though `flow validate` passes (validate only checks the `.flow` JSON schema — it does not check that resource-backed nodes have bindings).

### Step 1 — Pull the manifest

```bash
uip flow registry get <NODE_TYPE> --output json
```

From `Data.Node.model.bindings`, record:
- `resourceKey` — a path-like string (e.g. `"Shared/CountLetters CodedAgent.CountLetters"`). Do not replace this with the node type's GUID; use what the registry returns.
- `resourceSubType` — see the per-prefix table below.
- `orchestratorType` — see the per-prefix table below.
- `values.name` and `values.folderPath` — the default name and folder-path strings.

| Node type prefix | `resourceSubType` | `orchestratorType` |
|---|---|---|
| `uipath.core.agent.` | `Agent` | `agent` |
| `uipath.core.rpa-workflow.` | `Process` | `process` |
| `uipath.core.api-workflow.` | `Api` | `api` |

### Step 2 — Pick two binding IDs

Generate two unique IDs, one per binding entry. Convention used by the CLI: a lowercase `b` followed by 8 random alphanumerics (e.g. `bKEFLMRB2`, `bwSwZQsvT`). Any short unique string works; just make sure the two IDs differ from each other and from any existing binding IDs in the flow.

### Step 3 — Append two entries to top-level `bindings[]`

```json
"bindings": [
  {
    "id": "<NAME_BINDING_ID>",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<RESOURCE_KEY>",
    "default": "<NAME_VALUE>",
    "propertyAttribute": "name",
    "resourceSubType": "<SUB_TYPE>"
  },
  {
    "id": "<FOLDER_BINDING_ID>",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "<RESOURCE_KEY>",
    "default": "<FOLDER_PATH_VALUE>",
    "propertyAttribute": "folderPath",
    "resourceSubType": "<SUB_TYPE>"
  }
]
```

If `bindings[]` doesn't exist at the top level of the flow yet, add it as a sibling of `nodes`, `edges`, `definitions`.

### Step 4 — Wire `model.context[]` on the node

Inside the node's `model`, add a `context` array that references the two binding IDs:

```json
"model": {
  "type": "bpmn:ServiceTask",
  "serviceType": "<SERVICE_TYPE>",
  "version": "v2",
  "section": "Published",
  "bindings": {
    "resource": "process",
    "resourceSubType": "<SUB_TYPE>",
    "resourceKey": "<RESOURCE_KEY>",
    "orchestratorType": "<ORCH_TYPE>",
    "values": {
      "name": "<NAME_VALUE>",
      "folderPath": "<FOLDER_PATH_VALUE>"
    }
  },
  "context": [
    { "name": "name", "type": "string", "value": "=bindings.<NAME_BINDING_ID>", "default": "<NAME_VALUE>" },
    { "name": "folderPath", "type": "string", "value": "=bindings.<FOLDER_BINDING_ID>", "default": "<FOLDER_PATH_VALUE>" },
    { "name": "_label", "type": "string", "value": "<NAME_VALUE>" }
  ]
}
```

- `model.bindings.resourceKey` must equal the `resourceKey` on both top-level entries (this is how the CLI matches nodes to bindings when generating `bindings_v2.json`).
- `context[].value` uses `=bindings.<id>` — not `<bindings.<name>>`, not a raw string.
- The `_label` context entry is Studio Web's display label; set it to the `name` value.
- `serviceType` comes from the registry manifest (e.g. `Orchestrator.StartAgentJob` for agents). Copy it verbatim.

### Shared bindings across multiple nodes

If two nodes invoke the same resource (same `resourceKey`), they should share the same two binding entries — don't duplicate. Both nodes reference the same `<NAME_BINDING_ID>` and `<FOLDER_BINDING_ID>` from their `model.context[]`.

### Per-plugin details

See the relevant plugin's `impl.md` for node-type-specific values and a complete worked example: [agent/impl.md](plugins/agent/impl.md), [rpa/impl.md](plugins/rpa/impl.md), [api-workflow/impl.md](plugins/api-workflow/impl.md).
