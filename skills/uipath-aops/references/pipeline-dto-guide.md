# PipelineDto Guide

Field-by-field reference for the JSON shape `uip aops pipeline create --file` and `pipeline save-and-run --file` consume.

> **Casing.** Keys in a `--file` payload are the DTO's own **camelCase** names. Keys in CLI stdout are **PascalCase**. Never capture stdout into a file and pass it back — see [migration-guide.md § 1](migration-guide.md#1-stdout-data-keys-are-pascalcase).

## PipelineDto vs EditPipelineDto

Two distinct shapes — do NOT mix them.

| Shape | Consumed by | Includes |
|---|---|---|
| **PipelineDto** | `pipeline create --file`, `pipeline save-and-run --file`; returned by `pipeline get <id>` | Full binding: connection + repository + project + process + run config |
| **EditPipelineDto** | `pipeline update <id> --file`; returned by `pipeline get <id> --for-update` | Subset — only the editable surface: `identifier`, `name`, `runMode`, `description`, `arguments` |

`pipeline update` is a full-replace (HTTP PUT). The narrower EditPipelineDto means binding fields are immutable for the life of a pipeline. To change the project or branch binding, delete and recreate.

## PipelineDto fields

Only `branch` is required by the SDK type system. The other fields are optional in TypeScript but the API rejects pipelines omitting the binding fields below — fill them.

| Field | Required for create | Type | Source — Solution path | Source — Standalone-project path |
|---|---|---|---|---|
| `identifier` | No (server-assigned) | string (UUID) | Omit on create | Omit |
| `name` | Recommended | string | User-supplied. Defaults to `<source-kebab>-<process-kebab>` if not given | Same |
| `runMode` | Recommended | `"Manually"` \| `"AtSpecificTime"` \| `"ForEachCommit"` | Default `"Manually"` | Same |
| `description` | No | string \| null | User-supplied | Same |
| `connectionIdentifier` | Yes | string (UUID) | `connection list` → chosen `Identifier` | Same |
| `repositoryId` | Yes | string | `connection repos` row whose `Identifier` matches `solution.Repository.Identifier` → **`RemoteId`** | `connection repos` row whose `Name` matches the project's `Repository` field → **`RemoteId`** |
| `repositoryUrl` | Yes | string | `solution.Repository.CloneUrl` | Matched repo's `CloneUrl` |
| `repositoryName` | Yes | string | `solution.Repository.Name` | Matched repo's `Name` |
| `repositoryType` | Yes | string | `"git"` (server-normalized) | `"git"` |
| `branch` | **Yes (hard-required)** | string | `solution.Repository.DefaultBranch` | Matched repo's `DefaultBranch` |
| `projectName` | No | string | `""` (empty string — UI-created pipelines leave this blank) | `""` |
| `projectPath` | Yes | string | `project.ProjectRelativePath` exactly | `repo project-files` row's `Path` |
| `processIdentifier` | Yes | string (UUID) | `pipeline processes` → user-picked `ProcessId` | Same |
| `arguments` | No | any \| null | Runtime overrides. Default `null`. See § arguments | Same |
| `latestPipelineExecution` | Never on create | object | Server-populated read-only. Omit | Omit |

## Field sourcing

The discovery flow ([discovery-flow.md](discovery-flow.md)) returns every value listed above. Composition rules follow.

### `name`

The pipeline name shown in the StudioAdmin UI. Constraints:

- Must be unique within the runtime environment — `pipeline create` returns a conflict error on duplicates
- No format restriction beyond non-empty

Default pattern when the user doesn't supply one: `<source-kebab>-<process-kebab>`. Verify uniqueness via:

```bash
uip aops pipeline list --search "<candidate>" --output json
```

Empty `Data: []` means the name is free. Prefer `pipeline list --search` over `pipeline search --name`: `search --name` exits 1 with `Pipeline '<name>' not found.` when nothing matches, which is awkward to distinguish from a real failure.

### `runMode`

| Value | When to use |
|---|---|
| `"Manually"` | Default. Pipeline only runs on explicit `pipeline run <id>` or `save-and-run`. Best for a first-create flow. |
| `"AtSpecificTime"` | Pipeline runs on a server-side schedule. The schedule config itself is set in the StudioAdmin UI after creation — the CLI cannot author it. |
| `"ForEachCommit"` | Pipeline runs on every commit to `branch`. Wire only when the user explicitly asks for continuous-build behavior. |

### `branch`

The branch the pipeline checks out for every run. The only hard-required field in the DTO.

1. **User named a branch** → use it verbatim. Optionally verify via `uip aops repo branches <REPOSITORY_SC_UUID> --output json` (that verb takes the SourceControl UUID, not `RemoteId`).
2. **No user input** → use the repository's `DefaultBranch`. Never assume `"main"` / `"master"`.

### `repositoryType`

The server normalizes this to `"git"` regardless of provider. Always send `"git"`. Sending `"GitHub"` / `"Azure"` is accepted but the round-trip returns `"git"`.

### `repositoryId` — provider-native id, not SourceControl UUID

The most common trap. The `RepositoryDto` carries two ids:

| Field | What it is | Use for |
|---|---|---|
| `Identifier` | SourceControl service's internal UUID for the repo | `repo branches`, `repo project-files`, `pipeline list --repository-ids` |
| `RemoteId` | The provider's native repo id — numeric for GitHub, UUID for Azure DevOps | **`PipelineDto.repositoryId`** |

Sending `Identifier` makes `pipeline create` return `Success`, but the resulting pipeline can't resolve the repository at runtime. The StudioAdmin UI flags it "connection no longer valid" — misleading, since the connection is fine and only the repo binding is wrong. Always send `RemoteId`.

Note the asymmetry: the DTO wants `RemoteId`, while every other CLI verb that addresses a repository wants `Identifier`.

### `projectName`

UI-created pipelines store `""` here. The binding resolves on `repositoryId` + `projectPath` + `branch`; `projectName` is metadata-only. Default to `""`.

### `projectPath`

The path of the project file (`project.json` / `project.uiproj`) within the repository, forward-slash separated.

**Solution path:** `project.ProjectRelativePath` exactly. Example: `<project-dir>/project.json`.

**Standalone-project path:** `repo project-files <REPOSITORY_SC_UUID>` → the matching row's `Path`. When several rows come back, disambiguate against the project the user named; ask if still ambiguous.

Do NOT derive `projectName` from the last segment of `projectPath` — that segment is the project file, not the project.

### `processIdentifier`

The `ProcessId` of the already-published Orchestrator process the pipeline runs / updates. Picked **independently** of the source project — see [discovery-flow.md § Step 6](discovery-flow.md#step-6--pick-the-already-published-orchestrator-process).

Source (project) and target (process) are decoupled. The pipeline builds whatever source the project carries and then operates on the bound process; the project does NOT need to be the one that originally published the process. Do not auto-derive — let the user pick, or confirm an inference.

### `arguments`

Override values the pipeline passes to the automation process when it runs. The schema is process-specific — every published process declares its own parameter set. Four related surfaces — do NOT conflate:

| Field | Type | Where | What it carries |
|---|---|---|---|
| `Data.Arguments` | object | response from `pipeline process <process-id>` | Declared **input parameter schema** — names, types, defaults. Read-only metadata. |
| `Data.InputArguments` | JSON string | same response | Orchestrator-style serialized **default values**. Parse with `JSON.parse`. |
| `PipelineDto.arguments` | `any \| null` | **what you write** on create | **Override values** the pipeline passes at run time. `null` = use process defaults. |
| `Data.InputArguments` | object | `execution get <id> --with-arguments` | **Actual runtime values** the execution ran with. The CLI parses the string into an object. Use to verify what the pipeline submitted. |

#### Workflow — inspect, infer, ask

1. **Inspect the schema:**

   ```bash
   uip aops pipeline process <PROCESS_ID> --output json
   ```

   Read `Data.Arguments` for the declared parameter list and parse `Data.InputArguments` for default values:

   ```javascript
   const defaults = JSON.parse(response.Data.InputArguments ?? "{}");
   ```

2. **For each declared parameter**, decide what value to use:

   | Situation | Action |
   |---|---|
   | Conversation context implies a value (user named a file, date, count) | Record the inferred value as an override |
   | No inference, but the parameter has a default in `InputArguments` | Skip — omit from the override object; the default fires at runtime |
   | No inference, no default, parameter is required | Ask the user. Choice-style prompt for enum / boolean values; free-form for text / numbers / paths |
   | No inference, no default, parameter is optional | Omit |

3. **Build the override object** — Orchestrator-style key/value, only the parameters to change:

   ```json
   {
     "BatchDate": "2026-05",
     "DryRun": false
   }
   ```

   Empty object `{}` and `null` both mean "use all defaults" — prefer `null` for readability.

4. **Verify after the first run:**

   ```bash
   uip aops execution get <EXECUTION_ID> --with-arguments --output json
   ```

   `Data.InputArguments` shows what the pipeline actually submitted. If it diverges from the override set, the wire-shape caveat below applies.

#### Inference examples

| User says | Inferred override |
|---|---|
| "Create a pipeline that processes the May 2026 invoice batch" | `BatchDate: "2026-05"` (if `BatchDate` is declared) |
| "Set it to dry-run mode for now" | `DryRun: true` (if `DryRun` is declared) |
| "Use the file at /data/inputs/april.csv" | `InputFile: "/data/inputs/april.csv"` (if a path-like parameter is declared) |
| Nothing about parameters mentioned | `arguments: null` — defaults apply |

If a piece of conversation context could match multiple declared parameters, ask the user rather than guessing.

#### Asking the user — phrasing

For free-form values, ask in a regular chat reply, naming the parameter, its declared type, and the schema default if any:

> "The `<my-process>` process declares an `InputFolder` parameter (type `String`, no default). What folder path should the pipeline use?"

For choice-like values, present the declared enum options (or `true` / `false` for boolean parameters) and ask the user to pick.

#### Wire-shape caveat

The SDK types `PipelineDto.arguments` as `any`. The Orchestrator-style key/value shape is the conservative interpretation derived from how `execution get --with-arguments` parses runtime arguments. Some processes may expect a richer envelope (typed argument descriptors, qualified names). When `pipeline process <id>` surfaces a schema in `Arguments`, match that shape exactly. If `pipeline create` rejects the DTO with a parameter-shape error, re-fetch the process detail and align.

After the first successful run, `execution get --with-arguments` is ground truth for what the pipeline submitted — treat any divergence as a defect in the override composition, not in the API.

## Minimum useful PipelineDto

```json
{
  "name": "<my-pipeline>",
  "runMode": "Manually",
  "description": null,
  "connectionIdentifier": "<CONNECTION_ID>",
  "repositoryId": "<REPOSITORY_REMOTE_ID>",
  "repositoryUrl": "https://github.com/<my-org>/<my-repo>.git",
  "repositoryName": "<my-repo>",
  "repositoryType": "git",
  "branch": "main",
  "projectName": "",
  "projectPath": "<project-dir>/project.json",
  "processIdentifier": "<PROCESS_ID>",
  "arguments": null
}
```

Write to disk at e.g. `./pipeline-<my-pipeline>.json`, then:

```bash
uip aops pipeline create --file ./pipeline-<my-pipeline>.json --output json
```

Success returns:

```json
{
  "Result": "Success",
  "Code": "PipelineCreated",
  "Data": { "Identifier": "<new-pipeline-id>", "Name": "<my-pipeline>", "Branch": "main" }
}
```

`Data` is the full persisted PipelineDto. Capture `Data.Identifier`.

Optional: `--telemetry-flow-id <id>` adds a server-side correlation id as a query parameter. Only pass it when the user supplies one.

## Common create-time errors

`--file` is read and parsed before any API client is built, so file errors surface without credentials and without a request.

| Error | Cause | Fix |
|---|---|---|
| `File not found: <path>` | Wrong path passed to `--file` | Verify the file was actually written before invoking create |
| `File '<path>' does not contain a JSON object.` | The file holds `null`, a number, a string, or an array | Write a single JSON object |
| `required option '--file <path>' not specified` (exit 3) | Flag omitted | `create` and `save-and-run` both require `--file` |
| `"already exists"` / 409 conflict | Pipeline name clashes within the runtime environment | Rename in the JSON file, retry |
| `"branch '<x>' not found"` | The branch doesn't exist on the mirrored repository | Re-sync the connection, or use `DefaultBranch` |
| `"process not found"` / 404 on process | Stale `processIdentifier` | Re-run `pipeline processes` — the process may have been removed |
| `"repository … not found"` | Stale `repositoryId`, or `Identifier` sent where `RemoteId` was needed | Re-run `connection repos` and take `RemoteId` |
| `Pipelines.Edit` permission error | Current user lacks `Pipelines.Edit` on the active runtime environment | Switch runtime environment via the StudioAdmin UI |

## Round-trip editing an existing pipeline

To modify a pipeline after create, use the EditPipelineDto round-trip — NOT a new `create`:

```bash
# 1. Fetch the editable shape as a raw camelCase DTO on disk
uip aops pipeline get <pipeline-id> --for-update --output-file ./pipeline-edit.json --output json

# 2. Edit ./pipeline-edit.json — name / runMode / description / arguments only

# 3. Re-apply
uip aops pipeline update <pipeline-id> --file ./pipeline-edit.json --output json
```

`--output-file` is what makes this work: it writes the untransformed DTO, while stdout is PascalCased. Capturing stdout instead produces a file `update` rejects.

Rules `update` enforces:

| Rule | Failure |
|---|---|
| Every key in the file must be one of `identifier`, `name`, `runMode`, `description`, `arguments` | `ValidationError`, exit 3, nothing sent. The message names the offending keys and flags case-only mismatches |
| At least one editable field must be present | `ValidationError`, exit 3 — `carries no EditPipelineDto field to apply` |
| The file's `identifier`, if set, must match the positional id | `Failure`, exit 1 — `Mismatch: --file declares pipeline '<x>' but the positional id is '<y>'` |

Success returns `Code: "PipelineUpdated"` with `Data.Pipeline` — the serialized **request**, not the parsed file, so the envelope can only show what was actually sent.

Binding fields (`connectionIdentifier`, `repositoryId`, `branch`, `projectName`, `projectPath`, `processIdentifier`) are NOT editable. To change them, delete and recreate:

```bash
uip aops pipeline delete <pipeline-id> --yes --output json
```

`--yes` is mandatory — the CLI never prompts. Confirm with the user first. Deletion is permanent and does not auto-stop in-flight executions.
