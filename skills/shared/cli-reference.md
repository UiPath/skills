# UiPath CLI (`uip rpa`) Reference

CLI reference for `uip rpa` -- communicates with UiPath Studio over named pipes (IPC).

> **Installation is automatic.** Do NOT attempt to install `uip` manually or instruct the user to install it.

> **This guide may not list every available command.** The CLI is self-documenting -- append `--help` at any level to progressively discover commands, subcommands, and parameters:

```bash
uip --help                              # top-level command groups
uip rpa --help                          # all rpa subcommands
uip rpa validate --help                 # parameters for a specific command
```

---

## Global Options

Every `uip rpa` invocation accepts these flags:

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir <path>` | Project directory to match against running Studio instances | Current working directory |
| `--studio-dir <path>` | Path to Studio installation directory | Auto-detected (see below) |
| `--timeout <seconds>` | Timeout in seconds for Studio resolution | `300` |
| `--verbose` | Enable verbose/debug logging | Off |
| `--format <format>` | Output format: `json`, `table`, `yaml`, `plain` | `table` |

> **Always use `--format json`** when calling `uip rpa` commands programmatically. The `table` format pads columns and can produce extremely large output (100KB+). JSON is compact and machine-readable.

### STUDIO_DIR Resolution

`--studio-dir` is optional -- omit it by default and let `uip` auto-detect Studio. Only provide it explicitly if auto-detection fails, using the first match:

1. Environment variable `UIPATH_STUDIO_DIR` if set.
2. Default install: `C:\Program Files\UiPath\Studio` (or `x86` variant) if `UiPathStudio.exe` exists there.
3. Dev build: Studio source tree build output (e.g. `<repo-root>\Output\bin\Debug`).

> **Error `"Studio X.X.X does not have interop support"` or `"Requires Studio 26.2+"`** means the detected Studio is too old. Stop calling `uip rpa` commands and inform the user to update Studio.

### PROJECT_DIR Resolution

`--project-dir` defaults to the current working directory. When the project is elsewhere, pass the absolute path to the folder containing `project.json`.

---

## Installed Package Activity Documentation

Located at `{projectRoot}/.local/docs/packages/{PackageId}/`.

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Read activity doc directly** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md` | Package ID + activity simple class name. **Preferred when you know both.** |
| **Read package overview** | `Read` tool on `{projectRoot}/.local/docs/packages/{PackageId}/overview.md` | Package ID (e.g., `UiPath.WebAPI.Activities`) |
| **List documented packages** | `Bash`: `ls {projectRoot}/.local/docs/packages/` | Project root directory |
| **List documented activities** | `Bash`: `ls {projectRoot}/.local/docs/packages/{PackageId}/activities/` | Package ID |
| **Search activity docs by keyword** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/` to list files, then `Read` matches. **Do not use `Grep`** -- `.local/` is gitignored and `Grep` skips it. | Glob pattern + Read |

---

## Commands -- Studio Management

### list-instances

List running UiPath Studio instances and their IPC status.

```bash
uip rpa list-instances --format json
```

No command-specific options.

---

### start-studio

Ensure a Studio instance is running. Resolution waterfall:
1. Match by `--project-dir` -- reuse if available, wait if busy
2. Use an idle instance (no project loaded)
3. Start a new instance via `--studio-dir` -- poll until available

```bash
uip rpa start-studio --project-dir "<PROJECT_DIR>" --format json
```

---

## Commands -- Project Lifecycle

### create-project

Create a new UiPath project from a template. Also available as `uip rpa new`.

```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --format json
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--name` | Yes | -- | Name of the project |
| `--location` | Yes | -- | Parent directory where the project folder will be created |
| `--template-id` | No | `BlankTemplate` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--description` | No | -- | Project description |
| `--expression-language` | No | -- | `VisualBasic` or `CSharp` |
| `--target-framework` | No | -- | `Legacy`, `Windows`, or `Portable` |

---

### open-project

Open an existing project in Studio. Only needed when explicitly loading a project that isn't already open (e.g. after `create-project`, or when switching projects). Most commands (`validate`, `run-file`) auto-resolve a Studio instance, so this is rarely required.

```bash
uip rpa open-project --project-dir "<PROJECT_DIR>" --format json
```

No command-specific options.

---

## Commands -- Validation and Execution

### validate

Validate a file or the entire project. Forces Studio to re-analyze the code.

```bash
uip rpa validate --project-dir "<PROJECT_DIR>" --format json
uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--file-path` | No | -- | File to validate (relative to project directory). If omitted, validates the whole project. |

`validate` forces re-analysis AND returns errors -- a single command for both. `get-errors` also re-validates by default (use `--skip-validation` for cached-only).

---

### run-file

Run or debug a workflow file using Studio.

```bash
# Run (default -- closes app on completion or error):
uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --format json

# Debug (pauses on error -- keeps app open for inspection/repair):
uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command StartDebugging --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | Yes | Path to the workflow file to run |
| `--command` | No | `StartExecution` (default) or `StartDebugging`. **Use `StartDebugging` for UI automation workflows** -- it pauses on error instead of tearing down the app, preserving the UI state for selector repair. Other debug commands: `Stop`, `StepInto`, `StepOver`, `StepOut`, `Continue`, `Break`, `ToggleBreakpoint`. |
| `--input-arguments` | No | JSON string of input arguments |
| `--log-level` | No | Logging verbosity level |

`Data.runResult` is a **JSON string** (not an object) -- parse it to get `Output` and `HasErrors`.

---

### get-errors

Return validation errors for a file or project. By default, forces Studio to re-validate before returning errors.

```bash
uip rpa get-errors [--file-path "<FILE>"] [--skip-validation] --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | No | File to check (relative to project directory). Omit to check the whole project. |
| `--skip-validation` | No | Return cached errors without re-validating (faster, but may be stale) |

---

## Commands -- Package Management

### install-or-update-packages

Install or update NuGet packages in the project.

```bash
uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]' --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--packages` | Yes | JSON array of objects with `id` and optional `version` |

Omit `version` to automatically resolve the latest compatible version (preferred). Only pin a specific version when there is a known compatibility constraint.

**Error recovery:**
- **Package not found** -- verify the exact package ID; use `--help` or activity docs to discover the correct name.
- **Network/feed error** -- check NuGet feed configuration in Studio settings.

---

## Commands -- Test Manager

### get-manual-test-cases

Get unautomated test case IDs from Test Manager.

```bash
uip rpa get-manual-test-cases --project-dir "<PROJECT_DIR>" --format json
```

No command-specific options.

---

### get-manual-test-steps

Get steps for specific test cases from Test Manager.

```bash
uip rpa get-manual-test-steps --test-case-ids "id1,id2,id3" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-ids` | Yes | Comma-separated test case IDs |

---

## Commands -- Integration Service (IS)

| Command | Description | Key Parameters |
|---------|-------------|----------------|
| `uip is connectors list` | List available connectors | `--filter` (by name/key) |
| `uip is connectors get <key>` | Get connector details | `connector-key` (required) |
| `uip is connections list [key]` | List connections | `connector-key` (optional filter), `--connection-id`, `--folder-key` |
| `uip is connections create <key>` | Create connection (OAuth) | `connector-key` (required), `--no-browser` |
| `uip is connections ping <id>` | Ping/verify connection | `connection-id` (required) |
| `uip is connections edit <id>` | Edit/re-auth connection | `connection-id` (required) |
| `uip is activities list <key>` | List connector activities | `connector-key` (required) |
| `uip is resources list <key>` | List connector resources | `--operation` (List/Retrieve/Create/Update/Delete/Replace) |
| `uip is resources describe <key> <obj>` | Describe resource schema | `--operation` |
| `uip is resources execute <op> <key> <obj>` | Execute resource CRUD | Operations: `create`, `list`, `get`, `update`, `replace`, `delete` |

All IS commands support `--format json`. The CLI is self-documenting: `uip is --help`, `uip is connections --help`, etc.

---

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
| Any unrecognized error | Unknown | Check `--verbose` flag: `uip rpa --verbose <command>` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.
