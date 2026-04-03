---
name: uipath-coded-workflows
description: "Full coding assistant for UiPath coded automations — create, edit, build, pack, run, and debug coded workflows, test cases, and project configuration. TRIGGER when: Coded workflow project detected (project.json with UiPath dependencies AND .cs files with [Workflow]/[TestCase] attributes); User references coded workflows, coded automations, coded test cases, or C#-based UiPath automations; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, queues, API calls, Integration Service connectors, etc.) and a UiPath coded workflow project exists nearby; User asks about UiPath activities or how to use them in code; User wants to call an Integration Service connector (Jira, Salesforce, ServiceNow, Slack, etc.) from a coded workflow using IntegrationConnectorService. DO NOT TRIGGER when: User is working with XAML/RPA workflows (use uipath-rpa-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-platform instead)."
---

# UiPath Coded Workflows Assistant

Full coding assistant for creating, editing, managing and running UiPath coded automation projects.

## When to Use This Skill

- User wants to **create a new** UiPath coded automation project
- User wants to **add** a coded workflow or test case to an existing project
- User wants to **edit** an existing coded workflow or test case
- User wants to **modify project configuration** (dependencies, entry points)
- User asks about **UiPath activities** or how to automate something with UiPath coded workflows
- User wants to **add dependencies** to a project
- User wants to **create a test case** with assertions (can be in any project type)
- User wants to **add helper/utility classes** or models to a project (Coded Source Files)
- User wants to **validate, build, pack and run** a coded workflow project

## Precondition: Project Context

Before doing any work, check if `.claude/rules/project-context.md` exists in the project directory.

**If the file exists** → check for staleness:
1. Read the first line of `.claude/rules/project-context.md` to extract the metadata comment: `<!-- discovery-metadata: cs=N xaml=N deps=N -->`
2. Count current files: Glob `**/*.cs` (excluding `.local/` and `.codedworkflows/`) and `**/*.xaml` in the project directory
3. Count current dependencies: read `project.json` and count keys in the `.dependencies` object
4. Compare the current counts against the stored metadata values
5. For each count (cs, xaml, deps), compute the percentage difference: `abs(current - stored) / max(stored, 1) * 100`
6. If **any individual count differs by 60–70% or more** → run the discovery flow below
7. If all counts are within the threshold → context is fresh, proceed with the skill workflow

**If the file does NOT exist** → run the discovery flow below.
**Discovery flow** (used for both missing and stale context):
1. Trigger the `uipath-project-discovery-agent` and wait for it to complete
2. The agent returns the generated context document as its response
3. Write the returned content to **both**:
   - `.claude/rules/project-context.md` (create `.claude/rules/` directory if needed) — auto-loaded by Claude Code in future sessions
   - `AGENTS.md` at project root — read by UiPath Autopilot in Studio Desktop. If `AGENTS.md` already exists, look for `<!-- PROJECT-CONTEXT:START -->` / `<!-- PROJECT-CONTEXT:END -->` markers and replace only between them; if no markers exist, append the fenced block at the end
4. Then proceed with the skill workflow

## Quick Start

**Step 0 — Resolve `PROJECT_DIR` first** (applies to ALL operations below):

Before creating or modifying anything, you MUST determine which project to work with. Do NOT skip this step. Do NOT assume no project exists.

`PROJECT_DIR` is the absolute path to the root folder of a UiPath project (the folder that contains `project.json`).

**Step 0a — Determine the path** (use the first rule that matches):
1. **Explicit path** — The user provided a directory path → use it as-is.
2. **Project name reference** — The user mentioned a project by name (e.g., "the MyAutomation project") → search the file system for a folder with that name containing a `project.json`.
3. **Detect from running Studio** — No path or name given → run this command:
   ```bash
   uip rpa list-instances --output json --use-studio
   ```
   Parse the JSON response. If `Data` is a non-empty array, each entry has a `ProjectDirectory` field containing the absolute path of the open project. Use it:
   - **One instance** → use its `ProjectDirectory`.
   - **Multiple instances** → pick the one whose `ProjectDirectory` best matches the user's context (or ask the user which project).

   Example response:
   ```json
   { "Data": [{ "ProcessId": 11764, "ProjectDirectory": "C:\\Users\\me\\Documents\\UiPath\\MyProject" }] }
   ```
   → `PROJECT_DIR` = `C:\Users\me\Documents\UiPath\MyProject`

   This works regardless of where Claude Code was launched from (Studio terminal, external terminal, etc.).
4. **Fall back to current working directory** — If `Data` is an empty array (no Studio instance is running), use the current working directory.

**Step 0b — Ensure a project exists at that path**:
- Check whether `<PROJECT_DIR>/project.json` exists.
  - **If yes** → A project already exists here. Proceed with this directory.
  - **If no** → No project exists yet. Create one (see below).

**Creating a new project** (ONLY when no project is open and none exists at cwd or user gives a specific path):

**ALWAYS use `uip rpa create-project --use-studio`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually:
```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --studio-dir "<STUDIO_DIR>" --output json --use-studio
```
Use `--template-id TestAutomationProjectTemplate` for test projects, or `--template-id LibraryProcessTemplate` for libraries.

After creation:
1. **Read the scaffolded files** — `create-project` generates starter files (e.g. `Main.cs`, `project.json`). Read them before making changes so you build on valid defaults rather than overwrite blindly
2. Add workflow/test case/source files and **edit** `project.json` as needed (add dependencies, entry points — do NOT rewrite the entire file)
3. **Validate each file** (Critical Rule #14) — run the validation loop on every `.cs` file you create or edit until it compiles cleanly

See [references/operations-guide.md § Initialize a New Project](references/operations-guide.md) for the full step-by-step procedure.

**Adding to existing project:**
1. **Perform API Discovery** — Search for and read 5 existing .cs files to learn project patterns
2. Identify operation type (workflow, test case, or source file)
3. Follow relevant operation guide ([references/operations-guide.md](references/operations-guide.md))
4. Update `project.json` as needed
5. Use appropriate template from `assets/`
6. Add `using` statements based on packages in `project.json`
7. **Validate each file** (Critical Rule #14) — run the validation loop on every `.cs` file you create or edit until it compiles cleanly

## Critical Rules

1. **NEVER create a project without first confirming no project already exists.** Follow the Step 0a resolution order above: if the user gave an explicit path or project name, check whether `project.json` exists there. If no path was given, run `uip rpa list-instances --output json --use-studio` — if a Studio instance is running with a `ProjectDirectory`, that IS the project. Only create a new project when you have confirmed no existing project matches AND the user explicitly requests creation (or no project exists at cwd). This prevents accidentally creating nested projects or working in the wrong directory.
2. **Prefer UiPath built-in activities** for Orchestrator integration (`system.GetAsset`, `system.AddQueueItem`), UI automation (`uiAutomation.*`), and document handling (`excel.*`, `word.*`) — these provide reliability, logging, and Studio-level support. **Prefer plain .NET / third-party packages** for pure data transforms, HTTP calls to non-Orchestrator endpoints, parsing, string manipulation, and anything where code is clearly the right tool. When no built-in activity exists, find a well-known NuGet package — inspect it with `uip rpa inspect-package --use-studio` first, then add it to `project.json`.
3. **ALWAYS inherit from `CodedWorkflow`** base class for workflow and test case classes (NOT for Coded Source Files — see below).
4. **ALWAYS use `[Workflow]` or `[TestCase]` attribute** on the `Execute` method (workflows/test cases only).
5. **Generate the companion `.cs.json` metadata file** for each `.cs` workflow/test case file (NOT for Coded Source Files). When the project is managed in UiPath Studio, Studio may regenerate these — only create them when scaffolding new files outside Studio.
6. **Update `project.json` entry points** when adding or removing **workflow** files (NOT for Coded Source Files).
7. **Update `project.json` fileInfoCollection** when adding or removing **test case** files (NOT for Coded Source Files).
8. **Use v25.x dependency versions** by default (UiPath.CodedWorkflows is implicit in v25.x).
9. **One workflow/test case class per file**, class name must match file name. Coded Source Files may group related types (e.g. multiple models or enums in one file).
10. **Namespace = sanitized project name** from `project.json`. Sanitize: remove spaces and invalid C# identifier characters, replace hyphens/spaces with `_`, ensure it doesn't start with a digit. E.g. project name `"My Invoice-App 2"` becomes namespace `My_Invoice_App_2`. For files in subfolders, append the folder name: `ProjectName.FolderName`.
11. **Entry method is always named `Execute`** (workflows/test cases only).
12. **ALWAYS ensure required package dependencies are in `project.json`** when using a service. Each service on `CodedWorkflow` requires its corresponding NuGet package — without it you get `CS0103: The name 'xxx' does not exist in the current context`. See the Service-to-Package mapping below.
13. **Use Coded Source Files for reusable code** — extract models, helper classes, utilities, and shared logic into plain `.cs` files that don't inherit from `CodedWorkflow`. These have NO `.cs.json`, NO entry point, NO fileInfoCollection, and NO `[Workflow]`/`[TestCase]` attribute.
14. **ALWAYS validate each file until error-free after creating or editing it.** Never consider a file "done" until validation returns no errors. Follow this loop after every create/edit:
    1. Run `uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --output json --use-studio` — this forces Studio to re-analyze the specific file and returns a JSON result with validation status and any errors found
    2. If errors exist in the response: read the error messages, fix the code, and go back to step 1
    3. Repeat until validation returns zero errors (max 5 fix attempts)
    4. Only then proceed to run the workflow or report success to the user
    5. If after 5 fix attempts errors persist, stop and present the remaining errors to the user — they may require domain knowledge, missing dependencies, or environment-specific fixes you cannot resolve autonomously
    Note: `get-errors` returns the cached error state without re-analyzing — use `validate` instead when files have been changed outside Studio. For the full fix-one-thing rule and iteration loop, see [shared/validation-loop.md](../shared/validation-loop.md).
15. **For UI automation workflows**, follow the target configuration approach in [ui-automation-guide.md](references/ui-automation-guide.md). For shared UIA procedures (prerequisites, target configuration, debug workflow, selector recovery, multi-step flows), see the [shared/](../shared/) files referenced from that guide.

### UI Automation References

Shared UIA procedures (used by both coded and RPA skills):
- [Prerequisites and version check](../shared/uia-prerequisites.md)
- [Configure target workflows](../shared/uia-configure-target-workflows.md)
- [Debug workflow procedure](../shared/uia-debug-workflow.md)
- [Selector recovery](../shared/uia-selector-recovery.md)
- [Multi-step UI flows](../shared/uia-multi-step-flows.md)

For C#-specific patterns (workflow pattern, screen handle affinity, descriptor resolution, common pitfalls), see [ui-automation-guide.md](references/ui-automation-guide.md).

The UIA activity-docs version folder contains skill files (`uia-configure-target`, `uia-improve-selector`) and additional guides (selector creation, CV targeting). Discover them by globbing: `Glob: pattern="**/*.md" path="../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/"`. These are **reference docs to read and follow** — they are NOT invocable as slash commands. Read the relevant `.md` file and follow its steps using the `uip rpa` CLI commands directly.

For full API details: `.local/docs/packages/UiPath.UIAutomation.Activities/` → fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/coded/`.

## Task Navigation

Choose your task to find the right reference files. **For any activity package docs**, always follow the doc resolution order from [Resolving Packages & Activity Docs § Step 2](#step-2--find-activity-docs-priority-order): check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/` first, then fall back to the bundled references below.

| I need to... | Read these |
|-------------|-----------|
| **Create a new project** | Quick Start above → [operations-guide.md § Initialize](references/operations-guide.md) |
| **Add/edit a workflow** | [operations-guide.md § Add Workflow](references/operations-guide.md) → [coding-guidelines.md](references/coding-guidelines.md) |
| **Add a test case** | [operations-guide.md § Add Test Case](references/operations-guide.md) |
| **Write UI automation** | [ui-automation-guide.md](references/ui-automation-guide.md) → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.UIAutomation.Activities/{closest}/coded/` → [operations-guide.md § Indicate](references/operations-guide.md) |
| **Use Excel/Word/Mail/etc.** | Service table below → `.local/docs/packages/{PackageId}/` → fallback: `../../references/activity-docs/{PackageId}/{closest}/coded/` |
| **Call an Integration Service connector** | [references/integration-service.md](references/integration-service.md) — use [uipath-development skill](../uipath-platform//SKILL.md) first to resolve connector key, connection id, object name, httpMethod, path, and parameter types. **Before writing any Create/Update call:** run Step 1b in that guide to check for `"type": "multipart"` params in the raw metadata file — if found, pass `multipartParameters: new()` to `ExecuteAsync` |
| **Use Office 365 / Google** | Service table below → [codedworkflow-reference.md § Integration Service](references/codedworkflow-reference.md) |
| **Use Azure services** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Azure.Activities/{closest}/coded/` |
| **Use Google Cloud (GCP)** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.GoogleCloud.Activities/{closest}/coded/` |
| **Use Exchange Server** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.ExchangeServer.Activities/{closest}/coded/` |
| **Use System Center** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.SystemCenter.Activities/{closest}/coded/` |
| **Use Amazon Web Services** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.AmazonWebServices.Activities/{closest}/coded/` |
| **Use Amazon WorkSpaces** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.AmazonWorkSpaces.Activities/{closest}/coded/` |
| **Use Azure AD** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.AzureActiveDirectory.Activities/{closest}/coded/` |
| **Use Azure WVD** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.AzureWVD.Activities/{closest}/coded/` |
| **Use Active Directory** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.ActiveDirectory.Activities/{closest}/coded/` |
| **Use Citrix** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.Citrix.Activities/{closest}/coded/` |
| **Use Hyper-V** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.HyperV.Activities/{closest}/coded/` |
| **Use NetIQ eDirectory** | Service table below → `.local/docs/` → fallback: `../../references/activity-docs/UiPath.NetIQeDirectory.Activities/{closest}/coded/` |
| **Build/run/validate** | [cli-reference.md](references/cli-reference.md) |
| **Add a NuGet package** | [operations-guide.md § Add Dependency](references/operations-guide.md) → [third-party-packages-guide.md](references/third-party-packages-guide.md) |
| **Troubleshoot errors** | [coding-guidelines.md § Common Issues](references/coding-guidelines.md) |
| **Review coding rules** | [coding-guidelines.md](references/coding-guidelines.md) (using statements, best practices, anti-patterns) |

## Three Types of .cs Files

| Type | Base Class | Attribute | `.cs.json` | Entry Point | Purpose |
|------|-----------|-----------|------------|-------------|---------|
| **Coded Workflow** | `CodedWorkflow` | `[Workflow]` | Yes | Yes | Executable automation logic |
| **Coded Test Case** | `CodedWorkflow` | `[TestCase]` | Yes | Yes | Automated test with assertions |
| **Coded Source File** | None (plain C#) | None | No | No | Reusable models, helpers, utilities, hooks |

## Service-to-Package Dependency Mapping

Each service available on the `CodedWorkflow` base class is injected by UiPath Studio **only when its corresponding NuGet package** is listed in `project.json` `dependencies`. If the package is missing, the service property won't exist and you'll get a compile error.

### Commonly used packages
These packages are typically included in most projects. **Always check `project.json` `dependencies`** to confirm which are actually present before using their services — not all projects include all of them:

| Service Property | Required Package in `project.json` |
|-----------------|-------------------------------------|
| `system` | `UiPath.System.Activities` `[25.12.2]` |
| `testing` | `UiPath.Testing.Activities` `[25.10.0]` |
| `uiAutomation` | `UiPath.UIAutomation.Activities` `[25.10.21]` |

### Integration Service package (add when calling connectors from code)

| API Class | Required Package in `project.json` | Reference |
|---|---|---|
| `IntegrationConnectorService` | `UiPath.IntegrationService.Activities` `[1.24.0]` | [references/integration-service.md](references/integration-service.md) |

Use `IntegrationConnectorService.Create(services.Container).ExecuteAsync(...)` to call any connector (Jira, Salesforce, ServiceNow, Slack, etc.) directly. Requires the connector key, connection id, object name, HTTP method, path, and parameter buckets — all resolved up-front via the `uipath-development` skill.

### Domain-specific packages (add only when needed)
These packages provide the `excel`, `word`, `powerpoint`, `mail`, `office365`, and `google` services. Add them to `project.json` `dependencies` when the workflow uses the corresponding service.

| Service Property | Required Package in `project.json` |
|-----------------|-------------------------------------|
| `excel` | `UiPath.Excel.Activities` `[3.3.1]` |
| `word` | `UiPath.Word.Activities` `[2.3.1]` |
| `powerpoint` | `UiPath.Presentations.Activities` `[2.3.1]` |
| `mail` | `UiPath.Mail.Activities` `[2.5.10]` |
| `office365` | `UiPath.MicrosoftOffice365.Activities` `[3.6.10]` |
| `google` | `UiPath.GSuite.Activities` `[3.6.10]` |

### Infrastructure & Cloud packages (add only when needed)
These packages provide services for cloud platforms, virtualization, directory services, and IT infrastructure automation. Add them to `project.json` `dependencies` when the workflow uses the corresponding service.

| Service Property | Required Package in `project.json` | API Reference |
|-----------------|-------------------------------------|---------------|
| `azure` | `UiPath.Azure.Activities` | `../../references/activity-docs/UiPath.Azure.Activities/{latest}/coded/` |
| `gcp` | `UiPath.GoogleCloud.Activities` | `../../references/activity-docs/UiPath.GoogleCloud.Activities/{latest}/coded/` |
| `exchangeserver` | `UiPath.ExchangeServer.Activities` | `../../references/activity-docs/UiPath.ExchangeServer.Activities/{latest}/coded/` |
| `systemCenter` | `UiPath.SystemCenter.Activities` | `../../references/activity-docs/UiPath.SystemCenter.Activities/{latest}/coded/` |
| `aws` | `UiPath.AmazonWebServices.Activities` | `../../references/activity-docs/UiPath.AmazonWebServices.Activities/{latest}/coded/` |
| `awrks` | `UiPath.Amazon.Workspaces.Activities` | `../../references/activity-docs/UiPath.AmazonWorkSpaces.Activities/{latest}/coded/` |
| `azureAD` | `UiPath.AzureActiveDirectory.Activities` | `../../references/activity-docs/UiPath.AzureActiveDirectory.Activities/{latest}/coded/` |
| `azureWVD` | `UiPath.AzureWVD.Activities` | `../../references/activity-docs/UiPath.AzureWVD.Activities/{latest}/coded/` |
| `activeDirectoryDomainServices` | `UiPath.ActiveDirectory.Activities` | `../../references/activity-docs/UiPath.ActiveDirectory.Activities/{latest}/coded/` |
| `citrix` | `UiPath.Citrix.Activities` | `../../references/activity-docs/UiPath.Citrix.Activities/{latest}/coded/` |
| `hyperv` | `UiPath.HyperV.Activities` | `../../references/activity-docs/UiPath.HyperV.Activities/{latest}/coded/` |
| `netiq` | `UiPath.NetIQeDirectory.Activities` | `../../references/activity-docs/UiPath.NetIQeDirectory.Activities/{latest}/coded/` |

> **Note:** The `office365` and `google` services require **Integration Service connections** configured in UiPath Automation Cloud. They inject both a service property (`office365` / `google`) and a `connections` property for accessing configured connection instances. `office365` provides Mail, Calendar, Excel (cloud), OneDrive, and SharePoint via Microsoft Graph API. `google` provides Gmail, Google Calendar, Google Drive, Google Sheets, and Google Docs via Google Workspace APIs. Both use OAuth tokens managed by Integration Service — see [references/codedworkflow-reference.md § Integration Service Connections](references/codedworkflow-reference.md).

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
   > **Important:** The `.local/` folder is gitignored and hidden, so `Grep` will not find it. Always use `Glob` + `Read` or `Bash: ls` to discover and search docs inside `.local/docs/`.
2. **Fall back to bundled reference docs** — if `.local/docs/` is missing or doesn't contain docs for this package, look in `../../references/activity-docs/{PackageId}/` and pick the **closest version folder** to what is installed:
   - Extract major.minor from the installed version (e.g., `[25.10.21]` → `25.10`)
   - List available doc folders: `ls ../../references/activity-docs/{PackageId}/`
   - Pick the closest match: exact major.minor if it exists, otherwise the nearest available folder
   - If the package was just installed (new), use the latest available folder

**Resolving `{latest}`:** Throughout this document, `{latest}` means "list the version folders under the package directory and pick the highest one." When the project already has the package installed, prefer the docs version closest to the installed version instead.

📖 **Using statements rules and best practices**: [references/coding-guidelines.md](references/coding-guidelines.md)

## CodedWorkflow Base Class

All workflow and test case files inherit from `CodedWorkflow`, which provides built-in methods (`Log`, `Delay`, `RunWorkflow`), service properties (mapped in the table above), and the `workflows` property for strongly-typed invocation of other workflows. It can be extended with Before/After hooks via `IBeforeAfterRun`.

📖 **Full reference** (methods, invocation patterns, hooks): [references/codedworkflow-reference.md](references/codedworkflow-reference.md)

## Project Structure Reference

```
ProjectName/
├── project.json              # Project configuration (dependencies, entry points, runtime options)
├── project.uiproj            # Simple project descriptor (Name, ProjectType, MainFile)
├── Main.cs                   # Main entry point workflow (CodedWorkflow + [Workflow])
├── Main.cs.json              # Metadata for Main.cs (DisplayName, Arguments)
├── [OtherWorkflow].cs        # Additional workflow/test case files
├── [OtherWorkflow].cs.json   # Metadata for each workflow/test case .cs file
├── [HelperClass].cs          # Coded Source File — plain C# class (NO .cs.json, NO entry point)
├── [Models].cs               # Coded Source File — data models, DTOs, enums
├── .codedworkflows/          # Auto-generated (ConnectionsFactory.cs, ConnectionsManager.cs)
├── .objects/                 # Object Repository metadata
├── .project/
│   ├── PackageBindingsMetadata.json
│   └── design.json
├── .settings/Design/         # IDE design settings
├── .tmh/config.json          # Telemetry config
└── .variations/              # (Tests only) data-driven test parameters
```

> **Important: Auto-generated coded workflow artifacts** — Files under `.codedworkflows/` (such as `ObjectRepository.cs`, `ConnectionsFactory.cs`, `ConnectionsManager.cs`, `WorkflowRunnerService.cs`) are **only generated by Studio when the project contains at least one coded workflow (`.cs`) file**. If the project only has XAML workflows, these files will not exist. When adding the first coded workflow to a project, even creating an empty `.cs` file is enough to trigger Studio to generate these artifacts — no need to validate first. Do not create or edit these files manually.

📖 **Design guidelines**: See [assets/project-structure-examples.md](assets/project-structure-examples.md)

## Templates

📁 **Location**: `assets/`

All file templates with ready-to-use code:
- **Workflow templates** → [assets/codedworkflow-template.md](assets/codedworkflow-template.md)
- **Test case templates** → [assets/testcase-template.md](assets/testcase-template.md)
- **Helper class templates** → [assets/helper-utility-template.md](assets/helper-utility-template.md)
- **JSON/config templates** → [assets/json-template.md](assets/json-template.md) (project.json, .cs.json, project.uiproj)
- **Project structure examples** → [assets/project-structure-examples.md](assets/project-structure-examples.md)
- **Before/After hooks template** → [assets/before-after-hooks-template.md](assets/before-after-hooks-template.md)

## Activity Examples & References

**Always check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/` first** — these are auto-generated from the installed package and are the most accurate. Only fall back to the bundled references below when `.local/docs/` is unavailable.

Bundled reference docs live in `../../references/activity-docs/{PackageId}/{Version}/coded/` — pick the version folder closest to what is installed in the project (see [Resolving Packages & Activity Docs § Step 2](#step-2--find-activity-docs-priority-order)).

Available reference packages:
- **Document & productivity:** `UiPath.Excel.Activities`, `UiPath.Word.Activities`, `UiPath.Presentations.Activities`, `UiPath.Mail.Activities`, `UiPath.MicrosoftOffice365.Activities`, `UiPath.GSuite.Activities`
- **Cloud platforms:** `UiPath.Azure.Activities`, `UiPath.GoogleCloud.Activities`, `UiPath.AmazonWebServices.Activities`
- **Virtualization & infrastructure:** `UiPath.AmazonWorkSpaces.Activities`, `UiPath.AzureWVD.Activities`, `UiPath.Citrix.Activities`, `UiPath.HyperV.Activities`
- **Identity & directory:** `UiPath.AzureActiveDirectory.Activities`, `UiPath.ActiveDirectory.Activities`, `UiPath.NetIQeDirectory.Activities`
- **IT automation:** `UiPath.ExchangeServer.Activities`, `UiPath.SystemCenter.Activities`
- **Core:** `UiPath.System.Activities`, `UiPath.Testing.Activities`, `UiPath.UIAutomation.Activities`

## Completion Output

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — whether all files passed validation (or remaining errors if max retries hit)
3. **How to run** — the `uip rpa run-file --use-studio` command to execute the workflow (if applicable)
4. **Next steps** — any follow-up actions the user should take (e.g. configure Integration Service connections, add Object Repository elements)
