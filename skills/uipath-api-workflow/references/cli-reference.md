# CLI Reference — API Workflows

All `uip` commands relevant to authoring, running, packaging, and publishing API workflows. The api-workflow-tool ships with `@uipath/cli` (no separate install).

## `uip api-workflow init`

Scaffold a new API workflow project in the **correct Studio Web editable shape**. This is the canonical way to create a project — do NOT hand-assemble the files.

```bash
uip api-workflow init <name> \
  [--force] \
  [--skip-solution-registration] \
  [--output json]
```

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `<name>` | yes | Project name (and folder created under the cwd). Letters, numbers, spaces, `_`, `-` only. |
| `--force` | no | Write files even if the target directory is non-empty (does not clear existing contents). |
| `--skip-solution-registration` | no | Do NOT auto-register the project in the surrounding solution `.uipx`. Use for standalone (CLI-only) projects. |

Run it from inside the solution directory (the folder containing the `.uipx`) so it auto-registers the project. It writes four files into `<name>/`:

| File | Content |
|------|---------|
| `project.uiproj` | `{ "ProjectType": "Api", "Name": "<name>", "Description": null, "MainFile": "Workflow.json" }` |
| `Workflow.json` | The `WorkflowStart` skeleton (same as the empty template) |
| `entry-points.json` | `$schema`/`$id`, one entry: `filePath: "content/Workflow.json"`, fresh `uniqueId`, `type: "Api"`, `input`/`output` null |
| `bindings_v2.json` | `{ "version": "2.0", "resources": [] }` |

When run inside a solution, it also appends the project to the `.uipx` `Projects` array (`ProjectRelativePath: "<name>/project.uiproj"`, a fresh `Id`, `Type: "Api"`). It does NOT write `.local/ProjectSettings.json` — Studio Web creates that on first open; do not author it by hand.

### Success output

```json
{
  "Result": "Success",
  "Code": "ApiWorkflowInit",
  "Data": {
    "Status": "Created successfully",
    "Path": "<projectDir>",
    "SolutionRegistration": { /* registration result; NextSteps when applicable */ }
  }
}
```

Failure (`Result: "Failure"`, exit 1) on an invalid name or a non-empty directory without `--force` (`Message: "Failed to create API Workflow project"`, details in `Instructions`).

## `uip api-workflow build`

Build (compile) a single API workflow project — a fast project-scoped check that does not touch unrelated projects in a solution.

```bash
uip api-workflow build <project-path> [--output json]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `<project-path>` | yes | Path to the API workflow project directory or `.uip` file. |

Output: `{ "Result": "Success", "Code": "ApiWorkflowBuild", "Data": { "Success": true } }`. Exit 1 on failure.

## `uip api-workflow pack`

Pack a single API workflow project into a `.nupkg`. Use to verify one project in isolation; full solution packaging still goes through `uip solution pack`.

```bash
uip api-workflow pack <project-path> <destinationPath> \
  [--package-id <id>] \
  [--package-version <version>] \
  [--signing-certificate-path <path>] \
  [--signing-certificate-password <password>] \
  [--signing-timestamp-server <url>] \
  [--output json]
```

| Argument / Flag | Required | Description |
|-----------------|----------|-------------|
| `<project-path>` | yes | API workflow project directory or `.uip` file. |
| `<destinationPath>` | yes | Directory where the `.nupkg` is written. |
| `--package-id <id>` | no | NuGet package ID. |
| `--package-version <version>` | no | NuGet package version. |
| `--signing-*` | no | Optional package signing (certificate path/password, timestamp server). |

Output: `{ "Result": "Success", "Code": "ApiWorkflowPack", "Data": { "Success": true, "Packages": ["<path>.nupkg"] } }`. Exit 1 on failure.

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
| `<keyword>` | yes | Whitespace-tokenized; every token must substring-match somewhere in `displayName`, `connectorKey`, `objectName`, `fullName`. Case-insensitive. Combined queries narrow: `"github list records"` matches GitHub's "List Records". |
| `-l, --limit <n>` | no | Max results (default: 50). |

Success output (keys are PascalCased by the output formatter):
```json
{
  "Result": "Success",
  "Code": "ActivityResolveSuccess",
  "Data": {
    "Keyword": "newest email",
    "ResultCount": 1,
    "Matches": [
      {
        "UiPathActivityTypeId": "b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a",
        "DisplayName": "Get Newest Email",
        "Description": "...",
        "ConnectorKey": "uipath-microsoft-outlook365",
        "ObjectName": "getNewestEmail",
        "HttpMethod": "GET",
        "ActivityType": "Curated",
        "Operation": null
      }
    ]
  }
}
```

`Operation` is set for Generic activities (`"List"`, `"Retrieve"`, `"Create"`, …; capitalized in TypeCache) and `null` for Curated. Generic matches carry no `ObjectName`/`HttpMethod` — those resolve at stub time from `--object-name` + IS metadata.

Failure modes:
- `"Not logged in. Run 'uip login' first."`
- `"No activities matched '<keyword>'"` — try a different keyword (vendor-internal names differ from marketing names).
- `"Invalid --limit value"` — must be a positive integer.

### `uip api-workflow registry stub`

Emit a ready-to-paste activity object for a known `uiPathActivityTypeId`. Combines the TypeCache entry (GUID + `InstanceParameters`) with Integration Service Elements metadata (full path, request/response fields, multipart signal) and picks Http kind (`UiPath.Http`) or IntSvc kind (`UiPath.IntSvc`) by `connectorKey`.

```bash
uip api-workflow registry stub <activity-type-id> \
  [--connection-id <uuid>] \
  [--object-name <name>] \
  [--instance <n>] \
  [--slot-key <PascalCase>] \
  [--inputs <json>] \
  --output json
```

| Argument / Flag | Required | Description |
|--|--|--|
| `<activity-type-id>` | yes | The `uiPathActivityTypeId` GUID from `resolve`. |
| `--connection-id <uuid>` | IntSvc kind only | Pinged vendor connection UUID. IntSvc kind leaves `<REPLACE_WITH_VENDOR_CONNECTION_UUID>` placeholders if omitted. Ignored for Http kind (HTTP). |
| `--object-name <name>` | Generic activities only | Target connector object for a Generic activity ("List Records" of *what*). Discover names with `uip is resources list <connector-key> --connection-id <uuid>`. Defaults to the object pinned in the activity definition, when present. Ignored (with a warning) for Curated activities — their object is fixed by the activity definition. |
| `--instance <n>` | no | Suffix for slot/export bucket key. Default `1`. `--instance 2` produces `<Name>_2` keys. |
| `--slot-key <PascalCase>` | no | Override the auto-derived PascalCase slot key. The export bucket key always derives from `objectName + "_<n>"` (both Curated and Generic) and is not affected by this flag. |
| `-i, --inputs <json>` | no | JSON object mapping field names to values. Field names match the IS schema (flat dotted keys — `"message.subject"`, not `{message:{subject:…}}`). Pass bare strings for literals; `${...}` for expression references. |
| `--resource-key <field>=<key>` | no (repeatable) | Bind a Solution-resource picker field (listed in `Data.SolutionResourceFields`) to a solution resource **key**, so StudioWeb's picker renders the selection. The key is the `key` field of the matching file under the solution's `resources/` tree (e.g. `resources/solution_folder/process/process/<Name>.json`). The field's *value* (the resource name) still goes via `--inputs`. Requires a StudioWeb build with `savedResourceSelections` support; older builds ignore the entry (runtime unaffected). |

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
    "Parameters": [ { "name": "parentFolderId", "type": "query", "required": true } ],
    "RequestFields": [],
    "ResponseFields": [ { "name": "subject", ... } ],
    "IsEnrichmentAvailable": true,
    "Warnings": [...]
  }
}
```

`Data.Activity` drops directly into the root sequence's `do` array. `Data.ExportBucketKey` is what `$context.outputs.<X>` reads as downstream — bind expressions against this, NOT against `Data.SlotKey`. `Data.Parameters` (query/path/multipart) and `Data.RequestFields` (body) list the operation's inputs with `required` flags; `Data.ResponseFields` lists the fields the IS schema says will be present on the activity output (under `.content.<field>` for IntSvc kind). `Data.SolutionResourceFields` (when present) lists fields StudioWeb renders as Solution-resource pickers — see [Solution resources as activity fields](connector-activity-discovery.md#solution-resources-as-activity-fields-run-job-add-queue-item-) for the authoring recipe.

`Data.Warnings` (when present):
- `"IS Elements metadata could not be fetched…"` → IS schema lookup failed; stub uses fallback path `/<objectName>` and ships no `requestFields`. Endpoint may be wrong (no hub prefix, no multipart declaration).
- `"Required field(s) not provided via --inputs: …"` → the IS schema marks these `required: true` and they're absent; the run will likely 4xx. Re-stub with `--inputs` or add the values to the pasted activity.
- `"No --connection-id provided…"` → IntSvc kind stub has placeholder UUIDs; replace before running.

Failure modes:
- `"Activity '<guid>' not found in the Api-compatible TypeCache"` — re-run `resolve` to find a valid GUID.
- `"Activity type '<X>' is not supported"` — trigger flavors (`CuratedTrigger`, `GenericTrigger`, `GenericPersistence`, …) are event subscriptions, not callable tasks; they cannot be stubbed. Curated and Generic activities are both supported.
- `"Generic activity '<name>' needs a target object"` — Generic activities require `--object-name`. Discover candidates with `uip is resources list <connector-key> --connection-id <uuid>`.
- `"Could not resolve operation '<op>' on object '<name>' …"` — the object doesn't exist or doesn't support this operation (Generic stubs hard-require IS metadata; there is no fallback path/verb). Check the object with `uip is resources describe <connector-key> <object-name> --connection-id <uuid>`.
- `"Invalid --inputs JSON"` — `--inputs` must be a JSON object (`'{"key":"value"}'`).

### Typical sequence

```bash
# 1. Resolve
uip api-workflow registry resolve "outlook newest email" --output json

# 2. (IntSvc kind only) verify a connection
uip is connections list uipath-microsoft-outlook365 --output json
uip is connections ping <uuid> --output json

# 3a. Describe the operation FIRST — learn its inputs (required flags, value
#     semantics, lookup hints) so the stub can be run once, complete:
uip is resources describe uipath-microsoft-outlook365 getNewestEmail \
  --operation List \
  --connection-id <uuid> \
  --output json

# 3b. Stub, passing the required inputs learned in 3a
uip api-workflow registry stub b1d06cc8-be7f-3d0f-b54c-cb54f0e0690a \
  --connection-id <uuid> \
  --inputs '{"parentFolderId":"Inbox"}' \
  --output json
# Safety net: the stub echoes the schema (Data.Parameters / Data.RequestFields)
# and raises a Data.Warnings entry if a required field is still missing —
# an empty Warnings array confirms the activity is complete.

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

Walk a `Workflow.json`, extract IntSvc-kind connector activities, and emit the canonical `bindings_v2.json` file next to it. Connection bindings are derived locally; **Solution-resource bindings** (process/queue/asset fields like Run Job's `ReleaseName`) are derived by querying IS metadata for each activity's object — when IS is unreachable, generation is skipped and any pre-existing entries of those kinds are preserved rather than dropped. This mirrors what StudioWeb computes in-memory via `computeBindings$` when a workflow is opened in the designer, and what `solution pack` writes at pack time. The output is the **required input** to `uip solution resources refresh`, which is what actually writes the Solution catalogue file AND per-user debug overwrites (the two artefacts StudioWeb's properties panel reads to resolve `connectionId` on activity click).

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
    "ResourceCount": 2,
    "ActivitiesVisited": 1,
    "IntSvcActivities": 1,
    "DuplicatesCollapsed": 0,
    "ResourceBindings": 1,
    "PreservedResources": 0
  }
}
```

`ResourceCount` is the total entries written (connections + resource bindings + preserved). `DuplicatesCollapsed` reports activities that shared a connection — two Outlook activities reading the same mailbox count as 1 binding, with `DuplicatesCollapsed: 1`. `ResourceBindings` counts Solution-resource entries generated from IS metadata (e.g. `process | RPA Workflow` for a Run Job activity); `PreservedResources` counts pre-existing non-connection entries carried over because this run did not regenerate them.

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

Read the IS Elements schema for one operation on one connector. **Run this before stubbing** (step 3a) — it tells you which `--inputs` the operation needs (required flags, value semantics, lookup hints, parent-field actions), so the stub runs once and complete. The stub then echoes the same schema (`Data.Parameters` / `Data.RequestFields`) and warns if a required field is still missing, as a final check.

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

## `uip solution init`

Initialize a new empty solution. Required before adding API workflow projects. (Formerly `uip solution new` — that verb was retired; `new` now errors `unknown command 'new'`.)

```bash
uip solution init <solutionName> [--output json]
```

| Argument | Description |
|----------|-------------|
| `<solutionName>` | Solution name or path. Creates a directory with this name containing a `.uipx` manifest (empty `Projects` array) plus `AGENTS.md`/`CLAUDE.md` briefing files. |

Output: `{ "Result": "Success", "Code": "SolutionInit", "Data": { "Status": "Created successfully", ... } }`.

## `uip solution project add` *(scope: solution-tool)*

For **new** API workflow projects, prefer `uip api-workflow init <name>` run inside the solution directory — it scaffolds the correct `project.uiproj` shape AND auto-registers the project in the `.uipx`. `uip solution project add` errors (`Project name already exists`) on an already-registered project, and `remove`+`add` destroys the project `Id`. Reserve direct `.uipx` edits for converting a legacy `project.json` project in place (change only `ProjectRelativePath` → `<folder>/project.uiproj`, preserve `Id`/`Type`). A registerable project folder must contain `project.uiproj` (`ProjectType: "Api"`) + `Workflow.json` + `entry-points.json` — see [workflow-file-format.md](workflow-file-format.md#project-structure-studio-web-editable-contract) and SKILL.md rule 19a. See `uip solution project add --help` for current flags.

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

1. Reads the project file — `project.uiproj` (`ProjectType: "Api"`) for the Studio Web editable shape — and the entry point from `entry-points.json`
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
# 0. (once) create the solution if you don't have one
uip solution init MySolution --output json

# 1. Scaffold the project in the correct Studio Web shape + register it in the .uipx (rule 19a).
#    init's <name> takes no slashes — cd into the solution dir so it finds the parent .uipx.
cd ./MySolution
uip api-workflow init MyApiProject --output json
# ... edit MyApiProject/Workflow.json to add tasks ...

# 2. Local smoke test
uip api-workflow run ./MyApiProject/Workflow.json --no-auth --output json

# 3. Authenticate (only needed for publish / deploy)
uip login

# 4. Authenticated run
uip api-workflow run ./MyApiProject/Workflow.json --output json

# 5. Pack the solution
uip solution pack . ./build \
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

- `uip api-workflow publish` <!-- uip-check-skip --> (publish goes through `uip solution publish`)
- `uip apw <anything>` (no alias) <!-- uip-check-skip -->

These DO exist (don't route around them): `uip api-workflow init` (scaffold), `uip api-workflow build` (compile one project), `uip api-workflow pack` (one-project `.nupkg`). Solution-level packaging/publishing go through `uip solution pack` / `uip solution publish`. Offline validation is `uip api-workflow validate` (or running with `--no-auth`).
