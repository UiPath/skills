---
name: bindings
description: Synchronize UiPath agent code with bindings.json for resource overrides. Scan Python code to detect UiPath SDK resource calls (assets, queues, connections, processes, buckets, context grounding, tasks, MCP servers) and generate or update bindings.json entries. This skill should be used when the user says "sync bindings", "update bindings.json", "generate bindings", "check bindings", "fix bindings.json", "add resource bindings", "sync resources", or mentions resource overrides, bindings drift, or bindings.json synchronization.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
user-invocable: true
---

# Sync Agent Code with bindings.json

Synchronize UiPath platform resource references in agent Python code with the `bindings.json` manifest. This ensures all overridable resources (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, and MCP servers) are correctly declared for runtime replacement in Orchestrator.

## When to Use

- After adding, removing, or modifying UiPath SDK resource calls in agent code
- Before packaging/deploying an agent with the [Deploy skill](/uipath-coded-agents:deploy) (`uipath pack` / `uipath publish`)
- When resource override configuration in Orchestrator is missing entries or shows stale resources
- To audit existing bindings.json for correctness

## Workflow

### Step 1: Locate Project Files

Find the project root by looking for `pyproject.toml` or `uipath.json`. Then locate:

1. **All Python source files** — Glob for `**/*.py` in the project root (exclude `.venv/`, `__pycache__/`, `.uipath/`)
2. **Existing `bindings.json`** — Should be at the project root alongside `pyproject.toml`
3. **`entry-points.json`** — Should be at the project root. Read it to discover available entrypoints (each has a `uniqueId` and `filePath`). This is needed for entrypoint binding in Step 4.

If `bindings.json` does not exist, create it with the empty skeleton:

```json
{
  "version": "2.0",
  "resources": []
}
```

### Step 2: Scan Code for Resource Calls

Search all Python files for UiPath SDK resource calls that produce bindings. The eight bindable resource types are:

| SDK Service | Method Pattern | Resource Type | Identifier Param |
|------------|---------------|---------------|-----------------|
| `.assets.retrieve` / `.retrieve_async` / `.retrieve_credential` / `.retrieve_credential_async` | `("name", folder_path="folder")` | `asset` | `name` (positional) |
| `.queues.create_item` / `.create_item_async` / `.create_items` / `.create_items_async` / `.create_transaction_item` / `.create_transaction_item_async` | `item={"Name": "queue_name", ...}` or `queue_name="queue_name"` | `queue` | `item["Name"]` or `queue_name` |
| `.processes.invoke` / `.invoke_async` | `(name="name", ..., folder_path="folder")` | `process` | `name` |
| `.buckets.*` (all methods: `retrieve`, `upload`, `download`, `delete`, `list_files`, etc.) | `(name="name", folder_path="folder")` | `bucket` | `name` |
| `.tasks.create` / `.create_async` / `.retrieve` / `.retrieve_async` | `(..., app_name="name", app_folder_path="folder")` | `app` | `app_name` |
| `.context_grounding.*` (all methods: `retrieve`, `search`, `add_to_index`, `create_index`, etc.) | `(name="name", folder_path="folder")` | `index` | `name` or `index_name` |
| `.connections.retrieve` / `.retrieve_async` | `("connection_key")` | `connection` | `key` (positional) |
| `.mcp.retrieve` / `.retrieve_async` | `(slug="slug", folder_path="folder")` | `mcpServer` | `slug` |

Use Grep to find calls matching these patterns. Then read the surrounding code to extract the literal string values for resource name and folder path.

**Important:** Only literal string arguments can be bound. If a value is dynamic (variable, f-string, function call), flag it to the user — it requires manual handling or refactoring.

### Step 3: Compare with Existing Bindings

Read the current `bindings.json` and compare:

1. **Missing in bindings** — Resource calls found in code but no matching entry in bindings.json
2. **Stale in bindings** — Entries in bindings.json with no matching resource call in code
3. **Mismatched values** — Entries where the key, name, or folder path differs from code

Report the comparison results to the user before making changes.

### Step 4: Resolve Entrypoint Bindings

Each resource can optionally be linked to an entrypoint from `entry-points.json`. This step determines whether to add `EntryPointUniqueId` and/or `EntryPointPath` to each resource's `value` block.

**Rules:**
- Add **only one** entrypoint field per resource — prefer `EntryPointUniqueId`. Only fall back to `EntryPointPath` if `uniqueId` is not available in the entrypoint definition.
- The field follows the standard value format: `{ "defaultValue": "...", "isExpression": false, "displayName": "<filePath>" }` — `displayName` is **mandatory** and must be set to the entrypoint's `filePath` value from `entry-points.json`
- `EntryPointUniqueId` maps to the `uniqueId` field of an entrypoint in `entry-points.json`
- `EntryPointPath` maps to the `filePath` field of an entrypoint in `entry-points.json`

**Workflow:**
1. **Single entrypoint** — If `entry-points.json` contains exactly one entrypoint, automatically bind all resources to it. Add `EntryPointUniqueId` (preferred) or `EntryPointPath` (fallback). No need to ask the user.
2. **Multiple entrypoints** — Use `AskUserQuestion` to ask the user which entrypoint each resource should be bound to. Present the entrypoint names/filePaths as choices. Include a **"None"** option — if the user chooses "None", omit the entrypoint field from that resource's `value`.
3. **No `entry-points.json`** — Skip entrypoint binding entirely.
4. **Existing entrypoint fields** — If a resource already has `EntryPointUniqueId`/`EntryPointPath`, preserve them unless the referenced entrypoint no longer exists in `entry-points.json` (flag as stale).

### Step 5: Update bindings.json

After confirming with the user, update `bindings.json`:

- **Add** entries for resources found in code but missing from bindings
- **Remove** entries that are stale (no longer referenced in code), after user confirmation
- **Update** entries where values have drifted
- **Add/update entrypoint fields** per Step 4 resolution

For the exact JSON structure of each resource type, consult `references/bindings-reference.md`. Key rules:

- `version` is always `"2.0"`
- Each resource entry has `resource`, `key`, `value`, and `metadata` fields
- The `key` is `<name>.<folder_path>` for most types, just `<connection_key>` for connections
- `ActivityName` in metadata always uses the `_async` variant name
- Connection entries use `ConnectionId` instead of `name` and have no `folderPath`
- The `app` resource type uses the app name as `DisplayLabel`; all others use `"FullName"`
- Entrypoint fields (`EntryPointUniqueId`, `EntryPointPath`) are optional in any resource's `value` block, but when present must include a `displayName` set to the entrypoint's `filePath` from `entry-points.json`

### Step 6: Verify

After writing the updated `bindings.json`:

1. Read it back and validate the JSON is well-formed
2. Confirm each code resource call has a matching binding entry
3. Confirm no orphaned entries remain (unless the user chose to keep them)
4. If entrypoint binding was applied, verify `EntryPointUniqueId` values match valid `uniqueId` entries in `entry-points.json`

## Reference Files

For detailed bindings.json schema, all eight resource type templates, SDK method signatures, and a complete worked example, consult:

- **`references/bindings-reference.md`** — Full bindings.json format specification and resource type mapping

## Edge Cases

- **Multiple entry points (code scanning)** — Scan all Python files, not just `main.py`. LangGraph agents may define tools in separate modules.
- **Multiple entry points (entrypoint binding)** — When `entry-points.json` has multiple entrypoints, ask the user per-resource which entrypoint it belongs to. User can choose "None" to skip entrypoint binding for that resource.
- **Duplicate resources** — If the same resource (same name + folder) is called multiple times, produce only one binding entry.
- **No folder_path** — Some asset calls omit `folder_path`. In that case, use an empty string `""` for `folderPath.defaultValue` and construct the key as just `<name>.` (name followed by a dot and empty string).
- **LangGraph ContextGroundingVectorStore** — `ContextGroundingVectorStore(index_name="...", folder_path="...")` creates an `index` binding with the same structure as `context_grounding.retrieve_async`.
- **Sync vs async** — Both `retrieve()` and `retrieve_async()` produce the same binding. Always use the `_async` method name in `ActivityName`.
- **Jobs resume** — `sdk.jobs.resume(process_name="...")` creates a `process` binding (identifier param is `process_name`, not `name`).
- **Broad override coverage** — For `bucket` and `index`, ALL SDK methods (upload, download, search, add_to_index, etc.) participate in overrides, not just `retrieve`. One binding entry per unique resource suffices.
- **Queue name extraction** — Queue names are nested inside the `item` dict (`"Name"` key) or `QueueItem`/`TransactionItem` model (`name=` field), not as a top-level keyword argument. For `create_items`, the queue name is the direct `queue_name` parameter. Scan for all three patterns.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid JSON in bindings.json | Malformed file from manual edit or merge conflict | Read the file, fix syntax errors, and re-validate |
| Dynamic value cannot be auto-bound | Resource name or folder path is a variable, f-string, or function return | Refactor to use literal strings, or add the binding entry manually |
| Duplicate key in resources array | Same resource scanned from multiple code paths | Deduplicate — keep one entry per unique key |
| Missing project root | No `pyproject.toml` or `uipath.json` found | Verify the working directory is a UiPath agent project |
| Stale entries after refactor | Old resource calls removed but bindings.json not updated | Run the full sync workflow to detect and remove orphaned entries |

## Additional Instructions

- Read `references/bindings-reference.md` before generating or modifying any binding entries — do not guess the JSON structure.
- Confirm stale entry removal with the user before deleting — stale entries may be intentionally kept for future use.
- When in doubt about whether a value is static or dynamic, read the surrounding code context to determine if the string literal is truly constant.
- After updating bindings.json, always re-read it to verify well-formed JSON before reporting success.
