# Case Management Task — Implementation

Same structure as [process](../process/impl.md) — only `type` differs.

## Binding (declare at root)

```json
{ "id": "b<8chars>", "name": "name",       "type": "string", "resource": "process", "propertyAttribute": "name",       "resourceKey": "Shared/Claims.SubCaseProcess", "default": "SubCaseProcess" },
{ "id": "b<8chars>", "name": "folderPath", "type": "string", "resource": "process", "propertyAttribute": "folderPath", "resourceKey": "Shared/Claims.SubCaseProcess", "default": "Shared/Claims" }
```

## Task

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "Run Sub-Case",
  "description": "Spawns and waits for a nested case management process.",
  "type": "case-management",
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
