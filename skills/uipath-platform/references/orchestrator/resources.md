# Resources (`uip or`)

Manage Orchestrator assets, queues, queue items, buckets, files, triggers, libraries, and webhooks. Run these commands under `uip or`; the former standalone resource tool was retired. `storage-buckets`/`storage-bucket-files` are now `buckets`/`bucket-files`. Run `uip or <resource> <verb> --help` for full option details (e.g., `uip or assets list --help`).

---

## Common Flags

| Flag | Scope | Purpose |
|------|-------|---------|
| `--tenant <name>` | All commands | Override the default tenant. |
| `--output json` | All commands | Emit structured JSON; always use when parsing programmatically. |
| `--folder-path <path>` | Folder-scoped commands | Target a folder by path, such as `"Finance"` or `"Finance/Invoicing"`. |
| `--folder-key <key>` | Folder-scoped commands | Target a folder by GUID key. |
| `--limit <n>` | List commands | Number of items; default 50. |
| `--offset <n>` | List commands | Number of items to skip for pagination. |
| `--sort-by <field>` | List commands | OData-style sort, such as `'Name asc'` or `'Id desc'`. |

---

## Command Tree

```
uip or
  ├── assets              (9 verbs)
  ├── queues              (8 verbs)
  ├── queue-roi           (4 verbs)
  ├── queue-items         (15 verbs)
  ├── buckets             (8 verbs)
  ├── bucket-files        (8 verbs)
  ├── triggers            (8 verbs)
  ├── libraries           (6 verbs)
  └── webhooks            (7 verbs)
```

---

## Workflow References

Load the matching workflow for any multi-command goal:

| Workflow | File | Covers |
|----------|------|--------|
| Manage Assets | [manage-assets.md](manage-assets.md) | Create, share, rotate, and delete assets |
| Process Queues | [process-queues.md](process-queues.md) | Queues, queue items, transactions, reviews |
| Business ROI | [business-roi.md](business-roi.md) | ROI inputs per queue (`queue-roi`) and process (`process-roi`) |
| Work with Storage | [work-with-storage.md](work-with-storage.md) | Buckets, file upload/download, pre-signed URLs |
| Triggers & Webhooks | [triggers-and-webhooks.md](triggers-and-webhooks.md) | Time/queue/API triggers and webhook management |

---

## Libraries

Libraries are tenant-scoped; no folder context is needed.

| Command | Behavior |
|---------|----------|
| `uip or libraries list` | List tenant-feed libraries; supports `--limit <N>` (default 50), `--offset <N>`, `--sort-by "<field> <asc\|desc>"`, and `--all-fields`. There is no native search: filter client-side with global `--output-filter "<JMESPath>"`. Curated rows contain `Key`, `Title`, `Version`, `Authors`, `Published`, `IsLatestVersion`, `IsPrerelease`, `ProjectType`. `Published` is often empty because the bare collection endpoint does not populate it; `get`/`versions` return it. |
| `uip or libraries get <key>` | Get `PackageId:Version` details (for example, `MyLib:1.0.0`). Curated output adds `Description`, `PackageSize`, `Created`, `LastUpdated`, etc.; use `--all-fields` for the raw DTO. Untracked dates are empty strings because the API serializes 0001-01-01 sentinels and the CLI strips them. |
| `uip or libraries versions <package-id>` | List versions by package ID (`Title` from `list`); curated rows match `list`, and `--all-fields` returns raw output. A nonexistent package ID fails with `Library not found`, not empty success. |
| `uip or libraries upload --file <path>` | Upload a `.nupkg`; the file must exist (client-side check). The default shared feed is read-only on many tenants. If upload returns a read-only/feed-not-found error, enable Tenant Libraries in tenant settings or target a writable feed with `--feed-id` (`uip or feeds list`). |
| `uip or libraries download <key> --destination <path>` | Download a `.nupkg`; `--destination` creates missing parent directories and overwrites an existing file. |
| `uip or libraries delete <key>` | Delete one library version. Key format is `PackageId:Version` and is validated client-side. |

```bash
uip or libraries list --limit 500 --output json
uip or libraries list --limit 500 --output-filter "[?Title != null && contains(Title, 'Excel')]" --output json
uip or libraries list --limit 500 --output-filter "[?Title != null && (contains(Title, 'Common') || contains(Title, 'Shared'))]" --output json
uip or libraries upload --file ./MyLibrary.1.0.0.nupkg --output json
uip or libraries versions "UiPath.System.Activities" --output json
uip or libraries download "UiPath.System.Activities:24.10.0" --destination ./system-activities.nupkg --output json
uip or libraries delete "UiPath.System.Activities:24.4.0" --yes --output json
```

For `Title` filters, guard nulls with `Title != null`; otherwise `contains()` errors.

---

## Output Behavior

By default, commands return a curated PascalCase projection. On list/get-style commands, pass `--all-fields` for the raw API DTO, whose keys are camelCase; the shapes have different casing. This applies across `uip or`; see [orchestrator.md](orchestrator.md).

List responses include:

```json
{
  "Pagination": { "Returned": 50, "Limit": 50, "Offset": 0, "HasMore": true },
  "Data": [...]
}
```

When `HasMore` is `true`, increment `--offset` by `--limit` and fetch again until `HasMore` is `false` or `Returned < Limit`.

---

## Related

- **Orchestrator** (`uip or`) — folders, jobs, processes, packages, users, machines → [orchestrator.md](orchestrator.md)
- **Solutions** (`uip solution`) — pack, publish, deploy solution packages → [`uipath-solution`](/uipath:uipath-solution)
- **Folder/user setup** — required before folder-scoped resources can be used → [setup-environment.md](setup-environment.md)