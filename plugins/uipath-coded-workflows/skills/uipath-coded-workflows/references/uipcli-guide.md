# RPA Tool Guide

This guide covers using the `rpa-tool` CLI for creating, managing, building, and running UiPath coded workflow projects via Studio IPC.

## Overview

The `rpa-tool` is a standalone CLI that communicates with UiPath Studio over named pipes (IPC).

> **This guide may not list every available command.** The tool evolves faster than this document. Before assuming a command doesn't exist, run `rpa-tool --help` to see the full list of commands, and `rpa-tool <command> --help` to see all flags for a specific command.

| Category | Commands |
|----------|----------|
| **Static** | `list-instances`, `start-studio` |
| **Local tools** | `create-project`, `open-project`, `run-file`, `validate`, `get-manual-test-cases`, `get-manual-test-steps` |
| **Dynamic (IPC)** | `indicate-application`, `indicate-element`, plus additional commands discovered from a running Studio instance |

---

## Prerequisites and Setup

### 1. Install Bun

Bun is the runtime used to build and run the rpa-tool. Install it if not already present:
```bash
powershell -c "irm bun.sh/install.ps1 | iex"
```

### 2. Install dependencies

```bash
cd RpaTool/rpa-tool
bun install
```

### 3. Build the tool

```bash
cd RpaTool/rpa-tool
bun run build
```

This produces two ESM bundles in `dist/`:
- `dist/tool.js` — plugin entry for the UiPath CLI
- `dist/index.js` — standalone CLI entry

### 4. Register the global command

```bash
cd RpaTool/rpa-tool
bun link
```

After this, `rpa-tool` is available as a global command from any directory.

### 5. Verify installation

```bash
rpa-tool --help
rpa-tool list-instances
```

---

## Global Options

Every `rpa-tool` invocation accepts these flags:

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir <path>` | Project directory to match against running Studio instances | Current working directory |
| `--studio-dir <path>` | Path to Studio installation directory (for starting a new instance) | Auto-detected |
| `--timeout <seconds>` | Timeout in seconds for Studio resolution | `300` |
| `--verbose` | Enable verbose/debug logging | Off |
| `--format <format>` | Output format: `json`, `table`, `yaml`, `plain` | `table` |

> **IMPORTANT: Always use `--format json`** when calling rpa-tool commands programmatically. The default `table` format pads columns to match the widest value, which can produce extremely large output (100KB+) for commands like `run-file`. JSON is compact and machine-readable.

---

## Variable Resolution Guide

**Two types of variables in this skill:**

### **Type 1: STUDIO_DIR — UiPath Studio Installation Directory**

`STUDIO_DIR` is the path to the UiPath Studio installation directory. Resolve it using one of these methods (first match wins):

1. **Environment variable** — If `UIPATH_STUDIO_DIR` is set, use its value.
2. **Default install location** — Check `C:\Program Files\UiPath\Studio` (or `C:\Program Files (x86)\UiPath\Studio`). If `UiPathStudio.exe` exists there, use that path.
3. **Dev build** — If working from a Studio source tree, use the build output directory (e.g. `<repo-root>\Output\bin\Debug`).
4. **Run without this parameter** — If none of the above resolves, run the command without the parameter and let the `rpa-tool` decide which Studio to use.

> **IMPORTANT** When encountering the error `"Studio X.X.X does not have interop support"` it means the auto-detected Studio is too old — passing `--studio-dir "<STUDIO_DIR>"` explicitly resolves this.

---

### **Type 2: YOU MUST RESOLVE (LLM responsibility)**

These variables YOU must determine before execution:

#### `PROJECT_DIR` - UiPath Project Directory

The absolute path to the root folder of a UiPath project (the folder that contains `project.json`).

See **SKILL.md → Quick Start → Step 0** for the full resolution logic (detect from running Studio, explicit path, project name, fallback to cwd).

**Example**: `C:\Projects\MyAutomation`

#### `WORKFLOW_NAME` - Name of the C# Workflow File

The filename (with `.cs` extension) of the coded workflow to create or reference.

**Step 1 — Determine the name** (use the first rule that matches):
1. **User provided a name** — Use it directly. Append `.cs` if the user omitted the extension.
2. **User described what the workflow does** — Derive a descriptive PascalCase name from the description (e.g., "process invoices" → `ProcessInvoices.cs`, "send email report" → `SendEmailReport.cs`).
3. **Neither name nor description given** — Infer a name from the workflow logic you are about to implement.

**Step 2 — Validate the name**:
- Must end with `.cs`.
- Must use PascalCase (e.g., `MyWorkflow.cs`, not `my_workflow.cs` or `myWorkflow.cs`).
- Must be unique within the project folder — check for existing files with the same name before creating.

**Example**: `ProcessSalesData.cs`

---

## Commands Reference

### list-instances

List running UiPath Studio instances and their IPC status.

```bash
rpa-tool list-instances [--format <format>]
```

**Options:**
- `--format` — Output format: `table` (default), `json`, `yaml`, `plain`

---

### start-studio

Ensure a Studio instance is running. Triggers the resolution waterfall:
1. Match by project directory — reuse if available, wait if busy
2. Use an idle instance (no project, available)
3. Start a new Studio instance — poll until available
```bash
rpa-tool start-studio --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

---

### create-project

Create a new UiPath project from a template.

```bash
rpa-tool create-project --name "<NAME>" --location "<PARENT_DIR>" --studio-dir "<STUDIO_DIR>" [--template-id <TEMPLATE>] [--description "<DESC>"] [--expression-language <LANG>] [--target-framework <FW>] --format json
```

**Parameters:**
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--name` | Yes | — | Name of the project |
| `--location` | Yes | — | Parent directory where the project folder will be created |
| `--template-id` | No | `BlankTemplate` | Template: `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` |
| `--description` | No | — | Project description |
| `--expression-language` | No | — | `VisualBasic` or `CSharp` |
| `--target-framework` | No | — | `Legacy`, `Windows`, or `Portable` |

**Example response (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "success": true, "projectDirectory": "C:\\Projects\\MyAutomation", "errorMessage": "" }
}
```

---

### open-project

Open an existing UiPath project in Studio. Use this when you need to explicitly open a project that isn't already loaded — for example, after creating a new project with `create-project`, or when switching to a different project directory. Most other commands (like `validate`, `run-file`) automatically resolve a Studio instance, so `open-project` is only needed when you want to ensure a specific project is open in Studio's UI.

```bash
rpa-tool open-project --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

---

### run-file

Run a workflow or coded file using Studio. This is the primary way to execute a workflow.

```bash
rpa-tool run-file --file-path "<FILE_PATH>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file-path` | Yes | Path to the `.cs` workflow file to run |

**Example:**
```bash
rpa-tool run-file --file-path "ProcessData.cs" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

**Example response (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "runResult": "{\"Output\":\"ProcessData execution started\\r\\nProcessing records...\\r\\nProcessData execution ended in: 00:00:02\\r\\n\",\"HasErrors\":false}"
  }
}
```

**Interpreting the result:**
- `Data.runResult` is a **JSON string** (not an object) — parse it to get `Output` and `HasErrors`
- `HasErrors: false` + `Result: "Success"` = workflow ran successfully
- `HasErrors: true` = runtime error occurred; the `Output` field contains the error details
- The `Output` field contains the Studio execution log (workflow logs, timing info)

---

### validate

Validates a file or the entire project. Forces Studio to re-analyze the code and returns a JSON result with validation status and any errors found.

```bash
rpa-tool validate [--file-path "<FILE_PATH>"] --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

**Parameters:**
| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--file-path` | No | — | Relative path of the file to validate (relative to project directory). If omitted, validates the whole project. |

**Usage:**
- After editing code, run `validate` to get accurate, up-to-date compilation results in a single call
- Can target a single file for faster feedback: `--file-path "MyWorkflow.cs"`
- Use in the validation loop: edit → validate → fix errors → validate again → repeat until clean (max 5 attempts)

**Example response — no errors (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "status": "Valid",
    "errors": []
  }
}
```

**Example response — with errors (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": {
    "status": "Valid",
    "errors": [
      {
        "file": "SendEmail.cs",
        "description": "; expected",
        "code": "CS1002",
        "severity": "Error"
      }
    ]
  }
}
```

**Interpreting the result:**
- `Data.status` — validation status (e.g. `"Valid"`)
- `Data.errors` — array of compilation errors; empty array means the project compiles cleanly
- Each error has: `file` (relative path), `description` (error message), `code` (e.g. `CS0103`), `severity` (e.g. `"Error"`, `"Warning"`)

---

### get-manual-test-cases

Get manual test cases from Test Manager (returns unautomated test case IDs).

```bash
rpa-tool get-manual-test-cases --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

---

### get-manual-test-steps

Get steps for specific test cases from Test Manager.

```bash
rpa-tool get-manual-test-steps --test-case-ids "id1,id2,id3" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

---

### indicate-application

Indicate an application window on screen using Studio's visual indicator. Creates a new **Screen** entry in the Object Repository under the specified AppVersion. The command opens Studio's indicator UI — the user must point at the application window to capture it.

```bash
rpa-tool indicate-application --name "<SCREEN_NAME>" --parent-id "<APP_VERSION_REFERENCE>" --activity-class-name "<ACTIVITY_CLASS>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | No | Name for the new screen (e.g. `"LoginScreen"`, `"Dashboard"`). Recommended. |
| `--parent-id` | No** | Reference ID of the **AppVersion** (from `.objects/<AppShortId>/<AppVersionShortId>/.metadata`). Prefer this over `--parent-name`. |
| `--parent-name` | No** | Alternative to `--parent-id` — matches by **AppVersion name** (e.g. `"1.0.0"`), NOT the App display name. Unreliable if AppVersion names are non-unique. |
| `--activity-class-name` | No | The activity class name for the application (e.g. `"UiPath.UIAutomationNext.UI.App"`) |
| `--description` | No | Optional description for the screen |

*`indicate-application` has no strictly required parameters — all are optional. However, `--name` is strongly recommended.
**When no App exists in `.objects/`, omit both `--parent-id` and `--parent-name` — the command creates the App + AppVersion automatically. When adding a screen to an existing App, provide `--parent-id` with the AppVersion reference (prefer over `--parent-name`).

> **`--parent-id` vs `--parent-name`:** Use `--parent-id` with the **AppVersion** reference, not the App reference. The App `_reference` field in `ObjectRepository.cs` is the App reference — read `.objects/<AppShortId>/<AppVersionShortId>/.metadata` to get the AppVersion reference.

**Example response (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "reference": "0CEMSOp5E0Cg_qEt2bfuIA/abc123..." }
}
```

After the user completes the indication, Studio regenerates `ObjectRepository.cs`. Re-read it to get the actual descriptor path before writing workflow code.

---

### indicate-element

Indicate a UI element on screen using Studio's visual indicator. Creates a new **Element** entry under an existing Screen in the Object Repository. The screen must already exist before adding elements to it.

```bash
rpa-tool indicate-element --name "<ELEMENT_NAME>" --parent-id "<SCREEN_REFERENCE>" --activity-class-name "<ACTIVITY_CLASS>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--name` | Yes | Name for the new element (e.g. `"UsernameField"`, `"LoginButton"`) |
| `--parent-id` | Yes* | Reference ID of the parent screen (from `ObjectRepository.cs` screen's `Reference` field, or from the `indicate-application` result) |
| `--parent-name` | Yes* | Alternative to `--parent-id` — matches by screen name. Works reliably for screens since screen names are unique and meaningful. |
| `--activity-class-name` | Yes | The activity class name for the element — use the interaction type: `"TypeInto"`, `"Click"`, `"GetText"`, etc. |
| `--description` | No | Optional description for the element |

*One of `--parent-id` or `--parent-name` is required.

**Example response (JSON):**
```json
{
  "Result": "Success",
  "Code": "ToolResult",
  "Data": { "reference": "0CEMSOp5E0Cg_qEt2bfuIA/xyz789..." }
}
```

After the user completes the indication, Studio regenerates `ObjectRepository.cs`. Re-read it to find the new descriptor path (e.g. `Descriptors.App.Screen.ElementName`) — Studio may normalize the name you requested.

---

## Build and Execution Workflow

### Standard Workflow

1. **Validate the file** (forces re-analysis and returns errors in one call)
   ```bash
   rpa-tool validate --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
   ```
   - Check the JSON response for errors. If errors exist, fix and re-validate until clean.

2. **Run the workflow**
   ```bash
   rpa-tool run-file --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
   ```

3. **Inspect the result**
   - Parse `Data.runResult` (it's a JSON string) to get `Output` and `HasErrors`
   - `HasErrors: false` = success; `HasErrors: true` = runtime error (details in `Output`)

### Iterative Development (Fix -> Validate -> Run Loop)

1. **Make code changes** (Edit tool)
2. **Validate the file**: `rpa-tool validate --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json`
3. If errors: fix and go back to step 2
4. **Run the workflow**: `rpa-tool run-file --file-path "<WORKFLOW_NAME>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json`
5. **Repeat** until workflow succeeds
