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
| `--no-auth` | no | Skip credential loading. Use for workflows that don't need Orchestrator/IS auth (the typical case for this skill, since HTTP/Connector activities are out of scope). |
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

- `uip api-workflow build`
- `uip api-workflow validate`
- `uip api-workflow publish`
- `uip api-workflow init`
- `uip apw <anything>` (no alias)

Build / publish go through `uip solution pack` / `uip solution publish`. Validation is done by running with `--no-auth`.
