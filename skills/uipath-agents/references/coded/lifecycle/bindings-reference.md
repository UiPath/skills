# Sync Agent Code with bindings.json

Synchronize UiPath platform resource references in agent Python code with the `bindings.json` manifest. This ensures all overridable resources (assets, queues, connections, processes, buckets, context grounding indexes, Action Center apps, and MCP servers) are correctly declared for runtime replacement in Orchestrator.

## When to Use

- After adding, removing, or modifying UiPath SDK resource calls in agent code
- Before packaging/deploying an agent with the [deployment reference](deployment.md) (`uip codedagent pack` / `uip codedagent publish`)
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

Search **every** Python file found in Step 1 for UiPath SDK resource calls that produce bindings. Do NOT limit scanning to the main entry point (`main.py` / `graph.py`) — resource calls are frequently in helper modules, utility files, or store layers.

**Scanning strategy:**
1. Grep ALL `**/*.py` files (excluding `.venv/`, `__pycache__/`, `.uipath/`) for SDK service method patterns listed below.
2. When a match is found, read the file to extract the argument values (resource name, folder path).
3. If the argument is a **module-level constant** (e.g., `BUCKET = "my-bucket"`) rather than an inline string literal, **resolve it** — search the same file (and imports from sibling modules) for the constant definition and use its literal value. This is not dynamic; it is a resolvable constant.
4. Only flag values as truly dynamic when they come from function calls, f-strings, environment variables, or runtime state that cannot be statically determined.

The eight bindable resource types are:

| SDK Service | Method Pattern | Resource Type | Identifier Param |
|------------|---------------|---------------|-----------------|
| `.assets.retrieve` / `.retrieve_async` | `("name", folder_path="folder")` | `asset` | `name` (positional) |
| `.assets.retrieve_credential` / `.retrieve_credential_async` | `("name", folder_path="folder")` | `asset` (with `SubType: "credentialAsset"` in metadata) | `name` (positional) |
| `.queues.create_item` / `.create_item_async` / `.create_items` / `.create_items_async` / `.create_transaction_item` / `.create_transaction_item_async` | `item={"Name": "queue_name", ...}` or `queue_name="queue_name"` | `queue` | `item["Name"]` or `queue_name` |
| `.processes.invoke` / `.invoke_async` | `(name="name", ..., folder_path="folder")` | `process` | `name` |
| `.buckets.*` (all methods: `retrieve`, `upload`, `download`, `delete`, `list_files`, etc.) | `(name="name", folder_path="folder")` | `bucket` | `name` |
| `.tasks.create` / `.create_async` / `.retrieve` / `.retrieve_async` | `(..., app_name="name", app_folder_path="folder")` | `app` | `app_name` |
| `.context_grounding.*` (all methods: `retrieve`, `search`, `add_to_index`, `create_index`, etc.) | `(name="name", folder_path="folder")` | `index` | `name` or `index_name` |
| `.connections.retrieve` / `.retrieve_async` | `("connection_key")` | `connection` | `key` (positional) |
| `.mcp.retrieve` / `.retrieve_async` | `(slug="slug", folder_path="folder")` | `mcpServer` | `slug` |

Use Grep to find calls matching these patterns across all project Python files. Then read the surrounding code to extract the literal string values for resource name and folder path.

**Important:** Only literal or constant-resolvable string arguments can be bound. If a value is truly dynamic (computed at runtime from function calls, f-strings with variables, environment variables, or user input), flag it to the user — it requires manual handling or refactoring. Module-level constants (e.g., `BUCKET = "my-bucket"`) are NOT dynamic — resolve them to their literal values.

**SubType inference during scanning:**

For `retrieve_credential` / `retrieve_credential_async` calls, always emit `"SubType": "credentialAsset"` — the method name is definitive. For all other calls, follow the full lookup procedure in the **SubType Metadata** section below: fetch metadata → filter by kind → disambiguate from code → fall back to `AskUserQuestion` → omit `SubType` if the user skips. Omitting `SubType` is always safe — `uipath push` still creates a virtual placeholder for supported kinds, just with the base `kind` only.

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

For the exact JSON structure of each resource type, consult `bindings-reference.md`. Key rules:

- `version` is always `"2.0"`
- Each resource entry has `resource`, `key`, `value`, and `metadata` fields
- The `key` is `<name>.<folder_path>` for most types, just `<connection_key>` for connections. When `folder_path` is empty, omit the dot separator — the key is just `<name>`
- `ActivityName` in metadata always uses the `_async` variant name
- Connection entries use `ConnectionId` instead of `name` and have no `folderPath`
- The `app` resource type uses the app name as `DisplayLabel`; all others use `"FullName"`
- `SubType` is an optional metadata field — see the **SubType Metadata** section for the full lookup procedure and the `retrieve_credential*` shortcut.
- Entrypoint fields (`EntryPointUniqueId`, `EntryPointPath`) are optional in any resource's `value` block, but when present must include a `displayName` set to the entrypoint's `filePath` from `entry-points.json`

### Step 6: Verify

After writing the updated `bindings.json`:

1. Read it back and validate the JSON is well-formed
2. Confirm each code resource call has a matching binding entry
3. Confirm no orphaned entries remain (unless the user chose to keep them)
4. If entrypoint binding was applied, verify `EntryPointUniqueId` values match valid `uniqueId` entries in `entry-points.json`

## Reference Files

For detailed bindings.json schema, all eight resource type templates, SDK method signatures, and a complete worked example, consult:

- **`bindings-reference.md`** — Full bindings.json format specification and resource type mapping

## Edge Cases

- **Multiple entry points (code scanning)** — Scan ALL Python files in the project (`**/*.py`, excluding `.venv/`, `__pycache__/`, `.uipath/`), not just `main.py` or `graph.py`. Resource calls commonly live in helper modules (e.g., `storage.py`, `utils.py`, tool definition files). When arguments use module-level constants, resolve them to their literal values before creating bindings.
- **Multiple entry points (entrypoint binding)** — When `entry-points.json` has multiple entrypoints, ask the user per-resource which entrypoint it belongs to. User can choose "None" to skip entrypoint binding for that resource.
- **Duplicate resources** — If the same resource (same name + folder) is called multiple times, produce only one binding entry.
- **No folder_path** — Some calls omit `folder_path`. In that case, use an empty string `""` for `folderPath.defaultValue` and construct the key as just `<name>` (no trailing dot).
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
| Push creates wrong asset type as virtual resource | Missing `SubType` in metadata for a `retrieve_credential*` call | Add `"SubType": "credentialAsset"` to the asset's metadata and re-run `uipath push` |
| Push warns "was not found" for connection/mcpServer/index | These kinds do not support virtual-resource fallback | Create the resource in Orchestrator / Integration Service before running `uipath push` |

## Additional Instructions

- Read `bindings-reference.md` before generating or modifying any binding entries — do not guess the JSON structure.
- Confirm stale entry removal with the user before deleting — stale entries may be intentionally kept for future use.
- When in doubt about whether a value is static or dynamic, read the surrounding code context to determine if the string literal is truly constant.
- After updating bindings.json, always re-read it to verify well-formed JSON before reporting success.

---

# bindings.json Reference

Complete reference for the bindings.json file format, resource type mappings, and SDK method signatures.

## File Format

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "<resource_type>",
      "key": "<unique_key>",
      "value": { ... },
      "metadata": { ... }
    }
  ]
}
```

- `version` is always `"2.0"`.
- `resources` is an array of resource binding entries. An empty array (`[]`) is valid when the agent uses no overridable resources.

---

## Resource Types

Eight resource types are supported. Each maps to a specific UiPath SDK service and method.

### Asset

**SDK call:**
```python
asset = await sdk.assets.retrieve_async("asset_name", folder_path="folder_key")
credential = await sdk.assets.retrieve_credential_async("cred_name", folder_path="folder_key")
# or synchronous:
asset = sdk.assets.retrieve("asset_name", folder_path="folder_key")
credential = sdk.assets.retrieve_credential("cred_name", folder_path="folder_key")
```

**Binding entry:**
```json
{
  "resource": "asset",
  "key": "<name>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<name>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "retrieve_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<name>.<folder_path>` — the first positional argument joined with the `folder_path` keyword argument by a dot. When `folder_path` is empty, omit the dot — use just `<name>`.

**Parameter extraction:**
- `name` — first positional argument to `retrieve_async()` / `retrieve()`
- `folder_path` — keyword argument `folder_path=`

**Credential asset variant — `retrieve_credential` / `retrieve_credential_async`:**

When the SDK call is `retrieve_credential` or `retrieve_credential_async`, add `"SubType": "credentialAsset"` to the metadata block. The rest of the binding entry is identical:

```json
{
  "resource": "asset",
  "key": "<name>.<folder_path>",
  "value": {
    "name": { "defaultValue": "<name>", "isExpression": false, "displayName": "Name" },
    "folderPath": { "defaultValue": "<folder_path>", "isExpression": false, "displayName": "Folder Path" }
  },
  "metadata": {
    "ActivityName": "retrieve_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName",
    "SubType": "credentialAsset"
  }
}
```

This SubType is required for `uipath push` to create a credential-asset placeholder (rather than a plain string asset) when the asset doesn't yet exist in Orchestrator.

---

### Queue

**SDK call:**
```python
# create_item / create_item_async — queue name is inside the QueueItem dict
sdk.queues.create_item(item={"Name": "queue_name", "SpecificContent": {...}})
await sdk.queues.create_item_async(item=QueueItem(name="queue_name", specific_content={...}))

# create_items / create_items_async — queue name is a direct parameter
sdk.queues.create_items(queue_name="queue_name", items=[...], commit_type=CommitType.ALL_OR_NOTHING)

# create_transaction_item / create_transaction_item_async — queue name is inside the TransactionItem dict
sdk.queues.create_transaction_item(item={"Name": "queue_name", "SpecificContent": {...}})
```

**Binding entry:**
```json
{
  "resource": "queue",
  "key": "<queue_name>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<queue_name>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "create_item_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<queue_name>.<folder_path>`

**Parameter extraction:**
- `queue_name` — extracted from `QueueItem.name` (alias `"Name"`) inside the `item` dict, or from the `queue_name` keyword argument in `create_items()`
- `folder_path` — inherited from `FolderContext` (set via `sdk.queues` folder configuration or the agent's default folder)

**Note:** The queue name is embedded inside the `item` parameter (a dict or `QueueItem`/`TransactionItem` model), not as a top-level keyword argument like other services. When scanning code, look for the `"Name"` key in the dict literal or `name=` in `QueueItem()`/`TransactionItem()` constructors.

---

### Process

**SDK call:**
```python
result = await sdk.processes.invoke_async(name="process_name", input_arguments={...}, folder_path="folder_path")
# or synchronous:
result = sdk.processes.invoke(name="process_name", input_arguments={...}, folder_path="folder_path")
```

**Binding entry:**
```json
{
  "resource": "process",
  "key": "<name>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<name>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "invoke_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<name>.<folder_path>`

**Parameter extraction:**
- `name` — keyword argument `name=`
- `folder_path` — keyword argument `folder_path=`

**ActivityName:** Always use `invoke_async` in metadata, regardless of whether the code uses the sync or async variant.

---

### Bucket

**SDK call:**
```python
bucket = await sdk.buckets.retrieve_async(name="bucket_name", folder_path="folder_path")
# or synchronous:
bucket = sdk.buckets.retrieve(name="bucket_name", folder_path="folder_path")
```

**Binding entry:**
```json
{
  "resource": "bucket",
  "key": "<name>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<name>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "retrieve_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<name>.<folder_path>`

**Parameter extraction:**
- `name` — keyword argument `name=`
- `folder_path` — keyword argument `folder_path=`

---

### App (Action Center Tasks / Escalations)

**SDK call:**
```python
task = await sdk.tasks.create_async(title="...", data={...}, app_name="app_name", app_folder_path="app_folder_path")
# or synchronous:
task = sdk.tasks.create(title="...", data={...}, app_name="app_name", app_folder_path="app_folder_path")
```

**Binding entry:**
```json
{
  "resource": "app",
  "key": "<app_name>.<app_folder_path>",
  "value": {
    "name": {
      "defaultValue": "<app_name>",
      "isExpression": false,
      "displayName": "App Name"
    },
    "folderPath": {
      "defaultValue": "<app_folder_path>",
      "isExpression": false,
      "displayName": "App Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "create_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "<app_name>"
  }
}
```

**Key construction:** `<app_name>.<app_folder_path>`

**Parameter extraction:**
- `app_name` — keyword argument `app_name=`
- `app_folder_path` — keyword argument `app_folder_path=`

**Note:** The `DisplayLabel` in metadata uses the literal app name value, not `"FullName"`. Both Action Center tasks and escalations use this resource type — `CreateEscalation` extends `CreateTask` with the same `app_name`/`app_folder_path` fields.

---

### Index (Context Grounding)

**SDK call:**
```python
index = await sdk.context_grounding.retrieve_async(name="index_name", folder_path="folder_path")
# also search:
results = await sdk.context_grounding.search_async(name="index_name", query="...", folder_path="folder_path")
# synchronous variants:
index = sdk.context_grounding.retrieve(name="index_name", folder_path="folder_path")
results = sdk.context_grounding.search(name="index_name", query="...", folder_path="folder_path")
```

**Binding entry:**
```json
{
  "resource": "index",
  "key": "<name>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<name>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "retrieve_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<name>.<folder_path>`

**Parameter extraction:**
- `name` — keyword argument `name=`
- `folder_path` — keyword argument `folder_path=`

---

### Connection (Integration Service)

**SDK call:**
```python
connection = await sdk.connections.retrieve_async("connection_key")
# or synchronous:
connection = sdk.connections.retrieve("connection_key")
```

**Binding entry:**
```json
{
  "resource": "connection",
  "key": "<connection_key>",
  "value": {
    "ConnectionId": {
      "defaultValue": "<connection_key>",
      "isExpression": false,
      "displayName": "Connection"
    }
  },
  "metadata": {
    "BindingsVersion": "2.2",
    "Connector": "",
    "UseConnectionService": "True"
  }
}
```

**Key construction:** Just `<connection_key>` (no folder path, no dot).

**Parameter extraction:**
- `connection_key` — first positional argument to `retrieve_async()` / `retrieve()`

**Differences from other resource types:**
- No `folderPath` in `value`
- Uses `ConnectionId` instead of `name` in `value`
- No `ActivityName` in metadata
- Has `Connector` (empty string default) and `UseConnectionService` (`"True"`) in metadata

---

### MCP Server

**SDK call:**
```python
server = await sdk.mcp.retrieve_async(slug="mcp_server_slug", folder_path="folder_path")
# or synchronous:
server = sdk.mcp.retrieve(slug="mcp_server_slug", folder_path="folder_path")
```

**Binding entry:**
```json
{
  "resource": "mcpServer",
  "key": "<slug>.<folder_path>",
  "value": {
    "name": {
      "defaultValue": "<slug>",
      "isExpression": false,
      "displayName": "Name"
    },
    "folderPath": {
      "defaultValue": "<folder_path>",
      "isExpression": false,
      "displayName": "Folder Path"
    }
  },
  "metadata": {
    "ActivityName": "retrieve_async",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

**Key construction:** `<slug>.<folder_path>`

**Parameter extraction:**
- `slug` — keyword argument `slug=` to `retrieve_async()` / `retrieve()`
- `folder_path` — keyword argument `folder_path=`

**Note:** The resource identifier for MCP servers is `slug`, not `name`. The `value.name.defaultValue` in the binding still stores the slug value.

---

## SubType Metadata

The `SubType` field in a resource's `metadata` block specifies a sub-classification of the resource `kind`. It is **optional** but should be emitted when determinable, so `uipath push` can create the correct virtual-resource placeholder when the resource isn't found in the catalog (see `Virtual Resource Fallback on uipath push` below).

### Authoritative source for valid SubType values

The valid SubType values for each kind are defined by the Studio Web Resource Builder metadata. **Do not hardcode or guess** — always look them up from one of these two sources:

1. **Preferred — live endpoint** (when authenticated against a UiPath tenant):
   ```
   GET https://<BASE_URL>/<ORG_ID>/studio_/backend/api/resourcebuilder/metadata
   ```
   Example: `https://cloud.uipath.com/myorg/studio_/backend/api/resourcebuilder/metadata`. Returns the up-to-date list of supported kinds/types for the target tenant.

2. **Fallback — bundled snapshot:** `assets/solutions/metadata.json` (relative to the skill root). Use when the live endpoint is unreachable or the agent is not authenticated. May be stale; the file's `_snapshotDate` shows when it was captured.

### Metadata structure

The two sources return slightly different shapes. The agent only needs `{kind, type}` from each entry — everything else can be ignored.

**Live endpoint** — array of full entries:

```json
[
  { "kind": "asset", "type": "stringAsset", "versions": [ ... ] },
  { "kind": "asset", "type": "credentialAsset", "versions": [ ... ] },
  { "kind": "queue", "versions": [ ... ] }
]
```

**Bundled snapshot** — wrapper with trimmed entries (only `kind` and `type` are kept):

```json
{
  "_snapshotDate": "2026-04-24",
  "_source": "https://<BASE_URL>/<ORG_ID>/studio_/backend/api/resourcebuilder/metadata",
  "_note": "...",
  "entries": [
    { "kind": "asset", "type": "stringAsset" },
    { "kind": "asset", "type": "credentialAsset" },
    { "kind": "queue", "type": null }
  ]
}
```

In both shapes:

- `kind` — maps directly to the binding's `resource` field.
- `type` — optional. When present, this is the `SubType` value to emit. When `null` or absent, the kind has no sub-type.
- A kind may appear in multiple entries (one per valid sub-type). Example: `asset` has 5 entries (`stringAsset`, `integerAsset`, `booleanAsset`, `credentialAsset`, `secretAsset`).

### Lookup procedure

For each binding, follow these steps:

1. **Fetch metadata.** Try the live endpoint first; on any failure (network error, auth failure, non-200 response), read `assets/solutions/metadata.json`. From the bundled snapshot, read the `entries` array; from the live endpoint, use the top-level array directly.
2. **Filter by `kind`.** Select all entries where `kind` equals the binding's `resource` value.
3. **Collect candidate `type` values.** Build a set from the `type` field of the matched entries, dropping `null`/absent values.
4. **Choose a SubType:**
   - **No candidates** (all entries lack `type`) → omit `SubType`.
   - **One candidate** → emit it as `SubType`.
   - **Multiple candidates** → try code-based disambiguation first (see rules below). If no rule matches, **ask the user via `AskUserQuestion`**: present the candidate `type` values as a multiple-choice list plus a `None / skip` option, and include the resource name and folder in the prompt for context. If the user picks `None / skip`, omit `SubType`.

### Refreshing the bundled snapshot

When the live endpoint adds new kinds or types, regenerate `assets/solutions/metadata.json` from an authenticated tenant:

```bash
curl -s -H "Authorization: Bearer <TOKEN>" \
  "https://<BASE_URL>/<ORG_ID>/studio_/backend/api/resourcebuilder/metadata" \
| jq --arg date "$(date -u +%Y-%m-%d)" '{
    _snapshotDate: $date,
    _source: "https://<BASE_URL>/<ORG_ID>/studio_/backend/api/resourcebuilder/metadata",
    _note: "Trimmed projection: agents only consume {kind, type} for SubType lookup.",
    entries: [.[] | {kind, type}]
  }' > skills/uipath-agents/assets/solutions/metadata.json
```

### Known code-based disambiguation rules

Apply these rules in order. Only fall through to the `AskUserQuestion` prompt if none of them produces a confident match.

| Kind | Rule | SubType | Confidence |
|------|------|---------|------------|
| `asset` | SDK call is `retrieve_credential` or `retrieve_credential_async` | `credentialAsset` | **High** — method name is definitive |
| `asset` | The returned value is used/type-annotated as `str` (plain text context, no password/secret naming) | `stringAsset` | Medium — confirm with user if unsure |
| `asset` | The returned value is used/type-annotated as `int` | `integerAsset` | Medium |
| `asset` | The returned value is used/type-annotated as `bool` | `booleanAsset` | Medium |
| `asset` | The variable name or surrounding context suggests a password/API key/credential (e.g. `password`, `api_key`, `secret`, `token`, `pwd`), even without `retrieve_credential*` | `credentialAsset` or `secretAsset` — **ask the user which** | Medium — presence of sensitive naming is a strong signal but `credentialAsset` vs `secretAsset` is not distinguishable from code |

**How to apply the code-based heuristics for `retrieve` / `retrieve_async`:**

1. Find the assignment target: `x = await sdk.assets.retrieve_async("my_asset", folder_path="Finance")`.
2. Check for a type annotation: `x: str = ...` → `stringAsset`; `x: int = ...` → `integerAsset`; `x: bool = ...` → `booleanAsset`.
3. If no annotation, check how `x` is used downstream:
   - Passed to a function expecting `str`, concatenated with strings, used in string formatting → `stringAsset`.
   - Used in arithmetic, compared numerically → `integerAsset`.
   - Used in `if x:` as a truth check where Orchestrator stores it as boolean → `booleanAsset`.
4. Check the variable name and surrounding context against sensitive patterns (`password`, `pwd`, `api_key`, `secret`, `token`, `credential`). If a match is found, prompt the user to choose between `credentialAsset` and `secretAsset` (they differ in how Orchestrator exposes the value).
5. If the heuristic is inconclusive or produces only medium confidence, fall through to the `AskUserQuestion` prompt with the heuristic's best guess pre-highlighted.

### Asking the user (example prompts)

When multiple candidates remain, prompt with the full candidate list from the metadata. Example:

- **Asset** (after excluding the credential shortcut above): *"Select the asset sub-type for `db_config` in folder `Finance`:"* → `stringAsset` / `integerAsset` / `booleanAsset` / `secretAsset` / *None (skip)*
- **Bucket**: *"Select the backing storage for bucket `reports` in folder `Shared`:"* → `orchestratorBucket` / `amazonBucket` / `azureBucket` / *None (skip)*
- **App (`sdk.tasks.*`)**: *"Select the app sub-type for `ApprovalApp` in folder `HR`:"* → `Coded` / `CodedAction` / *None (skip — default app type)*
- **MCP Server**: *"Select the MCP server sub-type for slug `my-server`:"* → `Coded` / `Command` / `Remote` / `UiPath` / *None (skip)*
- **Process (`sdk.processes.invoke` / `sdk.jobs.resume`)**: *"Select the target process sub-type for `InvoiceProcessor` in folder `Finance/Invoices`:"* → `process` / `agent` / `flow` / `api` / `caseManagement` / `processOrchestration` / `testAutomationProcess` / `webApp` / `mcpServer` / *None (skip)*

Always include a `None / skip` option — it means "I don't know, emit no SubType." Batch prompts when possible (one question per binding, sent together) to minimize interruption.

> **Preserve user-supplied SubType values.** When updating an existing `bindings.json`, do not overwrite a SubType value that is already present unless the referenced resource no longer exists in code. Do not re-prompt the user for bindings whose `SubType` is already set.

### Behavior of SubType during push

- If the resource is **found in the catalog**, `SubType` in metadata is ignored — the catalog's sub-type is used.
- If the resource is **not found in the catalog** and the kind supports virtual creation, `SubType` is passed as the `type` field of the virtual-resource creation request. A missing `SubType` for an ambiguous kind results in a virtual resource with only a base `kind`, which may fail or create a placeholder of the wrong type.

---

## Virtual Resource Fallback on uipath push

Starting with `uipath` 2.10.52, `uipath push` creates a virtual resource placeholder when a binding's resource isn't found in the Resource Catalog — the project can be deployed before its dependencies exist. The fallback only works for a subset of kinds.

The push command fetches the supported-kinds list from `/studio_/backend/api/resourcebuilder/metadata` at push time. The static fallback (used when that endpoint is unreachable) is `app, asset, bucket, process, queue, taskCatalog, trigger`.

| Catalog-miss behavior | Kinds |
|----------------------|---------|
| **Creates a virtual resource placeholder** (uses `SubType` from metadata for the placeholder's `type`). Project still deploys. | `app`, `asset`, `bucket`, `process`, `queue`, `taskCatalog`, `trigger` (static fallback; the live endpoint may add more) |
| **Warns and skips.** The resource must exist in Integration Service before push. | `connection` |
| **Warns and skips.** The resource must exist in Orchestrator before push. | `mcpServer`, `index`, and any kind absent from the supported list |

### Implications for binding generation

1. **Emit `SubType` where determinable.** Always emit `"SubType": "credentialAsset"` for `retrieve_credential*` asset calls. Without it, the virtual-resource fallback will create a plain string asset placeholder, causing runtime failures when the agent expects a credential.
2. **Warn the user about non-fallback kinds.** For `connection`, `mcpServer`, and `index` bindings, the referenced resource must exist in Orchestrator before `uipath push`. If it doesn't, the binding is skipped with a warning and the agent will fail at runtime. Flag this to the user when generating such bindings.
3. **Optional `SubType` for bucket.** The bucket's backing storage is not inferable from code. Consider asking the user which storage type their buckets use, so virtual-resource fallback creates the correct kind.

---

## Entrypoint Binding

Any resource in `bindings.json` can optionally be linked to an entrypoint defined in `entry-points.json`. This is done by adding `EntryPointUniqueId` and/or `EntryPointPath` to the resource's `value` block.

### entry-points.json Structure

```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "agent",
      "uniqueId": "708b62c7-15f1-46d8-9564-5d03c6a8668f",
      "type": "agent",
      "input": { ... },
      "output": { ... }
    }
  ]
}
```

Key fields for binding:
- `uniqueId` — UUID that maps to `EntryPointUniqueId` in the binding
- `filePath` — path string that maps to `EntryPointPath` in the binding

### Entrypoint Fields in Resource Value

**Preferred — using `EntryPointUniqueId`** (when `uniqueId` is available in entry-points.json):
```json
{
  "resource": "asset",
  "key": "my_asset.Finance",
  "value": {
    "name": { "defaultValue": "my_asset", "isExpression": false, "displayName": "Name" },
    "folderPath": { "defaultValue": "Finance", "isExpression": false, "displayName": "Folder Path" },
    "EntryPointUniqueId": {
      "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f",
      "isExpression": false,
      "displayName": "agent"
    }
  },
  "metadata": { "ActivityName": "retrieve_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName" }
}
```

**Fallback — using `EntryPointPath`** (only when `uniqueId` is not available):
```json
{
  "resource": "asset",
  "key": "my_asset.Finance",
  "value": {
    "name": { "defaultValue": "my_asset", "isExpression": false, "displayName": "Name" },
    "folderPath": { "defaultValue": "Finance", "isExpression": false, "displayName": "Folder Path" },
    "EntryPointPath": {
      "defaultValue": "agent",
      "isExpression": false,
      "displayName": "agent"
    }
  },
  "metadata": { "ActivityName": "retrieve_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName" }
}
```

### Rules

- **Add only one field per resource** — prefer `EntryPointUniqueId`. Only use `EntryPointPath` as a fallback if the entrypoint has no `uniqueId`.
- The field uses the standard value format: `{ "defaultValue": "...", "isExpression": false, "displayName": "<filePath>" }` — `displayName` is **mandatory** and must be set to the entrypoint's `filePath` value from `entry-points.json`.
- **The field is optional.** If a resource is not bound to any entrypoint, omit it entirely.
- The field goes inside the `value` object alongside `name`, `folderPath`, `ConnectionId`, etc.
- For connections, `EntryPointUniqueId`/`EntryPointPath` sits alongside `ConnectionId` in the `value` block.

### When to Add Entrypoint Fields

- **Single entrypoint** in `entry-points.json` — auto-bind all resources. Add `EntryPointUniqueId` (preferred) or `EntryPointPath` (fallback).
- **Multiple entrypoints** — ask the user per resource. If the user chooses "None", omit the field.
- **No `entry-points.json`** — skip entrypoint binding entirely.

---

## SDK Method to Resource Type Mapping

The `SubType (default)` column below is a quick-reference for the most common case. **The authoritative list of valid SubType values per kind is the Resource Builder metadata** — always run the lookup procedure from `SubType Metadata` before emitting a value.

| SDK Property | Methods | Resource Type | Resource Identifier Param | ActivityName | SubType (default) |
|-------------|---------|---------------|--------------------------|-------------|---------------------|
| `sdk.assets` | `retrieve`, `retrieve_async` | `asset` | `name` (1st positional) | `retrieve_async` | *(omit — code can't disambiguate `stringAsset` / `integerAsset` / `booleanAsset` / `secretAsset`)* |
| `sdk.assets` | `retrieve_credential`, `retrieve_credential_async` | `asset` | `name` (1st positional) | `retrieve_async` | `credentialAsset` |
| `sdk.queues` | `create_item`, `create_item_async`, `create_items`, `create_items_async`, `create_transaction_item`, `create_transaction_item_async` | `queue` | `item["Name"]` or `queue_name` | `create_item_async` | *(omit — kind has no sub-type)* |
| `sdk.processes` | `invoke`, `invoke_async` | `process` | `name` | `invoke_async` | *(omit — target process type not known here)* |
| `sdk.jobs` | `resume`, `resume_async` | `process` | `process_name` | `invoke_async` | *(omit — target process type not known here)* |
| `sdk.buckets` | ALL methods (`retrieve`, `upload`, `download`, `delete`, `list_files`, etc.) | `bucket` | `name` | `retrieve_async` | *(omit — ask user for `orchestratorBucket` / `amazonBucket` / `azureBucket`)* |
| `sdk.tasks` | `create`, `create_async`, `retrieve`, `retrieve_async` | `app` | `app_name` | `create_async` | *(omit — user chooses `Coded` / `CodedAction` / default)* |
| `sdk.context_grounding` | ALL methods (`retrieve`, `search`, `add_to_index`, `create_index`, `delete`, `ingest_data`, etc.) | `index` | `name` or `index_name` | `retrieve_async` | *(omit — must exist in Orchestrator; no virtual fallback)* |
| `sdk.connections` | `retrieve`, `retrieve_async` | `connection` | `key` (1st positional) | *(none)* | *(omit — must exist in Integration Service; no virtual fallback)* |
| `sdk.mcp` | `retrieve`, `retrieve_async` | `mcpServer` | `slug` | `retrieve_async` | *(omit — sub-type is one of `Coded` / `Command` / `Remote` / `UiPath`; ask user)* |

**Note on ActivityName:** Always use the `_async` variant in the `ActivityName` metadata field, regardless of whether the code uses the sync or async version.

**Note on broad override coverage:** For `bucket` and `index` (context_grounding), ALL SDK methods have the `@resource_override` decorator — not just `retrieve`. This means `upload`, `download`, `search`, `add_to_index`, etc. all participate in resource overrides. However, a single binding entry per unique resource (name + folder) is sufficient regardless of how many methods are called on that resource.

---

## SDK Variable Name Patterns

The UiPath SDK instance may be stored in different variable names. Common patterns:

```python
# Direct instantiation
uipath = UiPath()
sdk = UiPath()
client = UiPath()

# Attribute access in LangGraph / tools
self.sdk = UiPath()
```

When scanning code, search for all calls to the relevant service methods (`.assets.retrieve`, `.processes.invoke`, etc.) regardless of the variable name preceding them.

---

## Methods That Do NOT Create Bindings

Not every SDK service supports resource overrides. The following services have NO `@resource_override` decorator and do NOT produce bindings:

- `sdk.llm.*` / `sdk.llm_openai.*` — no bindings support
- `sdk.documents.*` — no bindings support (uses `bucket` bindings for storage via `storage_bucket_name`)
- `sdk.entities.*` — no bindings support
- `sdk.guardrails.*` — no bindings support
- `sdk.attachments.*` — no bindings support
- `sdk.agenthub.*` — no bindings support
- `sdk.folders.*` — no bindings support
- `sdk.resource_catalog.*` — no bindings support

**Note on assets:** `sdk.assets.update()` does NOT have `@resource_override` — only `retrieve` and `retrieve_credential` do.

---

## Dynamic Values vs Resolvable Constants

Not every non-literal argument is dynamic. **Resolve module-level constants before flagging a value as dynamic.**

**Resolvable (DO bind):**
```python
# Module-level constant — resolve to its literal value
BUCKET = "one-alpha-signals"
sdk.buckets.list_files(name=BUCKET, prefix="kiss/")  # → bind as "one-alpha-signals"

# Constant imported from a sibling module in the same project
from .config import QUEUE_NAME  # where QUEUE_NAME = "invoices"
sdk.queues.create_item(item={"Name": QUEUE_NAME, ...})  # → bind as "invoices"
```

**Truly dynamic (flag to user):**
```python
# Runtime function call — cannot resolve statically
asset_name = get_config("asset_name")
asset = await sdk.assets.retrieve_async(asset_name, folder_path=folder)

# f-string with runtime variable
bucket = f"data-{environment}"
sdk.buckets.upload(name=bucket, ...)

# Environment variable
queue = os.environ["QUEUE_NAME"]
```

**Resolution strategy:** When a non-literal argument is found, search the same file for an assignment to that variable name at module scope (e.g., `BUCKET = "..."`). If not found in the same file, check imports from sibling modules within the project (not third-party packages). If the value traces back to a string literal through constants only, use that literal. Otherwise, flag as dynamic.

---

## Complete Example

Given this agent code and a single entrypoint in `entry-points.json`:

**entry-points.json:**
```json
{
  "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
  "$id": "entry-points.json",
  "entryPoints": [
    {
      "filePath": "agent",
      "uniqueId": "708b62c7-15f1-46d8-9564-5d03c6a8668f",
      "type": "agent",
      "input": { ... },
      "output": { ... }
    }
  ]
}
```

**Agent code:**
```python
async def main() -> Response:
    uipath = UiPath()

    asset = await uipath.assets.retrieve_async("my_asset", folder_path="Finance")
    password = await uipath.assets.retrieve_credential_async("db_password", folder_path="Finance")
    conn = await uipath.connections.retrieve_async("salesforce_conn")
    result = await uipath.processes.invoke_async(
        name="InvoiceProcessor", input_arguments={"id": "123"}, folder_path="Finance/Invoices"
    )
    server = await uipath.mcp.retrieve_async(slug="my-mcp-server", folder_path="Shared")

    return Response(...)
```

**The corresponding bindings.json** (with entrypoint binding — single entrypoint with `uniqueId`, so `EntryPointUniqueId` is used):

```json
{
  "version": "2.0",
  "resources": [
    {
      "resource": "asset",
      "key": "my_asset.Finance",
      "value": {
        "name": { "defaultValue": "my_asset", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": "Finance", "isExpression": false, "displayName": "Folder Path" },
        "EntryPointUniqueId": { "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f", "isExpression": false, "displayName": "agent" }
      },
      "metadata": { "ActivityName": "retrieve_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName" }
    },
    {
      "resource": "asset",
      "key": "db_password.Finance",
      "value": {
        "name": { "defaultValue": "db_password", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": "Finance", "isExpression": false, "displayName": "Folder Path" },
        "EntryPointUniqueId": { "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f", "isExpression": false, "displayName": "agent" }
      },
      "metadata": { "ActivityName": "retrieve_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName", "SubType": "credentialAsset" }
    },
    {
      "resource": "connection",
      "key": "salesforce_conn",
      "value": {
        "ConnectionId": { "defaultValue": "salesforce_conn", "isExpression": false, "displayName": "Connection" },
        "EntryPointUniqueId": { "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f", "isExpression": false, "displayName": "agent" }
      },
      "metadata": { "BindingsVersion": "2.2", "Connector": "", "UseConnectionService": "True" }
    },
    {
      "resource": "process",
      "key": "InvoiceProcessor.Finance/Invoices",
      "value": {
        "name": { "defaultValue": "InvoiceProcessor", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": "Finance/Invoices", "isExpression": false, "displayName": "Folder Path" },
        "EntryPointUniqueId": { "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f", "isExpression": false, "displayName": "agent" }
      },
      "metadata": { "ActivityName": "invoke_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName" }
    },
    {
      "resource": "mcpServer",
      "key": "my-mcp-server.Shared",
      "value": {
        "name": { "defaultValue": "my-mcp-server", "isExpression": false, "displayName": "Name" },
        "folderPath": { "defaultValue": "Shared", "isExpression": false, "displayName": "Folder Path" },
        "EntryPointUniqueId": { "defaultValue": "708b62c7-15f1-46d8-9564-5d03c6a8668f", "isExpression": false, "displayName": "agent" }
      },
      "metadata": { "ActivityName": "retrieve_async", "BindingsVersion": "2.2", "DisplayLabel": "FullName" }
    }
  ]
}
```
