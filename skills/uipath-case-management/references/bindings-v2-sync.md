# bindings_v2.json and Connection Resource Sync

Shared procedure for keeping `bindings_v2.json` and connection resource files in sync after any plugin writes to `root.data.uipath.bindings[]` in `caseplan.json`.

## When to Run

After any plugin creates or modifies entries in `root.data.uipath.bindings[]`. Currently applies to connector plugins only:
- connector-activity ([impl-json.md](plugins/tasks/connector-activity/impl-json.md) § 3a-post)
- connector-trigger / event trigger (via [connector-trigger-common.md](connector-trigger-common.md) § Root-level bindings post-sync)

Non-connector tasks (process, agent, rpa, action, api-workflow, case-management) do not write root bindings in the JSON path and do not need this procedure.

---

## § Regenerate bindings_v2.json

After writing bindings to `root.data.uipath.bindings[]`, regenerate `bindings_v2.json` from the **complete** bindings array.

### Procedure

1. Read `caseplan.json` to get the current `root.data.uipath.bindings` array.
2. Write `bindings_v2.json` in the same directory as `caseplan.json`:

```json
{
  "version": "2.0",
  "resources": [<entire root.data.uipath.bindings array>]
}
```

### Rules

- **Full overwrite** — always regenerate from the complete array, never append. Multiple connector tasks may share or deduplicate bindings; regenerating from the full array ensures consistency.
- **Use the Write tool** — this is a wholesale replacement, not a partial edit.
- **Path** — same directory as `caseplan.json`: `<SolutionDir>/<ProjectName>/bindings_v2.json`.
- **Deduplication** is already handled at the root bindings level by each plugin (see [bindings/impl-json.md](plugins/variables/bindings/impl-json.md) § Deduplication). The regenerated array is already deduped.

---

## § Create Connection Resource File

For each **new** connection used by a connector task, create a resource file so that `uip solution resource refresh` and `uip solution upload` can register it on Studio Web.

### When to create

In the same plugin step that creates the root binding (connector-activity § 3a-post, connector-trigger-common § Root-level bindings post-sync). The data needed is already captured from the `get-connection` CLI call.

### Path

```
<SolutionDir>/resources/solution_folder/connection/<connectorKey>/<connectionName>.json
```

### Directory creation

The directory may not exist. Create it before writing:

```bash
mkdir -p "<SolutionDir>/resources/solution_folder/connection/<connectorKey>"
```

### Deduplication

Multiple connector tasks may use the same connection. Before creating the file, check if a file already exists in `<SolutionDir>/resources/solution_folder/connection/<connectorKey>/` for this `connectionId`. If any file in that directory contains `"key": "<connectionId>"`, skip — the resource already exists.

In practice, check if the directory exists and contains any `.json` file with the matching connection name. If so, skip creation.

### Resource file shape

```json
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<connectionName>",
    "kind": "connection",
    "type": "<connectorKey>",
    "apiVersion": "integrationservice.uipath.com/v1",
    "isOverridable": true,
    "dependencies": [],
    "runtimeDependencies": [],
    "files": [],
    "folders": [{ "fullyQualifiedName": "solution_folder" }],
    "spec": {
      "connectorName": "<connectorName>",
      "name": "<connectionName>",
      "description": null,
      "authenticationType": "AuthenticateAfterDeployment",
      "connectorVersion": "<connectorVersion if available, omit key if null>",
      "connectorKey": "<connectorKey>"
    },
    "locks": [],
    "key": "<connectionId>"
  }
}
```

### Field sources

| Field | Source | Plugin step |
|---|---|---|
| `connectionName` | `.Data.Connections[selected].name` from `get-connection` | Step 1 |
| `connectorKey` | `connector-key` from `tasks.md` | Planning |
| `connectorName` | `.Data.Connections[selected].connector.name` from `get-connection` | Step 1 |
| `connectorVersion` | `enrichment.connectorVersion` from `tasks describe` (triggers only; `null` for activities) | Step 2 |
| `connectionId` | `connection-id` from `tasks.md` | Planning |

### Graceful degradation

If `get-connection` failed (Step 1), the plugin has no `connectionName` or `connectorName`. In that case, **skip** both the connection resource file and `bindings_v2.json` regeneration — no root bindings were written, so there is nothing to sync.

---

## Cleanup on task removal

When a connector task is removed and its root bindings are pruned (per [caseplan-editing.md](caseplan-editing.md) § node deletion cascade):

1. After pruning root bindings, regenerate `bindings_v2.json` from the updated array.
2. If a connection's bindings were **all** pruned (no remaining task references that connectionId), also remove the corresponding connection resource file from `resources/solution_folder/connection/<connectorKey>/`.
