# Resource Bindings — Implementation

Root-level binding creation for `root.data.uipath.bindings[]`. Referenced by connector task plugins for ConnectionId + folderKey bindings.

## What Bindings Are

`root.data.uipath.bindings[]` stores resource metadata for tasks — process names, folder paths, connection IDs. Tasks reference these indirectly via `=bindings.<id>` instead of storing literal values.

```json
// root.data.uipath.bindings[]
{
  "id": "bG0SraLpg",
  "name": "name",
  "type": "string",
  "resource": "process",
  "resourceSubType": "ProcessOrchestration",
  "resourceKey": "Shared.MyProcess",
  "default": "MyProcess",
  "propertyAttribute": "name"
}
```

## Per Task Type

| Task Type | `resource` | `resourceSubType` | Bindings Created |
|---|---|---|---|
| process | `"process"` | `"ProcessOrchestration"` | name + folderPath |
| action | `"app"` | — | name + folderPath |
| agent | `"process"` | `"Agent"` | name + folderPath |
| rpa | `"process"` | — | name + folderPath |
| api-workflow | `"process"` | `"Api"` | name + folderPath |
| case-management | `"process"` | `"CaseManagement"` | name + folderPath |
| connector (event trigger) | `"Connection"` | — | ConnectionId + folderKey |

## Task References Bindings

```json
// task.data
{
  "name": "=bindings.bG0SraLpg",
  "folderPath": "=bindings.bH1iJK2lm"
}
```

## Deduplication

Multiple tasks referencing the same resource share one binding. Deduped by `default + resource + resourceKey`. The FE checks before creating a new binding.

## Binding ID Generation

IDs use `b` prefix + 8 alphanumeric chars (e.g., `bG0SraLpg`). Generated via `createBinding()` in `FPSFormControlUtils.ts`.

## Usage

1. Create binding entries in `root.data.uipath.bindings[]` before or during task creation
2. Reference from task data via `=bindings.<id>` (e.g., `data.context[].value` for connectors, `data.name` / `data.folderPath` for process tasks)
3. Apply deduplication check before creating new bindings
