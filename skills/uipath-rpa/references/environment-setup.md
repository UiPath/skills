# Environment Setup

**Goal:** Resolve the project root before any other operations.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## Studio Desktop vs headless Studio

`uip rpa` uses headless Studio (Helm, shipped as `UiPath.Studio.Helm.{Platform}` NuGet package and auto-launched when needed) by default. Studio Desktop is unnecessary for the standard authoring loop (`init`, `run`, `debug start`, `validate`, `build`, `activities find`, `packages install`, and `uia` indication/capture/interaction). It is required only for `uip rpa files diff` and `uip rpa focus-activity`; see [§ Edge case: requiring Studio Desktop](#edge-case-requiring-studio-desktop).

The first invocation may silently restore Helm for 30–90 seconds (longer behind a slow feed); a heartbeat every 15s confirms progress. The default shell timeout covers this; increase `timeoutSeconds` only behind a slow feed.

## Step 0.1: Establish Project Root

`uip rpa` targets the current directory unless `--project-dir` is supplied; a non-root CWD causes failure or targets the wrong project. Resolve in order:

1. User-provided directory: use it as-is.
2. Named project: search for a same-named folder containing `project.json`.
3. Otherwise use the CWD.

If the CWD is not the root, locate it with `Glob: pattern="**/project.json"`, pass `--project-dir` explicitly to every `uip rpa` command, and store it consistently as `{projectRoot}`.

## Step 0.2: Authentication (If Needed)

For IS connections, workflow examples, or cloud features, run:

```bash
uip login
```

For 401, 403, or “not authenticated” errors, prompt the user to run `uip login` against their UiPath Cloud tenant.

## Step 0.3: Creating a New Project

**ALWAYS use `uip rpa init`; never manually write `project.json`, `project.uiproj`, or scaffolding files.** `init` always scaffolds XAML: `BlankTemplate` → `Main.xaml`, `TestAutomationProjectTemplate` → `TestCase.xaml`, and `LibraryProcessTemplate` → XAML library workflows. No flag changes scaffolding to coded. `--expression-language` controls VB/C# syntax inside XAML, not coded workflows; `.cs` workflows with `[Workflow]`/`[TestCase]` work in both `VisualBasic` and `CSharp` projects.

For coded mode, run the same XAML `init`, then add `.cs` workflows using [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints` in `project.json`. XAML and coded workflows may coexist; retain scaffolded `Main.xaml`/`TestCase.xaml` unless the user explicitly requests coded-only.

Choose the template using [§ Template selection](#template-selection) **before** `init`; use `BlankTemplate` only when no template or domain pattern was named.

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

Decide and pass both `--target-framework` and `--expression-language`; never omit them. They are immutable after creation. Omitting `--target-framework` silently creates **Windows**. The new-project options shown here are `Windows` and `Portable`; `Windows - Legacy` is a last resort for an explicit ask or hard .NET 4.6.1 need and must be created/authored in **Legacy mode**, not through this command. Choose from runtime/host-OS signals per SKILL.md Common Rule 2a.

Inside a solution folder, `init` registers the new project in the enclosing `.uipx`; pass `--skip-solution-registration` for a project that stays out of the solution, such as a scratch or probe project.

`--expression-language` defaults to `VisualBasic`; use `CSharp` only when explicitly requested for C# expressions in XAML. Headless Studio needs no `--studio-dir`; pass it only when Studio Desktop is explicitly forced (`UIPATH_RPA_TOOL_USE_STUDIO=1`, or `diff`/`focus-activity`) and registry auto-detection fails.

### For Coded Projects (only when the user explicitly requested coded)

Run the same command above; there is no separate coded form. Then add `.cs` workflows per [coded/operations-guide.md § Add a Workflow File](coded/operations-guide.md#add-a-workflow-file-to-existing-project) and update `entryPoints`.

#### Parameters

| Parameter | Options | Default | Notes |
|---|---|---|---|
| `--name` | Any string | required | Project folder name |
| `--location` | Directory path | current dir | Parent directory |
| `--template-id` | `BlankTemplate`, `LibraryProcessTemplate`, `TestAutomationProjectTemplate` | `BlankTemplate` | Project template |
| `--expression-language` | `VisualBasic`, `CSharp` | none—set explicitly | XAML expression syntax; immutable |
| `--target-framework` | `Windows`, `Portable` (Cross-platform), `Legacy` (Windows - Legacy) | none—set explicitly (omitting → Windows) | Immutable; `Legacy` only as a last resort per Rule 2a |
| `--description` | Any string | none | Description in `project.json` |
| `--skip-solution-registration` | flag | off | Inside a solution folder, leaves the project out of the `.uipx` |

`uip rpa init` may return `success: false` while creating files. On failure, check for the project directory and `project.json` before retrying.

### Template selection

Before `init`, apply these rules:

| User says... | Action |
|---|---|
| "REFramework", "ERP template", "SAP template", "based on X template", or any specific template name | Run `uip rpa templates search --query "<term>" --output json` (see § "Search and select" below) |
| "library", "library project" | Use `--template-id LibraryProcessTemplate` (built-in, no search) |
| "test project", "test automation" | Run `uip rpa templates search --query "Test Automation Framework" --output json` and create from the Official Test Automation Framework template ([testing-guide.md § Test Automation Framework](testing-guide.md#test-automation-framework)); `--template-id TestAutomationProjectTemplate` (built-in, no search) only when the user asks for a blank test project |
| Nothing template-related | Use `--template-id BlankTemplate` (default) |

**Search and select**

Run `uip rpa templates search --query "<term>" --output json` and evaluate `Data[*]` top-down:

- If the user named a specific non-Official template (e.g. "Enhanced REFramework", "Lite ReFrameWork", a specific package name) and a `Marketplace` item’s `title` or `packageId` substring-matches that qualifier ("Enhanced", "Lite", etc.), ask the user and treat the Official item plus that Marketplace item as candidates; do not auto-pick.
- If exactly one `source == "Official"` item exists and no non-Official template was named, pick it without prompting.
- **Multiple `Official` items** → present candidates (`packageId`, `version`, `title`, `description`) and ask the user.
- **Zero `Official` items, ≥1 `Marketplace` item** → present and ask. Never silently pick a Marketplace template.
- For no results, tell the user and create with `--template-id BlankTemplate`.

For a selected Official/Marketplace template, pass `--template-package-id` and optionally `--template-package-version` (omit it for latest) to `init`; when `--template-package-id` is set, `--template-id` is ignored.

### From a NuGet Template Package

Use this when the user requests a domain-specific or named package, or wants to browse templates. Run:

```bash
uip rpa templates search --query "<SEARCH_TERM>" --output json
```

This needs no open project and returns a JSON array of `TemplateSearchResult` objects with fields `packageId`, `version`, `title`, `description`, `authors`, `source`, and `tags` (an array). `--query` is a string filter (omit to list all); `--limit` is an integer, default `20`; `--include-prerelease` is a flag, default `false`.

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

Create from the chosen package with:

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

Pass `--target-framework` and `--expression-language` here too (Rule 2a). `--template-package-id` is a NuGet ID and overrides `--template-id`; `--template-package-version` defaults to latest and may be omitted.

### After Creation

1. Run `uip rpa project open --project-dir "/path/to/MyAutomation"`.
2. Read the scaffolded files before editing.
3. Continue with the new project root.

Batch reading scaffolded files, `packages install` for known-needed packages, and the first `activities find` as parallel tool calls in one message; they depend only on project existence and share the warmed host. See SKILL.md § Execution Maps and [execution-maps-guide.md](execution-maps-guide.md).

## Edge case: requiring Studio Desktop

Only these commands require a running Studio Desktop instance:

| Command | Behavior |
|---|---|
| `uip rpa files diff` | Opens an interactive diff window and finishes when the user closes it |
| `uip rpa focus-activity` | Selects/highlights an activity in the active designer; against headless it silently succeeds without doing anything, so `success: true` does not prove focus |

When needed, run:

```bash
uip rpa instances list --output json   # hidden diagnostic — confirms a Studio Desktop instance is running
uip rpa studio start --project-dir "{projectRoot}" --output json   # launches Studio Desktop if none is running
```

If registry resolution fails, pass `--studio-dir` with the Studio installation root. You may force Studio for any command with `UIPATH_RPA_TOOL_USE_STUDIO=1`, but this is unnecessary for standard authoring and loses headless benefits.

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

`.cs` files with `[Workflow]`/`[TestCase]`; auto-generated `.cs.json` files (never create manually); `.codedworkflows/` and `.local/.codedworkflows/` support files when `.cs` exists; and `.variations/` data-driven test parameters for Tests projects.

#### XAML-Only Elements

`.xaml` workflow files and `project.json` expression language (`VisualBasic` or `CSharp`).

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

Important meanings: `name` is the package-output name; `main` is the relative default workflow; `dependencies` contains NuGet constraints; `expressionLanguage` is immutable `CSharp` or `VisualBasic` and defaults to `VisualBasic`; `designOptions.outputType` is `Process`, `Library`, or `Tests`; `targetFramework` is `Windows` (.NET 6 Windows-only), `Portable` (Cross-platform .NET 6+), or `Legacy` (Windows - Legacy, .NET Framework 4.6.1), selected explicitly at init; and `entryPoints` contains per-workflow metadata only for **Process** projects—Tests and Library projects use empty `[]`.

### Rules

1. **Use CLI for dependencies:** Always use `uip rpa packages install` to add/update dependencies; never manually edit `dependencies` in `project.json`.
2. **Do not edit `.local/` or `.objects/`:** They are build-managed.
3. **`main` entry point:** It runs by default when unspecified; `entryPoints` is populated only for **Process** projects, while Tests and Library use `[]`.
4. **`--project-dir` awareness and project creation:** See [§ Step 0.1](#step-01-establish-project-root) and [§ Step 0.3](#step-03-creating-a-new-project).

### Common Activity Packages

| Package ID | Description | Key Activities |
|---|---|---|
| `UiPath.System.Activities` | Core system | Assign, If, ForEach, While, Invoke Workflow, Log Message, Delay |
| `UiPath.UIAutomation.Activities` | UI interaction | Click, Type Into, Get Text, Open Browser, Use Application/Browser |
| `UiPath.Excel.Activities` | Excel | Read Range, Write Range, Read Cell, Write Cell, Format Range |
| `UiPath.Mail.Activities` | Email | Send Mail, Get Mail, Save Attachments, Forward Mail |
| `UiPath.Database.Activities` | Database | Execute Query, Execute Non Query, Connect, Disconnect |
| `UiPath.WebAPI.Activities` | HTTP/REST | HTTP Request, Deserialize JSON, Serialize JSON |
| `UiPath.PDF.Activities` | PDF | Read PDF Text, Read PDF with OCR, Extract Data From PDF |
| `UiPath.Word.Activities` | Word | Read Text, Replace Text, Insert Image, Export to PDF |
| `UiPath.Testing.Activities` | Testing/assertions | Verify Expression, Verify Are Equal, Generate Test Data |
| `UiPath.Presentations.Activities` | PowerPoint | Add Slide, Replace Text, Insert Image |
| `UiPath.IntegrationService.Activities` | Integration Service connector runtime | Generic connector activities for Salesforce, ServiceNow, HubSpot, etc. |
| `UiPath.Cryptography.Activities` | Encryption/hashing | Encrypt Text, Decrypt Text, Hash File |

### Version Constraints

Dependencies use NuGet constraints: `[1.0.0]` means exact version; `[1.0.0, )` means 1.0.0 or higher; `[1.0.0, 2.0.0)` means 1.0.0 inclusive through below 2.0.0.

## Designing Project Structure

Proactively design files for task complexity; do not put everything in one root workflow. For coded versus XAML, see [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md); new projects default to XAML.

### Guidelines

- One simple task may use one root workflow (`Main.xaml` or `Main.cs`).
- A multi-step process uses a root orchestrator plus one workflow per step.
- Put shared data structures in Coded Source Files such as `Models.cs` or `InvoiceData.cs`; XAML cannot define types.
- Put repeated logic in reusable XAML workflows, or helper Coded Source Files in coded/hybrid projects.
- Use one test case per scenario. Coded tests may use `partial class CodedWorkflow : CodedWorkflowBase, IBeforeAfterRun` in `CodedWorkflowHooks.cs`; XAML tests use Test Activities for shared setup.
- Isolate complex business rules in typed Coded Source Files or activity-driven workflows for reuse and testing.

### Designing for Reuse

#### Single responsibility

One workflow file performs one meaningful action and is named for it (`ProcessInvoice.xaml`, `LoginToApplication.xaml`). Split at roughly 20–30 activities. What remains inline follows SKILL.md Common Rule 4b.

#### Standard folder shape

For multi-step processes use this shape:

```
Project/
├── Main.xaml              # High-level orchestration only
├── Framework/             # Init, cleanup, error handling, app open/close
├── BusinessLogic/         # Process-specific rules and transactions
├── Utilities/             # Process-agnostic helpers (formatters, screenshots)
└── Data/                  # Config files, templates
```

#### Separate business logic from UI components

UI workflows interact with applications and contain no business rules; business workflows decide and never touch UI. Keep reads and writes distinct (for example, `GetCustomerInfo.xaml` and `ChangeCustomerInfo.xaml`) so UI changes and business-rule changes remain independent. Promote process-agnostic UI components to shared libraries when useful.

#### Composition and argument naming

Compose with `Invoke Workflow File` (coded: `workflows.StepName()`). Use directional process argument prefixes `in_InvoiceId`, `out_Result`, and `io_Browser`; library public workflows omit prefixes ([library-authoring-guide.md § The Public-Workflow Contract](library-authoring-guide.md)).

#### Layout and scale-out

Choose Sequence, Flowchart, or State Machine per [xaml/xaml-basics-and-rules.md § Workflow Types](xaml/xaml-basics-and-rules.md). Use dispatcher/performer queues for high-volume transactions: [reframework-guide.md § Execution Mode: Queue-Driven](reframework-guide.md).

#### Promotion ladder

Promote only as reuse appears: inline → separate workflow file → shared library ([library-authoring-guide.md](library-authoring-guide.md)) → UI Library for shared selectors ([uia-starter-guide.md § Object Repository as a Published UI Library](uia-starter-guide.md#object-repository-as-a-published-ui-library)).

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

For new projects default to XAML unless the user explicitly says “coded” or names coded-specific triggers such as custom data models, complex algorithms, or unit tests on business logic. Use `Main.xaml` for XAML and `Main.cs` for coded. Then apply:

- Single simple task → one root workflow.
- Multi-step process → root invoking separate step files.
- Repeated data structures → Coded Source File, including in XAML projects.
- Shared logic → reusable XAML workflow or helper Coded Source File.
- Test project → one case per scenario; coded tests may use `CodedWorkflowHooks.cs` and partial class `CodedWorkflow`.
- Complex business rules → isolate in Coded Source Files.
- UI automation plus complex non-UI logic → hybrid: XAML UI/orchestration, coded business logic/data models; see [coded-vs-xaml-guide.md](coded-vs-xaml-guide.md).

## Project Conversion (expressionLanguage / targetFramework)

Rule 23 (SKILL.md) forbids changing either field in an existing project. Both are fixed at creation for every XAML file: changing `expressionLanguage` invalidates expressions; changing `targetFramework` invalidates package references and activity compatibility.

Do not convert in place. When conversion is requested: (1) confirm with the user; (2) copy the project to a temporary folder; (3) create a new project with `uip rpa init --expression-language <VisualBasic|CSharp> --target-framework <Windows|Portable>`; for Windows - Legacy create it in Legacy mode instead, not through modern `init`; (4) recreate every old workflow equivalently; (5) delete the temporary copy only after successful generation and user agreement.

## Project Context Discovery

Before project work, check `.claude/rules/project-context.md`.

If it exists, read its first-line metadata `<!-- discovery-metadata: cs=N xaml=N deps=N -->`; count `**/*.cs` excluding `.local/` and `.codedworkflows/`, `**/*.xaml`, and dependency keys in `project.json`. For each count compute `abs(current - stored) / max(stored, 1) * 100`. If **any individual count differs by 60–70% or more**, run discovery; otherwise proceed.

If absent, run the skip gate below; if it does not trip, run the discovery flow.

### Skip gate: nothing to discover yet

**Do NOT spawn the discovery agent** when any condition holds:

| Condition | Check |
|---|---|
| Greenfield | Step 0 found no `project.json` |
| Empty | `**/*.xaml` + `**/*.cs`, excluding dot-directories and `obj/`, `bin/`, counts 0 |
| Fresh scaffold | Count 1 and it is untouched `Main.xaml` process/template, `NewActivity*.xaml` library, `TestCase.xaml` test, or `Main.cs` coded, with no authored logic: empty root `Sequence` or only `Comment` activities, or empty coded `Execute` body |

For a tripped gate, write no context files now; proceed, then **after the build** write both context files yourself using the discovery-flow paths and `AGENTS.md` marker logic.

### Discovery flow

For missing or stale context:

1. Spawn the project discovery agent and wait. Its definition is [`../agents/uipath-project-discovery-agent.md`](../agents/uipath-project-discovery-agent.md). Use the registered `uipath-project-discovery-agent` when available; otherwise spawn a subagent with that file as instructions/custom skill and write access. Read-only is allowed via step 3.
2. The agent writes context files and returns a `context-files:` status line plus the document. Use that document for this session; do **not** reread or rewrite files it wrote.
3. Only when it returns `context-files: not-written` (read-only host or write error), write the returned content to both `.claude/rules/project-context.md` (create `.claude/rules/`) and root `AGENTS.md`. If `AGENTS.md` has `<!-- PROJECT-CONTEXT:START -->` / `<!-- PROJECT-CONTEXT:END -->`, replace only the marked content; otherwise append the fenced block.
4. If it returns `SKIP: <reason>`, treat it as a gate trip: write no context files now and write them yourself after the build.
5. Proceed with the skill workflow.
