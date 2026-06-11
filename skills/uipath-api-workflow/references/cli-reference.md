# CLI Reference — API Workflows

All `uip` commands relevant to authoring, running, packaging, and publishing API workflows. The api-workflow-tool ships with `@uipath/cli` (no separate install).

## `uip api-workflow run`

Execute an API workflow JSON file locally using the Serverless Workflow executor.

```bash
uip api-workflow run <file> \
  [--input-arguments <json>] \
  [--no-auth] \
  [--output json]
```

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `<file>` | yes | Path to the workflow JSON file. |
| `-i, --input-arguments <json>` | no | Input arguments as a JSON string (e.g., `'{"name":"World"}'`). Invalid JSON exits 1. |
| `--no-auth` | no | Skip credential loading. Use for workflows that don't need Orchestrator/IS auth — control-flow-only workflows, or Http kind activities using `connectionId: "ImplicitConnection"`. IntSvc kind (vendor connector) activities always need auth at run time. |
| `--output json` | no | Emit machine-readable JSON. Strongly recommended when output is parsed. |

### Success output

```json
{
  "Result": "Success",
  "Code": "WorkflowRun",
  "Data": { /* workflow output */ }
}
```

Exit code: `0`.

If the workflow has no `Response` task and no final `$output`, `Data` is `{ "message": "(no output)" }`.

### Failure output

```json
{
  "Result": "Failure",
  "Message": "<error description>",
  "Instructions": "<remediation hint>"
}
```

Exit code: `1`. Common `Message` values:
- `"File not found: <path>"`
- `"Invalid JSON in workflow file"`
- `"Invalid JSON in --input-arguments"`
- `"<task error>"` (executor-level failure)

### Examples

```bash
# Smoke test (control flow + JS, the typical case for this skill)
uip api-workflow run ./hello.json --no-auth --output json

# With inputs
uip api-workflow run ./greet.json \
  --input-arguments '{"name":"Alice","count":3}' \
  --output json
```

## `uip api-workflow registry`

Look up DAP / connector activities (StudioWeb TypeCache, `projectType=Api`) and emit api-workflow-shaped activity stubs. Replaces the old `uip case registry` flow for api-workflow authoring. Both subcommands require `uip login`. <!-- uip-check-skip -->

### `uip api-workflow registry resolve`

Search the API-workflow-compatible TypeCache by keyword. Returns candidate activities with the GUID, connector key, object name, and HTTP method needed for `stub`.

```bash
uip api-workflow registry resolve <keyword> [--limit <n>] --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `<keyword>` | yes | Substring matched against `displayName`, `connectorKey`, `objectName`, `fullName`. Case-insensitive. |
| `-l, --limit <n>` | no | Max results (default: 20). |

Success output:
```json
{
  "Result": "Success",
  "Code": "ActivityResolveSuccess",
  "Data": {
    "Keyword": "newest email",
    "ResultCount": 1,
    "Matches": [
      {
        "uiPathActivityTypeId": "b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a",
        "displayName": "Get Newest Email",
        "description": "...",
        "connectorKey": "uipath-microsoft-outlook365",
        "objectName": "getNewestEmail",
        "httpMethod": "GET",
        "activityType": "Curated"
      }
    ]
  }
}
```

Failure modes:
- `"Not logged in. Run 'uip login' first."`
- `"No activities matched '<keyword>'"` — try a different keyword (vendor-internal names differ from marketing names).
- `"Invalid --limit value"` — must be a positive integer.

### `uip api-workflow registry stub`

Emit a ready-to-paste activity object for a known `uiPathActivityTypeId`. Combines the TypeCache entry (GUID + `InstanceParameters`) with Integration Service Elements metadata (full path, request/response fields, multipart signal) and picks Http kind (`UiPath.Http`) or IntSvc kind (`UiPath.IntSvc`) by `connectorKey`.

```bash
uip api-workflow registry stub <activity-type-id> \
  [--connection-id <uuid>] \
  [--instance <n>] \
  [--slot-key <PascalCase>] \
  [--inputs <json>] \
  --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `<activity-type-id>` | yes | The `uiPathActivityTypeId` GUID from `resolve`. |
| `--connection-id <uuid>` | IntSvc kind only | Pinged vendor connection UUID. IntSvc kind leaves `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholders if omitted. Ignored for Http kind (HTTP). |
| `--instance <n>` | no | Suffix for slot/export bucket key. Default `1`. `--instance 2` produces `<Name>_2` keys. |
| `--slot-key <PascalCase>` | no | Override the auto-derived PascalCase slot key. Export bucket key always derives from `objectName + "_<n>"`. |
| `-i, --inputs <json>` | no | JSON object mapping field names to values. Field names match the IS schema (flat dotted keys — `"message.subject"`, not `{message:{subject:…}}`). Pass bare strings for literals; `${...}` for expression references. |

Success output:
```json
{
  "Result": "Success",
  "Code": "ActivityStubSuccess",
  "Data": {
    "Kind": "IntSvc",
    "SlotKey": "GetNewestEmail_1",
    "ExportBucketKey": "getNewestEmail_1",
    "Activity": { "GetNewestEmail_1": { "call": "UiPath.IntSvc", ... } },
    "ResponseFields": [ { "name": "subject", ... } ],
    "IsEnrichmentAvailable": true,
    "Warnings": [...]
  }
}
```

`Data.Activity` drops directly into the root sequence's `do` array. `Data.ExportBucketKey` is what `$context.outputs.<X>` reads as downstream — bind expressions against this, NOT against `Data.SlotKey`. `Data.ResponseFields` lists the fields the IS schema says will be present on the activity output (under `.content.<field>` for IntSvc kind).

`Data.Warnings` (when present):
- `"IS Elements metadata could not be fetched…"` → IS schema lookup failed; stub uses fallback path `/<objectName>` and ships no `requestFields`. Endpoint may be wrong (no hub prefix, no multipart declaration).
- `"No --connection-id provided…"` → IntSvc kind stub has placeholder UUIDs; replace before running.

Failure modes:
- `"Activity '<guid>' not found in the Api-compatible TypeCache"` — re-run `resolve` to find a valid GUID.
- `"Activity type '<X>' is not supported in v1"` — only `Curated` activities are stubbed today; Generic / Trigger flavors require additional `InstanceParameters` fields not yet handled.
- `"Invalid --inputs JSON"` — `--inputs` must be a JSON object (`'{"key":"value"}'`).

### Typical sequence

```bash
# 1. Resolve
uip api-workflow registry resolve "outlook newest email" --output json

# 2. (IntSvc kind only) verify a connection
uip is connections list uipath-microsoft-outlook365 --output json
uip is connections ping <uuid> --output json

# 3a. Stub
uip api-workflow registry stub b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a \
  --connection-id <uuid> \
  --inputs '{"parentFolderId":"Inbox"}' \
  --output json

# 3b. Cross-check required request fields — stub silently drops required: true fields
uip is resources describe uipath-microsoft-outlook365 getNewestEmail \
  --operation List \
  --connection-id <uuid> \
  --output json

# 4. Drop Data.Activity into the root sequence, fill missing required fields, replace placeholders.

# 5. (CONDITIONAL: IntSvc kind + Solutions-mode — skip for Http kind / ImplicitConnection / standalone projects)
#     Emit bindings_v2.json next to the workflow, then sync the Solution catalogue + debug overwrites:
uip api-workflow bindings sync --workflow Solution/<ProjectName>/Workflow.json --output json
uip solution resources refresh --solution-folder Solution --output json

# 6. Validate:
uip api-workflow run ./my-workflow.json --output json
```

See [connector-activity-discovery.md](connector-activity-discovery.md) for the full flow, field-shape rules, the Solution-resource file shape, and worked examples.

## `uip api-workflow bindings sync`

Walk a `Workflow.json`, extract IntSvc-kind connector activities, and emit the canonical `bindings_v2.json` file next to it. Pure-local transformation — no auth, no API calls. This mirrors what StudioWeb computes in-memory via `computeBindings$` when a workflow is opened in the designer, and what `solution pack` writes at pack time. The output is the **required input** to `uip solution resources refresh`, which is what actually writes the Solution catalogue file AND per-user debug overwrites (the two artefacts StudioWeb's properties panel reads to resolve `connectionId` on activity click).

**When to run.** After every `registry stub --connection-id <uuid>` that adds an IntSvc activity to a workflow inside a `Solution/` tree. Always paired with `uip solution resources refresh` (the next step in the typical sequence).

**When to skip:**
- **Http-kind-only workflows** — no IntSvc activities to bind. The command will still succeed with `ResourceCount: 0`, but the empty `bindings_v2.json` it writes serves no purpose.
- **Standalone projects** (no `Solution/` wrapper). StudioWeb doesn't consult a Solution resource tree in this mode; the downstream `solution resources refresh` has no solution to operate on.

```bash
uip api-workflow bindings sync \
  --workflow <path-to-Workflow.json> \
  --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `--workflow <path>` | yes | Path to the api-workflow JSON file. The output `bindings_v2.json` is written into the same directory as this file. |

Success output:
```json
{
  "Result": "Success",
  "Code": "BindingsSync",
  "Data": {
    "BindingsPath": "<dir>/bindings_v2.json",
    "ResourceCount": 1,
    "ActivitiesVisited": 1,
    "IntSvcActivities": 1,
    "DuplicatesCollapsed": 0
  }
}
```

`ResourceCount` is the number of unique connections in the output (one binding per unique UUID). `DuplicatesCollapsed` reports activities that shared a connection — two Outlook activities reading the same mailbox count as 1 binding, with `DuplicatesCollapsed: 1`.

Failure modes:
- `"Workflow file not found: <path>"` — `--workflow` does not exist. Pass an existing path.
- `"Workflow file is not valid JSON: <error>"` — the file exists but won't parse. Fix the JSON syntax.

**Idempotency.** Always overwrites the existing `bindings_v2.json`. The output is a pure function of the workflow's IntSvc activities — re-running with the same workflow produces the same file byte-for-byte (modulo trailing newline).

## `uip solution resources refresh`

Re-scan all projects in a solution and sync resource declarations from their `bindings_v2.json` files into the Solution catalogue. Uses `@uipath/resource-builder-sdk` to write the catalogue resource files (`Solution/resources/...*.json`) AND the per-user debug overwrites (`Solution/userProfile/<guid>/debug_overwrites.json`) — the two artefacts StudioWeb's properties panel reads to resolve `connectionId` on activity click. For api-workflow projects, run `uip api-workflow bindings sync` first to generate the `bindings_v2.json` this command consumes.

```bash
uip solution resources refresh \
  --solution-folder <path-to-solution-root> \
  [--login-validity <minutes>] \
  --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `--solution-folder <path>` | no (defaults to cwd) | Path to the solution root folder (the folder containing `.uipx`). |
| `--login-validity <minutes>` | no | Minimum minutes of token validity before forcing a refresh (default `10`). |

Requires `uip login`. The SDK resolves folder keys via Resource Catalog Service; an authenticated tenant context is required.

**Idempotency.** Import-only by design. First run for a binding triggers `addOrUpdateResourceToSolutionAsync` (status `Added`); subsequent runs skip the binding because its key is already in the solution. Re-running is safe and a no-op when nothing changed.

Lives in `solution-tool`, not `api-workflow-tool`. Full details in the [solution skill](../uipath-platform).

## `uip is resources describe`

Read the IS Elements schema for one operation on one connector. Used as the **required cross-check** after `uip api-workflow registry stub` (which silently drops `required: true` request fields).

```bash
uip is resources describe <connector-key> <object-name> \
  [--operation <operation>] \
  [--connection-id <uuid>] \
  --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `<connector-key>` | yes | Connector key (e.g. `uipath-microsoft-outlook365`). |
| `<object-name>` | yes | IS object name (e.g. `getNewestEmail`). |
| `--operation <op>` | no (recommended) | IS operation name (`List`, `Create`, `Get`, …). Without it, the call returns the available operations and prompts you to re-run with `--operation`. |
| `--connection-id <uuid>` | no | A pinged vendor connection UUID. Improves the field metadata (lookups can resolve, defaults from the live element are returned). |

Sample output (Outlook `getNewestEmail`, `--operation List`):

```json
{
  "Data": {
    "queryParameters": [
      { "name": "parentFolderId", "required": true,  "displayName": "Email folder" },
      { "name": "filter",         "required": false },
      { "name": "unReadOnly",     "required": false, "defaultValue": false },
      { "name": "withAttachmentsOnly", "required": false, "defaultValue": false },
      { "name": "importance",     "required": false, "defaultValue": "any" },
      { "name": "markAsRead",     "required": false, "defaultValue": false },
      { "name": "orderBy",        "required": false, "defaultValue": "receivedDateTime desc" },
      { "name": "top",            "required": false, "defaultValue": "1" }
    ],
    "pathParameters": null,
    "bodyParameters": null
  }
}
```

For every entry with `required: true`, confirm the stub's emitted activity has a value at `with.<location>Parameters.<name>`. Re-stub with `--inputs '{"<name>":"<value>"}'` or hand-edit. See [connector-activity-discovery.md — Required-field cross-check](connector-activity-discovery.md#required-field-cross-check--the-stub-drops-required-true-request-fields) and [troubleshooting.md](troubleshooting.md#required-request-field-dropped-by-registry-stub).

## `uip solution new`

Create an empty solution file. Required before adding API workflow projects.

```bash
uip solution new <solutionName> [--output json]
```

| Argument | Description |
|----------|-------------|
| `<solutionName>` | Solution name or path. Appends `.uipx` if no extension. Creates a folder with the same base name. |

Output: `{ "Result": "Success", "Code": "SolutionNew", "Data": { "Path": "<file>" } }`.

## `uip solution project add` *(scope: solution-tool)*

Add an API workflow project (folder containing `project.json` with `Type: "Api"`) to a solution. See `uip solution project add --help` for current flags.

## `uip solution pack`

Pack a solution folder into a `.zip` containing one `.nupkg` per project. Auto-detects projects with `Type: "Api"` and dispatches to `@uipath/tool-apiworkflow`.

```bash
uip solution pack <solutionPath> <outputPath> \
  [--name <name>] \
  [--version <version>] \
  [--login-validity <minutes>] \
  [--output json]
```

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `<solutionPath>` | yes | Path to solution folder or `.uis`/`.uipx` file. |
| `<outputPath>` | yes | Output directory for the `.zip`. |
| `-n, --name <name>` | no | Package name. Defaults to solution folder name. |
| `-v, --version <version>` | no | Package version. Default `1.0.0`. |
| `--login-validity <minutes>` | no | Min minutes before token refresh. Default `10`. |

### What the API workflow packager does

For each `Type: "Api"` project:

1. Validates project structure (must contain `project.json`)
2. Copies workflow JSON files to a clean output directory
3. Generates `operate.json` — runtime configuration consumed by the executor
4. Generates `package-descriptor.json` — manifest for the Cloud platform
5. Wraps the output as a `.nupkg`

Do NOT commit `operate.json` or `package-descriptor.json` — they are generated.

## `uip solution publish`

Upload a packed solution `.zip` to UiPath Pipelines for tenant deployment.

```bash
uip solution publish <packagePath> \
  [--tenant <tenant-name>] \
  [--login-validity <minutes>] \
  [--output json]
```

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `<packagePath>` | yes | Path to `.zip` from `uip solution pack`. Non-zip files reject. |
| `-t, --tenant <tenant>` | no | Tenant name. Defaults to the tenant chosen during `uip login`. |
| `--login-validity <minutes>` | no | Min minutes before token refresh. Default `10`. |

Requires `uip login`. Failure modes:
- `"File not found: <path>"`
- `"Invalid file type. Expected a .zip file"`
- HTTP errors from Pipelines API (auth, quota, naming conflict)

## `uip solution deploy`

Activate / configure / inspect a published solution. Subcommands: `deploy run`, `deploy status`, `deploy activate`, `deploy config`, `deploy list`, `deploy uninstall`. See `uip solution deploy --help` for the current subcommand list.

## `uip login` / `uip logout`

| Command | Use when |
|---------|----------|
| `uip login` | Before publishing, before deploying. (Workflows from this skill don't need auth to run locally.) |
| `uip login status --output json` | Verify auth state. Returns `{ "Status": "Logged in" \| "Logged out", ... }`. |
| `uip logout` | Clear stored credentials. |

## End-to-End Example

```bash
# 1. Author the workflow
cp ./.claude/plugins/uipath/skills/uipath-api-workflow/assets/templates/api-workflow-template.json \
   ./MyApiProject/main.json
# ... edit main.json to add tasks ...

# 2. Local smoke test
uip api-workflow run ./MyApiProject/main.json --no-auth --output json

# 3. Authenticate (only needed for publish / deploy)
uip login

# 4. Authenticated run
uip api-workflow run ./MyApiProject/main.json --output json

# 5. Pack the solution
uip solution pack ./MySolution ./build \
  --name MyApiSolution \
  --version 1.0.0 \
  --output json

# 6. Publish
uip solution publish ./build/MyApiSolution.zip \
  --tenant MyTenant \
  --output json
```

## Commands That Do NOT Exist

The agent should not invent these — they are NOT part of the api-workflow-tool surface:

- `uip api-workflow publish` <!-- uip-check-skip -->
- `uip api-workflow init` <!-- uip-check-skip -->
- `uip apw <anything>` (no alias) <!-- uip-check-skip -->

Build / publish go through `uip solution pack` / `uip solution publish`. Validation is done by running with `--no-auth`.
