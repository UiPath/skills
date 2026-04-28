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
| **Package project (optional)** | `Bash`: `uip rpa-legacy package <project-path> -o <output-dir>` | `<project-path>` (required), `-o` output dir |
| **Debug workflow** | `Bash`: `uip rpa-legacy debug <xaml-path>` | `<xaml-path>` (required), `-i` input args |

### package

Packages an RPA project into a deployable `.nupkg` file. **Optional** — not required for debugging (legacy RPA can be debugged directly).

```bash
# Basic package
uip rpa-legacy package "C:/Projects/MyLegacyProject" -o "C:/output"

# Package with version
uip rpa-legacy package "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0"

# Auto-version
uip rpa-legacy package "C:/Projects/MyLegacyProject" -o "C:/output" --auto-version

# With release notes
uip rpa-legacy package "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0" --release-notes "Bug fixes and improvements"
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
