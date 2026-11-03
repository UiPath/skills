# CLI Tool Reference

Reference for `uip rpa-legacy` commands and recovery. `rpa-legacy` is standalone, requires no Studio Desktop IPC, uses UiRobot, and resolves dependencies independently.

Sections: [Path and Output Rules](#path-and-output-rules) · [File Operations](#file-operations-built-in-tools) · [Activity Discovery Tools](#activity-discovery-tools) · [Validation Tools](#validation-tools) · [Package & Debug Tools](#package--debug-tools) · [Documentation Search](#documentation-search) · [CLI Error Recovery](#cli-error-recovery) · [Phase 0: Environment Readiness](#phase-0-environment-readiness) · [Legacy Project Structure](#legacy-project-structure) · [Discovery Workflow](#discovery-workflow--detailed-steps) · [Phase 3: Validate & Fix Loop](#phase-3-validate--fix-loop)

The CLI is self-documenting: append `--help` at any level:
```bash
uip rpa-legacy --help
uip rpa-legacy find-activities --help
uip rpa-legacy validate --help
```

## Path and Output Rules

- Always use absolute paths, store `{projectRoot}` at Phase 0, pass it to every command, and never use `cd`.
- Always use `--output json` for programmatic parsing; it is global on all `uip` subcommands.
- **NEVER suppress stderr** (`2>/dev/null`) — error details are in the JSON output on stderr when exit code is non-zero.
- Check `Result` (`"Success"` or `"Failure"`); on failure read `Message` and `Instructions`.

Use paths directly:
```bash
WRONG:  cd "C:/Projects/MyProject" && uip rpa-legacy validate . --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject" --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject/Main.xaml" --output json
```

## File Operations (Built-in Tools)

| Action | Tool and parameters |
|---|---|
| Explore project files | `Glob`, `**/*.xaml`, project root |
| Find files by pattern | `Glob`, e.g. `**/*Mail*.xaml`, pattern and path |
| Search XAML | `Grep`, regex across `.xaml` files, path/file |
| Read contents | `Read`, file path, offset, limit |
| Read project definition | `Read`, `{projectRoot}/project.json` |
| Create workflow | `Write`, new `.xaml` path and XAML content |
| Edit workflow | `Edit`, exact `old_string`/`new_string` replacement in `.xaml` |

## Activity Discovery Tools

| Command | Required/options |
|---|---|
| `uip rpa-legacy find-activities <project-path> --query "..." --output json` | `<project-path>` required; `--query`, `--tags`, `--limit` (default 50) |
| `uip rpa-legacy find-activities <project-path> --query "..." --include-type-definitions --output json` | Adds full argument type definitions |
| `uip rpa-legacy type-definition <project-path> --type "FullyQualifiedTypeName" --output json` | `<project-path>` required; `--type` full or simple name; `--timeout <seconds>` |
| `uip rpa-legacy find-package --query "..." --output json` | `--query` required; `--limit` (default: 50) |

### find-activities

Search installed NuGet dependencies. It returns activity names, typed in/out arguments, `XamlSnippet`, `XmlnsDeclaration`, and optional `TypeDefinitions`. Always start with returned `XamlSnippet`, add `XmlnsDeclaration` to root `<Activity>`, and never construct activity XAML from scratch.

`<project-path>` is a required positional project folder or `project.json`; `--query <search>` filters name/description/category; `--tags <tags>` is comma-separated; `-l, --limit <count>` defaults to 50; `--include-type-definitions` includes enums/classes/interfaces; `--exact` returns case-insensitive exact `ClassName`/`DisplayName` matches. Queries support relevance-scored multi-word matching and CamelCase boundaries. `TypeDefinitions` includes enum values, class properties, and related type information.

```bash
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "Excel Read Range" --output json
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "ReadRange" --exact --output json
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "invoke code" --include-type-definitions --output json
```

Output includes fields such as:
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

### type-definition

Inspect any .NET type from project NuGet dependencies for enum values, properties, methods, constructors, and base types. Run it for every enum or complex type and whenever docs do not list valid values.

```bash
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "UiPath.Mail.Activities.MailFolder" --output json
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "System.Net.Mail.MailMessage" --output json
```

### find-package

Search configured NuGet feeds by name/description; `UiPathActivities` packages appear first and enabled v3 feeds are searched in parallel. Add the selected package to `dependencies` in `project.json`, then run `find-activities`.

```bash
uip rpa-legacy find-package --query "UiPath.Excel" --limit 10 --output json
uip rpa-legacy find-package --query "barcode" --output json
```

Output fields: `Id`, `Version`, `Description`, `Authors`, `Source`. `--query <search>` is required; `-l, --limit <count>` defaults to 50.

## Validation Tools

| Action | Command |
|---|---|
| Validate file | `uip rpa-legacy validate <xaml-path> --output json` |
| Validate project | `uip rpa-legacy validate <project-path> --output json` |

`validate` accepts a XAML file, `project.json`, or project folder and checks compilation errors, including missing arguments, broken references, and type mismatches. Validate the file during iteration and the project before completion.

```bash
uip rpa-legacy validate "C:/Projects/MyLegacyProject/Main.xaml" --output json
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --output json
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --result-path "C:/output/errors.json"
```

`<path>` is required; `--result-path <path>` writes JSON results instead of stdout.

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

**Caution:** `debug` executes the workflow — it performs real actions (clicks, emails, file writes). Only use when safe to run, or with mock input data.

Success output:
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

`Output` appears only when Out arguments have values. Failure output contains `Result: "Failure"`, `Message`, and `Data.Error` fields `ExceptionType`, `Message`, `ActivityDisplayName`, `ActivityType`, `XamlFile`, `StackTrace`, plus `Data.ErrorLog` entries with `Timestamp`, `Level`, and `Message`. Use `Error.ActivityDisplayName` + `Error.XamlFile` to locate the problem, `Error.ExceptionType` + `Error.Message` to understand it, `Error.StackTrace` for the call chain, and `ErrorLog` for error-level robot entries. Fix and retry: edit XAML → validate → debug again.

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

**If docsai is also insufficient**, use `WebSearch` to search the broader community: UiPath Forum (`forum.uipath.com`), Stack Overflow, GitHub public repos, Reddit (`r/UiPath`). **Always** verify web-sourced information against the project's actual configuration before applying.

## CLI Error Recovery

| Error | Cause | Recovery |
|---|---|---|
| `"project not found"`, `"project.json not found"` | Wrong project path | Verify `<project-path>` points to the folder containing `project.json` |
| `"file not found"` | Wrong XAML path | Verify `<xaml-path>` is a full path to an existing `.xaml` |
| `"package not found"`, `"version not available"` | Missing NuGet dependency | Ask the user to install it in Studio or check NuGet feeds |
| `"not authenticated"`, 401, 403 | Cloud authentication | Run `uip login` and retry |
| `"UiRobot not found"` | UiRobot.exe absent/not in PATH | Pass `--robot-path` or ask the user to install UiPath Robot |
| `"timeout"`, `"ETIMEDOUT"` | Command too slow | Increase `--timeout` |
| `"compilation error"` in validate | XAML errors | Parse details, fix XAML, re-validate |
| Unrecognized error | Unknown | Use `--log-level debug`, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

## Phase 0: Environment Readiness

Before other operations, establish `{projectRoot}` and verify a Legacy framework project. `rpa-legacy` is standalone, requires no Studio Desktop, resolves NuGet dependencies directly, and uses UiRobot.

### Step 0.1: Establish Project Root

All commands require `<project-path>` pointing to the folder containing `project.json` or the file itself. Run:
```bash
ls {cwd}/project.json
```
If needed, locate it with `Glob: pattern="**/project.json"`; ask the user when multiple project files are found. Store the root as `{projectRoot}` and use it consistently.

### Step 0.2: Verify Legacy Project

Read:
```
Read: file_path="{projectRoot}/project.json"
```

Check `targetFramework` is `"Legacy"` (it may be absent in pre-2021 projects, implying Legacy); `expressionLanguage` is `"VisualBasic"` or `"CSharp"`; `studioVersion` is typically `< 23.x`; and `dependencies` use classic package versions (pre-2021 versions may be `≤ 22.x`). If `targetFramework` is `"Windows"` or `"Portable"`, use the `uipath-rpa` skill. If absent, use `studioVersion` and `dependencies` to confirm Legacy.

### Step 0.3: Authentication (If Needed)

Run `uip login` when private NuGet feeds, `build` commands that push packages to Orchestrator, or Orchestrator assets/queues during `debug` require authentication. It opens a browser-based login flow. For most local development tasks (validate, edit, find-activities), authentication is **not required**.

### Step 0.4: Package Restore

After creating or modifying `project.json` dependencies, packages must be restored before `find-activities` or `type-definition` will work.

**Trigger restore** by running validate on the project directory:
```bash
uip rpa-legacy validate "{projectRoot}" --output json
```
This resolves NuGet packages from configured feeds. After this completes, `find-activities` and `type-definition` will have access to the package assemblies.

**If `find-activities` returns "No assemblies resolved from package dependencies"**, run validate first to trigger restore.

## Legacy Project Structure

### Directory Layout

```text
{projectRoot}/
├── project.json
├── Main.xaml
├── *.xaml
├── Workflows/
├── Data/
├── .screenshots/
├── .settings/
└── .tmh/
```

Optional directories are `Workflows/`, `Data/`, `.screenshots/`, `.settings/`, and `.tmh/`. Legacy has no `.local/docs/packages/`, `.codedworkflows/`, `.objects/`, or `.project/JitCustomTypesSchema.json`.

### Creating a project.json from Scratch

Start with this minimal template; only `UiPath.System.Activities` is required:
```json
{
  "name": "MyProject",
  "description": "",
  "main": "Main.xaml",
  "dependencies": { "UiPath.System.Activities": "[24.10.8]" },
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
  "designOptions": { "projectProfile": "Developement", "outputType": "Process" },
  "entryPoints": [{ "filePath": "Main.xaml", "uniqueId": "00000000-0000-0000-0000-000000000000", "input": [], "output": [] }]
}
```

Add packages only as needed:

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

Packages may be added later. `find-activities` searches only `dependencies`; after adding one, run it again. If known packages do not cover a capability, run `uip rpa-legacy find-package --query "barcode" --limit 10 --output json`, add the result to `dependencies`, and run `find-activities`. Arbitrary NuGet packages such as `CsvHelper`, `ClosedXML`, and `HtmlAgilityPack` may provide custom .NET types for `InvokeCode`; avoid Studio-bundled packages such as `Newtonsoft.Json` because version conflicts can cause runtime issues.

### project.json Key Fields

`name` is the package ID when packaged; `main` is the relative entry XAML; `dependencies` contains package/version constraints; `expressionLanguage` is `"VisualBasic"` or `"CSharp"`; `targetFramework` is `"Legacy"` for .NET Framework 4.6.1; `designOptions.outputType` is `"Process"` or `"Library"`; and `studioVersion` identifies the creating Studio version.

| Syntax | Meaning |
|---|---|
| `[1.2.3]` | Exact version 1.2.3 |
| `[1.2.3, )` | Minimum version 1.2.3 |
| `[1.0, 2.0)` | `>= 1.0`, `< 2.0` |

### Library Project Template

For reusable workflows, set `outputType` to `"Library"`:
```json
{
  "name": "Acme.Finance.InvoiceUtilities",
  "description": "Reusable invoice processing workflows",
  "dependencies": { "UiPath.System.Activities": "[24.10.8]" },
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
  "designOptions": { "projectProfile": "Developement", "outputType": "Library" }
}
```

Libraries have no `main` or `entryPoints`, publish as activity packages, expose Public workflows as activities, and keep Private workflows as helpers. See [project-organization-guide.md](./project-organization-guide.md).

## Discovery Workflow — Detailed Steps

Complete discovery before writing or editing XAML.

### Step 1: Project Structure

Run:
```
Glob: pattern="**/*.xaml" path="{projectRoot}"
Read: file_path="{projectRoot}/project.json"
```
Analyze folder conventions, names, workflows, `expressionLanguage`, and `dependencies`.

### Step 2: Consult Activity Reference Docs

Read `references/activity-docs/`: known package → `activity-docs/{PackageName}.md`; unknown package → `activity-docs/_INDEX.md`; VB.NET → `activity-docs/_PATTERNS.md`; XAML → `references/xaml-basics-and-rules.md`; gotchas → `activity-docs/_COMMON-PITFALLS.md`; InvokeCode → `activity-docs/_INVOKE-CODE.md`; REFramework → `activity-docs/_REFRAMEWORK.md`; Document Understanding → `activity-docs/_DU-PROCESS.md`; all activities → `activity-docs/AllActivities.md`. These describe behavior, not exact CLR names, property names, or enum values; Steps 4 and 5 remain mandatory for those.

### Step 3: Search Current Project

Run `Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"`, `Grep: pattern="ActivityName|pattern" path="{projectRoot}"`, and `Read: file_path="{projectRoot}/ExistingWorkflow.xaml"`. In mature projects prioritize local patterns; skip this step in greenfield projects.

### Step 4: Discover Activities (MANDATORY for non-built-in activities)

Skip `find-activities` for built-ins listed in [_BUILT-IN-ACTIVITIES.md](./activity-docs/_BUILT-IN-ACTIVITIES.md): `If`, `Assign`, `Sequence`, `TryCatch`, `Flowchart`, `ForEach`, `While`, `Switch`, `Throw`, `Delay`, `Parallel`, `LogMessage`, `InvokeCode`, `InvokeWorkflowFile`, `ForEachRow`, `AddDataRow`. Use their provided XAML snippets directly.

For every other activity, run:
```bash
uip rpa-legacy find-activities "{projectRoot}" --query "send mail" --output json
uip rpa-legacy find-activities "{projectRoot}" --query "invoke code" --include-type-definitions --output json
```
Use returned `XamlSnippet` and `XmlnsDeclaration`; do not guess. Multi-word relevance scoring, CamelCase boundaries, and `--exact` are supported. Use `--exact` for known names; calls take ~15-30 seconds.

### Step 5: Inspect Types (MANDATORY for Enums/Complex Types)

Run for every enum or complex type and any type lacking valid values in docs:
```bash
uip rpa-legacy type-definition "{projectRoot}" --type "NetLanguage" --output json
uip rpa-legacy type-definition "{projectRoot}" --type "System.Net.Mail.MailMessage" --output json
```
InvokeCode `Language` accepts `VBNet` and `CSharp`, not `VisualBasic` or `VB`.

### Step 5.5: Search NuGet for Packages (When Needed)

When known packages and `find-activities` do not cover a capability, run:
```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```
Search all configured feeds by name/description, add the package to `dependencies`, then run `find-activities`. This also applies to `CsvHelper` and `HtmlAgilityPack`; avoid bundled `Newtonsoft.Json` because version conflicts can occur.

### Step 6: Search UiPath Documentation (Fallback)

Run:
```bash
uip docsai ask "best practices for Excel automation in legacy projects" --output json
uip docsai ask "ExcelApplicationScope ActivityAction body validation error" --output json
```
Use when bundled docs and CLI tools are insufficient, for best practices/guidelines/troubleshooting, unfamiliar errors, or concepts such as Orchestrator, queues, and triggers.

### Step 7: Search the Web (Last Resort)

Use `WebSearch` for UiPath Forum, Stack Overflow, GitHub, Reddit:

```
WebSearch: "UiPath forum ExcelApplicationScope ActivityAction body legacy"
WebSearch: "site:stackoverflow.com UiPath legacy ExcelApplicationScope XAML"
WebSearch: "site:github.com UiPath REFramework legacy XAML example"
```

Use when: all previous steps fail, obscure errors, community workarounds needed. **Always** verify web-sourced info against project config.

### Troubleshooting

For a wrong enum value or `"Cannot create unknown type"`/`"is not a member of"`, run `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`. For an unknown activity class or namespace, run `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, then add xmlns and assembly reference. For batch-edit errors, revert to the last good state, re-add one activity at a time, and validate after each. For docs/property mismatches, run `find-activities --include-type-definitions` for exact CLR names. For an unfamiliar problem, use `docsai ask` → `WebSearch` → ask user.

## Phase 3: Validate & Fix Loop

### Step 3.1: Validate

Run after every XAML edit; do not batch edits without validation. Validate the file during iteration and the project before completion:
```bash
uip rpa-legacy validate "{projectRoot}/Main.xaml" --output json
uip rpa-legacy validate "{projectRoot}" --output json
```

### Step 3.2: Categorize and Fix Errors

**Fix order:** Package → Structure → Type → Activity Properties → Logic. **Always** fix in this order — higher-category fixes often resolve lower-category errors automatically.

1. **Package:** For a missing namespace, activity, or assembly, identify the package, confirm it in [activity reference docs](./activity-docs/_INDEX.md), and ask the user to install it manually in Studio (Studio → Manage Packages → search → Install) or edit `project.json` dependencies directly, matching NuGet constraints. The legacy CLI has no `install-or-update-packages`. Re-validate after installation.
2. **Structure:** Read around the error, use `Edit` to fix XML, and cross-check [xaml-basics-and-rules.md](./xaml-basics-and-rules.md). Check unclosed elements, mismatched prefixes, and duplicate `x:Name` attributes.
3. **Type:** Always run `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`; never guess enum values. Check `x:TypeArguments`, prefixes such as `sd:DataTable` vs `x:String`, and VB/C# syntax. InvokeCode `Language` accepts `VBNet`, not `VisualBasic` or `VB`.
4. **Activity Properties:** Always run `uip rpa-legacy find-activities "{projectRoot}" --query "activity name" --include-type-definitions --output json`. Treat CLI output as authoritative for CLR names and properties; check modern-versus-Legacy differences and enum values.
5. **Logic:** Read and edit XAML, match project expression syntax, consult [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md), and run `uip rpa-legacy debug` when static checks pass.

### Step 3.3: Iteration Loop

```text
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

When stuck on one error, consider deferring to the user if it is a configuration detail (missing package, credential setup, connection string); state clearly what needs to be done.

### Step 3.4: Package (Optional)

After validation passes, run this when a deployable artifact is needed; packaging is not required for debugging:
```bash
uip rpa-legacy pack "{projectRoot}" -o "{outputDir}" --output json
```

### Step 3.5: Smoke Test with Debug (Optional)

Always validate before debugging:
```bash
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --timeout 60
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --result-path /tmp/result.json --log-level error
```

Exit code `0` means success; inspect `Data.Output`. Exit code `1` means failure; inspect `Data.Error`: `Error.ActivityDisplayName` + `Error.XamlFile` locates it, `Error.ExceptionType` + `Error.Message` explains it, `Error.StackTrace` gives the call chain, and `Data.ErrorLog` gives error-level context. Fix and retry: edit XAML → validate → debug again. Debug performs real actions; use only when safe. For test data creation see **[testing-guide.md § Test Data Creation](testing-guide.md#test-data-creation)**.

### Common Error Scenarios

Wrong enum: run `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`; InvokeCode accepts `VBNet` and `CSharp`, not `VisualBasic` or `VB`. Unknown activity: run `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, then add xmlns and assembly reference. Batch errors: revert and add one activity at a time with validation. Property mismatch: run `find-activities --include-type-definitions`. Stuck: `uip docsai ask "..."` → `WebSearch` (UiPath Forum, Stack Overflow, GitHub) → ask user.
