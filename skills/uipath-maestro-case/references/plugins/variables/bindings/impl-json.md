# Resource Bindings — Implementation

Top-level binding creation. Referenced by **all** task plugins — non-connector tasks for name + folderPath bindings, connector tasks for ConnectionId + folderKey bindings. Every task type MUST create bindings; see each task plugin's §Root-level bindings section.

## Schema-dependent destination

Read `Schema:` header from `tasks.md` per Rule 18.

| Schema | Bindings array path |
|---|---|
| **v19** | `root.data.uipath.bindings[]` |
| **v20** | `bindings[]` *(top level — no `root` wrapper, no `data.uipath`)* |

Field shape inside the array is **identical** across schemas. Only the destination path differs.

## What Bindings Are

The bindings array stores resource metadata for tasks — process names, folder paths, connection IDs. Tasks reference these indirectly via `=bindings.<id>` instead of storing literal values.

## Per Task Type

| Task Type | `resource` | `resourceSubType` | Bindings Created |
|---|---|---|---|
| process | `"process"` | `"ProcessOrchestration"` | name + folderPath |
| action | `"app"` | — | name + folderPath |
| agent | `"process"` | `"Agent"` | name + folderPath |
| rpa | `"process"` | — | name + folderPath |
| api-workflow | `"process"` | `"Api"` | name + folderPath |
| case-management | `"process"` | `"CaseManagement"` | name + folderPath |
| connector (activity/trigger) | `"Connection"` | — | ConnectionId + folderKey |

## Binding Creation

For every task, create **two** binding entries in the bindings array (path per § Schema-dependent destination above). Both bindings share the same `resourceKey`. The shape is identical for all task types — only the field values differ per the Per Task Type table above.

**Every binding entry MUST include all 7 fields:** `id`, `name`, `type`, `resource`, `resourceKey`, `default`, `propertyAttribute` (plus optional `resourceSubType`). Omitting `name` or `type` causes Studio Web to fail to render the case.

### Full binding shape (two entries per task)

```json
[
  {
    "id": "<b + 8 alphanumeric chars>",
    "name": "name",
    "type": "string",
    "resource": "<see Per Task Type table>",
    "resourceSubType": "<see Per Task Type table, omit key if none>",
    "resourceKey": "<folderPath>.<name>",
    "default": "<name>",
    "propertyAttribute": "name"
  },
  {
    "id": "<b + 8 alphanumeric chars>",
    "name": "folderPath",
    "type": "string",
    "resource": "<same as above>",
    "resourceSubType": "<same as above>",
    "resourceKey": "<folderPath>.<name>",
    "default": "<folderPath>",
    "propertyAttribute": "folderPath"
  }
]
```

> The `name` field mirrors `propertyAttribute` — for non-connector tasks the values are `"name"` and `"folderPath"`, for connector tasks `"ConnectionId"` and `"folderKey"`.

### Data sources — non-connector tasks

| Field | Source |
|---|---|
| `name` | `tasks.md` `name` field (captured from registry during planning: `entry.name` for process types, `entry.deploymentTitle` for action) |
| `folderPath` | `tasks.md` `folder-path` field (captured from registry during planning: `entry.folders[0].fullyQualifiedName` for process types, `entry.deploymentFolder.fullyQualifiedName` for action) |

### resourceKey construction — non-connector tasks

```
resourceKey = "<folderPath>.<name>"
```

Examples:
- folderPath `"Shared"`, name `"KYC"` → `"Shared.KYC"`
- folderPath `"Shared/Finance"`, name `"InvoiceProcess"` → `"Shared/Finance.InvoiceProcess"`
- folderPath `""` (empty), name `"ReviewHITL"` → `".ReviewHITL"`

### Data sources — connector tasks

| Field | Source |
|---|---|
| `name` / `propertyAttribute` | First binding: `"ConnectionId"`. Second binding: `"folderKey"`. |
| `default` (ConnectionId) | `connection-id` from `tasks.md` |
| `default` (folderKey) | `folderKey` from `get-connection` (Step 1) |
| `resourceKey` | `connection-id` from `tasks.md` |

### Task references

Non-connector: set `data.name` to `=bindings.<nameBindingId>` and `data.folderPath` to `=bindings.<folderPathBindingId>`.
Connector: set `data.context[].connection` to `=bindings.<connBindingId>` and `data.context[].folderKey` to `=bindings.<folderBindingId>`.
Do NOT use literal strings.

## Deduplication

Multiple tasks referencing the same resource share one binding pair. Deduped by `default + resource + resourceKey`. Before creating a new binding, check if an existing entry in the bindings array (v19: `root.data.uipath.bindings[]`; v20: top-level `bindings[]`) matches on all three fields. If found, reuse the existing binding's `id` instead of creating a new one.

## Binding ID Generation

IDs use `b` prefix + 8 alphanumeric chars (e.g., `bG0SraLpg`).

## bindings_v2.json Sync

`bindings_v2.json` must mirror the bindings array in SDK format (source path: `root.data.uipath.bindings[]` in v19, top-level `bindings[]` in v20). Regenerated in batch (not per-task) at end of Step 9 and Step 9.7. See [bindings-v2-sync.md](../../../bindings-v2-sync.md).
