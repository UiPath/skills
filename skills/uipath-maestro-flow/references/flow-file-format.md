# UiPath Flow File Format

The `.flow` file is a JSON document at `<ProjectName>.flow` in the project root. It is the **only file you should edit** — other generated files will be overwritten.

## Top-level structure

```json
{
  "id": "<uuid>",
  "version": "1.0.0",
  "name": "MyFlow",
  "nodes": [],
  "edges": [],
  "definitions": [],
  "bindings": [],
  "variables": {},
  "layout": {
    "nodes": {}
  }
}
```

`solutionId` and `projectId` may also appear at the top level — these are auto-populated by `uip maestro flow init` and packaging. Do not add them manually.

> **`bindings[]`** holds Orchestrator resource references for `uipath.core.*` resource nodes (rpa, agent, flow, agentic-process, api-workflow, hitl) and for connector-node connections. See [Bindings — Orchestrator resource bindings](#bindings--orchestrator-resource-bindings-top-level-bindings) below and the [connector plugin](plugins/connector/impl.md) for the connector-binding shape.

## Project structure (from `uip maestro flow init`)

```
<ProjectName>/
├── project.uiproj          # { "Name": "...", "ProjectType": "Flow" }
├── <ProjectName>.flow      # ← edit this
├── bindings_v2.json        # resource bindings
├── entry-points.json       # input/output schema declarations
├── operate.json            # runtime options
└── package-descriptor.json # packaging manifest
```

## Node instance

```json
{
  "id": "rollDice",
  "type": "core.action.script",
  "typeVersion": "1.0.0",
  "display": { "label": "Roll Dice" },
  "inputs": {
    "script": "return { roll: Math.floor(Math.random() * 6) + 1 };"
  },
  "outputs": {
    "output": {
      "type": "object",
      "description": "The return value of the script",
      "source": "=result.response",
      "var": "output"
    },
    "error": {
      "type": "object",
      "description": "Error information if the script fails",
      "source": "=result.Error",
      "var": "error"
    }
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Required fields**: `id`, `type`, `typeVersion`

> **No `ui` block on nodes.** Position and size are stored in the top-level `layout` object, not on individual nodes. See [Layout](#layout) below.

### Node outputs

Nodes that produce data consumed by downstream nodes **must** include an `outputs` block on the node instance. This tells the runtime how to capture the node's results into `$vars.{nodeId}.{outputId}`. Without it, downstream `$vars` references may not resolve.

Each output entry has:

- `type` — data type (usually `"object"`)
- `description` — human-readable description
- `source` — runtime binding expression (e.g., `"=result.response"` for the primary output, `"=result.Error"` for errors)
- `var` — the variable name (matches the output ID, e.g., `"output"`, `"error"`)

The standard `outputs` block for most action nodes (script, HTTP, transform, connector, agent):

```json
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
```

Trigger nodes (manual, scheduled, connector triggers) have a single output — no error port:

```json
"outputs": {
  "output": {
    "type": "object",
    "description": "The return value of the trigger.",
    "source": "=result.response",
    "var": "output"
  }
}
```

End/terminate nodes do **not** use this pattern — their `outputs` maps workflow-level output variables (see [end/impl.md](plugins/end/impl.md)).

## Layout

Node positioning is stored in a **top-level `layout` object**, not on individual nodes. Do NOT put `ui` or `position` on node instances.

> **Size rule — `{ "width": 96, "height": 96 }` on every node.** The file format stores **expanded** dimensions. For every standard flow node (triggers, actions, decisions, switches, loops, merges, ends, scripts, HTTP, transforms, connectors, agents, RPA, subflows), size is always `{ "width": 96, "height": 96 }`. Do NOT use rectangular dimensions like `{ "width": 200, "height": 80 }` — those render as rectangles in Studio Web. Do NOT omit `size` — the canvas falls back to an expanded-shape default that may not be 96×96. Always emit size explicitly on every `layout.nodes.<id>` entry.

```json
"layout": {
  "nodes": {
    "start": {
      "position": { "x": 200, "y": 144 },
      "size": { "width": 96, "height": 96 },
      "collapsed": false
    },
    "rollDice": {
      "position": { "x": 400, "y": 144 },
      "size": { "width": 96, "height": 96 },
      "collapsed": false
    },
    "end": {
      "position": { "x": 600, "y": 144 },
      "size": { "width": 96, "height": 96 },
      "collapsed": false
    }
  }
}
```

Each key in `layout.nodes` is a node `id`. Every node in the `nodes` array should have a corresponding entry.

**Layout rules:**
- Horizontal canvas — place nodes left-to-right with increasing `x` (spacing ~200px) and a consistent `y` baseline (e.g., `y: 144`)
- For decision branches, offset the `y` value for each branch path
- Size is **always** `{ "width": 96, "height": 96 }` (see Size rule above) — never rectangular, never omitted
- Never use vertical (top-to-bottom) layout

**Subflow layout is scoped.** Each subflow entry in `subflows.<id>` has its **own** `layout.nodes` map for the nodes inside that subflow. Do NOT put subflow node positions in the top-level `layout.nodes` — they live alongside the subflow's `nodes`/`edges`/`variables`. See [subflow/impl.md](plugins/subflow/impl.md).

## Edge — both ports required

```json
{
  "id": "edge-start-rollDice",
  "sourceNodeId": "start",
  "sourcePort": "output",
  "targetNodeId": "rollDice",
  "targetPort": "input"
}
```

> **Gotcha**: `targetPort` is required. Omitting it produces `[error] [edges.N.targetPort] expected string, received undefined` at validate time.

## Definition entry

Every node type appearing in `nodes` must have a matching entry in `definitions`. Get the correct definition from:

```bash
uip maestro flow registry get core.action.script --output json
```

Copy the object at `Data.Node` into your `definitions` array. Do not write definitions by hand — always pull from the registry to ensure schema compliance.

## Common node types

| Type | Purpose | `model.type` | Key inputs |
|------|---------|--------------|------------|
| `core.trigger.manual` | Entry point | `bpmn:StartEvent` | — |
| `core.action.script` | Run JavaScript | `bpmn:ScriptTask` | `script` |
| `core.action.http` | HTTP request | `bpmn:ServiceTask` | `method`, `url`, `headers`, `body` |
| `core.action.transform` | Map/filter/group data | `bpmn:ScriptTask` | `collection`, `operations` |
| `core.logic.decision` | If/else branch | `bpmn:InclusiveGateway` | `expression` |
| `core.logic.switch` | Multi-way branch | `bpmn:ExclusiveGateway` | `cases` |
| `core.logic.loop` | Iterate collection | `bpmn:SubProcess` | `collection`, `parallel` |
| `core.logic.merge` | Sync parallel paths | `bpmn:ParallelGateway` | — |
| `core.control.end` | Graceful end | `bpmn:EndEvent` | — |
| `core.logic.terminate` | Abort workflow | `bpmn:EndEvent` | — |

For full details on each node (ports, inputs, outputs, when to use), see [planning-arch.md](planning-arch.md). For implementation resolution (registry lookups, connection binding, reference field resolution), see [planning-impl.md](planning-impl.md).

Discover all available types:
```bash
uip maestro flow registry list --output json
uip maestro flow registry search <keyword>
```

## Standard ports by node type

| Node type | Source ports (outgoing) | Target ports (incoming) |
|-----------|------------------------|------------------------|
| `core.trigger.manual` | `output` | — |
| `core.action.script` | `success`, `error` | `input` |
| `core.action.http` | `default`, `error`, `branch-{id}` (dynamic) | `input` |
| `core.action.transform` | `output`, `error` | `input` |
| `core.logic.decision` | `true`, `false` | `input` |
| `core.logic.switch` | `case-{id}` (dynamic), `default` | `input` |
| `core.logic.loop` | `success`, `output` | `input`, `loopBack` |
| `core.logic.merge` | `output` | `input` |
| `core.control.end` | — | `input` |
| `core.logic.terminate` | — | `input` |

Connector activities, agent nodes, and RPA nodes follow the same pattern as the generic action nodes above: a primary source port plus an implicit `error` port.

Verify exact ports for any node type:
```bash
uip maestro flow registry get <nodeType> --output json
# Look at Data.Node.handleConfiguration[].handles[].id
# Also check Data.Node.supportsErrorHandling — see "Implicit error port" below
```

## Implicit error port on action nodes

Any node with `supportsErrorHandling: true` in the registry exposes an implicit `error` source port for catching node-level failures. This applies to HTTP, Script, Transform (all variants), connector activities, agent nodes, and RPA nodes — essentially every action node.

The port is **not** listed in the registry's `handleConfiguration`. It's only visible at serialization time: when the flow contains an outgoing edge with `sourcePort: "error"` from the node, the serializer emits a BPMN boundary error event attached to the node.

### When the error port fires

- Network failures, DNS errors, TLS errors
- Request timeouts
- Non-2xx HTTP responses (unless caught by a configured `inputs.branches` entry)
- Script exceptions (`throw`, undefined reference, etc.)
- Transform operation failures (invalid collection, missing field)
- Any unhandled runtime exception inside the node

Without a wired error edge, any of these fails the whole flow with `finalStatus: "Faulted"`.

### Wiring the error port

```bash
# Confirm the node supports error handling
uip flow registry get <nodeType> --output json \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['Data']['Node'].get('supportsErrorHandling'))"

# Add an outgoing edge with sourcePort: "error"
uip flow edge add <Project>.flow <actionNodeId> <errorHandlerId> \
  --source-port error --target-port input --output json
```

Inside the error handler, `$vars.{actionNodeId}.error` resolves to the error object. For HTTP it's `{ code, message, detail, category, status }`; other nodes have similar shapes — check the node's `outputDefinition.error.schema` in the registry.

### Error port vs other branching

| Mechanism | When to use |
| --- | --- |
| **`error` source port** (any action node) | The node failed (exception, timeout, non-2xx not caught by a branch). Generic "something went wrong" handler. |
| **`branch-{id}` ports** (HTTP only, `inputs.branches`) | The call succeeded and you want to route on response *content* — different paths for e.g. empty vs non-empty results. |
| **`core.logic.decision` downstream** | Simple yes/no routing on the node's successful output. Doesn't help if the node itself fails. |
| **`core.logic.switch` downstream** | Multi-way routing on the node's successful output. Same — doesn't catch failures. |

## Minimal working example — dice roller

Building a flow is a two-step process: write the nodes/edges structure, then populate `definitions` from the registry.

### Step 1 — Write nodes and edges

Replace `<uuid>` with any generated UUID (e.g. `crypto.randomUUID()` in Node.js, or any UUID v4 generator). The same UUID must appear in `entry-points.json` as `uniqueId`.

```json
{
  "id": "3d4a8c34-5682-4ebe-a6bc-d92a18830bb5",
  "version": "1.0.0",
  "name": "DiceRoller",
  "nodes": [
    {
      "id": "start",
      "type": "core.trigger.manual",
      "typeVersion": "1.0.0",
      "inputs": {},
      "outputs": {
        "output": {
          "type": "object",
          "description": "The return value of the trigger.",
          "source": "=result.response",
          "var": "output"
        }
      },
      "model": { "type": "bpmn:StartEvent", "entryPointId": "<uuid>" }
    },
    {
      "id": "rollDice",
      "type": "core.action.script",
      "typeVersion": "1.0.0",
      "display": { "label": "Roll Dice" },
      "inputs": {
        "script": "return { roll: Math.floor(Math.random() * 6) + 1 };"
      },
      "outputs": {
        "output": {
          "type": "object",
          "description": "The return value of the script",
          "source": "=result.response",
          "var": "output"
        },
        "error": {
          "type": "object",
          "description": "Error information if the script fails",
          "source": "=result.Error",
          "var": "error"
        }
      },
      "model": { "type": "bpmn:ScriptTask" }
    },
    {
      "id": "end",
      "type": "core.logic.terminate",
      "typeVersion": "1.0.0",
      "inputs": {},
      "model": { "type": "bpmn:EndEvent", "eventDefinition": "bpmn:TerminateEventDefinition" }
    }
  ],
  "edges": [
    {
      "id": "edge-start-roll",
      "sourceNodeId": "start",
      "sourcePort": "output",
      "targetNodeId": "rollDice",
      "targetPort": "input"
    },
    {
      "id": "edge-roll-end",
      "sourceNodeId": "rollDice",
      "sourcePort": "success",
      "targetNodeId": "end",
      "targetPort": "input"
    }
  ],
  "definitions": [],
  "bindings": [],
  "variables": {},
  "layout": {
    "nodes": {
      "start": {
        "position": { "x": 200, "y": 144 },
        "size": { "width": 96, "height": 96 },
        "collapsed": false
      },
      "rollDice": {
        "position": { "x": 400, "y": 144 },
        "size": { "width": 96, "height": 96 },
        "collapsed": false
      },
      "end": {
        "position": { "x": 600, "y": 144 },
        "size": { "width": 96, "height": 96 },
        "collapsed": false
      }
    }
  }
}
```

### Step 2 — Populate definitions from the registry

Run one command per node type used in `nodes`. Copy the `Data.Node` object from each response into the `definitions` array.

```bash
uip maestro flow registry get core.trigger.manual --output json
uip maestro flow registry get core.action.script --output json
uip maestro flow registry get core.logic.terminate --output json
```

The `definitions` array must contain exactly one entry per unique `type` used — not one per node instance. If two nodes share the same type, one definition covers both.

> **Never write definitions by hand.** The registry is the authoritative source; hand-written definitions will fail validation or cause runtime errors.

## entry-points.json — auto-generated, do not edit

`entry-points.json` declares the flow's external interface (input/output schemas and trigger entry points). **Do not edit this file directly** — it is auto-generated by `uip maestro flow init` and regenerated by `uip maestro flow debug` before upload. Manual edits will be overwritten.

Flow input and output parameters are declared through **variables** in the `.flow` file:
- **Flow inputs**: Add output variables to the start node (`variables.nodes.start.outputs`) — the start node "outputs" input values to downstream nodes
- **Flow outputs**: Add output variables to the end/terminate node
- Downstream nodes reference inputs via `$vars.start.output.<paramName>`

The packaging/debug step derives `entry-points.json` from these variable declarations.

## Bindings — Orchestrator resource bindings (top-level `bindings[]`)

The top-level `bindings` array (a sibling of `nodes`, `edges`, `definitions`, `variables`, `layout`) holds resource-reference indirections for **Orchestrator resource nodes** — RPA workflows, agents, flows, agentic processes, API workflows, and HITL apps.

Each entry gives a node instance's `model.context[]` a resolvable target for the `name` and `folderPath` attributes it passes to Orchestrator:

```json
"bindings": [
  {
    "id": "<UNIQUE_ID>",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<FolderPath>.<ResourceName>",
    "default": "<ResourceName>",
    "propertyAttribute": "name",
    "resourceSubType": "Process"
  },
  {
    "id": "<UNIQUE_ID_2>",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "<FolderPath>.<ResourceName>",
    "default": "<FolderPath>",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Process"
  }
]
```

**Rules:**

- Add **two entries** per resource node (one for `name`, one for `folderPath`).
- **Share** entries across node instances that reference the same resource — do not duplicate.
- Entry IDs are unique strings within the file. Descriptive IDs (e.g. `bDepositRpaName`) are preferred over short random IDs.
- The node instance's `model.context[].value` references an entry via `"value": "=bindings.<id>"`.
- `resourceSubType` mirrors the node's `model.bindings.resourceSubType`: `Process` (rpa), `Agent` (agent), `Flow` (flow), `ProcessOrchestration` (agentic-process), `Api` (api-workflow), or the app type for HITL.

**Why this is required.** The registry's `Data.Node.model.context[].value` fields are template placeholders (`<bindings.name>`, `<bindings.folderPath>`) — they are NOT runtime-resolvable. The runtime reads the node instance's `model.context` and resolves `=bindings.<id>` against the top-level `bindings[]` array. Without both pieces, `uip maestro flow debug` fails with "Folder does not exist or the user does not have access to the folder" even though `uip maestro flow validate` passes.

**Definitions stay verbatim.** Do NOT rewrite `<bindings.*>` placeholders inside the `definitions` entry — the definition is a schema copy, not a runtime input. Critical Rule #7 applies unchanged.

See each resource plugin's `impl.md` for the full JSON per node type: [rpa](plugins/rpa/impl.md), [agent](plugins/agent/impl.md), [flow](plugins/flow/impl.md), [agentic-process](plugins/agentic-process/impl.md), [api-workflow](plugins/api-workflow/impl.md), [hitl](plugins/hitl/impl.md).

**Not to be confused with `bindings_v2.json`.** That file holds connector connection bindings for Integration Service nodes — a separate system. A flow may have both: a top-level `bindings[]` for resource references and a `bindings_v2.json` file for connector connections.

## Bindings — connector connection binding

When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. This is configured in `content/bindings_v2.json`.

See the relevant node guide in `nodes/` for the full `bindings_v2.json` schema, connection resource field reference, JSON examples, and the connection fetching workflow.
