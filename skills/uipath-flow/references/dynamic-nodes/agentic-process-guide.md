# Agentic Process Nodes

Agentic process nodes invoke process orchestrations via Orchestrator. They use the `Orchestrator.StartAgenticProcess` service type and are designed for published orchestration processes. They are tenant-specific resources that appear in the registry after `uip login` + `uip flow registry pull`.

For shared structure (handle configuration, definition/instance templates, bindings pattern), see [resource-node-guide.md](resource-node-guide.md).

## When to Use

| Situation | Use Agentic Process? |
|---|---|
| Invoke a published orchestration process | Yes |
| Invoke a published AI agent | No -- use an agent node |
| Call another published flow | No -- use a flow subflow node |
| Need desktop/browser automation | No -- use an RPA workflow node |
| Resource not yet published | No -- use `core.logic.mock` placeholder |

## Type Parameters

| Field | Value |
|---|---|
| `model.serviceType` | `Orchestrator.StartAgenticProcess` |
| `model.bindings.resourceSubType` | `ProcessOrchestration` |
| `model.bindings.orchestratorType` | `agentic-process` |
| `category` | `agentic-process` |
| `display.icon` | `agentic-process` |
| `display.iconBackground` | `linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)` |
| `display.iconBackgroundDark` | `linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)` |
| Node type pattern | `uipath.core.agentic-process.<KEY>` |

## Discovery

```bash
uip flow registry pull --force
uip flow registry search "uipath.core.agentic-process" --output json
```

Requires `uip login`. Only published agentic processes from your tenant appear.

## Registry Validation

```bash
uip flow registry get "uipath.core.agentic-process.<KEY>" --output json
```

Confirm:

- Input port: `input`
- Output port: `output`
- `model.serviceType` -- `Orchestrator.StartAgenticProcess`
- `model.bindings.resourceSubType` -- `ProcessOrchestration`
- `inputDefinition` -- typically empty
- `outputDefinition.error` -- error schema

## Complete Example -- CustomerOnboarding

A hypothetical "CustomerOnboarding" agentic process with two inputs and two outputs.

### Node Instance

```json
{
  "id": "n_agentic_onboard_01",
  "type": "uipath.core.agentic-process.f1e2d3c4-b5a6-7890-fedc-ba9876543210",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 480, "y": 200 },
    "size": { "width": 96, "height": 96 }
  },
  "display": {
    "label": "CustomerOnboarding",
    "icon": "agentic-process",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "inputs": {
    "in_CustomerName": "=\"Acme Corp\"",
    "in_AccountType": "=\"Enterprise\""
  },
  "outputs": {
    "out_OnboardingId": { "var": "out_OnboardingId" },
    "out_Status": { "var": "out_Status" }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgenticProcess",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "ProcessOrchestration",
      "resourceKey": "f1e2d3c4-b5a6-7890-fedc-ba9876543210",
      "orchestratorType": "agentic-process",
      "values": {
        "name": "CustomerOnboarding",
        "folderPath": "Operations"
      }
    },
    "projectId": "proj-customer-onboard",
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.ba1b2c3d", "default": "CustomerOnboarding" },
      { "name": "folderPath", "type": "string", "value": "=bindings.be4f5g6h", "default": "Operations" },
      { "name": "_label", "type": "string", "value": "CustomerOnboarding" }
    ]
  }
}
```

### Node Definition

```json
{
  "nodeType": "uipath.core.agentic-process.f1e2d3c4-b5a6-7890-fedc-ba9876543210",
  "version": "1.0.0",
  "category": "agentic-process",
  "description": "",
  "tags": [],
  "sortOrder": 5,
  "supportsErrorHandling": true,
  "display": {
    "label": "CustomerOnboarding",
    "icon": "agentic-process",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.StartAgenticProcess",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "ProcessOrchestration",
      "resourceKey": "f1e2d3c4-b5a6-7890-fedc-ba9876543210",
      "orchestratorType": "agentic-process",
      "values": {
        "name": "CustomerOnboarding",
        "folderPath": "Operations"
      }
    },
    "projectId": "proj-customer-onboard",
    "context": [
      { "name": "name", "type": "string", "value": "<bindings.name>" },
      { "name": "folderPath", "type": "string", "value": "<bindings.folderPath>" },
      { "name": "_label", "type": "string", "value": "CustomerOnboarding" }
    ]
  }
}
```

### Binding Entries

```json
[
  {
    "id": "ba1b2c3d",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "f1e2d3c4-b5a6-7890-fedc-ba9876543210",
    "default": "CustomerOnboarding",
    "propertyAttribute": "name",
    "resourceSubType": "ProcessOrchestration"
  },
  {
    "id": "be4f5g6h",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "f1e2d3c4-b5a6-7890-fedc-ba9876543210",
    "default": "Operations",
    "propertyAttribute": "folderPath",
    "resourceSubType": "ProcessOrchestration"
  }
]
```

## Note on Flow Type

The `Flow` resource type also uses `Orchestrator.StartAgenticProcess` as its service type, but with different category and icon values. Flow resources represent other `.flow` projects invoked as sub-orchestrations.

| Field | Agentic Process | Flow |
|---|---|---|
| `resourceSubType` | `ProcessOrchestration` | `Flow` |
| `orchestratorType` | `agentic-process` | `flow` |
| `category` | `agentic-process` | `flow` |
| `icon` | `agentic-process` | `flow-project` |
| `serviceType` | `Orchestrator.StartAgenticProcess` | `Orchestrator.StartAgenticProcess` |

When constructing nodes, the `serviceType` alone is not sufficient to distinguish these two types. Always check `resourceSubType` and `category` to determine which resource type you are working with.

## Output Variables

- `$vars.<NODE_ID>.error` -- error details if execution fails (`code`, `message`, `detail`, `category`, `status`)

## Adding via CLI

```bash
uip flow node add <PROJECT_NAME>.flow "uipath.core.agentic-process.<KEY>" --output json \
  --label "<PROCESS_NAME>" \
  --position <X>,<Y>
```

## Common Mistakes

1. **Confusing with RPA process.** Agentic processes use `Orchestrator.StartAgenticProcess`, not `Orchestrator.StartJob`. They also use `ProcessOrchestration` for `resourceSubType`, not `Process`.

2. **Wrong resourceSubType.** Using `Process` instead of `ProcessOrchestration`. This causes Orchestrator to treat the invocation as a standard RPA job rather than a process orchestration.

3. **Confusing with Flow type.** Both agentic processes and flows share the same `serviceType` (`Orchestrator.StartAgenticProcess`). Differentiate by `resourceSubType` (`ProcessOrchestration` vs `Flow`), `category` (`agentic-process` vs `flow`), and `icon` (`agentic-process` vs `flow-project`).

## Debug

| Error | Cause | Fix |
|---|---|---|
| Node type not found in registry | Process not published or registry stale | Run `uip login` then `uip flow registry pull --force` |
| Process execution failed | Underlying orchestration errored | Check `$vars.<NODE_ID>.error` for details |
