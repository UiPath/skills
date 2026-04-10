# Bindings Guide

Bindings connect flow nodes to external resources at runtime. There are two distinct binding systems depending on node type:

| System | Scope | Used By |
|--------|-------|---------|
| `bindings_v2.json` | Project-level file in the project root | Connector nodes (`uipath.connector.*`) |
| `workflow.bindings[]` | Array inside the `.flow` file | Resource nodes (RPA workflow, agent, API workflow, agentic process) |

---

## When Bindings Are Needed

- **OOTB-only flows** (triggers, scripts, HTTP, logic, transforms) -- no bindings required. `bindings_v2.json` stays empty or absent.
- **Connector nodes** (`uipath.connector.*`) -- require a `Connection` resource in `bindings_v2.json` to authenticate via Integration Service at runtime.
- **Resource nodes** (`uipath.core.rpa-workflow.*`, `uipath.core.agent.*`, etc.) -- require 2 entries in `workflow.bindings[]` plus `model.context` references on the node instance. They do NOT use `bindings_v2.json`.

---

## `bindings_v2.json` -- Connector Nodes

### Schema

```json
{
  "version": "2.0",
  "resources": []
}
```

Each element in `resources` is a binding resource. For connector activities, the resource type is **`Connection`**.

### OOTB-Only Flows (Empty)

Flows that use only OOTB nodes have no resources:

```json
{
  "version": "2.0",
  "resources": []
}
```

### Connection Resource Format

| Field | Description |
|-------|-------------|
| `resource` | Always `"Connection"` |
| `key` | The connection ID (UUID from `uip is connections list`) |
| `id` | `"Connection"` + `<connection-id>` (concatenated, no separator) |
| `value.ConnectionId.defaultValue` | The actual connection ID |
| `value.ConnectionId.isExpression` | Always `false` |
| `value.ConnectionId.displayName` | Human-readable label (e.g., `"uipath-atlassian-jira connection"`) |
| `metadata.UseConnectionService` | Always `"true"` |
| `metadata.Connector` | Connector key (e.g., `"uipath-atlassian-jira"`) -- must match the node's `model.context` connector key |
| `metadata.ActivityName` | Display name of the activity using this connection |
| `metadata.BindingsVersion` | Always `"2.2"` |
| `metadata.DisplayLabel` | Same as `value.ConnectionId.displayName` |

### How Connector Nodes Reference Bindings

Each connector node's `model.context` contains a `connection` entry with a placeholder:

```json
{ "name": "connection", "type": "string", "value": "<bindings.uipath-atlassian-jira connection>" }
```

At runtime, the engine resolves this placeholder by looking up `bindings_v2.json` for a `Connection` resource whose `metadata.Connector` matches `uipath-atlassian-jira`.

### Deduplication

Deduplicate by unique connector key. Add one `Connection` resource per unique connector. If two nodes use the same connector (e.g., two Jira activities), they share a single `Connection` resource.

### Single Connector Example (Jira)

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

### Multi-Connector Example (Jira + Slack)

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

### Other Resource Types in `bindings_v2.json`

Beyond `Connection`, `bindings_v2.json` can contain other resource types for trigger-based flows:

| Resource type | When used | Key fields |
|---------------|-----------|------------|
| `EventTrigger` | Connector trigger nodes (e.g., "Issue Created") | `metadata.Operation`, `metadata.ObjectName` |
| `Property` | Trigger filter parameters | `value.<param>.defaultValue`, `metadata.ParentResourceKey` |
| `Queue` | Queue trigger bindings | Queue name and folder |
| `TimeTrigger` | Scheduled triggers | Cron expression |

For manual-trigger flows with connector activities, you only need `Connection` resources.

> **Never hardcode connection IDs.** Always fetch them from IS at authoring time. Connection IDs are tenant-specific and change across environments.

---

## `workflow.bindings[]` -- Resource Nodes

Resource nodes (RPA workflow, agent, API workflow, agentic process) use an in-flow binding system stored in the top-level `workflow.bindings[]` array of the `.flow` file. Each resource node creates **2 entries**: one for `name` and one for `folderPath`.

### Binding Entry Format

```json
{
  "id": "<BINDING_ID>",
  "name": "<PROPERTY_NAME>",
  "type": "string",
  "resource": "process",
  "resourceKey": "<RESOURCE_KEY>",
  "default": "<DEFAULT_VALUE>",
  "propertyAttribute": "<PROPERTY_NAME>",
  "resourceSubType": "<RESOURCE_SUB_TYPE>"
}
```

| Field | Description |
|-------|-------------|
| `id` | `b` + 8 random alphanumeric characters (e.g., `bXk9mNpQr`) |
| `name` | `"name"` or `"folderPath"` |
| `type` | Always `"string"` |
| `resource` | Always `"process"` |
| `resourceKey` | The resource key from the node's `model.bindings.resourceKey` |
| `default` | The resource display name (for `name`) or folder path (for `folderPath`) |
| `propertyAttribute` | Same as `name` -- `"name"` or `"folderPath"` |
| `resourceSubType` | `"Process"`, `"Agent"`, `"ProcessOrchestration"`, or `"Api"` |

### Example: 2 Binding Entries for an RPA Workflow

```json
[
  {
    "id": "bA1b2C3d4",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "invoice-process-abc123",
    "default": "Invoice Processor",
    "propertyAttribute": "name",
    "resourceSubType": "Process"
  },
  {
    "id": "bE5f6G7h8",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "invoice-process-abc123",
    "default": "Finance/Automation",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Process"
  }
]
```

### Node `model.context` Connection Placeholder Format

The node instance's `model.context` references the binding IDs to resolve the resource name and folder at runtime:

```json
"context": [
  { "name": "name", "type": "string", "value": "=bindings.bA1b2C3d4", "default": "Invoice Processor" },
  { "name": "folderPath", "type": "string", "value": "=bindings.bE5f6G7h8", "default": "Finance/Automation" },
  { "name": "_label", "type": "string", "value": "Invoice Processor" }
]
```

> **Definition vs instance syntax:** Definition templates use `"<bindings.name>"` template syntax. Node instances use `"=bindings.<BINDING_ID>"` with the resolved binding ID.

### Deduplication

Deduplicate by the `resourceKey` + `propertyAttribute` pair. Do not add multiple entries with the same combination. If two nodes reference the same resource, they share the same binding entries.

---

## Summary: Which Binding System to Use

| Node Category | Binding System | Location | Entries Per Node |
|---------------|---------------|----------|------------------|
| Connector (`uipath.connector.*`) | `bindings_v2.json` | Project root file | 1 `Connection` resource per unique connector |
| Resource (RPA, agent, API, agentic) | `workflow.bindings[]` | Inside `.flow` file | 2 entries (`name` + `folderPath`) per resource node |
| OOTB (trigger, script, HTTP, logic) | None | N/A | 0 |

See [connector-guide.md](connectors/connector-guide.md) for the full connector configuration workflow. See [resource-node-guide.md](dynamic-nodes/resource-node-guide.md) for the resource node step-by-step.
