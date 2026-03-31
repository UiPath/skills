---
name: uipath-rpa-workflows
description: "Generate, edit, test, and run RPA workflows (XAML files) in UiPath Studio Desktop using uip CLI and filesystem operations. TRIGGER when: RPA project detected (project.json with UiPath dependencies AND .xaml workflow files); User mentions XAML workflows, RPA workflows, .xaml files, or UiPath Studio Desktop workflows; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, transaction processing, queue items, API calls, etc.) and a UiPath RPA/XAML project exists nearby; User asks about fixing XAML errors or workflow validation issues. DO NOT TRIGGER when: User is working with coded workflows (.cs files with [Workflow]/[TestCase] attributes — use uipath-coded-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-platform instead)."
---

# RPA Workflow Architect

Generate and edit RPA workflows using a **discovery-first approach** with **iterative error-driven refinement**. Always understand before acting, start simple, and validate continuously.

This skill uses `uip` CLI commands (via `Bash`) and Claude Code's built-in tools (`Read`, `Write`, `Edit`, `Glob`, `Grep`) to interact with UiPath Studio Desktop projects and manage workflow files.

## Core Principles

1. **Activity Docs Are the Source of Truth** — Installed packages may ship structured documentation at `{projectRoot}/.local/docs/packages/{PackageId}/`. When present, these docs contain source-accurate properties, types, defaults, enum values, conditional property groups, and working XAML examples. They eliminate guesswork and are more reliable than examples or CLI-retrieved defaults. Always check for them first; push for package updates if unavailable, or fallback to `get-default-activity-xaml` and/or `get-workflow-example`.
2. **Know Before You Write** — Never generate XAML blind. Never try to guess properties, types, or configurations. Understand the project structure, what packages are installed, what expression language is used, and what patterns existing workflows follow. The deeper your understanding, the fewer validation cycles you'll need.
3. **Use What You Know, Skip What You Don't Need** — If you already know the package ID and activity class name, go directly to its doc file — don't enumerate all packages first. If activity docs give you a complete XAML example, don't also call `get-default-activity-xaml`. Be efficient: the discovery steps are a priority ladder, not a mandatory checklist.
4. **Start Minimal, Iterate to Correct** — Build one activity at a time. Write the smallest working XAML, validate with `uip rpa get-errors --use-studio`, fix what breaks, repeat. Start with what you know works (default or example values, configurations). Complex workflows emerge from validated building blocks, not from generating everything at once.
5. **Validate After Every Change** — Never assume an edit succeeded. Always confirm with `uip rpa get-errors --use-studio`. Static validation catches most problems; `run-file` catches the rest.
6. **Fix Errors by Category** — Triage errors in order: Package (missing dependencies) → Structure (invalid XML) → Type (wrong property types) → Activity Properties (misconfigured activity) → Logic (wrong behavior). Fixing in this order avoids cascading false errors.

---

## CLI Output Format

All `uip` commands support `--output <format>` (table, json, yaml, plain).

**Always use `--output json`** for commands whose output you need to parse or act on (e.g., `get-errors`, `find-activities`, `list-workflow-examples`, `is connections list`). JSON output is structured, unambiguous, and avoids table-formatting surprises.

Use the default (table) only when displaying results directly to the user for readability.

---

## Tool Quick Reference

For the full CLI command reference (all tools, parameters, and error recovery), see **[references/cli-reference.md](./references/cli-reference.md)**.

Key commands at a glance: `find-activities`, `get-default-activity-xaml`, `get-errors`, `install-or-update-packages`, `run-file`, `list-workflow-examples`, `get-workflow-example`. For IS connectors: `is connectors list/get`, `is connections list/create/ping`, `is activities list`, `is resources list/describe/execute`.

**The CLI is fully self-documenting.** Append `--help` or `-h` at any level to discover commands, subcommands, and parameters: `uip --help`, `uip rpa --help`, `uip rpa get-default-activity-xaml --help`, `uip is --help`, `uip is connections --help`, etc.

---

## Supporting References

**Always check installed activity docs first** (`{projectRoot}/.local/docs/packages/`) before using the bundled references below. See [Step 1.2](#step-12-discover-activity-documentation-primary-source).

### Resolving Packages & Activity Docs

Follow this flow whenever you need to use an activity package:

#### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies` for the required package.

- **If the package IS in `project.json`** → note the installed version, proceed to Step 2. You may suggest updating to the latest for the best experience, but **never force an update** — respect the user's current version.
- **If the package is NOT in `project.json`** → discover and install the latest version:

```bash
# List latest versions including prerelease/beta (newest first) — DEFAULT
uip rpa get-versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json --use-studio

# List only stable versions (use when the user explicitly prefers stable)
uip rpa get-versions --package-id <PackageId> --project-dir "<PROJECT_DIR>" --output json --use-studio

# Install a specific version
uip rpa install-or-update-packages --packages '[{"id":"<PackageId>","version":"<version>"}]' --project-dir "<PROJECT_DIR>" --output json --use-studio

# Install without specifying version (auto-resolves: prerelease Studio → latest preview, stable Studio → latest stable)
uip rpa install-or-update-packages --packages '[{"id":"<PackageId>"}]' --project-dir "<PROJECT_DIR>" --output json --use-studio
```

**By default, use `--include-prerelease`** to get the absolute latest version (including beta/preview). Only omit it when the user explicitly asks for stable versions. Always prefer `uip rpa get-versions` over hardcoded version numbers — it queries the actual NuGet feeds configured for the project.

#### Step 2 — Find activity docs (priority order)

Once the package is installed, find the right documentation in this order:

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — these are auto-generated docs from the installed package version and are always the most accurate match. If present, use them as the **primary source** and stop here.
2. **Fall back to bundled reference docs** — if `.local/docs/` is missing or doesn't contain docs for this package, look in `../../references/activity-docs/{PackageId}/` and pick the **closest version folder** to what is installed:
   - Extract major.minor from the installed version (e.g., `[25.10.21]` → `25.10`)
   - List available doc folders: `ls ../../references/activity-docs/{PackageId}/`
   - Pick the closest match: exact major.minor if it exists, otherwise the nearest available folder
   - If the package was just installed (new), use the latest available folder

### Procedural Reference Files

Detailed procedures extracted from the main workflow phases:
- **[cli-reference.md](./references/cli-reference.md)** — Full `uip` CLI command reference guide (all tools, parameters, commands)
- **[environment-setup.md](./references/environment-setup.md)** — Phase 0 details: project root detection, Studio verification, authentication, and new project creation
- **[validation-and-fixing.md](./references/validation-and-fixing.md)** — Phase 3 details: package resolution, JIT custom types, focus-activity debugging, iteration loop, smoke testing
- **[connector-capabilities.md](./references/connector-capabilities.md)** — IS connector discovery, resource schema inspection, connection management

### Domain Reference Files

For XAML structure, control flow, and domain-specific patterns not covered by activity docs, consult these files (read them on-demand).

**For all activity package docs below:** always check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/` first — these are auto-generated from the installed package and are the most accurate. Only fall back to the bundled references when `.local/docs/` is unavailable. When using bundled references, pick the version folder closest to what is installed (see [Resolving Packages & Activity Docs § Step 2](#step-2--find-activity-docs-priority-order)).

- **[xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md)** — XAML file anatomy, workflow types, safety rules, common editing operations, reference examples, and ConnectorActivity internals. **CRITICAL: read before generating/creating/editing any XAML.**
- **System activities** (`UiPath.System.Activities`) — Core control flow activities (Assign, If/Else, For Each, While, Try Catch, etc.) and code integration (InvokeCode, InvokeWorkflow). `.local/docs/` → fallback: `../../references/activity-docs/UiPath.System.Activities/{closest}/activities/`. InvokeCode is a pragmatic fallback when dedicated activities have unresolvable issues.
- **[common-pitfalls.md](./references/common-pitfalls.md)** — Common pitfalls, constraints, scope requirements, property conflicts, gotchas, and issues that should be known before working with RPA workflows, along with strategies to avoid them
- **GSuite activities** (`UiPath.GSuite.Activities`) — Gmail, Google Sheets, Google Drive, Google Calendar patterns. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.GSuite.Activities/{closest}/activities/`.
- **Document Understanding activities** (`UiPath.DocumentUnderstanding.Activities`) — Classification, extraction, validation, PDF utilities. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.DocumentUnderstanding.Activities/{closest}/activities/`.
- **Word activities** (`UiPath.Word.Activities`) — WordApplicationScope, read/append/replace text, export to PDF. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Word.Activities/{closest}/activities/`.
- **PowerPoint activities** (`UiPath.Presentations.Activities`) — PowerPointApplicationScope, insert/replace/delete slides. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Presentations.Activities/{closest}/activities/`.
- **Excel activities** (`UiPath.Excel.Activities`) — Modern and classic styles, scope containers, iterators, read/write/format. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Excel.Activities/{closest}/activities/`.
- **Outlook Mail activities** (`UiPath.Mail.Activities`) — Classic Outlook mail patterns (not O365). `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Mail.Activities/{closest}/activities/`.
- **Office 365 Outlook activities** (`UiPath.MicrosoftOffice365.Activities`) — O365 mail patterns, triggers, filter expressions. `.local/docs/` → fallback: `../../references/activity-docs/UiPath.MicrosoftOffice365.Activities/{closest}/activities/`.
- **[project-structure.md](./references/project-structure.md)** — Project directory layout, project.json schema, common packages
- **[jit-custom-types-schema.md](./references/jit-custom-types-schema.md)** - How to get JIT custom types of dynamic activities.
- **[UI Automation guide](./references/ui-automation-guide.md)** (`UiPath.UIAutomation.Activities`) — UIA overview: selectors, target configuration, Object Repository, indication flow, sub-skills, and common pitfalls. **CRITICAL: read before generating/editing any UI Automation workflows.** For full activity details: `.local/docs/` → fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/`.

#### UI Automation References

For a quick overview of selectors, target configuration, indication flow, and common pitfalls, see [ui-automation-guide.md](./references/ui-automation-guide.md).

The UIA activity-docs version folder may contain additional guides (selector creation, target configuration, CV targeting, selector improvement). Discover them by globbing: `Glob: pattern="**/*.md" path="../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/"`. These are **reference docs to read and follow** — they are NOT invocable as slash commands. Read the relevant `.md` file and follow its steps using the `uip rpa` CLI commands directly.

For full activity details: `.local/docs/packages/UiPath.UIAutomation.Activities/` → fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/activities/`.

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

**Quick check:** Find `project.json` to establish `{projectRoot}`, run `uip rpa list-instances --output json` to verify Studio, and `uip rpa open-project` if needed.

**Expression language for new projects:** Prefer `VisualBasic` for Windows target framework projects.

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
- **Package not installed?** Install it first: `uip rpa install-or-update-packages --packages '[{"id":"UiPath.WebAPI.Activities"}]' --use-studio` — this also syncs docs if the package ships them.
- **Package installed but no docs?** Update to the latest version: `uip rpa install-or-update-packages --packages '[{"id":"UiPath.WebAPI.Activities"}]' --use-studio` (omit version to get latest) — newer releases are more likely to ship documentation.

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
| **You don't know the package** | `Glob` with `**/*.md` in `{projectRoot}/.local/docs/packages/` to list all doc files, then `Read` promising matches. The `.local/` folder is gitignored and hidden, so `Grep` will not find it — always use `Glob` + `Read` or `Bash: ls` to discover docs. |
| **Docs exist but activity isn't documented** | Use other activity docs in the same package as structural reference, fall back to `get-default-activity-xaml`. |
| **No docs for the package** | **Update the package first** (`uip rpa install-or-update-packages --use-studio`) -- this often adds docs. If still no docs, fall back to Steps 1.4-1.7. |
| **Package not installed** | **Install it first** (`uip rpa install-or-update-packages --use-studio`) -- both docs and `get-default-activity-xaml` require it. After install, check for docs before proceeding to fallbacks. |
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

Use `uip rpa find-activities --use-studio` when you need to find which activity implements a user-described action, discover activities not covered by installed docs, or get the exact fully qualified class name, type ID, and `isDynamicActivity` flag.

```bash
uip rpa find-activities --query "send mail" --limit 10 --output json --use-studio
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
uip rpa find-activities --query "send mail" --limit 5 --output json --use-studio

# Find weather-related activities
uip rpa find-activities --query "get weather" --output json --use-studio

# Find Excel read activities
uip rpa find-activities --query "read range" --limit 10 --output json --use-studio
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

Use `uip rpa get-default-activity-xaml --use-studio` to retrieve the activity's default XAML template. **Requires the package to be installed** (see [Step 1.2](#step-12-discover-activity-documentation-primary-source)). If activity docs exist with XAML examples, prefer those as your starting point -- they're richer than bare defaults.

The command handles both non-dynamic and dynamic activities.

#### For Non-Dynamic Activities

```bash
uip rpa get-default-activity-xaml --activity-class-name "UiPath.Core.Activities.WriteLine" --use-studio
```

#### For Dynamic Activities

```bash
uip is connections list # Find relevant connection ID, if any
uip rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id "{connectionId}" --use-studio

# Or, if no relevant connection, pass an empty string
uip rpa get-default-activity-xaml --activity-type-id "178a864d-90fd-43d3-a305-249b07ac0127" --connection-id "" --use-studio
```

**When to use this command:**
- Activity docs don't exist or don't cover this specific activity
- You need the exact bare-bones default XAML template for Studio compatibility
- You're working with dynamic activities that require runtime-resolved properties
- You need to verify the correct property names and default values when docs are ambiguous

**Key parameters:**
- `--activity-class-name`: For non-dynamic activities. Must be fully qualified (e.g., `UiPath.Core.Activities.WriteLine`)
- `--activity-type-id`: For dynamic activities. Use `uip rpa find-activities --use-studio` to find the exact type ID
- `--connection-id`: Optional, only used for dynamic activities. Discover available connections using `uip is connections list [connector-key]`

**For JIT custom types**, read the schema file:

```
Read: file_path="{projectRoot}/.project/JitCustomTypesSchema.json"
```

For more details, see **[jit-custom-types-schema.md](./references/jit-custom-types-schema.md)**

### Step 1.7: Search Examples Repository

Use when activity docs, `find-activities`, `get-default-activity-xaml`, and domain-specific [reference](./references/) files don't provide enough context — or when you need **full end-to-end workflow composition patterns**.

## Searching Examples

```bash
# Search by service tags (AND logic — all tags must match)
uip rpa list-workflow-examples --tags web --limit 10 --output json --use-studio

# Multiple tags narrow down results (AND logic — all tags must match)
uip rpa list-workflow-examples --tags jira,confluence --limit 10 --output json --use-studio

# Use prefix to filter by category
uip rpa list-workflow-examples --tags gmail --prefix "email-communication/" --limit 15 --output json --use-studio

# Once you identify relevant examples from the list operation, retrieve XAML content:
uip rpa get-workflow-example --key "email-communication/add-new-gmail-emails-to-keap-as-contacts.xaml" --use-studio
```

**Complete tag list:** `adobe-sign`, `asana`, `box`, `concur`, `confluence`, `database`, `document-understanding`, `docusign`, `dropbox`, `email-generic`, `excel`, `excel-online`, `freshbooks`, `freshdesk`, `github`, `gmail`, `google-calendar`, `google-docs`, `google-drive`, `google-sheets`, `gsuite`, `hubspot`, `intacct`, `jira`, `mailchimp`, `marketo`, `microsoft-365`, `onedrive`, `outlook`, `outlook-calendar`, `pdf`, `powerpoint`, `productivity`, `quickbooks`, `salesforce`, `servicenow`, `sharepoint`, `shopify`, `slack`, `smartsheet`, `stripe`, `teams`, `testing`, `trello`, `web`, `webex`, `word`, `workday`, `zendesk`, `zoom`

## When to Use

- Activity docs, `find-activities`, and `get-default-activity-xaml` didn't provide enough context
- You need end-to-end workflow patterns showing multiple activities composed together
- You need to understand service-specific integration patterns (e.g., OAuth flows, trigger setups)
- You're building a complex multi-activity workflow and want to see how others structured similar automations

## Studying Retrieved Examples

When studying repository examples from `uip rpa get-workflow-example --use-studio`:
- The command returns the full XAML content directly
- Parse the namespace declarations at the top to identify required packages
- Examine the exact set of activity configurations, properties, variables, types, and set values. These are valid configurations

### Step 1.8: Get Current Context (As Needed)

Before generating, understand reusable elements by combining multiple reads:

```
Read: file_path="{projectRoot}/project.json"                → project definition (deps, expression language)
Glob: pattern="**/*" path="{projectRoot}/.objects/"         → explore object repository
Read: file_path="{projectRoot}/.objects/.metadata"          → object repository metadata
Read: file_path="{projectRoot}/Main.xaml"                   → existing workflow (variables, arguments, imports)
Glob: pattern="**/*" path="{projectRoot}/.settings/"        → settings profiles
Bash: uip is connections list --output json              → available Integration Service connections
Bash: uip is connectors list --output json               → available connectors
```

This surfaces variables, arguments, imports, expression language, available connections, and reusable project-level resources.

### Step 1.9: Discover Connector Capabilities (For IS/Connector Workflows)

When the workflow involves Integration Service connectors (dynamic activities), explore capabilities and manage connections before writing XAML. See **[references/connector-capabilities.md](./references/connector-capabilities.md)** for the full procedure (activity/resource discovery, connection management, schema inspection).

---

## Phase 2: Generate or Edit

### Guidelines for both CREATE and EDIT:
Apply Core Principles: consult activity docs first, read relevant [reference files](./references/) for XAML structure and patterns, start minimal and iterate.

### UI Automation Workflows — Target Configuration Gate

**Before writing any XAML that contains UI activities** (Click, TypeInto, GetText, etc.), every UI element target must be configured through the `uia-configure-target` skill flow. This means: for each distinct element the workflow interacts with, read and follow the `uia-configure-target` skill steps (found in the UIA activity-docs). The skill handles snapshot capture, element discovery, selector generation, selector improvement, and Object Repository registration. All steps must complete — do not stop after getting a raw selector.

**Do NOT manually call low-level `uip rpa uia` CLI commands** (`snapshot capture`, `snapshot filter`, `selector-intelligence get-default-selector`) to build selectors outside of the skill flow. These are internal tools used *by* the skill — calling them directly skips selector improvement and OR registration, producing fragile selectors that aren't tracked in the project.

**Do NOT launch the target application before running `uia-configure-target`.** The skill's first steps (CREATE-1 + CREATE-2) capture the top-level window tree and search for the app. Only if the app is not found in the window list should you launch it — and then re-run the capture. Launching preemptively creates duplicate instances and risks targeting the wrong window.

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
- If certain activity properties or arguments are unknown, provide default values (e.g., placeholders, default type values, or use `uip rpa get-default-activity-xaml --use-studio`)

### Step 3.1: Check for Errors

```bash
# Check errors for a specific file (preferred — faster, especially in large projects):
uip rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --output json --use-studio

# Check errors for the entire project:
uip rpa get-errors --output json --use-studio

# Use cached errors (skip re-validation — faster but may be stale):
uip rpa get-errors --file-path "Workflows/MyWorkflow.xaml" --skip-validation --output json --use-studio
```

**Notes:** `--file-path` must be **relative to the project directory** (e.g., `"Workflows/SendEmail.xaml"`, not absolute). Always prefer `--file-path` for targeted checks (faster). Use `--skip-validation` only for quick cached-error checks. For slow projects, increase timeout: `uip rpa --timeout 600 get-errors --file-path "..." --use-studio`.

### Step 3.2: Categorize and Fix

**Fix order:** Package → Structure → Type → Activity Properties → Logic. Always fix in this order — higher-category fixes often resolve lower-category errors automatically.

**1. Package Errors** — Missing namespace, unknown activity type, unresolved assembly
- Check `project.json` for current dependencies
- Install/update the package: `uip rpa install-or-update-packages --packages '[{"id":"PackageId"}]' --use-studio` (omit `version` for latest)
- After install, activity docs become available at `.local/docs/packages/{PackageId}/` — re-read them to correct property issues downstream
- If package ID is uncertain, use `uip rpa find-activities --query "..." --use-studio` to discover it

**2. Structural Errors** — Invalid XML, malformed elements, missing closing tags
- `Read` the XAML around the error location → `Edit` to fix XML structure
- Cross-check against [xaml-basics-and-rules.md](./references/xaml-basics-and-rules.md) for correct element nesting and namespace declarations

**3. Type Errors** — Wrong property type, invalid cast, type mismatch
- Check the activity doc at `.local/docs/packages/{PackageId}/activities/{ActivityName}.md` for correct types and enum values
- For dynamic activities, Integration Service connectors, JIT types: see [jit-custom-types-schema.md](./references/jit-custom-types-schema.md)
- If docs are unavailable, use `uip rpa get-default-activity-xaml --use-studio` to see the expected default property types
- Push for package updates if docs are missing, inaccurate, or if `get-default-activity-xaml` cannot resolve
- If default activity activity XAML is unavailable, check for examples in the examples repository (`list-workflow-examples` and `get-workflow-example`)

**4. Activity Properties Errors** — Unknown properties, misconfigured conditional groups, missing required fields
- **Primary:** Read the activity doc — it documents all properties, conditional groups (`Visible When`), valid configurations, and enum values
- **Fallback:** `uip rpa get-default-activity-xaml --use-studio` for the activity's default XAML template
- Pay attention to mutually exclusive property groups (OverloadGroups) — setting properties from multiple groups causes errors
- For IS/dynamic activities, check connection status: `uip is connections list <connector-key> --output json`

**5. Logic Errors** — Wrong behavior, incorrect expressions, business logic issues
- `Read` the XAML to understand current flow → `Edit` to correct
- Verify expression syntax matches project language (VB.NET vs C#)
- Use `uip rpa run-file --use-studio` for runtime validation if static checks pass

**When stuck on one error:** consider deferring to the user if it's a minor configuration detail (e.g., fill in a connection, update a placeholder value). Just inform the user about what needs to be updated. If failing to resolve an activity altogether, consider using code activities as a last resort (find `InvokeCode.md` under the latest version folder in `../../references/activity-docs/UiPath.System.Activities/`).

For detailed procedures (package resolution, JIT types, focus-activity debugging, iteration loop, smoke testing, runtime selector recovery), see **[references/validation-and-fixing.md](./references/validation-and-fixing.md)**.

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
- Manually craft UI selectors by calling low-level `uip rpa uia` CLI commands (`snapshot capture`, `snapshot filter`, `selector-intelligence get-default-selector`) outside of the `uia-configure-target` skill flow — this skips selector improvement and OR registration
- Assume a create/edit succeeded without validating with `uip rpa get-errors --use-studio`
- Stop the iteration loop before correctly rendering all activities
- Guess properties, types, inputs/outputs, or configurations without checking activity docs, or `get-default-activity-xaml`, or the examples repository, or the appropriate reference files
- Use incorrect/guessed keys with `uip rpa get-workflow-example --use-studio` (always use keys from list results)
- Pass absolute paths to `--file-path` in `get-errors` (must be relative to project directory)
- Ask the user to choose a service provider without first checking project signals — auto-select when possible (Step 1.5)
- Retry failing CLI commands in a loop without diagnosing the root cause
- Skip Phase 0 (Studio readiness) — all subsequent phases depend on Studio IPC
- Use connector/dynamic activities without checking whether a connection exists (`uip is connections list`)

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
- [ ] For connector workflows: connections verified with `uip is connections list`

**UI Automation Targets (if applicable):**
- [ ] Every UI element target configured through the `uia-configure-target` skill flow (not raw CLI commands)
- [ ] Selectors improved (selector improvement step completed, not just raw `get-default-selector` output)
- [ ] All targets registered in the Object Repository (screens and elements created via OR commands)

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
