# API Workflow Task — Implementation

Same structure as [process](../process/impl.md) — only `type` differs.

## Binding (declare at root)

```json
{ "id": "b<8chars>", "name": "name",       "type": "string", "resource": "process", "propertyAttribute": "name",       "resourceKey": "Shared/ExpenseReport.APIWorkflow", "default": "API Workflow" },
{ "id": "b<8chars>", "name": "folderPath", "type": "string", "resource": "process", "propertyAttribute": "folderPath", "resourceKey": "Shared/ExpenseReport.APIWorkflow", "default": "Shared/ExpenseReport" }
```

## Task

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "API Workflow",
  "description": "Executes the API workflow for backend processing.",
  "type": "api-workflow",
  "isRequired": true,
  "shouldRunOnlyOnce": true,
  "data": {
    "name": "=bindings.<nameId>",
    "folderPath": "=bindings.<folderPathId>",
    "inputs": [],
    "outputs": [
      {
        "name": "Error", "displayName": "Error", "value": "error", "type": "jsonSchema",
        "source": "=Error", "var": "error", "id": "error", "target": "=error",
        "elementId": "<stageId>-<taskId>",
        "body": { "type": "object", "properties": { "code": { "type": "string" }, "message": { "type": "string" }, "detail": { "type": "string" }, "category": { "type": "string" }, "status": { "type": "number" }, "element": { "type": "string" } } },
        "_jsonSchema": { "type": "object", "properties": { "code": { "type": "string" }, "message": { "type": "string" }, "detail": { "type": "string" }, "category": { "type": "string" }, "status": { "type": "number" }, "element": { "type": "string" } } }
      }
    ]
  },
  "entryConditions": [
    { "id": "Condition_<6chars>", "displayName": "Stage entered", "rules": [[{ "rule": "current-stage-entered", "id": "Rule_<6chars>" }]] }
  ]
}
```
