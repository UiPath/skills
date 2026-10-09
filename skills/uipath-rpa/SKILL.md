---
name: uipath-rpa
description: "Always invoke for `.xaml` or `.cs` workflow files. UiPath RPA — create, edit, validate, build, pack, run, debug coded `.cs` and `.xaml` workflows, Modern or Legacy. Live desktop/browser UI automation and exploration with Object Repository selectors, test case authoring, Integration Service connector calls. Packing stays here; solution `.uipx` deployment→uipath-solution. Non-solution Orchestrator ops→uipath-platform. Test reports→uipath-test. Agents→uipath-agents."
when_to_use: "User wants to create, edit, validate, debug, run, or pack a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'pack this project', 'build a .nupkg', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', a .NET Framework 4.6.1 / Windows-Legacy project, or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents)."
---

# UiPath RPA Assistant

Create, edit, manage, and run UiPath coded (C#) and low-code (XAML) projects. UIA covers Windows/macOS and desktop/web; targets use strict or fuzzy selectors (with anchors), Computer Vision, or semantic matching. `uia-configure-target` selects the route and falls back automatically.

> **Read every required reference in full before acting.** This SKILL.md routes to references; it does not replace them. Read whole files when a rule, Task Navigation entry, or section points to them. Do not grep or skim, use `--help`, or substitute prior knowledge. Exception: references prescribing targeted lookup (Grep `^##` for a table of contents, flags via `<command> --help`) are catalogs; read matching sections only. Skipped or partial references commonly cause errors that escape `validate` and appear at `build` or runtime.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## When to Use This Skill

Use for projects, workflows, tests or source files, dependencies or entry points, UiPath activities, validation/build/run/debugging, NuGet, tests/assertions, Integration Service connectors (Jira, Salesforce, ServiceNow, Slack, etc.), and desktop/web UI automation.

## UIA Prerequisites

All UIA work requires `UiPath.UIAutomation.Activities` at or above the skill's minimum version. [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md) is the sole source for version, check, discovery/install commands, and the **upgrade-consent matrix (NEVER install or upgrade UIA silently)**. Never hardcode the version from memory.

## Precondition: Project Context

<!--skill-flavor:project-context-precondition:start-->
Before any work, check `.claude/rules/project-context.md` in the project directory:
- **Exists and fresh:** proceed.
- **Missing or stale:** run the skip gate, then, only if it does not trip, follow [environment-setup.md § Project Context Discovery](references/environment-setup.md). This includes metadata-comment count staleness check (60–70% threshold), greenfield/empty/untouched-scaffold skip gate, host-specific discovery-agent spawn options, and `context-files:` / `SKIP:` status-line handling. The agent writes context files; do NOT reread or rewrite them. **Dispatch at most once per session:** reuse a running agent or produced context document; later discovery calls mean integrate the earlier dispatch, never spawn again.
- **Skip gate trips (greenfield / empty / untouched scaffold):** create no agent or context files now; after build, write both context files yourself per that section.
<!--skill-flavor:project-context-precondition:end-->

## Step 0: Resolve PROJECT_DIR

Before creating or modifying anything, determine the project per [references/environment-setup.md](references/environment-setup.md). Find `project.json` to establish `{projectRoot}`; no Studio Desktop check is needed for the standard loop. `uip rpa` auto-launches headless Studio (UiPath.Studio.Helm NuGet) on first call. Studio Desktop is required only for `files diff` and `focus-activity`. Coded UI automation's `ObjectRepository.cs` (`Descriptors.*`) regenerates on per-file `validate` once a `[Workflow]`/`[TestCase]` `.cs` is on disk (§ Capture-First Fast Path step 2; [coded/operations-guide.md § Configure UI Targets](references/coded/operations-guide.md#configure-ui-targets-object-repository)).

## Project Type Detection

After resolving `PROJECT_DIR`, **first inspect `project.json` `targetFramework`:**
- `targetFramework: "Legacy"` (or absent in an older project): stop and use [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md). Legacy uses standalone `uip rpa-legacy`, .NET Framework 4.6.1, classic activities (no “X” suffix), and `mscorlib` references; the rest of this SKILL.md does not apply.
- `targetFramework: "Windows"` or `"Portable"` (Cross-platform): modern mode; use `uip rpa`. “Windows” means Modern Windows-only, not Windows-Legacy.

> **Use `uip rpa-legacy` ONLY for `targetFramework: "Legacy"`, never as fallback when `uip rpa` is unavailable.** It can pack a Modern (`Windows`/`Portable`) project and exit 0; passing pack does not prove correct tool selection. Fix `uip rpa` instead.

For modern projects, determine authoring mode:
1. **Coded:** `.cs` files with `[Workflow]` or `[TestCase]`, and no `.xaml` workflow beyond scaffolded `Main.xaml`.
2. **XAML:** `.xaml` workflows and no coded workflow `.cs` files.
3. **Hybrid:** both; consult [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for each new file; default to the user's current request.
4. **New project:** neither; default to XAML. Choose coded only for explicit “coded”, “.cs”, “C# workflow”, “coded test case”, or coded-specific triggers (custom data models / DTOs, unit-testable business logic). Otherwise (“create a workflow”, “automate X”, “build an automation”), use XAML. See [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for the full decision flowchart.

Use Task Navigation after choosing a mode. For mode choice see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md); for Legacy see [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md).

## Authoring Mode Selection

Match existing project mode; for new or ambiguous projects default to XAML (widest activity coverage; unmarked “create a workflow” means XAML, “create a coded workflow” means coded). Choose coded only for explicit phrasing or a coded-specific trigger.

| Scenario | Mode | Why |
|----------|------|-----|
| Standard RPA (Excel, email, file ops) | **XAML** (default) | Direct activity support, no code needed |
| UI automation | **XAML** (default) | Full activity support; coded also works via `uiAutomation` service |
| Integration Service connectors (XAML) | **XAML** | IS connector activities use XAML-specific dynamic activity config |
| No matching activity for a subtask | **Coded fallback** | Small .cs invoked from XAML via `Invoke Workflow File` |
| Complex data transforms, HTTP, parsing | **Coded** | C# is more natural than nested XAML activities |
| Tempted to call a PowerShell script | **Coded** | Prefer coded; if PS is genuinely needed (admin cmdlets, existing `.ps1`), use `InvokePowerShell<T>`—never `Invoke Process` + `powershell.exe`. See [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| Custom data models / DTOs | **Coded Source File** | XAML cannot define types; plain `.cs`, no `CodedWorkflow` base |
| Unit tests with assertions | **Coded Test Case** | `[TestCase]` with Arrange/Act/Assert |
| User explicitly requests coded/XAML | **User's choice** | Never second-guess explicit preference |

### UI Automation Boundaries

If behavior opens an app/browser, clicks, types, scrapes visible UI, submits a form, or verifies UI state, the interaction layer MUST be UiPath UI Automation: `NApplicationCard` plus UIA activities (XAML); `uiAutomation.Open`/`Attach` plus Object Repository descriptors (coded); or, where the package's coded authoring guide § Selector-Only Targets allows, CLI-captured selectors via `TargetAppModel` / `Target.FromSelector` (coded). Do NOT substitute `InvokeCode`, PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or external browser-driver scripts. Coded fallbacks are only for non-UI helper logic (data transforms, parsing, DTOs, calculations, API-only integrations). If target configuration is unavailable, use the documented UIA indication path, never external browser automation.

The full prohibited-tool list, UIA-only exploration requirement, and `InvokeJS`/`InjectJsScript` exception scope are in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Mandatory: Generate Targets Before Writing Any UI Code; read it in full per Rule 7 before UIA work.

### Placeholder-Selector Stub Pattern (when live app access is unavailable)

For UI automation without live app access (app unavailable, no UI, or capture deferred), emit **real UIA activities with placeholder selectors and `TODO Indicate` markers**, never `Log` stubs. A UI-interaction step such as `Log("LoginWorkflow: type username")` with `// TODO[selectors]:` is forbidden: it passes build/validate but silently does nothing.

Use the real activity (`NTypeInto`, `NClick`, `NGetText`, `NApplicationCard`, etc.), leave its target descriptor selector as a placeholder string, and put `TODO Indicate` in its `DisplayName` (XAML) or adjacent `// TODO[Indicate]` comment (coded). The developer clicks **Indicate** on each marked activity in Studio. Applies to both modes; read [uia-starter-guide.md § Placeholder-Selector Stub Pattern](references/uia-starter-guide.md) before stub-mode authoring. No UIA package or CLI is required.

**Hybrid pattern:** XAML orchestration plus coded fallback for logic with no matching activity: `Main.xaml` → `InvokeWorkflowFile` → `ProcessData.cs`. See [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for decision flowchart, InvokeCode extraction rules, and hybrid patterns.

## Capture-First Fast Path

For “automate this dialog/form” or “build a UI test from these manual steps” (mostly target capture), defer authoring prerequisites until capture finishes: capture is interactive, app-state-sensitive, and time-bound; discovery steals time and adds nothing during capture.

1. **Read per Rule 7:** [uia-starter-guide.md](references/uia-starter-guide.md), UIA package core guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) in full, and the target-capture orchestration reference mandated by that guide.
2. **[Coded only] Before first `uip rpa` call, install every needed activity package and write an empty `[Workflow] public void Execute() { }` class (namespace per Rule 17).** The host generates `.local/.codedworkflows/` from packages and coded files present at first load. Loading without the stub causes authoring `CS0246 'CodedWorkflow'`, cleared only by host restart. Later `validate` refreshes only `ObjectRepository.cs`; `CodedWorkflow.cs` service accessors (`uiAutomation`, …) and `workflows.X` cross-call methods are first-load snapshots, so later package installation or a new cross-called workflow needs regen ([coded/operations-guide.md § Configure UI Targets](references/coded/operations-guide.md#configure-ui-targets-object-repository)).
3. **Pre-flight Window Baseline:** list top-level windows once; decide whether to launch the app (package guide § Window Baseline).
4. **Inventory manual-step targets** (Test Manager test case, PDD, or written script): map every “Click X” / “Enter Y” / “Select Z” / “Verify W” to one OR element; group by screen state (package guide § Capturing from Manual Test Steps); decide every element and screen name now and apply verbatim during capture.
5. **Capture all targets** screen-by-screen via `uia-configure-target` and screen advancement (package guide § Multi-Step UI Flows). Author only at screen boundaries, never between capture calls within a screen.
6. **Then author:** integrate discovery already dispatched if required (at most once; never spawn again), read mode's authoring guide (Rule 7), write code, validate. Coded: validate once to regenerate `ObjectRepository.cs`, read it, and reference every target as `Descriptors.<App>.<Screen>.<Element>`; member names come from that file, not OR names passed at capture. Never author against string target names while the file is missing.

Skip for no-UI tasks (data transforms, IS calls, headless file/email automation) or UI with no live app to capture (not installed, no GUI, capture deferred); for the latter use § Placeholder-Selector Stub Pattern. Window Baseline does not prove app installation or GUI availability: check separately (e.g. executable on disk) or ask the user.

## Session Pre-warm

The first heavy `uip rpa` call incurs ~22s Studio host cold-start, shared across `validate`/`build`/`run`/`activities get-default-xaml`/`analyzer-rules list`. If expecting more than one, background this at session start:

```bash
uip rpa activities find --query log --output json > /dev/null 2>&1 &
```

In Windows PowerShell, `&` does not background: use `Start-Process powershell.exe -ArgumentList ...` (not `pwsh`). Never `Start-Process -FilePath "uip"` (or any `.ps1`): Windows opens it in Notepad, not PowerShell. Skip for 0 or 1 heavy calls (read-only Q&A, single-file inspection); warm-up cannot repay its cost.

## Critical Rules

**Rule numbering:** Common Rules 1–12 below; Coded 13–19 in [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md); XAML 16–21a and 24 in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md), with 22 and 23 below. Numbers 16–19 occur in both mode sequences; `[Coded]` / `[XAML]` disambiguates. “Common Rule 10”, “Rule 21”, and “Rule 24” identify unique rules.

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Resolve per Step 0: explicit path, project name, then CWD for `project.json`. Create only if no matching project exists AND user explicitly requests creation.
<!--skill-flavor:rules-project-creation:start-->
2. **ALWAYS create projects with `uip rpa init`**, never manual `project.json` or scaffolding. Decide template need first. For named template (“REFramework”, “based on the X template”) or industry/domain pattern (SAP, ERP, banking, mainframe), first run `uip rpa templates search --query "<term>" --output json` and select per [environment-setup.md § Template selection](references/environment-setup.md). **NEVER silently pick a Marketplace template** (present candidates and ask). If a named template matches both Official and Marketplace items, ask; do not auto-pick.
2a. **Pass `--target-framework` AND `--expression-language` explicitly on every `uip rpa init`; never omit either.** Both are immutable after creation (Rule 23); omitting `--target-framework` silently creates **Windows**. Choose by runtime: cross-platform/non-Windows (Linux, container, serverless) or Studio Web editing → **`Portable`** (Cross-platform); Windows runtime needing Windows-only capabilities (Excel COM, classic Office, WPF / `PresentationFramework`, Windows-only UIA) or Studio Desktop as edit surface → **`Windows`** (not editable in Studio Web). Cross-platform runtime plus Windows-only capability is contradictory: surface it, do not choose silently. **Windows - Legacy is last resort** (explicit ask or hard .NET 4.6.1 need; never infer from VB.NET or non-“X” classic activities); create in Legacy mode, not modern `init`. With no signal, `AskUserQuestion` (Windows vs Cross-platform), framed around runtime host. `--expression-language`: default `VisualBasic`; `CSharp` only on explicit request.
<!--skill-flavor:rules-project-creation:end-->
<!--skill-flavor:rules-validation-gate:start-->
3. **Phase-gated validation:**
   - **Per-file:** after every create/edit, run `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors. Catches structural XAML, missing references, analyzer-rule, and schema violations. Fix one thing per iteration.
   - **Project build:** after all session files pass per-file `validate`, and before declaring done, run `uip rpa build "<PROJECT_DIR>" --output json` until clean. Covers all workflows (including untouched/unvalidated files), project-scope analyzer rules, and packaging; per-file passes do not prove project compilation. See [cli-reference.md § What each phase covers](references/cli-reference.md#what-each-phase-covers). On build errors, identify file in output and rerun `validate --file-path` on it.
   - **5-attempt cap per loop:** 5 per file's validate loop and a separate 5 for project build; fix one root cause per iteration.
   - Successful `uip rpa run` substitutes for standalone end-of-session build because `run` compiles internally. Prefer `run --skip-build` after a passing build; [cli-reference.md § Smoke Test](references/cli-reference.md#smoke-test).
   - Do NOT run `uip rpa analyzer-rules list` as an authoring prerequisite. `validate` and `build` enforce enabled rules and report IDs/recommendations; speculative unscoped calls can take a minute or more. Run on demand for user questions about project best-practice/analyzer rules or repeated violations suggesting the full rule set. See [cli-reference.md § analyzer-rules list](references/cli-reference.md#analyzer-rules-list).
   - Warnings do not gate delivery: 0 errors from `validate` and `build` satisfies the gate. Do NOT investigate/fix warnings unless requested or blocking acceptance criteria. UIA projects can correctly emit recurring verification-feature, Automation Hub URL, and duplicate display name warnings: [cli-reference.md § Expected non-defect warnings](references/cli-reference.md#expected-non-defect-warnings). Report warnings; do not spend gate attempts on them.

   See [cli-reference.md § Validation Iteration Loop](references/cli-reference.md#validation-iteration-loop).
4. **ALWAYS make every touched file per-file `validate` clean and verify project build before declaring done.** Rule 3 defines cadence/caps/coverage. Clean `validate` alone is insufficient; build is mandatory. A clean gate is not runtime proof: for observable-output workflows, end the gate with one `run` and check outputs ([execution-maps-guide.md § Gate ≠ runtime proof](references/execution-maps-guide.md#gate--runtime-proof)).
<!--skill-flavor:rules-validation-gate:end-->
5. Prefer UiPath built-in activities for Orchestrator integration, UI automation, and document handling; plain .NET / third-party packages for pure data transforms, HTTP, and parsing.
6. **ALWAYS ensure required package dependencies are in `project.json`** before using activities/services.
6a. **Pre-edit verification gate:** before removing a dependency, grep project usages (a package may supply an activity used elsewhere; `MergePDFs` is in the IntelligentOCR.StudioWeb family). Before writing an activity tag, confirm via `uip rpa activities find --query "<verb>" --output json` and use returned `ClassName`; never derive tag names from Studio display names. See [common-pitfalls.md § Common Activity Name Confusions](references/xaml/common-pitfalls.md).
7. **[UIA] Before writing ANY UIA activity** (`<uix:N*>` or coded `uiAutomation.*` / `Descriptors.*`), MUST read [references/uia-starter-guide.md](references/uia-starter-guide.md) via two-step read, never plain full Read: (1) Grep `^## Conditional Policies`, (2) Read with `limit` set to that line. The two policy sections below the marker load only when their stated condition applies. Then read mandated UIA package core guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) IN FULL, and before authoring read mode's authoring guide IN FULL as routed by core guide § Documentation. No “simple UI” exception. Skipping this rule is the most common cause of hallucinated selectors, wrong target XML, and missing OR descriptors. NEVER hand-write selectors: use exclusively `uia-configure-target` (package guide explains how); coded selector-only skips only Object Repository registration, not capture. Package guide exists only after package install: verify [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md) first (Rule 7a); if installed but absent, the installed version predates it — treat as below the minimum version. Starter guide owns skill-side UIA policies: run/debug and runtime selector recovery, stub deliverable, and UI Library publishing.
7a. **[UIA] Verify prerequisites before `uia-configure-target`.** Run the check in [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md), the only version source. If package is below minimum or package guide absent (Rule 7 treats missing guide as below-minimum), `uip rpa uia` is unavailable; capture and indication both require it, so indication is not fallback for missing package. Ask user to install/upgrade per that section. If declined or impossible, use § Placeholder-Selector Stub Pattern (real activities with `TODO Indicate`; no CLI). Never silently route to a nonexistent skill path. Use indication capture only with compatible package when `uia-configure-target` cannot see element; record `UI capture: indication-only` in plan header to skip `uia-configure-target`. For persistent UIA snapshot live-scan failures (driver/COM errors on every scan), first rule out locked/non-interactive Windows session (`LogonUI` running means lock screen): unlock, do not fallback. Only if scans still fail on an unlocked interactive session, treat capture as unavailable and use placeholder stubs.
8. Use `--output json` on all CLI commands whose output is parsed programmatically.
8a. **Judge `run` / `debug start` from `Data`, never outer `Result` alone or log level.** Identify backend by `Data` keys; shape varies:
   - **Headless Studio (Helm; no Studio Desktop instance has project open):** `{output, hasErrors, errorMessage, profiling, debugState, debugDetails}`. Pass only if `hasErrors` is `false`, `errorMessage` is `null`, and `debugState` is `null` or `"Completed"`. Faulted `run` returns outer `Result: "Failure"` with fields JSON-encoded in `Message`; faulted `debug start` returns `Result: "Success"`, `debugState: "Suspended"`, exception in `debugDetails`; session remains alive and must be cancelled or continued.
   - **Studio Desktop (project open in running Studio):** `{output, errors, logEntries, debugState}`. Pass only if `errors` is empty AND `output` is `"Session ended"`. Missing entry point returns `Result: "Success"`, `errors: []`, `output: "Failed to open the file <path>"`; both conditions are required.
   - `Result: "Success"` alone falsely greens failures on both backends. Successful workflows may emit `Log Message` at `Error`/`Warning` for observability (Helm `[Level]` lines above envelope; Desktop `logEntries`); these are workflow data, not failures; treating them as a failure signal flips green runs to "failed" and burns retries on healthy workflows.
   - Read printed envelope: no `--output-filter` on `run` / `debug start` (backend keys differ; a missing key makes call fail after execution), and never `| tail` / `| head` (Helm logs precede envelope; Desktop verdict precedes long `logEntries`; either can cut needed fields). See [cli-reference.md § Capturing the verdict](references/cli-reference.md#capturing-the-verdict), [cli-reference.md § Reading run / debug results](references/cli-reference.md#reading-run--debug-results), and [debugging.md § Output Format](references/debugging.md#output-format).
9. For “leverage / reuse / find shared libraries,” search tenant feed, not local filesystem, NuGet.org, or keyword-permutation loops. Run `uip or libraries list --limit 500 --output-filter "<JMESPath>" --output json`. Zero filtered results → fallback branch, do not re-keyword. Skip if SDD records §16 “Shared libraries referenced” or user earlier said “no shared libraries”. See [tenant-library-search-guide.md](references/tenant-library-search-guide.md).
10. Register every test case file in `project.json` → `designOptions.fileInfoCollection` (XAML and coded). Required keys, GUID format, JSON snippet, and schema (including `dataVariationFilePath` for data-driven and `publishAsTestCase` for coded): [references/testing-guide.md § project.json Registration](references/testing-guide.md) and [assets/json-template.md](assets/json-template.md).
11. Test cases use **Given-When-Then** in both modes. Canonical patterns: [references/testing-guide.md § XAML Test Case Structure](references/testing-guide.md); its lead links coded variant in `coded/operations-guide.md`.
12. **Trigger activity placement:** identify type using `uip rpa activities find --query "<event>" --output json`, reading `isTrigger` and `triggerType`.
   - **Integration** (`isTrigger: true`, `triggerType: "integration"`) — **strict placement.** MUST be the first activity of `Main.xaml`'s root `Sequence`; CANNOT be placed inside `ui:TriggerScope`. Bind `Result` to workflow-scope variable; remaining Sequence is handler. IS triggers (Mail / GSuite / O365 / Salesforce / Jira / Slack / ServiceNow / any `*.IntegrationService.Activities` package) require connection asset (`ConnectionId`); Orchestrator-native (`TimeTrigger`, `QueueTrigger`, `ManualTrigger`) do not.
   - **Local** (`isTrigger: true`, `triggerType: "local"`): either first activity of root `Sequence` (Orchestrator dispatches fresh job per event) or inside `<ui:TriggerScope.Triggers>` with handler in `<ui:TriggerScope.Action>` (robot stays alive while scope active; trigger fires in-process). Both valid; choose runtime model. No connection asset.
   - **Unknown `triggerType`** (forward-compatible, e.g. future `"scheduled"`): read bundled doc and ask user; do not assume placement.
   - Existing XAML: activity in `<ui:TriggerScope.Triggers>` must be local; integration there is broken—flag it. Root activity can be either; check `triggerType`.

   See [trigger-pattern-guide.md](references/trigger-pattern-guide.md) for examples, `SchedulingMode`, trigger catalog, and editing existing `ui:TriggerScope` workflows.

### Destination Preflight (Both Modes)

<!--skill-flavor:studio-web-destination:start-->
**Studio Web destination means a Solution-wrapped deliverable, not a bare project.** Signals: “Studio Web”, “SW”, “upload to web”, “browser editor”, “cloud workspace edit”. Studio Web ingests only Solutions; bare folders are invisible in both SW workspace tabs. If signaled, build RPA project normally, then hand off to `uipath-solution` to wrap and ship: `uip solution init <NAME>` → `uip solution projects import "<PROJECT_DIR>" --solutionFile <SOLUTION>.uipx` → `uip solution upload "<SOLUTION_DIR>"`. Deliver Solution, not bare project. Bare projects are fine for local `uip rpa run` and Orchestrator `uip rpa pack` → `uip or packages upload` (there is no `uip rpa publish`); only SW changes deliverable shape.
<!--skill-flavor:studio-web-destination:end-->

### Execution Discipline (Both Modes)

**Run to completion; do not stop with plan tasks remaining.** If request references or has discoverable `docs/plans/*.md`, read its header before acting and at every checkpoint.
- `Execution autonomy: autonomous`: continue until all task boxes are `[x]` or a concrete `Stop conditions` item is hit.
- `Execution autonomy: interactive`, or no plan: use judgment and confirm material decisions.
- Before declaring done, reread plan and enumerate unchecked boxes. If any remain and no Stop condition was hit, continue; do not call partial work “Done”.
- “Feels expensive”, many tool calls, natural pause, usable partial result, or complexity are NOT Stop conditions; only concrete plan `Stop conditions` count.
- Plan decisions are authoritative. Do not ask `AskUserQuestion` about structure, file count, selector strategy, or capture approach already specified by plan.

### Error Handling (Both Modes)

Wrap external UI/file/network/DB interactions in Try/Catch and classify failures: `BusinessRuleException` for bad input (no retry; human needed); system exceptions for transient faults (retry then escalate). Do not blanket-wrap pure logic or leave Catch empty; use `Rethrow`, never `Throw New Exception(ex.Message)`, to preserve stack trace. Before adding resilience, read [references/error-handling-guide.md](references/error-handling-guide.md) in full for exception taxonomy, Retry Scope count/interval semantics, `ContinueOnError` suppression, screenshot-on-error, Global Exception Handler recipe (scaffold + `project.json` registration + verdict logic), and patterns: recover app state before retry, per-item transaction boundaries, idempotent/compensating writes to avoid **duplicate creates** and partial writes, sensitive-data redaction, and **retry ownership** across queue/Retry-Scope/GEH/job layers.

### Execution Maps (Both Modes)

**Follow [execution-maps-guide.md](references/execution-maps-guide.md) for every build/edit**: it defines tool-call batches per assistant turn (greenfield ≤5 turns, brownfield ≤5; pitfalls vet turn included). Within a turn, chain dependent `uip` calls with `&&` in one `Bash`; issue independent `Bash`/`Read`/`Edit` calls in parallel. Split turns only when a call needs earlier stdout or a file mutation. Rule 21 off-card activity discovery fans out in T1/T2: all K `find`s parallel, then all K doc `Read`s, then all K `get-default-xaml`s; never one activity at a time.

**Never batch across sequential gates:** `templates search` → `init` (Rule 2 decision gate); any `AskUserQuestion` or consent gate; UIA state advances and indication (guide defines per-screen gates).

### Coded-Specific Rules

13–19. **[Coded]** Before creating/editing any coded workflow, test case, or source file, read [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md); these are mandatory, not reference-only. It also has coded quick reference (file types, service-to-package mapping, templates) and task navigation.

### XAML-Specific Rules

16–21a, 24–25. **[XAML]** Rules are in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md); Rule 22 requires reading it in full before XAML work. It also contains XAML task navigation and quick reference.
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) in full before generating/editing any XAML**, as a plain full Read in journey's first turn alongside card reads; no lookup precedes it. The file contains mandatory content only. For per-operation/activity catalogs use [references/xaml/xaml-editing-catalog.md](references/xaml/xaml-editing-catalog.md): Grep `^###`, Read matching entries; if unsure, read. **Before first `Write`/`Edit`, vet plan against [references/xaml/common-pitfalls.md](references/xaml/common-pitfalls.md).** common-pitfalls.md is a catalog of independent gotcha sections — do NOT read it end-to-end: list headings with Grep `^##` in first turn (no prior output needed); next turn, Read every section matching a workflow activity, property, or feature; if unsure, read. This prevents gotchas `validate` cannot catch. [execution-maps-guide.md](references/execution-maps-guide.md) fixes placement: heading list T1, section Reads T2; one turn, not a grep→Read pair per file.
23. **[XAML] NEVER change existing project's `expressionLanguage` or `targetFramework`.** Decide at init (Common Rule 2a); both fields are immutable and apply to every XAML file—changing either invalidates expressions or package references project-wide. Do not convert in place. For conversion, confirm with user and follow [environment-setup.md § Project Conversion](references/environment-setup.md): copy aside, `init` fresh with target settings, recreate every workflow, delete copy only after user agrees.

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Work in a Legacy (.NET 4.6.1) project** | Legacy | [legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) — entry point; modern rules do not apply. |
| **Plan build turn structure** | Both | [execution-maps-guide.md](references/execution-maps-guide.md) — first for any build/edit journey |
| **Choose coded vs XAML / hybrid** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [environment-setup.md § Designing Project Structure](references/environment-setup.md#designing-project-structure) |
| **Create a project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Any XAML authoring/editing** (workflows, tests, Flowchart/StateMachine/LRW, common activities, Data Fabric, IS connectors, triggers, troubleshooting) | XAML | [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — Rule 22; § Critical Rules — XAML + § Task Navigation — XAML route rest |
| **Any coded authoring/editing** (workflows, tests, source files, IS connectors, NuGet, API discovery, troubleshooting) | Coded | [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md) — § Critical Rules — Coded + § Task Navigation — Coded route rest |
| **Set up data-driven testing** | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md); register `fileInfoCollection` (Common Rule 10) |
| **Set up Test Manager** (server URL + default project) | Both | [cli-reference.md § Test Manager](references/cli-reference.md) — `uip rpa tm connect` / `set-default-project` |
| **Add error handling/resilience** (Try/Catch, Retry Scope, BusinessRuleException, ContinueOnError, screenshot-on-error, Global Exception Handler, app-state recovery, transaction boundaries, idempotency/duplicate creates, retry ownership) | Both | [error-handling-guide.md](references/error-handling-guide.md) |
| **Write UI automation** | Both | UIA package guide `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` (Rule 7) |
| **Share Object Repository selectors across projects (UI Library)** | Both | [uia-starter-guide.md § Object Repository as a Published UI Library](references/uia-starter-guide.md) |
| **Run/debug UIA workflow** | Both | [uia-starter-guide.md § Running UI Automation Workflows](references/uia-starter-guide.md) — baseline, debug, window cleanup, selector recovery |
| **Drive a captured control** (date inputs, native/custom dropdowns, buttons disabled during async) | Both | UIA package guide § Control-Specific Interaction Patterns |
| **Use Excel/Word/Mail/etc.** | Both | `.local/docs/packages/{PackageId}/`; fallback `references/activity-docs/{PackageId}/{closest}/` (see § Resolving Packages & Activity Docs) |
| **Manipulate data** (DataTable/LINQ, strings, RegEx, DateTime, collections, JSON) | Both | [data-manipulation-guide.md](references/data-manipulation-guide.md) |
| **Inspect Integration Service trigger lifecycle** (webhook/polling, filter fields, webhook URL retrieval) | Both | [trigger-pattern-guide.md § Connection Handling](references/trigger-pattern-guide.md) and [§ Server-Side Filtering](references/trigger-pattern-guide.md) |
| **Build/run/validate** | Both | [cli-reference.md](references/cli-reference.md), per-command catalog, do NOT read end-to-end: Grep `^## `, Read every command section you will run, plus § Reading run / debug results regardless — the outer `Result` is not the run's verdict, and reading it as one reports failed workflows as passing |
| **Profile slow workflow / verify UIA correctness** | Both | [debugging.md § Profiling Workflow Performance](references/debugging.md) |
| **Pack & publish to Orchestrator** | Both | [cli-reference.md § Pack & Publish to Orchestrator](references/cli-reference.md#pack--publish-to-orchestrator) |
| **List best-practice/analyzer rules** | Both | [cli-reference.md § analyzer-rules list](references/cli-reference.md) |
| **Find/reuse tenant libraries** | Both | [tenant-library-search-guide.md](references/tenant-library-search-guide.md) |
| **Extract/publish reusable library logic** | Both | [library-authoring-guide.md](references/library-authoring-guide.md) — public-workflow contract, private helpers, § Pack & Publish |
| **Invoke PowerShell from workflow** | Both | [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| **List/install Data Fabric entities** | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md) |
| **Understand project structure** | Both | [environment-setup.md § Project Structure Reference](references/environment-setup.md#project-structure-reference) |

## Mode Packs

Mode rules, quick reference, and task navigation live with each mode's primary reference; read per gates above (Rule 22 for XAML; Coded Rules 13–19):
- **XAML:** [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — § Critical Rules — XAML, § XAML Task Navigation & Quick Reference, authoring workflow, anatomy; per-entry operations/examples in [xaml/xaml-editing-catalog.md](references/xaml/xaml-editing-catalog.md).
- **Coded:** [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md) — § Critical Rules — Coded, § Coded Quick Reference (file types, service-to-package mapping, templates), § Task Navigation — Coded, base-class reference.

## Resolving Packages & Activity Docs

For any activity package:

### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies`. **Always query versions with `--include-prerelease`**: packages may ship `-preview` between stable releases, adding activities, fixing signatures, and updating `.local/docs`; without the flag, stale stable versions may be selected.
- **Present:** note installed version, list available versions with `--include-prerelease`, compare. If newer stable or preview exists, inform user of installed/latest versions and that newer packages improve activity generation (latest surface, accurate `.local/docs`, fewer signature mismatches); ask whether to upgrade. Never force-upgrade an installed package. If already latest, proceed.
- **Absent:** install latest from `packages versions --include-prerelease` (preview is acceptable):

```bash
uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages 'id=<PackageId>,version=<LATEST_VERSION>' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find activity docs (priority order)

1. Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/` (auto-generated, most accurate). Read exact file directly (`.../{PackageId}/activities/<Activity>.md`); failed Read checks existence. `Glob` and `Grep` skip gitignored `.local/`; misses prove nothing. Use Bash `ls` on exact directory to list contents. NEVER enumerate docs tree (hundreds of files; UIA guide § Documentation lists every reference).
2. Fall back to bundled `references/activity-docs/{PackageId}/`, choosing version folder closest to installed.

## UI Automation References

UIA references have two locations; cite location so readers know which tree:
- **This skill (`references/`):** skill-owned policies—prerequisites/version gating, run/debug orchestration, stub deliverables, UI Library publishing.
- **UIA activity pack (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`), installed with `uip rpa packages install`:** authoring guide, target-capture orchestration, task guides, concrete `uip rpa uia` syntax, per-activity properties, coded API, internal procedures. Co-versioned and authoritative over skill content when they diverge.

### In this skill (`references/`, relative to this SKILL.md)

- [uia-starter-guide.md](references/uia-starter-guide.md) — read first for any UIA work (Rule 7); mandates package guide, owns skill-side run/debug (baseline → debug → cancel → window cleanup), profiling/runtime selector recovery, placeholder stubs, UI Library publishing, and prerequisite/upgrade consent.

### In the UIA activity pack (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`)

- `ui-automation-guide.md` — entry point for all UIA authoring; read fully first (Rule 7), check availability under Rule 7a. Use Bash `ls` on exact path or direct Read; `Glob`/`Grep` skip gitignored `.local/`, so misses never prove absence. Never enumerate docs tree. Covers window baseline, capture orchestration, pitfalls, control-specific interaction, coded/XAML patterns; § Documentation routes to target-capture orchestration, task guides, CLI inventory, per-activity properties, coded API, runtime selector recovery, and bundled UIA skill (`uia-configure-target`).

## Completion Output

**Before reporting done, verify plan completion.** If a `docs/plans/*.md` drove work:
1. Reread plan and scan task checkboxes.
2. If `[ ]` remains, autonomy is `autonomous`, and no `Stop conditions` item was hit, do not report done; resume execution on the next unchecked task.
3. If unchecked boxes remain due to a Stop condition, name exact item in report.
4. If all checked or autonomy is `interactive`, report below.

If harness provides persistent memory, save only patterns qualified by [execution-maps-guide.md § Cross-session memory](references/execution-maps-guide.md#cross-session-memory) (first-try clean gate on card-covered activities qualifies none). Make memory `Write`s parallel with report and context-file writes, never in their own turns. Output check links the gate chain; report is one message carrying context-file writes, memory writes, and text below; nothing runs after it.

When finishing, report:
<!--skill-flavor:report-what-was-done:start-->
1. **What was done** — list paths of created, edited, or deleted files.
<!--skill-flavor:report-what-was-done:end-->
<!--skill-flavor:report-validation-status:start-->
2. **Validation status** — per-file `validate` results (all passed or remaining errors) AND project-level `uip rpa build`. Claim verification only if both are clean; `validate` covers only targeted files, `build` compiles whole project (Rule 3). If build has not run since last edit, say so explicitly.
<!--skill-flavor:report-validation-status:end-->
3. **Plan completion** — which `docs/plans/*.md` checkboxes are `[x]`; list any `[ ]` and, for each, the Stop-condition item that interrupted it (or “not reached” if execution was cut short another way).
<!--skill-flavor:report-how-to-run:start-->
4. **How to run** — `uip rpa run` (or `uip rpa debug start`) command, if applicable.
<!--skill-flavor:report-how-to-run:end-->
5. **Next steps** — follow-ups (configure connections, add OR elements, fill placeholders).
6. **Trouble?** — if user hit issues, say: “If something didn't work as expected, use `/uipath-feedback` to send a report.”

Do NOT say “complete”, “done”, “finished”, or “the automation is built” unless every plan task is checked. Otherwise say “Partial”, “stopped at <task N>”, or “blocked by <stop condition>”.