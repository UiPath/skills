---
name: uipath-rpa-workflows
description: "Generate, edit, test, and run RPA workflows (XAML files) in UiPath Studio Desktop using uipcli CLI and filesystem operations. TRIGGER when: RPA project detected (project.json with UiPath dependencies AND .xaml workflow files); User mentions XAML workflows, RPA workflows, .xaml files, or UiPath Studio Desktop workflows; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, transaction processing, queue items, API calls, etc.) and a UiPath RPA/XAML project exists nearby; User asks about fixing XAML errors or workflow validation issues. DO NOT TRIGGER when: User is working with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-development instead)."
---

# RPA Workflow Architect

Generate and edit RPA workflows using a **discovery-first approach** with **iterative error-driven refinement**. Always understand before acting, start simple, and validate continuously.

This skill uses `uipcli` CLI commands (via `Bash`) and Claude Code's built-in tools (`Read`, `Write`, `Edit`, `Glob`, `Grep`) to interact with UiPath Studio Desktop projects and manage workflow files.

## Core Principles

1. **Discovery Before Generation** - Never generate XAML without first understanding project structure and existing patterns
2. **Search Examples Repository** - Always use `uipcli rpa list-workflow-examples` to find relevant examples, then `uipcli rpa get-workflow-example` to retrieve and study them
3. **Start Simple, Iterate** - Build iteratively, in small increments. Create minimal working version first, then refine through validation cycles. Take it one step (and one activity) at a time. Configure on the go based on errors and validation feedback
4. **Validate After Every Change** - Never assume success; always check with `uipcli rpa get-errors`
5. **Fix Errors Methodically** - Categorize errors and fix in order: Package -> Structure -> Type -> Logic

---

## CLI Output Format

All `uipcli` commands support `--format <format>` (table, json, yaml, plain).

**Always use `--format json`** for commands whose output you need to parse or act on (e.g., `get-errors`, `find-activities`, `list-workflow-examples`, `is connections list`). JSON output is structured, unambiguous, and avoids table-formatting surprises.

Use the default (table) only when displaying results directly to the user for readability.

---

## Tool Quick Reference

### Core RPA Workflow Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Explore project files** | `Glob` with `**/*.xaml` pattern, or `Bash`: `ls -la {projectRoot}` | Project root directory |
| **Find files by pattern** | `Glob` with pattern (e.g., `**/*Mail*.xaml`) | Glob pattern, path |
| **Search XAML content** | `Grep` with regex pattern across `.xaml` files | Pattern, file/directory path |
| **Read file contents** | `Read` tool | File path, offset, limit |
| **Read project definition** | `Read` tool on `{projectRoot}/project.json` | File path |
| **Explore object repository** | `Glob` `**/*` in `{projectRoot}/.objects/` + `Read` metadata files | `.objects/` path |
| **Get full project context** | `Read` project.json + `Read` XAML files + `Glob`/`Read` `.objects/` + `Read` `.settings/` | Combine multiple reads |
| **Search for activities** | `Bash`: `uipcli rpa find-activities --query "..." [--tags "..."] [--limit N] --format json` | `--query` (required), `--tags`, `--limit` (default 10) |
| **Get default activity XAML (non-dynamic)** | `Bash`: `uipcli rpa get-default-activity-xaml --activity-class-name "..."` | `--activity-class-name` (fully qualified) |
| **Get default activity XAML (dynamic)** | `Bash`: `uipcli rpa get-default-activity-xaml --activity-type-id "..." [--connection-id "..."]` | `--activity-type-id`, `--connection-id` (optional) |
| **List workflow examples** | `Bash`: `uipcli rpa list-workflow-examples --tags '["service1","service2"]' [--prefix "..."] [--limit N] --format json` | `--tags` (JSON array, required), `--prefix` (optional), `--limit` (default 10) |
| **Get workflow example** | `Bash`: `uipcli rpa get-workflow-example --key "path/to/example.xaml"` | `--key` (blob path from list results) |
| **Create new workflow file** | `Write` tool — create a new `.xaml` file with full XAML content | File path, XAML content |
| **Edit existing workflow** | `Edit` tool — exact string replacement in `.xaml` files | File path, old_string, new_string |
| **Get errors** | `Bash`: `uipcli rpa get-errors [--file-path "..."] [--skip-validation] --format json` | `--file-path` (relative to project dir), `--skip-validation` (use cached errors) |
| **Get JIT type definitions** | `Read` tool on `{projectRoot}/.project/JitCustomTypesSchema.json` | File path |
| **Install/update packages** | `Bash`: `uipcli rpa install-or-update-packages --packages '[{"id":"...","version":"..."}]'` | `--packages` (JSON array) |
| **Run workflow** | `Bash`: `uipcli rpa run-file --file-path "..." [--input-arguments '...'] [--log-level ...]` | `--file-path` (required), `--input-arguments` (JSON), `--log-level` |

### Project Lifecycle Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Create new project** | `Bash`: `uipcli rpa new --name "..." [--template-id ...] [--location ...] [--expression-language ...] [--target-framework ...] [--description "..."]` | See [Creating New Projects](#creating-new-projects) |
| **Open project in Studio** | `Bash`: `uipcli rpa open-project [--project-dir "..."]` | `--project-dir` (optional) |
| **Close project** | `Bash`: `uipcli rpa close-project [--project-dir "..."]` | `--project-dir` (optional) |

### Studio Management Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **List Studio instances** | `Bash`: `uipcli rpa list-instances --format json` | (none) |
| **Start Studio** | `Bash`: `uipcli rpa start-studio` | (none) |
| **Focus activity in designer** | `Bash`: `uipcli rpa focus-activity [--activity-id "..."]` | `--activity-id` (IdRef; omit to focus all sequentially) |

### UI Automation Indication Tools

Use these when building UI Automation workflows to capture selectors into the Object Repository. See **[ui-automation.md](./references/ui-automation.md)** for the full UIA workflow.

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Indicate application/screen** | `Bash`: `uipcli rpa indicate-application [--name "..."] [--parent-id "..." \| --parent-name "..."] [--activity-class-name "..."]` | `--name` (screen name in Object Repository), `--parent-id`/`--parent-name` (application ref) |
| **Indicate UI element** | `Bash`: `uipcli rpa indicate-element --name "..." --activity-class-name "..." [--parent-id "..." \| --parent-name "..."]` | `--name` (required), `--activity-class-name` (required, e.g. `UiPath.UIAutomation.Activities.TypeInto`), `--parent-id`/`--parent-name` (screen ref) |

**UI Automation indication workflow:**
1. First indicate the application/screen: `uipcli rpa indicate-application --name "MyApp"` — the user points at the application window
2. Then indicate individual elements within that screen: `uipcli rpa indicate-element --name "SubmitButton" --activity-class-name "UiPath.UIAutomation.Activities.ClickX" --parent-name "MyApp"` — the user points at the element
3. The indicated elements are stored in the Object Repository (`.objects/`) and can be referenced in XAML via their `ObjectRepositoryReference`
4. Read the resulting `.objects/` metadata to get the element IDs for use in workflow XAML

### Test Manager Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **Get manual test cases** | `Bash`: `uipcli rpa get-manual-test-cases --format json` | (none) |
| **Get manual test steps** | `Bash`: `uipcli rpa get-manual-test-steps --format json` | (none) |

### Integration Service (IS) Tools

| Action | How | Key Parameters |
|--------|-----|----------------|
| **List connectors** | `Bash`: `uipcli is connectors list [--filter "..."] --format json` | `--filter` (by name/key) |
| **Get connector details** | `Bash`: `uipcli is connectors get <connector-key> --format json` | `connector-key` (required) |
| **List connections** | `Bash`: `uipcli is connections list [connector-key] [--connection-id "..."] [--folder-key "..."] --format json` | `connector-key` (optional filter), `--connection-id`, `--folder-key` |
| **Create connection (OAuth)** | `Bash`: `uipcli is connections create <connector-key> [--no-browser]` | `connector-key` (required), opens OAuth flow |
| **Ping/verify connection** | `Bash`: `uipcli is connections ping <connection-id>` | `connection-id` (required) |
| **Edit/re-auth connection** | `Bash`: `uipcli is connections edit <connection-id>` | `connection-id` (required), opens OAuth flow |
| **List connector activities** | `Bash`: `uipcli is activities list <connector-key> --format json` | `connector-key` (required) |
| **List connector resources** | `Bash`: `uipcli is resources list <connector-key> [--operation ...] --format json` | `connector-key`, `--operation` (List/Retrieve/Create/Update/Delete/Replace) |
| **Describe resource schema** | `Bash`: `uipcli is resources describe <connector-key> <object-name> [--operation ...] --format json` | `connector-key`, `object-name`, `--operation` |
| **Execute resource CRUD** | `Bash`: `uipcli is resources execute <op> <connector-key> <object-name>` | Operations: `create`, `list`, `get`, `update`, `replace`, `delete` |

---

## Supporting References

For detailed information, consult these files (read them on-demand):
- **[basics-and-rules.md](./references/basics-and-rules.md)** — XAML file anatomy, workflow types, safety rules, common editing operations, reference examples, and ConnectorActivity internals. **CRITICAL: read before generating/creating/editing any XAML.**
- **[invoke-code-activities.md](./references/invoke-code-activities.md)** — An escape hatch for when XAML activities can't be reliably generated or edited. Offers the possibility to integrate VB or C# code snippets as activities, when to use them, and best practices for integrating code into RPA workflows. Useful as a pragmatic fallback when dedicated activities have unresolvable issues and writing code would do it.
- **[control-flow-activities.md](./references/control-flow-activities.md)** — Core control flow activities with syntax and examples (Assign, If/Else, For Each, While, Try Catch, etc.)
- **[common-pitfalls.md](./references/common-pitfalls.md)** — Common pitfalls, constraints, scope requirements, property conflicts, gotchas, and issues that should be known before working with RPA workflows, along with strategies to avoid them
- **[gsuite-activities.md](./references/gsuite/gsuite-activities.md)** — Google Suite activity patterns: Gmail (send, iterate, get newest, download attachments, label/archive/delete/move/mark-read, auto-reply), Google Sheets (read range, write range, write row, create spreadsheet), Google Drive (get file/folder, list files, iterate folder, upload, download), and Google Calendar (create event). Covers triggers for all services and model types (`GmailMessage`, `GDriveRemoteItem`, `GSuiteEventItem`). Read when working with `UiPath.GSuite.Activities`.
- **[pdf-document-understanding.md](./references/document-understanding/pdf-document-understanding.md)** — PDF utility activities: ExtractPDFText, GetPDFPageCount, SetPDFPassword, MergePDFs, ExtractPDFPageRange, ExtractPDFImages. Also covers the DU pipeline overview. Read when working with PDF utility activities in `UiPath.DocumentUnderstanding.Activities`.
- **[document-understanding-activities.md](./references/document-understanding/document-understanding-activities.md)** — Document Understanding (DU) pipeline activities for non-PDF inputs: classification (`ClassifyDocument` with ML and generative classifiers), extraction (`ExtractDocumentDataWithDocumentData` with ML and generative extractors), and validation (`ValidateDocumentDataWithDocumentData`, `CreateValidationAction`/`WaitForValidationAction` async pair, `CreateClassificationValidationActionAndWait`). Read when working with `UiPath.DocumentUnderstanding.Activities` for classify/extract/validate workflows.
- **[word-activities.md](./references/word/word-activities.md)** — Word document activity patterns: WordApplicationScope (required scope), WordReadText, WordAppendText, WordReplaceText, WordExportToPdf, and other Word manipulation activities. Read when working with `UiPath.Word.Activities`.
- **[powerpoint-activities.md](./references/powerpoint/powerpoint-activities.md)** — PowerPoint presentation activity patterns: PowerPointApplicationScope (required scope), InsertTextInPresentation, FindAndReplaceTextInPresentation, ReplaceShapeWithMedia, ReplaceShapeWithDataTable, InsertSlide, DeleteSlide, CopyPasteSlide, SavePresentationAsPdf, RunMacro, and related activities. Read when working with `UiPath.Presentations.Activities`.
- **[excel-activities.md](./references/excel/excel-activities.md)** — Excel activity patterns for both modern (`ueab:` with `ExcelApplicationCard`/`ExcelProcessScopeX`) and classic (`ui:` standalone) styles. Covers scope containers, iterators (`ExcelForEachRowX`, `ForEachSheetX`), read/write/cell/format/sort/lookup/pivot/chart/VBA activities, and namespace requirements. Read when working with `UiPath.Excel.Activities`.
- **[outlook-mail-activities.md](./references/mail/outlook-mail-activities.md)** — Classic Outlook mail activity patterns: namespaces, `GetOutlookMailMessages`, `MoveOutlookMessage`, `SaveMailAttachments`, `SendOutlookMail` (classic `ui:` prefix), modern `OutlookApplicationCard` scope with `ForEachEmailX`, variable type (`System.Net.Mail.MailMessage`), and IS connection pattern. Read when working with `UiPath.Mail.Activities` Outlook activities (not O365).
- **[msoffice365-outlook-activities.md](./references/mail/msoffice365-outlook-activities.md)** — Office 365 Outlook mail activity patterns: namespaces, `SendMailConnections`, `GetNewestEmail`, `DownloadEmailAttachments`, `NewEmailReceived` trigger, filter expressions, and `Office365Message` type. Read when working with `UiPath.MicrosoftOffice365.Activities`.
- **[project-structure.md](./references/project-structure.md)** — Project directory layout, project.json schema, common packages
- **[jit-custom-types-schema.md](./references/jit-custom-types-schema.md)** - How to get JIT custom types of dynamic activities.
- **[ui-automation.md](./references/ui-automation.md)** — UI Automation (UIA) best practices, rules, and XAML examples. **CRITICAL: read before generating/editing any UI Automation workflows**

---

## Core Workflow: Classify Request

**Determine CREATE or EDIT before proceeding:**

| Request Type | Trigger Words | Action |
|--------------|---------------|--------|
| **CREATE** | "generate", "create", "make", "build", "new" | Start with Phase 0 -> Discovery -> Generate |
| **EDIT** | "update", "change", "fix", "modify", "add to" | Start with Phase 0 -> Discovery -> Edit |

If unclear which file to edit, **ask the user** rather than guessing.

---

## Phase 0: Environment Readiness

**Goal:** Ensure Studio Desktop is running, connected, and targeting the correct project before any other operations.

### Step 0.1: Establish Project Root

The `uipcli rpa` commands use `--project-dir` to target a specific project (defaults to current working directory). **If the current working directory is NOT the UiPath project root, all commands will fail or target the wrong project.**

```bash
# Check if project.json exists in the CWD
ls {cwd}/project.json
```

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- **Pass `--project-dir` explicitly** to every `uipcli rpa` command, or
- Ask the user where their project is located

Store the project root path and use it consistently as `{projectRoot}` throughout all subsequent operations.

### Step 0.2: Verify Studio is Running

```bash
uipcli rpa list-instances --format json
```

**If no instances are found or Studio is not running:**
```bash
uipcli rpa start-studio
```

**If Studio is running but the project is not open:**
```bash
uipcli rpa open-project --project-dir "{projectRoot}"
```

**If Studio IPC connection fails** (error messages about connection refused, timeout, or pipe not found):
1. Check if Studio Desktop is actually installed on the machine
2. Try `uipcli rpa start-studio` to launch a fresh instance
3. If Studio is running but IPC fails, the user may need to restart Studio
4. Inform the user and ask them to ensure Studio Desktop is open and responsive

### Step 0.3: Authentication (If Needed)

Some commands (IS connections, workflow examples, cloud features) require authentication:

```bash
uipcli login
```

If you encounter auth errors (401, 403, "not authenticated") during any phase, prompt the user to run `uipcli login` to authenticate against their UiPath Cloud tenant.

---

## Phase 1: Discovery

**Goal:** Understand project context and existing patterns before writing any XAML.

### Step 1.1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
Bash: ls -la {projectRoot}                            → explore project root (if needed)
```

Analyze:
- Where should new workflows be placed? (folder conventions)
- What naming pattern is used? (match existing file names)
- What similar workflows already exist?
- Should I use VB or C# syntax? (check `expressionLanguage` in `project.json`, also check existing workflows and imports for `Microsoft.VisualBasic`)
- What packages are already installed? (check `dependencies` in `project.json` and namespaces in existing XAML files)
- Are there existing connections, credentials, or objects I can reuse?

### Step 1.2: Find Examples

Search **both** the examples repository and the current project. This step is critical for understanding activity patterns, proper XAML structure, and activity properties.

**Choose your approach based on project maturity:**
- **Mature project** (has existing workflows): Prioritize local patterns first (Section A) — they reflect the project's established conventions. Use the examples repository (Section B) to fill gaps.
- **Greenfield project** (empty or near-empty): Go straight to the examples repository (Section B) — local search will yield nothing useful.

#### A. Search Current Project

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"     → find files matching a pattern
Grep: pattern="ActivityName|pattern" path="{projectRoot}"  → search XAML content for activities
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"      → read a relevant existing workflow
```

#### B. Search Examples Repository

Use `uipcli rpa list-workflow-examples` to discover relevant example workflows by service/integration tags:

```bash
# Search by service tags (AND logic — all tags must match)
uipcli rpa list-workflow-examples --tags '["salesforce"]' --limit 10 --format json

# Multiple tags narrow down results
uipcli rpa list-workflow-examples --tags '["jira", "confluence"]' --limit 10 --format json

# Use prefix to filter by category
uipcli rpa list-workflow-examples --tags '["gmail"]' --prefix "email-communication/" --limit 15 --format json

# Once you identify relevant examples, retrieve XAML content:
uipcli rpa get-workflow-example --key "email-communication/add-new-gmail-emails-to-keap-as-contacts.xaml"
```

**Tag Selection Guidelines:**
- Identify the services/integrations the user wants (e.g., "salesforce", "gmail", "jira")
- Convert to lowercase tags: `["salesforce"]`, `["gmail"]`, `["jira", "confluence"]`
- Multiple tags use AND logic — all tags must match
- Common tags: `confluence`, `jira`, `salesforce`, `outlook`, `gmail`, `slack`, `excel`, `sharepoint`, `teams`, `dropbox`, `hubspot`, `zendesk`, `servicenow`

**Best Practices:**
- Retrieve 3-5 most relevant examples based on filename/tags matching user intent
- Study the XAML structure, activity configuration, and patterns
- Note the namespaces and packages used in the examples
- Extract reusable patterns for error handling, data transformation, etc.

### Step 1.3: Study Patterns

After retrieving example XAML content, analyze the XAML thoroughly.
**See the "Supporting References" section above. Read the relevant [reference files](./references/) before studying the examples to make sense of the structure and patterns.**

**Extract from ALL examples (both repository and local):**
- How are activities structured and configured?
- What properties are commonly set?
- What error handling patterns are used (Try-Catch, Retry scopes)?
- What packages/namespaces are referenced in the XAML header?
- What variable types and scopes are used?
- Are objects and connections from the project used?
- How are credentials and authentication handled?
- What output/result handling patterns exist?

**When studying repository examples from `uipcli rpa get-workflow-example`:**
- The command returns the full XAML content directly
- Parse the namespace declarations at the top to identify required packages
- Look for `<Variable>` elements to understand data structures
- Study `<Argument>` elements for input/output patterns
- Study `<Configuration>` and `<Connection>` sections for determining dynamic activity properties usage
- Examine activity configurations for proper property settings

### Step 1.4: Discover Activities (When Needed)

Use `uipcli rpa find-activities` when the user describes an action and you need to find which activity implements it, or when you need the exact fully qualified class name, type ID, and `isDynamicActivity` flag before getting the default activity XAML.

```bash
uipcli rpa find-activities --query "send mail" --limit 10 --format json
```

**When to use this command:**
- You need to find the correct activities to use in a workflow, searching as you would do in a global search engine for activities
- You need activity details: fully qualified class name, type ID, description, configuration, whether it's dynamic, whether it's a trigger
- You need to explore available, useful activities before generating or editing workflows
- The user describes an action (e.g., "get weather") and you need to discover which activity implements it
- Before getting default activity XAML, to find the exact FQDN class name, type ID, and `isDynamicActivity` flag
- You want to discover new activities not necessarily installed in the project (results are global, not limited to installed packages)

**How search works:**
- Works similarly to Studio's activity search bar
- Returns **global** results — not limited to packages currently installed in the project
- If a useful activity is found that isn't installed, use `uipcli rpa install-or-update-packages` to add it
- Tags can be used alongside the query to narrow down results further

**Examples:**
```bash
# Find activities for sending email
uipcli rpa find-activities --query "send mail" --limit 5 --format json

# Find weather-related activities
uipcli rpa find-activities --query "get weather" --format json

# Find Excel read activities
uipcli rpa find-activities --query "read range" --limit 10 --format json
```

**Do NOT use when:**
- You already know the exact activity to use and its exact fully qualified class name and/or type ID and can directly get the default XAML

### Step 1.5: Disambiguate Service / Provider

This step requires `find-activities` results from Step 1.4.

When results contain multiple competing packages for the same capability (e.g., O365 vs Gmail vs SMTP for email), determine the correct one using these signals — **do not ask the user unless all signals are ambiguous:**

**Auto-select** (skip prompting) when **any** of these are true:
- The user specified the provider (e.g., "send email via O365", "use Gmail")
- Only one package matches the search
- The project already has one of the competing packages installed (`dependencies` in `project.json`)
- The project defines a connection matching one of the options
- The workflow already uses activities from one of the packages — stay consistent with what's there
- If packages are legacy/deprecated and it's clear which is the modern one

**Prompt only as a last resort** — when multiple viable options exist and none of the above signals apply:
1. Present the top 2–4 choices from the search results
2. Mark the recommended option with **(Recommended)** — prefer the most modern/full-featured option
3. Include a one-line difference for each (e.g., "requires Integration Service connection" vs "protocol-based, works on-premise")
4. Continue with **only** the chosen package

**Save the preference:** After resolving disambiguation (whether auto-selected or user-chosen), suggest saving the preference to `CLAUDE.md` and `AGENTS.md` in the project folder so future sessions auto-select without re-prompting. For example: _"Want me to save this preference (e.g., 'Always use O365 for email activities') to CLAUDE.md and AGENTS.md so it's remembered for future workflows?"_

### Step 1.6: Resolve Activity Properties

When you need to insert or edit a specific activity, use `uipcli rpa get-default-activity-xaml` to retrieve the activity's default XAML template, its properties, and the default values. Use it as a starting point for configuring new activities. This default representation is a crucial starting point as it ensures that Studio can properly render and parse the activity.

The command handles both non-dynamic and dynamic activities.

#### For Non-Dynamic Activities

```bash
uipcli rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.WriteLine"
```

#### For Dynamic Activities

```bash
uipcli rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id ""
```

**When to use this command:**
- You know which activity to use but need its exact XAML structure
- You need to verify the correct property names and default values
- You want a clean starting template without inherited configurations from examples

**Key parameters:**
- `--activity-class-name`: For non-dynamic activities. Must be fully qualified (e.g., `UiPath.Core.Activities.WriteLine`)
- `--activity-type-id`: For dynamic activities. Use `uipcli rpa find-activities` to find the exact type ID
- `--connection-id`: Optional, only used for dynamic activities. Discover available connections using `uipcli is connections list [connector-key]`

**Do NOT use when:**
- You already have the correct, error-free activity XAML
- You're unsure which activity to use (use `uipcli rpa find-activities` first)
- You need to understand what activities are available (use `uipcli rpa find-activities` first)

**For JIT custom types**, read the schema file:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

For more details, see **[jit-custom-types-schema.md](./references/jit-custom-types-schema.md)**

### Step 1.7: Get Current Context

Before generating, understand reusable elements by combining multiple reads:

```
Read: file_path="{projectRoot}/project.json"                → project definition (deps, expression language)
Glob: pattern="**/*" path="{projectRoot}/.objects/"         → explore object repository
Read: file_path="{projectRoot}/.objects/.metadata"          → object repository metadata
Read: file_path="{projectRoot}/Main.xaml"                   → existing workflow (variables, arguments, imports)
Glob: pattern="**/*" path="{projectRoot}/.settings/"        → settings profiles
Bash: uipcli is connections list --format json              → available Integration Service connections
Bash: uipcli is connectors list --format json               → available connectors
```

This provides:
- Existing variables and their types/scopes (from XAML files)
- Current arguments and their directions (In/Out/InOut) (from XAML `<x:Members>`)
- Activity hierarchy and flow structure (from XAML body)
- Available imports and namespaces (from XAML `<TextExpression.NamespacesForImplementation>`)
- Whether the project is C# or VB (`expressionLanguage` in `project.json`, or check for `Microsoft.VisualBasic` in imports)
- Available assets, connections, queues, credentials, and other project-level or global-level resources

### Step 1.8: Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Service connectors (e.g., Salesforce, Jira, ServiceNow), explore the connector's capabilities before writing XAML:

```bash
# What activities does this connector offer?
uipcli is activities list <connector-key> --format json

# What data objects/resources does it expose?
uipcli is resources list <connector-key> --format json

# What fields does a specific resource have? (essential for configuring dynamic activity properties)
uipcli is resources describe <connector-key> <object-name> --format json
```

**Check if a connection exists:**
```bash
uipcli is connections list <connector-key> --format json
```

**If no connection exists**, you have two options:
1. **Create one** (requires user interaction for OAuth): `uipcli is connections create <connector-key>`
2. **Use a placeholder** — insert the dynamic activity with an empty `connectionId` and inform the user they need to configure the connection in Studio

**Verify a connection is active:**
```bash
uipcli is connections ping <connection-id>
```

If the ping fails, offer to re-authenticate: `uipcli is connections edit <connection-id>`

---

## Phase 2: Generate or Edit

### IMPORTANT Guidelines for both CREATE and EDIT:
- Always start with a minimal working version (e.g., default activity representation), then iterate based on errors and validation
- **CRITICAL:** Always read the relevant [reference files](./references/) for proper structure, syntax, rules, and patterns before generating or editing any XAML content. These references contain crucial information that prevents common mistakes and ensures the generated/edited workflows are correct and functional.
- Before generating ANY XAML, ensure you have studied relevant examples and understand the required structure and properties

### For CREATE Requests

**Strategy:** Generate minimal working version, expect to iterate.

Use the `Write` tool to create a new `.xaml` file with proper XAML boilerplate. Refer to [basics-and-rules.md](./references/basics-and-rules.md) for the complete XAML file anatomy template.

```
Write: file_path="{projectRoot}/Workflows/DescriptiveName.xaml"
       content=<full XAML content with proper headers, namespaces, and body>
```

**File path inference:**
- Use folder conventions from project structure exploration
- Create descriptive filename: `Workflows/[Category]/[DescriptiveName].xaml` or follow existing project patterns
- Ensure filename ends with `.xaml`

### For EDIT Requests

**Strategy:** Always read current content before editing.

```
Read: file_path="{projectRoot}/WorkflowToEdit.xaml"              → understand current structure
Grep: pattern="section to modify" path="{projectRoot}/..."       → OR search for specific sections
```

Then use the `Edit` tool for targeted string replacement:

```
Edit: file_path="{projectRoot}/WorkflowToEdit.xaml"
      old_string=<exact text from file>
      new_string=<modified text>
```

**Critical:** `old_string` must match exactly what's in the file and be unique. Include surrounding context if needed to ensure uniqueness.

---

## Phase 3: Validate & Fix Loop

- This phase repeats until we obtain a 0-error state or errors cannot be resolved automatically.
- It is acceptable to defer some remaining configuration to the user. Just inform the user about any required manual updates they need to make after generation.
- If the required activity connection does not exist, reuse any available connection in the project as a placeholder
- If certain activity properties or arguments are unknown, provide default values (e.g., placeholders, default type values, or use `uipcli rpa get-default-activity-xaml`)

### Step 3.1: Check for Errors

```bash
# Check errors for a specific file (preferred — faster, especially in large projects):
uipcli rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --format json

# Check errors for the entire project:
uipcli rpa get-errors --format json

# Use cached errors (skip re-validation — faster but may be stale):
uipcli rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --skip-validation --format json
```

**Important notes on `--file-path`:**
- The path must be **relative to the project directory**, not an absolute path
- Example: `--file-path "Workflows/SendEmail.xaml"`, NOT `--file-path "C:\Users\...\Workflows\SendEmail.xaml"`
- By default, `get-errors` forces Studio to re-validate before returning errors, ensuring up-to-date results
- Use `--skip-validation` only when you want to quickly check the last known errors without triggering a new validation pass
- **Always prefer `--file-path`** for targeted checks — much faster than full-project validation
- For long-running projects, consider using `--timeout` on the parent `uipcli rpa` command if validation takes too long: `uipcli rpa --timeout 600 get-errors --file-path "..."`

### Step 3.2: Categorize and Fix

| Error Category | Indicators | Fix Strategy |
|----------------|------------|--------------|
| **Package Errors** | Missing namespace, unknown activity type | `Read` project.json -> `Bash` `uipcli rpa install-or-update-packages` |
| **Structural Errors** | Invalid XML, missing required properties | `Read` file -> `Edit` the XAML |
| **Type Errors** | Incorrect property type, invalid value | `Read` JIT schema / `Grep` XAML -> `Edit` the XAML |
| **Activity Properties Errors** | Unknown dynamic properties, misconfigured activity | `Bash` `uipcli rpa find-activities` -> `Bash` `uipcli rpa get-default-activity-xaml` -> `Edit` the XAML |
| **Logic Errors** | Business logic issues, wrong behavior | `Read` file -> `Edit` the XAML |

**Fix order:** Package -> Structure -> Type -> Dynamic Activity -> Logic

### Step 3.3: Package Error Resolution

```
Read: file_path="{projectRoot}/project.json"     → check current dependencies

Bash: uipcli rpa install-or-update-packages --packages '[{"id": "UiPath.Excel.Activities", "version": "24.10.6"}]'
```

**If `install-or-update-packages` fails:**
- **Package not found**: Verify the exact package ID — check spelling, use `uipcli rpa find-activities` to discover the correct package name from an activity's assembly
- **Version conflict**: Try a different version, or omit the version to get the latest compatible one
- **Network/feed error**: The user may need to check their NuGet feed configuration in Studio settings

### Step 3.4: Resolving Dynamic Activity Custom Types

Dynamic activities (e.g., Integration Service connectors) retrieved via `uipcli rpa get-default-activity-xaml` (with `--activity-type-id`) may use **JIT-compiled custom types** for their input/output properties. After the activity is added to the workflow, when you need to discover the property names and CLR types of these custom entities (e.g., to populate an `Assign` activity targeting a custom type property, or to create a variable of a custom type), read the JIT custom types schema:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

### Step 3.5: Focus Activity for Debugging

When `get-errors` returns an error referencing a specific activity (by IdRef or DisplayName), use `focus-activity` to highlight it in the Studio designer. This helps the user see the problematic activity in context and verify fixes visually:

```bash
# Focus a specific activity by its IdRef (from the error output):
uipcli rpa focus-activity --activity-id "Assign_1"

# Focus all activities sequentially (useful for walkthrough):
uipcli rpa focus-activity
```

This is especially useful when:
- An error references an activity and you want the user to confirm the context
- You've made a fix and want to show the user which activity was modified
- The error is ambiguous and you need to verify which activity instance is affected

### Step 3.6: Iteration Loop

```
REPEAT:
  1. uipcli rpa get-errors --file-path "path/to/workflow.xaml" --format json
  2. IF 0 errors (or errors cannot be resolved automatically) -> EXIT to Phase 4
  3. Identify highest-priority error category
  4. Apply appropriate fix
  5. (Optional) Focus the fixed activity: uipcli rpa focus-activity --activity-id "..."
  6. GOTO 1

DO NOT stop until all activities are resolved (recognized).
DO NOT skip validation steps.
DO NOT assume edits worked without checking.
```

Expect multiple iteration cycles for complex workflows.

### Step 3.7: Smoke Test (Optional but Recommended)

After reaching 0 errors, optionally run the workflow to catch runtime errors (wrong credentials, missing files, logic bugs) that static validation cannot detect:

```bash
# Run with default arguments:
uipcli rpa run-file --file-path "Workflows/MyWorkflow.xaml" --format json

# Run with input arguments:
uipcli rpa run-file --file-path "Workflows/MyWorkflow.xaml" --input-arguments '{"recipientEmail": "test@example.com", "subject": "Test"}' --format json

# Run with verbose logging for debugging:
uipcli rpa run-file --file-path "Workflows/MyWorkflow.xaml" --log-level Verbose --format json
```

**When to run:**
- The workflow has no compilation errors but you want to verify runtime behavior
- The workflow involves file I/O, API calls, or data transformations that could fail at runtime
- The user specifically asks to test the workflow

**When NOT to run:**
- The workflow has side effects (sends emails, modifies databases, calls external APIs) — warn the user first
- The workflow requires interactive input (UI automation, attended triggers)
- Compilation errors still exist (fix those first)

If `run-file` reveals runtime errors, analyze the output and loop back to Step 3.2 to fix them.

---

## Phase 4: Response

**Provide comprehensive summary:**

1. **File path** of created/edited workflow (clickable reference)
2. **Brief description** of what the workflow does
3. **Key activities** and logic implemented
4. **Packages installed** (if any)
5. **Limitations** or notes for the user
6. **Suggested next steps** (testing, parameterization, etc.)
7. **Encourage user to review and customize further as needed** (e.g., fill in placeholders, set up connections etc.)

**Do NOT just say "workflow created"** - give user confidence the request was fully fulfilled.

---

## Creating New Projects

When the user needs a brand-new UiPath project (not just a new workflow in an existing project):

```bash
uipcli rpa new \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language "VisualBasic" \
  --target-framework "Windows" \
  --description "Automates invoice processing" \
  --format json
```

**Parameters:**
| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `--name` | Any string | (required) | Project folder name |
| `--location` | Directory path | (current dir) | Parent directory where project folder is created |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | (template default) | Expression syntax for XAML workflows |
| `--target-framework` | `Legacy`, `Windows`, `Portable` | (template default) | .NET target framework |
| `--description` | Any string | (none) | Project description in project.json |

**After creation:**
1. Open the project in Studio: `uipcli rpa open-project --project-dir "/path/to/MyAutomation"`
2. The project root is now `/path/to/parent/directory/MyAutomation/`
3. Proceed to Phase 1 (Discovery) using the new project root

---

## CLI Error Recovery

When `uipcli` commands fail, diagnose by error category:

| Error Pattern | Cause | Recovery |
|---------------|-------|----------|
| `"connection refused"`, `"EPIPE"`, `"pipe not found"` | Studio IPC not available | Run `uipcli rpa start-studio`, then `uipcli rpa open-project --project-dir "..."` |
| `"timeout"`, `"ETIMEDOUT"` | Command took too long | Increase timeout: `uipcli rpa --timeout 600 <command>`, or use `--skip-validation` for `get-errors` |
| `"not authenticated"`, `401`, `403` | Auth required for cloud features | Run `uipcli login` and re-try |
| `"package not found"`, `"version not available"` | Wrong package ID or version | Verify package name via `uipcli rpa find-activities`, try without version for latest |
| `"project not found"`, `"no project open"` | Wrong project-dir or project not open | Verify `--project-dir` path, run `uipcli rpa open-project` |
| `"file not found"` in `get-errors` | Wrong `--file-path` (must be relative to project) | Use path relative to project root, not absolute |
| `"Studio is busy"`, `"operation in progress"` | Studio is processing a previous request | Wait a few seconds and retry the command |
| Any unrecognized error | Unknown | Check `--verbose` flag on parent: `uipcli rpa --verbose <command>` for debug details, inform the user |

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

---

## Anti-Patterns

**Never:**
- Try to generate large, complex workflows in one single go
- Generate XAML without first checking project structure and existing examples
- Assume a create/edit succeeded without validating with `uipcli rpa get-errors`
- Stop iteration loop before reaching 0 errors
- Guess file paths without exploring project structure first
- Edit or create XAML without reading the appropriate [reference files](./references/) for proper structure, syntax, rules, and patterns
- Use a non-unique string for replacement that matches multiple locations in the file
- Create non-XAML workflow files (this skill creates XAML only)
- Skip searching the examples repository with `uipcli rpa list-workflow-examples`
- Use incorrect/guessed keys with `uipcli rpa get-workflow-example` (always use keys from list results)
- Guess activity class names or type IDs (use `uipcli rpa find-activities` to find the exact type ID and FQDN class name first)
- Ask the user to choose a service provider without first checking project signals (installed packages, connections, existing activities) — auto-select when possible (Step 1.5)
- Skip `uipcli rpa find-activities` when unsure which activity implements a user-described action
- Guess dynamic activity property names or types without using `uipcli rpa get-default-activity-xaml` with `--activity-type-id`
- Pass absolute paths to `--file-path` in `get-errors` (must be relative to project directory)
- Retry failing CLI commands in a loop without diagnosing the root cause
- Skip Phase 0 (Studio readiness) — all subsequent phases depend on Studio IPC being available
- Use connector/dynamic activities without checking whether a connection exists (use `uipcli is connections list` first)

---

## Quality Checklist

Before handover, verify:

**Environment:**
- [ ] Studio is running and connected (Phase 0 completed)
- [ ] Project root is correctly identified and used consistently

**Discovery & Examples:**
- [ ] Examples repository was searched with `uipcli rpa list-workflow-examples` for relevant patterns
- [ ] Relevant examples were retrieved and studied with `uipcli rpa get-workflow-example`
- [ ] Local project was explored for existing patterns and workflows
- [ ] Activities were discovered with `uipcli rpa find-activities`
- [ ] Service/provider disambiguation was resolved — auto-selected or prompted when all signals were ambiguous (Step 1.5)
- [ ] Started with a safe default XAML structure using `uipcli rpa get-default-activity-xaml` (with correct parameters for dynamic vs non-dynamic)
- [ ] Activity properties were resolved with `uipcli rpa get-default-activity-xaml` (for dynamic activities custom types, see the "Resolving Dynamic Activity Custom Types" section)
- [ ] For connector workflows: connections verified with `uipcli is connections list`

**XAML Content Quality:**
- [ ] VB.NET or C# syntax matches project language (checked existing workflows)
- [ ] All namespace declarations present for activities used (`xmlns:ui=...` etc.)
- [ ] Variables and arguments properly scoped and named

**Validation & Testing:**
- [ ] Workflow file path is valid and follows project conventions
- [ ] All required activities are present
- [ ] Error handling (Try-Catch) is included where appropriate
- [ ] `get-errors` returns 0 errors (or remaining errors are documented as user-deferred)
- [ ] Smoke test with `run-file` considered (if workflow is safe to run)

**User Communication:**
- [ ] User has been informed of any limitations
- [ ] Next steps have been suggested (testing, customization)
- [ ] Informed the user about any manual edits needed after generation (e.g., configuring connections, updating placeholders etc.)
