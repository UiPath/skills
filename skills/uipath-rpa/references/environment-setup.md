# Environment Setup

**Goal:** Resolve the project root before any other operations.

## Studio Desktop vs headless Studio

`uip rpa` runs against a **headless Studio** by default (codename Helm — ships as the `UiPath.Studio.Helm.{Platform}` NuGet package, auto-launched the first time a command needs it). **Studio Desktop is not required** for the standard authoring loop — `init`, `run`, `debug start`, `validate`, `build`, `activities find`, `packages install`, the `uia` group (indication, capture, interaction), etc. all work headless.

Studio Desktop is only required for two interactive UI tools:
- `uip rpa files diff` — opens an interactive diff window in Studio's UI.
- `uip rpa focus-activity` — selects an activity in Studio's active workflow designer.

For these two, see [§ Edge case: requiring Studio Desktop](#edge-case-requiring-studio-desktop) below.

> **First call is slow.** On a cold NuGet cache, the very first `uip rpa` invocation triggers a silent `dotnet restore` of the headless Studio package and may sit near-silent for 30–90 seconds (longer behind a slow feed). A heartbeat line every 15s confirms it's still working. The default shell timeout covers this; bump `timeoutSeconds` only behind a slow feed.

## Step 0.1: Establish Project Root

The `uip rpa` commands use `--project-dir` to target a specific project (defaults to current working directory). **If the current working directory is NOT the UiPath project root, all commands will fail or target the wrong project.**

**Resolution order** (use the first rule that matches):
1. **Explicit path** — The user provided a directory path → use it as-is.
2. **Project name reference** — The user mentioned a project by name → search for a folder with that name containing `project.json`.
3. **Fall back to current working directory** — If neither is given.

If the CWD is not the project root:
- Locate the project root by finding `project.json`: `Glob: pattern="**/project.json"`
- **Pass `--project-dir` explicitly** to every `uip rpa` command
- Store the project root path and use it consistently as `{projectRoot}`

## Step 0.2: Authentication (If Needed)

Some commands (IS connections, workflow examples, cloud features) require authentication:

```bash
uip login
```

If you encounter auth errors (401, 403, "not authenticated") during any phase, prompt the user to run `uip login` to authenticate against their UiPath Cloud tenant.

## Step 0.3: Creating a New Project

**ALWAYS use `uip rpa init`** — never write `project.json`, `project.uiproj`, or other scaffolding files manually.

**`init` always scaffolds XAML.** Regardless of flags, the templates produce XAML files: `BlankTemplate` → `Main.xaml`, `TestAutomationProjectTemplate` → `TestCase.xaml`, `LibraryProcessTemplate` → XAML library workflows. There is no flag that flips the scaffolding to coded.

**`--expression-language` is independent of coded vs XAML.** It controls VB vs C# syntax inside XAML activity expressions — not whether the project has `.cs` workflow files. Coded workflows (`.cs` with `[Workflow]` / `[TestCase]`) work fine in both `VisualBasic` and `CSharp` projects.

**To work in coded mode**, scaffold the project (always XAML), then add `.cs` workflow files following [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints` in `project.json`. The scaffolded `Main.xaml` / `TestCase.xaml` can stay alongside your `.cs` files — `.xaml` and `.cs` workflows coexist freely.

**First, decide which template to use** — see [§ Template selection](#template-selection) below **before** running any `init` command. Defaulting to `--template-id BlankTemplate` is correct only when the user did not name a template or domain pattern.

### For XAML Projects (default for new projects)

```bash
uip rpa init \
  --name "MyAutomation" \
  --location "/path/to/parent/directory" \
  --template-id "BlankTemplate" \
  --expression-language <VisualBasic|CSharp> \
  --target-framework <Windows|Portable> \
  --description "Automates invoice processing" \
  --output json
```

**Decide `--target-framework` and `--expression-language` before running — never omit them.** Both are immutable after creation; omitting `--target-framework` silently produces a **Windows** project. The placeholder shows the two new-project options (`Windows`, `Portable`). Windows - Legacy is a last resort (explicit ask or hard .NET 4.6.1 need) and is created/authored in **Legacy mode**, not via this command. Choose from runtime / host-OS signals per SKILL.md Common Rule 2a.

**Expression language:** Default `VisualBasic`. Use `CSharp` only when the user explicitly asks for C# expressions inside XAML activities.

**`--studio-dir`:** Optional. Headless Studio does not need it. Pass it only when you have explicitly forced Studio Desktop (`UIPATH_RPA_TOOL_USE_STUDIO=1`, or invoking `diff`/`focus-activity`) and Studio's auto-detection from the registry fails.

### For Coded Projects (only when the user explicitly requested coded)

Run the **same** `init` command as for an XAML project (above) — there is no separate coded form. After it scaffolds, add `.cs` workflow files per [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints` in `project.json`. The scaffolded `Main.xaml` / `TestCase.xaml` can stay — remove it only if the user explicitly asks for a coded-only project.

#### Parameters

| Parameter | Options | Default | Notes |
|-----------|---------|---------|-------|
| `--name` | Any string | (required) | Project folder name |
| `--location` | Directory path | (current dir) | Parent directory where project folder is created |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | none — set explicitly | Expression syntax for XAML workflows. Immutable after creation |
| `--target-framework` | `Windows`, `Portable` (Cross-platform), `Legacy` (Windows - Legacy) | none — set explicitly (omitting → Windows) | .NET target framework. Immutable after creation. `Legacy` is a last resort for new projects (explicit ask or hard .NET 4.6.1 need only). Decide per Rule 2a |
| `--description` | Any string | (none) | Project description in project.json |

**Note:** `uip rpa init` may return `success: false` but still create the project files (partial success). If it fails, check whether the project directory and `project.json` were created before retrying.

### Template selection

Before running `init`, decide which template to use.

**1. Trigger keywords**

| User says... | Action |
|---|---|
| "REFramework", "ERP template", "SAP template", "based on X template", or any specific template name | Run `uip rpa templates search --query "<term>" --output json` (see § "Search and select" below) |
| "library", "library project" | Use `--template-id LibraryProcessTemplate` (built-in, no search) |
| "test project", "test automation" | Use `--template-id TestAutomationProjectTemplate` (built-in, no search) |
| Nothing template-related | Use `--template-id BlankTemplate` (default) |

**2. Search and select**

Run `uip rpa templates search --query "<term>" --output json`. Apply this rule against `Data[*]`, top-down:

- **User named a specific non-Official template** (e.g. "Enhanced REFramework", "Lite ReFrameWork", a specific package name) AND a `Marketplace` item's `title` or `packageId` substring-matches the user's specific qualifier ("Enhanced", "Lite", etc.) → ask the user (treat Official + that Marketplace item as candidates). Do NOT auto-pick.
- **Exactly one item with `source == "Official"`** AND user did not name a non-Official template → pick it. No user prompt.
- **Multiple `Official` items** → present candidates (`packageId`, `version`, `title`, `description`) and ask the user.
- **Zero `Official` items, ≥1 `Marketplace` item** → present and ask. Never silently pick a Marketplace template.
- **No results** → tell the user, then create with `--template-id BlankTemplate`.

**3. Create from package**

For Official/Marketplace templates, pass `--template-package-id` (and optionally `--template-package-version` — omit for latest) to `init`. When `--template-package-id` is set, `--template-id` is ignored.

### From a NuGet Template Package

Use when the user asks for a domain-specific template, references a specific template package by name, or wants to browse available templates.

**1. Search for available templates:**

```bash
uip rpa templates search --query "<SEARCH_TERM>" --output json
```

Does not require a project to be open. Returns a JSON array of `TemplateSearchResult` objects:

```json
[
  {
    "packageId": "UiPath.Template.SAPExample",
    "version": "2.0.0",
    "title": "SAP Automation Template",
    "description": "Pre-configured project for SAP GUI automation",
    "authors": "UiPath",
    "source": "https://feed.example.com/v3/index.json",
    "tags": ["SAP", "ERP"]
  }
]
```

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `--query` | string | (none) | Filter by name or description. Omit to list all |
| `--limit` | integer | 20 | Maximum results |
| `--include-prerelease` | flag | false | Include prerelease versions |

**2. Create from the chosen template:**

```bash
uip rpa init \
  --name "MySAPAutomation" \
  --location "/path/to/parent/directory" \
  --template-package-id "<PACKAGE_ID>" \
  --template-package-version "<VERSION>" \
  --target-framework <Windows|Portable> \
  --expression-language <VisualBasic|CSharp> \
  --output json
```

Pass `--target-framework` and `--expression-language` here too (Rule 2a) — a template package does not exempt you from the explicit-framework decision.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `--template-package-id` | string | (none) | NuGet package ID from `templates search` results. **Overrides `--template-id` when set** |
| `--template-package-version` | string | (latest) | Omit to use the latest available version |

### After Creation

1. Open the project in Studio: `uip rpa project open --project-dir "/path/to/MyAutomation"`
2. **Read the scaffolded files** — the command generates starter files. Read them before making changes so you build on valid defaults
3. Proceed with the skill workflow using the new project root

> **Batch the post-`init` prerequisites.** Step 2 here, `packages install` for known-needed packages, and the first `activities find` all depend only on the project existing — emit them as parallel tool calls in one message, not one per turn. They share the warmed Studio host. See SKILL.md § Execution Maps and [execution-maps-guide.md](execution-maps-guide.md).

## Edge case: requiring Studio Desktop

Two `uip rpa` commands need a running Studio Desktop instance — they have UI side effects that Helm cannot render:

| Command | Why it needs Studio |
|---------|---------------------|
| `uip rpa files diff` | Opens an interactive diff window in Studio's UI; finishes when the user closes the window. |
| `uip rpa focus-activity` | Selects/highlights an activity in Studio's active workflow designer. ⚠️ Against headless it **silently succeeds without doing anything** (there is no designer) — a `success: true` from a headless session does NOT mean anything was focused. |

When (and only when) you need to run one of these, ensure Studio Desktop is up:

```bash
uip rpa instances list --output json   # hidden diagnostic — confirms a Studio Desktop instance is running
uip rpa studio start --project-dir "{projectRoot}" --output json   # launches Studio Desktop if none is running
```

If `studio start` cannot resolve Studio's install directory from the registry, pass `--studio-dir` pointing to the Studio installation root.

You can also force Studio Desktop for any other command by setting `UIPATH_RPA_TOOL_USE_STUDIO=1`, but this is not needed for the standard authoring loop and gives up the headless benefits.

---

## Project Structure Reference

### Directory Layout

```
MyProject/
├── project.json          # Project manifest (name, dependencies, settings)
├── Main.xaml             # Default entry point (XAML mode) ─┐ typically one
├── Main.cs               # Default entry point (coded mode) ─┘ or the other
├── *.xaml                # Additional XAML workflow files
├── *.cs                  # Coded workflows, test cases, and source files
├── *.cs.json             # Auto-generated by Studio — do not create manually
├── .codedworkflows/      # Auto-generated coded workflow support files (ConnectionsFactory.cs, ConnectionsManager.cs, ISConnections.cs, etc.)
├── .entities/            # Data Fabric entity manifest — EntitiesStore.json. Committed; source of truth for which entities are bound to the project. Managed via uip rpa data-fabric-entities install.
├── .local/               # Local cache (package restore, compiled artifacts)
│   ├── install/          # Restored NuGet packages
│   ├── docs/             # Auto-generated activity documentation
│   │   └── packages/     # Per-package doc folders
│   ├── .codedworkflows/  # Auto-generated (ObjectRepository.cs, CodedWorkflow.cs, WorkflowRunnerService.cs)
│   └── .entities/        # Compiled Data Fabric entity assemblies (DataService.<Namespace>.dll) per install signature. Regenerated on demand — do not edit.
├── .objects/             # Object Repository metadata (UI element selectors)
├── .project/             # Project metadata
│   ├── JitCustomTypesSchema.json  # JIT-compiled custom type definitions
│   └── PackageBindingsMetadata.json
├── .screenshots/         # Activity screenshots (auto-generated)
├── .settings/            # Project-level settings
├── .autopilot/           # Autopilot service specific files
│   └── skills/           # Project-specific Autopilot skills
└── .storage/             # Activity resource storage (bucket-organized)
    ├── .design/          # Design-time only resources (NOT packed into published package)
    │   └── <bucket>/     # Named bucket to prevent conflicts
    └── .runtime/         # Runtime resources (packed into published NuPkg)
        └── <bucket>/     # Named bucket with resource files
```

#### Coded-Only Elements

- `.cs` files with `[Workflow]`/`[TestCase]` attributes — executable coded automations
- `.cs.json` metadata files — auto-generated by Studio for each coded workflow/test case (do not create manually)
- `.codedworkflows/` — auto-generated support files (only when project has `.cs` files)
- `.local/.codedworkflows/` — auto-generated `ObjectRepository.cs`, `CodedWorkflow.cs`, etc.
- `.variations/` — data-driven test parameters (Tests projects only)

#### XAML-Only Elements

- `.xaml` workflow files — visual workflow definitions
- Expression language configured in `project.json` (`VisualBasic` or `CSharp`)

### project.json Key Fields

```json
{
  "name": "MyProject",
  "description": "",
  "main": "Main.xaml",
  "dependencies": {
    "UiPath.System.Activities": "[24.12.1]"
  },
  "schemaVersion": "4.0",
  "studioVersion": "25.0.0.0",
  "projectVersion": "1.0.0",
  "runtimeOptions": {
    "autoDispose": false,
    "netFramework": { "targetFramework": "net6.0-windows" },
    "isPausable": true,
    "isAttended": false,
    "requiresUserInteraction": false
  },
  "designOptions": {
    "projectProfile": "Developement",
    "outputType": "Process",
    "libraryOptions": {
      "includeOriginalXaml": false,
      "privateWorkflows": []
    }
  },
  "expressionLanguage": "VisualBasic",
  "entryPoints": [
    {
      "filePath": "Main.xaml",
      "uniqueId": "2f510550-3882-4340-9239-53a24d0717f6",
      "input": [],
      "output": []
    }
  ],
  "targetFramework": "Windows"
}
```

#### Important Fields

| Field | Description |
|-------|-------------|
| `name` | Project name (used in package output) |
| `main` | Entry point workflow file (relative path) |
| `dependencies` | NuGet package dependencies with version constraints |
| `expressionLanguage` | `CSharp` or `VisualBasic` — determines expression syntax in XAML. Default `VisualBasic`. Immutable after creation (decide at init — SKILL.md Rule 2a) |
| `designOptions.outputType` | `Process`, `Library`, or `Tests` |
| `targetFramework` | `Windows` (.NET 6 Windows-only), `Portable` (Cross-platform .NET 6+), or `Legacy` (Windows - Legacy, .NET Framework 4.6.1). Set explicitly at init (Rule 2a); omitting `--target-framework` yields `Windows` |
| `entryPoints` | Per-workflow metadata: filePath, uniqueId, input/output definitions (**Process projects only** — Tests and Library projects use empty `[]`) |

### Rules

1. **Use CLI for dependencies**: Always use `uip rpa packages install` to add/update dependencies. Do not manually edit `dependencies` in `project.json`.
2. **Do not edit `.local/` or `.objects/`**: These are cache directories managed by the build system.
3. **`main` entry point**: The default entrypoint that gets run if not specified otherwise. `entryPoints` array is only populated for **Process** projects — Tests and Library projects leave it empty (`[]`).
4. **`--project-dir` awareness and project creation**: [§ Step 0.1](#step-01-establish-project-root) and [§ Step 0.3](#step-03-creating-a-new-project) above.

### Common Activity Packages

| Package ID | Description | Key Activities |
|------------|-------------|----------------|
| `UiPath.System.Activities` | Core system activities | Assign, If, ForEach, While, Invoke Workflow, Log Message, Delay |
| `UiPath.UIAutomation.Activities` | UI interaction | Click, Type Into, Get Text, Open Browser, Use Application/Browser |
| `UiPath.Excel.Activities` | Excel automation | Read Range, Write Range, Read Cell, Write Cell, Format Range |
| `UiPath.Mail.Activities` | Email operations | Send Mail, Get Mail, Save Attachments, Forward Mail |
| `UiPath.Database.Activities` | Database operations | Execute Query, Execute Non Query, Connect, Disconnect |
| `UiPath.WebAPI.Activities` | HTTP/REST calls | HTTP Request, Deserialize JSON, Serialize JSON |
| `UiPath.PDF.Activities` | PDF processing | Read PDF Text, Read PDF with OCR, Extract Data From PDF |
| `UiPath.Word.Activities` | Word automation | Read Text, Replace Text, Insert Image, Export to PDF |
| `UiPath.Testing.Activities` | Testing and assertions | Verify Expression, Verify Are Equal, Generate Test Data |
| `UiPath.Presentations.Activities` | PowerPoint automation | Add Slide, Replace Text, Insert Image |
| `UiPath.IntegrationService.Activities` | Integration Service connector runtime | Generic connector activities for Salesforce, ServiceNow, HubSpot, etc. |
| `UiPath.Cryptography.Activities` | Encryption/hashing | Encrypt Text, Decrypt Text, Hash File |

### Version Constraints

Dependencies use NuGet version constraint syntax:

| Syntax | Meaning |
|--------|---------|
| `[1.0.0]` | Exact version 1.0.0 |
| `[1.0.0, )` | Version 1.0.0 or higher |
| `[1.0.0, 2.0.0)` | Between 1.0.0 (inclusive) and 2.0.0 (exclusive) |

---

## Designing Project Structure

When creating a project, **proactively design the right file structure** based on the task complexity. Do not put everything into a single root workflow file. Use your best judgment to split the project into multiple files following good software engineering practices.

For the coded vs XAML decision, see [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md). For new projects, the default is XAML — examples below lead with XAML and note where the coded equivalent differs.

### Guidelines

- **Single simple task** (e.g. "read a CSV and log it") — one workflow file (`Main.xaml` for XAML projects, `Main.cs` for coded) is fine
- **Multi-step process** (e.g. "read invoices, validate, post to system") — split into multiple workflow files, each handling one step. The root workflow invokes each step
- **Shared data structures** — extract into a Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). XAML cannot define types, so a Coded Source File is the right home even in an otherwise XAML project
- **Repeated logic** — in XAML projects, extract into a reusable XAML workflow. In coded or hybrid projects, extract into a helper Coded Source File (e.g. `ValidationHelpers.cs`)
- **Test project** — one test case per scenario. Coded test projects optionally use `partial class CodedWorkflow : IBeforeAfterRun` in `CodedWorkflowHooks.cs` for shared setup. XAML test projects use Test Activities for shared setup
- **Complex domain logic** — isolate business rules so they can be unit-tested and reused (Coded Source File for typed logic, or a separate workflow for activity-driven logic)

### Designing for Reuse

Structure decisions that keep components extractable later.

#### Single responsibility

One workflow file = one meaningful action, named for it (`ProcessInvoice.xaml`, `LoginToApplication.xaml`). Split a workflow when it exceeds ~20-30 activities.

#### Standard folder shape

For multi-step processes, organize by layer:

```
Project/
├── Main.xaml              # High-level orchestration only
├── Framework/             # Init, cleanup, error handling, app open/close
├── BusinessLogic/         # Process-specific rules and transactions
├── Utilities/             # Process-agnostic helpers (formatters, screenshots)
└── Data/                  # Config files, templates
```

#### Separate business logic from UI components

UI workflows interact with applications and carry zero business rules; business-logic workflows decide and never touch the UI. Make read and write distinct invocable components — `GetCustomerInfo.xaml` and `ChangeCustomerInfo.xaml`, not one `HandleCustomer.xaml`. When the target application's UI changes, only the UI workflows need fixing; when a business rule changes, the UI workflows are untouched. Process-agnostic UI components are also the ones worth promoting to a shared library later.

#### Composition and argument naming

Compose via `Invoke Workflow File` (coded: `workflows.StepName()`). Process workflow arguments use directional prefixes — `in_InvoiceId`, `out_Result`, `io_Browser` — so data flow is visible at every invocation site. Exception: library public workflows drop the prefixes ([library-authoring-guide.md § The Public-Workflow Contract](library-authoring-guide.md)).

#### Layout and scale-out

- Sequence vs Flowchart vs State Machine per workflow: Workflow Types table in SKILL.md § XAML Workflows Quick Reference
- High-volume transactional work: dispatcher/performer split via queues — [reframework-guide.md § Execution Mode: Queue-Driven](reframework-guide.md)

#### Promotion ladder

Promote logic only as reuse materializes:

1. **Inline** — used once in one workflow
2. **Separate workflow file** — reused within the project
3. **Shared library** — reused across projects ([library-authoring-guide.md](library-authoring-guide.md))
4. **UI Library** — selectors shared across projects ([uia-starter-guide.md § Object Repository as a Published UI Library](uia-starter-guide.md#object-repository-as-a-published-ui-library))

### Example — Invoice Processing Project (XAML)

```
InvoiceProcessor/
├── project.json
├── Main.xaml                  # Root workflow: sequences each step via Invoke Workflow File
├── ReadInvoices.xaml          # Step 1: reads invoices from Excel
├── ValidateInvoices.xaml      # Step 2: validates data
├── PostToERP.xaml             # Step 3: posts to external system
└── InvoiceData.cs             # Coded source file: typed data model used across XAML steps
```

`Main.xaml` invokes each step via `Invoke Workflow File`, passing arguments In/Out. `InvoiceData.cs` is included even in this otherwise-XAML project because XAML cannot define types — typed DTOs eliminate `DataTable` column-name guessing.

#### Coded equivalent

```
InvoiceProcessor/
├── project.json
├── Main.cs                    # Root workflow: calls each step via workflows.StepName()
├── ReadInvoices.cs            # Step 1
├── ValidateInvoices.cs        # Step 2
├── PostToERP.cs               # Step 3
├── InvoiceData.cs             # Coded source file: data model
└── ValidationHelpers.cs       # Coded source file: validation utilities
```

`Main.cs` uses strongly-typed workflow invocation:

```csharp
[Workflow]
public void Execute(string inputFolder)
{
    var readResult = workflows.ReadInvoices(folderPath: inputFolder);
    Log($"Read {readResult.count} invoices");

    var validateResult = workflows.ValidateInvoices(invoices: readResult.invoiceList);
    Log($"Valid: {validateResult.validCount}, Invalid: {validateResult.invalidCount}");

    var postResult = workflows.PostToERP(validInvoices: validateResult.validInvoices);
    Log($"Posted {postResult.successCount} invoices to ERP");
}
```

### Example — Test Project

```
InvoiceTests/
├── project.json
├── CodedWorkflowHooks.cs      # Coded test projects only: partial class CodedWorkflow with Before/After hooks
├── TestLoginFlow.cs           # Test case: login scenario (hooks apply automatically via partial class merge)
├── TestInvoiceCreation.cs     # Test case: create invoice scenario
├── TestInvoiceValidation.cs   # Test case: validation rules
└── TestData.cs                # Source file: shared test constants/fixtures
```

XAML test projects use `.xaml` test cases instead of `.cs` and Test Activities for shared setup; the rest of the layout is the same.

### Example — Hybrid Project (XAML Root + Coded Logic)

```
OrderProcessing/
├── project.json
├── Main.xaml                  # XAML root workflow: sequences steps, handles retries
├── ScrapeOrderPortal.xaml     # XAML: UI automation with visual selector builder
├── SendConfirmationEmail.xaml # XAML: Mail activities (straightforward)
├── ProcessOrder.cs            # Coded workflow: 12 validation rules + LINQ transforms
├── OrderModels.cs             # Coded source file: Order, LineItem, ValidationResult DTOs
├── TransformHelpers.cs        # Coded source file: date parsing, currency conversion
└── TestProcessOrder.cs        # Coded test case: unit tests for ProcessOrder logic
```

#### Why hybrid here

- **ScrapeOrderPortal.xaml** — UI automation benefits from XAML's visual selector builder and recording tools
- **ProcessOrder.cs** — Order validation has 12 business rules with nested conditions; coded C# is clearer and testable
- **OrderModels.cs** — Typed DTOs used by both XAML (via typed arguments) and coded workflows, eliminating DataTable column-name guessing
- **SendConfirmationEmail.xaml** — Simple Mail activity, no logic — XAML is the simpler choice
- **Main.xaml** — Orchestration is linear (scrape → process → email); XAML Sequence is readable

#### Data flow

1. `Main.xaml` invokes `ScrapeOrderPortal.xaml` → returns `DataTable` via Out argument
2. `Main.xaml` invokes `ProcessOrder.cs` via Invoke Workflow File → passes raw data, returns validated `Order` objects
3. `Main.xaml` invokes `SendConfirmationEmail.xaml` → passes validated order data

### Project Structure Decision Tree

**First — coded or XAML?** For new projects, default to XAML unless the user explicitly said "coded" or named a coded-specific trigger (custom data models, complex algorithms, unit tests on business logic). See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md). The root workflow is `Main.xaml` for XAML projects and `Main.cs` for coded projects — substitute accordingly below.

**Is it a single, simple task?**
- ✅ Yes → Single root workflow

**Is it a multi-step process?**
- ✅ Yes → A root workflow that invokes each step + separate workflow files for each step

**Does it involve repeated data structures?**
- ✅ Yes → Extract to Coded Source File (e.g. `Models.cs`, `InvoiceData.cs`). Required even in XAML projects — XAML cannot define types

**Is there shared logic across workflows?**
- ✅ Yes → Extract to a reusable XAML workflow (XAML projects) or a helper Coded Source File (coded or hybrid projects)

**Is it a test project?**
- ✅ Yes → One test case file per scenario. Coded test projects optionally use `CodedWorkflowHooks.cs` (partial class CodedWorkflow) for shared setup/teardown

**Does it have complex business rules?**
- ✅ Yes → Isolate in Coded Source Files for reusability and testability (extract from XAML via `Invoke Workflow File` if needed)

**Does it need both UI automation AND complex non-UI logic?**
- ✅ Yes → Hybrid: XAML for UI automation + orchestration, Coded for business logic + data models. See [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md)
