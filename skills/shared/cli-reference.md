# UiPath CLI (`uip rpa`) Reference

CLI reference for `uip rpa` -- communicates with UiPath Studio over named pipes (IPC).

> **Installation is automatic.** Do NOT attempt to install `uip` manually or instruct the user to install it.

> **This guide may not list every available command.** The CLI is self-documenting -- append `--help` at any level to progressively discover commands, subcommands, and parameters:

```bash
uip --help                              # top-level command groups
uip rpa --help                          # all rpa subcommands
uip rpa get-errors --help               # parameters for a specific command
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
| `--output <format>` | Output format: `json`, `table`, `yaml`, `plain` | `table` |

> **Always use `--output json`** when calling `uip rpa` commands programmatically. The `table` format pads columns and can produce extremely large output (100KB+). JSON is compact and machine-readable.

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
uip rpa list-instances --output json --use-studio
```

No command-specific options.

---

### start-studio

Ensure a Studio instance is running. Resolution waterfall:
1. Match by `--project-dir` -- reuse if available, wait if busy
2. Use an idle instance (no project loaded)
3. Start a new instance via `--studio-dir` -- poll until available

```bash
uip rpa start-studio --project-dir "<PROJECT_DIR>" --output json --use-studio
```

---

## Commands -- Project Lifecycle

### create-project

Create a new UiPath project from a template. Also available as `uip rpa new`.

```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --output json --use-studio
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
uip rpa open-project --project-dir "<PROJECT_DIR>" --output json --use-studio
```

No command-specific options.

---

## Commands -- Validation and Execution

### run-file

Run or debug a workflow file using Studio.

```bash
# Run (default -- closes app on completion or error):
uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio

# Debug (pauses on error -- keeps app open for inspection/repair):
uip rpa run-file --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --command StartDebugging --output json --use-studio
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
uip rpa get-errors [--file-path "<FILE>"] [--skip-validation] --output json --use-studio
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
uip rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities"}]' --output json --use-studio
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
uip rpa get-manual-test-cases --project-dir "<PROJECT_DIR>" --output json --use-studio
```

No command-specific options.

---

### get-manual-test-steps

Get steps for specific test cases from Test Manager.

```bash
uip rpa get-manual-test-steps --test-case-ids "id1,id2,id3" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-ids` | Yes | Comma-separated test case IDs |

---

## Commands -- Integration Service (IS)

All IS commands support `--output json`. The CLI is self-documenting: `uip is --help`, `uip is connections --help`, etc.

### connectors list

List available connectors, optionally filtered by name or key.

```bash
uip is connectors list --output json
uip is connectors list --filter "<NAME_OR_KEY>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--filter` | No | Filter by connector name or key |

---

### connectors get

Get details for a specific connector.

```bash
uip is connectors get <CONNECTOR_KEY> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |

---

### connections list

List connections, optionally filtered by connector.

```bash
uip is connections list --output json
uip is connections list <CONNECTOR_KEY> --output json
uip is connections list --connection-id "<ID>" --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | No | Filter by connector key (positional) |
| `--connection-id` | No | Filter by specific connection ID |
| `--folder-key` | No | Filter by folder key |

---

### connections create

Create a new connection via OAuth flow. Opens a browser for authentication.

```bash
uip is connections create <CONNECTOR_KEY>
uip is connections create <CONNECTOR_KEY> --no-browser
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `--no-browser` | No | Print the OAuth URL instead of opening a browser |

---

### connections ping

Verify a connection is alive and authenticated.

```bash
uip is connections ping <CONNECTION_ID>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connection-id>` | Yes | Connection ID (positional) |

---

### connections edit

Re-authenticate or edit an existing connection. Opens OAuth flow.

```bash
uip is connections edit <CONNECTION_ID>
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connection-id>` | Yes | Connection ID (positional) |

---

### activities list

List activities available for a connector.

```bash
uip is activities list <CONNECTOR_KEY> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |

---

### resources list

List resources available for a connector, optionally filtered by operation.

```bash
uip is resources list <CONNECTOR_KEY> --output json
uip is resources list <CONNECTOR_KEY> --operation List --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `--operation` | No | Filter by operation: `List`, `Retrieve`, `Create`, `Update`, `Delete`, `Replace` |

---

### resources describe

Get the schema for a specific resource object.

```bash
uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --output json
uip is resources describe <CONNECTOR_KEY> <OBJECT_NAME> --operation Create --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<connector-key>` | Yes | Connector key (positional) |
| `<object-name>` | Yes | Resource object name (positional) |
| `--operation` | No | Schema for a specific operation |

---

### resources execute

Execute a CRUD operation on a connector resource.

```bash
uip is resources execute <OPERATION> <CONNECTOR_KEY> <OBJECT_NAME> --output json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `<operation>` | Yes | One of: `create`, `list`, `get`, `update`, `replace`, `delete` |
| `<connector-key>` | Yes | Connector key (positional) |
| `<object-name>` | Yes | Resource object name (positional) |

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
