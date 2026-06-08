# Resources (`uip resource`)

Manage Orchestrator resources -- assets, queues, queue items, buckets, files, triggers, libraries, and webhooks.

> **Important:** These commands use `uip resource`, NOT `uip or`. The old `storage-buckets`/`storage-bucket-files` names have been renamed to `buckets`/`bucket-files`.

> For full option details on any command, use `--help` (e.g., `uip resource assets list --help`).

---

## Common Flags

| Flag | Scope | Purpose |
|------|-------|---------|
| `--tenant <name>` | All commands | Override the default tenant. |
| `--output json` | All commands | Emit structured JSON. Always use this when parsing output programmatically. |
| `--folder-path <path>` | Folder-scoped commands | Target folder by path (e.g., `"Finance"` or `"Finance/Invoicing"`). |
| `--folder-key <key>` | Folder-scoped commands | Target folder by GUID key. |
| `--limit <n>` | List commands | Number of items to return (default 50). |
| `--offset <n>` | List commands | Number of items to skip for pagination. |
| `--sort-by <field>` | List commands | OData-style sort (e.g., `'Name asc'`, `'Id desc'`). |

---

## Command Tree

```
uip resource
  ├── assets              (9 verbs)
  ├── queues              (8 verbs)
  ├── queue-items         (15 verbs)
  ├── buckets             (8 verbs)
  ├── bucket-files        (8 verbs)
  ├── triggers            (8 verbs)
  ├── libraries           (6 verbs)
  └── webhooks            (7 verbs)
```

---

## Workflow References

Each workflow doc covers a multi-command choreography for a specific goal. Load the one that matches your task.

| Workflow | File | Covers |
|----------|------|--------|
| Manage Assets | [manage-assets.md](manage-assets.md) | Create, share, rotate, and delete assets |
| Process Queues | [process-queues.md](process-queues.md) | Queues, queue items, transactions, reviews |
| Work with Storage | [work-with-storage.md](work-with-storage.md) | Buckets, file upload/download, pre-signed URLs |
| Triggers & Webhooks | [triggers-and-webhooks.md](triggers-and-webhooks.md) | Time/queue/API triggers, webhook management |

---

## Libraries

Libraries are tenant-scoped -- no folder context needed.

| Command | Description |
|---------|-------------|
| `uip resource libraries list` | List libraries in the tenant feed. Options: `--limit <N>` (default 50), `--offset <N>`, `--sort-by "<field> <asc\|desc>"`. No native search — filter client-side via global `--output-filter "<JMESPath>"`. Returns `Key`, `Title`, `Version`, `Authors`. |
| `uip resource libraries get <key>` | Get library details. Key format is `PackageId:Version` (e.g., `MyLib:1.0.0`). Returns the full API DTO. |
| `uip resource libraries versions <package-id>` | List all versions of a library by package ID (the `Title` from `list` output). |
| `uip resource libraries upload --file <path>` | Upload a `.nupkg` library package to the tenant feed. |
| `uip resource libraries download <key> --destination <path>` | Download a `.nupkg` to local disk. |
| `uip resource libraries delete <key>` | Delete a specific library version. |

```bash
# List libraries (first 500). Default --limit is 50; bump it for tenants with many libraries.
uip resource libraries list --limit 500 --output json

# Filter by name client-side. Title can be null — guard with `Title != null` or contains() will error.
uip resource libraries list --limit 500 \
  --output-filter "[?Title != null && contains(Title, 'Excel')]" \
  --output json

# Multi-keyword OR filter
uip resource libraries list --limit 500 \
  --output-filter "[?Title != null && (contains(Title, 'Common') || contains(Title, 'Shared'))]" \
  --output json

# Upload a library
uip resource libraries upload --file ./MyLibrary.1.0.0.nupkg --output json

# List versions, then download a specific one
uip resource libraries versions "UiPath.System.Activities" --output json
uip resource libraries download "UiPath.System.Activities:24.10.0" \
  --destination ./system-activities.nupkg --output json

# Delete an old version
uip resource libraries delete "UiPath.System.Activities:24.4.0" --output json
```

---

## Output Behavior

Resource tool commands return **full API responses** (all fields) by default. There is no `--all-fields` flag — the convention in `resource-tool` is raw camelCase DTO. (This differs from `orchestrator-tool`, which curates by default and exposes `--all-fields` for the raw view; see [`uipath-orchestrator`](../orchestrator/orchestrator.md).)

List responses include a `Pagination` block:

```json
{
  "Pagination": { "Returned": 50, "Limit": 50, "Offset": 0, "HasMore": true },
  "Data": [...]
}
```

When `HasMore` is `true`, increment `--offset` by `--limit` and fetch again. Continue until `HasMore` is `false` or `Returned < Limit`.

---

## Related

- **Orchestrator** (`uip or`) — folders, jobs, processes, packages, users, machines → [`uipath-orchestrator`](../orchestrator/orchestrator.md)
- **Solutions** (`uip solution`) — pack, publish, deploy solution packages → [`uipath-solution`](/uipath:uipath-solution)
- **Folder/user setup** — required before folder-scoped resources can be used → [`uipath-orchestrator/setup-environment`](../orchestrator/setup-environment.md)
