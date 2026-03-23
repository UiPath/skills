---
name: uipath-coded-workflows
description: "Full coding assistant for UiPath coded automations — create, edit, build, pack, run, and debug coded workflows, test cases, and project configuration. TRIGGER when: Coded workflow project detected (project.json with UiPath dependencies AND .cs files with [Workflow]/[TestCase] attributes); User references coded workflows, coded automations, coded test cases, or C#-based UiPath automations; User asks to automate a task (Excel, email, web scraping, UI automation, database, PDF, queues, API calls, etc.) and a UiPath coded workflow project exists nearby; User asks about UiPath activities or how to use them in code. DO NOT TRIGGER when: User is working with XAML/RPA workflows (use uipath-rpa-workflows instead), or asking about Orchestrator/deployment/CLI setup (use uipath-development instead)."
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

## Quick Start

**Step 0 — Resolve `PROJECT_DIR` first** (applies to ALL operations below):

Before creating or modifying anything, you MUST determine which project to work with. Do NOT skip this step. Do NOT assume no project exists.

`PROJECT_DIR` is the absolute path to the root folder of a UiPath project (the folder that contains `project.json`).

**Step 0a — Determine the path** (use the first rule that matches):
1. **Explicit path** — The user provided a directory path → use it as-is.
2. **Project name reference** — The user mentioned a project by name (e.g., "the MyAutomation project") → search the file system for a folder with that name containing a `project.json`.
3. **Detect from running Studio** — No path or name given → run this command:
   ```bash
   uip rpa list-instances --format json
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

**ALWAYS use `uip rpa create-project`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually:
```bash
uip rpa create-project --name "<NAME>" --location "<PARENT_DIR>" --studio-dir "<STUDIO_DIR>" --format json
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

1. **NEVER create a project without first confirming no project already exists.** Follow the Step 0a resolution order above: if the user gave an explicit path or project name, check whether `project.json` exists there. If no path was given, run `uip rpa list-instances --format json` — if a Studio instance is running with a `ProjectDirectory`, that IS the project. Only create a new project when you have confirmed no existing project matches AND the user explicitly requests creation (or no project exists at cwd). This prevents accidentally creating nested projects or working in the wrong directory.
2. **Prefer UiPath built-in activities** for Orchestrator integration (`system.GetAsset`, `system.AddQueueItem`), UI automation (`uiAutomation.*`), and document handling (`excel.*`, `word.*`) — these provide reliability, logging, and Studio-level support. **Prefer plain .NET / third-party packages** for pure data transforms, HTTP calls to non-Orchestrator endpoints, parsing, string manipulation, and anything where code is clearly the right tool. When no built-in activity exists, find a well-known NuGet package — inspect it with `uip rpa inspect-package` first, then add it to `project.json`.
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
    1. Run `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json` — this forces Studio to re-analyze the specific file and returns a JSON result with validation status and any errors found
    2. If errors exist in the response: read the error messages, fix the code, and go back to step 1
    3. Repeat until validation returns zero errors (max 5 fix attempts)
    4. Only then proceed to run the workflow or report success to the user
    5. If after 5 fix attempts errors persist, stop and present the remaining errors to the user — they may require domain knowledge, missing dependencies, or environment-specific fixes you cannot resolve autonomously
    Note: `get-errors` returns the cached error state without re-analyzing — use `validate` instead when files have been changed outside Studio.
15. **NEVER use UITask (ScreenPlay) as the primary UI automation approach.** For ANY workflow using `uiAutomation.*`, follow the Finding Descriptors hierarchy in [ui-automation overview](../../references/activity-docs/UiPath.UIAutomation.Activities/26.2/coded/ui-automation.md): (1) Check Object Repository, (2) Check UILibrary NuGet packages, (3) Indicate missing elements via Studio, (4) UITask ONLY as last resort for brittle selectors. Do NOT skip steps or jump to UITask because indicating seems tedious.

## Task Navigation

Choose your task to find the right reference files:

| I need to... | Read these |
|-------------|-----------|
| **Create a new project** | Quick Start above → [operations-guide.md § Initialize](references/operations-guide.md) |
| **Add/edit a workflow** | [operations-guide.md § Add Workflow](references/operations-guide.md) → [coding-guidelines.md](references/coding-guidelines.md) |
| **Add a test case** | [operations-guide.md § Add Test Case](references/operations-guide.md) |
| **Write UI automation** | [ui-automation.md](../../references/activity-docs/UiPath.UIAutomation.Activities/26.2/coded/ui-automation.md) → [operations-guide.md § Indicate](references/operations-guide.md) |
| **Use Excel/Word/Mail/etc.** | Service table below → activity reference in `../../references/activity-docs/{PackageId}/{Version}/coded/` (e.g. [excel](../../references/activity-docs/UiPath.Excel.Activities/3.5/coded/excel.md), [word](../../references/activity-docs/UiPath.Word.Activities/2.5/coded/word.md), [mail](../../references/activity-docs/UiPath.Mail.Activities/2.8/coded/mail.md), [powerpoint](../../references/activity-docs/UiPath.Presentations.Activities/2.5/coded/powerpoint.md)) |
| **Use Office 365 / Google** | Service table below → [codedworkflow-reference.md § Integration Service](references/codedworkflow-reference.md) |
| **Use Azure services** | Service table below → [azure](../../references/activity-docs/UiPath.Azure.Activities/1.7/coded/azure.md) |
| **Use Google Cloud (GCP)** | Service table below → [google-cloud](../../references/activity-docs/UiPath.GoogleCloud.Activities/2.5/coded/google-cloud.md) |
| **Use Exchange Server** | Service table below → [exchange-server](../../references/activity-docs/UiPath.ExchangeServer.Activities/1.4/coded/exchange-server.md) |
| **Use System Center** | Service table below → [system-center](../../references/activity-docs/UiPath.SystemCenter.Activities/1.6/coded/system-center.md) |
| **Use Amazon Web Services** | Service table below → [amazon-web-services](../../references/activity-docs/UiPath.AmazonWebServices.Activities/2.9/coded/amazon-web-services.md) |
| **Use Amazon WorkSpaces** | Service table below → [amazon-workspaces](../../references/activity-docs/UiPath.AmazonWorkSpaces.Activities/1.5/coded/amazon-workspaces.md) |
| **Use Azure AD** | Service table below → [azure-active-directory](../../references/activity-docs/UiPath.AzureActiveDirectory.Activities/1.6/coded/azure-active-directory.md) |
| **Use Azure WVD** | Service table below → [azure-wvd](../../references/activity-docs/UiPath.AzureWVD.Activities/1.5/coded/azure-wvd.md) |
| **Use Active Directory** | Service table below → [active-directory](../../references/activity-docs/UiPath.ActiveDirectory.Activities/1.7/coded/active-directory.md) |
| **Use Citrix** | Service table below → [citrix](../../references/activity-docs/UiPath.Citrix.Activities/1.5/coded/citrix.md) |
| **Use Hyper-V** | Service table below → [hyperv](../../references/activity-docs/UiPath.HyperV.Activities/1.4/coded/hyperv.md) |
| **Use NetIQ eDirectory** | Service table below → [netiq-edirectory](../../references/activity-docs/UiPath.NetIQeDirectory.Activities/1.6/coded/netiq-edirectory.md) |
| **Build/run/validate** | [uip-guide.md](references/uip-guide.md) |
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
| `azure` | `UiPath.Azure.Activities` | [azure](../../references/activity-docs/UiPath.Azure.Activities/1.7/coded/azure.md) |
| `gcp` | `UiPath.GoogleCloud.Activities` | [google-cloud](../../references/activity-docs/UiPath.GoogleCloud.Activities/2.5/coded/google-cloud.md) |
| `exchangeserver` | `UiPath.ExchangeServer.Activities` | [exchange-server](../../references/activity-docs/UiPath.ExchangeServer.Activities/1.4/coded/exchange-server.md) |
| `systemCenter` | `UiPath.SystemCenter.Activities` | [system-center](../../references/activity-docs/UiPath.SystemCenter.Activities/1.6/coded/system-center.md) |
| `aws` | `UiPath.AmazonWebServices.Activities` | [amazon-web-services](../../references/activity-docs/UiPath.AmazonWebServices.Activities/2.9/coded/amazon-web-services.md) |
| `awrks` | `UiPath.Amazon.Workspaces.Activities` | [amazon-workspaces](../../references/activity-docs/UiPath.AmazonWorkSpaces.Activities/1.5/coded/amazon-workspaces.md) |
| `azureAD` | `UiPath.AzureActiveDirectory.Activities` | [azure-active-directory](../../references/activity-docs/UiPath.AzureActiveDirectory.Activities/1.6/coded/azure-active-directory.md) |
| `azureWVD` | `UiPath.AzureWVD.Activities` | [azure-wvd](../../references/activity-docs/UiPath.AzureWVD.Activities/1.5/coded/azure-wvd.md) |
| `activeDirectoryDomainServices` | `UiPath.ActiveDirectory.Activities` | [active-directory](../../references/activity-docs/UiPath.ActiveDirectory.Activities/1.7/coded/active-directory.md) |
| `citrix` | `UiPath.Citrix.Activities` | [citrix](../../references/activity-docs/UiPath.Citrix.Activities/1.5/coded/citrix.md) |
| `hyperv` | `UiPath.HyperV.Activities` | [hyperv](../../references/activity-docs/UiPath.HyperV.Activities/1.4/coded/hyperv.md) |
| `netiq` | `UiPath.NetIQeDirectory.Activities` | [netiq-edirectory](../../references/activity-docs/UiPath.NetIQeDirectory.Activities/1.6/coded/netiq-edirectory.md) |

> **Note:** The `office365` and `google` services require **Integration Service connections** configured in UiPath Automation Cloud. They inject both a service property (`office365` / `google`) and a `connections` property for accessing configured connection instances. `office365` provides Mail, Calendar, Excel (cloud), OneDrive, and SharePoint via Microsoft Graph API. `google` provides Gmail, Google Calendar, Google Drive, Google Sheets, and Google Docs via Google Workspace APIs. Both use OAuth tokens managed by Integration Service — see [references/codedworkflow-reference.md § Integration Service Connections](references/codedworkflow-reference.md).

### Determining Package Version for Activity Docs

Activity reference docs are versioned by major.minor under `../../references/activity-docs/{PackageId}/{Major.Minor}/coded/`. **Before reading any activity docs, determine the user's installed version:**

1. **Read `project.json`** in the user's project directory and find the package in the `dependencies` object:
   ```json
   {
     "dependencies": {
       "UiPath.Excel.Activities": "[3.3.1]",
       "UiPath.UIAutomation.Activities": "[25.10.21]",
       "UiPath.System.Activities": "[25.12.2]"
     }
   }
   ```
2. **Extract major.minor** from the version string — strip the brackets and drop the patch version:
   - `[3.3.1]` → `3.3`
   - `[25.10.21]` → `25.10`
   - `[2.5.10]` → `2.5`
3. **List available version folders** for the package:
   ```
   Glob: pattern="{PackageId}/*" path="../../references/activity-docs/"
   ```
4. **Pick the best match:**
   - If the exact major.minor folder exists (e.g., `3.3/`) → use it
   - If not, use the **closest available version that doesn't exceed** the installed version (e.g., installed `3.3`, available folders are `3.5/` → use `3.5/` as it's the closest, but note docs may reference newer APIs)
   - Fall back to the latest available folder if no lower version exists

The version numbers in the links throughout this document represent the latest documented version. Always cross-check with the user's actual installed version when available.

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

Activity and service references live in `../../references/activity-docs/{PackageId}/{Version}/coded/` — each contains a main guide, API reference (`api.md`, `windows-api.md`, `portable-api.md`), and `examples.md`. See the Task Navigation table above for links.

Available reference packages:
- **Document & productivity:** [Excel](../../references/activity-docs/UiPath.Excel.Activities/3.5/coded/excel.md), [Word](../../references/activity-docs/UiPath.Word.Activities/2.5/coded/word.md), [Presentations](../../references/activity-docs/UiPath.Presentations.Activities/2.5/coded/powerpoint.md), [Mail](../../references/activity-docs/UiPath.Mail.Activities/2.8/coded/mail.md), [Office365](../../references/activity-docs/UiPath.MicrosoftOffice365.Activities/3.8/coded/office365.md), [GSuite](../../references/activity-docs/UiPath.GSuite.Activities/3.8/coded/gsuite.md)
- **Cloud platforms:** [Azure](../../references/activity-docs/UiPath.Azure.Activities/1.7/coded/azure.md), [Google Cloud](../../references/activity-docs/UiPath.GoogleCloud.Activities/2.5/coded/google-cloud.md), [Amazon Web Services](../../references/activity-docs/UiPath.AmazonWebServices.Activities/2.9/coded/amazon-web-services.md)
- **Virtualization & infrastructure:** [Amazon WorkSpaces](../../references/activity-docs/UiPath.AmazonWorkSpaces.Activities/1.5/coded/amazon-workspaces.md), [Azure WVD](../../references/activity-docs/UiPath.AzureWVD.Activities/1.5/coded/azure-wvd.md), [Citrix](../../references/activity-docs/UiPath.Citrix.Activities/1.5/coded/citrix.md), [Hyper-V](../../references/activity-docs/UiPath.HyperV.Activities/1.4/coded/hyperv.md)
- **Identity & directory:** [Azure Active Directory](../../references/activity-docs/UiPath.AzureActiveDirectory.Activities/1.6/coded/azure-active-directory.md), [Active Directory](../../references/activity-docs/UiPath.ActiveDirectory.Activities/1.7/coded/active-directory.md), [NetIQ eDirectory](../../references/activity-docs/UiPath.NetIQeDirectory.Activities/1.6/coded/netiq-edirectory.md)
- **IT automation:** [Exchange Server](../../references/activity-docs/UiPath.ExchangeServer.Activities/1.4/coded/exchange-server.md), [System Center](../../references/activity-docs/UiPath.SystemCenter.Activities/1.6/coded/system-center.md)
- **Core:** [System](../../references/activity-docs/UiPath.System.Activities/25.10/coded/system.md), [Testing](../../references/activity-docs/UiPath.Testing.Activities/25.10/coded/testing.md), [UI Automation](../../references/activity-docs/UiPath.UIAutomation.Activities/26.2/coded/ui-automation.md)

## Completion Output

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — whether all files passed validation (or remaining errors if max retries hit)
3. **How to run** — the `uip rpa run-file` command to execute the workflow (if applicable)
4. **Next steps** — any follow-up actions the user should take (e.g. configure Integration Service connections, add Object Repository elements)
