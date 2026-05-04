---
name: uipath-rpa
description: "UiPath RPA — create, edit, build, run, debug `.cs` coded workflows and `.xaml` workflows. UI automation with Object Repository selectors, test case authoring, Integration Service connector calls. Deploy→uipath-platform. Test reports→uipath-test. Agents→uipath-agents. Legacy→uipath-rpa-legacy."
when_to_use: "User wants to create, edit, debug, or run a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents), legacy .NET 4.6.1 projects (→uipath-rpa-legacy)."
---

# UiPath RPA Assistant

Full assistant for creating, editing, managing, and running UiPath automation projects — both coded workflows (C#) and low-code RPA workflows (XAML).

## When to Use This Skill

- User wants to **create a new** UiPath automation project (coded or XAML)
- User wants to **add** a workflow, test case, or source file to an existing project
- User wants to **edit** an existing workflow or test case
- User wants to **modify project configuration** (dependencies, entry points)
- User asks about **UiPath activities** or how to automate something
- User wants to **validate, build, run, or debug** a workflow
- User wants to **add dependencies** or NuGet packages to a project
- User wants to **create test cases** with assertions
- User wants to **call an Integration Service connector** (Jira, Salesforce, ServiceNow, Slack, etc.)
- User wants to **use UI automation** to interact with desktop or web applications

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

## Step 0: Resolve PROJECT_DIR

Before creating or modifying anything, determine which project to work with. See [references/environment-setup.md](references/environment-setup.md) for the full procedure.

**Quick check:** Find `project.json` to establish `{projectRoot}`. That's it — no Studio Desktop check needed. `uip rpa` auto-launches a headless Studio (UiPath.Studio.Helm NuGet) on first call. Studio Desktop is required only for `diff` and `focus-activity`.

## Project Type Detection

After establishing `PROJECT_DIR`, determine whether this is a **coded** or **XAML** project:

1. **Coded mode** — `.cs` files with `[Workflow]` or `[TestCase]` attributes exist AND no `.xaml` workflow files (beyond scaffolded `Main.xaml`)
2. **XAML mode** — `.xaml` workflow files exist AND no coded workflow `.cs` files
3. **Hybrid** — Both exist → consult [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) to pick the right mode for each new file; default to matching the user's current request
4. **New project** — Neither exists → consult [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for decision criteria; ask the user if still ambiguous, or infer from request language ("create a coded workflow" vs "create a workflow")

**Routing:** Once mode is determined, use the Task Navigation table below to find the right reference files. For guidance on **choosing** between coded and XAML approaches, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Authoring Mode Selection

**Default to matching the project's existing mode.** For new projects or ambiguous cases, default to XAML — it is the more common mode and has the widest activity coverage.

| Scenario | Mode | Why |
|----------|------|-----|
| Standard RPA (Excel, email, file ops) | **XAML** (default) | Direct activity support, no code needed |
| UI automation | **XAML** (default) | Full activity support; coded also works via `uiAutomation` service |
| Integration Service connectors (XAML) | **XAML** | IS connector activities use XAML-specific dynamic activity config |
| No matching activity for a subtask | **Coded fallback** | Small .cs invoked from XAML via `Invoke Workflow File` |
| Complex data transforms, HTTP, parsing | **Coded** | C# is more natural than nested XAML activities |
| Custom data models / DTOs | **Coded Source File** | XAML cannot define types — plain `.cs`, no `CodedWorkflow` base |
| Unit tests with assertions | **Coded Test Case** | `[TestCase]` with Arrange/Act/Assert |
| User explicitly requests coded/XAML | **User's choice** | Never second-guess explicit preference |

### UI Automation Boundaries

For any task whose business behavior is "open an app/browser, click, type, scrape visible UI, submit a form, or verify UI state", the interaction layer MUST be UiPath UI Automation — `NApplicationCard` plus UIA activities (XAML), or `uiAutomation.Open`/`Attach` plus Object Repository descriptors (coded). Do NOT substitute `InvokeCode`, PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or external browser-driver scripts. The coded fallback rows above apply only to non-UI helper logic (data transforms, parsing, DTOs, calculations, API-only integrations).

If target configuration is unavailable, fall back to the documented UIA indication path — never to an external browser automation shortcut.

See [ui-automation-guide.md § Mandatory: Generate Targets Before Writing Any UI Code](references/ui-automation-guide.md#mandatory-generate-targets-before-writing-any-ui-code) for the full prohibited-tool list, the UIA-only exploration requirement, and the `InvokeJS`/`InjectJsScript` exception scope.

**Hybrid pattern** — XAML orchestration + coded fallback for logic with no matching activity:

    Main.xaml                  ← orchestration (XAML)
      └── InvokeWorkflowFile → ProcessData.cs  ← coded logic

For the full decision flowchart, InvokeCode extraction rules, and detailed hybrid patterns, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Critical Rules

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Follow Step 0 resolution: check explicit path, project name, then CWD for `project.json`. Only create when confirmed no project matches AND user explicitly requests creation.
2. **ALWAYS use `uip rpa create-project`** to create new projects — never write `project.json` or scaffolding manually.
   - **Before creating, decide if a template is needed.** If the user names a template ("REFramework", "Robotic Enterprise Framework", "based on the X template"), an industry/domain pattern (SAP, ERP, banking, mainframe), or otherwise hints at a non-blank starter, run `uip rpa search-templates --query "<term>" --output json` first. Selection rule against `Data[*]`:
     - **User named a specific non-Official template** (e.g. "Enhanced REFramework", "Lite ReFrameWork") AND a `Marketplace` item's `title` or `packageId` substring-matches the user's specific qualifier → ask the user (Official + that Marketplace item are both candidates). Do NOT auto-pick.
     - **Exactly one `source == "Official"` match AND user did not name a non-Official template** → use it; pass `--template-package-id <packageId> --template-package-version <version>` to `create-project`. Proceed without asking.
     - **Multiple `Official` matches OR only `Marketplace` matches** → present candidates (`packageId`, `version`, `source`, `title`) to the user and ask which to use. Never silently pick a Marketplace template.
     - **No matches** → fall back to a built-in `--template-id` and tell the user nothing was found.
   - Built-in `--template-id` keywords map without a search: `library` → `LibraryProcessTemplate`, `test automation` / `test project` → `TestAutomationProjectTemplate`, otherwise `BlankTemplate`. When `--template-package-id` is set, `--template-id` is ignored. Full decision flow: [environment-setup.md § Template selection](references/environment-setup.md#template-selection).
3. **ALWAYS list project analyzer rules before generating workflows, validate files as you go, AND verify the project builds before declaring done.** Three-phase validation:
   - **Pre-generation** (before creating or editing any workflow file — `.cs` with `[Workflow]`/`[TestCase]`, or `.xaml`): `uip rpa get-analyzer-rules --project-dir "<PROJECT_DIR>" --output json` to list the enabled Workflow Analyzer rules. Apply every `error` and `warning` rule during authoring so generated code passes `analyze` and `build` on the first attempt. Run once at the start of the task; re-run only when project dependencies change (a newly added package can ship its own `MA-*` rules).
   - **Per-file** (after every create or edit): `uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors. Cap at 5 fix attempts.
   - **Project-level end-goal** (before reporting done): `uip rpa build "<PROJECT_DIR>" --output json`. Projects returned to the user must compile. `get-errors` is static analysis and misses compile-time failures — notably attribute-form XAML expressions in projects with `expressionLanguage: CSharp`. A successful `uip rpa run-file` smoke test covers this; if no smoke test runs, `uip rpa build` is mandatory.

   See [references/validation-guide.md](references/validation-guide.md).
4. **ALWAYS validate files as you go AND verify the project builds before declaring done.** Per-file `get-errors` after every create or edit; project-level `build` (or a passing `run-file` smoke test) before reporting done. See [references/validation-guide.md](references/validation-guide.md).
5. **Prefer UiPath built-in activities** for Orchestrator integration, UI automation, and document handling. Prefer plain .NET / third-party packages for pure data transforms, HTTP calls, parsing.
6. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
7. **For UI automation workflows**, MUST follow the target configuration workflow in [references/ui-automation-guide.md](references/ui-automation-guide.md). NEVER hand-write selectors — use `uia-configure-target` exclusively.
7a. **[UIA] Verify UIA prerequisites before invoking `uia-configure-target`.** UIA minimum is `26.4.1-preview` (source-of-truth: [uia-prerequisites.md](references/uia-prerequisites.md) — kept in sync with that file). Run the prerequisite check in that file. If `UiPath.UIAutomation.Activities` is below the minimum or `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md` is absent: ask the user to upgrade or fall back to indication authoring — never silently route to a non-existent skill path. If the plan header records `UI capture: indication-only`, skip `uia-configure-target` entirely and use indication authoring.
8. **Use `--output json`** on all CLI commands whose output is parsed programmatically.

### Execution Discipline (Both Modes)

**Run to completion — do not declare work done while plan tasks remain.** If a plan file exists at `docs/plans/*.md` referenced by this request (or discoverable there for this feature), read its header before acting and during every checkpoint.

- If the header has `Execution autonomy: autonomous`: continue until ALL plan task checkboxes are `[x]` OR a concrete item from the plan's `Stop conditions` section is hit.
- If the header has `Execution autonomy: interactive`, or no plan file exists: use judgment and confirm with the user on material decisions.
- Before declaring the task done, re-read the plan and enumerate any unchecked boxes. If unchecked tasks remain and no Stop condition was hit, keep going — do not summarize partial work as "Done".
- "Feels expensive", "many tool calls used", "natural pause point", "partial result looks usable", and "too complex to continue in one session" are **NOT** Stop conditions. Only the concrete hard blockers in the plan's `Stop conditions` section count.
- Plan decisions already made are authoritative. Do not `AskUserQuestion` about structure, file count, selector strategy, or capture approach when the plan specifies them — those questions belonged to the planner.

### Coded-Specific Rules

8. **[Coded] ALWAYS inherit from `CodedWorkflow`** base class for workflow and test case classes (NOT for Coded Source Files).
9. **[Coded] ALWAYS use `[Workflow]` or `[TestCase]` attribute** on the `Execute` method.
10. **[Coded] Update `project.json` entry points** when adding/removing workflow files in **Process** projects. **Tests and Library projects do NOT use `entryPoints`** — skip this step for those project types. Always update `fileInfoCollection` for test case files.
12. **[Coded] One workflow/test case class per file**, class name must match file name.
13. **[Coded] Namespace = sanitized project name** from `project.json`. Sanitize: remove spaces, replace hyphens with `_`, ensure valid C# identifier.
14. **[Coded] Entry method is always named `Execute`**.
15. **[Coded] Use Coded Source Files** for reusable code — plain `.cs` files without `CodedWorkflow` inheritance, no entry point.

### XAML-Specific Rules

16. **[XAML] Activity docs are the source of truth** — check `{projectRoot}/.local/docs/packages/{PackageId}/` first. Always.
17. **[XAML] MUST understand project structure** — read `project.json`, check expression language, scan existing patterns. NEVER generate XAML blind.
18. **[XAML] Start minimal, iterate to correct** — build one activity at a time, validate after each addition.
19. **[XAML] Fix errors by category** — Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] ViewState handling depends on the operation.** When editing existing files, do NOT modify ViewState on nodes you are not changing. When generating new Flowchart/StateMachine/ProcessDiagram workflows, generate ViewState for each node (see [canvas-layout-guide.md](references/xaml/canvas-layout-guide.md)). For Sequences, ViewState is optional.
21. **[XAML] Reading `<Activity>.md` is a precondition for `get-default-activity-xaml` — for every activity, not just complex ones.** Workflow: (1) `find-activities` → class name, (2) read `<Activity>.md` and extract a property checklist (required + use-case-relevant), (3) `get-default-activity-xaml` → starter element, (4) **diff your checklist against the starter and add what's missing** — an empty checklist means you skipped step 2, go back. Doc lookup order: primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; fallback `skills/uipath-rpa/references/activity-docs/<PackageId>/<closest-version>/<Activity>.md` for older package versions where `.local/docs` is empty. Skip-tax: `get-default-activity-xaml` omits any property at type default — for `NTypeInto` that's 2 of 20. Self-exempting "this activity is simple" is the failure mode. Full procedure: [xaml/xaml-basics-and-rules.md § Activity Property Surface](references/xaml/xaml-basics-and-rules.md#activity-property-surface-and-starter-xaml).
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md)** before generating or editing any XAML.
23. **[XAML] NEVER change `expressionLanguage` or `targetFramework` on an existing project.** Both fields in `project.json` are fixed at creation time and apply to every XAML file in the project — flipping `expressionLanguage` (VisualBasic ↔ CSharp) invalidates every expression, and flipping `targetFramework` (Windows ↔ Portable/cross-platform, or Legacy) invalidates package references and activity compatibility. **Do not attempt in-place conversion.** If the user wants to convert an existing project, confirm with them, copy the project to a temporary folder, create a new project via `uip rpa create-project --expression-language <VisualBasic|CSharp> --target-framework <Windows|Portable|Legacy>`, make sure all the defined workflows in the old project have an equivalent in the new project. Delete the copied project just after the new project has been successfully generated and the user agree with the changes.

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Choose coded vs XAML** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) |
| **Work in a hybrid project** | Hybrid | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [project-structure.md](references/project-structure.md) |
| **Create a new project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Add/edit a coded workflow** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) → [coded/coding-guidelines.md](references/coded/coding-guidelines.md) |
| **Add a coded test case** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) |
| **Set up data-driven testing** | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md) |
| **Create XAML test case (Given-When-Then)** | XAML | [testing-guide.md § XAML Test Case Structure](references/testing-guide.md) |
| **Use mock testing** | XAML | [testing-guide.md § Mock Testing (WIP)](references/testing-guide.md) — requires CLI command not yet available |
| **Use XAML test activities** | XAML | [testing-guide.md § XAML Test Activities](references/testing-guide.md) |
| **Use execution templates** | XAML | [testing-guide.md § Execution Templates](references/testing-guide.md) |
| **Create/edit XAML workflow** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) |
| **Create Flowchart/StateMachine/LRW** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) |
| **Write UI automation** | Both | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) |
| **Build multi-screen UIA XAML workflow** | XAML | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md § Multi-Step UI Flows](references/uia-configure-target-workflows.md#multi-step-ui-flows) |
| **Use Excel/Word/Mail/etc.** | Both | Service table below → `.local/docs/packages/{PackageId}/` → fallback: `references/activity-docs/{PackageId}/{closest}/` |
| **Call an IS connector (coded)** | Coded | [coded/integration-service-guide.md](references/coded/integration-service-guide.md) |
| **Call an IS connector (XAML)** | XAML | [is-connector-xaml-guide.md](references/is-connector-xaml-guide.md) → [connector-capabilities.md](references/connector-capabilities.md) |
| **Build/run/validate** | Both | [cli-reference.md](references/cli-reference.md) → [validation-guide.md](references/validation-guide.md) |
| **List project best-practice / analyzer rules** | Both | [cli-reference.md § get-analyzer-rules](references/cli-reference.md) |
| **Add a NuGet package** | Coded | [coded/operations-guide.md § Add Dependency](references/coded/operations-guide.md) → [coded/third-party-packages-guide.md](references/coded/third-party-packages-guide.md) |
| **List / install Data Fabric entities** | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md#commands----data-fabric-entities) |
| **Discover activity APIs** | Coded | [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md) |
| **Troubleshoot coded errors** | Coded | [coded/coding-guidelines.md § Common Issues](references/coded/coding-guidelines.md) |
| **Troubleshoot XAML errors** | XAML | [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) → [validation-guide.md](references/validation-guide.md) |
| **Understand project structure** | Both | [project-structure.md](references/project-structure.md) |

## Coded Workflows Quick Reference

Coded workflows use standard C# development: create file → write code → validate → run. Activity discovery (`find-activities`, `get-default-activity-xaml`) is XAML-specific — for coded mode, check `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` first for service API docs, then fall back to `inspect-package`. See [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md).

### Three Types of .cs Files

| Type | Base Class | Attribute | Entry Point | Purpose |
|------|-----------|-----------|-------------|---------|
| **Coded Workflow** | `CodedWorkflow` | `[Workflow]` | Process only | Executable automation logic |
| **Coded Test Case** | `CodedWorkflow` | `[TestCase]` | Process only | Automated test with assertions |
| **Coded Source File** | None (plain C#) | None | No | Reusable models, helpers, utilities, hooks |

### Service-to-Package Mapping

Each service on `CodedWorkflow` requires its NuGet package in `project.json`. Without it: `CS0103`.

| Service Property | Required Package |
|-----------------|------------------|
| `system` | `UiPath.System.Activities` |
| `testing` | `UiPath.Testing.Activities` |
| `uiAutomation` | `UiPath.UIAutomation.Activities` |
| `excel` | `UiPath.Excel.Activities` |
| `word` | `UiPath.Word.Activities` |
| `powerpoint` | `UiPath.Presentations.Activities` |
| `mail` | `UiPath.Mail.Activities` |
| `office365` | `UiPath.MicrosoftOffice365.Activities` |
| `google` | `UiPath.GSuite.Activities` |

For infrastructure/cloud packages (azure, gcp, aws, azureAD, citrix, hyperv, etc.), see [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md).

For IS connectors from coded workflows via `ConnectorConnection.ExecuteAsync`: `UiPath.IntegrationService.Activities` — see [coded/integration-service-guide.md](references/coded/integration-service-guide.md).

### CodedWorkflow Base Class

All workflow/test case files inherit from `CodedWorkflow`, providing built-in methods (`Log`, `Delay`, `RunWorkflow`), service properties, and the `workflows` property for strongly-typed invocation. Extendable with Before/After hooks via `IBeforeAfterRun`.

Full reference: [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md)

### Templates

- [assets/codedworkflow-template.md](assets/codedworkflow-template.md) — Workflow boilerplate
- [assets/testcase-template.md](assets/testcase-template.md) — Test case boilerplate
- [assets/helper-utility-template.md](assets/helper-utility-template.md) — Helper class boilerplate
- [assets/json-template.md](assets/json-template.md) — project.json templates
- [assets/before-after-hooks-template.md](assets/before-after-hooks-template.md) — Before/After hooks
- [assets/project-structure-examples.md](assets/project-structure-examples.md) — Design guidelines

## XAML Workflows Quick Reference

XAML workflows follow a **discovery-first, phase-based approach**: Discovery → Generate/Edit → Validate & Fix → Response. See [references/xaml/workflow-guide.md](references/xaml/workflow-guide.md) for the full phase workflow.

### Workflow Types

| Type | When to Use |
|------|-------------|
| **Sequence** | Linear step-by-step logic; most common for simple automations |
| **Flowchart** | Branching/looping logic with multiple decision points |
| **State Machine** | Long-running processes with distinct states and transitions |
| **Long Running Workflow** | BPMN-style horizontal flow; event-driven processes with long waits |

### Expression Language

Check `expressionLanguage` in `project.json`. VB.NET uses `[brackets]` for expressions; C# uses `CSharpValue<T>` / `CSharpReference<T>`. Default for new XAML projects is VB.NET.

### Key CLI Commands

| Command | Purpose |
|---------|---------|
| `find-activities --query "<keyword>"` | Discover activities by keyword |
| `get-default-activity-xaml --activity-class-name "<class>"` | Get starter XAML for an activity |
| `get-analyzer-rules --project-dir "<dir>"` | List enabled Workflow Analyzer rules — run before generating |
| `get-errors --file-path "<file>"` | Validate a workflow file |

### Common Activities

| Activity | Package | Purpose |
|----------|---------|---------|
| Use Application/Browser | `UiPath.UIAutomation.Activities` | Scope for all UI automation actions |
| Click | `UiPath.UIAutomation.Activities` | Click a UI element |
| Type Into | `UiPath.UIAutomation.Activities` | Type text into a field |
| Get Text | `UiPath.UIAutomation.Activities` | Extract text from a UI element |
| If | built-in | Conditional branching |
| Assign | built-in | Set variable/argument values |
| For Each | built-in | Iterate over a collection |
| Invoke Workflow File | built-in | Call another workflow file |

### XAML File Anatomy

The XAML file anatomy template (namespace declarations, root Activity element, body structure) is in [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — read it before generating or editing any XAML.

### Key References

- [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — XAML anatomy, safety rules, editing operations (read before any XAML work)
- [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) — Activity gotchas, scope requirements, property conflicts
- [xaml/csharp-activity-binding-guide.md](references/xaml/csharp-activity-binding-guide.md) — Canonical C# binding forms per common activity property (LogMessage, GetText, StartProcess, …) — flat lookup table + recipes
- [xaml/csharp-expression-pitfalls.md](references/xaml/csharp-expression-pitfalls.md) — C#-specific expression failures (attribute-form VB JIT, ThrowIfNotInTree, OutArgument parse errors)
- [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) — Flowchart, State Machine, and Long Running Workflow canvas layout with ViewState
- [xaml/jit-custom-types-schema.md](references/xaml/jit-custom-types-schema.md) — JIT custom type discovery

### Multi-Screen UI Automation Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its targets get registered in the OR — validating with `get-errors` after each batch. See [uia-configure-target-workflows.md § Multi-Step UI Flows](references/uia-configure-target-workflows.md#multi-step-ui-flows) for the capture loop and the Complete-then-advance rule.

## Resolving Packages & Activity Docs

Follow this flow whenever you need to use an activity package:

### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies` for the required package.

- **If present** → note the version, proceed to Step 2. Suggest updating but **never force**.
- **If absent** → install:

```bash
uip rpa get-versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output jsonuip rpa install-or-update-packages --packages '[{"id":"<PackageId>"}]' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find activity docs (priority order)

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — auto-generated, most accurate. Use `Glob` + `Read` (not `Grep` — `.local/` is gitignored).
2. **Fall back to bundled references** at `references/activity-docs/{PackageId}/` — pick the version folder closest to what is installed.

## UI Automation References

**MUST read [references/ui-automation-guide.md](references/ui-automation-guide.md) before any UI automation work** — mode-specific UIA patterns (coded vs XAML).

Additional UIA procedures and guides:
- [uia-prerequisites.md](references/uia-prerequisites.md) — Package version requirements
- [uia-debug-workflow.md](references/uia-debug-workflow.md) — Running and debugging UI automation workflows
- [uia-selector-recovery.md](references/uia-selector-recovery.md) — Fixing selectors that fail at runtime
- [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) — Target configuration workflow, multi-step UI flows, and indication fallback

## Completion Output

**Before reporting "done", verify the plan is complete.** If a plan file at `docs/plans/*.md` drove this work:
1. Re-read the plan and scan its task checkboxes.
2. If any `[ ]` boxes remain AND the plan's header says `Execution autonomy: autonomous` AND no `Stop conditions` item was hit — **do not report done**. Resume execution on the next unchecked task.
3. If unchecked boxes remain because a Stop condition was hit, name the exact stop-condition item in the report.
4. If the plan is fully checked off, or execution autonomy is `interactive`, proceed to the report format below.

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — per-file `get-errors` result (all files passed, or remaining errors) **and** project-level `uip rpa build` result. If neither `build` nor a successful `run-file` smoke test has run, the project is not verified — say so explicitly rather than claiming success.
3. **Plan completion** — which task checkboxes in `docs/plans/*.md` are now `[x]`; list any still `[ ]` and, for each, the Stop-condition item that interrupted it (or "not reached" if execution was cut short another way)
4. **How to run** — the `uip rpa run-file` command (if applicable)
5. **Next steps** — follow-up actions (configure connections, add OR elements, fill placeholders)
6. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, use `/uipath-feedback` to send a report."

Do NOT use framing like "complete", "done", "finished", or "the automation is built" unless every plan task is checked off. "Partial", "stopped at <task N>", or "blocked by <stop condition>" is the honest framing otherwise.
