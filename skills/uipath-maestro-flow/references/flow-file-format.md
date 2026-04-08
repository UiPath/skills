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
  "metadata": {
    "createdAt": "2026-01-01T00:00:00.000Z",
    "updatedAt": "2026-01-01T00:00:00.000Z"
  }
}
```

## Project structure (from `uip flow init`)

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
  "ui": {
    "position": { "x": 400, "y": 144 },
    "size": { "width": 96, "height": 96 },
    "collapsed": false
  },
  "display": { "label": "Roll Dice" },
  "inputs": {
    "script": "return { roll: Math.floor(Math.random() * 6) + 1 };"
  },
  "model": { "type": "bpmn:ScriptTask" }
}
```

**Required fields**: `id`, `type`, `typeVersion`, `ui.position`

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
uip flow registry get core.action.script --output json
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
uip flow registry list --output json
uip flow registry search <keyword>
```

## Standard ports by node type

| Node type | Source ports (outgoing) | Target ports (incoming) |
|-----------|------------------------|------------------------|
| `core.trigger.manual` | `output` | — |
| `core.action.script` | `success` | `input` |
| `core.action.http` | `branch-{id}` (dynamic), `default` | `input` |
| `core.action.transform` | `output` | `input` |
| `core.logic.decision` | `true`, `false` | `input` |
| `core.logic.switch` | `case-{id}` (dynamic), `default` | `input` |
| `core.logic.loop` | `success`, `output` | `input`, `loopBack` |
| `core.logic.merge` | `output` | `input` |
| `core.control.end` | — | `input` |
| `core.logic.terminate` | — | `input` |

Verify exact ports for any node type:
```bash
uip flow registry get <nodeType> --output json
# Look at Data.Node.handleConfiguration[].handles[].id
```

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
      "ui": { "position": { "x": 200, "y": 144 } },
      "inputs": {},
      "model": { "type": "bpmn:StartEvent", "entryPointId": "<uuid>" }
    },
    {
      "id": "rollDice",
      "type": "core.action.script",
      "typeVersion": "1.0.0",
      "ui": { "position": { "x": 400, "y": 144 } },
      "display": { "label": "Roll Dice" },
      "inputs": {
        "script": "return { roll: Math.floor(Math.random() * 6) + 1 };"
      },
      "model": { "type": "bpmn:ScriptTask" }
    },
    {
      "id": "end",
      "type": "core.logic.terminate",
      "typeVersion": "1.0.0",
      "ui": { "position": { "x": 600, "y": 144 } },
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
  "variables": {}
}
```

### Step 2 — Populate definitions from the registry

Run one command per node type used in `nodes`. Copy the `Data.Node` object from each response into the `definitions` array.

```bash
uip flow registry get core.trigger.manual --output json
uip flow registry get core.action.script --output json
uip flow registry get core.logic.terminate --output json
```

The `definitions` array must contain exactly one entry per unique `type` used — not one per node instance. If two nodes share the same type, one definition covers both.

> **Never write definitions by hand.** The registry is the authoritative source; hand-written definitions will fail validation or cause runtime errors.

## entry-points.json — auto-generated, do not edit

`entry-points.json` declares the flow's external interface (input/output schemas and trigger entry points). **Do not edit this file directly** — it is auto-generated by `uip flow init` and regenerated by `uip flow debug` before upload. Manual edits will be overwritten.

Flow input and output parameters are declared through **variables** in the `.flow` file:
- **Flow inputs**: Add output variables to the start node (`variables.nodes.start.outputs`) — the start node "outputs" input values to downstream nodes
- **Flow outputs**: Add output variables to the end/terminate node
- Downstream nodes reference inputs via `$vars.start.output.<paramName>`

The packaging/debug step derives `entry-points.json` from these variable declarations.

## Bindings — connector connection binding

When a flow uses connector nodes, the runtime needs to know **which authenticated connection** to use for each connector. This is configured in `content/bindings_v2.json`.

See the relevant node guide in `nodes/` for the full `bindings_v2.json` schema, connection resource field reference, JSON examples, and the connection fetching workflow.
