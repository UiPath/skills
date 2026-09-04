---
name: uipath-rpa
description: "Always invoke for `.xaml` or `.cs` workflow files. UiPath RPA — create, edit, build, run, debug `.cs` coded workflows and `.xaml` workflows. UI automation with Object Repository selectors, test case authoring, Integration Service connector calls. Live desktop/browser UI exploration and control. Deploy via `.uipx`→uipath-solution. Non-solution Orchestrator ops→uipath-platform. Test reports→uipath-test. Agents→uipath-agents."
when_to_use: "User wants to create, edit, debug, or run a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents)."
---

# UiPath RPA Assistant

Full assistant for creating, editing, managing, and running UiPath automation projects — both coded workflows (C#) and low-code RPA workflows (XAML). One UIA activity set covers every UI target: Windows and macOS, desktop and web, in a single automation — targets configured with strict or fuzzy selectors (reinforced by anchors), Computer Vision, or semantic matching; `uia-configure-target` picks the route and falls back automatically.

> **Reading the referenced files is imperative — read each required file in full.** This SKILL.md is a router: it tells you *which* reference to open, not *what* it says. When a rule, the Task Navigation table, or a section points you to a reference for the task at hand, open it and read the **whole** file before acting — do not grep it for a keyword, skim the first screen, fall back to `--help`, or substitute prior knowledge. Exception: files whose rule prescribes a **targeted lookup** (Grep `^##` for the table of contents, flags via `<command> --help`) — these are catalogs: read the matching sections, never the whole file. Most errors that slip past `validate` and surface at `build` or runtime trace back to a reference that was skipped or only partially read.

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

## UIA Prerequisites

`UiPath.UIAutomation.Activities` at or above the skill's minimum version is required for all UIA work — the minimum version, the version check, the discovery/install commands, and the **upgrade-consent matrix (NEVER install or upgrade UIA silently)** live in [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md) — the only source of truth; do not hardcode the version from memory.

## Precondition: Project Context

Before doing any work, check `.claude/rules/project-context.md` in the project directory:

- **Exists and fresh** → proceed with the skill workflow.
- **Missing or stale** → run the skip gate, then — only if it does not trip — the discovery flow, both per [environment-setup.md § Project Context Discovery](references/environment-setup.md): the staleness check (metadata-comment counts vs current counts, 60–70% threshold), the skip gate (greenfield / empty project / untouched scaffold — nothing to discover yet), the discovery-agent spawn options per host, and the handling of the agent's `context-files:` / `SKIP:` status lines (the agent writes the context files itself — do NOT re-read or rewrite them). **Dispatch discovery AT MOST ONCE per session** — if a discovery agent is already running or its context document was already produced, reuse that result; a later step that calls for "project-context discovery" means INTEGRATE the earlier dispatch, never spawn a second.
- **Skip gate tripped (greenfield / empty / untouched scaffold)** → no discovery agent and no context files now; after the build completes, write both context files yourself per the same section.

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
4. **New project** — Neither exists → **default to XAML.** Switch to coded only when the user explicitly says "coded", ".cs", "C# workflow", "coded test case", or names a coded-specific trigger (custom data models / DTOs, unit-testable business logic). For all other phrasings ("create a workflow", "automate X", "build an automation"), use XAML. See [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) for the full decision flowchart.

**Routing:** Once mode is determined, use the Task Navigation table below to find the right reference files. For guidance on **choosing** between coded and XAML approaches, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md). For Legacy projects, follow [references/legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) instead.

## Authoring Mode Selection

**Default to matching the project's existing mode.** For new projects or ambiguous cases, **default to XAML** — it is the more common mode, has the widest activity coverage, and is the unmarked term in user vocabulary ("create a workflow" means XAML; "create a coded workflow" means coded). Switch to coded only on explicit user phrasing or a coded-specific trigger from the table below.

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

For any task whose business behavior is "open an app/browser, click, type, scrape visible UI, submit a form, or verify UI state", the interaction layer MUST be UiPath UI Automation — `NApplicationCard` plus UIA activities (XAML), or `uiAutomation.Open`/`Attach` plus Object Repository descriptors (coded). Do NOT substitute `InvokeCode`, PowerShell, Selenium, Playwright, Chrome DevTools Protocol, raw DOM JavaScript, HTTP form posts, or external browser-driver scripts. The coded fallback rows above apply only to non-UI helper logic (data transforms, parsing, DTOs, calculations, API-only integrations).

If target configuration is unavailable, fall back to the documented UIA indication path — never to an external browser automation shortcut.

The full prohibited-tool list, the UIA-only exploration requirement, and the `InvokeJS`/`InjectJsScript` exception scope are in the UIA package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) § Mandatory: Generate Targets Before Writing Any UI Code — read it in full per Rule 7 before any UIA work.

### Placeholder-Selector Stub Pattern (when live app access is unavailable)

When generating a UI automation workflow **without** live app access (target capture cannot be run because the app is not installed, the agent has no UI, or the user explicitly deferred capture to a developer), emit **real UIA activities with placeholder selectors and `TODO Indicate` markers** — never `Log` stubs.

**Forbidden:** a workflow whose UI-interaction steps are `Log("LoginWorkflow: type username")` with a `// TODO[selectors]:` comment. The workflow passes build/validate and runs cleanly, but does nothing. This is the most expensive kind of stub — it looks complete, the validator says it's fine, and the failure mode is silent.

**Required:** the **real** UIA activity (`NTypeInto`, `NClick`, `NGetText`, `NApplicationCard`, etc.) with the target descriptor's selector left as a placeholder string and a `TODO Indicate` marker embedded in the activity's `DisplayName` (XAML) or in a `// TODO[Indicate]` comment immediately adjacent to the coded call. A developer opens Studio, clicks **Indicate** on each marked activity, and the workflow runs.

This applies to **both** XAML and coded modes. The full pattern with XAML and coded examples is in [uia-starter-guide.md § Placeholder-Selector Stub Pattern](references/uia-starter-guide.md) — read it before authoring stub-mode workflows. It requires no UIA package or CLI.

**Hybrid pattern** — XAML orchestration + coded fallback for logic with no matching activity:

    Main.xaml                  ← orchestration (XAML)
      └── InvokeWorkflowFile → ProcessData.cs  ← coded logic

For the full decision flowchart, InvokeCode extraction rules, and detailed hybrid patterns, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Capture-First Fast Path

When the request is "automate this dialog/form" or "build a UI test from these manual steps" — i.e. the bulk of the work is target capture, not coding — **defer authoring-phase prerequisites until target capture is complete**. The capture surface is interactive, app-state-sensitive, and time-bound; project-context discovery adds nothing during capture and steals time from it.

**Fast-path order for capture-first tasks:**

1. **Read per Rule 7** — [uia-starter-guide.md](references/uia-starter-guide.md) and the UIA package's core guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`), both IN FULL, plus the target-capture orchestration reference the core guide mandates.
2. **Pre-flight Window Baseline** — list top-level windows once; decide whether to launch the app (package guide § Window Baseline).
2a. **[Coded mode only] Write the workflow stub before capture** — an empty `[Workflow] public void Execute() { }` class. Studio generates `ObjectRepository.cs` descriptors only when a coded file is already on disk at the moment the Object Repository is written, so the stub makes the capture flow's own registration the trigger and you read real member names before writing the body. Preconditions and recovery: the coded authoring guide's § Step 1.
3. **Inventory targets from manual steps** (Test Manager test case, PDD, or written script). Each "Click X" / "Enter Y" / "Select Z" / "Verify W" step maps to one OR element. Group by screen state (package guide § Capturing from Manual Test Steps), and decide every element and screen name now — apply them verbatim during capture.
4. **Capture all targets** screen by screen via `uia-configure-target` and screen advancement (package guide § Multi-Step UI Flows). Authoring only at screen boundaries — never between capture calls within a screen.
5. **Then enter authoring phase:** integrate project-context discovery (already dispatched if the precondition required it — at-most-once, never a second spawn), read your mode's authoring guide (Rule 7), write code, validate.

Skip this path when the task has no UI surface (data transforms, IS connector calls, headless file/email automation). Also skip it when the task HAS a UI surface but **no live app to capture against** (app not installed, no GUI, capture deferred to a developer) — there is nothing to capture, so use the § Placeholder-Selector Stub Pattern above instead. The Window Baseline does not tell you if the app is installed and has a GUI — validate that separately (e.g. look for the executable on disk) or ask the user.

## Session Pre-warm

First heavy `uip rpa` call pays a ~22s Studio host cold-start (shared across `validate`/`build`/`run`/`activities get-default-xaml`/`analyzer-rules list`). When more than one is expected this session, background a cheap warm-up at session start so the tax hides behind planning:

```bash
uip rpa activities find --query log --output json > /dev/null 2>&1 &
```

On Windows PowerShell, `&` doesn't background — use `Start-Process powershell.exe -ArgumentList ...` (not `pwsh`). Never `Start-Process -FilePath "uip"` (or any `.ps1`): Windows opens it in Notepad, not PowerShell.

**Skip** when 0 or 1 heavy `uip rpa` calls are expected (read-only Q&A, single-file inspection) — the warm-up doesn't reclaim its cost.

## Critical Rules

**Rule numbering.** Common Rules use 1–12 (below). Coded-specific rules 13–19 live in [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md); XAML-specific rules are an independent 16–24 sequence — 16–21a and 24 live in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md), 22 and 23 below. Numbers 16/17/18/19 appear in both mode sequences — the `[Coded]` / `[XAML]` prefix disambiguates. Cross-references ("Common Rule 10", "Rule 21", "Rule 24") always point to a uniquely-numbered rule.

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Follow Step 0 resolution: check explicit path, project name, then CWD for `project.json`. Only create when confirmed no project matches AND user explicitly requests creation.
2. **ALWAYS use `uip rpa init`** to create new projects — never write `project.json` or scaffolding manually.
   - **Before creating, decide if a template is needed.** If the user names a template ("REFramework", "based on the X template") or an industry/domain pattern (SAP, ERP, banking, mainframe), run `uip rpa templates search --query "<term>" --output json` first and select per the decision flow in [environment-setup.md § Template selection](references/environment-setup.md) — its two hard constraints: **NEVER silently pick a Marketplace template** (present candidates and ask), and when the user's named template matches both an Official and a Marketplace item, ask — do NOT auto-pick.
2a. **Pass `--target-framework` AND `--expression-language` explicitly on every `uip rpa init` — never omit them.** Both are immutable after creation (Rule 23); omitting `--target-framework` silently yields a **Windows** project. Choose framework by where the automation runs: cross-platform / non-Windows runtime (Linux, container, serverless) or Studio Web editing → **`Portable`** (Cross-platform); Windows runtime using Windows-only capabilities (Excel COM, classic Office, WPF / `PresentationFramework`, Windows-only UIA) or Studio Desktop as the edit surface → **`Windows`** (not editable in Studio Web). A request needing *both* a cross-platform runtime and a Windows-only capability is contradictory — surface it, don't silently pick. **Windows - Legacy is a last resort** (explicit ask or hard .NET 4.6.1 need; never inferred from VB.NET or non-"X" classic activities) — create it in Legacy mode, not modern `init`. No signal → `AskUserQuestion` (Windows vs Cross-platform), framed around the runtime host. `--expression-language`: default `VisualBasic`, `CSharp` only on explicit request.
3. **Phase-gated validation.** Two-phase validation:
   - **Per-file** (after every create or edit): `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors. Catches structural XAML, missing references, analyzer-rule violations, schema violations. Fix one thing per iteration.
   - **Project-level build** (after per-file `validate` is clean across all files in the edit session, and before declaring done): `uip rpa build "<PROJECT_DIR>" --output json` until clean. Covers the whole project — every workflow including ones you never edited or validated, plus project-scope analyzer rules and packaging — so per-file `validate` passing on each edited file does NOT establish that the project compiles. Coverage split: [cli-reference.md § What each phase covers](references/cli-reference.md#what-each-phase-covers). If `build` errors, identify the offending file from the output and re-run `validate --file-path` on it.
   - **5-attempt cap per loop** — 5 attempts for each file's per-file `validate` loop; a separate 5 attempts for the project-level `build` loop. Fix one root cause per iteration.
   - **Smoke-test shortcut:** A successful `uip rpa run` substitutes for the standalone end-of-session `build` — `run` compiles internally. Prefer `run --skip-build` when `build` has just passed; see [cli-reference.md § Smoke Test](references/cli-reference.md#smoke-test).
   - **Do NOT run `uip rpa analyzer-rules list` as an authoring prerequisite.** `validate` and `build` already enforce the enabled analyzer rules and report violations with rule IDs and recommendations — pre-fetching the rule list is speculative cost (the unscoped call can take a minute or more). It is an **on-demand** command: run it when the user asks about the project's best-practice/analyzer rules, or when repeated violations of the same rule family suggest authoring against the full rule set. See [cli-reference.md § analyzer-rules list](references/cli-reference.md#analyzer-rules-list).

   - **Warnings do not gate delivery.** Once `validate` and `build` report 0 **errors**, the gate is satisfied — deliver. Do NOT investigate or fix a warning unless the user asked about it or it blocks a stated acceptance criterion. Several warnings are correct-by-design on UIA projects and fire on every build (verification-feature, Automation Hub URL, duplicate display name): [cli-reference.md § Expected non-defect warnings](references/cli-reference.md#expected-non-defect-warnings). Report warnings in the completion output; do not spend gate attempts on them.

   See [cli-reference.md § Validation Iteration Loop](references/cli-reference.md#validation-iteration-loop).
4. **ALWAYS bring every touched file to per-file `validate` clean AND verify the project builds before declaring done.** The full cadence, caps, and what each phase catches: Rule 3. `validate` clean alone is not "validated" — the project-level `build` is mandatory before declaring done, and a clean gate is not runtime proof: for observable-output workflows, end the gate with one `run` and check outputs ([execution-maps-guide.md § Gate ≠ runtime proof](references/execution-maps-guide.md#gate--runtime-proof)).
5. **Prefer UiPath built-in activities** for Orchestrator integration, UI automation, and document handling. Prefer plain .NET / third-party packages for pure data transforms, HTTP calls, parsing.
6. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
6a. **Pre-edit verification gate.** Two authoring actions are hard to roll back once `build` fails — verify before serialization, not after.
   - **Removing a dependency** — grep the project for usages before deleting an entry. A package may be the sole supplier of an activity used elsewhere (`MergePDFs` lives in the IntelligentOCR.StudioWeb family).
   - **Writing a new activity tag** — confirm via `uip rpa activities find --query "<verb>" --output json` and use the returned `ClassName`. Do not derive tag names from Studio display names. See [common-pitfalls.md § Common Activity Name Confusions](references/xaml/common-pitfalls.md).
7. **[UIA] Before writing ANY UIA activity (XAML `<uix:N*>` or coded `uiAutomation.*` / `Descriptors.*`), MUST read [references/uia-starter-guide.md](references/uia-starter-guide.md) — via a two-step read, never a plain full Read: (1) Grep `^## Conditional Policies` on it, (2) Read with `limit` set to that line; the two policy sections below the marker load only when their stated condition applies.** Then the UIA package's core guide it mandates (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md`) IN FULL, and — before authoring — your mode's authoring guide IN FULL (routed from the core guide's § Documentation). No exceptions for "simple" UIs. Skipping this rule is the most common cause of hallucinated selectors, wrong target XML, and missing OR descriptors. NEVER hand-write selectors — use `uia-configure-target` exclusively (the package guide explains how). The package guide exists only after the package is installed — verify [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md) first (Rule 7a); if the package is installed but the guide file is absent, the installed version predates it — treat as below the minimum version. The starter guide owns the skill-side UIA policies: run/debug procedure + runtime selector recovery, the stub-mode deliverable pattern, and UI Library publishing.
7a. **[UIA] Verify UIA prerequisites before invoking `uia-configure-target`.** The minimum version and the prerequisite check live in [uia-starter-guide.md § UIA Prerequisites](references/uia-starter-guide.md) — run that check first (do not hardcode the version from memory; that section is the only source of truth). If `UiPath.UIAutomation.Activities` is below the minimum or `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` is absent (Rule 7 treats a missing guide as below-minimum), the `uip rpa uia` CLI is unavailable — and **both** target capture and indication depend on it, so indication is *not* a fallback when the package itself is missing. Ask the user to install/upgrade per that section. If they decline or the package cannot be installed, fall back to the **Placeholder-Selector Stub Pattern** (§ above) — real activities with `TODO Indicate` markers need no CLI. Never silently route to a non-existent skill path. Use indication capture only when a compatible UIA package *is* installed but `uia-configure-target` cannot see the element; record `UI capture: indication-only` in the plan header to skip `uia-configure-target` in that case. **Runtime failure counts too:** when the package is present but the UIA snapshot CLI's live scans fail persistently (driver/COM errors on every scan), first rule out a locked or non-interactive Windows session (`LogonUI` running = lock screen) — that needs an unlock, not a fallback. Only if scans still fail on an unlocked interactive session, treat capture as unavailable and use the Placeholder-Selector Stub Pattern.
8. **Use `--output json`** on all CLI commands whose output is parsed programmatically.
8a. **A `run` / `debug start` verdict comes from `Data.errors` AND `Data.output` together — NEVER from the outer `Result`, and NEVER from any log entry's `level`.** A completed run passed only when `Data.errors` is empty **and** `Data.output` is `"Session ended"`. The outer `Result` qualifies the CLI invocation, not the workflow: it stays `"Success"` through unhandled exceptions, compile failures, and a missing entry point, so reading it as a verdict reports broken workflows as green. Both `Data` conditions are required, because `errors` stays empty for a missing entry point and for a debug session suspended on an exception, which report the failure in `output` instead. A successful workflow may emit `Log Message` activities at `Error` or `Warning` level as observability — those are workflow-emitted data, not failures, and treating log-entry levels as a failure signal flips green runs to "failed" and burns retries on healthy workflows. Once a run has failed, `logEntries` at `Error` level carry the most specific root cause. **Capture the verdict with `--output-filter` on the run command; never `| tail` the raw payload — `output` and `errors` precede the hundreds of `logEntries` lines, so tailing drops exactly the two fields this rule adjudicates on.** Copy-paste filter: [cli-reference.md § Capturing the verdict](references/cli-reference.md#capturing-the-verdict). See also [cli-reference.md § Reading run / debug results](references/cli-reference.md#reading-run--debug-results) and [debugging.md § Output Format](references/debugging.md#output-format).
9. **For "leverage / reuse / find shared libraries" requests, search the tenant feed — not the local filesystem, NuGet.org, or keyword-permutation loops.** Run `uip or libraries list --limit 500 --output-filter "<JMESPath>" --output json`. On zero results from the filtered call, take the fallback branch — do not re-keyword. Skip when an SDD already records §16 "Shared libraries referenced" or the user has said "no shared libraries" earlier in the session. See [tenant-library-search-guide.md](references/tenant-library-search-guide.md) for the full procedure.
10. **Register every test case file in `project.json` → `designOptions.fileInfoCollection`.** Applies to both XAML and coded test cases. Required keys, GUID format, JSON snippet, and full schema (including `dataVariationFilePath` for data-driven and `publishAsTestCase` for coded): [references/testing-guide.md § project.json Registration](references/testing-guide.md) and [assets/json-template.md](assets/json-template.md).

11. **Test case structure: Given-When-Then.** Applies to both XAML and coded test cases. See [references/testing-guide.md § XAML Test Case Structure](references/testing-guide.md) for the canonical patterns (the section's lead also points to the coded variant in `coded/operations-guide.md`).

12. **Trigger activity placement.** Two trigger types — identify from `uip rpa activities find --query "<event>" --output json` by reading `isTrigger` and `triggerType`. Placement rules differ.

    **Integration triggers** (`isTrigger: true`, `triggerType: "integration"`) — **strict placement.** MUST be the first activity of `Main.xaml`'s root `Sequence`; CANNOT be placed inside `ui:TriggerScope`. Bind `Result` to a workflow-scope variable; the rest of the `Sequence` is the handler. **Connection asset (`ConnectionId`) required for IS-based** triggers (Mail / GSuite / O365 / Salesforce / Jira / Slack / ServiceNow / any `*.IntegrationService.Activities` package); **not required for Orchestrator-native** triggers (`TimeTrigger`, `QueueTrigger`, `ManualTrigger`).

    **Local triggers** (`isTrigger: true`, `triggerType: "local"`) — **flexible placement.** Place EITHER as the first activity of `Main.xaml`'s root `Sequence` (Orchestrator dispatches a fresh job per event) OR inside `<ui:TriggerScope.Triggers>` with handler in `<ui:TriggerScope.Action>` (robot stays alive while the scope is active; trigger fires in-process). Both placements are valid — choose by runtime model. No connection asset required.

    **Unknown `triggerType`** (forward-compat — e.g. a future `"scheduled"`) → read the bundled doc and ask the user. Do not assume placement.

    **Reading existing XAML:** activity inside `<ui:TriggerScope.Triggers>` must be a local trigger; an integration trigger there is broken — flag to the user. Activity at workflow root can be either type — check `triggerType` to disambiguate.

    See [trigger-pattern-guide.md](references/trigger-pattern-guide.md) for worked examples, the `SchedulingMode` reference, the catalog of trigger activities, and the procedure for editing existing `ui:TriggerScope` workflows.


### Destination Preflight (Both Modes)

<!--skill-flavor:studio-web-destination:start-->
**Studio Web destination → Solution-wrapped deliverable, not a bare project.** Studio Web ingests Solutions only; a bare project folder is invisible in both SW workspace tabs. Treat these phrases as SW signals in the request: "Studio Web", "SW", "upload to web", "browser editor", "cloud workspace edit". On match, build the RPA project normally per the rest of this skill, then hand off to `uipath-solution` to wrap and ship it: `uip solution init <NAME>` → `uip solution projects import "<PROJECT_DIR>" --solutionFile <SOLUTION>.uipx` → `uip solution upload "<SOLUTION_DIR>"`. The final deliverable is the Solution, not the bare project folder. Local execution (`uip rpa run`) and the Orchestrator package flow (`uip rpa pack` → `uip or packages upload` — there is no `uip rpa publish`) are fine with a bare project — only an SW destination changes the deliverable shape.
<!--skill-flavor:studio-web-destination:end-->

### Execution Discipline (Both Modes)

**Run to completion — do not declare work done while plan tasks remain.** If a plan file exists at `docs/plans/*.md` referenced by this request (or discoverable there for this feature), read its header before acting and during every checkpoint.

- If the header has `Execution autonomy: autonomous`: continue until ALL plan task checkboxes are `[x]` OR a concrete item from the plan's `Stop conditions` section is hit.
- If the header has `Execution autonomy: interactive`, or no plan file exists: use judgment and confirm with the user on material decisions.
- Before declaring the task done, re-read the plan and enumerate any unchecked boxes. If unchecked tasks remain and no Stop condition was hit, keep going — do not summarize partial work as "Done".
- "Feels expensive", "many tool calls used", "natural pause point", "partial result looks usable", and "too complex to continue in one session" are **NOT** Stop conditions. Only the concrete hard blockers in the plan's `Stop conditions` section count.
- Plan decisions already made are authoritative. Do not `AskUserQuestion` about structure, file count, selector strategy, or capture approach when the plan specifies them — those questions belonged to the planner.

### Error Handling (Both Modes)

**Wrap external interactions (UI, file, network, DB) in Try/Catch and classify failures — `BusinessRuleException` for bad input data (no retry; needs a human), system exceptions for transient faults (retry then escalate).** Don't blanket-wrap pure logic, don't leave a Catch empty, and `Rethrow` (never `Throw New Exception(ex.Message)`) to preserve the stack trace. For exception taxonomy, Retry Scope count/interval semantics, ContinueOnError suppression, screenshot-on-error, the Global Exception Handler recipe (scaffold + `project.json` registration + verdict logic), and the resilience patterns — recovering to a known app state before retrying, per-item transaction boundaries, idempotent/compensating writes to avoid **duplicate creates** and partial writes, sensitive-data redaction, and **retry ownership** across queue/Retry-Scope/GEH/job layers — read [references/error-handling-guide.md](references/error-handling-guide.md) in full before adding resilience to a workflow.

### Execution Maps (Both Modes)

**Follow the journey map in [execution-maps-guide.md](references/execution-maps-guide.md) for every build or edit** — it fixes which tool calls batch into which assistant turn (greenfield ≤5 turns, brownfield ≤4). Within a turn: chain dependent `uip` calls with `&&` in one `Bash`; emit independent `Bash`/`Read`/`Edit` calls as parallel tool uses. Split turns only where a call needs an earlier call's stdout or a file mutation. Rule 21 discovery for off-card activities fans out inside T1/T2 — all K `find`s parallel, then all K doc `Read`s, then all K `get-default-xaml`s — never one activity at a time.

**Sequential by design — never batch across:** `templates search` → `init` (Rule 2 decision gate); any `AskUserQuestion` or consent gate; UIA state advances and indication (the UIA journey in the guide encodes its per-screen gating).

### Coded-Specific Rules

13–19. **[Coded] The coded critical rules live in [coded/codedworkflow-reference.md § Critical Rules — Coded](references/coded/codedworkflow-reference.md).** Read that section before creating or editing ANY coded workflow, test case, or coded source file — the rules are mandatory constraints, not reference material. The same file carries the coded quick reference (file types, service-to-package mapping, templates) and coded task navigation.

### XAML-Specific Rules

16–21a, 24. **[XAML] The XAML critical rules live in [xaml/xaml-basics-and-rules.md § Critical Rules — XAML](references/xaml/xaml-basics-and-rules.md)** — Rule 22's read-in-full mandate below covers them; they arrive with the file you must already read before any XAML work. The same file carries the XAML task navigation and quick reference.
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) before generating or editing any XAML — via this two-step read, never a plain full Read:** (1) Grep `^## Catalogs` on the file with line numbers, (2) Read the file with `limit` set to that line. Everything above the marker (including § Critical Rules — XAML) is the mandatory read; the catalog sections below it (editing operations, reference examples) load per-entry only — Grep `^###`, Read the entries matching the operation/activity at hand, unsure → read it. **Then vet the plan against [references/xaml/common-pitfalls.md](references/xaml/common-pitfalls.md).** common-pitfalls.md is a catalog of independent gotcha sections — do NOT read it end-to-end: list its headings (Grep `^##` on the file), then Read every section whose heading matches an activity, property, or feature in the workflow you are about to author. Unsure whether a section applies → read it. This is an authoring-time gate, not only a troubleshooting resource — consulting it first is cheaper than debugging a gotcha `validate` cannot see.
23. **[XAML] NEVER change `expressionLanguage` or `targetFramework` on an existing project.** Decide both proactively at init time (Common Rule 2a); this rule covers the immutability afterward. Both fields are fixed at creation and apply to every XAML file — flipping either invalidates expressions or package references project-wide. **Do not attempt in-place conversion.** If the user wants to convert an existing project, confirm with them and follow [environment-setup.md § Project Conversion](references/environment-setup.md) — copy aside, `init` fresh with the target settings, recreate every workflow, delete the copy only after the user agrees.

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Work in a Legacy (.NET 4.6.1) project** | Legacy | [legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) — entry point. Modern-mode rules below do not apply. |
| **Plan the build's turn structure** | Both | [execution-maps-guide.md](references/execution-maps-guide.md) — read first for any build/edit journey |
| **Choose coded vs XAML / work in a hybrid project** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [environment-setup.md § Designing Project Structure](references/environment-setup.md#designing-project-structure) |
| **Create a new project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Any XAML authoring/editing task** (workflows, test cases, Flowchart/StateMachine/LRW, common activities, Data Fabric, IS connectors, triggers, XAML troubleshooting) | XAML | [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — Rule 22 read; § Critical Rules — XAML + § Task Navigation — XAML route the rest |
| **Any coded authoring/editing task** (workflows, test cases, source files, IS connectors, NuGet, API discovery, coded troubleshooting) | Coded | [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md) — § Critical Rules — Coded + § Task Navigation — Coded route the rest |
| **Set up data-driven testing** | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Set up Test Manager for the project** (server URL + default project) | Both | [cli-reference.md § Test Manager](references/cli-reference.md) — `uip rpa tm connect` / `set-default-project` |
| **Add error handling / resilience** (Try/Catch, Retry Scope, BusinessRuleException, ContinueOnError, screenshot-on-error, Global Exception Handler, recover app state, transaction boundary, idempotency / avoid duplicate creates, queue vs local retry ownership) | Both | [error-handling-guide.md](references/error-handling-guide.md) |
| **Write UI automation** | Both | UIA package guide `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` (Rule 7) |
| **Share Object Repository selectors across projects (UI Library)** | Both | [uia-starter-guide.md § Object Repository as a Published UI Library](references/uia-starter-guide.md) |
| **Run / debug a UIA workflow** | Both | [uia-starter-guide.md § Running UI Automation Workflows](references/uia-starter-guide.md) — baseline, debug session, window cleanup, selector recovery |
| **Drive a captured control** (date inputs, native vs custom dropdowns, buttons disabled during async) | Both | UIA package guide § Control-Specific Interaction Patterns |
| **Use Excel/Word/Mail/etc.** | Both | `.local/docs/packages/{PackageId}/` → fallback: `references/activity-docs/{PackageId}/{closest}/` (§ Resolving Packages & Activity Docs below) |
| **Manipulate data (DataTable/LINQ, strings, RegEx, DateTime, collections, JSON)** | Both | [data-manipulation-guide.md](references/data-manipulation-guide.md) |
| **Inspect Integration Service trigger lifecycle** (webhook vs. polling, filter fields, webhook URL retrieval) | Both | [trigger-pattern-guide.md § Connection Handling](references/trigger-pattern-guide.md) and [§ Server-Side Filtering](references/trigger-pattern-guide.md) |
| **Build/run/validate** | Both | [cli-reference.md](references/cli-reference.md) — a per-command catalog, do NOT read end-to-end: Grep `^## `, then Read the section for **every** command you will run, plus § Reading run / debug results regardless — the outer `Result` is not the run's verdict, and reading it as one reports failed workflows as passing |
| **Profile a slow workflow / verify UI automation correctness** | Both | [debugging.md § Profiling Workflow Performance](references/debugging.md) |
| **Pack & publish project to Orchestrator** | Both | [cli-reference.md § Pack & Publish to Orchestrator](references/cli-reference.md#pack--publish-to-orchestrator) |
| **List project best-practice / analyzer rules** | Both | [cli-reference.md § analyzer-rules list](references/cli-reference.md) |
| **Find / reuse existing tenant libraries** | Both | [tenant-library-search-guide.md](references/tenant-library-search-guide.md) |
| **Extract reusable logic into a library / publish it** | Both | [library-authoring-guide.md](references/library-authoring-guide.md) — public-workflow contract, private helpers, § Pack & Publish |
| **Invoke a PowerShell script from a workflow** | Both | [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| **List / install Data Fabric entities** | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md) |
| **Understand project structure** | Both | [environment-setup.md § Project Structure Reference](references/environment-setup.md#project-structure-reference) |

## Mode Packs

Each authoring mode's critical rules, quick reference, and task navigation live with the mode's primary reference — read per the gates above (Rule 22 for XAML; Coded Rules 13–19 gate for coded):

- **XAML:** [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — § Critical Rules — XAML, § XAML Task Navigation & Quick Reference, authoring workflow, anatomy, editing operations
- **Coded:** [coded/codedworkflow-reference.md](references/coded/codedworkflow-reference.md) — § Critical Rules — Coded, § Coded Quick Reference (file types, service-to-package mapping, templates), § Task Navigation — Coded, base-class reference

## Resolving Packages & Activity Docs

Follow this flow whenever you need to use an activity package:

### Step 1 — Ensure the package is installed

Check `project.json` → `dependencies` for the required package.

**Always query versions with `--include-prerelease`.** Many UiPath activity packages ship as `-preview` between stable releases, and the latest preview routinely contains new activities, fixed signatures, and updated `.local/docs` content that activity generation depends on. Without the flag, the listing hides these and the agent will pick a stale stable.

- **If present** → note the installed version. Then list available versions with `--include-prerelease` and compare:
  - If a newer version (stable or preview) exists, **inform the user**: state the installed version, the latest available version, and that newer packages offer the best support for activity generation (latest activity surface, accurate `.local/docs`, fewer signature mismatches). Ask whether to upgrade. **Never force-upgrade** an already-installed package.
  - If the installed version is already the latest, proceed to Step 2.
- **If absent** → install the latest version returned by `packages versions --include-prerelease` (preview is acceptable):

```bash
uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json
uip rpa packages install --packages 'id=<PackageId>,version=<LATEST_VERSION>' --project-dir "<PROJECT_DIR>" --output json
```

### Step 2 — Find activity docs (priority order)

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — auto-generated, most accurate. **Read the exact file directly by path** (`.../{PackageId}/activities/<Activity>.md`) — a failed Read IS the existence check. `Glob` AND `Grep` both skip `.local/` as gitignored: a miss from either proves NOTHING about the docs. To list what exists, `ls` the exact directory via Bash. NEVER enumerate the docs tree (hundreds of files; for UIA the guide's § Documentation already lists every reference).
2. **Fall back to bundled references** at `references/activity-docs/{PackageId}/` — pick the version folder closest to what is installed.

## UI Automation References

UIA references live in two locations. Always cite by location so the reader knows which tree to open:

- **This skill** (`references/`, relative to this SKILL.md) — policy this skill owns: prerequisites/version gating, run/debug orchestration, stub-mode deliverables, UI Library publishing.
- **UIA activity pack** (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`, installed via `uip rpa packages install`) — the UIA authoring guide, target-capture orchestration, single-purpose task guides, concrete `uip rpa uia` CLI syntax, per-activity property surfaces, coded API surface, and the UIA skill internal procedures. Co-versioned with the package, so always source-of-truth over anything in this skill when they diverge.

### In this skill (`references/`, relative to this SKILL.md)

- [uia-starter-guide.md](references/uia-starter-guide.md) — **read first for any UIA work** (Rule 7). Mandates the package guide read, then owns the skill-side UIA policies: run/debug procedure (baseline → debug → cancel → window cleanup) + profiling + runtime selector failure recovery, the placeholder-stub deliverable pattern, and UI Library publishing. Version gating and upgrade consent: its § UIA Prerequisites.

### In the UIA activity pack (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`)

- `ui-automation-guide.md` — **the entry point for all UIA authoring** (Rule 7; read in full first — also the Rule 7a availability probe: `ls` the exact path via Bash or attempt the direct Read; `Glob`/`Grep` skip gitignored `.local/`, so a miss from them NEVER proves absence — never enumerate the docs tree). Window baseline, capture orchestration, common pitfalls, control-specific interaction, coded and XAML patterns. Its § Documentation routes to everything else in the pack: target-capture orchestration, task guides, CLI command inventory, per-activity property surfaces, coded API surface, runtime selector recovery, and the bundled UIA skill (`uia-configure-target`).

## Completion Output

**Before reporting "done", verify the plan is complete.** If a plan file at `docs/plans/*.md` drove this work:
1. Re-read the plan and scan its task checkboxes.
2. If any `[ ]` boxes remain AND the plan's header says `Execution autonomy: autonomous` AND no `Stop conditions` item was hit — **do not report done**. Resume execution on the next unchecked task.
3. If unchecked boxes remain because a Stop condition was hit, name the exact stop-condition item in the report.
4. If the plan is fully checked off, or execution autonomy is `interactive`, proceed to the report format below.

Then, if the harness provides persistent memory, save validated patterns per [execution-maps-guide.md § Cross-session memory](references/execution-maps-guide.md#cross-session-memory) before reporting.

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — per-file `validate` result (all files passed, or remaining errors) **and** project-level `uip rpa build` result. Both must be clean to claim verification — `validate` clean alone is insufficient — it covers only the files it was pointed at, while `build` compiles the whole project (Rule 3). If `build` has not run since the last edit, say so explicitly rather than claiming success.
3. **Plan completion** — which task checkboxes in `docs/plans/*.md` are now `[x]`; list any still `[ ]` and, for each, the Stop-condition item that interrupted it (or "not reached" if execution was cut short another way)
4. **How to run** — the `uip rpa run` (or `uip rpa debug start`) command (if applicable)
5. **Next steps** — follow-up actions (configure connections, add OR elements, fill placeholders)
6. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, use `/uipath-feedback` to send a report."

Do NOT use framing like "complete", "done", "finished", or "the automation is built" unless every plan task is checked off. "Partial", "stopped at <task N>", or "blocked by <stop condition>" is the honest framing otherwise.
