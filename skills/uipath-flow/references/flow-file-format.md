# UiPath Flow File Format

The `.flow` file is a JSON document in `flow_files/<ProjectName>.flow`. It is the **only file you should edit** — `content/*.bpmn` is auto-generated from it.

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
├── project.uiproj                   # { "Name": "...", "ProjectType": "Flow" }
├── flow_files/
│   └── <ProjectName>.flow           # ← edit this
└── content/
    ├── <ProjectName>.bpmn           # auto-generated — DO NOT edit
    ├── entry-points.json            # input/output schema declarations
    ├── operate.json                 # runtime options
    ├── bindings_v2.json             # resource bindings
    └── package-descriptor.json     # packaging manifest
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
uip flow registry get core.action.script --format json
```

Copy the object at `Data.Node` into your `definitions` array. Do not write definitions by hand — always pull from the registry to ensure schema compliance.

## Common node types

| Type | Purpose | `model.type` | Key inputs |
|------|---------|--------------|------------|
| `core.trigger.manual` | Entry point | `bpmn:StartEvent` | — |
| `core.action.script` | Run JavaScript | `bpmn:ScriptTask` | `script` |
| `core.action.http` | HTTP request | `bpmn:ServiceTask` | `url`, `method`, `headers`, `body` |
| `core.action.transform` | Map/filter/group data | `bpmn:ScriptTask` | `expression` |
| `core.logic.terminate` | End event | `bpmn:EndEvent` | — |
| `core.logic.condition` | Branch on expression | `bpmn:Gateway` | `expression` |

Discover all available types:
```bash
uip flow registry list --format json
uip flow registry search <keyword>
```

## Standard ports by node type

| Node type | Source ports (outgoing) | Target ports (incoming) |
|-----------|------------------------|------------------------|
| `core.trigger.manual` | `output` | — |
| `core.action.script` | `success`, `error` | `input` |
| `core.action.http` | `success`, `error` | `input` |
| `core.action.transform` | `success`, `error` | `input` |
| `core.logic.terminate` | — | `input` |
| `core.logic.condition` | `true`, `false` | `input` |

Verify exact ports for any node type:
```bash
uip flow registry get <nodeType> --format json
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
uip flow registry get core.trigger.manual --format json
uip flow registry get core.action.script --format json
uip flow registry get core.logic.terminate --format json
```

The `definitions` array must contain exactly one entry per unique `type` used — not one per node instance. If two nodes share the same type, one definition covers both.

> **Never write definitions by hand.** The registry is the authoritative source; hand-written definitions will fail validation or cause runtime errors.

## entry-points.json — declaring outputs

To expose flow outputs (so callers can read them), declare them in `content/entry-points.json`:

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "/content/<ProjectName>.bpmn#start",
      "uniqueId": "<same-uuid-as-trigger-entryPointId>",
      "type": "processorchestration",
      "input": { "type": "object", "properties": {} },
      "output": {
        "type": "object",
        "properties": {
          "roll": { "type": "integer", "description": "Dice roll result (1-6)" }
        }
      },
      "displayName": "Manual trigger"
    }
  ]
}
```

The `uniqueId` must match the `entryPointId` field in your `core.trigger.manual` node's `model`.
