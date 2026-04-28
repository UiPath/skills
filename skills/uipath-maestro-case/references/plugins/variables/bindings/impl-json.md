# Resource Bindings — Implementation

Root-level binding creation for `root.data.uipath.bindings[]`. Referenced by **all** task plugins — non-connector tasks for name + folderPath bindings, connector tasks for ConnectionId + folderKey bindings. Every task type MUST create root bindings; see each task plugin's §Root-level bindings section.

## What Bindings Are

`root.data.uipath.bindings[]` stores resource metadata for tasks — process names, folder paths, connection IDs. Tasks reference these indirectly via `=bindings.<id>` instead of storing literal values.

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

## Non-Connector Binding Creation (name + folderPath)

For every non-connector task (process, action, agent, rpa, api-workflow, case-management), create **two** binding entries in `root.data.uipath.bindings[]`. Both bindings share the same `resourceKey`.

### Data sources

| Field | Source |
|---|---|
| `name` | `tasks.md` `name` field (captured from registry during planning: `entry.name` for process types, `entry.deploymentTitle` for action) |
| `folderPath` | `tasks.md` `folder-path` field (captured from registry during planning: `entry.folders[0].fullyQualifiedName` for process types, `entry.deploymentFolder.fullyQualifiedName` for action) |

### resourceKey construction

```
resourceKey = "<folderPath>.<name>"
```

Examples:
- folderPath `"Shared"`, name `"KYC"` → `"Shared.KYC"`
- folderPath `"Shared/Finance"`, name `"InvoiceProcess"` → `"Shared/Finance.InvoiceProcess"`
- folderPath `""` (empty), name `"ReviewHITL"` → `".ReviewHITL"`

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

### Task references

After creating bindings, set `data.name` to `=bindings.<nameBindingId>` and `data.folderPath` to `=bindings.<folderPathBindingId>`. Do NOT use literal strings.

## Deduplication

Multiple tasks referencing the same resource share one binding pair. Deduped by `default + resource + resourceKey`. Before creating a new binding, check if an existing entry in `root.data.uipath.bindings[]` matches on all three fields. If found, reuse the existing binding's `id` instead of creating a new one.

## Binding ID Generation

IDs use `b` prefix + 8 alphanumeric chars (e.g., `bG0SraLpg`).

## bindings_v2.json Sync

`bindings_v2.json` must mirror `root.data.uipath.bindings[]` in SDK format. Regenerated in batch (not per-task) at end of Step 9 and Step 9.7. See [bindings-v2-sync.md](../../../bindings-v2-sync.md).
