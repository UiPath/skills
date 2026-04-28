# bindings_v2.json Sync

Shared procedure for keeping `bindings_v2.json` in sync after any plugin writes to `root.data.uipath.bindings[]` in `caseplan.json`.

## When to Run

After any plugin creates or modifies entries in `root.data.uipath.bindings[]`. Applies to ALL task types that create root bindings:

**Non-connector tasks** (create name + folderPath bindings):
- process ([impl-json.md](plugins/tasks/process/impl-json.md) § Root-level bindings)
- action ([impl-json.md](plugins/tasks/action/impl-json.md) § Root-level bindings)
- agent ([impl-json.md](plugins/tasks/agent/impl-json.md) § Root-level bindings)
- rpa ([impl-json.md](plugins/tasks/rpa/impl-json.md) § Root-level bindings)
- api-workflow ([impl-json.md](plugins/tasks/api-workflow/impl-json.md) § Root-level bindings)
- case-management ([impl-json.md](plugins/tasks/case-management/impl-json.md) § Root-level bindings)

**Connector tasks** (create ConnectionId + folderKey bindings):
- connector-activity ([impl-json.md](plugins/tasks/connector-activity/impl-json.md) § 3a)
- connector-trigger / event trigger (via [connector-trigger-common.md](connector-trigger-common.md) § Root-level bindings)

---

## § Regenerate bindings_v2.json

After writing bindings to `root.data.uipath.bindings[]`, regenerate `bindings_v2.json`. This file uses a **different format**: `caseplan.json` stores two entries per resource (one per property), `bindings_v2.json` stores one entry per resource with properties nested under `value`.

### Procedure

1. Read `root.data.uipath.bindings[]` from `caseplan.json`
2. Group bindings by `resourceKey` — entries sharing the same key belong to one resource
3. For each group, produce one resource entry using the shapes below
4. Write the full file (always overwrite, never append) to `<SolutionDir>/<ProjectName>/bindings_v2.json`

### Non-connector resource entry

```json
{
  "resource": "<resource>",
  "key": "<resourceKey>",
  "value": {
    "name": { "defaultValue": "<name binding default>" },
    "folderPath": { "defaultValue": "<folderPath binding default>" }
  },
  "metadata": { "subType": "<resourceSubType — omit metadata key if none>" }
}
```

### Connector resource entry

```json
{
  "resource": "Connection",
  "key": "<connectionId>",
  "value": {
    "connectionId": { "defaultValue": "<connectionId>" },
    "folderKey": { "defaultValue": "<folderKey>" }
  },
  "metadata": { "connector": "<connectorKey>" }
}
```

> **Known CLI bug:** `syncConnectionResources` reads `value.connectionId` (lowercase c) but `flow-schema` writes `value.ConnectionId` (uppercase C). Use **lowercase `connectionId`** until fixed.

File envelope: `{ "version": "2.0", "resources": [ /* one entry per resource */ ] }`

---

## § Populate IS connection cache

`uip solution resource refresh` reads a local IS cache that connector plugins must populate after `get-connection`.

**Path:** `~/.uipath/cache/integrationservice/<connectorKey>/connections.json`

**Shape — bare JSON array:**

```json
[
    {
        "id": "<connectionId>",
        "name": "<connectionName>",
        "connectorKey": "<connectorKey>",
        "connectorName": "<connectorName>",
        "folderKey": "<folderKey>",
        "folderName": "<folderName>"
    }
]
```

### Field sources

| Field | Source | Plugin step |
|---|---|---|
| `id` | `connection-id` from `tasks.md` | Planning |
| `name` | `.Data.Connections[selected].name` from `get-connection` | Step 1 |
| `connectorKey` | `connector-key` from `tasks.md` | Planning |
| `connectorName` | `.Data.Connections[selected].connector.name` from `get-connection` | Step 1 |
| `folderKey` | `.Data.Connections[selected].folder.key` from `get-connection` | Step 1 |
| `folderName` | `.Data.Connections[selected].folder.name` from `get-connection` | Step 1 |

### Procedure

After `get-connection` succeeds (Step 1), write or merge the cache:

1. Read existing cache at the path above (may not exist — start with `[]`)
2. If an entry with the same `id` already exists, skip
3. Otherwise append the new entry
4. Write the file as a bare JSON array (NOT wrapped in `{ cachedAt, data }`)

```bash
mkdir -p ~/.uipath/cache/integrationservice/<connectorKey>
```

> Workaround for CLI bugs: (1) tenant-ID prefix in cache path, (2) wrapped `{ cachedAt, data }` format. Direct write bypasses both.

---

## What `resource refresh` produces

With `bindings_v2.json` and IS cache in place, `uip solution resource refresh` creates:

| Input | Output | Purpose |
|---|---|---|
| Non-connector bindings in `bindings_v2.json` | `resources/solution_folder/process/` files | Resource declarations imported from Orchestrator |
| Connection binding in `bindings_v2.json` + IS cache | `resources/solution_folder/connection/<connectorKey>/<name>.json` | Connection resource declaration |
| Both | `userProfile/<userId>/debug_overwrites.json` | Maps abstract resources to Orchestrator instances for debug |

All three required for `uip solution upload` and `uip maestro case debug` to work without "Resource is not configured" warnings.

---

## Cleanup on task removal

When any task is removed and its root bindings are pruned (per [case-editing-operations.md](case-editing-operations.md) § node deletion cascade):

1. After pruning root bindings, regenerate `bindings_v2.json` from the updated array.
