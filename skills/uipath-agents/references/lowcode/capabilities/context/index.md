# Index Context (Context Grounding RAG)

Walkthrough for adding a context resource backed by an ECS Context Grounding index for retrieval-augmented generation (RAG). For other variants, see [context.md](context.md).

## When to Use

Use this skill when an agent retrieves from an indexed knowledge base. The index must already exist in Context Grounding and be backed by an Orchestrator storage bucket. To create or manage the index from the CLI, see [uipath-platform/references/context-grounding/index-management.md](../../../../../uipath-platform/references/context-grounding/index-management.md).

`uip solution resources refresh` emits an `index` binding into `bindings_v2.json`, resolves the backing storage bucket through ECS and Orchestrator, and writes `resources/solution_folder/index/<IndexName>.json`, `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json`, and two `debug_overwrites.json` entries (`kind: "index"`, `kind: "bucket"`). Do not manually author solution-level resources for supported indexes.

Only `contextType: "index"` with a StorageBucket data source is supported. `attachments`, `datafabricentityset`, and indexes backed by GoogleDrive / OneDrive / Dropbox / Confluence emit a refresh warning and must be hand-authored.

## Discovery

Use two `uip` calls: identity from `resource list`, then configuration from `resource get`. This is symmetric with [../process/process.md § Discovery](../process/process.md#discovery).

### Step 1 — Verify login and scaffold (if not already done)

Run:

```bash
uip login status --output json
```

If the solution or agent does not exist, scaffold it per [../../project-lifecycle.md § End-to-End Example](../../project-lifecycle.md#end-to-end-example--new-standalone-agent).

### Step 2 — Find the index (identity)

Run:

```bash
uip solution resources list --kind Index --source remote --search "<INDEX_NAME>" --output json
```

Parse `.Data[]` from `{Result, Code: "ResourceList", Data: [...]}`:

| Field | Use |
|---|---|
| `Key` | Index GUID; pass it to `resource get` in Step 3. Do not store it in the agent resource. |
| `Name` | Exact, case-sensitive `indexName`; also becomes binding `name`. |
| `Folder` | Literal folder path; set top-level `folderPath` and binding `folderPath` (for example, `"Shared/Knowledge"`). Refresh uses `(name, folderPath)` jointly for ECS lookup. |
| `FolderKey` | Folder GUID; refresh resolves it from `Folder`. |

When `Name` repeats across folders, select by `Key`.

### Step 3 — Get the index configuration

Run:

```bash
uip solution resources get <KEY> --output json
```

Use `Data.spec` from `{Result, Code: "ResourceConfiguration", Data: {...}}` as the source of truth; refresh round-trips it into `resources/solution_folder/index/<IndexName>.json`.

| `Data.spec` field | Confirm / use |
|---|---|
| `dataSourceType` | Must equal `"StorageBucket"`. GoogleDrive / OneDrive / Dropbox / Confluence / Attachments require hand-authored solution-level files or escalation; refresh warns and skips them. |
| `storageBucketReference.name` | Bucket display name and bucket-manifest `name`. Optionally cross-check with `uip solution resources list --kind Bucket --source remote --search "<NAME>" --output json`. |
| `storageBucketReference.key` | Bucket GUID; refresh writes it verbatim to the bucket manifest and to `dependencies[].key` and `spec.storageBucketReference.key` in the index manifest. |
| `storageBucketReference.folderKey` | Bucket folder GUID; it matches the index `FolderKey`. |
| `fileNameGlob` | Index file-extension filter; sanity-check it, but it need not match `settings.fileExtension.value`. |
| `includeSubfolders`, `ingestionType`, `encrypted` | Reference fields round-tripped into the solution-level index manifest. |

The wrapper-level `apiVersion` is `"ecs.uipath.com/v2"`.

## Agent-Level Resource Shape

Path: `<AgentName>/resources/<ContextName>/resource.json`

```jsonc
{
  "$resourceType": "context",
  "id": "<uuid>",
  "referenceKey": null,
  "name": "<ContextName>",
  "description": "",
  "contextType": "index",
  "folderPath": "Shared/Knowledge",
  "indexName": "<IndexName>",
  "settings": {
    "retrievalMode": "semantic",
    "query": { "variant": "dynamic", "description": "Query for retrieval" },
    "folderPathPrefix": { "variant": "static" },
    "fileExtension": { "value": "All" },
    "threshold": 0,
    "resultCount": 3
  }
}
```

Generate `id` once and keep it stable. Leave `referenceKey` null; refresh resolves the ECS index GUID by `indexName`. `name` is the display name and resource-folder name. `folderPath` is the literal `Folder` from Step 2 and propagates verbatim to `bindings_v2.json`. `indexName` must exactly match the ECS index `Name`.

`retrievalMode` values are lowercase and constrain `fileExtension.value` and extra fields:

| `retrievalMode` | Legal `fileExtension.value` | Extra required fields |
|---|---|---|
| `"semantic"` | `"All"`, `"pdf"`, `"csv"`, `"json"`, `"docx"`, `"xlsx"`, `"txt"` | none |
| `"structured"` | `"csv"` | none |
| `"deeprag"` | `"pdf"`, `"txt"` | `"citationMode": { "value": "Inline" }` or `"Skip"` |
| `"batchtransform"` | `"csv"` | `"webSearchGrounding": { "value": "Enabled" }` or `"Disabled"`; `"outputColumns": [{ "name": "...", "description": "..." }, ...]` |

`query.variant` may be `"dynamic"` (LLM supplies it), `"argument"` (bound to an input field), or `"static"` (preset). `folderPathPrefix.variant` may be `"static"` (no prefix) or `"argument"` (runtime folder path). `fileExtension` is an object, not a string. Casing matters: `contextType` and `retrievalMode` are lowercase. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.

## Solution-Level Files

For `contextType: "index"` with a StorageBucket-backed ECS index, `uip agent refresh` emits this binding into the agent project root `bindings_v2.json`:

```json
{
  "resource": "index",
  "key": "<IndexName>",
  "value": {
    "name": { "defaultValue": "<IndexName>", "isExpression": false, "displayName": "Index Name" },
    "folderPath": { "defaultValue": "<Folder>", "isExpression": false }
  },
  "metadata": { "bindingsVersion": "2.2", "solutionsSupport": "true" }
}
```

`folderPath` comes verbatim from the agent resource. `uip solution resources refresh` then:

1. Calls ECS `GET ecs_/v2/indexes/AllAcrossFolders?$filter=Name eq '<IndexName>'&$expand=dataSource` to resolve the index GUID, folder key, and data source. Binding `folderPath` narrows duplicate names to the deployment folder.
2. Warns and skips when `dataSource.@odata.type` is not `#UiPath.Vdbs.Domain.Api.V20Models.StorageBucketDataSource`.
3. Calls Orchestrator `GET orchestrator_/odata/Buckets?$filter=Name eq '<BucketName>'` with the index `folderKey` as `X-UIPATH-FolderKey` to obtain the bucket `Identifier` GUID.
4. Registers the bucket and writes `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json`.
5. Writes `resources/solution_folder/index/<IndexName>.json` with `kind: "index"`, `apiVersion: "ecs.uipath.com/v2"`, `dependencies: [{name: "<BucketName>", kind: "bucket"}]`, `spec.storageBucketReference: { name, key }`, and `dataSourceType: "StorageBucket"`.
6. Appends `kind: "index"` and `kind: "bucket"` entries to `userProfile/<userId>/debug_overwrites.json`.

All failures—index not found, ambiguous name match, non-StorageBucket data source, or missing bucket—warn and continue; the command never aborts.

### Index Definition (refresh fallback)

Path: `resources/solution_folder/index/{IndexName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<IndexName>",
    "kind": "index",
    "apiVersion": "ecs.uipath.com/v2",
    "isOverridable": true,
    "dependencies": [
      { "name": "<BucketName>", "kind": "bucket", "key": "<bucket-resource-uuid>" }
    ],
    "spec": {
      "name": "<IndexName>",
      "description": "",
      "storageBucketReference": { "name": "<BucketName>", "key": "<bucket-resource-uuid>" },
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

Path: `resources/solution_folder/bucket/orchestratorBucket/{BucketName}.json`

```jsonc
{
  "docVersion": "1.0.0",
  "resource": {
    "name": "<BucketName>",
    "kind": "bucket",
    "type": "orchestratorBucket",
    "apiVersion": "orchestrator.uipath.com/v1",
    "isOverridable": true,
    "spec": { "type": "Orchestrator", "description": null, "tags": [] },
    "key": "<unique-uuid>"
  }
}
```

## Walkthrough

### Step 4 — Create the agent-level context resource

Create `<AgentName>/resources/<ContextName>/resource.json` using the schema above. At minimum, set `contextType` to `"index"`, `folderPath` to the literal Step 2 `Folder`, `indexName` to the exact Step 2 `Name`, `retrievalMode` to `"semantic"`, `query.variant` to `"dynamic"`, `folderPathPrefix.variant` to `"static"`, `fileExtension.value` to `"All"`, `threshold` to `0`, and `resultCount` to `3`. See **Agent-Level Resource Shape** for all variants and per-mode settings (`citationMode` for `deeprag`; `webSearchGrounding` and `outputColumns` for `batchtransform`).

### Step 4b — Inline agents only: wire the context flow node

Skip this step for standalone agents. For an **inline** agent embedded in a flow, `resource.json` alone is never reached at runtime. Add a `uipath.agent.resource.context.index.<index-name>.<index-id>` flow node connected to the autonomous node's `context` handle (bottom port). Fetch its manifest by running:

```bash
uip maestro flow registry get "<NodeType>" --output json
```

Delegate node and edge authoring to the `uipath-maestro-flow` skill (Critical Rule 16; this skill does not author `.flow` graphs). Run Step 5 with `--inline-in-flow` and `--bindings-target <FlowProjectDir>/bindings_v2.json`. See [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md).

### Step 5 — Refresh and validate

Run:

```bash
uip agent refresh  "<AGENT_NAME>" --output json
uip agent validate "<AGENT_NAME>" --output json
```

Confirm `Validated.resources` includes the context. Validation is read-only. Inspect the binding:

```bash
cat "<AGENT_NAME>/bindings_v2.json"
```

Expect `resources[0]` with `{resource: "index", key: "<INDEX_NAME>", ...}`.

### Step 6 — Refresh solution resources

Run:

```bash
uip solution resources refresh --output json
```

Confirm it writes:

- `resources/solution_folder/index/<INDEX_NAME>.json` with `kind: "index"`, `apiVersion: "ecs.uipath.com/v2"`, `dependencies: [{name, kind: "bucket"}]`, and `spec.storageBucketReference.{name,key}`.
- `resources/solution_folder/bucket/orchestratorBucket/<BucketName>.json`.
- `userProfile/<userId>/debug_overwrites.json` with `kind: "index"` and `kind: "bucket"` entries referencing the index folder.

Check the `Warnings` array. Common warnings are:

- `Index "<NAME>" not found in ECS` — exact-name mismatch; re-check `indexName`.
- `Index uses <type>, which is not yet supported` — GoogleDrive/OneDrive/Dropbox/Confluence/Attachments; hand-author solution-level files. Step 3 should detect this.
- `Storage bucket "<NAME>" not found in Orchestrator folder` — bucket deleted or in another folder.

### Step 7 — Bundle and upload

Run:

```bash
uip solution bundle . -d ./dist --output json
uip solution upload ./dist/<SOLUTION_NAME>.uis --output json
```

Open `Data.DesignerUrl` from the upload response and verify in Studio Web that the context is wired to the ECS index.

## Gotchas

`contextType` and `retrievalMode` values MUST be lowercase. See [../../critical-rules/critical-rules.md](../../critical-rules/critical-rules.md) Anti-pattern 12.

**Cap retrievals in the system prompt.** Without a call limit, the agent may re-query until runtime termination at `AGENT_RUNTIME.TERMINATION_MAX_ITERATIONS` (in a flow: node Failed, incident `170002`). Raising `settings.maxIterations` only moves the failure: 5 dies at 5 and 25 dies at 25. State a cap and fallback:

```text
Call <toolName> at most <N> times (N ≤ 3 for a single decision). After the last call, stop retrieving and decide with the evidence you already have.
If the retrieved content does not cover a detail, say so in <rationaleField>, lower <confidenceField>, and still return every outputSchema field. Never end a run without a determination.
```

## References

- [context.md](context.md) — capability overview and variant decision
- [attachments.md](attachments.md) — runtime file attachments
- [datafabric.md](datafabric.md) — DataFabric entity-set context
- [../../solution-resources.md](../../solution-resources.md) § Refresh Mechanics