---
name: uipath-aops
description: "UiPath StudioAdmin AOps (`uip aops`) — SourceControl discovery plus CICD pipelines. Drives `aops connection` / `repo` / `project` / `solution` to resolve a GitHub or Azure source binding, `aops pipeline processes` to pick an already-published Orchestrator process, then composes a PipelineDto for `pipeline create` / `save-and-run` and follows runs via `aops execution logs --follow`. Replaces the retired `uip sc` and `uip cicd` tools. For AOps governance policies (`uip gov aops-policy`)→uipath-governance. For `uip solution pack/publish/deploy`→uipath-platform. For workflow authoring (.xaml/.cs)→uipath-rpa."  # <!-- uip-check-skip -->
when_to_use: "User wants to discover StudioAdmin SourceControl state or create, run, or edit a UiPath CICD pipeline that builds source from an SC-synced Studio Solution or standalone project and binds it to an already-published Orchestrator process. Triggers: 'create a pipeline for X process', 'set up CI/CD for this solution', 'build + run my pipeline', 'list my source control connections', `uip aops`, `uip sc`, `uip cicd`, StudioAdmin SourceControl, PipelineDto."  # <!-- uip-check-skip -->
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath StudioAdmin AOps — Source Control + CICD Pipelines

Depends on the `@uipath/aops-tool` CLI plugin; install via `uip tools install @uipath/aops-tool` before using.

> **Tool migration.** `@uipath/sc-tool` (`uip sc`) and `@uipath/cicd-tool` (`uip cicd`) were unified into `@uipath/aops-tool` (`uip aops`). `@uipath/cicd-tool` is gone from npm. Every `uip sc <verb>` and `uip cicd <verb>` becomes `uip aops <verb>` — the verb trees merged without renaming any subcommand. See [migration-guide.md](references/migration-guide.md).  <!-- uip-check-skip -->

Build a StudioAdmin CICD pipeline that binds two independent things:

- **Source** — one Studio project the pipeline checks out on every run. Two equivalent ways to reach it:
  - **Solution path** — a project inside a Studio Solution surfaced by `aops connection solutions <connection-id>`
  - **Standalone-project path** — a project surfaced directly by `aops connection projects <connection-id>` (no enclosing Solution)
- **Target** — an already-published Orchestrator automation process surfaced by `aops pipeline processes`. The pipeline runs / updates this process as part of its execution.

## When to Use This Skill

- User wants a new pipeline for a Studio Solution or standalone project already synced to StudioAdmin
- User names a published Orchestrator process and wants a pipeline that runs / updates it
- User says "create / build / wire a pipeline" against a Solution or a process
- User wants a one-shot "create and run" with execution id + log follow
- User wants to inspect or kick off an existing pipeline run, or edit one after creation
- User wants to inspect SourceControl state — connections, repos, branches, project files, commit history

Do NOT use this skill for:

- AOps **governance** policies (`uip gov aops-policy` — Studio / Robot feature restrictions) → `uipath-governance`. Same "AOps" word, different product surface.
- Packing or publishing a `.nupkg` (`uip solution pack/publish/deploy`) → `uipath-platform`
- Authoring or editing workflow code (`.xaml`, `.cs`) → `uipath-rpa`
- Creating the SourceControl connection itself — connections are UI-only via the StudioAdmin web app
- Publishing a new process — processes are published separately (Studio publish / `uip solution publish`)

## Vocabulary

| Term in this skill | What it means |
|---|---|
| **SourceControl connection** | A StudioAdmin-side link to GitHub or Azure DevOps. Lists via `aops connection list`. UI-provisioned. |
| **Studio Solution** | A `.uipx` container surfaced by SourceControl, holding one or more projects. Lists via `aops connection solutions <connection-id>`. |
| **Project** (in this skill) | A Studio project — the **source** for the pipeline build. Reached two ways: nested inside a Solution (via `connection solutions`) OR standalone (via `connection projects`). Any project `Type` is eligible for source binding. |
| **Published (automation) process** | An already-deployed Orchestrator process the pipeline runs / updates. Lists via `aops pipeline processes`. **Independent of any project type.** |
| **PipelineDto** | The wire format `pipeline create` / `save-and-run` consume via `--file`. Carries source binding (project + repository + branch) AND target binding (`processIdentifier`). |
| **EditPipelineDto** | The narrower shape `pipeline update --file` consumes — `identifier`, `name`, `runMode`, `description`, `arguments` only. |

The published process is NOT the same thing as a Studio project of type "Process". Studio project types describe how to build / package source. Published processes are runnable artifacts in Orchestrator. The pipeline glues them: build source → update / run the target process.

## Critical Rules

1. **The tool is `aops`, not `sc` / `cicd`.** Run `uip tools list --output json` and confirm an entry with `commandPrefix: "aops"`. If missing: `uip tools install @uipath/aops-tool`. If the registry does not know the package, see [migration-guide.md § Install](references/migration-guide.md#install). Then `uip login status --output json`; if not logged in, `uip login`.
2. **Response keys are PascalCase; `--file` input keys are camelCase.** The CLI PascalCases every key inside the stdout `Data` payload (`Identifier`, `RemoteId`, `CloneUrl`, `DefaultBranch`, `ProjectRelativePath`). The JSON you *write* for `--file` must use the DTO's own camelCase names (`repositoryId`, `projectPath`, `processIdentifier`). Never round-trip stdout into `--file`. Use `--output-file` when you need a raw DTO on disk.
3. **Sources come from AOps, not local disk.** Do NOT scan `*.sln` / `*.uipx` / `project.json` files. Discover via `uip aops connection solutions <connection-id>` and `uip aops connection projects <connection-id>`. Local files don't carry `connectionIdentifier` / `remoteId` / project SourceControl UUIDs — fields the CICD API requires.
4. **Source project and target process are independent picks.** The pipeline binds one Studio project (for source) AND one already-published Orchestrator process (for run / update). Do NOT auto-derive the process from the project's name or type, and do NOT filter projects by `Type`. Both come from separate API calls; the user (or context) picks each.
5. **`pipeline create --file` consumes a PipelineDto, NOT an EditPipelineDto.** The two shapes differ — EditPipelineDto is for `pipeline update`. See [pipeline-dto-guide.md](references/pipeline-dto-guide.md).
6. **`branch` is the only hard-required field on PipelineDto.** Everything else is optional in the type system, but a useful pipeline needs `name`, `connectionIdentifier`, `repositoryId`, `projectPath`, `processIdentifier`, and `runMode`. Default `branch` to the repository's `DefaultBranch` unless the user specifies one.
7. **`--output json` on every command.** All `uip aops` calls are parsed by the agent. Never run them without it. Do NOT add `--output-filter` to a command that has a defaulted `--limit` unless you also pass `--limit` explicitly — the CLI refuses that combination (Rule 13).
8. **The published process is the user's pick.** `pipeline processes` returns `{ProcessId, Name, Description, Package, Version}`. When the user names a process by `Name` or `Package`, find the exact match — if 2+ candidates remain (same `Package`, different versions), prefer the highest `Version` and confirm. Never silently bind a process the user didn't name.
9. **Process arguments are process-specific — inspect, infer, then ask.** Before composing `PipelineDto.arguments`: (1) run `aops pipeline process <PROCESS_ID> --output json` to read `Arguments` (declared schema) + `InputArguments` (JSON string of default values). (2) Infer overrides from conversation context. (3) Ask the user only for parameters that cannot be inferred AND have no schema default. Default the field to `null` (= use process defaults). See [pipeline-dto-guide.md § arguments](references/pipeline-dto-guide.md#arguments).
10. **Connection-and-source discovery is two calls, in order.** `connection list` → pick the connection → `connection solutions` / `connection projects`. Never assume there is exactly one connection or one solution.
11. **If discovery returns nothing, then sync.** Try `connection solutions <id>` / `connection projects <id>` first. If both return an empty list OR the user reports a missing solution / project that was just added, check `connection state --connection <id>` and offer `connection sync <id> --wait`. A `SyncState: "Fail"` value is not by itself a reason to bail — cached data from the last successful sync is usually still usable.
12. **Never invent identifiers.** Source map:
    - `connectionIdentifier` ← `connection list` → `Identifier` (SourceControl UUID).
    - `repositoryId` ← `connection repos` → **`RemoteId`** (provider-native id: numeric for GitHub, UUID for Azure DevOps). NOT `Identifier` (SourceControl's internal UUID). Sending the SourceControl UUID makes `pipeline create` succeed but the pipeline fails runtime resolution — the StudioAdmin UI flags it "connection no longer valid".
    - `projectPath` ← `connection solutions` → `Projects[].ProjectRelativePath`, or `repo project-files <repo-id>` → `Path`.
    - `processIdentifier` ← `pipeline processes` → `ProcessId`.
13. **Pagination is page-based.** `--offset` must be an exact multiple of `--limit` or the command fails client-side before any request. Defaults: `connection projects` / `project list` 10; `connection solutions` / `pipeline list` / `pipeline executions` 20. `--take` / `--skip` are deprecated aliases on the `connection` and `project` verbs and do not exist at all on `pipeline executions`.
14. **`pipeline delete` requires `-y` / `--yes`.** The CLI never prompts. Without the flag the command refuses and no request is sent. Confirm with the user before passing it.
15. **`pipeline update --file` is a full-replace PUT that rejects unknown keys.** It accepts exactly `identifier`, `name`, `runMode`, `description`, `arguments`. Any other key — including one differing only in case — is a `ValidationError` (exit 3) and nothing is sent. Produce the file with `pipeline get <id> --for-update --output-file <path>`, never by capturing stdout.
16. **`pipeline create` returns the persisted PipelineDto.** Success is `{Result: "Success", Code: "PipelineCreated", Data: {…, "Identifier": "<new-id>"}}`. Capture `Data.Identifier` for follow-up `run` / `update` / `delete` calls.
17. **`pipeline save-and-run` returns `Data.Pipeline` + `Data.ExecutionId`.** `ExecutionId` is lifted out of the persisted DTO's `latestPipelineExecution`; when it is `null` the run was queued but the response didn't surface the row — fall back to `pipeline executions <pipeline-id> --limit 1 --output json`. See [save-and-run-guide.md](references/save-and-run-guide.md).

## Quick Start

The end-to-end flow is 7 steps (Step 3 has two variants — `3a` for Solution-nested sources, `3b` for standalone projects). The full procedure with example output and error handling is in [discovery-flow.md](references/discovery-flow.md). Reach for it whenever a step needs more detail than the snippet below.

### Step 0 — Tool + auth check

```bash
uip tools list --output json
uip login status --output json
```

If `aops` is missing: `uip tools install @uipath/aops-tool`. If not logged in: `uip login`. The SourceControl and CICD halves share one token but are separately entitled — SourceControl verbs need the StudioAdmin SourceControl service; pipeline verbs need StudioAdmin CICD plus `Pipelines.View` (mutations need `Pipelines.Edit` / `Pipelines.Run`) on the active runtime environment.

### Step 1 — Pick the SourceControl connection

```bash
uip aops connection list --output json
```

Row shape: `{Identifier, Name, Type, SyncState}`. `Type` is `"GitHub"` or `"Azure"`. Save the chosen `Identifier` as `CONNECTION_ID`. If multiple connections are returned and the user didn't name one, ask the user.

### Step 2 — Pick the source: Solution-nested project OR standalone project

Both kinds of source live on the same connection. List both, then let the user pick from the combined set:

```bash
uip aops connection solutions <CONNECTION_ID> --output json
uip aops connection projects <CONNECTION_ID> --output json
```

- `connection solutions` returns `Data.Result[]` (paged, default 20) of `SolutionDto`. Each row has `Identifier`, `Name`, `Path`, `Repository` (full RepositoryDto), and `Projects[]` (each `{ProjectId, Type, ProjectRelativePath}`).
- `connection projects` returns `Data[]` of curated rows `{ProjectId, Name, Description, Type, Repository}` (paged, default 10). **`Repository` is just the name** — the curated view drops the full RepositoryDto and the project file's path. Recover the rest in Step 3b.

Decision:

- **User named a Solution** → Solution path (Step 3a).
- **User named a standalone project that appears only in `connection projects`** → standalone path (Step 3b).
- **User named a name appearing in both** → ask the user.
- **No user hint** → list every Solution + every standalone project (label which is which) and ask the user.

### Step 3a — Solution path: pick a project inside the Solution

For the chosen Solution, list `Projects[]`. Common `Type` values: `Process`, `Library`, `TestCase`. **Do not filter by `Type`** — any project can serve as a pipeline's source binding.

- **1 project** → use it.
- **2+ projects** → ask the user, listing each project's `Type` and `ProjectRelativePath`.
- **0 projects** → fail with `Result: "Failure"`, instruct the user to add a project to the Solution and re-sync.

The Solution's embedded `Repository` lacks `RemoteId`. One extra call:

```bash
uip aops connection repos <CONNECTION_ID> --output json
```

Find the row whose `Identifier` matches `solution.Repository.Identifier`. That row carries `RemoteId`.

Derive the DTO fields:

| Variable | From |
|---|---|
| `REPOSITORY_ID` | matched repo's `RemoteId` (NOT `Identifier` — see Critical Rule 12) |
| `REPOSITORY_URL` | `solution.Repository.CloneUrl` |
| `REPOSITORY_NAME` | `solution.Repository.Name` |
| `DEFAULT_BRANCH` | `solution.Repository.DefaultBranch` |
| `PROJECT_PATH` | `project.ProjectRelativePath` exactly (e.g. `<project-dir>/project.json`) |
| `PROJECT_NAME` | `""` (empty string) — StudioAdmin's UI leaves it blank. Pipeline binding works without it. |

Skip to Step 4.

### Step 3b — Standalone-project path: recover repository and project path

The curated standalone views drop the data needed. Two extra calls fill the gaps:

```bash
uip aops connection repos <CONNECTION_ID> --output json
uip aops repo project-files <REPOSITORY_SC_UUID> --output json
```

- `connection repos` returns full RepositoryDtos. Look up the row whose `Name` matches the project's `Repository` field. Take its `Identifier` (for the next call), `RemoteId`, `CloneUrl`, `Name`, `DefaultBranch`.
- `repo project-files <repo-id>` takes the repo's **SourceControl UUID** (`Identifier`), not `RemoteId`, and returns one row per automation project file in the repo: `{Name, Path, Type, BuildableUnitType}`. `Path` is `PROJECT_PATH`. Add `--reference <branch|tag|sha>` to inspect a non-default branch.

Optional confirmation of the project's own metadata:

```bash
uip aops project get --project-id <PROJECT_ID> --output json
```

Returns `Name`, `Type`, `DefaultBranch`, and a flattened `Repository` name string — do not rely on it for any identifier. Add `--with-branches` for `AvailableBranches` (one extra round-trip).

Derive the DTO fields:

| Variable | From |
|---|---|
| `REPOSITORY_ID` | matched repo's `RemoteId` (NOT `Identifier`) |
| `REPOSITORY_URL` | matched repo's `CloneUrl` |
| `REPOSITORY_NAME` | matched repo's `Name` |
| `DEFAULT_BRANCH` | matched repo's `DefaultBranch` (agrees with `project get`'s `DefaultBranch`) |
| `PROJECT_NAME` | `""` (empty string) — UI-created pipelines leave it blank |
| `PROJECT_PATH` | `repo project-files` row's `Path`. If several rows come back, ask the user which project to build. |

### Step 4 — Pick the already-published Orchestrator process

```bash
uip aops pipeline processes --output json
```

Row shape: `{ProcessId, Name, Description, Package, Version}`. This is the catalog of processes already deployed in Orchestrator and available for binding — independent of any Studio project.

- **User named a process** (by `Name` or `Package`) → exact-match (case-insensitive). If 2+ rows share that `Name` / `Package` (different versions), pick the highest `Version` and confirm with the user.
- **No user name** → ask the user, listing each candidate's `Name`, `Package`, and `Version`.

Save `ProcessId` as `PROCESS_ID`.

### Step 5 — Inspect and resolve process arguments

```bash
uip aops pipeline process <PROCESS_ID> --output json
```

Read `Data.Arguments` (declared parameter schema) and `Data.InputArguments` (JSON-encoded string of default values). Parse `InputArguments` with `JSON.parse` to get the default-value object.

For each parameter declared in `Data.Arguments`:

1. **Try to infer the override from conversation context.** Example: user said "process the May 2026 batch" → infer `BatchDate: "2026-05"`.
2. **If inferable** → record the override value.
3. **If not inferable and the parameter has a default** (present in parsed `InputArguments`) → skip it; the default fires at runtime.
4. **If not inferable and no default** → ask the user. Use a choice-style prompt for enum / boolean parameters and a free-form prompt for strings / numbers / paths. Required parameters with no default fail at run time if omitted.

Build `PIPELINE_ARGUMENTS` as an override object containing only the parameters to change. Set to `null` when no overrides apply — that's the signal to use all process defaults. If `pipeline process` returns no arguments, default the field to `null`.

Full workflow, the four argument surfaces, and the wire-shape caveat: [pipeline-dto-guide.md § arguments](references/pipeline-dto-guide.md#arguments).

### Step 6 — Compose the PipelineDto

Start from [assets/templates/pipeline-dto-template.json](assets/templates/pipeline-dto-template.json) and fill the fields. Keys are **camelCase** — this is an input file, not CLI output. The minimum useful shape:

```json
{
  "name": "<PIPELINE_NAME>",
  "runMode": "Manually",
  "description": "<OPTIONAL>",
  "connectionIdentifier": "<CONNECTION_ID>",
  "repositoryId": "<REPOSITORY_REMOTE_ID>",
  "repositoryUrl": "<REPOSITORY_URL>",
  "repositoryName": "<REPOSITORY_NAME>",
  "repositoryType": "git",
  "branch": "<DEFAULT_BRANCH>",
  "projectName": "",
  "projectPath": "<PROJECT_PATH>",
  "processIdentifier": "<PROCESS_ID>",
  "arguments": null
}
```

Write the JSON to disk via `Write` — pick a path under the current working directory, e.g. `./pipeline-<name-kebab>.json`. Do NOT include `identifier`; that field is server-assigned. Replace `arguments` with the override object from Step 5 when there is one. `repositoryType` is normalized server-side to `"git"`. `projectName` is intentionally `""`; pipeline binding resolves on `repositoryId` + `projectPath` + `branch`.

Before calling create, sanity-check the name is free:

```bash
uip aops pipeline list --search "<PIPELINE_NAME>" --output json
```

Empty `Data: []` means the name is available. Prefer `pipeline list --search` over `pipeline search --name` for uniqueness checks — `list --search` returns a curated list reliably, while `search --name` exits 1 with a not-found error when nothing matches.

### Step 7 — Create the pipeline

**Create only:**

```bash
uip aops pipeline create --file ./pipeline-<name-kebab>.json --output json
```

Returns `Code: "PipelineCreated"` and the persisted DTO — capture `Data.Identifier`.

**Create + run + capture execution id:**

```bash
uip aops pipeline save-and-run --file ./pipeline-<name-kebab>.json --output json
```

Returns `Code: "PipelineSavedAndRunStarted"` with `Data.Pipeline` and `Data.ExecutionId`. If `ExecutionId` is `null`, look it up via `uip aops pipeline executions <new-pipeline-id> --limit 1 --output json`. See [save-and-run-guide.md](references/save-and-run-guide.md) for log-follow.

## PipelineRunMode

| Value | Semantics |
|---|---|
| `Manually` | Default. Pipeline runs only on explicit `pipeline run <id>` or `save-and-run`. |
| `AtSpecificTime` | Time-scheduled. Server-side trigger; the schedule itself is configured in the StudioAdmin UI. |
| `ForEachCommit` | Runs automatically on every commit to `branch`. |

Default to `Manually` unless the user asks for commit-driven or scheduled.

## Command Map

Every verb, grouped by subject. Details in the references.

| Subject | Verbs |
|---|---|
| `connection` | `list`, `state`, `sync`, `delete`, `repos`, `repos-bulk`, `projects`, `solutions`, `azure-projects` |
| `repo` | `branches`, `project-files` |
| `project` | `list`, `get`, `files`, `content`, `commits`, `commit` |
| `solution` | `get`, `commits` |
| `pipeline` | `list`, `state`, `processes`, `process`, `repos`, `get`, `search`, `create`, `update`, `delete`, `run`, `save-and-run`, `executions`, `executions-bulk` |
| `execution` | `get`, `logs`, `details`, `stop` |

## Reference Navigation

| I need to... | Read |
|---|---|
| **Translate an old `uip sc` / `uip cicd` command** | [migration-guide.md](references/migration-guide.md) |  <!-- uip-check-skip -->
| **Full discovery sequence with example outputs** | [discovery-flow.md](references/discovery-flow.md) |
| **Every PipelineDto field + where to source it** | [pipeline-dto-guide.md](references/pipeline-dto-guide.md) |
| **Create + run + follow logs in one flow** | [save-and-run-guide.md](references/save-and-run-guide.md) |
| **JSON skeleton for a new PipelineDto** | [assets/templates/pipeline-dto-template.json](assets/templates/pipeline-dto-template.json) |

## Completion Output

After a successful create / save-and-run, report:

1. The new `Data.Identifier` (UUID) and `Name`
2. For save-and-run: the `ExecutionId` and the `uip aops execution logs <execution-id> --follow` command the user can run to track it
3. The PipelineDto JSON file path on disk (so the user can edit + re-apply)
4. Next steps: list executions (`uip aops pipeline executions <id>`), edit (`uip aops pipeline get <id> --for-update --output-file <path>` → edit → `pipeline update <id> --file <path>`), or delete (`uip aops pipeline delete <id> --yes`)

## Anti-patterns

1. **Running `uip sc …` or `uip cicd …`.** Both tools are retired; `@uipath/cicd-tool` no longer exists on npm. Every verb lives under `uip aops`.  <!-- uip-check-skip -->
2. **Feeding stdout JSON back into `--file`.** Stdout `Data` keys are PascalCased. `pipeline update` rejects such a file outright (ValidationError, exit 3) rather than applying it as a partial wipe. Use `pipeline get <id> --for-update --output-file <path>`, which writes the raw camelCase DTO.
3. **Reading a local `*.sln` / `*.uipx` / `project.json` from disk.** The CICD API needs SourceControl-side identifiers (`connectionIdentifier`, `remoteId`, project UUIDs) local files don't expose.
4. **Filtering source projects by `Type`.** All Studio project types (`Process`, `Library`, `TestCase`, etc.) are valid source bindings.
5. **Auto-matching a project to a process by name / package.** Source and target are independent — always let the user pick the process explicitly (or confirm an inferred match).
6. **Building one pipeline for multiple projects.** Each pipeline binds a single source project. Two projects → two pipelines.
7. **Feeding `pipeline get <id>` output straight into `pipeline create --file`.** `get` returns a PipelineDto including server-assigned fields like `latestPipelineExecution`. For round-trip editing use `--for-update` + `pipeline update`, not `create`.
8. **Inventing the `branch` value.** When the user doesn't name one, take the repository's `DefaultBranch`. Hand-typing `"main"` is a footgun on repos defaulting to `master` or a release branch.
9. **Bailing out on `SyncState: "Fail"`.** A failed last sync doesn't invalidate cached data from the previous successful one. Try the listing first; escalate to `connection sync --wait` only if it comes back empty.
10. **Passing `--take` / `--skip`.** Deprecated aliases; they warn on the `connection` / `project` verbs and do not exist on `pipeline executions`. Use `--limit` / `--offset`, keeping `--offset` a multiple of `--limit`.
11. **Adding `--output-filter` without `--limit`.** On any command with a defaulted `--limit` the CLI refuses the combination, because the filter would silently run over a capped page.
12. **Calling `pipeline delete <id>` without `--yes`.** The CLI never prompts; the call is refused and nothing happens.
13. **Re-implementing in raw REST.** `uip aops` handles the StudioAdmin base paths (`/{orgId}/roboticsops_/sourcecontrol_/`, `/{orgId}/roboticsops_/cicd_/`), pagination, and the `Result/Code/Data` envelope. Never `curl` these endpoints by hand.
