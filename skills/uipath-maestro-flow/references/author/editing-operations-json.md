# Flow Editing Operations — Edit / Write Strategy

Modify `.flow` files with `Edit` and `Write` (read-modify-write). This requires manual management of definitions, variables, bindings, and edges.

> Use `Edit` by default; use `Write` only when ≥70% of nodes change. Recipes show the JSON for an `Edit` call’s `new_string`. `python`, `node`, `jq`, `sed`, `awk`, and shell heredocs are last-resort mutation tools and require explicit user approval after surfacing trade-offs; see the SKILL.md rule on scripted mutations and [editing-operations.md — Why not Python / Node / jq / sed?](editing-operations.md#why-not-python--node--jq--sed).
>
> Use this strategy for all non-carve-out `.flow` edits. Use Flow CLI only for connector activity, connector-trigger, and managed HTTP carve-outs documented by their plugins. Inline-agent lifecycle uses `uip agent init --inline-in-flow`, `uip agent refresh --inline-in-flow`, and `uip agent validate --inline-in-flow`; author the `uipath.agent.autonomous` node and edges with this guide. See [editing-operations.md](editing-operations.md) for the strategy selection matrix.

## Key Differences from CLI

| Concern | CLI handles | Edit / Write — you must |
|---|---|---|
| Definitions | Copies from registry cache | Copy the returned node definition object from `uip maestro flow registry get` into `definitions[]`. |
| Node variables | Adds to `variables.nodes` | Add output entries manually or regenerate them. |
| Delete cleanup | Removes connected edges | Remove every edge referencing the node. |
| Orphan cleanup | Removes unused definitions and orphaned bindings | Remove unreferenced definitions; remove connector bindings only when no remaining node uses that connector. |
| `targetPort` | Sets it | Set it on every edge; validation rejects omissions. |
| `bindings_v2.json` | Managed by `node configure` | Prefer the CLI carve-out for connector/managed HTTP configuration. Under the fallback, author top-level `.flow` `bindings[]` and touch generated files only when the plugin explicitly says to. |

## Pre-flight Checklist

Before editing, complete all applicable items:

<!--skill-flavor:flow-project-location:start-->
1. **Locate the canonical `.flow` file.** Run `find . -name project.uiproj -type f`. The flow project directory contains `project.uiproj`; the canonical `.flow` is its sibling, not the solution root. For nested paths created by `uip solution init <Name>` + `uip maestro flow init <Name>`, edit `<Name>/<Name>/<Name>.flow`, not `<Name>/<Name>.flow`. Pin every `Edit` / `Write` call to that sibling. `uip maestro flow validate <PATH>.flow` accepts misplaced files, so validation does not establish the target; colocation does.
<!--skill-flavor:flow-project-location:end-->
2. **Definitions and versions.** For each new type, run `uip maestro flow registry get <type> --output json`. Copy the returned node definition verbatim into `definitions[]`, one per unique `type:typeVersion`. It may be `Data.Node` or the top-level object containing `nodeType`, `version`, and `handleConfiguration`; copy the node object, not the `Result` / `Code` envelope. Set each instance `typeVersion` to the exact definition `version` string; do not normalize. For documented `uip maestro flow node add` carve-outs (managed HTTP, connector activities, connector triggers), use the CLI; see [http/impl.md — Step 1](plugins/http/impl.md#add-the-node).
3. **Unique ID.** Use a non-colliding camelCase ID, preferably meaningful because it appears in `$vars.<nodeId>.*` expressions.
4. **Edges.** Set `sourcePort` and `targetPort` on every edge. Use `sourcePort`, never `sourceHandle`; `sourceHandle` is not in the `.flow` schema. Look up ports in plugin `planning.md` or [file-format.md — Standard ports](../shared/file-format.md). If `sourcePort: "error"`, set `inputs.errorHandlingEnabled: true` on the source; set it only when an `error` edge exists. See [file-format.md — Default: off](../shared/file-format.md#default-off--enable-only-for-a-failure-the-flow-actually-handles).
5. **Outputs.** End-style nodes consume `outputs` at runtime to map workflow-level `out` variables; see [end/impl.md](plugins/end/impl.md). Action/trigger instance `outputs` are not consumed by BPMN serialization; the manifest `outputDefinition` is used. A matching block is documentation only; `$vars.<sourceNodeId>.output` requires `variables.nodes[]`.
6. **Node variables.** Add one `variables.nodes[]` entry for every data-producing node output: `output` for action/trigger nodes and `error` for action nodes. Use `{ "id": "<nodeId>.<outputId>", "type": "object", "binding": { "nodeId": "<nodeId>", "outputId": "<outputId>" } }`. The BPMN emitter uses these declarations; validation may pass while runtime resolves `undefined`. `uip maestro flow format` regenerates this block from `nodes[]` + `definitions[]`.
7. **Delete cascade.** Remove the node, every edge whose `sourceNodeId` or `targetNodeId` matches it, unused definitions, its `variables.nodes` and `variableUpdates` entries, and connector bindings only when no remaining node uses that connector.

> **Anti-pattern:** editing a `.flow` not colocated with `project.uiproj`. It is invisible to `uip maestro flow debug`, Studio, and discovery via `**/project.uiproj`; `uip maestro flow validate <PATH>.flow` can still pass. Always edit the sibling `.flow`.

## Edit Tooling

| Operation | Mechanic | Rule |
|---|---|---|
| Surgical leaf string/number/bool | `Edit` | Use one unique substring; re-`Read` after rewrites because matching is whitespace-sensitive. |
| New node, edge, definition, or variable | `Read` whole file → reconstruct in chat → `Write` whole file | Preserve field order; avoid dropping fields on files >1000 lines. |
| Nested replacement, field insertion, idempotent splice | `Edit` / `Write`; `python3` heredoc only after explicit user approval | Prefer direct authoring; scripts bypass safeguards and require diff review. |
| One-shot extraction/single-field CLI JSON mutation | `jq` | Use only when `--output-filter` cannot express it. |

The CLI has no `node update`; directly author node `inputs`, definition swaps, and array splices. For several same-file `Edit`s, anchor each on its target array’s opening key, never top-level key order; beware recurring `"nodes": [` / `"edges": [` inside `definitions[]` and `subflows.<id>`. See [editing-operations.md — Parallel same-file Edits](editing-operations.md#parallel-same-file-edits).

### Scripted structural rewrite

Use only after explicit approval:

```bash
python3 - <<'PY'
import json
flow = json.load(open("<FILE>.flow"))
# Mutate flow here — splice arrays, set nested fields, replace objects.
# Example: insert/overwrite a field on every node of a given type
for node in flow["nodes"]:
    if node.get("type") == "<NODE_TYPE>":
        node.setdefault("inputs", {})["<FIELD>"] = "<VALUE>"
json.dump(flow, open("<FILE>.flow", "w"), indent=2)
PY
uip maestro flow validate <FILE>.flow --output json
```

Preserve canonical 2-space indent. `flow format` normalizes layout but does not re-indent unrelated structure. Whole-file `Write` is lossy and risks clobbering CLI-owned `bindings[]` / `inputs.detail`, especially on files >500 lines or containing connector/managed-HTTP nodes; prefer `Edit` in place.

### `--output-filter` for CLI JSON

Run the CLI’s JMESPath filter for read-only extraction; expressions start at the `Data` envelope and omit `Data.`. See [shared/cli-conventions.md §3](../shared/cli-conventions.md#3-prefer---output-filter-for-extraction).

```bash
uip solution upload --output json --output-filter "DesignerUrl"
uip maestro flow registry get <node-type> --output json --output-filter "Node"
```

Use `jq` / `python3` only when JMESPath cannot express multi-step joins, format conversion, or conditional output computed from multiple fields.

## Primitive Operations

### Add a node

**Tool:** `Edit` into `nodes[]`, `definitions[]`, `variables.nodes`, and `layout.nodes`.

1. Run `uip maestro flow registry get <node-type> --output json`; copy `Data.Node` or the top-level node object verbatim.
2. Add an instance with the required shape:

```json
{
  "id": "<UNIQUE_NODE_ID>",
  "type": "<NODE_TYPE>",
  "typeVersion": "<DEFINITION_VERSION>",
  "display": { "label": "<LABEL>" },
  "inputs": {},
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the <node type> fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

For every node inside a `core.logic.loop` body, add `"parentId": "<LOOP_NODE_ID>"`; otherwise loop context and `$vars.<loopId>.currentItem` are unavailable. See [loop/impl.md](plugins/loop/impl.md).

Every node, including `core.control.end` and `core.logic.terminate`, requires `display: { "label": "<label>" }`. Do not add `ui` or an instance `model`; use layout. Definitions provide BPMN type, `serviceType`, event definition, and binding/context templates. Instance identity belongs in `inputs`: `entryPointId` / `isDefaultEntryPoint` for triggers, `color` / `content` for sticky notes, and `source` for `uipath.agent.autonomous` and every `uipath.agent.resource.*` node. Their definitions declare `model.source: true`; do not write `"model": { "source": ... }`. See [file-format.md — Instance-specific identity fields](../shared/file-format.md#instance-specific-identity-fields).

Orchestrator-job nodes (`api-workflow`, `rpa-workflow`, `agent`, `agentic-process`, `function`) declare `error` only with `source: "=Error"`; `output` is derived. Their converter copies authored `source` verbatim and injects `{name: "output", type: "jsonSchema", source: "=this", var: "output"}` only when non-empty `outputs` omits `output`. A wrong source such as `=result.response` makes downstream `$vars.{nodeId}.output` null while validation passes. Other action/trigger nodes ignore instance `outputs`; End / Terminate nodes are exceptions. See [end/impl.md](plugins/end/impl.md) and [file-format.md — Node outputs](../shared/file-format.md#node-outputs).

3. Add one exact registry definition per unique `type:typeVersion`; match instance `typeVersion` to its `version`.
4. For `uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, `uipath.core.flow.*`, `uipath.core.agentic-process.*`, `uipath.core.api-workflow.*`, or `uipath.core.human-task.*`, add two top-level `bindings[]` entries per resource (`name` and `folderPath`) with `resourceKey` exactly matching `definition.model.bindings.resourceKey`. Keep `<bindings.*>` placeholders verbatim; the emitter rewrites them by `(resourceKey, name)`. Missing entries may pass validation but fail debug with "Folder does not exist or the user does not have access to the folder."
5. Add `variables.nodes` entries for `output` and action-node `error`:

```json
[
  {
    "id": "<NODE_ID>.output",
    "type": "object",
    "description": "<Output description>",
    "binding": { "nodeId": "<NODE_ID>", "outputId": "output" }
  },
  {
    "id": "<NODE_ID>.error",
    "type": "object",
    "description": "Error information if the node fails",
    "binding": { "nodeId": "<NODE_ID>", "outputId": "error" }
  }
]
```

6. Add this placeholder to top-level `layout.nodes`:

```json
"<UNIQUE_NODE_ID>": {
  "position": { "x": 0, "y": 0 },
  "size": { "width": 96, "height": 96 },
  "collapsed": false
}
```

Run `uip maestro flow format <ProjectName>.flow` after structural edits. It regenerates `variables.nodes[]`, arranges nodes horizontally, sets canvas sizes (inline agents 288×96, containers 560×320, others 96×96), and recurses into subflows. Do not calculate coordinates manually.

### Delete a node

**Tool:** `Edit`.

1. Remove it from `nodes[]`.
2. Remove all edges whose `sourceNodeId` or `targetNodeId` is its ID.
3. Remove its definition only if no node uses that `type`.
4. Remove its `variables.nodes` entry and `variableUpdates` entries keyed by its ID.
5. For connector nodes, remove the `bindings_v2.json` binding only if no other node uses that connector; bindings are shared by connector level and keyed by `metadata.Connector`.

### Add an edge

**Tool:** `Edit` into `edges[]`:

```json
{
  "id": "edge_<SOURCE_NODE_ID>_<SOURCE_PORT>_<TARGET_NODE_ID>_<TARGET_PORT>",
  "sourceNodeId": "<SOURCE_NODE_ID>",
  "sourcePort": "<SOURCE_PORT>",
  "targetNodeId": "<TARGET_NODE_ID>",
  "targetPort": "<TARGET_PORT>"
}
```

The ID must exactly follow that pattern, never be a bare UUID or start with a digit. `targetPort` is mandatory; use `sourcePort`, not `sourceHandle`. For `sourcePort: "error"`, set source `inputs.errorHandlingEnabled: true`, and never set that flag without an `error` edge. Look up ports in plugin `planning.md` or [file-format.md — Standard ports](../shared/file-format.md).

### Delete an edge

**Tool:** `Edit`; remove the edge by its `id`.

### Update node inputs

**Tool:** `Edit` in place; preserve node IDs and `$vars` references.

```json
{
  "id": "checkStatus",
  "type": "core.logic.decision",
  "inputs": { "expression": "$vars.fetchData.output.statusCode === 200" }
}
```

## Variable Operations

These are `Edit`-only; the CLI has no variable-management fallback.

### Add a workflow variable

Add to `variables.globals`:

```json
{
  "id": "<VARIABLE_ID>",
  "direction": "in|out|inout",
  "type": "string|number|boolean|object|array|file",
  "defaultValue": "<OPTIONAL_DEFAULT>",
  "description": "<OPTIONAL_DESCRIPTION>"
}
```

Map every `out` variable on every reachable End node. Add `variableUpdates` for nodes modifying `inout` state. Attachment-carrying inputs must use `"type": "file"`, not `"object"`, or attachment binding breaks and IxP extraction faults with `[430002]`; see [plugins/ixp/impl.md#debug](plugins/ixp/impl.md#debug). See [variables-and-expressions.md](../shared/variables-and-expressions.md).

### Add output mapping on an End node

On every reachable End node, map every `out` variable:

```json
{
  "id": "doneSuccess",
  "type": "core.control.end",
  "typeVersion": "1.0.0",
  "display": { "label": "Done" },
  "inputs": {},
  "outputs": { "<VARIABLE_ID>": { "source": "=js:<EXPRESSION>" } }
}
```

Each key must match an `out` variable ID; missing mappings silently fail at runtime.

### Add a variable update

Add under `variables.variableUpdates.<NODE_ID>`:

```json
{
  "variables": {
    "variableUpdates": {
      "<NODE_ID>": [
        {
          "variableId": "<INOUT_VARIABLE_ID>",
          "expression": {
            "type": "jsExpression",
            "expression": "<BARE_JS_NO_PREFIX>",
            "fieldType": "<TARGET_VARIABLE_TYPE>"
          }
        }
      ]
    }
  }
}
```

Only `inout` variables can be updated; `in` variables are read-only. `expression` is an object, not a `=js:` string. Set `fieldType` to the declared target type (`integer` → `number`); validation does not cross-check mismatches. The string form fails with `[MIGRATION] Workflow migration failed at 1.9→1.10 … Offending field(s): variables.variableUpdates.<NODE_ID>.0.expression`. No CLI command exists for variable updates.

## Composite Operations

### Insert a node between two existing nodes

**Tool:** `Edit` × 3: delete the old edge; add the node, definition, variables, and layout; add upstream → new and new → downstream edges with valid source and target ports.

### Insert a decision branch

**Tool:** `Edit` × 3: delete the old edge; add the decision with `inputs.expression`; add upstream → decision (`targetPort: "input"`), decision → true (`sourcePort: "true"`, `targetPort: "input"`), and decision → false (`sourcePort: "false"`, `targetPort: "input"`) edges.

### Remove a node and reconnect

**Tool:** `Edit` × 4: record upstream/downstream edges; remove the node and incident edges; prune orphan definitions; add the direct reconnect edge.

### Replace a mock with a real resource node

**Tool:** `Edit` multiple calls.

1. Check in-solution first and run `uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --local --output json`; if unavailable, run `uip maestro flow registry get "<RESOURCE_NODE_TYPE>" --output json`.
2. Record mock connections; remove the mock and incident edges.
3. Add the real node with correct `type`, exact `typeVersion`, resolved `inputs`, action-node `outputs` (`output` + `error`), and no `model` block.
4. Copy its registry definition verbatim.
5. Add two top-level `bindings[]` entries per resource (`name` + `folderPath`) with matching `resourceKey`.
6. Re-create edges with the new ID and add `variables.nodes` entries.
7. Run `uip maestro flow validate <ProjectName>.flow --output json`.

### Replace manual trigger with scheduled trigger

**Tool:** `Edit` × 2.

1. Change `core.trigger.manual` to `core.trigger.scheduled` in place and retain `entryPointId`:

```json
"inputs": {
  "entryPointId": "<existing-uuid>",
  "timerType": "timeCycle",
  "timerPreset": "R/PT1H"
}
```

2. Replace the manual definition with the exact definition from `uip maestro flow registry get core.trigger.scheduled --output json`.
3. Run `uip maestro flow validate <ProjectName>.flow --output json`.

### Create a subflow

**Tool:** `Edit` (or `Write` when scaffolding from a template).

1. Add a `core.subflow` parent with `display`, inputs, and error output (the JSON below pins `typeVersion`):

```json
{
  "id": "<SUBFLOW_NODE_ID>",
  "type": "core.subflow",
  "typeVersion": "1.0.0",
  "display": { "label": "<LABEL>" },
  "inputs": { "<IN_VAR>": "=js:<EXPRESSION>" },
  "outputs": {
    "error": {
      "type": "object",
      "description": "Error information if the subflow fails",
      "source": "=Error",
      "var": "error"
    }
  }
}
```

2. Add `subflows.<SUBFLOW_NODE_ID>` with independent `nodes`, `edges`, `variables`, and `layout`; its variables include `in` variables with `triggerNodeId`, `out` variables, and `variables.nodes`.
3. Match subflow `in` variable IDs to parent input keys; map every `out` variable on its End node.
4. Parent `$vars` are not visible inside; pass values through inputs.
5. Put subflow positions in its own `layout.nodes`, never top-level layout. See [subflow/impl.md](plugins/subflow/impl.md).

## Connector Node Configuration (Edit / Write fallback)

Prefer `uip maestro flow node configure`. If using the fallback, use `Edit` for node configuration and `Edit` (or `Write` for a fresh file) for `bindings_v2.json`.

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
      "queryParameters": { "<FIELD>": "<VALUE>" },
      "pathParameters": { "<PLACEHOLDER>": "<VALUE>" }
    }
  }
}
```

Source metadata from either command. Run `uip maestro flow registry get <node-type> --connection-id <id> --output json`: `method` ← `connectorMethodInfo.method`; `endpoint` ← `connectorMethodInfo.path`; `bodyParameters.<name>` ← `inputDefinition.fields[].name`; `queryParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: query`; `pathParameters.<name>` ← `connectorMethodInfo.parameters[]` where `type: path`, matching a `{placeholder}` in `endpoint`.

Or run `uip is resources describe <connector-key> <objectName> --connection-id <id> --operation <Op> --output json`: `method` ← `availableOperations[].method`; `endpoint` ← `availableOperations[].path`; `bodyParameters.<name>` ← `requestFields[].name`; `queryParameters.<name>` ← `parameters[]` where `type: query`; `pathParameters.<name>` ← `parameters[]` where `type: path`, matching a `{placeholder}` in `endpoint`.

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

See [connector/impl.md](plugins/connector/impl.md) for the complete schema and multi-connector examples.