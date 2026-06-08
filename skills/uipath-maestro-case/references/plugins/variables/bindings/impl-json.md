# Resource Bindings — Implementation

Top-level binding creation. Referenced by **all** task plugins — non-connector tasks for name + folderPath bindings, connector tasks for ConnectionId + folderKey bindings. Every task type MUST create bindings; see each task plugin's §Root-level bindings section.

> **No `planning.md`** — bindings are created during implementation (driven by each task plugin's §Root-level bindings), not planned as standalone T-entries. Intentional, not a gap.

## Destination

Bindings live at top-level `bindings[]` in `caseplan.json` (no `root` wrapper, no `data.uipath`).

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

For every task, create **two** binding entries in top-level `bindings[]`. Both bindings share the same `resourceKey`. The shape is identical for all task types — only the field values differ per the Per Task Type table above.

**Every binding entry MUST include all 7 fields:** `id`, `name`, `type`, `resource`, `resourceKey`, `default`, `propertyAttribute` (plus optional `resourceSubType`). Omitting `name` or `type` causes Studio Web to fail to render the case.

### Full binding shape — non-connector tasks

For non-connector tasks (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`), `name` and `propertyAttribute` carry the same value (`"name"` / `"folderPath"`):

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

### Full binding shape — connector tasks (activity / trigger)

> **`name` and `propertyAttribute` deliberately differ** for connector bindings — the CLI's `binding-builder.ts` (in `uipcli-case-validate/packages/case-tool/src/utils/`) is the source of truth. Authoring with mirror-cased values may render in Studio Web but diverges from canonical CLI output.

ConnectionBinding `name` is **templated** with the connector key (`` `${connectorKey} connection` ``); FolderKey binding `name` is `"FolderKey"` (PascalCase) while its `propertyAttribute` is `"folderKey"` (camelCase). Both bindings share the same `resourceKey` (the connection UUID):

```json
[
  {
    "id": "<b + 8 alphanumeric chars>",
    "name": "<connectorKey> connection",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<connection-id>",
    "default": "<connection-id>",
    "propertyAttribute": "ConnectionId"
  },
  {
    "id": "<b + 8 alphanumeric chars>",
    "name": "FolderKey",
    "type": "string",
    "resource": "Connection",
    "resourceKey": "<connection-id>",
    "default": "<folderKey>",
    "propertyAttribute": "folderKey"
  }
]
```

Concrete example for Microsoft Outlook 365: `name: "uipath-microsoft-outlook365 connection"` on the ConnectionBinding.

The FolderKey binding is **omitted entirely** when `spec.connection.folderKey` is `null` (see `binding-builder.ts:73-83`).

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

| Binding | `name` | `propertyAttribute` | `default` | `resourceKey` |
|---|---|---|---|---|
| ConnectionBinding | `` `${connectorKey} connection` `` (templated, e.g. `"uipath-microsoft-outlook365 connection"`) | `"ConnectionId"` | `connection-id` from `tasks.md` | `connection-id` from `tasks.md` |
| FolderKey binding (omit when `spec.connection.folderKey === null`) | `"FolderKey"` (PascalCase) | `"folderKey"` (camelCase — different from `name`) | `folderKey` from `get-connection` (Step 1) | `connection-id` from `tasks.md` (same as ConnectionBinding) |

### Task references

Non-connector: set `data.name` to `=bindings.<nameBindingId>` and `data.folderPath` to `=bindings.<folderPathBindingId>`.
Connector: set `data.context[].connection` to `=bindings.<connBindingId>` and `data.context[].folderKey` to `=bindings.<folderBindingId>`.
Do NOT use literal strings.

## Deduplication

Multiple tasks referencing the same resource share one binding pair. Deduped by `default + resource + resourceKey`. Before creating a new binding, check if an existing entry in top-level `bindings[]` matches on all three fields. If found, reuse the existing binding's `id` instead of creating a new one.

## Binding ID Generation

IDs use `b` prefix + 8 alphanumeric chars (e.g., `bG0SraLpg`).

## bindings_v2.json Sync

`bindings_v2.json` must mirror top-level `bindings[]` in SDK format. Regenerated in batch (not per-task) at end of Step 9 and Step 9.7. See [bindings-v2-sync.md](../../../bindings-v2-sync.md).
