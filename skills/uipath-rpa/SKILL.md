---
name: uipath-rpa
description: "Always invoke for `.xaml` or `.cs` workflow files. UiPath RPA — create, edit, build, run, debug `.cs` coded workflows and `.xaml` workflows. UI automation with Object Repository selectors, test case authoring, Integration Service connector calls. Live desktop/browser UI exploration and control. Deploy via `.uipx`→uipath-solution. Non-solution Orchestrator ops→uipath-platform. Test reports→uipath-test. Agents→uipath-agents."
when_to_use: "User wants to create, edit, debug, or run a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents)."
---

# UiPath RPA Assistant

Full assistant for creating, editing, managing, and running UiPath automation projects — both coded workflows (C#) and low-code RPA workflows (XAML).

> **Reading the referenced files is imperative — read each required file in full.** This SKILL.md is a router: it tells you *which* reference to open, not *what* it says. When a rule, the Task Navigation table, or a section points you to a reference for the task at hand, open it and read the **whole** file before acting — do not grep it for a keyword, skim the first screen, fall back to `--help`, or substitute prior knowledge. Most errors that slip past `validate` and surface at `build` or runtime trace back to a reference that was skipped or only partially read. **Exception — generated `coded-api.md` package docs** (under `.local/docs/` or `references/activity-docs/`): read only the H2 sections for the services you need; they are per-service API listings, not sequential guides.

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

## Critical Rules

**Rule numbering.** Common Rules use 1–12. `### Coded-Specific Rules` continues 13–19. XAML-Specific Rules are an independent 16–24 sequence carried in [references/xaml/critical-rules-xaml.md](references/xaml/critical-rules-xaml.md), so numbers 16/17/18/19 appear in both mode-specific sequences — the `[Coded]` / `[XAML]` prefix on each rule disambiguates. Cross-references in this skill ("Common Rule 10", "Common Rule 12", "Rule 21", "Rule 24") always point to a uniquely-numbered rule.

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Follow Step 0 resolution: check explicit path, project name, then CWD for `project.json`. Only create when confirmed no project matches AND user explicitly requests creation.
2. **ALWAYS use `uip rpa init`** to create new projects — never write `project.json` or scaffolding manually.
   - **Before creating, decide if a template is needed.** If the user names a template ("REFramework", "Robotic Enterprise Framework", "based on the X template"), an industry/domain pattern (SAP, ERP, banking, mainframe), or otherwise hints at a non-blank starter, run `uip rpa templates search --query "<term>" --output json` first and apply the selection rule in [environment-setup.md § Template selection](references/environment-setup.md) — auto-pick only a single `Official` match; present candidates and ask the user for multiple `Official` matches, Marketplace matches, or a user-named non-Official template; never silently pick a Marketplace template; on no matches, fall back to a built-in `--template-id` and tell the user nothing was found.
   - Built-in `--template-id` keyword mappings (no search needed) and the full decision flow: [environment-setup.md § Template selection](references/environment-setup.md). When `--template-package-id` is set, `--template-id` is ignored.
2a. **Pass `--target-framework` AND `--expression-language` explicitly on every `uip rpa init` — never omit them.** Both are immutable after creation (XAML Rule 23 — [references/xaml/critical-rules-xaml.md](references/xaml/critical-rules-xaml.md)); omitting `--target-framework` silently yields a **Windows** project. Choose framework by where the automation runs: cross-platform / non-Windows runtime (Linux, container, serverless) or Studio Web editing → **`Portable`** (Cross-platform); Windows runtime using Windows-only capabilities (Excel COM/interop `UseExcelFile` — plain workbook range read/write via `excel.UseWorkBook` is Portable-safe; classic Office, WPF / `PresentationFramework`, Windows-only UIA) or Studio Desktop as the edit surface → **`Windows`** (not editable in Studio Web). A request needing *both* a cross-platform runtime and a Windows-only capability is contradictory — surface it, don't silently pick. **Windows - Legacy is a last resort** (explicit ask or hard .NET 4.6.1 need; never inferred from VB.NET or non-"X" classic activities) — create it in Legacy mode, not modern `init`. No signal → `AskUserQuestion` (Windows vs Cross-platform), framed around the runtime host. `--expression-language`: default `VisualBasic`, `CSharp` only on explicit request.
3. **Phase-gated validation: analyzer rules run at AUTHORING-phase start, not session start.** Full loop, fix discipline, and error-class lists: [references/validation-guide.md](references/validation-guide.md) — read before the session's first `validate`/`build`. Three phases:
   - **Authoring-phase start** (immediately before creating or editing any workflow file — `.cs` with `[Workflow]`/`[TestCase]`, or `.xaml`): `uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json`; apply every `error` and `warning` rule during authoring. Run once at this point; re-run only when project dependencies change. **DO NOT run at session start** — the call can take a minute or more (narrow with `--scope` if it times out, see [cli-reference.md § analyzer-rules list](references/cli-reference.md)). For capture-first tasks, deferred until capture is complete — § Capture-First Fast Path below.
   - **Per-file** (after every create or edit): `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors.
   - **Project-level build** (after per-file `validate` is clean across the edit session, before declaring done): `uip rpa build "<PROJECT_DIR>" --output json` until clean — catches what `validate` misses (unknown members, invalid enums, CacheMetadata, attribute-form C# JIT); on error, re-run `validate --file-path` on the offending file.
   - **5-attempt cap per loop** (per-file `validate` and project `build` each); fix one root cause per iteration. A successful `uip rpa run` substitutes for the end-of-session `build` (`run` compiles internally; prefer `run --skip-build` when `build` has just passed) — [validation-guide.md § Smoke Test](references/validation-guide.md).
4. **ALWAYS validate files as you go AND verify the project builds before declaring done.** `validate` clean alone is not "validated" — it cannot see member or enum errors; the project-level `build` is mandatory before declaring done. `build` is project-scoped: run it once at the end of the edit session, not after every Edit. See [references/validation-guide.md](references/validation-guide.md).
5. **Prefer UiPath built-in activities** for Orchestrator integration, UI automation, and document handling. Prefer plain .NET / third-party packages for pure data transforms, HTTP calls, parsing.
6. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
6a. **Pre-edit verification gate.** Two authoring actions are hard to roll back once `build` fails — verify before serialization, not after.
   - **Removing a dependency** — grep the project for usages before deleting an entry. A package may be the sole supplier of an activity used elsewhere (`MergePDFs` lives in the IntelligentOCR.StudioWeb family).
   - **Writing a new activity tag** — confirm via `uip rpa activities find --query "<verb>" --output json` and use the returned `ClassName`. Do not derive tag names from Studio display names. See [common-pitfalls.md § Common Activity Name Confusions](references/xaml/common-pitfalls.md).
7. **[UIA] Before writing ANY UIA activity (XAML `<uix:N*>` or coded `uiAutomation.*` / `Descriptors.*`), MUST read [references/ui-automation-guide.md](references/ui-automation-guide.md) IN FULL** — including the mode-specific section (For Coded Workflows or For XAML Workflows) and Running UI Automation Workflows. No exceptions for "simple" UIs. Skipping this rule is the most common cause of hallucinated selectors, wrong target XML, and missing OR descriptors. NEVER hand-write selectors — use `uia-configure-target` exclusively (the guide explains how). This guide is the single entry point for UIA work: it routes you to [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md), [uia-prerequisites.md](references/uia-prerequisites.md), and the package docs in order — the other UIA sections in this file point back here rather than restating the read mandate.
7a. **[UIA] Verify UIA prerequisites before invoking `uia-configure-target`.** The minimum version, the prerequisite check, upgrade-consent rules, and the fallback ladder when the `uip rpa uia` CLI is unavailable (placeholder stubs vs indication capture) live in [uia-prerequisites.md](references/uia-prerequisites.md) — read it and run that check first (do not hardcode the version from memory; that file is the only source of truth).
8. **Use `--output json`** on all CLI commands whose output is parsed programmatically.
8a. **`run` / `debug start` success/failure verdict comes from the outer `Result` (equivalently the inner `HasErrors`), NEVER from any log entry's `Level`** — successful workflows routinely emit `Log Message` at `Error`/`Warning` as observability; treating log levels as a verdict flips green runs to "failed". Envelope semantics: [debugging.md § Reading Debug Output Effectively](references/debugging.md) and [cli-reference.md § run](references/cli-reference.md).
9. **For "leverage / reuse / find shared libraries" requests, search the tenant feed — not the local filesystem, NuGet.org, or keyword-permutation loops.** Run `uip or libraries list --limit 500 --output-filter "<JMESPath>" --output json`. On zero results from the filtered call, take the fallback branch — do not re-keyword. Skip conditions and full procedure: [tenant-library-search-guide.md](references/tenant-library-search-guide.md).
10. **Register every test case file in `project.json` → `designOptions.fileInfoCollection`.** Applies to both XAML and coded test cases. Required keys, GUID format, JSON snippet, and full schema (including `dataVariationFilePath` for data-driven and `publishAsTestCase` for coded): [references/testing-guide.md § project.json Registration](references/testing-guide.md) and [assets/json-template.md](assets/json-template.md).

11. **Test case structure: Given-When-Then.** Applies to both XAML and coded test cases. See [references/testing-guide.md § XAML Test Case Structure](references/testing-guide.md) for the canonical patterns (the section's lead also points to the coded variant in `coded/operations-guide.md`).

12. **Trigger activity placement.** Two trigger types — identify from `uip rpa activities find --query "<event>" --output json` by reading `isTrigger` and `triggerType`. **Integration triggers** are strict (first activity of `Main.xaml`'s root `Sequence`; never inside `ui:TriggerScope`; `ConnectionId` required for IS-based ones); **local triggers** are flexible (root or `ui:TriggerScope`). Before placing, editing, or reading any trigger activity, read [trigger-pattern-guide.md](references/trigger-pattern-guide.md) — placement rules, decision rule (including unknown `triggerType` → ask, do not assume), connection handling, catalog, worked examples, and existing-`ui:TriggerScope` editing.

### Destination Preflight (Both Modes)

**Studio Web destination → Solution-wrapped deliverable, not a bare project.** Studio Web ingests Solutions only; a bare project folder is invisible in both SW workspace tabs. Treat these phrases as SW signals in the request: "Studio Web", "SW", "upload to web", "browser editor", "cloud workspace edit". On match, build the RPA project normally per the rest of this skill, then hand off to `uipath-solution` to wrap and ship it: `uip solution init <NAME>` → `uip solution project import "<PROJECT_DIR>" --solutionFile <SOLUTION>.uipx` → `uip solution upload "<SOLUTION_DIR>"`. The final deliverable is the Solution, not the bare project folder. Local execution (`uip rpa run`) and the Orchestrator package flow (`uip rpa pack` → `uip or packages upload` — there is no `uip rpa publish`) are fine with a bare project — only an SW destination changes the deliverable shape.

### Execution Discipline (Both Modes)

**Run to completion — do not declare work done while plan tasks remain.** If a plan file exists at `docs/plans/*.md` referenced by this request (or discoverable there for this feature), read its header before acting and during every checkpoint.

- If the header has `Execution autonomy: autonomous`: continue until ALL plan task checkboxes are `[x]` OR a concrete item from the plan's `Stop conditions` section is hit.
- If the header has `Execution autonomy: interactive`, or no plan file exists: use judgment and confirm with the user on material decisions.
- Before declaring the task done, re-read the plan and enumerate any unchecked boxes. If unchecked tasks remain and no Stop condition was hit, keep going — do not summarize partial work as "Done".
- "Feels expensive", "many tool calls used", "natural pause point", "partial result looks usable", and "too complex to continue in one session" are **NOT** Stop conditions. Only the concrete hard blockers in the plan's `Stop conditions` section count.
- Plan decisions already made are authoritative. Do not `AskUserQuestion` about structure, file count, selector strategy, or capture approach when the plan specifies them — those questions belonged to the planner.

### Call Batching (Both Modes)

**Batch independent tool calls into one assistant message — minimize model round-trips.** Two points in a new-project build serialize needlessly by default; collapse each into a single message.

1. **Post-`init` prerequisite batch.** After `uip rpa init` returns, these depend only on the project existing — NOT on each other. Emit them in ONE message:
   - `Read` `project.json` + the scaffolded `Main.xaml`
   - `uip rpa analyzer-rules list` (Rule 3 authoring-phase prerequisite)
   - `uip rpa packages install` for packages already known from the request
   - `uip rpa activities find` for activities you'll author

   These share the warmed Studio host (§ Session Pre-warm) — pay the cold-start once, then fire the batch.
2. **Activity-discovery fan-out.** XAML Rule 21 ([references/xaml/critical-rules-xaml.md](references/xaml/critical-rules-xaml.md)) runs a triple per non-card activity (`activities find` → read `<Activity>.md` → `get-default-xaml`). For K activities, emit all K `find`s as parallel `Bash`, then all K doc `Read`s in parallel, then all K `get-default-xaml`s in parallel — never one activity at a time. See [xaml/workflow-guide.md § Phase 1](references/xaml/workflow-guide.md).

**Chaining:** chain dependent `uip` calls with `&&` in one `Bash`; emit independent `Bash` / `Read` calls as parallel tool uses. Split a turn only where a call needs an earlier call's stdout or a file mutation.

**Do NOT batch — sequential by design:**
- `templates search` → `init`. The search result (and possibly an `AskUserQuestion`) picks `--template-package-id` (Rule 2). Decision gate, not a chain.
- The **per-file `validate` / per-activity authoring loop** (Rule 4, XAML Rule 18). Build one activity at a time, validate after each; project-level `build` runs once at the end. Batching validation hides which activity broke and burns the 5-attempt cap (Rule 3).

### Coded-Specific Rules

13. **[Coded] ALWAYS inherit from `CodedWorkflow`** base class for workflow and test case classes (NOT for Coded Source Files).
14. **[Coded] ALWAYS use `[Workflow]` or `[TestCase]` attribute** on the `Execute` method.
15. **[Coded] Update `project.json` → `entryPoints`** when adding/removing workflow files in **Process** projects. **Tests and Library projects do NOT use `entryPoints`** — skip this step for those project types. For `fileInfoCollection` (required for every test case in every project type — XAML and coded alike), see Common Rule 10.
16. **[Coded] One workflow/test case class per file**, class name must match file name.
17. **[Coded] Namespace = sanitized project name** from `project.json`. Sanitize: remove spaces, replace hyphens with `_`, ensure valid C# identifier.
18. **[Coded] Entry method is always named `Execute`**.
19. **[Coded] Use Coded Source Files** for reusable code — plain `.cs` files without `CodedWorkflow` inheritance, no entry point.

Working in coded mode? Also read [references/coded/critical-rules-coded.md](references/coded/critical-rules-coded.md) before authoring — `.cs` file types, service-to-package mapping, `CodedWorkflow` built-in surface, templates.

### XAML-Specific Rules (16–24)

Editing or creating XAML? Read [references/xaml/critical-rules-xaml.md](references/xaml/critical-rules-xaml.md) IN FULL before authoring — it carries Critical Rules 16–24 (activity docs as source of truth, structure-first reading, minimal iteration, error-fix order, ViewState handling, the Rule 21/21a activity-discovery procedure, the xaml-basics read mandate, `expressionLanguage`/`targetFramework` immutability, container-`Sequence` wrap) plus the XAML quick reference (workflow types, expression language, key CLI commands, common activities, file anatomy).

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Work in a Legacy (.NET 4.6.1) project** | Legacy | [legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) — entry point. Modern-mode rules in this file do not apply. |
| **Choose coded vs XAML** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) |
| **Work in a hybrid project** | Hybrid | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [project-structure.md](references/project-structure.md) |
| **Create a new project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Add/edit a coded workflow** | Coded | [coded/critical-rules-coded.md](references/coded/critical-rules-coded.md) → [coded/operations-guide.md](references/coded/operations-guide.md) → [coded/coding-guidelines.md](references/coded/coding-guidelines.md) |
| **Add a coded test case** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Set up data-driven testing** | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Create XAML test case (Given-When-Then)** | XAML | [testing-guide.md § XAML Test Case Structure](references/testing-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Use mock testing** | XAML | [testing-guide.md § Mock Testing (WIP)](references/testing-guide.md) — requires CLI command not yet available |
| **Use XAML test activities** | XAML | [testing-guide.md § XAML Test Activities](references/testing-guide.md) |
| **Use execution templates** | XAML | [testing-guide.md § Execution Templates](references/testing-guide.md) |
| **Create/edit XAML workflow** | XAML | [xaml/critical-rules-xaml.md](references/xaml/critical-rules-xaml.md) → [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) |
| **Use a common activity** (`Sequence` / `If` / `Switch<T>` / `TryCatch` / `While` / `DoWhile` / `ForEach<T>` / `Assign` / `LogMessage` / `WriteLine` / `Delay` / `Throw` / `Rethrow`) | XAML | [common-activity-card.md](references/common-activity-card.md) |
| **Create Flowchart/StateMachine** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) |
| **Create/edit Long Running Workflow (ProcessDiagram)** | XAML | [xaml/long-running-workflow-guide.md](references/xaml/long-running-workflow-guide.md) → [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) |
| **Write UI automation** | Both | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) |
| **Build multi-screen UIA XAML workflow** | XAML | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md § Multi-Step UI Flows](references/uia-configure-target-workflows.md) |
| **Share Object Repository selectors across projects (UI Library)** | Both | [ui-automation-guide.md § Object Repository as a Published UI Library](references/ui-automation-guide.md) |
| **Use Excel/Word/Mail/etc.** | Both | [coded/critical-rules-coded.md § Service-to-Package Mapping](references/coded/critical-rules-coded.md) → `.local/docs/packages/{PackageId}/` → fallback: `references/activity-docs/{PackageId}/{closest}/` |
| **Use Data Fabric entities** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [activity-docs overview](references/activity-docs/UiPath.DataService.Activities/overview.md) |
| **Query Data Fabric with filters** | XAML | [data-service-filter-builder-guide.md](references/activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) → [QueryEntityRecords](references/activity-docs/UiPath.DataService.Activities/activities/QueryEntityRecords.md) |
| **Call an IS connector (coded)** | Coded | [coded/integration-service-guide.md](references/coded/integration-service-guide.md) |
| **Call an IS connector (XAML)** | XAML | [is-connector-xaml-guide.md](references/is-connector-xaml-guide.md) → [connector-capabilities.md](references/connector-capabilities.md) |
| **Build an event-triggered workflow** (O365 / Gmail / Salesforce / Jira / Slack / ServiceNow / time / queue / file watcher / UI click) | XAML | [trigger-pattern-guide.md](references/trigger-pattern-guide.md) → `activity-docs/{PackageId}/{closest}/activities/<TriggerActivity>.md` |
| **Inspect Integration Service trigger lifecycle** (webhook vs. polling, filter fields, webhook URL retrieval) | Both | [trigger-pattern-guide.md § Connection Handling](references/trigger-pattern-guide.md) and [§ Server-Side Filtering](references/trigger-pattern-guide.md) |
| **Read or edit an existing `ui:TriggerScope` workflow** | XAML | [trigger-pattern-guide.md § Reading and Editing Existing TriggerScope XAML](references/trigger-pattern-guide.md) |
| **Build/run/validate** | Both | [validation-guide.md](references/validation-guide.md) → [cli-reference.md](references/cli-reference.md) for command flags and known CLI bugs |
| **Profile a slow workflow / verify UI automation correctness** | Both | [debugging.md § Profiling Workflow Performance](references/debugging.md) |
| **Pack & publish project to Orchestrator** | Both | [publishing-guide.md](references/publishing-guide.md) |
| **List project best-practice / analyzer rules** | Both | [cli-reference.md § analyzer-rules list](references/cli-reference.md) |
| **Add a NuGet package** | Coded | [coded/operations-guide.md § Add Dependency](references/coded/operations-guide.md) → [coded/third-party-packages-guide.md](references/coded/third-party-packages-guide.md) |
| **Find / reuse existing tenant libraries** | Both | [tenant-library-search-guide.md](references/tenant-library-search-guide.md) |
| **Extract reusable logic into a library** | Both | [library-authoring-guide.md](references/library-authoring-guide.md) — public-workflow contract, argument naming, private helpers |
| **Publish a library** | Both | [library-authoring-guide.md § Pack & Publish](references/library-authoring-guide.md) — tenant libraries feed, versioning |
| **Invoke a PowerShell script from a workflow** | Both | [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| **List / install Data Fabric entities** | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md) |
| **Discover activity APIs** | Coded | [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md) |
| **Troubleshoot coded errors** | Coded | [coded/coding-guidelines.md § Common Issues](references/coded/coding-guidelines.md) |
| **Troubleshoot XAML errors** | XAML | [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) → [validation-guide.md](references/validation-guide.md) |
| **Understand project structure** | Both | [project-structure.md](references/project-structure.md) |

## Precondition: Project Context

Before doing any work, check if `.claude/rules/project-context.md` exists in the project directory.

- **File exists** → check staleness per [environment-setup.md § Project Context Discovery](references/environment-setup.md): compare its `<!-- discovery-metadata: cs=N xaml=N deps=N -->` counts against current `.cs`/`.xaml` file counts and `project.json` dependency count; any count off by 60–70% or more → stale.
- **File missing or stale** → run the discovery flow in [environment-setup.md § Project Context Discovery](references/environment-setup.md): trigger the `uipath-project-discovery-agent`, write its output to **both** `.claude/rules/project-context.md` and `AGENTS.md` (between the `PROJECT-CONTEXT` markers if present), then proceed.
- **Fresh** → proceed with the skill workflow.

## Step 0: Resolve PROJECT_DIR

Before creating or modifying anything, determine which project to work with. See [references/environment-setup.md](references/environment-setup.md) for the full procedure.

**Quick check:** Find `project.json` to establish `{projectRoot}`. That's it — no Studio Desktop check needed for the standard loop. `uip rpa` auto-launches a headless Studio (UiPath.Studio.Helm NuGet) on first call. Studio Desktop is required only for `files diff`, `focus-activity`, and regenerating coded UI automation's `ObjectRepository.cs` (the `Descriptors.*` class — see Rule 7 and [environment-setup.md](references/environment-setup.md)).

## Project Type Detection

After establishing `PROJECT_DIR`, **first check `project.json` for `targetFramework`**:

- **`targetFramework: "Legacy"` (or field absent in an older project) → Legacy mode.** Stop here and switch to the Legacy-mode workflow: [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md). Legacy projects use the standalone `uip rpa-legacy` CLI, .NET Framework 4.6.1, classic activities (no "X" suffix), and `mscorlib` assembly references. The rest of this SKILL.md (modern mode) does NOT apply to Legacy projects.
- **`targetFramework: "Windows"` or `"Portable"` (Cross-platform) → Modern mode**, continue below.

For modern projects, determine whether this is a **coded** or **XAML** project:

1. **Coded mode** — `.cs` files with `[Workflow]` or `[TestCase]` attributes exist AND no `.xaml` workflow files (beyond scaffolded `Main.xaml`)
2. **XAML mode** — `.xaml` workflow files exist AND no coded workflow `.cs` files
3. **Hybrid** — Both exist → consult [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) to pick the right mode for each new file; default to matching the user's current request
4. **New project** — Neither exists → **default to XAML.** Switch to coded only on explicit coded phrasing ("coded", ".cs", "C# workflow", "coded test case") or a coded-specific trigger (custom data models / DTOs, unit-testable business logic); all other phrasings ("create a workflow", "automate X") mean XAML. Full decision flowchart: [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

**Routing:** Once mode is determined, use the Task Navigation table above to find the right reference files. For guidance on **choosing** between coded and XAML approaches, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md). For Legacy projects, follow [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) instead.

## Authoring Mode Selection

**Default to matching the project's existing mode; for new projects or ambiguous cases, default to XAML** (Project Type Detection item 4) — it is the more common mode, has the widest activity coverage, and is the unmarked term in user vocabulary. Switch to coded only on explicit user phrasing or a coded-specific trigger from the table below.

| Scenario | Mode | Why |
|----------|------|-----|
| Standard RPA (Excel, email, file ops) | **XAML** (default) | Direct activity support, no code needed |
| UI automation | **XAML** (default) | Full activity support; coded also works via `uiAutomation` service |
| Integration Service connectors (XAML) | **XAML** | IS connector activities use XAML-specific dynamic activity config |
| No matching activity for a subtask | **Coded fallback** | Small .cs invoked from XAML via `Invoke Workflow File` |
| Complex data transforms, HTTP, parsing | **Coded** | C# is more natural than nested XAML activities |
| Tempted to call a PowerShell script | **Coded** | Prefer a coded workflow. If PS is genuinely needed (admin cmdlets, existing `.ps1`), use the `InvokePowerShell<T>` activity — never `Invoke Process` + `powershell.exe`. See [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| Custom data models / DTOs | **Coded Source File** | XAML cannot define types — plain `.cs`, no `CodedWorkflow` base |
| Unit tests with assertions | **Coded Test Case** | `[TestCase]` with Arrange/Act/Assert |
| User explicitly requests coded/XAML | **User's choice** | Never second-guess explicit preference |

### UI Automation Boundaries

For any task whose business behavior is "open an app/browser, click, type, scrape visible UI, submit a form, or verify UI state", the interaction layer MUST be UiPath UI Automation — `NApplicationCard` plus UIA activities (XAML), or `uiAutomation.Open`/`Attach` plus Object Repository descriptors (coded). Do NOT substitute `InvokeCode`, PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or external browser-driver scripts — the full prohibited-tool list, UIA-only exploration requirement, and `InvokeJS`/`InjectJsScript` exception scope are in [ui-automation-guide.md § Mandatory: Generate Targets Before Writing Any UI Code](references/ui-automation-guide.md) (read in full per Rule 7). The coded fallback rows above apply only to non-UI helper logic. If target configuration is unavailable, follow Rule 7a's fallback ladder — never an external browser-automation shortcut.

**Running a UIA workflow:** use `uip rpa debug start` throughout development, not `run` — debug pauses on error and leaves UI state inspectable; `run --skip-build` is only the final smoke test. Full procedure (window baseline → `debug start` → cancel → window diff → selector-failure recovery, plus capture-time advancement rules): [ui-automation-guide.md § Running UI Automation Workflows](references/ui-automation-guide.md).

### Placeholder-Selector Stub Pattern (when live app access is unavailable)

When generating a UI automation workflow **without** live app access (app not installed, agent has no UI, or capture explicitly deferred to a developer), emit **real UIA activities with placeholder selectors and `TODO Indicate` markers** — never `Log` stubs: a `Log` stand-in passes build/validate, runs cleanly, and does nothing — the most expensive kind of stub. Applies to **both** XAML and coded modes. Marker placement and full XAML/coded examples: [ui-automation-guide.md § Placeholder-Selector Stub Pattern](references/ui-automation-guide.md) (read in full per Rule 7).

**Hybrid pattern** — XAML orchestration + coded fallback for logic with no matching activity:

    Main.xaml                  ← orchestration (XAML)
      └── InvokeWorkflowFile → ProcessData.cs  ← coded logic

For the full decision flowchart, InvokeCode extraction rules, and detailed hybrid patterns, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Capture-First Fast Path

When the request is "automate this dialog/form" or "build a UI test from these manual steps" — i.e. the bulk of the work is target capture, not coding — defer authoring-phase prerequisites (§ Precondition project-context discovery, Rule 3's analyzer-rules list) until capture completes. Fast-path order, skip conditions (no UI surface; no live app → Placeholder-Selector Stub Pattern), and the app-installed check: [ui-automation-guide.md § Capture-First Fast Path](references/ui-automation-guide.md) — read in full per Rule 7 first.

## Session Pre-warm

First heavy `uip rpa` call pays a ~22s Studio host cold-start (shared across `validate`/`build`/`run`/`activities get-default-xaml`/`analyzer-rules list`). When more than one is expected this session, background a cheap warm-up at session start so the tax hides behind planning:

```bash
uip rpa activities find --query log --output json > /dev/null 2>&1 &
```

**Skip** when 0 or 1 heavy `uip rpa` calls are expected (read-only Q&A, single-file inspection) — the warm-up doesn't reclaim its cost.

## Coded Workflows Quick Reference

Coded workflows use standard C# development: create file → write code → validate → run. Activity discovery (`activities find`, `activities get-default-xaml`) is XAML-specific — for coded mode, resolve service API docs in this order:

0. [coded/service-quick-card.md](references/coded/service-quick-card.md) — signatures for the most-used `system.*` / `excel.*` / `testing.*` calls (queues, assets, ranges, verifications). Covers most scenarios without opening a full API doc; escalate below when a signature, overload, or enum is missing.
1. `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` — present only after the package is installed in the project.
2. Bundled fallback (new projects, before install): Glob `references/activity-docs/{PackageId}/*/coded-api.md` and `references/activity-docs/{PackageId}/*/coded/coded-api.md` — the version folder's layout varies by package, so match both patterns. Read only the H2 sections for the services you need.
3. `packages inspect` — see [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md).

`.cs` file types, the service-to-package mapping, `CodedWorkflow` built-in methods, workflow invocation, and templates: [coded/critical-rules-coded.md](references/coded/critical-rules-coded.md). Integration Service connections, hooks, and job context: [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md).

## Resolving Packages & Activity Docs

Follow this flow whenever you need to use an activity package:

### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies`. **Always query versions with `--include-prerelease`** — previews carry the freshest activity surface and `.local/docs`; without the flag the listing hides them and you pick a stale stable. Installed but a newer stable/preview exists → inform the user (installed vs latest, newer packages best support activity generation) and ask before upgrading; **never force-upgrade**. Absent → install the latest from `packages versions --include-prerelease` (preview acceptable). Error handling: [cli-reference.md § packages install](references/cli-reference.md).

```bash
uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages 'id=<PackageId>,version=<LATEST_VERSION>' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find activity docs (priority order)

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — auto-generated, most accurate. Use `Glob` + `Read` (not `Grep` — `.local/` is gitignored).
2. **Fall back to bundled references** at `references/activity-docs/{PackageId}/` — pick the version folder closest to what is installed.

## UI Automation References

UIA references live in two locations. Always cite by location so the reader knows which tree to open:

- **This skill** (`references/`, relative to this SKILL.md) — policy, decision logic, target-capture orchestration, debug/recovery flows: [ui-automation-guide.md](references/ui-automation-guide.md) (**the entry point for all UIA work** — Rule 7; read in full first), [uia-prerequisites.md](references/uia-prerequisites.md) (versions, upgrade consent, CLI-unavailable fallbacks), [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) (target capture, multi-step UI flows, indication fallback).
- **UIA activity pack** (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`, installed via `uip rpa packages install`) — concrete `uip rpa uia` CLI syntax, per-activity property surfaces, coded API surface, UIA skill internal procedures. Co-versioned with the package, so always source-of-truth over anything in this skill when they diverge. Doc map: [ui-automation-guide.md § UIA Activity Pack Doc Map](references/ui-automation-guide.md).

## Completion Output

**Before reporting "done", verify the plan is complete** (§ Execution Discipline): re-read `docs/plans/*.md` and scan its checkboxes. With `Execution autonomy: autonomous` and no `Stop conditions` item hit, resume the next unchecked task instead of reporting. If a Stop condition interrupted, name the exact item in the report. Fully checked, or `interactive` → report per the format below.

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — per-file `validate` result (all files passed, or remaining errors) **and** project-level `uip rpa build` result. Both must be clean to claim verification — `validate` clean alone is insufficient (it does not detect unknown member names or invalid enum values). If `build` has not run since the last edit, say so explicitly rather than claiming success.
3. **Plan completion** — which task checkboxes in `docs/plans/*.md` are now `[x]`; list any still `[ ]` and, for each, the Stop-condition item that interrupted it (or "not reached" if execution was cut short another way)
4. **How to run** — the `uip rpa run` (or `uip rpa debug start`) command (if applicable)
5. **Next steps** — follow-up actions (configure connections, add OR elements, fill placeholders)
6. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, use `/uipath-feedback` to send a report."

Do NOT use framing like "complete", "done", "finished", or "the automation is built" unless every plan task is checked off. "Partial", "stopped at <task N>", or "blocked by <stop condition>" is the honest framing otherwise.
