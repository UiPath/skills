# CLI Tool Reference

Reference for `uip rpa-legacy` commands and recovery. The CLI is self-documenting; run `uip rpa-legacy --help`, `uip rpa-legacy find-activities --help`, or `uip rpa-legacy validate --help`. Unlike `uip rpa`, `rpa-legacy` is standalone: it needs no Studio Desktop IPC, uses UiRobot for execution, and resolves project dependencies independently.

## Path and Output Rules

- Always use absolute paths; store `{projectRoot}` at Phase 0 and pass it to every command. Never use `cd`.
- Always use `--output json` for programmatic parsing (global option on all `uip` subcommands). Never suppress stderr (`2>/dev/null`); non-zero-exit error details are JSON on stderr.
- Check `Result` (`"Success"` or `"Failure"`); on failure, read `Message` and `Instructions`.

```
WRONG:  cd "C:/Projects/MyProject" && uip rpa-legacy validate . --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject" --output json
RIGHT:  uip rpa-legacy validate "C:/Projects/MyProject/Main.xaml" --output json
```

## File Operations (Built-in Tools)

| Action | Tool and parameters |
|---|---|
| Explore project files | `Glob` pattern `**/*.xaml`, project root |
| Find files | `Glob` pattern (e.g. `**/*Mail*.xaml`), path |
| Search XAML | `Grep` regex across `.xaml` files, pattern and file/directory path |
| Read contents/project definition | `Read` file path, offset, limit; definition is `{projectRoot}/project.json` |
| Create workflow | `Write` new `.xaml` file, path and XAML content |
| Edit workflow | `Edit` exact string replacement in `.xaml`, path, old_string, new_string |

## Activity Discovery Tools

| Action | Command and parameters |
|---|---|
| Search activities | `uip rpa-legacy find-activities <project-path> --query "..." --output json`; `<project-path>` (required), `--query`, `--tags`, `--limit` (default 50) |
| Search with types | `uip rpa-legacy find-activities <project-path> --query "..." --include-type-definitions --output json`; adds full argument type definitions |
| Inspect .NET type | `uip rpa-legacy type-definition <project-path> --type "FullyQualifiedTypeName" --output json`; `--type` accepts full/simple name |
| Search NuGet | `uip rpa-legacy find-package --query "..." --output json`; `--query` required, `--limit` default 50 |

### find-activities

Search installed NuGet dependencies. Results include names, in/out arguments and types, ready-to-use XAML snippet, xmlns declaration, and optionally type definitions. **Always start activity XAML from returned `XamlSnippet`** to match installed package element, namespace, and property names.

```bash
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "Excel Read Range" --output json
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "ReadRange" --exact --output json
uip rpa-legacy find-activities "C:/Projects/MyLegacyProject" --query "invoke code" --include-type-definitions --output json
```

Activity output fields include `DisplayName`, `ClassName`, `Namespace`, `TypeFullName`, `Arguments` (`Name`, `Direction`, `Type`), `XmlnsPrefix`, `XmlnsDeclaration` (e.g. `"xmlns:umsa=\"clr-namespace:UiPath.Mail.SMTP.Activities;assembly=UiPath.Mail.Activities\""`), and `XamlSnippet`. `--include-type-definitions` adds a `TypeDefinitions` array (enum values, class properties, etc.).

| Parameter | Meaning |
|---|---|
| `<project-path>` | Required positional path to `project.json` or its folder |
| `--query <search>` | Filter by activity name, description, or category |
| `--tags <tags>` | Comma-separated category tags |
| `-l, --limit <count>` | Maximum results (default: 50) |
| `--include-type-definitions` | Include full argument type definitions (enums, classes, interfaces) |
| `--exact` | Case-insensitive exact `ClassName` or `DisplayName` match |

Multi-word queries use relevance scoring (`"Excel Read Range"`); CamelCase boundaries are detected (`SendHotkey`, `ExcelReadRange`). Use `--exact` for known names to avoid irrelevant matches (e.g. `--query "If" --exact` returns the WF4 If activity, not 17 unrelated matches).

### type-definition

Inspects dependency .NET types: enum values, properties, methods, constructors, and base types.
```bash
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "UiPath.Mail.Activities.MailFolder" --output json
uip rpa-legacy type-definition "C:/Projects/MyLegacyProject" --type "System.Net.Mail.MailMessage" --output json
```
`<project-path>` is the required positional path to `project.json` or its folder; `--type <name>` accepts full or simple name; `--timeout <seconds>` sets timeout.

### find-package

Searches enabled v3 NuGet feeds in parallel by package name or description; `UiPathActivities` packages rank first.
```bash
uip rpa-legacy find-package --query "UiPath.Excel" --limit 10 --output json
uip rpa-legacy find-package --query "barcode" --output json
```
Each result has `Id`, `Version`, `Description`, `Authors`, `Source`. Add a discovered package to `dependencies` in `project.json`, then `find-activities` indexes its activities.

## Validation Tools

| Action | Command |
|---|---|
| Validate file | `uip rpa-legacy validate <xaml-path> --output json` |
| Validate project | `uip rpa-legacy validate <project-path> --output json` |

### validate

Checks a XAML file, `project.json`, or project folder for compilation errors (missing arguments, broken references, type mismatches).
```bash
uip rpa-legacy validate "C:/Projects/MyLegacyProject/Main.xaml" --output json
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --output json
uip rpa-legacy validate "C:/Projects/MyLegacyProject" --result-path "C:/output/errors.json"
```
`<path>` is required and positional; `--result-path <path>` writes JSON to a file instead of stdout. Validate per-file during development for faster, focused feedback and the whole project before completion.

## Package & Debug Tools

| Action | Command |
|---|---|
| Package (optional) | `uip rpa-legacy pack <project-path> -o <output-dir>` |
| Debug | `uip rpa-legacy debug <xaml-path>` |

### pack

Creates a deployable `.nupkg`; optional and not required to debug legacy RPA.
```bash
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output"
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0"
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --auto-version
uip rpa-legacy pack "C:/Projects/MyLegacyProject" -o "C:/output" --version "1.2.0" --release-notes "Bug fixes and improvements"
```
`<project-path>` is required (project or `project.json`). Parameters: `-o, --output <path>`, `-v, --version <version>`, `--auto-version`, `--output-type <type>` (`Process|Library|Tests|Objects`), `--split-output`, `--repository-url <url>`, `--repository-commit <sha>`, `--repository-branch <branch>`, `--repository-type <type>`, `--project-url <url>`, `--release-notes <text>`, `--timeout <seconds>`.

### debug

Executes XAML locally via UiRobot; logs stream in real time. Structured JSON contains output arguments on success or diagnostics on failure. **Always validate before debugging; never debug a file with compilation errors.**
```bash
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml"
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx", "in_Count": 5}'
uip rpa-legacy debug "C:/Projects/MyLegacyProject/Main.xaml" -i '{"in_FilePath": "C:\\data.xlsx"}' --result-path /tmp/result.json --log-level error
```
`<xaml-path>` is required and full; `-i, --input <json>` supplies inputs; `--result-path <path>` persists full result JSON; `--timeout <seconds>` (0 = no timeout) kills the robot if exceeded; `--robot-path <path>` specifies UiRobot.exe (otherwise auto-detected); `--log-level <level>` is `debug|info|warn|error` (default `info`). Exit codes: 0 success, 1 failure.

Success has `Result`, `Code` (`RpaLegacyDebug`), and `Data` fields including `XamlPath`, `Status`, and, only when Out arguments have values, `Output` (e.g. `out_Result`, `out_RowCount`). Failure has `Result`, `Message`, and `Data.Error` fields `ExceptionType`, `Message`, `ActivityDisplayName`, `ActivityType`, `XamlFile`, `StackTrace`; `Data.ErrorLog` entries have `Timestamp`, `Level`, `Message`.

Diagnose with `Error.ActivityDisplayName` + `Error.XamlFile` (locate), `Error.ExceptionType` + `Error.Message` (understand), `Error.StackTrace` (call chain), and `ErrorLog` (all error-level robot entries; useful for multiple failures). Fix-and-retry: edit XAML → validate → debug. Debug performs real actions (clicks, emails, file writes); run only when safe or with mock input data.

## Documentation Search

| Action | Command |
|---|---|
| Search UiPath docs | `uip docsai ask "your question" --output json`; `<query>` required |

### docsai ask

Searches official UiPath documentation for answers, best practices, guidelines, troubleshooting, and configuration. Use when bundled docs and CLI discovery are insufficient.
```bash
uip docsai ask "best practices for error handling in legacy UiPath workflows" --output json
uip docsai ask "ExcelApplicationScope validation error ActivityAction body" --output json
uip docsai ask "Orchestrator queue item priority and deadline" --output json
uip docsai ask "REFramework MaxRetryNumber and retry logic" --output json
```
`<query>` is required positional; `-t, --tenant <tenant-name>` is optional and defaults to auth value. Use for uncovered topics, best practices/troubleshooting, or unfamiliar errors. If insufficient, use `WebSearch` for UiPath Forum (`forum.uipath.com`), Stack Overflow, GitHub public repos, Reddit (`r/UiPath`); verify web information against project configuration before applying.

## CLI Error Recovery

| Error pattern | Cause | Recovery |
|---|---|---|
| `"project not found"`, `"project.json not found"` | Wrong project path | Verify `<project-path>` points to folder containing `project.json` |
| `"file not found"` | Wrong XAML path | Verify `<xaml-path>` is a full path to an existing `.xaml` |
| `"package not found"`, `"version not available"` | Missing NuGet dependency | Ask user to install in Studio or check NuGet feeds |
| `"not authenticated"`, 401, 403 | Cloud auth required | Run `uip login` and retry |
| `"UiRobot not found"` | UiRobot.exe absent or not in PATH | Pass `--robot-path` explicitly or ask user to install UiPath Robot |
| `"timeout"`, `"ETIMEDOUT"` | Command took too long | Increase `--timeout` |
| `"compilation error"` in validate | XAML errors | Parse details, fix XAML, re-validate |
| Unrecognized | Unknown | Use `--log-level debug`; inform user |

Do not retry the same failing command in a loop. Diagnose root cause, recover, then retry once; if it fails again, inform the user.

## Phase 0: Environment Readiness

**Goal:** Establish `{projectRoot}` and verify a legacy framework project before other operations. `rpa-legacy` is standalone, needs no running Studio Desktop, resolves dependencies from NuGet, and uses UiRobot for execution.

### Step 0.1: Establish Project Root

Commands require `<project-path>` to point to the folder containing `project.json` or that file itself.
```bash
ls {cwd}/project.json
```
If CWD is not the root, locate with `Glob: pattern="**/project.json"`. Ask the user where the project is if multiple files are found. Store the root as `{projectRoot}` and use it consistently.

### Step 0.2: Verify Legacy Project

Read `{projectRoot}/project.json`:
```
Read: file_path="{projectRoot}/project.json"
```
Check `targetFramework` (`"Legacy"`; may be absent pre-2021, implying Legacy), `expressionLanguage` (`"VisualBasic"` or `"CSharp"`), `studioVersion` (typically `< 23.x`), and `dependencies` (classic package versions, no modern package IDs; pre-2021 projects may have versions ≤ 22.x). If `targetFramework` is `"Windows"` or `"Portable"`, use the `uipath-rpa` skill. If absent, check `studioVersion` and `dependencies`; old projects default to Legacy.

### Step 0.3: Authentication (If Needed)

Run `uip login` for private authenticated NuGet feeds, `build` commands that push to Orchestrator, or Orchestrator resources (assets, queues) during debug. Most local validate, edit, and find-activities work needs no authentication. Login opens a browser flow.

### Step 0.4: Package Restore

After creating or modifying `project.json` dependencies, restore before `find-activities` or `type-definition`: run
```bash
uip rpa-legacy validate "{projectRoot}" --output json
```
If `find-activities` reports `"No assemblies resolved from package dependencies"`, run validate first.

## Legacy Project Structure

### Directory Layout

```text
{projectRoot}/
├── project.json
├── Main.xaml
├── *.xaml
├── Workflows/       # optional
├── Data/            # optional
├── .screenshots/    # optional
├── .settings/       # optional
└── .tmh/            # optional
```
Legacy projects lack `.local/docs/packages/` (auto-generated activity docs), `.codedworkflows/` (coded automation), `.objects/` (Object Repository), and `.project/JitCustomTypesSchema.json` (JIT custom types).

### Creating a project.json from Scratch

#### Minimal Template

Only `UiPath.System.Activities` is required; add packages as needed.
```json
{
  "name": "MyProject", "description": "", "main": "Main.xaml",
  "dependencies": { "UiPath.System.Activities": "[24.10.8]" },
  "schemaVersion": "4.0", "studioVersion": "25.10.0.0", "projectVersion": "1.0.0",
  "expressionLanguage": "VisualBasic", "targetFramework": "Legacy",
  "runtimeOptions": { "autoDispose": false, "isPausable": true, "isAttended": false, "requiresUserInteraction": true, "supportsPersistence": false, "workflowSerialization": "DataContract", "excludedLoggedData": ["Private:*", "*password*"], "executionType": "Workflow" },
  "designOptions": { "projectProfile": "Developement", "outputType": "Process" },
  "entryPoints": [{ "filePath": "Main.xaml", "uniqueId": "00000000-0000-0000-0000-000000000000", "input": [], "output": [] }]
}
```

#### Package Selection Guide

Add only needed packages; `UiPath.System.Activities` is the only required package.

| Need | Package | Latest Legacy Version |
|---|---|---:|
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

For Excel, email, and REST dependencies:
```json
"dependencies": { "UiPath.System.Activities": "[24.10.8]", "UiPath.Excel.Activities": "[2.24.4]", "UiPath.Mail.Activities": "[1.24.18]", "UiPath.WebAPI.Activities": "[1.21.1]" }
```
Packages can be added later. `find-activities` searches only `dependencies`; after adding a package, run it again. If known packages do not cover a need, search configured feeds with `uip rpa-legacy find-package --query "barcode" --limit 10 --output json`, add the package to `dependencies`, then run `find-activities`. Arbitrary .NET packages support custom classes, methods, and types via `InvokeCode` with namespace imports (e.g. `CsvHelper`, `ClosedXML`, `HtmlAgilityPack`). Avoid packages bundled with Studio (e.g. `Newtonsoft.Json`) to prevent version conflicts.

#### project.json Key Fields

| Field | Meaning |
|---|---|
| `name` | Project name; package ID when packaged |
| `main` | Entry XAML (relative path) |
| `dependencies` | NuGet dependencies and version constraints |
| `expressionLanguage` | `"VisualBasic"` (most legacy) or `"CSharp"` |
| `targetFramework` | `"Legacy"` for .NET Framework 4.6.1 |
| `designOptions.outputType` | `"Process"` (standalone) or `"Library"` (reusable) |
| `studioVersion` | Creating Studio version |

Version constraints: `[1.2.3]` exact; `[1.2.3, )` minimum; `[1.0, 2.0)` means >= 1.0 and < 2.0.

#### Library Project Template

For reusable workflows published as a NuGet package, set `outputType` to `"Library"`:
```json
{
  "name": "Acme.Finance.InvoiceUtilities", "description": "Reusable invoice processing workflows",
  "dependencies": { "UiPath.System.Activities": "[24.10.8]" }, "schemaVersion": "4.0",
  "studioVersion": "25.10.0.0", "projectVersion": "1.0.0", "expressionLanguage": "VisualBasic", "targetFramework": "Legacy",
  "runtimeOptions": { "autoDispose": false, "isPausable": true, "isAttended": false, "requiresUserInteraction": false, "supportsPersistence": false, "workflowSerialization": "DataContract", "excludedLoggedData": ["Private:*", "*password*"], "executionType": "Workflow" },
  "designOptions": { "projectProfile": "Developement", "outputType": "Library" }
}
```
Library projects have no `main` or `entryPoints`; `outputType: "Library"` publishes an activity package, not a process. Public workflows become consumer activities; Private workflows are internal helpers. See [project-organization-guide.md](./project-organization-guide.md) for naming, versioning, and patterns.

## Discovery Workflow — Detailed Steps

Complete discovery before writing or editing XAML.

### Step 1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list workflows
Read: file_path="{projectRoot}/project.json"          → project definition
```
Analyze folder/naming conventions, existing workflows, `expressionLanguage` (VB.NET or C#), and installed `dependencies`.

### Step 2: Consult Activity Reference Docs

Read `references/activity-docs/` for behavior, gotchas, and patterns:

| Need | Read |
|---|---|
| Known package | `activity-docs/{PackageName}.md` |
| Find package | `activity-docs/_INDEX.md` |
| VB.NET expressions | `activity-docs/_PATTERNS.md` |
| XAML structure | `references/xaml-basics-and-rules.md` |
| Gotchas | `activity-docs/_COMMON-PITFALLS.md` |
| InvokeCode | `activity-docs/_INVOKE-CODE.md` |
| REFramework | `activity-docs/_REFRAMEWORK.md` |
| Document Understanding | `activity-docs/_DU-PROCESS.md` |
| All activities | `activity-docs/AllActivities.md` |

Docs explain behavior, not exact CLR property names/enum values; Steps 4 and 5 are mandatory for those.

### Step 3: Search Current Project

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```
Prioritize local patterns in mature projects; skip for greenfield projects.

### Step 4: Discover Activities (MANDATORY for non-built-in activities)

Skip `find-activities` for built-ins listed in [_BUILT-IN-ACTIVITIES.md](./activity-docs/_BUILT-IN-ACTIVITIES.md): If, Assign, Sequence, TryCatch, Flowchart, ForEach, While, Switch, Throw, Delay, Parallel, LogMessage, InvokeCode, InvokeWorkflowFile, ForEachRow, AddDataRow. Use their provided XAML snippets directly. For all others, run `find-activities`; use exact class names, signatures, types, `XamlSnippet`, and `XmlnsDeclaration` (add declaration to root `<Activity>`).
```bash
uip rpa-legacy find-activities "{projectRoot}" --query "send mail" --output json
uip rpa-legacy find-activities "{projectRoot}" --query "invoke code" --include-type-definitions --output json
```
Queries support multi-word relevance scoring and CamelCase. Use `--exact` for known names (e.g. `--query "ReadRange" --exact`); calls take ~15-30 seconds. Add specific terms or `--exact` if results are irrelevant. Reference docs do not give exact CLR names or argument types; skipping discovery means guessing and wasted validation cycles.

### Step 5: Inspect Types (MANDATORY for Enums/Complex Types)

Run for every enum, complex type argument, or type without documented valid values; use exact values, never guess.
```bash
# InvokeCode Language accepts VBNet and CSharp (NOT "VisualBasic" or "VB")
uip rpa-legacy type-definition "{projectRoot}" --type "NetLanguage" --output json
uip rpa-legacy type-definition "{projectRoot}" --type "System.Net.Mail.MailMessage" --output json
```

### Step 5.5: Search NuGet for Packages (When Needed)

If known packages in [§ Legacy Project Structure](#legacy-project-structure) and `find-activities` do not cover the capability, search feeds, add the package to `dependencies`, then use `find-activities`:
```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```
Arbitrary .NET packages are also supported (e.g. `CsvHelper`, `HtmlAgilityPack`). Avoid Studio-bundled packages (e.g. `Newtonsoft.Json`) to prevent version conflicts.

### Step 6: Search UiPath Documentation (Fallback)

Use when bundled docs and CLI tools are insufficient, for best practices/guidelines/troubleshooting, unfamiliar errors, or platform concepts (Orchestrator, queues, triggers):
```bash
uip docsai ask "best practices for Excel automation in legacy projects" --output json
uip docsai ask "ExcelApplicationScope ActivityAction body validation error" --output json
```

### Step 7: Search the Web (Last Resort)

Only if previous steps fail or for obscure errors/community workarounds, use `WebSearch` for UiPath Forum, Stack Overflow, GitHub, or Reddit; verify findings against project configuration:
```
WebSearch: "UiPath forum ExcelApplicationScope ActivityAction body legacy"
WebSearch: "site:stackoverflow.com UiPath legacy ExcelApplicationScope XAML"
WebSearch: "site:github.com UiPath REFramework legacy XAML example"
```

### Troubleshooting

- Wrong enum (`"Cannot create unknown type"`, `"is not a member of"`): run `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`.
- Unknown activity/missing namespace: run `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`; add xmlns and assembly reference.
- Multiple errors after batch edits: revert to last good state; re-add one activity at a time, validating each.
- Docs' property names fail: run `find-activities --include-type-definitions` for exact CLR names.
- Unfamiliar problem: `docsai ask` → `WebSearch` → ask user.

## Phase 3: Validate & Fix Loop

### Step 3.1: Validate

Validate a XAML file, `project.json`, or project folder:
```bash
uip rpa-legacy validate "{projectRoot}/Main.xaml" --output json
uip rpa-legacy validate "{projectRoot}" --output json
```
Run after **every** XAML edit (do not batch edits without validation); validate the whole project before completion to catch cross-file issues.

### Step 3.2: Categorize and Fix Errors

Always fix in this order: **Package → Structure → Type → Activity Properties → Logic**; higher-category fixes may resolve lower-category errors.

1. **Package** (missing namespace, unknown activity, unresolved assembly): legacy CLI has no `install-or-update-packages`. Identify package from error; confirm name in [activity reference docs](./activity-docs/_INDEX.md); ask user to install in Studio (Studio → Manage Packages → search → Install) or edit `project.json` dependencies directly (advanced; must meet NuGet version constraints); re-validate after installation.
2. **Structure** (invalid XML, malformed elements, missing closing tags): `Read` around error and `Edit`; check [xaml-basics-and-rules.md](./xaml-basics-and-rules.md) for nesting and namespaces. Common issues: unclosed elements, mismatched prefixes, duplicate `x:Name`.
3. **Type** (wrong property type, invalid cast, mismatch): always use `type-definition` for exact enum values/type members; do not guess.
   ```bash
   uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json
   ```
   InvokeCode `Language` accepts `VBNet` (not `VisualBasic` or `VB`). Check `x:TypeArguments`, namespace prefixes (`sd:DataTable` vs `x:String`), and VB/C# expression syntax. Docs provide behavior; `type-definition` exact values.
4. **Activity Properties** (unknown properties/settings): always use `find-activities --include-type-definitions` for exact names:
   ```bash
   uip rpa-legacy find-activities "{projectRoot}" --query "activity name" --include-type-definitions --output json
   ```
   CLI output is authoritative; check modern-only or misspelled properties and enum values.
5. **Logic** (behavior, expressions, business logic): `Read` the flow and `Edit` it; match project expression language, consult [activity-docs/_PATTERNS.md](./activity-docs/_PATTERNS.md), and use `uip rpa-legacy debug` for runtime validation after static checks pass.

### Step 3.3: Iteration Loop

```text
REPEAT:
  1. Run: uip rpa-legacy validate "{projectRoot}/{file}.xaml" --output json
  2. IF 0 errors → EXIT loop (success)
  3. IF errors exist:
     a. Categorize (Package/Structure/Type/Properties/Logic)
     b. Fix highest-category errors first
     c. Apply with Read + Edit
  4. IF an error cannot be auto-resolved:
     a. Document it for the user
     b. Suggest manual fix steps
     c. Continue fixing other errors
UNTIL: 0 errors OR all remaining errors require user action
```
For configuration issues (missing package, credentials, connection string), consider deferring to the user and clearly state what they must do.

### Step 3.4: Package (Optional)

If a deployable `.nupkg` is needed, package after validation passes:
```bash
uip rpa-legacy pack "{projectRoot}" -o "{outputDir}" --output json
```
Packaging is not required to debug legacy RPA.

### Step 3.5: Smoke Test with Debug (Optional)

Always validate before debugging; do not debug compilation errors.
```bash
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --timeout 60
uip rpa-legacy debug "{projectRoot}/Main.xaml" -i '{"in_TestMode": true}' --result-path /tmp/result.json --log-level error
```
Exit 0: check `Data.Output` for Out values. Exit 1: inspect `Data.Error`: `Error.ActivityDisplayName` + `Error.XamlFile` locates; `Error.ExceptionType` + `Error.Message` explains; `Error.StackTrace` gives call chain; `Data.ErrorLog` gives error-level context. Fix-and-retry: edit → validate → debug. Debug performs real actions (clicks, emails, file writes); run only when safe. For test data (Excel, CSV, JSON, common UiPath types), see **[testing-guide.md § Test Data Creation](testing-guide.md#test-data-creation)**.

### Common Error Scenarios

See [Troubleshooting](#troubleshooting) for enum, activity-name, batch-edit, and property-name errors. For unfamiliar problems, escalate `uip docsai ask "..."` → `WebSearch` (UiPath Forum, Stack Overflow, GitHub) → ask user.