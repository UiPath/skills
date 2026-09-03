# Connector Activity Discovery

<!--skill-flavor:connector-surface-summary:start-->
How to author an Integration Service connector activity (HTTP Request, Gmail, Outlook, GitHub, Slack, Salesforce, etc.) so it renders cleanly in StudioWeb's designer and runs from the CLI. Use `uip api-workflow registry` to resolve a keyword to an activity-type GUID, then generate a ready-to-paste activity with `metadata.configuration` (`unifiedTypesCompatible: true` and `savedJitInputFieldId`), the full endpoint path, multipart declarations, and stub-computed slot/export keys derived from TypeCache and Integration Service Elements metadata.
<!--skill-flavor:connector-surface-summary:end-->

<!--skill-flavor:host-command-scope:start-->
<!--skill-flavor:host-command-scope:end-->
<!--skill-flavor:registry-auth:start-->
> The `registry` subcommand ships with `@uipath/cli`'s api-workflow tool. No separate install. Both calls require `uip login` because TypeCache and IS Elements are tenant-scoped and served live.
<!--skill-flavor:registry-auth:end-->

## Why registry discovery is required

`uip is activities list <connector-key>` exposes runtime fields but not the `uiPathActivityTypeId` and `metadata.configuration` required for StudioWeb's activity card. Without both, StudioWeb shows a block/forbidden card and cloud execution can fail. `registry resolve` supplies the activity type; `registry stub` supplies the complete activity shape.

## Discovery flow

<!--skill-flavor:discovery-flow:start-->
1. Run `uip api-workflow registry resolve "<keyword>" --output json` and select the correct activity GUID.
2. For IntSvc activities, run `uip is connections list <connector-key>`, use the unfiltered and `--all-folders` fallbacks when necessary, and run `uip is connections ping <uuid>`. A successful ping is mandatory.
3. Run `uip api-workflow registry stub <activity-type-id> [--connection-id <uuid>] [--inputs '<json>'] --output json`; then run `uip is resources describe <connector-key> <object-name> --operation <op> --connection-id <uuid> --output json` to cross-check required fields.
4. Drop `Data.Activity` into the root sequence after `WorkflowStart`, fill missing required fields, replace every placeholder, and validate.
5. For Solutions-mode IntSvc workflows, synchronize the connection resource into the Solution catalogue.
<!--skill-flavor:discovery-flow:end-->

The stub re-fetches TypeCache and IS Elements metadata, chooses Http versus IntSvc by `connectorKey === "uipath-uipath-http"`, derives the full endpoint, builds essential `metadata.configuration`, computes `SlotKey` and `ExportBucketKey`, declares `multipartParameters`, and routes `--inputs` by schema location. Inputs use flat dotted field names, bare literals, and `${...}` only for actual expressions. Unknown input fields are silently dropped.

### Step 1 — Resolve the activity

```bash
uip api-workflow registry resolve "<keyword>" --output json
```

Search is server-side (`projectType=Api`) followed by whitespace-token AND matching against `displayName`, `description`, `connectorKey`, `objectName`, and `fullName`. Use `--limit <n>` when the default maximum of 50 is insufficient. `ActivityType: "Curated"` is directly stub-able; `ActivityType: "Generic"` also requires `--object-name` and exposes an `Operation` such as `List`, `Retrieve`, `Create`, `Update`, `Replace`, or `Delete`.

If no result appears, reduce to true distinctive tokens; do not infer absence. Recover connector-first:

1. Run `uip is connectors list --filter "<product words>" --output json` and read the exact `Key`; never guess a connector key.
2. Run `uip is activities list <connector-key> --output json` to enumerate that connector's activities. Conclude that the operation is unavailable only when this list confirms it.
3. Resolve and stub using the real activity noun rather than a marketing phrase.

When several connectors expose similar names, include the connector name in the query. Do not parallelize connection lookup with resolution because the exact connector key comes from `ConnectorKey`.

### Step 2 — Verify a vendor connection (IntSvc only)

Skip this step for `uipath-uipath-http`; HTTP uses `connectionId: "ImplicitConnection"` and needs no real connection. For every other connector, use the exact `ConnectorKey` from resolution.

```bash
uip is connections list <connector-key> --output json
uip is connections ping <connection-uuid> --output json
```

Choose an `Enabled` connection, preferring `IsDefault: "Yes"`. A successful ping has `Code: "ConnectionPing"`. Never author against a failed or unverified connection: `ConnectionNotEnabled` or a 404 is unusable and can cause a cloud 401.

If the filtered list is empty or its UUID fails, run both fallbacks:

```bash
uip is connections list --output json
uip is connections list --all-folders --output json
```

Search both results for the required `ConnectorKey`, try another UUID, and ping it. The unfiltered list can expose stale/orphaned records; `--all-folders` is required before concluding that no connection exists. It cannot be combined with `--folder` or `--folder-key`. Only after all three listings yield no UUID that pings successfully should you stop — see the connection-remediation note below.

<!--skill-flavor:connection-remediation:start-->
Only after the filtered, unfiltered, AND `--all-folders` listings have been exhausted (no UUID for that `ConnectorKey` pings cleanly) should you abort and tell the user to either re-authenticate (`uip is connections edit <connection-uuid>` opens a browser for OAuth) or create a fresh connection in the StudioWeb UI. **Do NOT author a workflow against a connection that hasn't pinged successfully** — it will 401 in cloud regardless of how correct the workflow JSON is.
<!--skill-flavor:connection-remediation:end-->

### Step 3 — Stub the activity

```bash
uip api-workflow registry stub <activity-type-id> \
  [--connection-id <uuid>] \
  [--inputs '<json>'] \
  [--instance <n>] \
  [--slot-key <PascalCase>] \
  [--object-name <object>] \
  [--resource-key '<field>=<key>'] \
  --output json
```

| Flag | Required/default | Purpose |
|---|---|---|
| `<activity-type-id>` | required | `uiPathActivityTypeId` from `resolve`. |
| `--connection-id <uuid>` | IntSvc only; optional | Pinged vendor UUID. Without it, IntSvc output contains placeholders; ignored for Http. |
| `--inputs <json>` | optional, default `{}` | Flat schema field names to values; bare strings are literals and `${...}` values are expressions. |
| `--instance <n>` | optional, default `1` | Suffixes slot/export keys, such as `_2`. |
| `--slot-key <PascalCase>` | optional | Overrides the slot key only; export key remains object-name-derived. |
| `--object-name <object>` | required for Generic unless pinned | Target object used with the activity's `Operation`. |
| `--resource-key '<field>=<key>'` | optional | Saves Solution-resource picker selection metadata. |

`Data.Activity` is the one-key object to insert into the root sequence. `Data.ExportBucketKey`, not `Data.SlotKey`, is the downstream `$context.outputs.<X>` key. `Data.ResponseFields` describes output fields under `.content` for IntSvc. Warnings may indicate unavailable IS metadata (fallback `/<objectName>`, no request fields) or a missing connection ID (replace placeholders or re-stub).

#### Required-field cross-check

After every stub, inspect `metadata.configuration` → `optionalConfiguration.fieldsContainer.inputFields`, including `name`, `required`, `fieldLocation`, and `defaultValue`, or run:

```bash
uip is resources describe <connector-key> <object-name> \
  --operation <op> --connection-id <uuid> --output json
```

The first describe call without `--operation` lists available operations. For every `required: true` field, verify a value exists in the matching `queryParameters`, `pathParameters`, or `bodyParameters` block. Re-run the stub with `--inputs` or add the missing flat, bare-literal field manually. Empty parameter blocks on a non-trivial CRUD operation are suspicious. Do not complete the workflow until `Data.Warnings` contains no missing-required-field warning.

<!--skill-flavor:resource-lookup-runtime:start-->
Well-known folder-name shortcuts (e.g. MS Graph's `"inbox"`, `"sentitems"`, `"drafts"`) work for `parentFolderId`-style fields at runtime, but the StudioWeb FolderPicker displays the friendly name only when the value matches a real folder ID from the lookup cache. For exact UI fidelity, fetch the real ID once by running `uip is resources run list <connector-key> <object-name> --connection-id <uuid>` against the `lookup.path` (e.g. `/MailFolders`).
<!--skill-flavor:resource-lookup-runtime:end-->

### Step 4 — Insert, replace placeholders, and validate

Insert `Data.Activity` after `WorkflowStart`. Replace every placeholder before writing the workflow:

- `<REPLACE_WITH_TARGET_URL>` in Http `bodyParameters.url`: use the target URL as a literal or `${$workflow.input.url}`.
- `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` in IntSvc `with.connectionId` and `with.connectionResourceId`: use the successfully pinged UUID, preferably by re-running with `--connection-id`.

<!--skill-flavor:required-field-cloud-validation:start-->
Before validating, run the **Required-field cross-check** above — if any `required: true` field is missing from `queryParameters` / `pathParameters` / `bodyParameters`, the workflow will run locally but fail in cloud (or worse — the StudioWeb FolderPicker / lookup picker will mark the field as invalid without a clear error).
<!--skill-flavor:required-field-cloud-validation:end-->

<!--skill-flavor:validate-and-run:start-->
Then validate by running:

```bash
uip api-workflow run ./my-workflow.json --output json
```

Do not use `--no-auth` for IntSvc. It requires `uip login`; `--no-auth` is valid for a public Http activity using `ImplicitConnection`.
<!--skill-flavor:validate-and-run:end-->

<!--skill-flavor:solution-metadata:start-->
### Step 5 — Solutions-mode IntSvc connection synchronization

Skip this step for Http (`call: "UiPath.Http"`, connector `uipath-uipath-http`), activities without connections, and standalone projects with top-level `project.json` and no `Solution/` wrapper.

For a Solution layout (`Solution/<ProjectName>/Workflow.json`), every vendor connection must exist in the Solution catalogue and per-user debug overwrites. Run:

```bash
uip api-workflow bindings sync --workflow Solution/<ProjectName>/Workflow.json --output json
uip solution resources refresh --solution-folder Solution --output json
```

`bindings sync` emits `bindings_v2.json`, derives one connection binding per UUID, and preserves existing solution-resource bindings when IS is unreachable. `solution resources refresh` reads project bindings, writes catalogue resources and `Solution/userProfile/<guid>/debug_overwrites.json`, requires `uip login`, and is idempotent.

If offline hand-authoring is unavoidable, write `Solution/resources/solution_folder/connection/<connector-key>/<connection-name>.json`, starting from [assets/templates/solution-connection-resource-template.json](../assets/templates/solution-connection-resource-template.json). Use the exact connection `Name`, `ConnectorKey`, `ConnectorName`, connector version from `essentialConfiguration.connectorVersion` (or `"1.0.0"` if unparseable), pinged UUID as `resource.key`, and the existing resource folder's `folders[0].fullyQualifiedName` (default `"solution_folder"`). The key must equal both workflow connection IDs and the binding key. Write one file per unique UUID. Do not hand-author `bindings_v2.json` or debug overwrites when the CLI commands are available.
<!--skill-flavor:solution-metadata:end-->
<!--skill-flavor:worked-example-solution-metadata:start-->
<!--skill-flavor:worked-example-solution-metadata:end-->

## Http versus IntSvc

| Connector key | Kind/call | Connection | Endpoint |
|---|---|---|---|
| `uipath-uipath-http` | Http / `UiPath.Http` | `ImplicitConnection` | `/http-request` |
| Any vendor key | IntSvc / `UiPath.IntSvc` | Pinged UUID | Full IS Elements path |

Never use Http kind with a vendor UUID, the simple `call: "http"` form, or a vendor URL in place of the IS endpoint. The HTTP-passthrough variant with `bodyParameters.targetConnector` is not generally available and requires a specially authorized HTTP connection.

### Http kind

`with.method` is always `POST`; `with.endpoint` is always `/http-request`. Put the actual request in `bodyParameters`: `authentication` (`"manual"` or `"connector"`), actual `method`, `url`, `headers`, `body`, and other inputs. Output is an envelope; use `Data.ExportBucketKey`, then `.content`, `.statusCode`, `.headers`, etc.

### IntSvc kind

Use the vendor key, pinged UUID in both connection fields, IS method, full IS endpoint, and schema-derived `queryParameters`, `pathParameters`, `bodyParameters`, and optional `multipartParameters`. Do not supply a vendor API URL; the connector and IS proxy perform that routing.

### Generic activities

Run:

```bash
uip is resources list <connector-key> --connection-id <uuid> --output json
uip is resources describe <connector-key> <object-name> --connection-id <uuid> --operation <Op> --output json
uip api-workflow registry stub <activity-type-id> --object-name <object-name> --connection-id <uuid> --output json
```

Generic activities require `--object-name` unless the definition pins one, and require IS metadata to resolve verb and path; unlike Curated activities they hard-fail when metadata is unavailable or the object lacks the operation. Operation casing is normalized to lowercase in `metadata.configuration`. Prefer Curated activities because Generic operations are auto-generated and less thoroughly verified. Inspect describe metadata for path-parameter formats; on a 404, cross-check with the path-parameter diagnostic below, then fall back to a Curated activity or Http kind.

<!--skill-flavor:export-bucket-stability:start-->
- **Slot key carries the operation; export bucket does not**: slot `ListUserRepos_1`, export bucket `user_repos_1` (objectName-based, like every Curated example). The bucket intentionally matches the platform's own derivation — solution reconcile (`resource refresh`) regenerates `Workflow.json` and recomputes export buckets from the object name, so a divergent bucket would be renamed on regeneration. As always, copy `Data.ExportBucketKey` verbatim; and after ANY external rewrite of `Workflow.json` (reconcile, designer save), re-check that downstream `$context.outputs.<X>` reads still match the on-disk `export.as` keys — `validate` cannot catch dangling output references; they surface only at run time as `undefined`.
<!--skill-flavor:export-bucket-stability:end-->
<!--skill-flavor:generic-resource-runtime-diagnostic:start-->
- **Path-parameter value formats are connector-specific.** `Retrieve`/`Update`/`Delete` endpoints take an id path param (e.g. `/repos/{repo}`) and the expected value format (name vs full name vs numeric id) varies and is sometimes wrong in the connector's own metadata — `uip is resources describe` shows the parameter's description and lookup hints. If the run 404s, cross-check by executing the same operation via `uip is resources run get <connector-key> <object-name> --connection-id <uuid> --query <param>=<value>`; if that also 404s, the connector's auto-generated metadata is broken upstream — pick a Curated activity or the Http kind instead.
<!--skill-flavor:generic-resource-runtime-diagnostic:end-->

<!--skill-flavor:solution-resource-fields:start-->
## Solution resources as activity fields

For fields referring to a process, queue, asset, or other Solution resource, use the resource **name** in runtime parameters and the resource **key** in picker metadata:

```bash
uip api-workflow registry stub <activity-type-id> \
  --connection-id <uuid> \
  --inputs '{"<resource-field>":"<resource-name>"}' \
  --resource-key '<resource-field>=<resource-key>' \
  --output json
```

Read the name and key from the corresponding Solution resource file. `Data.SolutionResourceFields` identifies these fields. Do not put the key in `--inputs` or the name in `--resource-key`. Deployment bindings are produced by `bindings sync`; picker display uses `savedResourceSelections`; the referenced resource must be deployed and visible to the connection.
<!--skill-flavor:solution-resource-fields:end-->

## Response shape and field rules

Both Http and IntSvc outputs are envelopes: `{ statusCode, statusText, headers, ok, request, content, vendorProcessingTimeMs }`. Read payloads under `.content`; IntSvc list payloads may be arrays directly, not `.content.value[]`. Inspect `optionalConfiguration.fieldsContainer.outputJsonSchema`: `type: "object"` means a single item; `type: "array"` means a list. Local CLI may return `content` as a JSON string while cloud returns a parsed value; normalize defensively in scripts. Use optional chaining and log the full output once if the expected shape is absent.
<!--skill-flavor:runtime-content-normalization-comment:start-->
<!--skill-flavor:runtime-content-normalization-comment:end-->

### Rule (a) — flat dotted keys

`bodyParameters`, `queryParameters`, and `pathParameters` must use exact flat schema names such as `message.subject` and `message.body.content`. Do not nest objects; StudioWeb's deserializer does not recurse and will drop nested fields on save.

### Rule (b) — bare connector literals

Connector parameter literals are bare (`"hi"`), not `${'hi'}`. Actual references remain `${$context...}`. This is opposite the Assign/Response/If literal-wrap rule 5. Pass bare strings through `--inputs`.

### Rule (c) — preserve both computed keys

Use `Data.SlotKey` for the activity key in `do` and `Data.ExportBucketKey` for `$context.outputs.<X>` and `export.as`. They may differ; never reconstruct or rename either. If renaming a slot, leave the export key unchanged. Re-stub with `--instance 2` for another instance rather than copying keys.

### Rule (d) — use the full endpoint

Use the IS Elements endpoint, which may include a hub prefix. `/<objectName>` is only a degraded fallback when `IsEnrichmentAvailable` is false; re-stub after IS access returns or inspect `uip is resources describe`.

## Multipart endpoints

The stub detects `parameters[].type === "multipart"` and emits both flat `bodyParameters` and `multipartParameters`, commonly including `{ "name": "body", "dataType": "string" }` and a file part. Keep `multipartParameters` even without an attachment: the executor JSON-stringifies the entire `bodyParameters` object into the string part and expects file references in file parts. Removing the declaration causes `400 "Unable to parse multipart body"`.

## Editing after stubbing

Use exact schema names, flat dotted keys, bare literals or real `${$context...}` expressions, and re-ping any replacement connection before changing both connection fields. Preserve the emitted export key. Re-stub with `--instance <n>` for additional instances. After reconcile or designer save, re-check downstream output references against the on-disk `export.as` keys.

## Limits

1. Trigger types (`"CuratedTrigger"`, `"GenericTrigger"`, `"GenericPersistence"`, and similar) cannot be stubbed; escalate to manual authoring.
2. `stub` does not validate `--inputs`; unknown fields are silently dropped. Check the IS schema.
3. Subsequent designer saves can re-introduce Response-activity mangling; see [troubleshooting.md](troubleshooting.md#object-valued-response-gets-corrupted-fields-evaluate-to-literal-expression-text).

<!--skill-flavor:registry-auth-limit:start-->
4. **Login is required for `resolve` and `stub`.** Both hit live tenant endpoints (TypeCache and IS Elements). `uip api-workflow run --no-auth` still works for the resulting workflow if it only uses Http kind with `ImplicitConnection`; IntSvc kind always needs auth at run time.
<!--skill-flavor:registry-auth-limit:end-->

## Anti-patterns

- Do not guess connector keys, activity GUIDs, endpoints, metadata, connection UUIDs, or Solution folder names; read them from CLI output and existing project metadata.
- Do not skip `uip is connections ping`, proceed after a failed ping, or trust only the filtered connection listing.
- Do not use Http kind for vendor activities, `call: "http"`, or a vendor URL in place of the IS endpoint.
- Do not read IntSvc output at the root; use `.content` and `Data.ExportBucketKey`.
- Do not nest connector fields or wrap connector literals as `${'literal'}`.
- Do not remove `multipartParameters` from multipart operations.
- Do not leave `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` or any `<REPLACE_WITH_*>` placeholder in a generated workflow; stop and ask the user if no working UUID or URL is available.
- Do not skip the required-field cross-check:

<!--skill-flavor:required-field-antipattern:start-->
- **Do NOT trust `registry stub`'s `queryParameters` / `pathParameters` / `bodyParameters` as complete.** After every stub call, cross-check via `uip is resources describe <connector-key> <object-name> --operation <op> --connection-id <uuid> --output json` (or parse `metadata.configuration.optionalConfiguration.fieldsContainer.inputFields` from the stub output itself) and fill in anything required that's missing. Symptom of skipping: workflow runs locally on stale defaults, fails in cloud with a 4xx, or the StudioWeb properties panel marks the field invalid without a clear error.
<!--skill-flavor:required-field-antipattern:end-->

<!--skill-flavor:solution-metadata-antipattern:start-->
- **Do NOT skip the Solution catalogue sync in Solutions-mode projects.** Two files MUST exist: the catalogue resource (`Solution/resources/solution_folder/connection/<connector-key>/<name>.json`) AND the per-user debug overwrites (`Solution/userProfile/<guid>/debug_overwrites.json`). Without both, the properties panel flags the activity with "to debug this resource, select a connection for it from the resource definition page" and clicking the activity nulls `with.connectionId`. Run `uip api-workflow bindings sync --workflow <Workflow.json>` followed by `uip solution resources refresh --solution-folder <path>` to write both. See [Step 5](#step-5--solutions-mode-intsvc-connection-synchronization).
<!--skill-flavor:solution-metadata-antipattern:end-->

<!--skill-flavor:http-example-execution-proof:start-->
Verified end-to-end: `uip api-workflow run --no-auth` on the resulting workflow returns `statusCode: 200`, `content.fact: "..."`. StudioWeb's designer renders the activity as the unified HTTP Request card. See [../assets/templates/connector-call-example.json](../assets/templates/connector-call-example.json) for a complete stub-generated workflow.
<!--skill-flavor:http-example-execution-proof:end-->
