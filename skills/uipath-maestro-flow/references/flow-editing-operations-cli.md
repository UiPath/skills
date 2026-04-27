# Flow Editing Operations — CLI Strategy

All flow file modifications via `uip maestro flow node` and `uip maestro flow edge` CLI commands. The CLI automatically manages definitions, variables, edge cleanup, and `bindings_v2.json` — eliminating the most common build errors.

> **When to use this strategy:** Use this strategy for connector, connector-trigger, and inline-agent nodes, or when the user explicitly requests CLI. For all other edits, Direct JSON is the default (see [flow-editing-operations-json.md](flow-editing-operations-json.md)). See [flow-editing-operations.md](flow-editing-operations.md) for the strategy selection matrix.

---

## Primitive Operations

### Add a node

```bash
uip maestro flow node add <ProjectName>.flow <nodeType> --output json \
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
| `--position` | No | `x,y` coordinates. Use horizontal layout: increasing `x`, consistent `y` baseline (e.g., `y: 144`). |
| `--output json` | Yes (for parsing) | Structured JSON response with the assigned node `id` |

**Shell quoting tip:** If `--input` JSON contains special characters (quotes, braces, `$vars`), write it to a temp file:

```bash
cat > /tmp/input.json << 'ENDJSON'
{"script": "const data = $vars.fetchData.output.body;\nreturn { count: data.items.length };"}
ENDJSON
uip maestro flow node add <ProjectName>.flow core.action.script \
  --input "$(cat /tmp/input.json)" --output json \
  --label "Process Data" --position 400,144
```

### Delete a node

```bash
uip maestro flow node delete <ProjectName>.flow <NODE_ID>
uip maestro flow node delete <ProjectName>.flow <NODE_ID> --output json
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

Returns all nodes with their `id`, `type`, and `display.label`. Use this to discover node IDs before wiring edges or deleting nodes.

### Add an edge

```bash
uip maestro flow edge add <ProjectName>.flow <SOURCE_NODE_ID> <TARGET_NODE_ID> --output json \
  --source-port <PORT> \
  --target-port <PORT>
```

**What the CLI handles automatically:**
- Inserts edge into `edges` array with a generated `id`
- Sets `targetPort` (required — validate rejects edges without it)

See each plugin's `planning.md` or [flow-file-format.md — Standard ports](flow-file-format.md) for port names by node type.

### Delete an edge

```bash
uip maestro flow edge delete <ProjectName>.flow <EDGE_ID>
uip maestro flow edge delete <ProjectName>.flow <EDGE_ID> --output json
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

## Composite Operations

These combine primitives to accomplish common editing tasks. Each recipe assumes you are working with an existing flow.

### Update node inputs (expression, script body, label, etc.)

The CLI does not have a `node update` command. **Do not use delete + re-add** — `node add` generates a new node ID, which breaks all downstream `$vars.{nodeId}.output` expressions and requires re-wiring every edge.

Instead, edit the node's `inputs` (and optionally `display.label`) directly in the `.flow` JSON file. See [JSON: Update node inputs](flow-editing-operations-json.md#update-node-inputs).

### Insert a node between two existing nodes

1. Find and delete the edge connecting the two nodes:
   ```bash
   uip maestro flow edge list <ProjectName>.flow --output json
   uip maestro flow edge delete <ProjectName>.flow <EDGE_ID>
   ```
2. Add the new node at a position between the two:
   ```bash
   uip maestro flow node add <ProjectName>.flow <NODE_TYPE> --output json \
     --input '<INPUT_JSON>' --label "<LABEL>" --position <X>,<Y>
   ```
3. Wire upstream → new node → downstream:
   ```bash
   uip maestro flow edge add <ProjectName>.flow <UPSTREAM_ID> <NEW_NODE_ID> --output json \
     --source-port <PORT> --target-port input
   uip maestro flow edge add <ProjectName>.flow <NEW_NODE_ID> <DOWNSTREAM_ID> --output json \
     --source-port success --target-port input
   ```

### Insert a decision branch

1. Delete the edge where you want to insert the branch:
   ```bash
   uip maestro flow edge list <ProjectName>.flow --output json
   uip maestro flow edge delete <ProjectName>.flow <EDGE_ID>
   ```
2. Add the decision node:
   ```bash
   uip maestro flow node add <ProjectName>.flow core.logic.decision --output json \
     --input '{"expression": "<BOOLEAN_EXPRESSION>"}' \
     --label "<LABEL>" --position <X>,<Y>
   ```
3. Wire upstream → decision, and decision → both branches:
   ```bash
   uip maestro flow edge add <ProjectName>.flow <UPSTREAM_ID> <DECISION_ID> --output json \
     --source-port <PORT> --target-port input
   uip maestro flow edge add <ProjectName>.flow <DECISION_ID> <TRUE_BRANCH_ID> --output json \
     --source-port true --target-port input
   uip maestro flow edge add <ProjectName>.flow <DECISION_ID> <FALSE_BRANCH_ID> --output json \
     --source-port false --target-port input
   ```

### Remove a node and reconnect

1. List nodes and edges to find the node and its connections:
   ```bash
   uip maestro flow node list <ProjectName>.flow --output json
   uip maestro flow edge list <ProjectName>.flow --output json
   ```
2. Note the upstream and downstream node IDs and ports
3. Delete the node (edges are removed automatically):
   ```bash
   uip maestro flow node delete <ProjectName>.flow <NODE_ID>
   ```
4. Reconnect upstream to downstream:
   ```bash
   uip maestro flow edge add <ProjectName>.flow <UPSTREAM_ID> <DOWNSTREAM_ID> --output json \
     --source-port <PORT> --target-port input
   ```

### Replace a mock with a real resource node

After the resource (RPA process, agent, etc.) has been published or added to the solution:

1. Discover the resource — check in-solution first, then tenant registry:
   ```bash
   # In-solution (preferred — no login required):
   uip maestro flow registry list --local --output json

   # Tenant registry (if not in solution):
   uip maestro flow registry pull --force
   uip maestro flow registry search "<RESOURCE_NAME>" --output json
   ```
2. Record the mock node's edges:
   ```bash
   uip maestro flow edge list <ProjectName>.flow --output json
   ```
3. Delete the mock node:
   ```bash
   uip maestro flow node delete <ProjectName>.flow <MOCK_NODE_ID>
   ```
4. Add the real resource node at the same position:
   ```bash
   uip maestro flow node add <ProjectName>.flow "<RESOURCE_NODE_TYPE>" --output json \
     --input '<INPUT_JSON>' --label "<LABEL>" --position <SAME_X>,<SAME_Y>
   ```
5. Re-wire all edges from step 2
6. Validate: `uip maestro flow validate <ProjectName>.flow --output json`

### Replace manual trigger with connector trigger

1. Delete the manual trigger (also removes its edges and orphaned definition):
   ```bash
   uip maestro flow node delete <ProjectName>.flow start --output json
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

### Replace manual trigger with scheduled trigger

1. Record the edge from the start node to the next node:
   ```bash
   uip maestro flow edge list <ProjectName>.flow --output json
   ```
2. Delete the manual trigger (also removes its edge and orphaned definition):
   ```bash
   uip maestro flow node delete <ProjectName>.flow start --output json
   ```
3. Add the scheduled trigger node:
   ```bash
   uip maestro flow node add <ProjectName>.flow core.trigger.scheduled --output json \
     --input '{"timerType": "timeCycle", "timerPreset": "R/PT1H"}' \
     --label "<LABEL>" --position 200,144
   ```
4. Re-wire edge from the new trigger to the next node:
   ```bash
   uip maestro flow edge add <ProjectName>.flow <NEW_TRIGGER_ID> <NEXT_NODE_ID> \
     --source-port output --target-port input --output json
   ```

See [scheduled-trigger/impl.md](plugins/scheduled-trigger/impl.md) for timer presets and custom frequency options.

---

## Operations NOT Supported by CLI

These operations require direct `.flow` JSON editing. Use the [JSON strategy guide](flow-editing-operations-json.md) for:

1. **Workflow variables** — add/remove/update `variables.globals`
2. **Variable updates** — add/modify `variables.variableUpdates` entries
3. **Output mapping on End nodes** — add `outputs` object with `source` expressions
4. **Subflows** — create `subflows.{nodeId}` with nested nodes, edges, variables
