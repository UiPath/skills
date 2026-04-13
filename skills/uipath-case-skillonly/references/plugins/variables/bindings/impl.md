# Bindings — Implementation

Bindings link tasks to their published resources (processes, agents, apps). Every standard-IO and action task requires two bindings: one for `name` and one for `folderPath`.

## Where Bindings Live

All bindings are declared in `root.data.uipath.bindings` — a flat array shared by all tasks. Tasks reference them via `=bindings.<id>`.

## Declaring a Binding Pair

For each process / agent / rpa / api-workflow / case-management task:

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "name",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "BookAppraisal"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "process",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/[CM] Insurance.BookAppraisal",
  "default": "Shared/[CM] Insurance"
}
```

For action tasks, use `"resource": "app"`:

```json
{
  "id": "b<8chars>",
  "name": "name",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "name",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "ApprovalApp"
},
{
  "id": "b<8chars>",
  "name": "folderPath",
  "type": "string",
  "resource": "app",
  "propertyAttribute": "folderPath",
  "resourceKey": "Shared/Claims.ApprovalApp",
  "default": "Shared/Claims"
}
```

## Referencing in Task Data

```json
"data": {
  "name": "=bindings.bCiT7IgAE",
  "folderPath": "=bindings.bbXi98qr7"
}
```

## Resource vs App

| Task type | `resource` value |
|---|---|
| `process`, `agent`, `rpa`, `api-workflow`, `case-management` | `"process"` |
| `action` | `"app"` |

## resourceKey Format

`"<FolderPath>/<ProjectName>.<ProcessName>"`

Use `uip case registry search "<keyword>"` to find the exact resourceKey from the tenant registry.

## One Binding Pair Per Task

Even if two tasks use the same process, declare separate binding pairs with unique IDs for each task.
