# Resource Node Guide

Resource nodes represent external Orchestrator resources (RPA workflows, agents, API workflows, agentic processes). They share a common structure — only the service type, category, icon, and resource-specific arguments differ.

---

## Resource Type Table

| ResourceType | serviceType | categoryId | icon | nodeType pattern |
|---|---|---|---|---|
| `Process` | `Orchestrator.StartJob` | `rpa-workflow` | `rpa` | `uipath.core.rpa-workflow.<KEY>` |
| `Agent` | `Orchestrator.StartAgentJob` | `agent` | `autonomous-agent` | `uipath.core.agent.<KEY>` |
| `ProcessOrchestration` | `Orchestrator.StartAgenticProcess` | `agentic-process` | `agentic-process` | `uipath.core.agentic-process.<KEY>` |
| `Api` | `Orchestrator.ExecuteApiWorkflowAsync` | `api-workflow` | `api` | `uipath.core.api-workflow.<KEY>` |

`<KEY>` is the Orchestrator Release Key GUID (lowercased, non-alphanumeric replaced with `-`). For personal workspace agents, `<KEY>` is a path string.

---

## Shared Handle Configuration

All resource nodes have identical ports:

```json
"handleConfiguration": [
  {
    "position": "left",
    "handles": [
      { "id": "input", "type": "target", "handleType": "input" }
    ]
  },
  {
    "position": "right",
    "handles": [
      { "id": "output", "type": "source", "handleType": "output" },
      {
        "id": "error",
        "label": "Error",
        "type": "source",
        "handleType": "output",
        "visible": "{inputs.errorHandlingEnabled}",
        "constraints": { "maxConnections": 1 }
      }
    ]
  }
]
```

---

## Shared Definition Template

The static skeleton for a resource node definition. Fill in `<PLACEHOLDERS>` from registry output:

```json
{
  "nodeType": "<NODE_TYPE>",
  "version": "1.0.0",
  "category": "<CATEGORY_ID>",
  "description": "",
  "tags": [],
  "sortOrder": 5,
  "supportsErrorHandling": true,
  "display": {
    "label": "<RESOURCE_NAME>",
    "icon": "<ICON>",
    "iconBackground": "<GRADIENT>",
    "iconBackgroundDark": "<GRADIENT_DARK>"
  },
  "handleConfiguration": "... (see Shared Handle Configuration)",
  "toolbarExtensions": {
    "design": {
      "actions": [{ "id": "open-workflow", "icon": "external-link", "label": "Open" }]
    }
  },
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "<SERVICE_TYPE>",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "<RESOURCE_SUB_TYPE>",
      "resourceKey": "<RESOURCE_KEY>",
      "orchestratorType": "<ORCHESTRATOR_TYPE>",
      "values": {
        "name": "<RESOURCE_NAME>",
        "folderPath": "<FOLDER_PATH>"
      }
    },
    "projectId": "<PROJECT_ID>",
    "context": [
      { "name": "name", "type": "string", "value": "<bindings.name>" },
      { "name": "folderPath", "type": "string", "value": "<bindings.folderPath>" },
      { "name": "_label", "type": "string", "value": "<RESOURCE_NAME>" }
    ]
  },
  "form": "<FROM_REGISTRY>",
  "inputDefinition": "<FROM_REGISTRY>",
  "inputDefaults": "<FROM_REGISTRY>",
  "outputDefinition": "<FROM_REGISTRY + standard error output>",
  "debug": { "runtime": "bpmnEngine" }
}
```

---

## Shared Node Instance Template

```json
{
  "id": "<NODE_ID>",
  "type": "<NODE_TYPE>",
  "typeVersion": "1.0.0",
  "ui": {
    "position": { "x": 0, "y": 0 },
    "size": { "width": 96, "height": 96 }
  },
  "display": {
    "label": "<RESOURCE_NAME>",
    "icon": "<ICON>",
    "iconBackground": "<GRADIENT>",
    "iconBackgroundDark": "<GRADIENT_DARK>"
  },
  "inputs": "<FROM_REGISTRY -- keyed by argument name>",
  "outputs": "<FROM_REGISTRY -- output variable mappings>",
  "model": {
    "type": "bpmn:ServiceTask",
    "serviceType": "<SERVICE_TYPE>",
    "version": "v2",
    "section": "In this solution",
    "bindings": {
      "resource": "process",
      "resourceSubType": "<RESOURCE_SUB_TYPE>",
      "resourceKey": "<RESOURCE_KEY>",
      "orchestratorType": "<ORCHESTRATOR_TYPE>",
      "values": {
        "name": "<RESOURCE_NAME>",
        "folderPath": "<FOLDER_PATH>"
      }
    },
    "projectId": "<PROJECT_ID>",
    "context": [
      { "name": "name", "type": "string", "value": "=bindings.<BINDING_ID_NAME>", "default": "<RESOURCE_NAME>" },
      { "name": "folderPath", "type": "string", "value": "=bindings.<BINDING_ID_FOLDER>", "default": "<FOLDER_PATH>" },
      { "name": "_label", "type": "string", "value": "<RESOURCE_NAME>" }
    ]
  }
}
```

> Definition uses `"<bindings.name>"` template syntax. Instance uses `"=bindings.bXXXXX"` resolved binding IDs.

---

## Bindings Pattern

Each resource node creates 2 entries in the top-level `bindings[]` array:

```json
[
  {
    "id": "<BINDING_ID_1>",
    "name": "name",
    "type": "string",
    "resource": "process",
    "resourceKey": "<RESOURCE_KEY>",
    "default": "<RESOURCE_NAME>",
    "propertyAttribute": "name",
    "resourceSubType": "<RESOURCE_SUB_TYPE>"
  },
  {
    "id": "<BINDING_ID_2>",
    "name": "folderPath",
    "type": "string",
    "resource": "process",
    "resourceKey": "<RESOURCE_KEY>",
    "default": "<FOLDER_PATH>",
    "propertyAttribute": "folderPath",
    "resourceSubType": "<RESOURCE_SUB_TYPE>"
  }
]
```

Binding IDs use the standard format: `b` + 8 random alphanumeric characters.

---

## Registry Interaction

> Resource nodes require the `uip` CLI and active authentication (`uip login`) to discover and fetch resource schemas.

```bash
# 1. Refresh the local registry cache
uip flow registry pull --force

# 2. Search for a resource by name
uip flow registry search "<RESOURCE_NAME>" --output json

# 3. Get the full node definition (copy into definitions[])
uip flow registry get "<NODE_TYPE>" --output json
```

The `registry get` response contains the complete definition object. Copy it verbatim into `workflow.definitions`.

---

## Step-by-Step -- Add a Resource Node

1. Run `uip flow registry pull --force` to refresh the cache.
2. Run `uip flow registry search "<NAME>" --output json` to find the resource.
3. Note the `nodeType` from the search results (e.g., `uipath.core.agent.93f09b44-...`).
4. Run `uip flow registry get "<NODE_TYPE>" --output json` to get the full definition.
5. Copy the definition into `workflow.definitions` (deduplicate by nodeType:version).
6. Generate a unique node ID per the ID algorithm in [project-scaffolding-guide.md](../project-scaffolding-guide.md).
7. Create the node instance using the instance template (see Shared Node Instance Template), filling in:
   - `type` from the registry
   - `inputs` from the registry's `inputDefinition` (use default values or expressions)
   - `model` fields from the registry's model
8. Generate 2 binding entries (see Bindings Pattern) and add to `workflow.bindings`.
9. Update `model.context` on the instance to reference the binding IDs with `=bindings.<ID>`.
10. Add edges connecting the node (ports: `input` target, `output` source).
11. Regenerate `workflow.variables.nodes` -- add entries for each output in the registry's `outputDefinition`.
12. Run the validation checklist from [validation-checklist.md](../validation-checklist.md).

---

## Placeholder Pattern

When the resource is not published yet, use `core.logic.mock` as a stand-in:

1. Add a `core.logic.mock` node with `display.description` noting what it replaces.
2. Wire it with the same topology the real node would use.
3. After the resource is published: run `registry pull`, `registry get`, then replace the mock with the real node following Steps 4-12 above.

---

## Standard Error Output

All resource node definitions include this error output (constant across all types):

```json
"error": {
  "type": "object",
  "description": "Error information if the node fails",
  "source": "=Error",
  "var": "error",
  "schema": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["code", "message", "detail", "category", "status"],
    "properties": {
      "code": { "type": "string", "description": "Error code as a string" },
      "message": { "type": "string", "description": "High-level error message" },
      "detail": { "type": "string", "description": "Detailed error description" },
      "category": { "type": "string", "description": "Error category" },
      "status": { "type": "integer", "description": "HTTP status code" }
    },
    "additionalProperties": false
  }
}
```

---

## Type-Specific Guides

For type-specific details (icon gradients, complete examples, input/output patterns):

| Resource Type | Guide |
|---|---|
| RPA Workflow | [rpa-workflow-guide.md](rpa-workflow-guide.md) |
| Agent | [agent-guide.md](agent-guide.md) |
| API Workflow | [api-workflow-guide.md](api-workflow-guide.md) |
| Agentic Process | [agentic-process-guide.md](agentic-process-guide.md) |
