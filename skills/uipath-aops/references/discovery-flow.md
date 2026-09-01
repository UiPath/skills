# Discovery Flow — Connection → Source → Process

Full procedure for resolving the identifiers a `PipelineDto` needs. Run sequentially.

All response field names below are as they appear on stdout — **PascalCase**. The JSON written for `--file` uses camelCase. See [migration-guide.md § 1](migration-guide.md#1-stdout-data-keys-are-pascalcase).

## Inputs the user provides

One or more of:

- **Solution name** — "create a pipeline for the `<my-solution>` solution"
- **Standalone project name** — "create a pipeline for the `<my-project>` project"
- **Already-published process name / package** — "create a pipeline for the `<my-process>` process"
- **Connection name** — disambiguates when multiple connections are in play

If none of the above are clear, ask the user before running any CLI command.

## Step 1 — Confirm the CLI tool is installed

```bash
uip tools list --output json
```

Expected: `Data` includes an entry with `"commandPrefix": "aops"` (from `@uipath/aops-tool`). If missing:

```bash
uip tools install @uipath/aops-tool
```

`@uipath/sc-tool` and `@uipath/cicd-tool` are retired — do not install or invoke them. Install failure recovery: [migration-guide.md § Install](migration-guide.md#install).

## Step 2 — Confirm login

```bash
uip login status --output json
```

If `Result: "Failure"` or expired: `uip login`. One token covers both halves of the tool, but entitlements differ:

- SourceControl verbs (`connection`, `repo`, `project`, `solution`) need the StudioAdmin SourceControl service enabled on the organization.
- Pipeline / execution verbs need StudioAdmin CICD enabled, a selected runtime environment, and `Pipelines.View` at minimum. Mutations need `Pipelines.Edit` / `Pipelines.Run`.

A cheap reachability check for the CICD half before doing real work:

```bash
uip aops pipeline state --output json
```

## Step 3 — List SourceControl connections

```bash
uip aops connection list --output json
```

Row shape: `{Identifier, Name, Type, SyncState}`. `Type` is `"GitHub"` or `"Azure"`. `SyncState` is `"Success"`, `"Fail"`, or `"Broken"`.

Decision:

- **User named the connection** → exact-match `Name`, take its `Identifier`
- **1 connection returned** → use it
- **2+ connections, no user hint** → ask the user, listing each connection's `Name` and `Type`

Save: `CONNECTION_ID`.

`SyncState: "Fail"` on the chosen connection is **not** a reason to bail. Cached solutions / projects from the last successful sync are usually still usable. Only escalate to a sync if the data needed in Steps 4–5 is missing.

## Step 4 — Discover the source (solutions + standalone projects)

Both kinds of source live on the same connection. List both:

```bash
uip aops connection solutions <CONNECTION_ID> --output json
uip aops connection projects <CONNECTION_ID> --output json
```

Both paginate page-based (`--offset` must be a multiple of `--limit`). `solutions` defaults to 20 per page, `projects` to 10. Raise `--limit` rather than paging when the user's org is small. `--search <term>` does a server-side substring filter on the name.

### `connection solutions` response

`Data.Result[]` — paged with a singular `Result` key. Each row is a `SolutionDto`:

```json
{
  "Identifier": "<SOLUTION_SC_UUID>",
  "ConnectionIdentifier": "<CONNECTION_ID>",
  "Name": "<my-solution>",
  "Path": "Solutions/<my-solution>.uipx",
  "Version": "1.0.0",
  "SolutionId": "…",
  "LastUpdated": "<iso-timestamp>",
  "Repository": {
    "Identifier": "<REPOSITORY_SC_UUID>",
    "Name": "<my-repo>",
    "CloneUrl": "https://github.com/<my-org>/<my-repo>.git",
    "DefaultBranch": "main"
  },
  "Projects": [
    { "ProjectId": "<PROJECT_ID>", "Type": "Process", "ProjectRelativePath": "<process-dir>/project.json" },
    { "ProjectId": "…",            "Type": "Library", "ProjectRelativePath": "<library-dir>/project.json" }
  ]
}
```

Carries the full `Repository` and the full project list with `ProjectRelativePath`. The embedded `Repository` does not carry `RemoteId` — Step 5a recovers it.

### `connection projects` response

`Data[]` — curated 5-column rows:

```json
{
  "ProjectId": "<PROJECT_SC_UUID>",
  "Name": "<my-project>",
  "Description": "",
  "Type": "Process",
  "Repository": "<my-repo>"
}
```

The curated view drops the full RepositoryDto and the project file's path. Step 5b recovers both. A project nested in a Solution can also appear here — the same project reached either way, with distinct ids (SourceControl project UUID vs the Studio `ProjectId` inside the Solution).

Server-side filters available: `--repository-ids <csv>`, `--project-type <type>`, `--target-framework <name>`, `--search <term>`, `--sort-by <field>` + `--sort-order <asc|desc>`. Azure connections additionally take `--azure-projects-ids <csv>` and `--organization-identifier <name>`.

### Decision

- **User named a Solution** → Step 5a
- **User named a name appearing only in `connection projects`** → Step 5b
- **User named a name appearing in both** → ask the user which kind of source they want
- **No user hint** → present a combined list (label each "Solution" or "Standalone project") and ask the user
- **Both responses empty** → no source visible to this connection. Check `uip aops connection state --connection <CONNECTION_ID> --output json` and offer `uip aops connection sync <CONNECTION_ID> --wait --output json`. If sync still yields nothing, the connection is empty or misconfigured

## Step 5a — Solution path: resolve source fields

The chosen `SolutionDto` carries most of what's needed, but its embedded `Repository` lacks `RemoteId`. One extra call:

```bash
uip aops connection repos <CONNECTION_ID> --output json
```

Find the row whose `Identifier` matches `solution.Repository.Identifier`. That row carries `RemoteId` (provider-native repo id).

List every entry in `solution.Projects[]`. `Type` values seen in practice: `Process`, `Library`, `TestCase`. **Do not filter by `Type`** — any project is eligible for source binding.

- **1 project** → use it
- **2+ projects** → ask the user, listing each `Type` and `ProjectRelativePath`
- **0 projects** → fail; tell the user to add a project to the Solution and re-sync the connection

Map fields:

| Variable | From |
|---|---|
| `REPOSITORY_ID` | matched repo's `RemoteId` (numeric for GitHub, UUID for Azure DevOps) — **NOT** `Identifier` |
| `REPOSITORY_URL` | `solution.Repository.CloneUrl` |
| `REPOSITORY_NAME` | `solution.Repository.Name` |
| `DEFAULT_BRANCH` | `solution.Repository.DefaultBranch` |
| `PROJECT_PATH` | `project.ProjectRelativePath` exactly |
| `PROJECT_NAME` | `""` (empty string — matches UI behavior) |

Skip to Step 6.

## Step 5b — Standalone-project path: resolve source fields

The curated views drop the data needed. Two calls fill the gaps:

```bash
uip aops connection repos <CONNECTION_ID> --output json
uip aops repo project-files <REPOSITORY_SC_UUID> --output json
```

### `connection repos` — full RepositoryDtos

```json
[
  {
    "Identifier": "<REPOSITORY_SC_UUID>",
    "Name": "<my-repo>",
    "CloneUrl": "https://github.com/<my-org>/<my-repo>.git",
    "RemoteId": "<provider-native-repo-id>",
    "CommitSha": "<sha>",
    "DefaultBranch": "main",
    "AzureProject": null
  }
]
```

Find the row whose `Name` matches the project's `Repository` field. Take `Identifier` (for the next call), `RemoteId`, `CloneUrl`, `Name`, `DefaultBranch`.

Azure DevOps connections spanning several projects / organizations: narrow with `--azure-projects-ids <csv>` (ids from `uip aops connection azure-projects <CONNECTION_ID> --output json`) and `--organization-identifier <name>`.

### `repo project-files` — the project file's path in the repo

```bash
uip aops repo project-files <REPOSITORY_SC_UUID> --output json
```

Takes the repository's **SourceControl UUID** (`Identifier`), NOT `RemoteId`. Returns one row per automation project file at the default branch's HEAD:

```json
[
  { "Name": "project.json", "Path": "project.json", "Type": "File", "BuildableUnitType": "Process" },
  { "Name": "project.json", "Path": "Libraries/Shared/project.json", "Type": "File", "BuildableUnitType": "Library" }
]
```

`Path` is `PROJECT_PATH`. Add `--reference <branch|tag|sha>` for a non-default branch.

- **1 row** → use its `Path`
- **2+ rows** → match against the project the user named; if still ambiguous, ask the user, listing each `Path` and `BuildableUnitType`
- **0 rows** → the repo has no automation project at that reference. Re-check the branch, or re-sync the connection

### `project get` — optional metadata confirmation

```bash
uip aops project get --project-id <PROJECT_ID> --output json
```

```json
{
  "Identifier": "<PROJECT_SC_UUID>",
  "Name": "<my-project>",
  "ConnectionIdentifier": "<CONNECTION_ID>",
  "ProjectVersion": "1.0.0",
  "Type": "Process",
  "TargetFramework": "Portable",
  "ExpressionLanguage": "CSharp",
  "Repository": "<my-repo>",
  "DefaultBranch": "main"
}
```

Confirms `Name`, `Type`, and `DefaultBranch`. `Repository` is a flattened name string — do not use it for any identifier. Optional flags: `--reference <ref>` to read the project at a non-default branch, `--with-branches` to add `AvailableBranches` (one extra round-trip).

Map fields:

| Variable | From |
|---|---|
| `REPOSITORY_ID` | matched repo's `RemoteId` — **NOT** `Identifier` |
| `REPOSITORY_URL` | matched repo's `CloneUrl` |
| `REPOSITORY_NAME` | matched repo's `Name` |
| `DEFAULT_BRANCH` | matched repo's `DefaultBranch` (agrees with `project get`'s `DefaultBranch`) |
| `PROJECT_NAME` | `""` (empty string — matches UI behavior) |
| `PROJECT_PATH` | `repo project-files` row's `Path` |

### Why `RemoteId` not `Identifier`?

`Identifier` is SourceControl's internal UUID. `RemoteId` is the provider's own repo id (numeric for GitHub, UUID for Azure DevOps). StudioAdmin's pipeline runtime resolves the repository via the provider's native id, not via the SourceControl index. Sending `Identifier` lets `pipeline create` return `Success`, but the resulting pipeline can't resolve its source — the UI flags it "connection no longer valid" even when the connection is healthy. Diff a UI-created pipeline's `repositoryId` against the `RemoteId` field of `connection repos` to confirm.

## Step 6 — Pick the already-published Orchestrator process

```bash
uip aops pipeline processes --output json
```

Row shape: `{ProcessId, Name, Description, Package, Version}`. This is the catalog of processes already deployed in Orchestrator — independent of any Studio project.

- **User named a process by `Name` or `Package`** → exact-match (case-insensitive). If 2+ rows share that `Name` / `Package` (different versions), prefer the highest semver `Version` and confirm with the user before picking.
- **No user name** → ask the user, listing each candidate's `Name`, `Package`, and `Version`.

Save: `PROCESS_ID`.

> The process is independent of the source project. A pipeline that builds project X can run process Y even when Y's source comes from a different repo. Do NOT auto-match.

## Step 7 — Inspect process arguments

```bash
uip aops pipeline process <PROCESS_ID> --output json
```

Read `Data.Arguments` (declared parameter schema) and `Data.InputArguments` (JSON-encoded string of default values). See [pipeline-dto-guide.md § arguments](pipeline-dto-guide.md#arguments) for the full inspect / infer / ask workflow.

If `pipeline process` errors or returns no arguments, fall back to `arguments: null` on the DTO — the pipeline will use whatever defaults the process declares server-side.

An unknown process id answers `Process <id> not found.` with exit 1 — re-run `pipeline processes` rather than retrying.

## Step 8 — (Optional) Verify a non-default branch exists

```bash
uip aops repo branches <REPOSITORY_SC_UUID> --output json
```

Rows are `{Name, Main}`. Takes the repository's SourceControl UUID. Skip this when using `DEFAULT_BRANCH` — that field is server-resolved and always exists. Only verify when the user named a specific branch.

## Output — identifiers needed for the PipelineDto

| Field on PipelineDto (camelCase) | Variable | Source |
|---|---|---|
| `connectionIdentifier` | `CONNECTION_ID` | Step 3 (`connection list` → `Identifier`) |
| `repositoryId` | `REPOSITORY_ID` | Step 5a / 5b — **`RemoteId`** (provider-native), NOT `Identifier` |
| `repositoryName` | `REPOSITORY_NAME` | Step 5a / 5b |
| `repositoryUrl` | `REPOSITORY_URL` | Step 5a / 5b |
| `repositoryType` | `"git"` | Server-normalized; safe to hard-code |
| `branch` | `DEFAULT_BRANCH` (or user-named) | Step 5a / 5b |
| `projectName` | `""` | Empty string — matches UI behavior |
| `projectPath` | `PROJECT_PATH` | Step 5a (`ProjectRelativePath`) / Step 5b (`repo project-files` → `Path`) |
| `processIdentifier` | `PROCESS_ID` | Step 6 |
| `arguments` | `PIPELINE_ARGUMENTS` or `null` | Step 7 |

Proceed to [pipeline-dto-guide.md](pipeline-dto-guide.md) for field-by-field composition.

## Error handling

| Failure | Recovery |
|---|---|
| `Unknown tool '@uipath/aops-tool'` | CLI registry index is stale — `uip update`, then retry. Do not fall back to `uip sc` / `uip cicd` |  <!-- uip-check-skip -->
| `connection list` returns 0 rows | Connections are UI-only — direct the user to the StudioAdmin web app to create one |
| `connection solutions` AND `connection projects` both empty | Check `connection state --connection <id>`; offer `connection sync <id> --wait`. If sync still yields nothing, the connection is empty / misconfigured |
| `--offset (N) must be a multiple of --limit (M)` | Client-side pagination guard. Use offsets of 0, M, 2M, … |
| `project get` 404s / `Project <id> not found.` | Project UUID stale — re-run `connection projects` (or re-sync) and pick again |
| `repo project-files` returns 0 rows | Wrong `--reference`, or the repo holds no automation project. Verify with `repo branches` |
| `pipeline processes` returns 0 candidates | No process is published in the active runtime environment. Direct the user to publish one first (`uip solution publish` — see `uipath-platform`) and re-run |
| `Not logged in.` on any verb | `uip login` and retry once |
| Failure naming the StudioAdmin SourceControl / CICD service | The organization lacks the service, or no runtime environment is selected. Both are fixed in the StudioAdmin UI — report to the user, do not retry |
