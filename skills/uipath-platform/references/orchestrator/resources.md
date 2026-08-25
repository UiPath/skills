# Resources (`uip or`)

Manage Orchestrator resources -- assets, queues, queue items, buckets, files, triggers, libraries, and webhooks.

> **Important:** These commands live under `uip or` (the former standalone resource tool was retired and folded into `uip or`). The old `storage-buckets`/`storage-bucket-files` names are now `buckets`/`bucket-files`.

> For full option details on any command, use `--help` (e.g., `uip or assets list --help`).

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
uip or
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
| `uip or libraries list` | List libraries in the tenant feed. Options: `--limit <N>` (default 50), `--offset <N>`, `--sort-by "<field> <asc\|desc>"`, `--all-fields`. No native search — filter client-side via global `--output-filter "<JMESPath>"`. Returns curated rows: `Key`, `Title`, `Version`, `Authors`, `Published`, `IsLatestVersion`, `IsPrerelease`, `ProjectType`. Note: `Published` is often empty on list rows (the bare collection endpoint doesn't populate it server-side); `get`/`versions` return it. |
| `uip or libraries get <key>` | Get library details. Key format is `PackageId:Version` (e.g., `MyLib:1.0.0`). Returns a curated detail view (adds `Description`, `PackageSize`, `Created`, `LastUpdated`, etc.); `--all-fields` for the raw DTO. Dates the feed doesn't track are returned as empty strings (the API serializes 0001-01-01 sentinels; the CLI strips them). |
| `uip or libraries versions <package-id>` | List all versions of a library by package ID (the `Title` from `list` output). Curated rows like `list`; `--all-fields` for raw. Fails with `Library not found` when the package ID doesn't exist (instead of an empty success). |
| `uip or libraries upload --file <path>` | Upload a `.nupkg` library package to the tenant feed. The file must exist (checked client-side). The default shared feed is read-only on many tenants — if upload fails with a read-only/feed-not-found error, enable Tenant Libraries in tenant settings or target a writable feed with `--feed-id` (`uip or feeds list`). |
| `uip or libraries download <key> --destination <path>` | Download a `.nupkg` to local disk. `--destination` creates missing parent dirs and overwrites an existing file. |
| `uip or libraries delete <key>` | Delete a specific library version. Key format is `PackageId:Version` (validated client-side). |

```bash
# List libraries (first 500). Default --limit is 50; bump it for tenants with many libraries.
uip or libraries list --limit 500 --output json

# Filter by name client-side. Title can be null — guard with `Title != null` or contains() will error.
uip or libraries list --limit 500 \
  --output-filter "[?Title != null && contains(Title, 'Excel')]" \
  --output json

# Multi-keyword OR filter
uip or libraries list --limit 500 \
  --output-filter "[?Title != null && (contains(Title, 'Common') || contains(Title, 'Shared'))]" \
  --output json

# Upload a library
uip or libraries upload --file ./MyLibrary.1.0.0.nupkg --output json

# List versions, then download a specific one
uip or libraries versions "UiPath.System.Activities" --output json
uip or libraries download "UiPath.System.Activities:24.10.0" \
  --destination ./system-activities.nupkg --output json

# Delete an old version
uip or libraries delete "UiPath.System.Activities:24.4.0" --yes --output json
```

---

## Output Behavior

These commands return a **curated PascalCase view** by default — a focused projection of the most useful fields. Pass `--all-fields` on list/get-style commands to receive the raw API DTO instead (raw DTO keys are camelCase; the two shapes do not share casing). This matches the convention across all `uip or` commands; see [orchestrator.md](orchestrator.md).

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

- **Orchestrator** (`uip or`) — folders, jobs, processes, packages, users, machines → [orchestrator.md](orchestrator.md)
- **Solutions** (`uip solution`) — pack, publish, deploy solution packages → [`uipath-solution`](/uipath:uipath-solution)
- **Folder/user setup** — required before folder-scoped resources can be used → [setup-environment.md](setup-environment.md)
