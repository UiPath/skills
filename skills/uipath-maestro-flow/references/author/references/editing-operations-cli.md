# Flow Editing Operations — CLI Carve-Outs

This is **not** a structural editing guide. Use direct `.flow` authoring via [editing-operations-json.md](editing-operations-json.md) for OOTB node/edge/variable CRUD, trigger swaps, output mapping, subflows, inline-agent node/wiring, non-connector resources, and in-place updates.

> **When to use this file:** only for CLI-managed carve-outs documented by a plugin: connector activities, connector triggers, and managed HTTP nodes (both `node add` and `node configure`). If you landed here while adding/removing/wiring OOTB nodes, inline-agent nodes, non-connector resources, or other structural graph elements, go back to the Edit / Write guide.

The primitive commands below are support commands for carve-out workflows only. They are not an opt-in path for non-carve-out structural edits.

---

## Primitive Commands for Carve-Out Workflows

### Add a node

```bash
uip maestro flow node add <ProjectName>.flow <node-type> --output json \
  --input '<INPUT_JSON>' \
  --label "<LABEL>" \
  --position <X>,<Y>
```

**What the CLI handles automatically:**
- Inserts node into `nodes` array with a generated `id`
- Copies the definition from the local registry cache into `definitions` (one per unique type)
- Adds node output variables to `variables.nodes`

**Flags:**

| Flag | Required | Description |
|------|----------|-------------|
| `--input` | No | JSON object of node-specific inputs (expression, script, URL, etc.). Omit for nodes with no inputs (merge, end, terminate). |
| `--label` | No | Display label shown on the canvas |
| `--position` | No | `x,y` coordinates. Any value is fine (e.g. `0,0`) — `flow format` rewrites positions on save. |
| `--output json` | Yes (for parsing) | Structured JSON response with the assigned node `id` |

**Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write it to a temp file and pass `--input "$(cat /tmp/input.json)"`.

### Remove a node

```bash
uip maestro flow node remove <ProjectName>.flow <NODE_ID>
uip maestro flow node remove <ProjectName>.flow <NODE_ID> --output json
```

**What the CLI handles automatically:**
- Removes the node from `nodes`
- Removes all connected edges
- Removes orphaned definitions (definitions no longer referenced by any node)
- Removes orphaned bindings (connector bindings are shared at the connector level — a binding is only orphaned when no remaining node uses that connector)
- Removes node variables from `variables.nodes`

### List nodes

```bash
uip maestro flow node list <ProjectName>.flow --output json
```

Returns all nodes with their `id`, `type`, and `display.label`. Use this to discover node IDs before wiring edges or removing nodes.

### Add an edge

```bash
uip maestro flow edge add <ProjectName>.flow <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
  --source-port <PORT> \
  --target-port <PORT>
```

**What the CLI handles automatically:**
- Inserts edge into `edges` array with a generated `id`
- Sets `targetPort` (required — validate rejects edges without it)

See each plugin's `planning.md` or [file-format.md — Standard ports](../../shared/file-format.md) for port names by node type.

### Remove an edge

```bash
uip maestro flow edge remove <ProjectName>.flow <EDGE_ID>
uip maestro flow edge remove <ProjectName>.flow <EDGE_ID> --output json
```

### List edges

```bash
uip maestro flow edge list <ProjectName>.flow --output json
```

Returns all edges with `id`, `sourceNodeId`, `sourcePort`, `targetNodeId`, `targetPort`.

### Configure a connector node

After adding a connector node with `node add`, configure it with connection details:

```bash
uip maestro flow node configure <ProjectName>.flow <NODE_ID> \
  --detail '<DETAIL_JSON>'
```

**What the CLI handles automatically:**
- Populates `inputs.detail` (connectionId, method, endpoint, bodyParameters, etc.)
- Creates connection binding entries in `bindings_v2.json`
- Creates connection resource files under `resources/solution_folder/connection/`

The `--detail` JSON schema differs between connector activity nodes, connector trigger nodes, and managed HTTP nodes — see [connector/impl.md](plugins/connector/impl.md), [connector-trigger/impl.md](plugins/connector-trigger/impl.md), and [http/impl.md](plugins/http/impl.md) for the exact fields.

**Shell quoting tip:** For complex `--detail` JSON, write it to a temp file:

```bash
uip maestro flow node configure <file> <nodeId> --detail "$(cat /tmp/detail.json)" --output json
```

### Configure a managed HTTP node

After adding a `core.action.http.v2` node, configure it with target connector and connection details:

```bash
uip maestro flow node configure <ProjectName>.flow <NODE_ID> \
  --detail '{
    "authentication": "connector",
    "targetConnector": "<TARGET_CONNECTOR_KEY>",
    "connectionId": "<TARGET_CONNECTION_ID>",
    "folderKey": "<FOLDER_KEY>",
    "method": "GET",
    "path": "/api/endpoint",
    "query": {"param1": "value1"}
  }'
```

**What the CLI handles automatically:**
- Wraps your fields into the full `inputs.detail` structure (connector: `uipath-uipath-http`, bodyParameters, configuration)
- Generates `bindings_v2.json` with the target connector's connection
- Creates a connection resource file under `resources/solution_folder/connection/`

See [http/impl.md](plugins/http/impl.md) for the full configuration workflow and JSON structure.

### Validate

```bash
uip maestro flow validate <ProjectName>.flow --output json
```

Run **once** after all nodes, edges, and configuration are complete. Do not validate after each individual edit — intermediate states are expected to be invalid.

---

## Carve-Out Composite Operations

These combine primitives only for workflows that are themselves carve-outs. Do not use them for non-carve-out structural edits; use [editing-operations-json.md](editing-operations-json.md) instead.

### Replace manual trigger with connector trigger

1. Remove the manual trigger (also removes its edges and orphaned definition):
   ```bash
   uip maestro flow node remove <ProjectName>.flow start --output json
   ```
2. Add the connector trigger node:
   ```bash
   uip maestro flow node add <ProjectName>.flow <TRIGGER_NODE_TYPE> \
     --label "<LABEL>" --position 200,144 --output json
   ```
3. Re-wire edge from the new trigger to the next node:
   ```bash
   uip maestro flow edge add <ProjectName>.flow <NEW_TRIGGER_ID> <NEXT_NODE_ID> \
     --source-port output --target-port input --output json
   ```
4. Configure the trigger with connection and event parameters:
   ```bash
   uip maestro flow node configure <ProjectName>.flow <NEW_TRIGGER_ID> --detail '<TRIGGER_DETAIL_JSON>'
   ```

See [connector-trigger/impl.md](plugins/connector-trigger/impl.md) for the full `--detail` schema.

---

## Operations Not Supported by CLI

These operations require the `Edit` tool. Use the [Edit / Write strategy guide](editing-operations-json.md) for:

1. **Any non-carve-out structural edit** — node/edge CRUD, scheduled triggers, HITL QuickForm nodes, inline-agent nodes, non-connector resources, and graph rewiring
2. **Node input updates** — the CLI does not have a `node update` command; use `Edit` to preserve node IDs and `$vars.{nodeId}` references
3. **Workflow variables** — add/remove/update `variables.globals`
4. **Variable updates** — add/modify `variables.variableUpdates` entries
5. **Output mapping on End nodes** — add `outputs` object with `source` expressions
6. **Subflows** — create `subflows.{nodeId}` with nested nodes, edges, variables
