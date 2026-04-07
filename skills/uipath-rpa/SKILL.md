---
name: uipath-rpa
description: "[PREVIEW] UiPath automations — coded workflows (C#), XAML workflows, and hybrid projects. Create, edit, build, run, debug. For Orchestrator/deploy→uipath-platform. For agents→uipath-coded-agents."
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

## Step 0: Resolve PROJECT_DIR and Environment

Before creating or modifying anything, determine which project to work with and ensure Studio is running. See [references/environment-setup.md](references/environment-setup.md) for the full procedure.

**Quick check:** Find `project.json` to establish `{projectRoot}`, run `uip rpa list-instances --output json` to verify Studio, and `uip rpa open-project` if needed.

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

**Hybrid pattern** — XAML orchestration + coded fallback for logic with no matching activity:

    Main.xaml                  ← orchestration (XAML)
      └── InvokeWorkflowFile → ProcessData.cs  ← coded logic

For the full decision flowchart, InvokeCode extraction rules, and detailed hybrid patterns, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Critical Rules

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Follow Step 0 resolution: check explicit path, project name, running Studio instances, then CWD. Only create when confirmed no project matches AND user explicitly requests creation.
2. **ALWAYS use `uip rpa create-project --use-studio`** to create new projects — never write `project.json` or scaffolding manually.
3. **ALWAYS validate after every file create or edit.** Run `uip rpa get-errors --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio` until 0 errors. Cap at 5 fix attempts. See [references/validation-guide.md](references/validation-guide.md).
4. **Prefer UiPath built-in activities** for Orchestrator integration, UI automation, and document handling. Prefer plain .NET / third-party packages for pure data transforms, HTTP calls, parsing.
5. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
6. **For UI automation workflows**, MUST follow the target configuration workflow in [references/ui-automation-guide.md](references/ui-automation-guide.md). NEVER hand-write selectors — use `uia-configure-target` exclusively.
7. **Use `--output json`** on all CLI commands whose output is parsed programmatically.

### Coded-Specific Rules

8. **[Coded] ALWAYS inherit from `CodedWorkflow`** base class for workflow and test case classes (NOT for Coded Source Files).
9. **[Coded] ALWAYS use `[Workflow]` or `[TestCase]` attribute** on the `Execute` method.
10. **[Coded] Generate companion `.cs.json` metadata file** for each workflow/test case (NOT for Coded Source Files).
11. **[Coded] Update `project.json` entry points** when adding/removing workflow files. Update `fileInfoCollection` for test case files.
12. **[Coded] One workflow/test case class per file**, class name must match file name.
13. **[Coded] Namespace = sanitized project name** from `project.json`. Sanitize: remove spaces, replace hyphens with `_`, ensure valid C# identifier.
14. **[Coded] Entry method is always named `Execute`**.
15. **[Coded] Use Coded Source Files** for reusable code — plain `.cs` files without `CodedWorkflow` inheritance, no `.cs.json`, no entry point.

### XAML-Specific Rules

16. **[XAML] Activity docs are the source of truth** — check `{projectRoot}/.local/docs/packages/{PackageId}/` first. Always.
17. **[XAML] MUST understand project structure** — read `project.json`, check expression language, scan existing patterns. NEVER generate XAML blind.
18. **[XAML] Start minimal, iterate to correct** — build one activity at a time, validate after each addition.
19. **[XAML] Fix errors by category** — Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] NEVER touch ViewState** in XAML files — it's designer layout metadata.
21. **[XAML] Use `get-default-activity-xaml` output** as a starting point — don't construct activity XAML from memory.
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md)** before generating or editing any XAML.

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Choose coded vs XAML** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) |
| **Work in a hybrid project** | Hybrid | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [project-structure.md](references/project-structure.md) |
| **Create a new project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Add/edit a coded workflow** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) → [coded/coding-guidelines.md](references/coded/coding-guidelines.md) |
| **Add a coded test case** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) |
| **Create/edit XAML workflow** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) |
| **Write UI automation** | Both | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) |
| **Use Excel/Word/Mail/etc.** | Both | Service table below → `.local/docs/packages/{PackageId}/` → fallback: `../../references/activity-docs/{PackageId}/{closest}/` |
| **Call an IS connector (coded)** | Coded | [coded/integration-service-guide.md](references/coded/integration-service-guide.md) |
| **Call an IS connector (XAML)** | XAML | [connector-capabilities.md](references/connector-capabilities.md) → [xaml/workflow-guide.md § Step 1.9](references/xaml/workflow-guide.md) |
| **Build/run/validate** | Both | [cli-reference.md](references/cli-reference.md) → [validation-guide.md](references/validation-guide.md) |
| **Add a NuGet package** | Coded | [coded/operations-guide.md § Add Dependency](references/coded/operations-guide.md) → [coded/third-party-packages-guide.md](references/coded/third-party-packages-guide.md) |
| **Discover activity APIs** | Coded | [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md) |
| **Troubleshoot coded errors** | Coded | [coded/coding-guidelines.md § Common Issues](references/coded/coding-guidelines.md) |
| **Troubleshoot XAML errors** | XAML | [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) → [validation-guide.md](references/validation-guide.md) |
| **Understand project structure** | Both | [project-structure.md](references/project-structure.md) |

## Coded Workflows Quick Reference

Coded workflows use standard C# development: create file → write code → validate → run. Activity discovery (`find-activities`, `get-default-activity-xaml`) is XAML-specific — for coded mode, check `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` first for service API docs, then fall back to `inspect-package`. See [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md).

### Three Types of .cs Files

| Type | Base Class | Attribute | `.cs.json` | Entry Point | Purpose |
|------|-----------|-----------|------------|-------------|---------|
| **Coded Workflow** | `CodedWorkflow` | `[Workflow]` | Yes | Yes | Executable automation logic |
| **Coded Test Case** | `CodedWorkflow` | `[TestCase]` | Yes | Yes | Automated test with assertions |
| **Coded Source File** | None (plain C#) | None | No | No | Reusable models, helpers, utilities, hooks |

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

For `IntegrationConnectorService` (IS connectors from code): `UiPath.IntegrationService.Activities` — see [coded/integration-service-guide.md](references/coded/integration-service-guide.md).

### CodedWorkflow Base Class

All workflow/test case files inherit from `CodedWorkflow`, providing built-in methods (`Log`, `Delay`, `RunWorkflow`), service properties, and the `workflows` property for strongly-typed invocation. Extendable with Before/After hooks via `IBeforeAfterRun`.

Full reference: [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md)

### Templates

- [assets/codedworkflow-template.md](assets/codedworkflow-template.md) — Workflow boilerplate
- [assets/testcase-template.md](assets/testcase-template.md) — Test case boilerplate
- [assets/helper-utility-template.md](assets/helper-utility-template.md) — Helper class boilerplate
- [assets/json-template.md](assets/json-template.md) — project.json, .cs.json templates
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

### Expression Language

Check `expressionLanguage` in `project.json`. VB.NET uses `[brackets]` for expressions; C# uses `CSharpValue<T>` / `CSharpReference<T>`. Default for new XAML projects is VB.NET.

### Key CLI Commands

| Command | Purpose |
|---------|---------|
| `find-activities --query "<keyword>"` | Discover activities by keyword |
| `get-default-activity-xaml --activity-class-name "<class>"` | Get starter XAML for an activity |
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
- [xaml/jit-custom-types-schema.md](references/xaml/jit-custom-types-schema.md) — JIT custom type discovery

## Resolving Packages & Activity Docs

Follow this flow whenever you need to use an activity package:

### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies` for the required package.

- **If present** → note the version, proceed to Step 2. Suggest updating but **never force**.
- **If absent** → install:

```bash
uip rpa get-versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json --use-studio
uip rpa install-or-update-packages --packages '[{"id":"<PackageId>"}]' --project-dir "<PROJECT_DIR>" --output json --use-studio
```

### Step 2 — Find activity docs (priority order)

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — auto-generated, most accurate. Use `Glob` + `Read` (not `Grep` — `.local/` is gitignored).
2. **Fall back to bundled references** at `../../references/activity-docs/{PackageId}/` — pick the version folder closest to what is installed.

## UI Automation References

**MUST read [references/ui-automation-guide.md](references/ui-automation-guide.md) before any UI automation work** — mode-specific UIA patterns (coded vs XAML).

Additional UIA procedures and guides:
- [uia-prerequisites.md](references/uia-prerequisites.md) — Package version requirements
- [uia-debug-workflow.md](references/uia-debug-workflow.md) — Running and debugging UI automation workflows
- [uia-multi-step-flows.md](references/uia-multi-step-flows.md) — Advancing application state between screens
- [uia-selector-recovery.md](references/uia-selector-recovery.md) — Fixing selectors that fail at runtime
- [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) — Target configuration workflow and indication fallback

## Completion Output

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — whether all files passed validation (or remaining errors)
3. **How to run** — the `uip rpa run-file --use-studio` command (if applicable)
4. **Next steps** — follow-up actions (configure connections, add OR elements, fill placeholders)
5. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, use `/uipath-feedback` to send a report."
