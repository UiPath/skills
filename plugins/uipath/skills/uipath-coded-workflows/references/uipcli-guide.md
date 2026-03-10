# RPA Tool Guide

CLI reference for `rpa-tool` — communicates with UiPath Studio over named pipes (IPC).

> **Installation is automatic.** Do NOT attempt to install `rpa-tool` manually or instruct the user to install it.

> **This guide may not list every available command.** Run `rpa-tool --help` for the full list, and `rpa-tool <command> --help` for all flags on a specific command.

---

## Global Options

Every `rpa-tool` invocation accepts these flags:

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir <path>` | Project directory to match against running Studio instances | Current working directory |
| `--studio-dir <path>` | Path to Studio installation directory | Auto-detected (see below) |
| `--timeout <seconds>` | Timeout in seconds for Studio resolution | `300` |
| `--verbose` | Enable verbose/debug logging | Off |
| `--format <format>` | Output format: `json`, `table`, `yaml`, `plain` | `table` |

> **Always use `--format json`** when calling `rpa-tool` programmatically. The `table` format pads columns and can produce extremely large output (100KB+). JSON is compact and machine-readable.

### STUDIO_DIR Resolution

`--studio-dir` is optional — omit it by default and let `rpa-tool` auto-detect Studio. Only provide it explicitly if auto-detection fails, using the first match:

1. Environment variable `UIPATH_STUDIO_DIR` if set.
2. Default install: `C:\Program Files\UiPath\Studio` (or `x86` variant) if `UiPathStudio.exe` exists there.
3. Dev build: Studio source tree build output (e.g. `<repo-root>\Output\bin\Debug`).

> **Error `"Studio X.X.X does not have interop support"` or `"Requires Studio 26.2+"`** means the detected Studio is too old. Stop calling `rpa-tool` and inform the user to update Studio.

### PROJECT_DIR Resolution

`--project-dir` defaults to the current working directory. When the project is elsewhere, pass the absolute path to the folder containing `project.json`.

See **SKILL.md -> Quick Start -> Step 0** for the full resolution logic.

---

## Commands Reference

### list-instances

List running UiPath Studio instances and their IPC status.

```bash
rpa-tool list-instances --format json
```

No command-specific options.

---

### start-studio

Ensure a Studio instance is running. Resolution waterfall:
1. Match by `--project-dir` — reuse if available, wait if busy
2. Use an idle instance (no project loaded)
3. Start a new instance via `--studio-dir` — poll until available

```bash
rpa-tool start-studio --project-dir "<PROJECT_DIR>" --format json
```

---

### create-project

Create a new UiPath project from a template.

```bash
rpa-tool create-project --name "<NAME>" --location "<PARENT_DIR>" --format json
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--name` | Yes | — | Name of the project |
| `--location` | Yes | — | Parent directory where the project folder will be created |
| `--template-id` | No | `BlankTemplate` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--description` | No | — | Project description |
| `--expression-language` | No | — | `VisualBasic` or `CSharp` |
| `--target-framework` | No | — | `Legacy`, `Windows`, or `Portable` |

**Example response:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "success": true, "projectDirectory": "C:\\Projects\\MyAutomation", "errorMessage": "" }
}
```

---

### open-project

Open an existing project in Studio. Only needed when explicitly loading a project that isn't already open (e.g. after `create-project`, or when switching projects). Most commands (`validate`, `run-file`) auto-resolve a Studio instance, so this is rarely required.

```bash
rpa-tool open-project --project-dir "<PROJECT_DIR>" --format json
```

No command-specific options.

---

### validate

Validate a file or the entire project. Forces Studio to re-analyze the code.

```bash
rpa-tool validate --project-dir "<PROJECT_DIR>" --format json
rpa-tool validate --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--file-path` | No | — | File to validate (relative to project directory). If omitted, validates the whole project. |

**Example response — clean:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "status": "Valid", "errors": [] }
}
```

**Example response — with errors:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "status": "Valid",
    "errors": [
      { "file": "SendEmail.cs", "description": "; expected", "code": "CS1002", "severity": "Error" }
    ]
  }
}
```

- `errors` — empty array means the project compiles cleanly
- Each error: `file` (relative path), `description`, `code` (e.g. `CS0103`), `severity` (`"Error"`, `"Warning"`)

---

### run-file

Run a workflow file using Studio.

```bash
rpa-tool run-file --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | Yes | Path to the `.cs` workflow file to run |

**Example response:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "runResult": "{\"Output\":\"ProcessData execution started\\r\\nProcessing records...\\r\\nProcessData execution ended in: 00:00:02\\r\\n\",\"HasErrors\":false}"
  }
}
```

- `Data.runResult` is a **JSON string** (not an object) — parse it to get `Output` and `HasErrors`
- `HasErrors: false` = workflow ran successfully
- `HasErrors: true` = runtime error; details in `Output`

---

### get-manual-test-cases

Get unautomated test case IDs from Test Manager.

```bash
rpa-tool get-manual-test-cases --project-dir "<PROJECT_DIR>" --format json
```

No command-specific options.

---

### get-manual-test-steps

Get steps for specific test cases from Test Manager.

```bash
rpa-tool get-manual-test-steps --test-case-ids "id1,id2,id3" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-ids` | Yes | Comma-separated test case IDs |

---

### indicate-application

Open Studio's visual indicator for the user to point at an application window. Creates a **Screen** entry in the Object Repository under the specified AppVersion.

```bash
rpa-tool indicate-application --name "<SCREEN_NAME>" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | No (recommended) | Name for the new screen (e.g. `"LoginScreen"`, `"Dashboard"`) |
| `--parent-id` | No | AppVersion reference ID (from `.objects/<AppShortId>/<AppVersionShortId>/.metadata`). Prefer over `--parent-name`. |
| `--parent-name` | No | AppVersion name (e.g. `"1.0.0"`). Unreliable if names are non-unique. |
| `--activity-class-name` | No | Activity class (e.g. `"UiPath.UIAutomationNext.UI.App"`) |
| `--description` | No | Description for the screen |

When no App exists in `.objects/`, omit `--parent-id` and `--parent-name` — the command creates App + AppVersion automatically. When adding to an existing App, provide `--parent-id` with the **AppVersion** reference (not the App reference from `ObjectRepository.cs`).

**Example response:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "reference": "0CEMSOp5E0Cg_qEt2bfuIA/abc123..." }
}
```

After indication, Studio regenerates `ObjectRepository.cs`. Re-read it to get the descriptor path before writing workflow code.

---

### indicate-element

Open Studio's visual indicator for the user to point at a UI element. Creates an **Element** entry under an existing Screen. The screen must already exist.

```bash
rpa-tool indicate-element --name "<ELEMENT_NAME>" --parent-id "<SCREEN_REFERENCE>" --activity-class-name "<ACTIVITY_CLASS>" --project-dir "<PROJECT_DIR>" --format json
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | Yes | Name for the element (e.g. `"UsernameField"`, `"LoginButton"`) |
| `--parent-id` | One required | Screen reference ID (from `ObjectRepository.cs` or `indicate-application` result) |
| `--parent-name` | One required | Alternative — matches by screen name |
| `--activity-class-name` | Yes | Interaction type: `"TypeInto"`, `"Click"`, `"GetText"`, etc. |
| `--description` | No | Description for the element |

**Example response:**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "reference": "0CEMSOp5E0Cg_qEt2bfuIA/xyz789..." }
}
```

After indication, Studio regenerates `ObjectRepository.cs`. Re-read it to find the new descriptor path (e.g. `Descriptors.App.Screen.ElementName`) — Studio may normalize the name.
