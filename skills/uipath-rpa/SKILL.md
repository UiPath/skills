---
name: uipath-rpa
description: "Always invoke for `.xaml`/`.cs` workflow files. UiPath RPA (Modern or Legacy): create, edit, validate, build, pack, run, debug coded `.cs` and `.xaml` workflows; UI automation with Object Repository selectors; live desktop/browser UI exploration/control; test case authoring; Integration Service connector calls. Packing stays here; solution-level `.uipx` deployment→uipath-solution; non-solution Orchestrator ops→uipath-platform; test reports→uipath-test; agents→uipath-agents."
when_to_use: "User wants to create, edit, validate, debug, run, or pack a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'pack this project', 'build a .nupkg', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', a .NET Framework 4.6.1 / Windows-Legacy project, or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents)."
---

# UiPath RPA Assistant

Create, edit, manage, validate, build, run, debug, test, and publish UiPath coded (C#) and XAML automations. One UIA activity set covers Windows/macOS, desktop/web, strict/fuzzy selectors with anchors, Computer Vision, and semantic matching; `uia-configure-target` selects and automatically falls back between routes.

> **Read referenced files imperatively.** This SKILL.md routes you; it does not replace references. When a rule, Task Navigation entry, or section points to a file, open and read it in full before acting—do not grep, skim, use `--help`, or substitute prior knowledge. Catalogs may prescribe targeted lookup (for example, Grep `^##` for contents or `<command> --help` for flags); read matching sections only. A pointer naming a section (`file.md § Section`) is targeted through the next heading of its level. Skipped or partial references commonly cause build/runtime errors.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## When to Use This Skill

Use for projects, workflows, tests, source files, configuration, dependencies, activities, validation/build/run/debug, assertions, Integration Service connectors, and desktop/web UI automation.

## UIA Prerequisites

UIA work requires `UiPath.UIAutomation.Activities` at or above its minimum version. Version, checks, discovery/install commands, and the upgrade-consent matrix (**NEVER install or upgrade UIA silently**) are only in [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md); do not hardcode the version.

## Precondition: Project Context

<!--skill-flavor:project-context-precondition:start-->
Before work, check `.claude/rules/project-context.md` in the project directory. If present and fresh, proceed. If missing/stale, run the skip gate and, only if it does not trip, perform [environment-setup.md § Project Context Discovery](references/environment-setup.md): metadata-comment counts versus current counts, the 60–70% threshold, greenfield/empty/untouched-scaffold skip gate, host-specific discovery-agent options, and `context-files:`/`SKIP:` handling. The agent writes context files; do not re-read or rewrite them. **Dispatch discovery AT MOST ONCE per session** — reuse a running agent or its produced result; a later step that calls for project-context discovery means INTEGRATE the earlier dispatch, never spawn a second. If the skip gate trips, use no discovery agent and write both context files yourself after build per that section.
<!--skill-flavor:project-context-precondition:end-->

## Step 0: Resolve PROJECT_DIR

Before creating/modifying anything, resolve the project using [environment-setup.md § Step 0.1](references/environment-setup.md#step-01-establish-project-root). Find `project.json` to establish `{projectRoot}`; no Studio Desktop check is needed for the standard loop. `uip rpa` auto-launches a headless Studio (UiPath.Studio.Helm NuGet) on first call. Studio Desktop is required only for `files diff` and `focus-activity`. Coded UI `ObjectRepository.cs` (`Descriptors.*`) regenerates on per-file `validate` after a `[Workflow]`/`[TestCase]` `.cs` exists (§ Capture-First Fast Path step 2; [coded/operations-guide.md § Configure UI Targets](references/coded/operations-guide.md#configure-ui-targets-object-repository)).

## Project Type Detection

After resolving `PROJECT_DIR`, inspect `project.json` `targetFramework` first:

- `"Legacy"` or absent in an older project: Legacy mode. Stop and follow [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md). Use standalone `uip rpa-legacy`, .NET Framework 4.6.1, classic activities without “X”, and `mscorlib`; modern rules do not apply.
- `"Windows"` or `"Portable"`: Modern mode; use `uip rpa`. `Windows` means modern Windows-only, not Windows-Legacy.

Use `uip rpa-legacy` only for Legacy, never because `uip rpa` is unavailable; it can pack Modern projects with exit 0, so fix `uip rpa` instead.

Modern mode: coded = `.cs` with `[Workflow]`/`[TestCase]` and no workflow `.xaml` beyond scaffolded `Main.xaml`; XAML = workflow `.xaml` and no coded workflow `.cs`; both = hybrid, consult [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) and match the request; neither = new project, default XAML. Switch to coded only for explicit “coded”, “.cs”, “C# workflow”, “coded test case”, or coded-specific triggers (DTOs/custom models/unit-testable business logic). Otherwise “create a workflow”, “automate X”, and “build an automation” mean XAML. Route through Task Navigation; Legacy follows its guide.

## Authoring Mode Selection

Match existing mode; new or ambiguous work defaults to XAML. Switch to coded only on explicit user phrasing or a coded-specific trigger from the table below.

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
| Project edited in Studio Web, a process a Flow solution starts included | **XAML**, VB expressions | Studio Web opens no project holding coded workflows or C# expressions (Common Rule 2a) |
| User explicitly requests coded/XAML | **User's choice** | Never second-guess explicit preference |

### UI Automation Boundaries

For opening apps/browsers, clicking, typing, scraping visible UI, submitting forms, or verifying UI state, use UiPath UIA only: XAML `NApplicationCard` plus UIA activities; coded `uiAutomation.Open`/`Attach` plus Object Repository descriptors; or, where the package's coded authoring guide § Selector-Only Targets allows it, CLI-captured selectors via `TargetAppModel` / `Target.FromSelector` (coded). Do not substitute `InvokeCode`, PowerShell, Selenium, Playwright, CDP, raw DOM JavaScript, HTTP form posts, or external browser drivers. Coded fallback is only for non-UI helpers. If target configuration is unavailable, use the documented UIA indication path, never an external shortcut.

Read `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Mandatory: Generate Targets Before Writing Any UI Code — read it in full per Rule 7 before any UIA work; it owns the prohibited-tool list, UIA-only exploration, and `InvokeJS`/`InjectJsScript` exception scope.

### Placeholder-Selector Stub Pattern (when live app access is unavailable)

Without live app access, emit real UIA activities with placeholder selector strings and `TODO Indicate` markers, never `Log` stubs: use real `NTypeInto`, `NClick`, `NGetText`, `NApplicationCard`, etc.; put `TODO Indicate` in XAML `DisplayName` or adjacent coded `// TODO[Indicate]`. Applies to XAML and coded; read [uia-starter-guide.md § Placeholder-Selector Stub Pattern](references/uia-starter-guide.md). It needs no UIA package or CLI. Do not create workflows whose UI steps merely log intentions. Hybrid orchestration is `Main.xaml` → `InvokeWorkflowFile` → coded helper; see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for the full flowchart, InvokeCode extraction rules, and patterns.

## Capture-First Fast Path

For dialog/form automation or UI tests from manual steps, defer authoring prerequisites until capture:

1. Per Rule 7, read [uia-starter-guide.md](references/uia-starter-guide.md), the UIA package core guide, and its mandated target-capture orchestration reference, all in full.
2. Coded only: install every needed activity package and write an empty `[Workflow] public void Execute() { }` class (namespace per Rule 17) before the first `uip rpa` call, including window baseline. The first host load snapshots `.local/.codedworkflows/`; without packages/stub authoring can hit `CS0246 'CodedWorkflow'`. `uip rpa project close --project-dir "<PROJECT_DIR>"` clears it. Later `validate` refreshes only `ObjectRepository.cs`; `CodedWorkflow.cs` service accessors and `workflows.X` cross-calls remain first-load snapshots, so a later package install or new cross-called workflow needs a regen; see [coded/operations-guide.md § Configure UI Targets](references/coded/operations-guide.md#configure-ui-targets-object-repository).
3. Run the package guide’s Window Baseline: list top-level windows once and decide whether to launch.
4. Inventory manual steps from Test Manager, PDD, script, or a `uipath-task-recording` handoff. Map each “Click/Enter/Select/Verify” to one OR element, group by screen (package guide § Capturing from Manual Test Steps), and decide every element and screen name now — apply them verbatim during capture.
5. Capture screen by screen with `uia-configure-target` and screen advancement (package guide § Multi-Step UI Flows); author only at screen boundaries, never between calls within a screen. A handoff step's `recorded selector` names the element the user clicked: when choosing that element's ref, keep the candidate its last tag matches, mapping that tag onto each candidate's ancestor chain with the selector-intelligence tools (the CLI reference the guide's § Documentation routes to, § Get Ancestors); the tags above it can carry stale titles. If none matches, choose as usual. It only confirms the ref; `uia-configure-target` still resolves the stored target.
6. Integrate already-dispatched context discovery (at-most-once, never a second spawn), read the mode authoring guide in full, author, and validate. Coded: validate once to regenerate `ObjectRepository.cs`, read it, and reference every target as `Descriptors.<App>.<Screen>.<Element>`; use member names from that file, never capture OR names, and never author against string target names while it is absent.

Skip this path when the task has no UI surface (data transforms, IS connector calls, headless file/email automation). Also skip it when the task HAS a UI surface but no live app to capture against (app not installed, no GUI, capture deferred to a developer) — use the § Placeholder-Selector Stub Pattern instead. Window Baseline does not prove an app/GUI exists; verify separately or ask.

## Session Pre-warm

When more than one heavy `uip rpa` call is expected, background at session start:

```bash
uip rpa activities find --query log --output json > /dev/null 2>&1 &
```

The first heavy call costs about 22s, shared by `validate`/`build`/`run`/`activities get-default-xaml`/`analyzer-rules list`; skip for zero/one heavy call. In Windows PowerShell use `Start-Process powershell.exe -ArgumentList ...` (not `pwsh`) because `&` does not background; never `Start-Process -FilePath "uip"` or any `.ps1` (Notepad opens it).

## Critical Rules

Common Rules are 1–12. Coded rules 13–19 are in [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md). XAML rules are independent 16–24/25: 16–21a and 24–25 in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md), with 22–23 below. `[Coded]`/`[XAML]` disambiguates repeated numbers; Cross-references (“Common Rule 10”, “Rule 21”, “Rule 24”) always point to a uniquely-numbered rule.

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Check explicit path, project name, then CWD for `project.json`; create only when no match exists and the user explicitly requests creation.
<!--skill-flavor:rules-project-creation:start-->
2. **ALWAYS use `uip rpa init`**; never manually write `project.json` or scaffolding. Before init, if the user names a template ("REFramework", "based on the X template") or an industry/domain pattern (SAP, ERP, banking, mainframe), run `uip rpa templates search --query "<term>" --output json` and follow [environment-setup.md § Template selection](references/environment-setup.md): never silently choose Marketplace; present candidates and ask; if Official and Marketplace both match, ask.
2a. **Pass `--target-framework` AND `--expression-language` explicitly on every `uip rpa init` — never omit them.** Both are immutable after creation (Rule 23); omitting `--target-framework` silently yields a **Windows** project. Choose `Portable` for cross-platform/non-Windows runtime (Linux, container, serverless) or Studio Web; choose `Windows` for Windows runtime using Windows-only capabilities (Excel COM, classic Office, WPF / `PresentationFramework`, Windows-only UIA) or Studio Desktop (`Windows` is not editable in Studio Web). Studio Web accepts Portable only when every workflow is XAML with VB expressions; errors are `20042 Project has coded workflows` and `20021 ... unsupported programming language: CSharp`, and the project then opens only in Studio Desktop. A request requiring both cross-platform runtime and Windows-only capability is contradictory—surface it. **Windows - Legacy is a last resort** (explicit ask or hard .NET 4.6.1 need; never inferred from VB.NET or non-"X" classic activities) — create it in Legacy mode, not modern `init`. No signal → `AskUserQuestion` about Windows versus Cross-platform, framed around runtime host. `--expression-language` defaults to `VisualBasic`; use `CSharp` only explicitly. `init` writes installed Studio `dotNetVersion`; unsupported robot versions fault before activities with `Error converting value "<VERSION>" to type 'UiPath.Shared.DotNetVersion'`; then set `dotNetVersion` to the robot version (`net8.0` where `net10.0` is refused), rebuild, and republish.
<!--skill-flavor:rules-project-creation:end-->
<!--skill-flavor:rules-validation-gate:start-->
3. **Phase-gated validation.** After every create/edit, run `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors, fixing one thing per iteration; after every touched file is clean, run `uip rpa build "<PROJECT_DIR>" --output json` until clean. `validate` catches structural XAML, references, and schema; `build` covers all project workflows, analyzer rules, and packaging. The split is [cli-reference.md § What each phase covers](references/cli-reference.md#what-each-phase-covers). If `build` errors, take each error's file from the build's detailed log and re-run `validate --file-path` on it for a compile error. Limit each file validation loop and separate build loop to 5 attempts. A smoke test does not replace build; prefer `run --skip-build` after a passing build ([cli-reference.md § Smoke Test](references/cli-reference.md#smoke-test)). Do not run `uip rpa analyzer-rules list` as an authoring prerequisite; use it only on request or after repeated rule-family violations (the unscoped call can take a minute or more; [cli-reference.md § analyzer-rules list](references/cli-reference.md#analyzer-rules-list)). Warnings do not gate delivery: with 0 errors from validate/build, deliver; investigate warnings only on request or acceptance impact. Report warning counts by rule ID; do not spend gate attempts on them. Expected UIA warnings (verification-feature, Automation Hub URL, duplicate display name) are at [cli-reference.md § Expected non-defect warnings](references/cli-reference.md#expected-non-defect-warnings). Read errors in full. See [cli-reference.md § Validation Iteration Loop](references/cli-reference.md#validation-iteration-loop).
4. **Always validate every touched file and verify project build before declaring done.** Clean validate alone is insufficient; for observable-output workflows, finish with one `run` and check outputs ([execution-maps-guide.md § Gate ≠ runtime proof](references/execution-maps-guide.md#gate--runtime-proof)).
<!--skill-flavor:rules-validation-gate:end-->
4a. Use file tools: `Write` each `.xaml`/`.cs` completely and `Edit` later; never generate workflow files with scripts/templates: validation and fixes stay per file, and Object Repository links survive `Edit` but not regeneration. For similar files, parallel `Write`s, a helper workflow, or copy a validated file and `Edit` differences.
4b. Write only invokable units: extract reused or independently readable groups; keep one activity or short assignments inline. Do not wrap one activity merely to pass arguments. A scope the activity needs (an Application Card, an attach) is no reason to extract it: open the scope at the step, around the steps that act on that window in a row.
5. Prefer UiPath built-in activities for Orchestrator integration, UIA, and documents; use plain .NET/third-party packages for pure transforms, HTTP, and parsing.
6. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
6a. Before serialization, remove only dependencies listed unused by `uip rpa cleanup --dry-run` ([cli-reference.md § packages install](references/cli-reference.md#packages-install)); packages may be sole suppliers, e.g. `MergePDFs` in IntelligentOCR.StudioWeb. Before writing an activity tag, run `uip rpa activities find --query "<verb>" --output json`, use returned `ClassName`, and never derive tags from display names ([common-pitfalls.md § Common Activity Name Confusions](references/xaml/common-pitfalls.md)).
7. **[UIA] Before any UIA activity** (`<uix:N*>`, `uiAutomation.*`, or `Descriptors.*`), MUST read [references/uia-starter-guide.md](references/uia-starter-guide.md) via two steps, never plain full Read: Grep `^## Conditional Policies`, then Read with `limit` at that line; conditional policy sections load only when applicable. Then read the package core guide in full and, before authoring, the mode authoring guide in full as routed by its § Documentation. No exceptions for "simple" UIs. Never hand-write selectors; use `uia-configure-target` exclusively; selector-only coded work skips only OR registration, not capture. The migration exception is [uia-starter-guide.md § Placeholder-Selector Stub Pattern](references/uia-starter-guide.md). Verify prerequisites first (Rule 7a); missing package guide means below minimum. The starter guide owns run/debug, runtime selector recovery, stub deliverables, and UI Library publishing.
7a. **[UIA] Verify prerequisites before `uia-configure-target`.** Follow [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md), including consent; if package is below minimum or core guide absent, `uip rpa uia` is unavailable and capture/indication depend on it. Ask for installation/upgrade; if declined/impossible, use real placeholder activities with `TODO Indicate`, not another path. Indication-only is allowed only when a compatible package exists but capture cannot see the element; record `UI capture: indication-only` in the plan header. Persistent scan failures require ruling out locked/noninteractive Windows (`LogonUI` means unlock first); only after failure on an unlocked interactive session use placeholders.
8. Use `--output json` whenever CLI output is parsed programmatically.
8a. A `run`/`debug start` verdict comes from `Data` — NEVER from the outer `Result` alone, and NEVER from a log line's level. Identify backend by keys. Headless Helm: `Data` = `{output, hasErrors, errorMessage, profiling, debugState, debugDetails}`; pass only with `hasErrors` false, `errorMessage` null, and `debugState` null or `"Completed"`. Faulted `run` has outer `Result: "Failure"` with JSON fields in `Message`; faulted `debug start` returns `Result: "Success"`, `debugState: "Suspended"`, and exception in `debugDetails`; cancel or continue the live session. Studio Desktop: `Data` = `{output, errors, logEntries, debugState}`; pass only when `errors` is empty and `output` is `"Session ended"`. Missing entry point can return `Result: "Success"`, empty errors, and `output: "Failed to open the file <path>"`; require both conditions. Reading `Result: "Success"` as a verdict reports broken workflows as green on both backends. Successful workflows may emit Error/Warning log messages; they are workflow data, not failures. Read the printed envelope: no `--output-filter` on `run`/`debug start` (a filter naming a key the current backend lacks fails the call after the workflow has already run), and never `| tail`/`| head`; Helm logs precede the envelope and Desktop has long `logEntries`. See [cli-reference.md § Capturing the verdict](references/cli-reference.md#capturing-the-verdict), [cli-reference.md § Reading run / debug results](references/cli-reference.md#reading-run--debug-results), and [debugging.md § Output Format](references/debugging.md#output-format).
9. For leverage/reuse/shared libraries, search tenant feed — not the local filesystem, NuGet.org, or keyword-permutation loops: `uip or libraries list --limit 500 --output-filter "<JMESPath>" --output json`. On zero filtered results use its fallback branch, never re-keyword. Skip if an SDD records §16 “Shared libraries referenced” or the user earlier said no shared libraries. Follow [tenant-library-search-guide.md](references/tenant-library-search-guide.md).
10. Register every test case in `project.json` → `designOptions.fileInfoCollection`, for both XAML/coded. Required keys, GUID format, schema, `dataVariationFilePath`, and coded `publishAsTestCase` are in [references/testing-guide.md § project.json Registration](references/testing-guide.md) and [assets/json-template.md](assets/json-template.md).
11. Test cases use Given-When-Then; see [references/testing-guide.md § XAML Test Case Structure](references/testing-guide.md), whose lead routes the coded variant to `coded/operations-guide.md`.
12. Identify triggers with `uip rpa activities find --query "<event>" --output json`, reading `isTrigger` and `triggerType`. Integration (`true`, `"integration"`) must be first in `Main.xaml` root `Sequence`, never in `ui:TriggerScope`; bind `Result` to workflow-scope variable and use the rest as handler. `ConnectionId` is required for IS packages (Mail/GSuite/O365/Salesforce/Jira/Slack/ServiceNow/any `*.IntegrationService.Activities`), not Orchestrator-native `TimeTrigger`, `QueueTrigger`, `ManualTrigger`. Local (`true`, `"local"`) may be root-first for a fresh job or in `<ui:TriggerScope.Triggers>` with handler in `<ui:TriggerScope.Action>` for an in-process robot; both placements are valid — choose by runtime model; no connection asset. Unknown types (for example future `"scheduled"`) require bundled docs and user question. Do not assume placement. Existing TriggerScope content must be local; an integration trigger there is broken — flag to the user. Root content may be either, so inspect `triggerType`. See [trigger-pattern-guide.md](references/trigger-pattern-guide.md) for worked examples, the `SchedulingMode` reference, the catalog of trigger activities, and the procedure for editing existing `ui:TriggerScope` workflows.

### Destination Preflight (Both Modes)

<!--skill-flavor:studio-web-destination:start-->
**Studio Web means a Solution deliverable, not a bare project.** Studio Web ingests Solutions only; a bare project folder is invisible in both SW workspace tabs. Signals: “Studio Web”, “SW”, “upload to web”, “browser editor”, “cloud workspace edit”. Build normally, then hand off to `uipath-solution`: `uip solution init <NAME>` → `uip solution projects import "<PROJECT_DIR>" --solutionFile <SOLUTION>.uipx` → `uip solution upload "<SOLUTION_DIR>"`. Deliver the Solution. Bare projects remain valid for local `uip rpa run` and Orchestrator `uip rpa pack` → `uip rpa publish`.
<!--skill-flavor:studio-web-destination:end-->

### Execution Discipline (Both Modes)

Run to completion; do not declare work done while plan tasks remain. If `docs/plans/*.md` is referenced or discoverable, read its header before work and every checkpoint. `Execution autonomy: autonomous` means continue until every checkbox is `[x]` or a concrete plan Stop condition occurs. `interactive` or no plan means use judgment and confirm material decisions. Before reporting, re-read and enumerate unchecked boxes; continue unless a Stop condition occurred. Cost, call count, pauses, partial usability, and complexity are not Stop conditions. Plan decisions already made are authoritative. Do not `AskUserQuestion` about structure, file count, selector strategy, or capture approach when the plan specifies them.

### Error Handling (Both Modes)

Wrap each external interaction whose failures need different handling in Try/Catch; classify bad input as `BusinessRuleException` (no retry, human needed) and transient faults as system exceptions (retry then escalate). Catch where handling differs, not around every activity; UI activities already wait and fail “element not found”, so do not guard them with Check App State (UIA package guide, *Unnecessary Check App State*). Do not blanket-wrap pure logic or leave Catch empty. `Rethrow`, never `Throw New Exception(ex.Message)`, to preserve the stack trace. Before resilience work, read [references/error-handling-guide.md](references/error-handling-guide.md) in full for exception taxonomy, Retry Scope count/interval, ContinueOnError, screenshots, Global Exception Handler scaffold/registration/verdict, state recovery, transaction boundaries, idempotent/compensating writes avoiding duplicate creates/partial writes, redaction, and retry ownership across queue/Retry-Scope/GEH/job layers.

### Execution Maps (Both Modes)

Follow [execution-maps-guide.md](references/execution-maps-guide.md) for every build/edit: it fixes batching into assistant turns (greenfield ≤5, brownfield ≤5; pitfalls vet turn included). Within a turn, chain dependent `uip` calls with `&&` in one `Bash`; parallelize independent `Bash`/`Read`/`Edit`; split only when stdout or a mutation is required. Rule 21 off-card discovery fans out: all K `find`s parallel, then all K doc Reads, then all K `get-default-xaml`s — never one activity at a time. Never batch across `templates search` → `init`, consent/`AskUserQuestion`, or UIA state advances/indication; the UIA guide’s per-screen gates control those.

### Coded-Specific Rules

13–19. **[Coded]** Before any coded workflow, test case, or source file, read [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md) in full. The same file also carries § Coded Quick Reference (file types, service-to-package mapping, templates) and § Task Navigation — Coded.

### XAML-Specific Rules

16–21a, 24–25. **[XAML] The XAML critical rules live in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md)** — Rule 22's read-in-full mandate below covers them; they arrive with the file you must already read before any XAML work. The same file carries the XAML task navigation and quick reference.
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) in full before generating or editing any XAML — a plain full Read, emitted in the journey's first turn alongside the card reads (no lookup precedes it; the file holds only the mandatory content).** The per-operation / per-activity catalogs (editing operations, reference examples) live in [references/xaml/xaml-editing-catalog.md](references/xaml/xaml-editing-catalog.md) and load per entry only — Grep `^###`, Read the entries matching the operation/activity at hand, unsure → read it. **Then vet the plan against [references/xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) before the first `Write`/`Edit`.** common-pitfalls.md is a catalog of independent gotcha sections — do NOT read it end-to-end: list its headings (Grep `^##` on the file — emit this in the first turn too, it needs no prior output), then in the next turn Read every section whose heading matches an activity, property, or feature in the workflow you are about to author. Unsure whether a section applies → read it. This is an authoring-time gate, not only a troubleshooting resource — consulting it first is cheaper than debugging a gotcha `validate` cannot see. The turn placement is fixed by [execution-maps-guide.md](references/execution-maps-guide.md): the heading list rides in T1, the section Reads are T2, so the gate costs one turn, never a grep→Read pair per file.
23. **[XAML]** Never change existing `expressionLanguage` or `targetFramework`. They are immutable from Common Rule 2a and project-wide. Do not convert in place; confirm and follow [environment-setup.md § Project Conversion](references/environment-setup.md): copy aside, fresh `init`, recreate all workflows, delete the copy only after user agreement.

## Task Navigation

| I need to... | Mode | Read these |
|---|---|---|
| Work in Legacy | Legacy | [legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) — entry point. Modern-mode rules below do not apply. |
| Plan build turns | Both | [execution-maps-guide.md](references/execution-maps-guide.md) — read first for any build/edit journey |
| Choose coded/XAML or hybrid | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [environment-setup.md § Designing Project Structure](references/environment-setup.md#designing-project-structure) |
| Create a project | Both | [environment-setup.md § Step 0.3](references/environment-setup.md#step-03-creating-a-new-project) |
| Any XAML authoring/editing task (workflows, test cases, Flowchart/StateMachine/LRW, common activities, Data Fabric, IS connectors, triggers, XAML troubleshooting) | XAML | [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — Rule 22 read; § Critical Rules — XAML + § Task Navigation — XAML route the rest |
| Any coded authoring/editing task (workflows, test cases, source files, IS connectors, NuGet, API discovery, coded troubleshooting) | Coded | [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md) — § Critical Rules — Coded + § Task Navigation — Coded route the rest |
| Data-driven testing | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md) plus Rule 10 |
| Test Manager setup | Both | [cli-reference.md § Test Manager](references/cli-reference.md) — `uip rpa tm connect` / `set-default-project` |
| Error handling/resilience (Try/Catch, Retry Scope, BusinessRuleException, ContinueOnError, screenshot-on-error, Global Exception Handler, recover app state, transaction boundary, idempotency / avoid duplicate creates, queue vs local retry ownership) | Both | [error-handling-guide.md](references/error-handling-guide.md) |
| UI automation | Both | UIA package guide `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` |
| Share OR selectors/UI Library | Both | [uia-starter-guide.md § Object Repository as a Published UI Library](references/uia-starter-guide.md) |
| Run/debug UIA | Both | [uia-starter-guide.md § Running UI Automation Workflows](references/uia-starter-guide.md) |
| Drive captured controls | Both | UIA package guide § Control-Specific Interaction Patterns |
| Excel/Word/Mail/etc. | Both | `.local/docs/packages/{PackageId}/`, fallback `references/activity-docs/{PackageId}/{closest}/` |
| Manipulate data (DataTable/LINQ, strings, RegEx, DateTime, collections, JSON) | Both | [data-manipulation-guide.md](references/data-manipulation-guide.md) |
| Inspect IS trigger lifecycle | Both | [trigger-pattern-guide.md § Connection Handling](references/trigger-pattern-guide.md) and [§ Server-Side Filtering](references/trigger-pattern-guide.md) |
| Build/run/validate | Both | [cli-reference.md](references/cli-reference.md) — per-command catalog, do NOT read end-to-end: Grep `^## `, read each command section used and § Reading run / debug results |
| Profile a slow workflow / verify UI automation correctness | Both | [debugging.md § Profiling Workflow Performance](references/debugging.md#profiling-workflow-performance) |
| Design/debug/run on a remote machine (Orchestrator unattended robot — Live Authoring vs Remote Run Only, `remote configure`/`status`/`start`/`stop`, `--remote` debug/run, file transfer, remote shell commands) | Both | [remote-session-guide.md](references/remote-session-guide.md) |
| Pack/publish | Both | [cli-reference.md § Pack & Publish to Orchestrator](references/cli-reference.md#pack--publish-to-orchestrator) |
| Analyzer rules | Both | [cli-reference.md § analyzer-rules list](references/cli-reference.md) |
| Find tenant libraries | Both | [tenant-library-search-guide.md](references/tenant-library-search-guide.md) |
| Author/publish library | Both | [library-authoring-guide.md](references/library-authoring-guide.md) |
| Invoke PowerShell | Both | [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| Data Fabric entities | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md) |
| Project structure | Both | [environment-setup.md § Project Structure Reference](references/environment-setup.md#project-structure-reference) |

## Mode Packs

XAML rules, quick reference, navigation, authoring, anatomy, and per-entry editing catalog: [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) and [xaml/xaml-editing-catalog.md](references/xaml/xaml-editing-catalog.md). Coded rules, quick reference, file types, service/package mapping, templates, navigation, and base classes: [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md).

## Resolving Packages & Activity Docs

### Step 1 — Ensure the package is installed

Check `project.json` dependencies. Always query with `--include-prerelease`; previews may contain required activities, signatures, and docs. If installed, note its version and query available versions. If a newer stable/preview exists, inform the user: state the installed version, the latest available version, and that newer packages offer the best support for activity generation; ask whether to upgrade; never force-upgrade. If already latest, proceed to Step 2. If absent, install the latest returned version (preview allowed):

```bash
uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages 'id=<PackageId>,version=<LATEST_VERSION>' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find activity docs

First directly Read `{PROJECT_DIR}/.local/docs/packages/{PackageId}/activities/<Activity>.md`; failed direct Read is the existence check. `Glob`/`Grep` skip gitignored `.local/` and prove nothing; use `ls` on the exact directory to list it. Never enumerate the tree. If absent, use the closest installed-version folder under `references/activity-docs/{PackageId}/`.

## UI Automation References

Skill references own prerequisites/version gating, run/debug orchestration, placeholder deliverables, and UI Library publishing. The installed UIA pack at `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/` owns authoring, capture, CLI syntax, activity properties, coded API, runtime recovery, and its bundled `uia-configure-target`; it is co-versioned and wins on divergence.

Read [uia-starter-guide.md](references/uia-starter-guide.md) first for UIA. The pack’s `ui-automation-guide.md` is the full entry point and routes target capture, task guides, CLI inventory, activity properties, coded API, recovery, and bundled skill; verify it by exact-path `ls` or direct Read, never `Glob`/`Grep`.

## Completion Output

Before “done”, verify plan completion: re-read `docs/plans/*.md`; if autonomous and unchecked boxes remain without a Stop condition, resume; if a Stop condition stopped work, name it; if interactive, report status. Save only memory patterns qualified by [execution-maps-guide.md § Cross-session memory](references/execution-maps-guide.md#cross-session-memory); a first-try clean gate on card-covered activities qualifies none. If persistent memory exists, write qualifying memory, context files, and report in parallel in the final turn; nothing runs afterward.

When finished, report:
<!--skill-flavor:report-what-was-done:start-->
1. **What was done** — created, edited, and deleted file paths.
<!--skill-flavor:report-what-was-done:end-->
<!--skill-flavor:report-validation-status:start-->
2. **Validation status** — every touched file’s per-file `validate` and project-level `uip rpa build`. Both must be clean to claim verification; if build has not run since the last edit, say so.
<!--skill-flavor:report-validation-status:end-->
3. **Plan completion** — checked `[x]` tasks and every remaining `[ ]`, with its Stop-condition item or “not reached”.
<!--skill-flavor:report-how-to-run:start-->
4. **How to run** — applicable `uip rpa run` or `uip rpa debug start` command.
<!--skill-flavor:report-how-to-run:end-->
5. **Next steps** — connections, OR elements, placeholders, and other follow-up actions.
6. **Trouble?** — if issues occurred, say: “If something didn't work as expected, use `/uipath-feedback` to send a report.”

Do not say “complete”, “done”, “finished”, or “the automation is built” unless all plan tasks are checked; otherwise say “Partial”, “stopped at <task N>”, or “blocked by <stop condition>”.
