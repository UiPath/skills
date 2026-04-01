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

For full details on each node (ports, inputs, outputs, when to use), see [planning-phase-architectural.md](planning-phase-architectural.md). For implementation resolution (registry lookups, connection binding, reference field resolution), see [planning-phase-implementation.md](planning-phase-implementation.md).

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

When a flow uses Integration Service connector nodes (e.g., Jira, Slack, Salesforce), the runtime needs to know **which authenticated connection** to use for each connector. This is configured in `content/bindings_v2.json`.

### How connector nodes reference bindings

Each connector node's `model.context` contains a `connection` entry with a placeholder:

```json
{ "name": "connection", "type": "string", "value": "<bindings.uipath-atlassian-jira connection>" }
```

At runtime, the engine resolves this placeholder by looking up `bindings_v2.json` for a `Connection` resource whose `metadata.Connector` matches `uipath-atlassian-jira`.

### bindings_v2.json schema

```json
{
  "version": "2.0",
  "resources": []
}
```

Each element in `resources` is a binding resource. For connector activities, the key resource type is **`Connection`**.

### Connection resource

| Field | Description |
|-------|-------------|
| `resource` | Always `"Connection"` |
| `key` | The connection ID (UUID from `uip is connections list`) |
| `id` | `"Connection" + <connection-id>` (concatenated, no separator) |
| `value.ConnectionId.defaultValue` | The actual connection ID |
| `value.ConnectionId.isExpression` | Always `false` |
| `value.ConnectionId.displayName` | Human-readable label (e.g., `"uipath-atlassian-jira connection"`) |
| `metadata.UseConnectionService` | Always `"true"` |
| `metadata.Connector` | Connector key (e.g., `"uipath-atlassian-jira"`) — must match the node's `model.context.connectorKey` |
| `metadata.ActivityName` | Display name of the activity using this connection |
| `metadata.BindingsVersion` | Always `"2.2"` |
| `metadata.DisplayLabel` | Same as `value.ConnectionId.displayName` |

### Single connector example (Jira)

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "7622a703-5d85-4b55-849b-6c02315b9e6e",
      "id": "Connection7622a703-5d85-4b55-849b-6c02315b9e6e",
      "value": {
        "ConnectionId": {
          "defaultValue": "7622a703-5d85-4b55-849b-6c02315b9e6e",
          "isExpression": false,
          "displayName": "uipath-atlassian-jira connection"
        }
      },
      "metadata": {
        "ActivityName": "Create Issue",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-atlassian-jira connection",
        "UseConnectionService": "true",
        "Connector": "uipath-atlassian-jira"
      }
    }
  ]
}
```

### Multi-connector example (Jira + Slack)

When a flow uses multiple connectors, add one `Connection` resource per unique connector:

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "Connection",
      "key": "7622a703-5d85-4b55-849b-6c02315b9e6e",
      "id": "Connection7622a703-5d85-4b55-849b-6c02315b9e6e",
      "value": {
        "ConnectionId": {
          "defaultValue": "7622a703-5d85-4b55-849b-6c02315b9e6e",
          "isExpression": false,
          "displayName": "uipath-atlassian-jira connection"
        }
      },
      "metadata": {
        "ActivityName": "Create Issue",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-atlassian-jira connection",
        "UseConnectionService": "true",
        "Connector": "uipath-atlassian-jira"
      }
    },
    {
      "resource": "Connection",
      "key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "id": "Connectiona1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "value": {
        "ConnectionId": {
          "defaultValue": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          "isExpression": false,
          "displayName": "uipath-salesforce-slack connection"
        }
      },
      "metadata": {
        "ActivityName": "Send Message to Channel",
        "BindingsVersion": "2.2",
        "DisplayLabel": "uipath-salesforce-slack connection",
        "UseConnectionService": "true",
        "Connector": "uipath-salesforce-slack"
      }
    }
  ]
}
```

### Other resource types

Beyond `Connection`, `bindings_v2.json` can contain other resource types for trigger-based flows:

| Resource type | When used | Key fields |
|---------------|-----------|------------|
| `EventTrigger` | Connector trigger nodes (e.g., "Issue Created") | `metadata.Operation`, `metadata.ObjectName` |
| `Property` | Trigger filter parameters | `value.<param>.defaultValue`, `metadata.ParentResourceKey` |
| `Queue` | Queue trigger bindings | Queue name and folder |
| `TimeTrigger` | Scheduled triggers | Cron expression |

For manual-trigger flows with connector activities, you only need `Connection` resources.

### Workflow: fetching the connection ID

```bash
# 1. List connections for the connector
uip is connections list "uipath-atlassian-jira" --output json
# → Pick the one with IsDefault: Yes, State: Enabled

# 2. Verify it's healthy
uip is connections ping "<connection-id>" --output json

# 3. Write into bindings_v2.json
```

> **Never hardcode connection IDs.** Always fetch them from IS at authoring time. Connection IDs are tenant-specific and change across environments.
