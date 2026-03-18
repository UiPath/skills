# CLI Tool Reference

Complete reference for all `uip` CLI commands and error recovery patterns.

**The CLI is fully self-documenting.** Append `--help` at any level to progressively discover commands, subcommands, and parameters:
```bash
uip --help                                  # top-level command groups
uip rpa --help                              # all rpa subcommands
uip rpa get-default-activity-xaml --help     # parameters for a specific command
uip is --help                               # Integration Service command groups
uip is connections --help                   # IS connections subcommands
uip is connections list --help              # parameters for a specific IS command
```

## Installed Package Activity Documentation (Primary Discovery)

Located at `{projectRoot}/.local/docs/packages/{PackageId}/`. See [Step 1.2](../SKILL.md#step-12-discover-activity-documentation-primary-source) for full details on structure, template, availability, and access patterns.

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Read activity doc directly** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` | Package ID + activity simple class name. **Preferred when you know both.** |
| **Read package overview** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/overview.md` | Package ID (e.g., `UiPath.WebAPI.Activities`) |
| **List documented packages** | `Bash`: `ls {projectRoot}/.local/docs/packages/` | Project root directory |
| **List documented activities of package** | `Bash`: `ls {projectRoot}/.local/docs/packages/{PackageId}/activities/` | Package ID |
| **Search activity docs by keyword** | `Grep` with pattern across `{projectRoot}/.local/docs/packages/` | Search pattern |

## Core RPA Workflow Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Explore project files** | `Glob` with `**/*.xaml` pattern, or `Bash`: `ls -la {projectRoot}` | Project root directory |
| **Find files by pattern** | `Glob` with pattern (e.g., `**/*Mail*.xaml`) | Glob pattern, path |
| **Search XAML content** | `Grep` with regex pattern across `.xaml` files | Pattern, file/directory path |
| **Read file contents** | `Read` tool | File path, offset, limit |
| **Read project definition** | `Read` tool on `{projectRoot}/project.json` | File path |
| **Explore object repository** | `Glob` `**/*` in `{projectRoot}/.objects/` + `Read` metadata files | `.objects/` path |
| **Get full project context** | `Read` project.json + `Read` XAML files + `Glob`/`Read` `.objects/` + `Read` `.settings/` | Combine multiple reads |
| **Search for activities** | `Bash`: `uip rpa find-activities --query "..." [--tags "..."] [--limit N] --format json` | `--query` (required), `--tags`, `--limit` (default 10) |
| **Get default activity XAML (non-dynamic)** | `Bash`: `uip rpa get-default-activity-xaml --activity-class-name "..."` | `--activity-class-name` (fully qualified) |
| **Get default activity XAML (dynamic)** | `Bash`: `uip rpa get-default-activity-xaml --activity-type-id "..." [--connection-id "..."]` | `--activity-type-id`, `--connection-id` (optional) |
| **List workflow examples** | `Bash`: `uip rpa list-workflow-examples --tags '["service1","service2"]' [--prefix "..."] [--limit N] --format json` | `--tags` (JSON array, required), `--prefix` (optional), `--limit` (default 10) |
| **Get workflow example** | `Bash`: `uip rpa get-workflow-example --key "path/to/example.xaml"` | `--key` (blob path from list results) |
| **Create new workflow file** | `Write` tool — create a new `.xaml` file with full XAML content | File path, XAML content |
| **Edit existing workflow** | `Edit` tool — exact string replacement in `.xaml` files | File path, old_string, new_string |
| **Get errors** | `Bash`: `uip rpa get-errors [--file-path "..."] [--skip-validation] --format json` | `--file-path` (relative to project dir), `--skip-validation` (use cached errors) |
| **Get JIT type definitions** | `Read` tool on `{projectRoot}/.project/JitCustomTypesSchema.json` | File path |
| **Install/update packages** | `Bash`: `uip rpa install-or-update-packages --packages '[{"id":"..."}]'` | `--packages` (JSON array; `version` optional — omit to auto-resolve latest) |
| **Run workflow** | `Bash`: `uip rpa run-file --file-path "..." [--input-arguments '...'] [--log-level ...]` | `--file-path` (required), `--input-arguments` (JSON), `--log-level` |

## Project Lifecycle Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Create new project** | `Bash`: `uip rpa new --name "..." [--template-id ...] [--location ...] [--expression-language ...] [--target-framework ...] [--description "..."]` | See [Creating New Projects](new-project-setup.md) |
| **Open project in Studio** | `Bash`: `uip rpa open-project [--project-dir "..."]` | `--project-dir` (optional) |
| **Close project** | `Bash`: `uip rpa close-project [--project-dir "..."]` | `--project-dir` (optional) |

## Studio Management Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **List Studio instances** | `Bash`: `uip rpa list-instances --format json` | (none) |
| **Start Studio** | `Bash`: `uip rpa start-studio` | (none) |
| **Focus activity in designer** | `Bash`: `uip rpa focus-activity [--activity-id "..."]` | `--activity-id` (IdRef; omit to focus all sequentially) |

## UI Automation Indication Tools

Use these when building UI Automation workflows to capture selectors into the Object Repository. See **[ui-automation.md](ui-automation.md)** for the full UIA workflow.

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Indicate application/screen** | `Bash`: `uip rpa indicate-application [--name "..."] [--parent-id "..." \| --parent-name "..."] [--activity-class-name "..."]` | `--name` (screen name in Object Repository), `--parent-id`/`--parent-name` (application ref) |
| **Indicate UI element** | `Bash`: `uip rpa indicate-element --name "..." --activity-class-name "..." [--parent-id "..." \| --parent-name "..."]` | `--name` (required), `--activity-class-name` (required, e.g. `UiPath.UIAutomation.Activities.TypeInto`), `--parent-id`/`--parent-name` (screen ref) |

**UI Automation indication workflow:**
1. First indicate the application/screen: `uip rpa indicate-application --name "MyApp"` — the user points at the application window
2. Then indicate individual elements within that screen: `uip rpa indicate-element --name "SubmitButton" --activity-class-name "UiPath.UIAutomation.Activities.ClickX" --parent-name "MyApp"` — the user points at the element
3. The indicated elements are stored in the Object Repository (`.objects/`) and can be referenced in XAML via their `ObjectRepositoryReference`
4. Read the resulting `.objects/` metadata to get the element IDs for use in workflow XAML

## Test Manager Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Get manual test cases** | `Bash`: `uip rpa get-manual-test-cases --format json` | (none) |
| **Get manual test steps** | `Bash`: `uip rpa get-manual-test-steps --format json` | (none) |

## Integration Service (IS) Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **List connectors** | `Bash`: `uip is connectors list [--filter "..."] --format json` | `--filter` (by name/key) |
| **Get connector details** | `Bash`: `uip is connectors get <connector-key> --format json` | `connector-key` (required) |
| **List connections** | `Bash`: `uip is connections list [connector-key] [--connection-id "..."] [--folder-key "..."] --format json` | `connector-key` (optional filter), `--connection-id`, `--folder-key` |
| **Create connection (OAuth)** | `Bash`: `uip is connections create <connector-key> [--no-browser]` | `connector-key` (required), opens OAuth flow |
| **Ping/verify connection** | `Bash`: `uip is connections ping <connection-id>` | `connection-id` (required) |
| **Edit/re-auth connection** | `Bash`: `uip is connections edit <connection-id>` | `connection-id` (required), opens OAuth flow |
| **List connector activities** | `Bash`: `uip is activities list <connector-key> --format json` | `connector-key` (required) |
| **List connector resources** | `Bash`: `uip is resources list <connector-key> [--operation ...] --format json` | `connector-key`, `--operation` (List/Retrieve/Create/Update/Delete/Replace) |
| **Describe resource schema** | `Bash`: `uip is resources describe <connector-key> <object-name> [--operation ...] --format json` | `connector-key`, `object-name`, `--operation` |
| **Execute resource CRUD** | `Bash`: `uip is resources execute <op> <connector-key> <object-name>` | Operations: `create`, `list`, `get`, `update`, `replace`, `delete` |

## CLI Error Recovery

When `uip` commands fail, diagnose by error category:

| Error Pattern | Cause | Recovery |
|---------------|-------|----------|
| `"connection refused"`, `"EPIPE"`, `"pipe not found"` | Studio IPC not available | Run `uip rpa start-studio`, then `uip rpa open-project --project-dir "..."` |
| `"timeout"`, `"ETIMEDOUT"` | Command took too long | Increase timeout: `uip rpa --timeout 600 <command>`, or use `--skip-validation` for `get-errors` |
| `"not authenticated"`, `401`, `403` | Auth required for cloud features | Run `uip login` and re-try |
| `"package not found"`, `"version not available"` | Wrong package ID or version | Verify package name via `uip rpa find-activities`; omit `version` to auto-resolve latest |
| `"project not found"`, `"no project open"` | Wrong project-dir or project not open | Verify `--project-dir` path, run `uip rpa open-project` |
| `"file not found"` in `get-errors` | Wrong `--file-path` (must be relative to project) | Use path relative to project root, not absolute |
| `"Studio is busy"`, `"operation in progress"` | Studio is processing a previous request | Wait a few seconds and retry the command |
| Any unrecognized error | Unknown | Check `--verbose` flag on parent: `uip rpa --verbose <command>` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.
