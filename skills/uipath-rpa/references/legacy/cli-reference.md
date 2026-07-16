# CLI Tool Reference

Complete reference for all `uip rpa-legacy` CLI commands and error recovery patterns.

**The CLI is fully self-documenting.** Append `--help` at any level to discover commands, subcommands, and parameters:
```bash
uip rpa-legacy --help                      # all rpa-legacy subcommands
uip rpa-legacy find-activities --help      # parameters for a specific command
uip rpa-legacy validate --help             # parameters for validate
```

**Key difference from `uip rpa`:** The `rpa-legacy` CLI is standalone — it does **not** require Studio Desktop IPC. It uses UiRobot directly for execution and resolves project dependencies independently.

---

## Path and Output Rules

- **Always use absolute paths** — store `{projectRoot}` at Phase 0, pass it to every command. **Never use `cd`.**
- **Always use `--output json`** for programmatic parsing (global option on all `uip` subcommands).
- **NEVER suppress stderr** (`2>/dev/null`) — error details are in the JSON output on stderr when exit code is non-zero.
- Check the `Result` field in output: `"Success"` or `"Failure"`.
- On failure, read `Message` and `Instructions` for diagnostics.

```
WRONG:  cd "C:/Projects/MyProject" && uip rpa-legacy validate . --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject" --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject/Main.xaml" --output json
```

---

## File Operations (Built-in Tools)

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Explore project files** | `Glob` with `**/*.xaml` pattern | Project root directory |
| **Find files by pattern** | `Glob` with pattern (e.g., `**/*Mail*.xaml`) | Glob pattern, path |
| **Search XAML content** | `Grep` with regex pattern across `.xaml` files | Pattern, file/directory path |
| **Read file contents** | `Read` tool | File path, offset, limit |
| **Read project definition** | `Read` tool on `{projectRoot}/project.json` | File path |
| **Create new workflow file** | `Write` tool — create a new `.xaml` file | File path, XAML content |
| **Edit existing workflow** | `Edit` tool — exact string replacement in `.xaml` files | File path, old_string, new_string |

---

## Activity Discovery Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Search for activities** | `Bash`: `uip rpa-legacy find-activities <project-path> --query "..." --output json` | `<project-path>` (required), `--query`, `--tags`, `--limit` (default 50) |
| **Search with type info** | `Bash`: `uip rpa-legacy find-activities <project-path> --query "..." --include-type-definitions --output json` | Adds full type definitions for argument types |
| **Inspect a .NET type** | `Bash`: `uip rpa-legacy type-definition <project-path> --type "FullyQualifiedTypeName" --output json` | `<project-path>` (required), `--type` (full or simple name) |
| **Search NuGet for packages** | `Bash`: `uip rpa-legacy find-package --query "..." --output json` | `--query` (required), `--limit` (default: 50) |

### find-activities

Searches for available activities in the project's installed NuGet dependencies. Returns activity names, arguments (in/out with types), **ready-to-use XAML snippet**, **xmlns declaration**, and optionally full type definitions.

**Always use the returned `XamlSnippet` as your starting point** for activity XAML instead of constructing from scratch. The snippet has correct element names, namespaces, and property names for the installed package version.

```bash
# Multi-word search (ranked by relevance)
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "Excel Read Range" --output json

# Exact match when you know the name
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "ReadRange" --exact --output json

# Find with type definitions (enums, classes)
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "invoke code" --include-type-definitions --output json
```

**Output per activity:**
```json
{
  "DisplayName": "SendMail",
  "ClassName": "SendMail",
  "Namespace": "UiPath.Mail.SMTP.Activities",
  "TypeFullName": "UiPath.Mail.SMTP.Activities.SendMail",
  "Arguments": [
    { "Name": "To", "Direction": "In", "Type": "String" },
    { "Name": "Result", "Direction": "Out", "Type": "String" }
  ],
  "XmlnsPrefix": "umsa",
  "XmlnsDeclaration": "xmlns:umsa=\"clr-namespace:UiPath.Mail.SMTP.Activities;assembly=UiPath.Mail.Activities\"",
  "XamlSnippet": "<umsa:SendMail\n    To=\"[toValue]\"\n    Result=\"[result]\" />"
}
```

With `--include-type-definitions`, output includes `TypeDefinitions` array with enum values, class properties, etc.

| Parameter | Description |
|-----------|-------------|
| `<project-path>` | Path to project.json or folder containing it (required, positional) |
| `--query <search>` | Filter activities by name, description, or category |
| `--tags <tags>` | Comma-separated category tags to filter by |
| `-l, --limit <count>` | Maximum results to return (default: 50) |
| `--include-type-definitions` | Include full type definitions for argument types (enums, classes, interfaces) |
| `--exact` | Only return activities whose ClassName or DisplayName exactly matches the query (case-insensitive) |

**Query tips:**
- **Multi-word queries work** with relevance scoring: `"Excel Read Range"` splits into words, scores matches independently, with bonuses when all words match
- **CamelCase boundaries detected**: `"SendHotkey"`, `"ExcelReadRange"` match correctly
- **Use `--exact`** when you know the exact activity name — avoids irrelevant results (e.g., `--query "If" --exact` returns only the WF4 If activity, not 17 unrelated matches)

### type-definition

Inspects any .NET type from the project's NuGet dependencies — enum values, properties, methods, constructors, and base types.

```bash
# Inspect an enum type
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "UiPath.Mail.Activities.MailFolder" --output json

# Inspect a class
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "System.Net.Mail.MailMessage" --output json
```

| Parameter | Description |
|-----------|-------------|
| `<project-path>` | Path to project.json or folder containing it (required, positional) |
| `--type <name>` | Full or simple name of the type to inspect |
| `--timeout <seconds>` | Timeout in seconds |

### find-package

Searches all configured NuGet feeds for packages by name or description. Use when known packages don't cover a capability.

```bash
uip rpa-legacy find-package --query "UiPath.Excel" --limit 10 --output json
uip rpa-legacy find-package --query "barcode" --output json
```

**Output per package:**
```json
{
  "Id": "UiPath.Excel.Activities",
  "Version": "2.24.4",
  "Description": "Excel automation activities",
  "Authors": "UiPath",
  "Source": "Official"
}
```

Activity packages (tagged `UiPathActivities`) are returned first. Searches all enabled v3 feeds in parallel.

| Parameter | Description |
|-----------|-------------|
| `--query <search>` | Search term to match against package name and description (required) |
| `-l, --limit <count>` | Maximum results (default: 50) |

After finding a package, add it to `dependencies` in project.json. Then `find-activities` will index its activities.

---

## Validation Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Validate file** | `Bash`: `uip rpa-legacy validate <xaml-path> --output json` | Single file validation |
| **Validate project** | `Bash`: `uip rpa-legacy validate <project-path> --output json` | Whole-project validation |

### validate

Checks a XAML workflow file or entire project for compilation errors — missing arguments, broken references, type mismatches.

Accepts: XAML file path, project.json path, or project folder path.

```bash
# Validate a specific file (use during iteration — one activity at a time)
uip rpa-legacy validate "C:/Projects/MyLegacyProject/Main.xaml" --output json

# Validate entire project (use before completing — final check)
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --output json

# Save results to file
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --result-path "C:/output/errors.json"
```

| Parameter | Description |
|-----------|-------------|
| `<path>` | XAML file, project.json, or project folder (required, positional) |
| `--result-path <path>` | Write validation results to a JSON file instead of stdout |

**Workflow:** Use per-file validation during development (faster, focused). Use project-level validation as a final step before completing the task.

---

## Package & Debug Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Package project (optional)** | `Bash`: `uip rpa-legacy pack <project-path> -o <output-dir>` | `<project-path>` (required), `-o` output dir |
| **Debug workflow** | `Bash`: `uip rpa-legacy debug <xaml-path>` | `<xaml-path>` (required), `-i` input args |

### pack

Packages an RPA project into a deployable `.nupkg` file. **Optional** — not required for debugging (legacy RPA can be debugged directly).

```bash
# Basic pack
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output"

# Pack with version
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0"

# Auto-version
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --auto-version

# With release notes
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0" --release-notes "Bug fixes and improvements"
```

| Parameter | Description |
|-----------|-------------|
| `<project-path>` | Path to the RPA project or project.json (required, positional) |
| `-o, --output <path>` | Output directory for the generated .nupkg |
| `-v, --version <version>` | Package version |
| `--auto-version` | Auto-generate package version |
| `--output-type <type>` | Force output type (Process\|Library\|Tests\|Objects) |
| `--split-output` | Split output into runtime and design libraries |
| `--repository-url <url>` | Source repository URL |
| `--repository-commit <sha>` | Source repository commit SHA |
| `--repository-branch <branch>` | Source repository branch |
| `--repository-type <type>` | Source repository type |
| `--project-url <url>` | Automation Hub project URL |
| `--release-notes <text>` | Release notes for the package |
| `--timeout <seconds>` | Timeout in seconds |

### debug

Executes a XAML workflow locally via UiRobot. Logs stream to console in real time. Returns structured JSON result with output arguments (success) or error diagnostics (failure).

**Always validate before debugging** — don't debug a file with compilation errors.

```bash
# Basic execution
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml"

# With input arguments
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx", "in_Count": 5}'

# Programmatic: suppress streaming logs, capture result to file
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" \
  -i '{"in_FilePath": "C:\\data.xlsx"}' \
  --result-path /tmp/result.json \
  --log-level error
```

| Parameter | Description |
|-----------|-------------|
| `<xaml-path>` | Full path to the XAML workflow file to execute (required, positional) |
| `-i, --input <json>` | Input arguments as a JSON string |
| `--result-path <path>` | Write full result JSON to file (persists after command exits) |
| `--timeout <seconds>` | Execution timeout in seconds (0 = no timeout); kills robot process if exceeded |
| `--robot-path <path>` | Path to UiRobot.exe (auto-detected if not provided) |
| `--log-level <level>` | Global log level: `debug\|info\|warn\|error` (default: info) |

**Exit codes:** 0 = success, 1 = failure.

**Success output:**
```json
{
  "Result": "Success",
  "Code": "RpaLegacyDebug",
  "Data": {
    "XamlPath": "C:\\MyProject\\Main.xaml",
    "Status": "Execution completed",
    "Output": { "out_Result": "Done", "out_RowCount": 42 }
  }
}
```
`Output` is only present when the workflow has Out arguments with values.

**Failure output:**
```json
{
  "Result": "Failure",
  "Message": "System.IO.FileFormatException: File contains corrupted data.",
  "Data": {
    "Error": {
      "ExceptionType": "System.IO.FileFormatException",
      "Message": "File contains corrupted data.",
      "ActivityDisplayName": "Read Stock Data",
      "ActivityType": "ReadRange",
      "XamlFile": "Main.xaml",
      "StackTrace": [
        "at ReadRange \"Read Stock Data\"",
        "at Sequence \"Initialize and Read Data\""
      ]
    },
    "ErrorLog": [
      {
        "Timestamp": "2026-03-21T16:30:37",
        "Level": "Error",
        "Message": "Read Stock Data: File contains corrupted data."
      }
    ]
  }
}
```

**Reading failure diagnostics:**
- `Error.ActivityDisplayName` + `Error.XamlFile` → locate the problem
- `Error.ExceptionType` + `Error.Message` → understand it
- `Error.StackTrace` → full call chain
- `ErrorLog` → all error-level robot log entries (useful when multiple things failed)

**Fix-and-retry loop:** edit XAML → validate → debug again.

**Caution:** `debug` executes the workflow — it performs real actions (clicks, emails, file writes). Only use when safe to run, or with mock input data.

---

## Documentation Search

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Search UiPath docs** | `Bash`: `uip docsai ask "your question" --output json` | `<query>` (required) |

### docsai ask

Searches official UiPath documentation and returns relevant answers including best practices, guidelines, troubleshooting steps, and configuration details. Use as a fallback when bundled activity reference docs and CLI discovery tools are insufficient.

```bash
# Best practices and guidelines
uip docsai ask "best practices for error handling in legacy UiPath workflows" --output json

# Troubleshooting
uip docsai ask "ExcelApplicationScope validation error ActivityAction body" --output json

# Platform concepts
uip docsai ask "Orchestrator queue item priority and deadline" --output json

# Configuration details
uip docsai ask "REFramework MaxRetryNumber and retry logic" --output json
```

| Parameter | Description |
|-----------|-------------|
| `<query>` | The question to ask (required, positional) |
| `-t, --tenant <tenant-name>` | Tenant (optional, defaults to auth value) |

**When to use:** Bundled activity docs and `find-activities`/`type-definition` don't cover the topic; you need best practices, guidelines, or troubleshooting from official UiPath documentation; you encounter an unfamiliar error.

**If docsai is also insufficient**, use `WebSearch` to search the broader community: UiPath Forum (`forum.uipath.com`), Stack Overflow, GitHub public repos, Reddit (`r/UiPath`). Always verify web-sourced information against the project's actual configuration before applying.

---

## CLI Error Recovery

When `uip rpa-legacy` commands fail, diagnose by error category:

| Error Pattern | Cause | Recovery |
|---------------|-------|----------|
| `"project not found"`, `"project.json not found"` | Wrong project path | Verify `<project-path>` points to the folder containing `project.json` |
| `"file not found"` | Wrong XAML path | Verify `<xaml-path>` is a full path to an existing `.xaml` file |
| `"package not found"`, `"version not available"` | Missing NuGet dependency | Ask the user to install the package in Studio, or check the NuGet feeds |
| `"not authenticated"`, 401, 403 | Auth required for cloud features | Run `uip login` and re-try |
| `"UiRobot not found"` | UiRobot.exe not installed or not in PATH | Pass `--robot-path` explicitly, or ask user to install UiPath Robot |
| `"timeout"`, `"ETIMEDOUT"` | Command took too long | Increase `--timeout` value |
| `"compilation error"` in validate | XAML has errors | Parse the error details, fix the XAML, re-validate |
| Any unrecognized error | Unknown | Use `--log-level debug` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

---

## Phase 0: Environment Readiness

**Goal:** Establish the project root and verify the project is a legacy framework project before any other operations.

**Key difference from modern (`uip rpa`):** The `uip rpa-legacy` CLI is standalone — it does **not** require Studio Desktop to be running. It resolves dependencies from NuGet directly and uses UiRobot for execution.

---

### Step 0.1: Establish Project Root

All `uip rpa-legacy` commands require a `<project-path>` argument pointing to the folder containing `project.json` (or the `project.json` file itself).

```bash
# Check if project.json exists in the CWD
ls {cwd}/project.json
```

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- Ask the user where their project is located if multiple `project.json` files are found

Store the project root path and use it consistently as `{projectRoot}` throughout all subsequent operations.

---

### Step 0.2: Verify Legacy Project

Read `project.json` and confirm this is a legacy framework project:

```
Read: file_path="{projectRoot}/project.json"
```

**Check these fields:**

| Field | Legacy Value | Notes |
|-------|-------------|-------|
| `targetFramework` | `"Legacy"` | May be absent in very old projects (pre-2021), which implies Legacy |
| `expressionLanguage` | `"VisualBasic"` (most common) or `"CSharp"` | Determines expression syntax in XAML |
| `studioVersion` | Typically `< 23.x` | Older Studio versions |
| `dependencies` | Classic package versions (no modern package IDs) | Very old projects (pre-2021) may have lower versions like ≤ 22.x |

**If `targetFramework` is `"Windows"` or `"Portable"`**, this is a modern project — use the `uipath-rpa` skill instead.

**If `targetFramework` is absent**, check the `studioVersion` and `dependencies` fields. Old projects without explicit `targetFramework` are Legacy by default.

---

### Step 0.3: Authentication (If Needed)

Some operations (cloud-based NuGet feeds, Orchestrator assets) may require authentication:

```bash
uip login
```

This opens a browser-based login flow. Authentication is typically needed only for:
- Projects that use private NuGet feeds requiring authentication
- `build` commands that push packages to Orchestrator
- Accessing Orchestrator resources (assets, queues) during `debug` execution

For most local development tasks (validate, edit, find-activities), authentication is **not required**.

---

### Step 0.4: Package Restore

After creating or modifying `project.json` dependencies, packages must be restored before `find-activities` or `type-definition` will work.

**Trigger restore** by running validate on the project directory:

```bash
uip rpa-legacy validate "{projectRoot}" --output json
```

This resolves NuGet packages from configured feeds. After this completes, `find-activities` and `type-definition` will have access to the package assemblies.

**If `find-activities` returns "No assemblies resolved from package dependencies"**, run validate first to trigger restore.

---

## Legacy Project Structure

Understanding the layout and configuration of a legacy UiPath RPA project.

---

### Directory Layout

```
{projectRoot}/
├── project.json              # Project metadata and dependencies
├── Main.xaml                 # Entry point workflow
├── *.xaml                    # Additional workflows (flat or in folders)
├── Workflows/                # (Optional) Sub-folder for organized workflows
├── Data/                     # (Optional) Input/output data files
├── .screenshots/             # (Optional) Studio screenshot captures
├── .settings/                # (Optional) Studio settings profiles
└── .tmh/                     # (Optional) Test Manager data
```

**Notable absences compared to modern projects:**
- No `.local/docs/packages/` — no auto-generated activity documentation
- No `.codedworkflows/` — no coded automation support
- No `.objects/` — no Object Repository
- No `.project/JitCustomTypesSchema.json` — no JIT custom types

---

### Creating a project.json from Scratch

#### Minimal Template

Start with this — only `UiPath.System.Activities` is required. Add other packages as needed.

```json
{
  "name": "MyProject",
  "description": "",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[24.10.8]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "25.10.0.0",
  "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic",
  "targetFramework": "Legacy",
  "runtimeOptions": {
    "autoDispose": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": true,
    "supportsPersistence": false,
    "workflowSerialization": "DataContract",
    "excludedLoggedData": ["Private:*", "*password*"],
    "executionType": "Workflow"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process"
  },
  "entryPoints": [
    {
      "filePath": "Main.xaml",
      "uniqueId": "00000000-0000-0000-0000-000000000000",
      "input": [],
      "output": []
    }
  ]
}
```

#### Package Selection Guide

**Add packages based on what the workflow needs.** Only `UiPath.System.Activities` is required — everything else is optional.

| Need | Package | Latest Legacy Version |
|------|---------|----------------------|
| **Core (always include)** | `UiPath.System.Activities` | **24.10.8** |
| UI automation (click, type, selectors) | `UiPath.UIAutomation.Activities` | **25.10.28** |
| Excel (read/write, macros, CSV) | `UiPath.Excel.Activities` | **2.24.4** |
| Email (SMTP, IMAP, POP3, Outlook) | `UiPath.Mail.Activities` | **1.24.18** |
| HTTP/REST/SOAP/JSON/XML | `UiPath.WebAPI.Activities` | **1.21.1** |
| Testing and assertions | `UiPath.Testing.Activities` | **25.10.1** |
| PDF (read text, OCR, merge, split) | `UiPath.PDF.Activities` | **3.25.2** |
| Office 365 (Graph API) | `UiPath.MicrosoftOffice365.Activities` | **2.9.13** |
| Word documents | `UiPath.Word.Activities` | **1.20.3** |
| PowerPoint presentations | `UiPath.Presentations.Activities` | **1.14.2** |
| Database (SQL queries) | `UiPath.Database.Activities` | **1.10.1** |
| Windows Credential Manager | `UiPath.Credentials.Activities` | **2.1.0** |
| FTP/SFTP file transfer | `UiPath.FTP.Activities` | **2.4.0** |
| Encryption/hashing (AES, HMAC, PGP) | `UiPath.Cryptography.Activities` | **1.6.1** |
| Python script execution | `UiPath.Python.Activities` | **1.10.0** |
| Java method invocation | `UiPath.Java.Activities` | **1.3.1** |
| Document Understanding/OCR | `UiPath.IntelligentOCR.Activities` | **6.27.3** |
| Forms (FormIo/HTML) | `UiPath.Form.Activities` | **2.0.8** |
| Terminal emulation (3270/5250/VT) | `UiPath.Terminal.Activities` | **2.9.0** |
| Google Suite (Gmail, Drive, Sheets) | `UiPath.GSuite.Activities` | **2.8.28** |
| NLP (sentiment, translation) | `UiPath.Cognitive.Activities` | **2.2.4** |
| StudioX scenario templates | `UiPath.ComplexScenarios.Activities` | **1.5.1** |
| OmniPage OCR engine | `UiPath.OmniPage.Activities` | **1.22.2** |
| Persistence (long-running workflows) | `UiPath.Persistence.Activities` | **1.8.1** |
| Mobile automation (iOS/Android) | `UiPath.MobileAutomation.Activities` | **25.10.0** |
| SAP BAPI function calls | `UiPath.SAP.BAPI.Activities` | **3.0.4** |

**Example:** A workflow that reads Excel, sends email, and calls a REST API needs:
```json
"dependencies": {
  "UiPath.System.Activities": "[24.10.8]",
  "UiPath.Excel.Activities": "[2.24.4]",
  "UiPath.Mail.Activities": "[1.24.18]",
  "UiPath.WebAPI.Activities": "[1.21.1]"
}
```

#### Packages Can Be Added Later

You don't need all packages upfront. Add them to `dependencies` as you discover what the workflow needs.

**Important:** `find-activities` only searches packages listed in `dependencies`. If you add a package to project.json, re-run `find-activities` to discover its activities.

#### Searching for Packages

When the known packages above don't cover a need, search configured NuGet feeds:

```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```

This searches all configured feeds (UiPath official + any custom feeds) by name and description. Add the discovered package to `dependencies`, then `find-activities` will index it.

#### Arbitrary .NET Packages

Any NuGet package can be added to `dependencies` for custom .NET classes, methods, and types. Examples:
- `CsvHelper` — advanced CSV parsing
- `ClosedXML` — .xlsx manipulation without COM
- `HtmlAgilityPack` — HTML parsing

Use these via `InvokeCode` with the appropriate namespace imports.

**Avoid adding packages already bundled with Studio** (e.g., `Newtonsoft.Json`) — version conflicts can cause runtime issues.

---

### project.json Key Fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used as package ID when packaged) |
| `main` | Entry point XAML file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `"VisualBasic"` (most legacy) or `"CSharp"` |
| `targetFramework` | `"Legacy"` for .NET Framework 4.6.1 projects |
| `designOptions.outputType` | `"Process"` (standalone) or `"Library"` (reusable) |
| `studioVersion` | Studio version that created the project |

#### Version Constraints

| Syntax | Meaning |
|--------|---------|
| `[1.2.3]` | Exact version 1.2.3 |
| `[1.2.3, )` | Minimum version 1.2.3 |
| `[1.0, 2.0)` | Range: >= 1.0, < 2.0 |

---

### Library Project Template

To create a **Library** project (reusable workflows published as a NuGet package), set `outputType` to `"Library"`:

```json
{
  "name": "Acme.Finance.InvoiceUtilities",
  "description": "Reusable invoice processing workflows",
  "dependencies": {
    "UiPath.System.Activities": "[24.10.8]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "25.10.0.0",
  "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic",
  "targetFramework": "Legacy",
  "runtimeOptions": {
    "autoDispose": false,
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false,
    "supportsPersistence": false,
    "workflowSerialization": "DataContract",
    "excludedLoggedData": ["Private:*", "*password*"],
    "executionType": "Workflow"
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Library"
  }
}
```

**Key differences from Process projects:**
- **No `main` field** — libraries have no entry point
- **No `entryPoints` array** — all workflows are callable individually
- **`outputType: "Library"`** — published as activity package, not deployed as process
- Workflows marked **Public** become activities when consumed; **Private** workflows are internal helpers

For full library design guidance (naming, versioning, patterns), see [project-organization-guide.md](./project-organization-guide.md).

---

## Discovery Workflow — Detailed Steps

Complete discovery procedure before writing or editing any XAML.

---

### Step 1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze: folder conventions, naming patterns, existing workflows, `expressionLanguage` (VB.NET or C#), installed packages (`dependencies`).

---

### Step 2: Consult Activity Reference Docs

Read `references/activity-docs/` for behavioral context (what activities do, gotchas, patterns).

| Situation | Action |
|-----------|--------|
| Know the package | Read `activity-docs/{PackageName}.md` directly |
| Don't know the package | Read `activity-docs/_INDEX.md` to find it |
| Need VB.NET expressions | Read `activity-docs/_PATTERNS.md` |
| Need XAML structure | Read `references/xaml-basics-and-rules.md` |
| Need gotchas | Read `activity-docs/_COMMON-PITFALLS.md` |
| Need InvokeCode patterns | Read `activity-docs/_INVOKE-CODE.md` |
| Working with REFramework | Read `activity-docs/_REFRAMEWORK.md` |
| Working with Document Understanding | Read `activity-docs/_DU-PROCESS.md` |
| Need all activities | Read `activity-docs/AllActivities.md` |

**These docs tell you what and how — NOT exact CLR property names/enum values for XAML. Steps 4 and 5 are mandatory for that.**

---

### Step 3: Search Current Project

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

Mature project: prioritize local patterns. Greenfield: skip.

---

### Step 4: Discover Activities (MANDATORY for non-built-in activities)

**Skip find-activities for built-in activities** listed in [_BUILT-IN-ACTIVITIES.md](./activity-docs/_BUILT-IN-ACTIVITIES.md): If, Assign, Sequence, TryCatch, Flowchart, ForEach, While, Switch, Throw, Delay, Parallel, LogMessage, InvokeCode, InvokeWorkflowFile, ForEachRow, AddDataRow. Use the provided XAML snippets directly.

**For all other activities**, run find-activities. Returns exact class names, argument signatures, types, **ready-to-use XAML snippet**, and **xmlns declaration**.

```bash
uip rpa-legacy find-activities "{projectRoot}" --query "send mail" --output json
uip rpa-legacy find-activities "{projectRoot}" --query "invoke code" --include-type-definitions --output json
```

**Use the returned `XamlSnippet` as your starting point** for activity XAML — it has correct element names, namespaces, and property names for the installed package version. Also add the returned `XmlnsDeclaration` to the root `<Activity>` element.

**Query syntax tips:**
- **Multi-word queries work** with relevance scoring: `"Excel Read Range"` splits into words, scores matches, bonuses when all words match
- **CamelCase boundaries detected**: `"SendHotkey"`, `"ExcelReadRange"` match correctly
- **Use `--exact`** when you know the exact activity name: `--query "ReadRange" --exact` — avoids irrelevant results
- Each call takes ~15-30 seconds — use `--exact` for known names to get precise results fast
- If a query returns too many irrelevant results, add `--exact` or use more specific terms

Activity reference docs describe behavior/gotchas but NOT exact CLR class names or argument types. Skipping this step → guessing → wasted validation cycles.

---

### Step 5: Inspect Types (MANDATORY for Enums/Complex Types)

**Run for every enum or complex type.** Gets exact valid values.

```bash
# Example: InvokeCode Language accepts VBNet and CSharp (NOT "VisualBasic" or "VB")
uip rpa-legacy type-definition "{projectRoot}" --type "NetLanguage" --output json

uip rpa-legacy type-definition "{projectRoot}" --type "System.Net.Mail.MailMessage" --output json
```

When to run: any enum property, any complex type argument, any type without listed valid values in docs.

---

### Step 5.5: Search NuGet for Packages (When Needed)

When the known packages in [project-structure.md](#legacy-project-structure) and `find-activities` don't cover a capability:

```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```

Searches all configured NuGet feeds by name and description. After finding the right package, add it to `dependencies` in project.json, then `find-activities` will index its activities.

Also works for arbitrary .NET packages (e.g., `CsvHelper`, `HtmlAgilityPack`). Avoid packages already bundled with Studio (e.g., `Newtonsoft.Json`) — version conflicts can cause issues.

---

### Step 6: Search UiPath Documentation (Fallback)

```bash
uip docsai ask "best practices for Excel automation in legacy projects" --output json
uip docsai ask "ExcelApplicationScope ActivityAction body validation error" --output json
```

Use when: bundled docs + CLI tools don't cover the topic, need best practices/guidelines/troubleshooting, unfamiliar error, platform concepts (Orchestrator, queues, triggers).

---

### Step 7: Search the Web (Last Resort)

Use `WebSearch` for UiPath Forum, Stack Overflow, GitHub, Reddit:

```
WebSearch: "UiPath forum ExcelApplicationScope ActivityAction body legacy"
WebSearch: "site:stackoverflow.com UiPath legacy ExcelApplicationScope XAML"
WebSearch: "site:github.com UiPath REFramework legacy XAML example"
```

Use when: all previous steps fail, obscure errors, community workarounds needed. Always verify web-sourced info against project config.

---

### Troubleshooting

#### Wrong enum value
**Symptom:** "Cannot create unknown type" or "is not a member of"
**Fix:** `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`

#### Activity class name not found
**Symptom:** Unknown activity type or missing namespace
**Fix:** `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, add xmlns + assembly ref

#### Multiple errors after batch editing
**Symptom:** Many errors at once
**Fix:** Revert to last good state. Re-add one activity at a time, validating after each.

#### Activity docs don't match XAML property names
**Symptom:** Properties from docs don't work
**Fix:** `find-activities --include-type-definitions` for exact CLR property names

#### Stuck on unfamiliar problem
**Escalation:** `docsai ask` → `WebSearch` → ask user

---

## Phase 3: Validate & Fix Loop

Detailed procedures for validating legacy workflows, analyzing project quality, and fixing errors iteratively.

---

### Step 3.1: Validate

Use `uip rpa-legacy validate` to check a XAML file or entire project for compilation errors. Accepts XAML file path, project.json path, or project folder.

```bash
# Validate a specific file (use during iteration — per activity)
uip rpa-legacy validate "{projectRoot}/Main.xaml" --output json

# Validate entire project (use as FINAL step before completing)
uip rpa-legacy validate "{projectRoot}" --output json
```

**Workflow:**
- **During iteration:** validate per-file after each activity edit (faster, focused feedback)
- **Before completing:** validate the entire project to catch cross-file issues
- Run after **every** XAML edit — do not batch multiple edits without validation

---

### Step 3.2: Categorize and Fix Errors

**Fix order:** Package → Structure → Type → Activity Properties → Logic. Always fix in this order — higher-category fixes often resolve lower-category errors automatically.

#### 1. Package Errors — Missing namespace, unknown activity type, unresolved assembly

**The legacy CLI does not have `install-or-update-packages`.** When a missing package is detected:
1. Identify the missing package from the error message
2. Check the [activity reference docs](./activity-docs/_INDEX.md) to confirm the correct package name
3. **Ask the user** to install the package manually in Studio:
   - Studio → Manage Packages → search for the package → Install
   - Or edit `project.json` dependencies directly (advanced — must match NuGet version constraints)
4. Re-validate after the package is installed

#### 2. Structural Errors — Invalid XML, malformed elements, missing closing tags

- `Read` the XAML around the error location → `Edit` to fix XML structure
- Cross-check against [xaml-basics-and-rules.md](./xaml-basics-and-rules.md) for correct element nesting and namespace declarations
- Common issues: unclosed elements, mismatched namespace prefixes, duplicate `x:Name` attributes

#### 3. Type Errors — Wrong property type, invalid cast, type mismatch

- **Always use `type-definition`** to discover exact enum values and type members — do not guess
  ```bash
  uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json
  ```
- Example: InvokeCode `Language` property accepts `VBNet` (not `VisualBasic`, not `VB`)
- Common fixes: wrong `x:TypeArguments`, missing namespace prefix (`sd:DataTable` vs `x:String`), VB vs C# expression syntax mismatch
- Consult activity reference docs for behavioral context, but rely on `type-definition` for exact values

#### 4. Activity Properties Errors — Unknown properties, misconfigured settings

- **Always use `find-activities --include-type-definitions`** to discover exact property names
  ```bash
  uip rpa-legacy find-activities "{projectRoot}" --query "activity name" --include-type-definitions --output json
  ```
- Activity reference docs describe behavior but may not list exact CLR property names — the CLI output is authoritative
- Common issues: properties that exist in modern but not legacy versions, misspelled property names, wrong enum values

#### 5. Logic Errors — Wrong behavior, incorrect expressions, business logic issues

- `Read` the XAML to understand current flow → `Edit` to correct
- Verify expression syntax matches project language (VB.NET vs C#)
- Consult [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md) for VB.NET expression patterns
- Use `uip rpa-legacy debug` for runtime validation if static checks pass

---

### Step 3.3: Iteration Loop

```
REPEAT:
  1. Run: uip rpa-legacy validate "{projectRoot}/{file}.xaml" --output json
  2. IF 0 errors → EXIT loop (success)
  3. IF errors exist:
     a. Categorize by type (Package/Structure/Type/Properties/Logic)
     b. Fix highest-category errors first
     c. Apply fix using Read + Edit tools
  4. IF error cannot be auto-resolved:
     a. Document the error for the user
     b. Suggest manual fix steps
     c. Continue fixing other errors
UNTIL: 0 errors OR all remaining errors require user action
```

**When stuck on one error:** Consider deferring to the user if it's a configuration detail (missing package, credential setup, connection string). Inform the user clearly about what needs to be done.

---

### Step 3.4: Package (Optional)

If a deployable `.nupkg` artifact is needed, package the project after validation passes:

```bash
uip rpa-legacy pack "{projectRoot}" -o "{outputDir}" --output json
```

Not required for debugging — legacy RPA can be debugged directly without packaging.

---

### Step 3.5: Smoke Test with Debug (Optional)

**Always validate before debugging** — don't debug a file with compilation errors.

```bash
# Basic smoke test
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --timeout 60

# Programmatic: capture result to file, suppress streaming logs
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --result-path /tmp/result.json --log-level error
```

**Reading results:**
- Exit code 0 → success: check `Data.Output` for out-argument values
- Exit code 1 → failure: check `Data.Error` for diagnostics:
  - `Error.ActivityDisplayName` + `Error.XamlFile` → locate the problem
  - `Error.ExceptionType` + `Error.Message` → understand it
  - `Error.StackTrace` → full call chain
  - `Data.ErrorLog` → all error-level log entries for context

**Fix-and-retry:** edit XAML → validate → debug again.

**Caution:** `debug` performs real actions (clicks, emails, file writes). Only use when safe.

For test data creation (Excel files, CSV, JSON, common UiPath types), see **[testing-guide.md § Test Data Creation](testing-guide.md#test-data-creation)**.

---

### Common Error Scenarios

#### Wrong enum value
**Symptom:** "Cannot create unknown type" or "is not a member of" for an enum property.
**Fix:** `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`. Example: InvokeCode `Language` accepts `VBNet` and `CSharp` — not `VisualBasic` or `VB`.

#### Activity class name not found
**Symptom:** Unknown activity type or missing namespace.
**Fix:** `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, add xmlns + assembly ref.

#### Multiple errors after batch editing
**Symptom:** Many errors after writing multiple activities at once.
**Fix:** Revert to last good state. Re-add one activity at a time, validating after each.

#### Activity docs don't match XAML property names
**Symptom:** Properties from reference docs don't work in XAML.
**Fix:** `find-activities --include-type-definitions` for exact CLR property names from compiled assemblies.

#### Stuck on unfamiliar problem
**Escalation:** `uip docsai ask "..."` → `WebSearch` (UiPath Forum, Stack Overflow, GitHub) → ask user.
