# Index Context (Context Grounding RAG)

Walkthrough for adding a context resource backed by an ECS Context Grounding index. Used for RAG (retrieval-augmented generation) — the agent issues queries against the index and gets back relevant chunks.

For other context variants, see [context.md](context.md).

## When to Use

- Agent needs to retrieve from a knowledge base of indexed documents
- The index already exists in Context Grounding and is backed by an Orchestrator storage bucket. To create or manage that index from the CLI, see [uipath-platform/references/context-grounding/index-management.md](../../../../../uipath-platform/references/context-grounding/index-management.md)

`uip solution resources refresh` emits an `index` binding into `bindings_v2.json`, resolves the backing storage bucket via ECS + Orchestrator, and writes all three artifacts automatically: `resources/solution_folder/index/<IndexName>.json`, `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json`, and two `debug_overwrites.json` entries (`kind: "index"`, `kind: "bucket"`). No manual solution-level authoring is required.

**Only `contextType: "index"` with a StorageBucket data source is supported.** `attachments` and `datafabricentityset` contexts, and indexes backed by GoogleDrive / OneDrive / Dropbox / Confluence, emit a warning from refresh and must be hand-authored.

## Discovery

Two `uip` calls — identity from `resource list`, full configuration from `resource get`. Symmetric with [../process/process.md § Discovery](../process/process.md#discovery).

### Step 1 — Verify login and scaffold (if not already done)

Run `uip login status --output json`. If a solution and agent do not yet exist, scaffold per [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Find the index (identity)

```bash
uip solution resources list --kind Index --source remote --search "<INDEX_NAME>" --output json
```

Response wrapper: `{Result, Code: "ResourceList", Data: [...]}` — parse `.Data[]`.

| Field | Use as |
|-------|--------|
| `Key` | index GUID — pass to `resource get` in Step 3. Not stored in the agent resource. |
| `Name` | exact `indexName` to set in the context resource → also propagates as binding `name` |
| `Folder` | literal folder path → top-level `folderPath` (e.g., `"Shared/Knowledge"`) and binding `folderPath`. Refresh uses `(name, folderPath)` jointly to look up the index in ECS. |
| `FolderKey` | folder GUID. Refresh resolves it from `Folder`; informational here. |

When the same `Name` repeats across folders, pick by `Key`.

### Step 3 — Get the index configuration

```bash
uip solution resources get <KEY> --output json
```

Response wrapper: `{Result, Code: "ResourceConfiguration", Data: {...}}`. `Data.spec` is the source-of-truth that `uip solution resources refresh` round-trips into `resources/solution_folder/index/<IndexName>.json` — confirm it before authoring.

| `Data.spec` field | Confirms / Use as |
|-------|------------------|
| `dataSourceType` | MUST equal `"StorageBucket"`. Anything else (GoogleDrive / OneDrive / Dropbox / Confluence / Attachments) — refresh warns + skips. Hand-author solution-level files or escalate. |
| `storageBucketReference.name` | Bucket display name. Refresh writes this as the bucket manifest's `name`. Optionally cross-check with `uip solution resources list --kind Bucket --source remote --search "<NAME>" --output json` to confirm the bucket is reachable. |
| `storageBucketReference.key` | Bucket GUID — refresh writes this verbatim as `key` in the bucket manifest and as `dependencies[].key` / `spec.storageBucketReference.key` in the index manifest. |
| `storageBucketReference.folderKey` | Folder GUID containing the bucket. Matches the index's `FolderKey` from Step 2 (the bucket lives in the same folder as the index). |
| `fileNameGlob` | File-extension filter on the index itself. Sanity-check — does not need to match the agent resource's `settings.fileExtension.value`. |
| `includeSubfolders`, `ingestionType`, `encrypted` | Reference fields — refresh round-trips them into the solution-level index manifest. |

Wrapper-level `apiVersion` is `"ecs.uipath.com/v2"` — matches what refresh writes.

## Agent-Level Resource Shape

**Path:** `<AgentName>/resources/<ContextName>/resource.json`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",                       // stable; generate once
  "referenceKey": null,                 // leave null; refresh resolves the ECS index GUID by indexName
  "name": "<ContextName>",              // display name; matches the folder under resources/
  "description": "",
  "contextType": "index",
  "folderPath": "Shared/Knowledge",     // Literal Folder from `uip solution resources list`. Propagates verbatim into bindings_v2.json.
  "indexName": "<IndexName>",           // MUST match the ECS index Name exactly (case-sensitive)
  "settings": {
    "retrievalMode": "semantic",        // "semantic" | "structured" | "deeprag" | "batchtransform"
    "query": { "variant": "dynamic", "description": "Query for retrieval" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },  // object, not string
    "threshold": 0,
    "resultCount": 3
  }
}
```

**`retrievalMode` values (all lowercase) and per-mode `fileExtension.value` + extra fields:**

| `retrievalMode` | Legal `fileExtension.value` | Extra required fields |
|---|---|---|
| `"semantic"` | `"All"`, `"pdf"`, `"csv"`, `"json"`, `"docx"`, `"xlsx"`, `"txt"` | none |
| `"structured"` | `"csv"` | none |
| `"deeprag"` | `"pdf"`, `"txt"` | `"citationMode": { "value": "Inline" }` (or `"Skip"`) |
| `"batchtransform"` | `"csv"` | `"webSearchGrounding": { "value": "Enabled" }` (or `"Disabled"`), `"outputColumns": [{ "name": "...", "description": "..." }, ...]` |

**`query.variant`:** `"dynamic"` (LLM supplies at runtime), `"argument"` (bound to an input field), or `"static"` (pre-set value).

**`folderPathPrefix.variant`:** `"static"` (no prefix) or `"argument"` (scope by a folder path provided at runtime).

**Casing matters.** All `contextType` and `retrievalMode` values are lowercase. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.

## Solution-Level Files

For `contextType: "index"` with a StorageBucket-backed ECS index, `uip agent refresh` emits:

```json
{
  "resource": "index",
  "key": "<IndexName>",
  "value": {
    "name":       { "defaultValue": "<IndexName>", "isExpression": false, "displayName": "Index Name" },
    "folderPath": { "defaultValue": "<Folder>",    "isExpression": false }
  },
  "metadata": { "bindingsVersion": "2.2", "solutionsSupport": "true" }
}
```

into `bindings_v2.json` at the agent project root. `folderPath` is propagated verbatim from the agent-level `resource.json`'s top-level `folderPath` field. `uip solution resources refresh` then:

1. Calls ECS `GET ecs_/v2/indexes/AllAcrossFolders?$filter=Name eq '<IndexName>'&$expand=dataSource` — resolves the index GUID, folder key, and data source type. With the binding's `folderPath` set, refresh narrows multi-folder name collisions to the exact deployment.
2. If `dataSource.@odata.type` is not `#UiPath.Vdbs.Domain.Api.V20Models.StorageBucketDataSource`, warns + skips (other data sources — GoogleDrive, OneDrive, Dropbox, Confluence, Attachments — are not yet wired).
3. Calls Orchestrator `GET orchestrator_/odata/Buckets?$filter=Name eq '<BucketName>'` with the index's `folderKey` as `X-UIPATH-FolderKey` — gets the bucket `Identifier` GUID.
4. Registers the bucket as a solution resource via the resource-builder SDK — writes `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json`.
5. Hand-writes `resources/solution_folder/index/<IndexName>.json` with `kind: "index"`, `apiVersion: "ecs.uipath.com/v2"`, `dependencies: [{name: "<BucketName>", kind: "bucket"}]`, `spec.storageBucketReference: { name, key }`, `dataSourceType: "StorageBucket"`.
6. Appends two entries (`kind: "index"` + `kind: "bucket"`) to `userProfile/<userId>/debug_overwrites.json`.

All failures (index not found, ambiguous name match, non-StorageBucket data source, bucket missing in Orchestrator) warn + continue — the command never aborts.

### Index Definition (refresh fallback)

**Path:** `resources/solution_folder/index/{IndexName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "MyIndex",
    "kind": "index",
    "apiVersion": "ecs.uipath.com/v2",
    "isOverridable": true,
    "dependencies": [
      {
        "name": "my_storage_bucket",
        "kind": "bucket",
        "key": "<bucket-resource-uuid>"
      }
    ],
    "spec": {
      "name": "MyIndex",
      "description": "",
      "storageBucketReference": {
        "name": "my_storage_bucket",
        "key": "<bucket-resource-uuid>"
      },
      "fileNameGlob": "All",
      "dataSourceType": "StorageBucket",
      "includeSubfolders": true,
      "ingestionType": "Advanced"
    },
    "key": "<unique-uuid>"
  }
}
```

### Storage Bucket Definition (refresh fallback)

**Path:** `resources/solution_folder/bucket/orchestratorBucket/{BucketName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "my_storage_bucket",
    "kind": "bucket",
    "type": "orchestratorBucket",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "spec": {
      "type": "Orchestrator",
      "description": null,
      "tags": []
    },
    "key": "<unique-uuid>"
  }
}
```

## Walkthrough

### Step 4 — Create the agent-level context resource

**Path:** `<AgentName>/resources/<ContextName>/resource.json`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",                       // generate a fresh UUID
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "index",
  "folderPath": "<FOLDER>",             // literal Folder from Step 2 (e.g., "Shared/Knowledge")
  "indexName": "<INDEX_NAME>",          // exact ECS index name from Step 2
  "settings": {
    "retrievalMode": "semantic",
    "query": { "variant": "dynamic" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },
    "threshold": 0,
    "resultCount": 3
  }
}
```

See § Agent-Level Resource Shape above for the full field reference, including the three variants (`index`/`attachments`/`datafabricentityset`) and per-`retrievalMode` settings (`citationMode` for `deeprag`, `webSearchGrounding` + `outputColumns` for `batchtransform`).

### Step 4b — Inline agents only: wire the context flow node

**Skip if the agent is standalone.** If the context is on an **inline** agent (embedded in a flow), the `resource.json` alone is never reached at runtime — you MUST also add a `uipath.agent.resource.context.index.<index-name>.<index-id>` flow node connected to the autonomous node's `context` handle (bottom port). Fetch its manifest with `uip maestro flow registry get "<NodeType>" --output json`, then hand the node + edge authoring to the `uipath-maestro-flow` skill (Critical Rule 16 — this skill does not author `.flow` graphs directly). Run Step 5's refresh/validate with `--inline-in-flow` plus `--bindings-target <FlowProjectDir>/bindings_v2.json`. See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).

### Step 5 — Refresh and validate

```bash
uip agent refresh  "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Refresh writes the binding. Validate is read-only. Confirm `Validated.resources` includes the context, then inspect the emitted binding:

```bash
cat "<AGENT_NAME>/bindings_v2.json"
# Expect: resources[0] with {resource: "index", key: "<INDEX_NAME>", ...}
```

### Step 6 — Refresh solution resources

```bash
uip solution resources refresh --output json
```

Refresh resolves the index via ECS `$expand=dataSource`, locates its backing StorageBucket in Orchestrator, and writes:

- `resources/solution_folder/index/<INDEX_NAME>.json` — manifest with `kind: "index"`, `apiVersion: "ecs.uipath.com/v2"`, `dependencies: [{name, kind: "bucket"}]`, `spec.storageBucketReference.{name,key}`.
- `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json` — standard bucket manifest.
- `userProfile/<userId>/debug_overwrites.json` — two entries (`kind: "index"` and `kind: "bucket"`), both referencing the index's folder.

Check the `Warnings` array in the refresh output. Common warnings:
- `Index "<NAME>" not found in ECS` — exact-name mismatch. Re-check the index name.
- `Index uses <type>, which is not yet supported` — data source is GoogleDrive/OneDrive/Dropbox/Confluence/Attachments; hand-author the solution-level files. Step 3's `dataSourceType` check should have caught this earlier.
- `Storage bucket "<NAME>" not found in Orchestrator folder` — the bucket was deleted or lives in a different folder than the index.

### Step 7 — Bundle and upload

```bash
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

The upload response includes a `Data.DesignerUrl` — open it to verify the context appears wired to the ECS index in Studio Web.

## Gotchas

`contextType` and `retrievalMode` values MUST be lowercase — see [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.

## References

- [context.md](context.md) — capability overview and variant decision
- [attachments.md](attachments.md) — runtime file attachments
- [datafabric.md](datafabric.md) — DataFabric entity-set context
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics
