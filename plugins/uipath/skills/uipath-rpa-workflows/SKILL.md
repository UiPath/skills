---
name: uipath-rpa-workflows
description: "Generate, edit, test, and run RPA workflows (XAML files) in UiPath Studio Desktop using uipcli CLI and filesystem operations. TRIGGER when: RPA project detected (project.json with UiPath dependencies AND .xaml workflow files); User mentions XAML workflows, RPA workflows, .xaml files, or UiPath Studio Desktop workflows; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, transaction processing, queue items, API calls, etc.) and a UiPath RPA/XAML project exists nearby; User asks about fixing XAML errors or workflow validation issues. DO NOT TRIGGER when: User is working with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-development instead)."
---

# RPA Workflow Architect

Generate and edit RPA workflows using a **discovery-first approach** with **iterative error-driven refinement**. Always understand before acting, start simple, and validate continuously.

This skill uses `uipcli` CLI commands (via `Bash`) and Claude Code's built-in tools (`Read`, `Write`, `Edit`, `Glob`, `Grep`) to interact with UiPath Studio Desktop projects and manage workflow files.

## Core Principles

1. **Activity Docs Are the Source of Truth** — Installed packages may ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/`. When present, these docs contain source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. They eliminate guesswork and are more reliable than examples or CLI-retrieved defaults. Always check for them first; push for package updates if unavailable, or fallback to `get-default-activity-xaml` and/or `get-workflow-example`.
2. **Know Before You Write** — Never generate XAML blind. Never try to guess properties, types, or configurations. Understand the project structure, what packages are installed, what expression language is used, and what patterns existing workflows follow. The deeper your understanding, the fewer validation cycles you'll need.
3. **Use What You Know, Skip What You Don't Need** — If you already know the package ID and activity class name, go directly to its doc file — don't enumerate all packages first. If activity docs give you a complete XAML example, don't also call `get-default-activity-xaml`. Be efficient: the discovery steps are a priority ladder, not a mandatory checklist.
4. **Start Minimal, Iterate to Correct** — Build one activity at a time. Write the smallest working XAML, validate with `uipcli rpa get-errors`, fix what breaks, repeat. Start with what you know works (default or example values, configurations). Complex workflows emerge from validated building blocks, not from generating everything at once.
5. **Validate After Every Change** — Never assume an edit succeeded. Always confirm with `uipcli rpa get-errors`. Static validation catches most problems; `run-file` catches the rest.
6. **Fix Errors by Category** — Triage errors in order: Package (missing dependencies) → Structure (invalid XML) → Type (wrong property types) → Activity Properties (misconfigured activity) → Logic (wrong behavior). Fixing in this order avoids cascading false errors.

---

## CLI Output Format

All `uipcli` commands support `--format <format>` (table, json, yaml, plain).

**Always use `--format json`** for commands whose output you need to parse or act on (e.g., `get-errors`, `find-activities`, `list-workflow-examples`, `is connections list`). JSON output is structured, unambiguous, and avoids table-formatting surprises.

Use the default (table) only when displaying results directly to the user for readability.

---

## Tool Quick Reference

For the full CLI command reference (all tools, parameters, and error recovery), see **[references/cli-reference.md](./references/cli-reference.md)**.

Key commands at a glance: `find-activities`, `get-default-activity-xaml`, `get-errors`, `install-or-update-packages`, `run-file`, `list-workflow-examples`, `get-workflow-example`. For IS connectors: `is connectors list/get`, `is connections list/create/ping`, `is activities list`, `is resources list/describe/execute`.

**The CLI is fully self-documenting.** Append `--help` or `-h` at any level to discover commands, subcommands, and parameters: `uipcli --help`, `uipcli rpa --help`, `uipcli rpa get-default-activity-xaml --help`, `uipcli is --help`, `uipcli is connections --help`, etc.

---

## Supporting References

**Always check installed activity docs first** (`{projectRoot}/.local/docs/packages/`) before using the bundled references below. See [Step 1.2](#step-12-discover-activity-documentation-primary-source).

### Procedural Reference Files

Detailed procedures extracted from the main workflow phases:
- **[cli-reference.md](./references/cli-reference.md)** — Full `uipcli` CLI command reference guide (all tools, parameters, commands)
- **[environment-setup.md](./references/environment-setup.md)** — Phase 0 details: project root detection, Studio verification, authentication, and new project creation
- **[validation-and-fixing.md](./references/validation-and-fixing.md)** — Phase 3 details: package resolution, JIT custom types, focus-activity debugging, iteration loop, smoke testing
- **[examples-repository.md](./references/examples-repository.md)** — Workflow examples search commands, tag guidelines, and how to study retrieved examples
- **[connector-capabilities.md](./references/connector-capabilities.md)** — IS connector discovery, resource schema inspection, connection management

### Domain Reference Files

For XAML structure, control flow, and domain-specific patterns not covered by activity docs, consult these files (read them on-demand):
- **[xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md)** — XAML file anatomy, workflow types, safety rules, common editing operations, reference examples, and ConnectorActivity internals. **CRITICAL: read before generating/creating/editing any XAML.**
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
- **[ui-automation-version-notes.md](./references/ui-automation-version-notes.md)** — Version-specific UIA differences (24.10.x vs 25.10+). Read when the installed `UiPath.UIAutomation.Activities` package is below 25.10 — several properties from the main reference don't exist in older versions.

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

Ensure Studio Desktop is running, connected, and targeting the correct project. See **[references/environment-setup.md](./references/environment-setup.md)** for the full setup procedure (project root detection, Studio verification, authentication).

**Quick check:** Find `project.json` to establish `{projectRoot}`, run `uipcli rpa list-instances --format json` to verify Studio, and `uipcli rpa open-project` if needed.

---

## Phase 1: Discovery

**Goal:** Understand project context, leverage installed activity documentation, study existing patterns, identify reusable components, and discover activities before writing any XAML.

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

### Step 1.2: Discover Activity Documentation (Primary Source)

**This is the most important discovery step.** Installed activity packages may ship structured markdown documentation at `{projectRoot}/.local/docs/packages/{PackageId}/`. These docs are generated from activity source code and contain everything needed to configure activities correctly on the first try: properties, types, defaults, enum values, conditional property groups, and working XAML examples.

**Availability:** Docs exist only for **installed packages** and typically only for **newer package versions**. When you're confident about which package you need:
- **Package not installed?** Install it first: `uipcli rpa install-or-update-packages --packages '[{"id":"UiPath.WebAPI.Activities"}]'` — this also syncs docs if the package ships them.
- **Package installed but no docs?** Update to the latest version: `uipcli rpa install-or-update-packages --packages '[{"id":"UiPath.WebAPI.Activities"}]'` (omit version to get latest) — newer releases are more likely to ship documentation.

Prioritize installing/updating packages early. It unlocks both activity docs and `get-default-activity-xaml` (which also requires the package to be installed).

#### Filesystem Structure (Deterministic)

The directory layout is fixed and predictable:

```
{projectRoot}/.local/docs/packages/
+-- {PackageId}/                           # e.g., UiPath.WebAPI.Activities
    +-- overview.md                        # Package summary + categorized activity index with descriptions and links to docs
    +-- activities/                        # One file per activity
    |   +-- {ActivitySimpleClassName}.md   # e.g., NetHttpRequest.md, DeserializeJson.md
    |   +-- ...
    +-- coded/                             # (Optional) Coded workflow API ref -- ignore for XAML workflows
```

- `{PackageId}` matches the NuGet package ID from `project.json` dependencies (e.g., `UiPath.WebAPI.Activities`)
- `{ActivitySimpleClassName}` is the short class name without namespace (e.g., `NetHttpRequest`, not `UiPath.Web.Activities.Http.NetHttpRequest`)

#### Activity Doc Template (All Files Follow This Structure)

Every `activities/{ActivityName}.md` follows a consistent template:

1. **Header** -- `# Display Name`, fully qualified class name in code span, one-line description
2. **Metadata** -- `**Package:**`, `**Category:**`, optionally `**Platform:**` (`Cross-platform` or `Windows`)
3. **`## Properties`** -- subsections:
   - **`### Input`** -- table: Name, Display Name, Kind (`InArgument`/`Property`), Type, Required, Default, Description
   - **`### Output`** -- table: Name, Display Name, Kind (`OutArgument`), Type, Description. May include output type property breakdowns
   - **`### {GroupName} (conditional)`** -- groups with a `Visible When` column showing which controlling property value makes each property appear. Critical for modes like authentication, request body type, retry policy, etc.
   - **`### Common`** / **`### Options`** -- ContinueOnError, Timeout, etc.
4. **`## Valid Configurations`** -- conditional modes, mutually exclusive groups, valid property combinations
5. **`## Enum Reference`** -- exhaustive valid values per enum-typed property
6. **`## XAML Examples`** -- **copy-paste ready** snippets with correct syntax and realistic configurations. Best starting point for new activities -- richer than `get-default-activity-xaml` output.
7. **`## Notes`** -- tips, caveats, migration guidance

The `overview.md` provides: package summary and categorized activity index table with links to per-activity docs.

#### Decision Table

The filesystem structure is deterministic -- use it to skip unnecessary enumeration steps.

| Situation | Action |
|-----------|--------|
| **You know the package + activity name** | Go directly: `Read: file_path="{projectRoot}/.local/docs/packages/{PackageId}/activities/{ActivityName}.md"` |
| **You know the package, not the activity** | `Read` the `overview.md`, then read the identified activity doc. |
| **You don't know the package** | `Grep` across `.local/docs/packages/` for keywords. |
| **Docs exist but activity isn't documented** | Use other activity docs in the same package as structural reference, fall back to `get-default-activity-xaml`. |
| **No docs for the package** | **Update the package first** (`uipcli rpa install-or-update-packages`) -- this often adds docs. If still no docs, fall back to Steps 1.4-1.7. |
| **Package not installed** | **Install it first** (`uipcli rpa install-or-update-packages`) -- both docs and `get-default-activity-xaml` require it. After install, check for docs before proceeding to fallbacks. |
| **No `.local/docs/` directory at all** | Project may not support this feature yet. Use fallback flow starting at Step 1.3. |

### Step 1.3: Search Current Project

Search existing workflows in the project for reusable patterns and conventions.

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"     → find files matching a pattern
Grep: pattern="ActivityName|pattern" path="{projectRoot}"  → search XAML content for activities
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"      → read a relevant existing workflow
```

**Choose your depth based on project maturity:**
- **Mature project** (has existing workflows): Prioritize local patterns — they reflect the project's established conventions (namespace prefixes, variable naming, error handling style).
- **Greenfield project** (empty or near-empty): Skip this step — local search will yield nothing useful.

### Step 1.4: Discover Activities (When Needed)

Use `uipcli rpa find-activities` when you need to find which activity implements a user-described action, discover activities not covered by installed docs, or get the exact fully qualified class name, type ID, and `isDynamicActivity` flag.

```bash
uipcli rpa find-activities --query "send mail" --limit 10 --format json
```

**When to use this command:**
- You need to find the correct activities to use in a workflow, searching as you would do in a global search engine for activities
- You need activity details: fully qualified class name, type ID, description, configuration, whether it's dynamic, whether it's a trigger
- The user describes an action (e.g., "get weather") and you need to discover which activity implements it
- You want to discover new activities not necessarily installed in the project (results are global, not limited to installed packages)
- Activity docs don't exist for the target package, and you need to explore available activities

**How search works:**
- Works similarly to Studio's activity search bar
- Returns **global** results — not limited to packages currently installed in the project
- **If a useful activity is found in an uninstalled package, install it immediately** (see [Step 1.2](#step-12-discover-activity-documentation-primary-source)) — this unlocks both activity docs and `get-default-activity-xaml`
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

### Step 1.6: Resolve Activity Properties (Fallback)

Use `uipcli rpa get-default-activity-xaml` to retrieve the activity's default XAML template. **Requires the package to be installed** (see [Step 1.2](#step-12-discover-activity-documentation-primary-source)). If activity docs exist with XAML examples, prefer those as your starting point -- they're richer than bare defaults.

The command handles both non-dynamic and dynamic activities.

#### For Non-Dynamic Activities

```bash
uipcli rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.WriteLine"
```

#### For Dynamic Activities

```bash
uipcli is connections list # Find relevant connection ID, if any
uipcli rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id "{connectionId}"

# Or, if no relevant connection, pass an empty string
uipcli rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id ""
```

**When to use this command:**
- Activity docs don't exist or don't cover this specific activity
- You need the exact bare-bones default XAML template for Studio compatibility
- You're working with dynamic activities that require runtime-resolved properties
- You need to verify the correct property names and default values when docs are ambiguous

**Key parameters:**
- `--activity-class-name`: For non-dynamic activities. Must be fully qualified (e.g., `UiPath.Core.Activities.WriteLine`)
- `--activity-type-id`: For dynamic activities. Use `uipcli rpa find-activities` to find the exact type ID
- `--connection-id`: Optional, only used for dynamic activities. Discover available connections using `uipcli is connections list [connector-key]`

**For JIT custom types**, read the schema file:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

For more details, see **[jit-custom-types-schema.md](./references/jit-custom-types-schema.md)**

### Step 1.7: Search Examples Repository

Use when activity docs, `find-activities`, `get-default-activity-xaml`, and domain-specific [reference](./references/) files don't provide enough context — or when you need **full end-to-end workflow composition patterns**. See **[references/examples-repository.md](./references/examples-repository.md)** for search commands, tag guidelines, and how to study retrieved examples.

### Step 1.8: Get Current Context (As Needed)

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

This surfaces variables, arguments, imports, expression language, available connections, and reusable project-level resources.

### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Service connectors (dynamic activities), explore capabilities and manage connections before writing XAML. See **[references/connector-capabilities.md](./references/connector-capabilities.md)** for the full procedure (activity/resource discovery, connection management, schema inspection).

---

## Phase 2: Generate or Edit

### Guidelines for both CREATE and EDIT:
Apply Core Principles: consult activity docs first, read relevant [reference files](./references/) for XAML structure and patterns, start minimal and iterate.

### For CREATE Requests

**Strategy:** Generate minimal working version, expect to iterate. Take it one activity at a time. Build incrementally and validate frequently.

Use the `Write` tool to create a new `.xaml` file with proper XAML boilerplate. Refer to [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for the complete XAML file anatomy template.

```
Write: file_path="{projectRoot}/Workflows/DescriptiveName.xaml"
       content=<valid XAML content with proper headers, namespaces, and body>
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

**Notes:** `--file-path` must be **relative to the project directory** (e.g., `"Workflows/SendEmail.xaml"`, not absolute). Always prefer `--file-path` for targeted checks (faster). Use `--skip-validation` only for quick cached-error checks. For slow projects, increase timeout: `uipcli rpa --timeout 600 get-errors --file-path "..."`.

### Step 3.2: Categorize and Fix

**Fix order:** Package → Structure → Type → Activity Properties → Logic. Always fix in this order — higher-category fixes often resolve lower-category errors automatically.

**1. Package Errors** — Missing namespace, unknown activity type, unresolved assembly
- Check `project.json` for current dependencies
- Install/update the package: `uipcli rpa install-or-update-packages --packages '[{"id":"PackageId"}]'` (omit `version` for latest)
- After install, activity docs become available at `.local/docs/packages/{PackageId}/` — re-read them to correct property issues downstream
- If package ID is uncertain, use `uipcli rpa find-activities --query "..."` to discover it

**2. Structural Errors** — Invalid XML, malformed elements, missing closing tags
- `Read` the XAML around the error location → `Edit` to fix XML structure
- Cross-check against [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for correct element nesting and namespace declarations

**3. Type Errors** — Wrong property type, invalid cast, type mismatch
- Check the activity doc at `.local/docs/packages/{PackageId}/activities/{ActivityName}.md` for correct types and enum values
- For dynamic activities, Integration Service connectors, JIT types: see [jit-custom-types-schema.md](./references/jit-custom-types-schema.md)
- If docs are unavailable, use `uipcli rpa get-default-activity-xaml` to see the expected default property types
- Push for package updates if docs are missing, inaccurate, or if `get-default-activity-xaml` cannot resolve
- If default activity activity XAML is unavailable, check for examples in the examples repository. See [examples-repository](./references/examples-repository.md)

**4. Activity Properties Errors** — Unknown properties, misconfigured conditional groups, missing required fields
- **Primary:** Read the activity doc — it documents all properties, conditional groups (`Visible When`), valid configurations, and enum values
- **Fallback:** `uipcli rpa get-default-activity-xaml` for the activity's default XAML template
- Pay attention to mutually exclusive property groups (OverloadGroups) — setting properties from multiple groups causes errors
- For IS/dynamic activities, check connection status: `uipcli is connections list <connector-key> --format json`

**5. Logic Errors** — Wrong behavior, incorrect expressions, business logic issues
- `Read` the XAML to understand current flow → `Edit` to correct
- Verify expression syntax matches project language (VB.NET vs C#)
- Use `uipcli rpa run-file` for runtime validation if static checks pass

**When stuck on one error:** consider deferring to the user if it's a minor configuration detail (e.g., fill in a connection, update a placeholder value). Just inform the user about what needs to be updated. If failing to resolve an activity altogether, consider using code activities as a last resort (see [invoke-code-activities.md](./references/invoke-code-activities.md)).

For detailed procedures (package resolution, JIT types, focus-activity debugging, iteration loop, smoke testing), see **[references/validation-and-fixing.md](./references/validation-and-fixing.md)**.

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

## CLI Error Recovery

For CLI error diagnosis and recovery patterns (IPC failures, auth errors, package issues, timeouts), see the **CLI Error Recovery** section in **[references/cli-reference.md](./references/cli-reference.md#cli-error-recovery)**.

**General strategy:** Do NOT retry the same failing command in a loop. Diagnose the root cause, apply the recovery action, then retry once. If it fails again, inform the user.

---

## Anti-Patterns

**Never** (items not already covered by Core Principles):
- Generate large, complex workflows in one go — build incrementally, one activity at a time
- Assume a create/edit succeeded without validating with `uipcli rpa get-errors`
- Stop the iteration loop before correctly rendering all activities
- Guess properties, types, inputs/outputs, or configurations without checking activity docs, or `get-default-activity-xaml`, or the examples repository, or the appropriate reference files
- Use incorrect/guessed keys with `uipcli rpa get-workflow-example` (always use keys from list results)
- Pass absolute paths to `--file-path` in `get-errors` (must be relative to project directory)
- Ask the user to choose a service provider without first checking project signals — auto-select when possible (Step 1.5)
- Retry failing CLI commands in a loop without diagnosing the root cause
- Skip Phase 0 (Studio readiness) — all subsequent phases depend on Studio IPC
- Use connector/dynamic activities without checking whether a connection exists (`uipcli is connections list`)

---

## Quality Checklist

Before handover, verify:

**Environment:**
- [ ] Studio is running and connected (Phase 0 completed)
- [ ] Project root is correctly identified and used consistently

**Discovery:**
- [ ] Activity docs in `{projectRoot}/.local/docs/packages/` consulted for relevant packages (or confirmed unavailable / package updated)
- [ ] Activity properties sourced from activity docs, `find-activities`, `get-default-activity-xaml`, `get-workflow-example` (priority ladder followed)
- [ ] Local project explored for existing patterns and conventions
- [ ] Service/provider disambiguation resolved — auto-selected or prompted only when ambiguous (Step 1.5)
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
