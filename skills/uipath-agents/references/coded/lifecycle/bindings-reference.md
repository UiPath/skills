# Sync Agent Code with bindings.json

Synchronize UiPath platform resource references in agent Python code with the root `bindings.json` manifest so overridable resources are declared for Orchestrator replacement. Covered resources: assets, queues, connections, processes, buckets, context-grounding indexes, Action Center apps, and MCP servers.

## When to Use

Use this skill after adding, removing, or modifying UiPath SDK resource calls; before deploying with the [deployment reference](deployment.md) (`uip codedagent deploy`); when Orchestrator override configuration is missing or stale; or to audit an existing `bindings.json`.

## Workflow

### Step 1: Locate Project Files

Find the project root by locating `pyproject.toml` or `uipath.json`.

1. Glob for every `**/*.py` below the root, excluding `.venv/`, `__pycache__/`, and `.uipath/`.
2. Locate root-level `bindings.json`, alongside `pyproject.toml`. If absent, create:

```json
{
  "version": "2.0",
  "resources": []
}
```

3. Locate and read root-level `entry-points.json`; each entrypoint has `uniqueId` and `filePath`, needed in Step 4.

### Step 2: Scan Code for Resource Calls

Search every discovered Python file, regardless of SDK variable name (`uipath`, `sdk`, `client`, `self.sdk`, or another name). Read surrounding code and resolve module-level constants from the same file and imported sibling modules.

Bind only values traceable to string literals. Treat function calls, runtime-variable f-strings, environment variables, user input, and runtime state as dynamic; flag them for manual handling or refactoring and do not auto-bind them. Do not infer values from third-party packages.

| SDK or pattern | Resource | Identifier and folder |
|---|---|---|
| `.assets.retrieve` / `.retrieve_async` | `asset` | First positional argument; `folder_path` |
| `.assets.retrieve_credential` / `.retrieve_credential_async` | `asset` | First positional argument; `folder_path`; `SubType: "credentialAsset"` when permitted |
| `.queues.create_item`, `.create_item_async`, `.create_items`, `.create_items_async`, `.create_transaction_item`, `.create_transaction_item_async` | `queue` | `item["Name"]`, `QueueItem`/`TransactionItem(name=...)`, or direct `queue_name` for `create_items*`; folder from `FolderContext` or the default folder |
| `.processes.invoke` / `.invoke_async` | `process` | `name`; `folder_path` |
| `.buckets.*` | `bucket` | `name`; `folder_path` |
| `.tasks.create` / `.create_async` / `.retrieve` / `.retrieve_async` | `app` | `app_name`; `app_folder_path` |
| `.context_grounding.*` | `index` | `name` or `index_name`; `folder_path` |
| `.connections.retrieve` / `.retrieve_async` | `connection` | First positional connection key; no folder |
| `.mcp.retrieve` / `.retrieve_async` | `mcpServer` | `slug`; `folder_path` |
| `EscalateAction(...)` | `app` | `app_name`; `app_folder_path` |
| `interrupt(InvokeProcess(...))` | `process` | `name`; `process_folder_path` |
| `interrupt(CreateTask(...))` | `app` | `app_name`; `app_folder_path` |
| `interrupt(CreateEscalation(...))` | `app` | `app_name`; `app_folder_path` |
| `sdk.jobs.resume` / `resume_async` | `process` | `process_name`; applicable folder |
| `ContextGroundingVectorStore(index_name=..., folder_path=...)` | `index` | `index_name`; `folder_path` |

Guardrail and interrupt patterns produce the same bindings as their SDK equivalents. Scan `EscalateAction`, `InvokeProcess`, `CreateTask`, and `CreateEscalation`, including calls imported from `uipath.platform.common`; `InvokeProcess` uses `process_folder_path`, not `folder_path`.

#### SubType inference during scanning

Run the version check in **SubType Metadata → Version-detection rule** first. If `uipath < 2.10.58`, emit no `SubType`, including for `retrieve_credential*`. If `uipath >= 2.10.58`, always emit `"SubType": "credentialAsset"` for `retrieve_credential` and `retrieve_credential_async`; the method is definitive. For other calls, follow **SubType Metadata**: fetch metadata, filter by kind, disambiguate from code, ask the user when necessary, and omit `SubType` if skipped or non-interactive. Omitting it is safe; `uip codedagent push` still creates a virtual placeholder for supported kinds using only the base `kind`.

### Step 3: Compare with Existing Bindings

Compare scanned resources with `bindings.json` and identify missing entries, stale entries, and mismatched keys, names, or folders.

In non-interactive mode, add or update missing and mismatched entries automatically, report no-ops silently, and ask only before deleting stale entries or handling dynamic values. Deduplicate repeated references by unique resource key.

### Step 4: Resolve Entrypoint Bindings

A resource may contain one optional entrypoint field in `value`:

- Prefer `EntryPointUniqueId`, mapped from `uniqueId`.
- Use `EntryPointPath` only when `uniqueId` is unavailable, mapped from `filePath`.
- Use `{ "defaultValue": "...", "isExpression": false, "displayName": "<filePath>" }`; `displayName` is mandatory and must equal the entrypoint `filePath`.

Apply these rules:

1. With exactly one entrypoint, bind every resource automatically; do not ask.
2. With multiple entrypoints, ask once which entrypoint, or `None`, applies to each resource. Present all resources and all choices; omit the field for `None`.
3. With no `entry-points.json`, skip entrypoint binding.
4. Preserve existing `EntryPointUniqueId` or `EntryPointPath` unless its referenced entrypoint no longer exists; flag stale references.
5. Add only one of the two fields per resource.

### Step 5: Update bindings.json

Consult **bindings.json Reference** before creating or modifying entries. Then add missing code resources, update drifted values, and remove stale entries only after user confirmation; stale entries may be intentional. Apply Step 4 entrypoint rules.

Every entry has `resource`, `key`, `value`, and `metadata`; `version` is always `"2.0"`. For non-connections, `key` is `<name>.<folder_path>`, or `<name>` when the folder is empty. Connections use only the connection key, `ConnectionId` instead of `name`, no `folderPath`, and `ConnectionId.defaultValue` equal to the connection id. Calls without a folder use `folderPath.defaultValue: ""` and a key without a trailing dot.

Always use the `_async` method name in `metadata.ActivityName`, regardless of source sync or async form. Connections have no `ActivityName`. Apps use the app name as `DisplayLabel`; other types use `"FullName"`. `SubType` is optional and follows **SubType Metadata**. Entrypoint fields, when present, must have `displayName` equal to the entrypoint `filePath`.

### Step 6: Verify

After writing the file:

1. Read it back and validate well-formed JSON.
2. Confirm every static code resource has a matching binding.
3. Confirm no orphaned entries remain, except those the user chose to keep.
4. If entrypoint binding was applied, verify every `EntryPointUniqueId` or `EntryPointPath` references `entry-points.json` and has the correct `displayName`.

## Edge Cases

- Scan all `**/*.py` files, excluding `.venv/`, `__pycache__/`, and `.uipath/`; calls often occur in helper, utility, store, or tool modules.
- Resolve module-level constants, including constants imported from sibling modules.
- Bind one entry per unique resource name and folder.
- `bucket` and `index` bindings cover all SDK methods, not only retrieval.
- Queue names are nested in `item["Name"]`, `QueueItem`/`TransactionItem(name=...)`, or the direct `queue_name` parameter of `create_items*`.
- `sdk.jobs.resume(process_name=...)` produces a `process` binding.
- `interrupt(WaitJob(job=...))` and `interrupt(WaitTask(action=...))` provide no static names and create no binding; bind the call that originally created the process or task handle.

## Troubleshooting

| Error | Cause | Solution |
|---|---|---|
| Invalid JSON in `bindings.json` | Manual-edit error or merge conflict | Read the file, fix syntax, and re-validate |
| Dynamic value cannot be auto-bound | Name or folder is runtime-derived | Refactor to literals or add the binding manually |
| Duplicate key in `resources` | Same resource found through multiple paths | Deduplicate by unique key |
| Missing project root | No `pyproject.toml` or `uipath.json` | Verify the working directory is a UiPath agent project |
| Stale entries after refactor | Removed calls were not removed from bindings | Run the full sync workflow and confirm orphan removal |
| Wrong asset type as virtual resource | Missing `SubType` for `retrieve_credential*` | When supported by the installed version, add `"SubType": "credentialAsset"` and re-run `uip codedagent push` |
| Push warns `was not found` for `connection`/`mcpServer`/`index` | These kinds lack virtual-resource fallback | Create the resource in Integration Service or Orchestrator before running `uip codedagent push` |

## Additional Instructions

- Consult **bindings.json Reference**; never guess JSON structure.
- Confirm stale-entry deletion before removing entries.
- Read surrounding code whenever static versus dynamic status is uncertain.
- Always re-read and validate `bindings.json` before reporting success.

# bindings.json Reference

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

`resources: []` is valid when no overridable resources are used. Catalog types include `process`, `index`, `app`, `asset`, `bucket`, `mcpServer`, `queue`, `remoteA2aAgent`, `memorySpace`, `entity`, and `connection`; this reference covers SDK-produced coded-agent bindings.

## Binding Structures and Extraction Rules

Use this common shape for non-connection resources:

```json
{
  "resource": "<type>",
  "key": "<name>.<folder_path>",
  "value": {
    "name": { "defaultValue": "<name>", "isExpression": false, "displayName": "Name" },
    "folderPath": { "defaultValue": "<folder_path>", "isExpression": false, "displayName": "Folder Path" }
  },
  "metadata": {
    "ActivityName": "<async_method>",
    "BindingsVersion": "2.2",
    "DisplayLabel": "FullName"
  }
}
```

Omit the dot in the key when the folder is empty. Type-specific rules:

- **Asset**: `sdk.assets.retrieve*`; first positional `name` and `folder_path`. `retrieve_credential*` adds `"SubType": "credentialAsset"` only when version rules permit it. `sdk.assets.update()` creates no binding.
- **Queue**: `sdk.queues.create_item*`, `create_transaction_item*`, and `create_items*`; extract names from `item["Name"]`, `QueueItem`/`TransactionItem(name=...)`, or direct `queue_name` for `create_items*`; use applicable folder context; `ActivityName` is `create_item_async`.
- **Process**: `sdk.processes.invoke*` extracts `name` and `folder_path`; `sdk.jobs.resume*` uses `process_name`; both use `ActivityName: "invoke_async"`.
- **Bucket**: every `sdk.buckets.*` method participates; extract `name` and `folder_path`; `ActivityName` is `retrieve_async`.
- **App**: `sdk.tasks.create*` or `retrieve*`, `EscalateAction(...)`, and `interrupt(CreateTask(...))`/`interrupt(CreateEscalation(...))`; extract `app_name` and `app_folder_path`; `ActivityName` is `create_async`; `DisplayLabel` is the literal app name.
- **Index**: every `sdk.context_grounding.*` method participates; extract `name` or `index_name` and `folder_path`; `ContextGroundingVectorStore(index_name=..., folder_path=...)` is equivalent; `ActivityName` is `retrieve_async`.
- **Connection**: `sdk.connections.retrieve*`; first positional argument is the key; use no `ActivityName` or folder:

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

- **MCP server**: `sdk.mcp.retrieve*`; extract `slug` and `folder_path`; use `name.defaultValue` for the slug and `ActivityName: "retrieve_async"`.

For `InvokeProcess`, use `process_folder_path` and otherwise produce the same process binding as `sdk.processes.invoke`. For `EscalateAction`, `CreateTask`, and `CreateEscalation`, use the same app binding as `sdk.tasks.create`. These patterns are described in [process-invocation.md](../capabilities/process-invocation.md) and [human-in-the-loop.md](../capabilities/human-in-the-loop.md).

## SubType Metadata

`SubType` is optional and must never be guessed. It enables correct virtual-resource creation when a catalog resource is absent.

### Version-detection rule

Read the resolved `uipath` version from `pyproject.toml`, `requirements.txt`, or `uv.lock`.

- If `uipath >= 2.10.58`, perform the lookup procedure below.
- If `uipath < 2.10.58`, or the version is unspecified/unresolvable, ask:

`⚠️ uipath is pinned to <version>. SubType support requires uipath >= 2.10.58 — without it every binding will be written with no SubType. Do you want to upgrade?`

Option A — Yes, upgrade `uipath`: print the command and stop; do not execute it. Tell the user to re-run this task after upgrading:

```bash
uv add 'uipath>=2.10.58'      # uv-managed projects (default)
# Poetry: poetry add 'uipath@^2.10.58'
# pip:    pip install --upgrade 'uipath>=2.10.58'
```

Option B — No, continue: omit `SubType` from every binding, including credential assets, and tell the user once: `"uipath" is pinned to "<version>"; SubType emission is disabled.`

### Authoritative metadata and lookup

Use the live endpoint when authenticated:

`GET https://<BASE_URL>/<ORG_ID>/studio_/backend/api/resourcebuilder/metadata`

If it fails for any reason, read `assets/solutions/metadata.json` relative to the skill root. The live response is an array; the snapshot has an `entries` array and `_snapshotDate`. Consume only `{kind, type}`. `kind` maps to `resource`; non-null `type` values are valid `SubType` values.

For each binding:

1. Fetch live metadata, then fall back to the snapshot on network, authentication, or non-200 failure.
2. Filter entries where `kind` equals the binding `resource`.
3. Collect unique non-null `type` values.
4. Emit no `SubType` if there are no candidates.
5. Emit the sole candidate if there is one.
6. With multiple candidates, apply code disambiguation; otherwise ask with every candidate and a final `skip`. `skip` or non-interactive mode omits `SubType`.

For plain-text prompts, list one candidate per line as `N. ` and make the final line `N. skip`; require a number, not a type name. Batch prompts when possible. Preserve an existing `SubType` unless its resource no longer exists in code; do not re-prompt for an existing value.

### Code disambiguation

Apply these rules in order:

| Code evidence | SubType or action |
|---|---|
| `retrieve_credential` or `retrieve_credential_async` | `credentialAsset` (high confidence) |
| Asset result annotated or clearly used as `str` | `stringAsset`; confirm if only medium confidence |
| Asset result annotated or used as `int` | `integerAsset`; confirm if only medium confidence |
| Asset result annotated or used as `bool` | `booleanAsset`; confirm if only medium confidence |
| Variable/context suggests password, API key, credential, secret, token, or `pwd` | Ask the user to choose `credentialAsset` or `secretAsset` |

For ordinary `retrieve*`, inspect assignment annotations and downstream use: string concatenation/formatting suggests `stringAsset`; arithmetic suggests `integerAsset`; boolean checks may suggest `booleanAsset`. If inconclusive, ask with the best guess highlighted.

### Refreshing the bundled snapshot

Run this command from an authenticated tenant when refreshing `assets/solutions/metadata.json`:

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

## Entrypoint Binding Reference

`entry-points.json` contains `entryPoints` with `uniqueId` and `filePath`. Add an optional `EntryPointUniqueId` or `EntryPointPath` object inside `value`, alongside `name`, `folderPath`, or `ConnectionId`:

```json
"EntryPointUniqueId": {
  "defaultValue": "<uniqueId>",
  "isExpression": false,
  "displayName": "<filePath>"
}
```

Use `EntryPointPath` with `filePath` as `defaultValue` only when `uniqueId` is unavailable. Add only one field. `displayName` must equal `filePath`. Omit both when unbound. Apply the single-entrypoint, multiple-entrypoint, missing-file, and stale-reference rules from Step 4.

## SDK Variable Names and Unsupported Services

Search patterns regardless of SDK variable name. These do not create bindings: `sdk.llm.*`, `sdk.llm_openai.*`, `sdk.documents.*`, `sdk.entities.*`, `sdk.guardrails.*`, `sdk.attachments.*`, `sdk.agenthub.*`, `sdk.folders.*`, and `sdk.resource_catalog.*`. Documents may use bucket bindings through `storage_bucket_name`. `sdk.assets.update()` is excluded.

## Dynamic Values vs Resolvable Constants

Resolve module-scope constants and same-project sibling-module imports before flagging values. Bind constants tracing to string literals. Flag function returns, runtime-variable f-strings, environment variables, and user input. Search the same file first, then sibling imports; do not infer values from third-party packages.

## What `uip codedagent push` Does with Bindings

`uip codedagent push` uploads source and, unless `--ignore-resources`, resolves each binding against the Resource Catalog. Most kinds match by `name` plus `folderPath`; connections match by `ConnectionId`. A wrong folder causes a miss.

- Found: import as a reference.
- Missing virtual-capable kind: create a placeholder and allow deployment.
- Missing non-virtual kind (`connection`, `mcpServer`, `index`): warn and skip the binding entirely.

A `was not found` warning is never expected. Diagnose wrong folder, wrong name/`ConnectionId`, or a genuinely missing resource; fix the binding or have the user create the resource, then re-run `uip codedagent push` and confirm the warning is gone. If unresolved, state plainly that the resource was not imported and cannot be overridden in Studio Web; do not report push as successful.

## Virtual Resource Fallback on uip codedagent push

Starting with `uipath` 2.10.52, push creates virtual placeholders for missing supported kinds. The live supported-kinds list comes from `/studio_/backend/api/resourcebuilder/metadata`; the static fallback is `app, asset, bucket, process, queue, taskCatalog, trigger`.

| Behavior | Kinds |
|---|---|
| Creates a placeholder using `SubType` when available | `app`, `asset`, `bucket`, `process`, `queue`, `taskCatalog`, `trigger` (static fallback; live metadata may add more) |
| Warns and skips; must exist in Integration Service | `connection` |
| Warns and skips; must exist in Orchestrator | `mcpServer`, `index`, and kinds absent from the supported list |

Therefore:

1. Emit `SubType` only for `uipath >= 2.10.58`; always emit `credentialAsset` for `retrieve_credential*` when permitted.
2. Warn that `connection`, `mcpServer`, and `index` resources must exist before push.
3. Bucket storage type is not inferable; when version support permits, ask whether it is `orchestratorBucket`, `amazonBucket`, or `azureBucket`.
4. Other `SubType` candidates by kind (prompt a numbered list when ambiguous): app (`sdk.tasks.*`) → `Coded`/`CodedAction`; mcpServer → `Coded`/`Command`/`Remote`/`UiPath`; process (`sdk.processes.invoke`/`sdk.jobs.resume`) → `process`/`agent`/`flow`/`api`/`caseManagement`/`processOrchestration`/`testAutomationProcess`/`webApp`/`mcpServer`.

## Complete SDK Mapping

| SDK property/pattern | Methods | Resource | Identifier | ActivityName |
|---|---|---|---|---|
| `sdk.assets` | `retrieve`, `retrieve_async` | `asset` | first positional `name` | `retrieve_async` |
| `sdk.assets` | `retrieve_credential`, `retrieve_credential_async` | `asset` | first positional `name` | `retrieve_async` |
| `sdk.queues` | `create_item*`, `create_items*`, `create_transaction_item*` | `queue` | nested name or `queue_name` | `create_item_async` |
| `sdk.processes` | `invoke`, `invoke_async` | `process` | `name` | `invoke_async` |
| `sdk.jobs` | `resume`, `resume_async` | `process` | `process_name` | `invoke_async` |
| `sdk.buckets` | all methods | `bucket` | `name` | `retrieve_async` |
| `sdk.tasks` | `create*`, `retrieve*` | `app` | `app_name` | `create_async` |
| `sdk.context_grounding` | all methods | `index` | `name` or `index_name` | `retrieve_async` |
| `sdk.connections` | `retrieve`, `retrieve_async` | `connection` | first positional key | none |
| `sdk.mcp` | `retrieve`, `retrieve_async` | `mcpServer` | `slug` | `retrieve_async` |
| `InvokeProcess` via `interrupt` | LangGraph HITL | `process` | `name`, folder from `process_folder_path` | `invoke_async` |
| `CreateTask` via `interrupt` | LangGraph HITL | `app` | `app_name` | `create_async` |
| `CreateEscalation` via `interrupt` | LangGraph HITL | `app` | `app_name` | `create_async` |
| `EscalateAction` | guardrail HITL | `app` | `app_name` | `create_async` |

Always use the `_async` variant in `ActivityName`, regardless of source call form. Bucket and context-grounding methods all participate in overrides, but repeated calls to one name/folder produce one entry.
