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
| **Search for activities** | `Bash`: `uip rpa-legacy find-activities <project-path> --query "..." --format json` | `<project-path>` (required), `--query`, `--tags`, `--limit` (default 50) |
| **Search with type info** | `Bash`: `uip rpa-legacy find-activities <project-path> --query "..." --include-type-definitions --format json` | Adds full type definitions for argument types |
| **Inspect a .NET type** | `Bash`: `uip rpa-legacy type-definition <project-path> --type "FullyQualifiedTypeName" --format json` | `<project-path>` (required), `--type` (full or simple name) |

### find-activities

Searches for available activities in the project's installed NuGet dependencies. Returns activity names, arguments (in/out with types), **ready-to-use XAML snippet**, **xmlns declaration**, and optionally full type definitions.

**Always use the returned `XamlSnippet` as your starting point** for activity XAML instead of constructing from scratch. The snippet has correct element names, namespaces, and property names for the installed package version.

```bash
# Find email-related activities
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "send mail" --format json

# Find with type definitions (enums, classes)
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "invoke code" --include-type-definitions --format json
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
| `--trace-level <level>` | Logging verbosity |

### type-definition

Inspects any .NET type from the project's NuGet dependencies — enum values, properties, methods, constructors, and base types.

```bash
# Inspect an enum type
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "UiPath.Mail.Activities.MailFolder" --format json

# Inspect a class
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "System.Net.Mail.MailMessage" --format json
```

| Parameter | Description |
|-----------|-------------|
| `<project-path>` | Path to project.json or folder containing it (required, positional) |
| `--type <name>` | Full or simple name of the type to inspect |
| `--trace-level <level>` | Logging verbosity |
| `--timeout <seconds>` | Timeout in seconds |

---

## Validation & Analysis Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Validate file** | `Bash`: `uip rpa-legacy validate <xaml-path> --format json` | Single file validation |
| **Validate project** | `Bash`: `uip rpa-legacy validate <project-path> --format json` | Whole-project validation |
| **Analyze project** | `Bash`: `uip rpa-legacy analyze <project-path> --format json` | Only when explicitly asked |

### validate

Checks a XAML workflow file or entire project for compilation errors — missing arguments, broken references, type mismatches.

Accepts: XAML file path, project.json path, or project folder path.

```bash
# Validate a specific file (use during iteration — one activity at a time)
uip rpa-legacy validate "C:/Projects/MyLegacyProject/Main.xaml" --format json

# Validate entire project (use before completing — final check)
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --format json

# Strict mode: treat warnings as errors
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --treat-warnings-as-errors --format json

# Save results to file
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --result-path "C:/output/errors.json"
```

| Parameter | Description |
|-----------|-------------|
| `<path>` | XAML file, project.json, or project folder (required, positional) |
| `--treat-warnings-as-errors` | Treat warnings as errors |
| `--result-path <path>` | Write validation results to a JSON file instead of stdout |
| `--trace-level <level>` | Logging verbosity |

**Workflow:** Use per-file validation during development (faster, focused). Use project-level validation as a final step before completing the task.

### analyze

Runs workflow analyzer rules on an entire RPA project and reports violations (unused dependencies, naming conventions, best practices).

**Only run when explicitly requested by the user.** Not part of the standard validation loop.

```bash
# Analyze entire project
uip rpa-legacy analyze "C:/Projects/MyLegacyProject" --format json

# Strict mode: fail on any violation
uip rpa-legacy analyze "C:/Projects/MyLegacyProject" --stop-on-rule-violation --format json

# Skip specific rules
uip rpa-legacy analyze "C:/Projects/MyLegacyProject" --ignored-rules "ST-NMG-001,ST-NMG-002" --format json

# Use governance policies
uip rpa-legacy analyze "C:/Projects/MyLegacyProject" --governance-file-path "C:/policies/governance.json" --format json
```

| Parameter | Description |
|-----------|-------------|
| `<project-path>` | Path to the RPA project or project.json (required, positional) |
| `--analyzer-trace-level <level>` | Message types to output (Off\|Error\|Warning\|Info\|Verbose) |
| `--stop-on-rule-violation` | Fail the command when a rule violation is detected |
| `--treat-warnings-as-errors` | Treat warnings as errors during analysis |
| `--result-path <path>` | Output file path for analysis results (JSON) |
| `--governance-file-path <path>` | Path to governance policies file (from Automation Ops) |
| `--ignored-rules <rules>` | Comma-separated list of rule IDs to skip |
| `--trace-level <level>` | Legacy CLI logging level (default: Information) |
| `--timeout <seconds>` | Timeout in seconds |

---

## Build & Debug Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Build project** | `Bash`: `uip rpa-legacy build <project-path> -o <output-dir>` | `<project-path>` (required), `-o` output dir |
| **Debug workflow** | `Bash`: `uip rpa-legacy debug <xaml-path>` | `<xaml-path>` (required), `-i` input args |

### build

Compiles and packages an RPA project into a deployable `.nupkg` file.

```bash
# Basic build
uip rpa-legacy build "C:/Projects/MyLegacyProject" -o "C:/output"

# Build with version
uip rpa-legacy build "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0"

# Auto-version build
uip rpa-legacy build "C:/Projects/MyLegacyProject" -o "C:/output" --auto-version

# Build with release notes
uip rpa-legacy build "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0" --release-notes "Bug fixes and improvements"
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
| `--trace-level <level>` | Legacy CLI logging level (default: Information) |
| `--timeout <seconds>` | Timeout in seconds |

### debug

Executes a XAML workflow locally via UiRobot and returns execution logs and output arguments.

```bash
# Run a workflow
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml"

# Run with input arguments
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" -i '{"in_Name": "John", "in_Count": 5}'

# Run with timeout and verbose logging
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" --timeout 120 --trace-level Verbose

# Save output arguments to file
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" --result-path "C:/output/result.json"
```

| Parameter | Description |
|-----------|-------------|
| `<xaml-path>` | Full path to the XAML workflow file to execute (required, positional) |
| `-i, --input <json>` | Input arguments as a JSON string |
| `--result-path <path>` | Write execution output (out arguments) to a JSON file instead of stdout |
| `--timeout <seconds>` | Execution timeout in seconds (0 = no timeout) |
| `--robot-path <path>` | Path to UiRobot.exe (auto-detected if not provided) |
| `--trace-level <level>` | Logging verbosity (None\|Critical\|Error\|Warning\|Information\|Verbose) |

**Caution:** `debug` executes the workflow — it will perform real actions (click buttons, send emails, modify files). Use only when safe to run, or with mock input data.

---

## Documentation Search

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Search UiPath docs** | `Bash`: `uip docsai ask "your question" --format json` | `<query>` (required) |

### docsai ask

Searches official UiPath documentation and returns relevant answers including best practices, guidelines, troubleshooting steps, and configuration details. Use as a fallback when bundled activity reference docs and CLI discovery tools are insufficient.

```bash
# Best practices and guidelines
uip docsai ask "best practices for error handling in legacy UiPath workflows" --format json

# Troubleshooting
uip docsai ask "ExcelApplicationScope validation error ActivityAction body" --format json

# Platform concepts
uip docsai ask "Orchestrator queue item priority and deadline" --format json

# Configuration details
uip docsai ask "REFramework MaxRetryNumber and retry logic" --format json
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
| Any unrecognized error | Unknown | Use `--trace-level Verbose` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.
