# Resource Bindings — Implementation (PLACEHOLDER)

> **Status**: Placeholder — not referenced by SKILL.md or planning/implementation docs.
> Currently the skill relies on CLI commands (`tasks add --task-type-id`) to auto-create bindings.
> This file documents the JSON-level binding structure for future direct-write support.

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

## TODO — Direct Write Migration

When moving from CLI to direct JSON editing:
1. Create binding entries in `root.data.uipath.bindings[]` before task creation
2. Set `task.data.name = "=bindings.<id>"` and `task.data.folderPath = "=bindings.<id>"`
3. Apply deduplication check before creating new bindings
