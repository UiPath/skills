# Resources (`uip or`)

Manage Orchestrator assets, queues, queue items, buckets, files, triggers, libraries, and webhooks.

> **Important:** Run these commands under `uip or`; the former standalone resource tool was retired. Use `buckets`/`bucket-files`, not `storage-buckets`/`storage-bucket-files`.

> For full options, run `uip or <resource> <verb> --help`.

## Common Flags

| Flag | Scope | Purpose |
|------|-------|---------|
| `--tenant <name>` | All commands | Override the default tenant. |
| `--output json` | All commands | Emit structured JSON for programmatic parsing. |
| `--folder-path <path>` | Folder-scoped commands | Target a folder by path, such as `"Finance"` or `"Finance/Invoicing"`. |
| `--folder-key <key>` | Folder-scoped commands | Target a folder by GUID key. |
| `--limit <n>` | List commands | Number of items returned; default 50. |
| `--offset <n>` | List commands | Number of items to skip. |
| `--sort-by <field>` | List commands | OData-style sort, such as `'Name asc'` or `'Id desc'`. |

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

## Workflow References

Load the workflow document matching the task:

| Workflow | File | Covers |
|----------|------|--------|
| Manage Assets | [manage-assets.md](manage-assets.md) | Create, share, rotate, and delete assets |
| Process Queues | [process-queues.md](process-queues.md) | Queues, queue items, transactions, reviews |
| Work with Storage | [work-with-storage.md](work-with-storage.md) | Buckets, file upload/download, pre-signed URLs |
| Triggers & Webhooks | [triggers-and-webhooks.md](triggers-and-webhooks.md) | Time/queue/API triggers, webhook management |

## Libraries

Libraries are tenant-scoped; no folder context is needed.

| Command | Description |
|---------|-------------|
| `uip or libraries list` | List libraries in the tenant feed. Options: `--limit <N>` (default 50), `--offset <N>`, `--sort-by "<field> <asc\|desc>"`, `--all-fields`. There is no native search; filter client-side with global `--output-filter "<JMESPath>"`. Curated rows contain `Key`, `Title`, `Version`, `Authors`, `Published`, `IsLatestVersion`, `IsPrerelease`, `ProjectType`. `Published` is often empty in list rows because the bare collection endpoint does not populate it; `get`/`versions` return it. |
| `uip or libraries get <key>` | Get library details. Use key format `PackageId:Version`, such as `MyLib:1.0.0`. The curated view adds `Description`, `PackageSize`, `Created`, `LastUpdated`, etc.; use `--all-fields` for the raw DTO. Dates the feed does not track are empty strings because the API serializes 0001-01-01 sentinels and the CLI strips them. |
| `uip or libraries versions <package-id>` | List all versions by package ID, which is the `Title` from `list` output. Use `--all-fields` for raw rows. A nonexistent package ID fails with `Library not found` instead of returning an empty success. |
| `uip or libraries upload --file <path>` | Upload a `.nupkg` package; the file must exist, checked client-side. The default shared feed is read-only on many tenants. If upload fails with a read-only/feed-not-found error, enable Tenant Libraries in tenant settings or target a writable feed with `--feed-id` (`uip or feeds list`). |
| `uip or libraries download <key> --destination <path>` | Download a `.nupkg`; `--destination` creates missing parent directories and overwrites an existing file. |
| `uip or libraries delete <key>` | Delete a specific library version. Use key format `PackageId:Version`; it is validated client-side. |

Run these examples as needed:

```bash
# List libraries (first 500). Default --limit is 50; bump it for tenants with many libraries.
uip or libraries list --limit 500 --output json

# Filter by name client-side. Title can be null — guard with Title != null or contains() will error.
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

## Output Behavior

By default, commands return a **curated PascalCase view**. On list/get-style commands, pass `--all-fields` for the raw API DTO, whose keys are camelCase; the shapes do not share casing. This follows the `uip or` convention described in [orchestrator.md](orchestrator.md).

List responses include:

```json
{
  "Pagination": { "Returned": 50, "Limit": 50, "Offset": 0, "HasMore": true },
  "Data": [...]
}
```

When `HasMore` is `true`, run another request with `--offset` increased by `--limit`. Continue until `HasMore` is `false` or `Returned < Limit`.

## Related

- **Orchestrator** (`uip or`) — folders, jobs, processes, packages, users, machines → [orchestrator.md](orchestrator.md)
- **Solutions** (`uip solution`) — pack, publish, deploy solution packages → [`uipath-solution`](/uipath:uipath-solution)
- **Folder/user setup** — required before folder-scoped resources can be used → [setup-environment.md](setup-environment.md)