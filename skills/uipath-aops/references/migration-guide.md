# Migration — `uip sc` + `uip cicd` → `uip aops`

`@uipath/sc-tool` (prefix `sc`) and `@uipath/cicd-tool` (prefix `cicd`) were unified into a single plugin, `@uipath/aops-tool` (prefix `aops`). `@uipath/cicd-tool` no longer exists on npm.

The merge kept every subcommand name. The rewrite is mechanical: replace the tool prefix, keep the rest.

```bash
uip sc   connection list --output json     →  uip aops connection list --output json
uip cicd pipeline create --file p.json     →  uip aops pipeline create --file p.json
```

## Install

```bash
uip tools install @uipath/aops-tool
uip tools list --output json
```

Confirm an entry with `"commandPrefix": "aops"`.

Known failure modes:

| Symptom | Cause | Action |
|---|---|---|
| `Unknown tool '@uipath/aops-tool'` | The installed CLI's registry index predates the tool | Update the CLI first (`uip update`), then retry the install. Report the CLI version (`uip --version`) to the user if it still fails. |
| `Unsupported URL Type "workspace:"` when installing `@uipath/sc-tool` | The last published `sc-tool` is a stale build with unresolved workspace dependencies | Do not install `sc-tool`. It is retired — install `aops-tool`. |

Do not fall back to `uip sc` / `uip cicd` when `aops` is unavailable. Report the install failure to the user instead.

## Verb map

Both old trees merged without collision — no verb was renamed, dropped, or moved to a different subject.

| Old | New |
|---|---|
| `uip sc connection list \| state \| sync \| delete` | `uip aops connection list \| state \| sync \| delete` |
| `uip sc connection repos \| repos-bulk \| projects \| solutions \| azure-projects` | `uip aops connection repos \| repos-bulk \| projects \| solutions \| azure-projects` |
| `uip sc repo branches \| project-files` | `uip aops repo branches \| project-files` |
| `uip sc project list \| get \| files \| content \| commits \| commit` | `uip aops project list \| get \| files \| content \| commits \| commit` |
| `uip sc solution get \| commits` | `uip aops solution get \| commits` |
| `uip cicd pipeline list \| state \| processes \| process \| repos \| get \| search` | `uip aops pipeline list \| state \| processes \| process \| repos \| get \| search` |
| `uip cicd pipeline create \| update \| delete \| run \| save-and-run` | `uip aops pipeline create \| update \| delete \| run \| save-and-run` |
| `uip cicd pipeline executions \| executions-bulk` | `uip aops pipeline executions \| executions-bulk` |
| `uip cicd execution get \| logs \| details \| stop` | `uip aops execution get \| logs \| details \| stop` |

## Behavior changes beyond the rename

These are the differences that break a command that used to work. Everything else — the `PipelineDto` / `EditPipelineDto` shapes, `repositoryId` = `RemoteId`, `projectName: ""`, `repositoryType: "git"`, the `PipelineRunMode` values — is unchanged.

### 1. Stdout `Data` keys are PascalCase

Every key inside the success envelope's `Data` is PascalCased on output: `identifier` → `Identifier`, `remoteId` → `RemoteId`, `syncState` → `SyncState`, `projectRelativePath` → `ProjectRelativePath`.

Input files are NOT transformed. A `--file` payload must use the DTO's own camelCase names. Capturing stdout and feeding it back is the single most common failure — `pipeline update` rejects it outright (see § 4).

To get a raw DTO on disk, use the command's `--output-file` flag, which writes the untransformed payload:

```bash
uip aops pipeline get <pipeline-id> --for-update --output-file ./edit.json --output json
```

### 2. `ConnectionType` is `Azure`, not `AzureDevOps`

`connection list` → `Type` is `"GitHub"` or `"Azure"`. Match on `"Azure"` when branching on provider.

### 3. `pipeline delete` requires explicit confirmation

```bash
uip aops pipeline delete <pipeline-id> --yes --output json
```

Without `-y` / `--yes` the command exits 1 with `Confirmation required: …` and sends no request. The CLI never prompts.

### 4. `pipeline update --file` rejects unrecognized keys

`update` is an HTTP PUT — a full replace. The serializer sends exactly five keys: `identifier`, `name`, `runMode`, `description`, `arguments`. Any other key in the file — including one that differs only in case, e.g. `Name` — is a `ValidationError` (exit 3) and nothing is sent. A file whose only key is `identifier` is rejected too ("carries no EditPipelineDto field to apply").

This gate exists because such a request used to succeed while silently clearing every field it failed to carry.

The supported round-trip:

```bash
uip aops pipeline get <pipeline-id> --for-update --output-file ./edit.json --output json
# edit ./edit.json — name / runMode / description / arguments only
uip aops pipeline update <pipeline-id> --file ./edit.json --output json
```

### 5. `--take` / `--skip` are deprecated, and absent on `pipeline executions`

`connection projects`, `connection solutions`, and `project list` still accept `--take` / `--skip` as hidden aliases and emit a deprecation warning. `pipeline list` and `pipeline executions` never had them — they take `--limit` / `--offset` only.

`--offset` must be an exact multiple of `--limit` on every paginated verb; otherwise the command fails client-side before any request.

| Verb | Default `--limit` |
|---|---|
| `connection projects`, `project list` | 10 |
| `connection solutions`, `pipeline list`, `pipeline executions` | 20 |
| `execution logs` | 200 (log-line page size) |

### 6. `--output-filter` requires an explicit `--limit`

`--output-filter` runs client-side over only the records the command fetched. When a filter is active and `--limit` resolved from its declared default, the CLI refuses to run rather than filter a silently capped page. Pass `--limit` explicitly:

```bash
uip aops pipeline list --search "my-pipeline" --limit 50 --output json --output-filter "Data[].PipelineId"
```

Commands with no declared `--limit` default — `pipeline create`, `pipeline save-and-run`, `pipeline get` — are unaffected:

```bash
uip aops pipeline save-and-run --file ./pipeline.json --output json --output-filter "Data.ExecutionId"
```

### 7. `repo project-files` closes the standalone `projectPath` gap

Previously the project file's path inside the repo had to be probed with `project content` or asked of the user. `repo project-files <repo-id>` now returns it directly:

```bash
uip aops repo project-files <REPOSITORY_SC_UUID> --output json
```

`Data[]` rows are `{Name, Path, Type, BuildableUnitType}`. `Path` is `PipelineDto.projectPath`. Takes the repository's SourceControl UUID (`Identifier` from `connection repos`), NOT `RemoteId`. `--reference <branch|tag|sha>` targets a non-default branch.

### 8. `--follow` / `--wait` timeout defaults

| Command | `--timeout` default | `--poll-interval` default |
|---|---|---|
| `execution logs --follow` | 1800000 (30 min) | 2000 |
| `execution stop --wait` | 300000 (5 min) | 2000 |
| `connection sync --wait` | 300000 (5 min) | 2000 |

Units live in the placeholder (`<ms>`) — there is no `--timeout-ms` flag.

### 9. `execution logs --follow` streams to stderr

With `--follow`, log lines are written to stderr as they arrive (shaped by `--output`), leaving stdout for the final envelope carrying the terminal state and line count. The stream is not subject to `--log-level` and is not captured by `--log-file`. Redirect stderr to keep it: `2> build.log`.

`--follow` requires the `<execution-id>` positional; `--job-key` alone is not enough because state polling is executionId-keyed.

## Do not confuse with `uip gov aops-policy`

Two unrelated product surfaces share the "AOps" name:

| Surface | Prefix | What it does | Skill |
|---|---|---|---|
| StudioAdmin AOps | `uip aops` | SourceControl connections, repos, projects, solutions; CICD pipelines and executions | this skill |
| AOps governance policies | `uip gov aops-policy` | Restrict / enforce Studio, StudioX, Assistant, Robot, AI Trust Layer features | `uipath-governance` |

If the request is about restricting what a product *can do*, it is a governance policy, not a pipeline.
