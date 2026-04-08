# API Workflow Nodes

API workflow nodes invoke lightweight HTTP-triggered workflows via Orchestrator. They share the common resource node structure from [resource-node-guide.md](resource-node-guide.md) with API-specific type parameters.

## Type Parameters

| Field | Value |
|---|---|
| `model.serviceType` | `Orchestrator.ExecuteApiWorkflowAsync` |
| `model.bindings.resourceSubType` | `Api` |
| `model.bindings.orchestratorType` | `api` |
| `category` | `api-workflow` |
| `display.icon` | `api` |
| `display.iconBackground` | `linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)` |
| `display.iconBackgroundDark` | `linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)` |
| Node type pattern | `uipath.core.api-workflow.<KEY>` |


## Constructed Example

A hypothetical "ProcessInvoice" API workflow with two inputs and two outputs.

### Node Instance

```json
{
  "id": "n_api_invoice_01",
  "type": "uipath.core.api-workflow.a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 480, "y": 200 },
    "size": { "width": 96, "height": 96 }
  },
  "display": {
    "label": "ProcessInvoice",
    "icon": "api",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "inputs": {
    "in_InvoiceId": "=\"INV-2024-001\"",
    "in_Amount": "=1250.00"
  },
  "outputs": {
    "out_Status": { "var": "out_Status" },
    "out_ProcessedAt": { "var": "out_ProcessedAt" }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.ExecuteApiWorkflowAsync",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Api",
      "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "orchestratorType": "api",
      "values": {
        "name": "ProcessInvoice",
        "folderPath": "Finance"
      }
    },
    "projectId": "proj-invoice-api",
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.b1a2b3c4", "default": "ProcessInvoice" },
      { "name": "folderPath", "type": "string", "value": "=bindings.b5e6f7g8", "default": "Finance" },
      { "name": "_label", "type": "string", "value": "ProcessInvoice" }
    ]
  }
}
```

### Node Definition

```json
{
  "nodeType": "uipath.core.api-workflow.a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "version": "1.0.0",
  "category": "api-workflow",
  "description": "",
  "tags": [],
  "sortOrder": 5,
  "supportsErrorHandling": true,
  "display": {
    "label": "ProcessInvoice",
    "icon": "api",
    "iconBackground": "linear-gradient(225deg, #FAFAFB 0%, #ECEDEF 100%)",
    "iconBackgroundDark": "linear-gradient(225deg, #526069 0%, rgba(50, 60, 66, 0.6) 100%)"
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "Orchestrator.ExecuteApiWorkflowAsync",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "Api",
      "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "orchestratorType": "api",
      "values": {
        "name": "ProcessInvoice",
        "folderPath": "Finance"
      }
    },
    "projectId": "proj-invoice-api",
    "context": [
      { "name": "name", "type": "string", "value": "<bindings.name>" },
      { "name": "folderPath", "type": "string", "value": "<bindings.folderPath>" },
      { "name": "_label", "type": "string", "value": "ProcessInvoice" }
    ]
  }
}
```

### Binding Entries

```json
[
  {
    "id": "b1a2b3c4",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "default": "ProcessInvoice",
    "propertyAttribute": "name",
    "resourceSubType": "Api"
  },
  {
    "id": "b5e6f7g8",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "default": "Finance",
    "propertyAttribute": "folderPath",
    "resourceSubType": "Api"
  }
]
```


## Key Differences from RPA Workflows

- Uses async execution (`Orchestrator.ExecuteApiWorkflowAsync`) -- the flow waits for the API workflow to complete before proceeding to the next node.
- Designed for lightweight HTTP-triggered workflows rather than attended/unattended robot jobs. RPA workflows use `Orchestrator.StartJob`.
- Same `model.bindings.resource` value (`"process"`) despite being an API workflow -- all resource types share this value.


## Common Mistakes

- **Wrong serviceType.** Using `Orchestrator.StartJob` (RPA) instead of `Orchestrator.ExecuteApiWorkflowAsync`. The flow will attempt to start a robot job instead of invoking the API endpoint.
- **Missing registry data.** API workflows still require `inputDefinition` and `outputDefinition` from the registry (`uip flow registry get`). Do not hand-author these -- fetch them from the registry and copy verbatim.
- **Wrong resourceSubType.** Using `Process` instead of `Api`. This causes Orchestrator to treat the invocation as an RPA process.
