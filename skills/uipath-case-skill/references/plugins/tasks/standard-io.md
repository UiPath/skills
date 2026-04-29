# Standard-IO Tasks — Implementation

Covers `process`, `agent`, `rpa`, `api-workflow`, and `case-management` tasks. All five share the same binding structure and JSON skeleton — only the `type` field differs.

## Binding (declare at root)

All five types use `"resource": "process"`:

```json
{ "id": "b<8chars>", "name": "name",       "type": "string", "resource": "process", "propertyAttribute": "name",       "resourceKey": "<Folder>/<Project>.<Process>", "default": "<ProcessDisplayName>" },
{ "id": "b<8chars>", "name": "folderPath", "type": "string", "resource": "process", "propertyAttribute": "folderPath", "resourceKey": "<Folder>/<Project>.<Process>", "default": "<Folder>" }
```

See [variables/bindings](../variables/bindings.md) for dedup rules when multiple tasks share a resource.

## Task Skeleton

```json
{
  "id": "t<8chars>",
  "elementId": "<stageId>-t<8chars>",
  "displayName": "<Task Name>",
  "description": "<task description>",
  "type": "<process|agent|rpa|api-workflow|case-management>",
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

Set `type` to one of: `process`, `agent`, `rpa`, `api-workflow`, `case-management`.

## Error Output Uniqueness

Every standard-IO task gets an Error output. Apply the global variable uniqueness rule: first task gets `var: "error"`, second `error2`, third `error3`, etc. See [variables/global-vars](../variables/global-vars.md).

For inputs and outputs wiring beyond the default Error, see [variables/global-vars](../variables/global-vars.md).
