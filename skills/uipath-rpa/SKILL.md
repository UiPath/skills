---
name: uipath-rpa
description: "Always invoke for `.xaml` or `.cs` workflow files. UiPath RPA — create, edit, build, run, debug `.cs` coded workflows and `.xaml` workflows. UI automation with Object Repository selectors, test case authoring, Integration Service connector calls. Live desktop/browser UI exploration and control. Deploy via `.uipx`→uipath-solution. Non-solution Orchestrator ops→uipath-platform. Test reports→uipath-test. Agents→uipath-agents."
when_to_use: "User wants to create, edit, debug, or run a UiPath automation — '.cs' coded workflows or '.xaml' files. Triggers: 'build a workflow', 'automate Excel/email/web/PDF/queue items', 'add a try-catch', 'fix this XAML error', 'scrape this site', 'process invoices', 'create a test case', or project.json shows UiPath dependencies. NOT for '.flow' files (→uipath-maestro-flow), Python agents (→uipath-agents)."
---

# UiPath RPA Assistant

Full assistant for creating, editing, managing, and running UiPath automation projects — both coded workflows (C#) and low-code RPA workflows (XAML).

> **Reading the referenced files is imperative — read each required file in full.** This SKILL.md is a router: it tells you *which* reference to open, not *what* it says. When a rule, the Task Navigation table, or a section points you to a reference for the task at hand, open it and read the **whole** file before acting — do not grep it for a keyword, skim the first screen, fall back to `--help`, or substitute prior knowledge. Most errors that slip past `validate` and surface at `build` or runtime trace back to a reference that was skipped or only partially read.

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

The full prohibited-tool list, the UIA-only exploration requirement, and the `InvokeJS`/`InjectJsScript` exception scope are in [ui-automation-guide.md](references/ui-automation-guide.md) § Mandatory: Generate Targets Before Writing Any UI Code — read it in full per Rule 7 before any UIA work.

**Running a UIA workflow.** Use `uip rpa debug start` throughout development, not `run` — a debug session pauses on error and leaves the UI state inspectable. During capture, advance app state with the UIA interact CLI, never `run` (a finishing `run` can close the target app). Switch to `run --skip-build` only as the final, non-interactive smoke test once the workflow is stable and `build` has passed. The full procedure — window baseline → `debug start` → cancel → window diff → selector-failure recovery — is in [ui-automation-guide.md](references/ui-automation-guide.md) § Running UI Automation Workflows.

### Placeholder-Selector Stub Pattern (when live app access is unavailable)

When generating a UI automation workflow **without** live app access (target capture cannot be run because the app is not installed, the agent has no UI, or the user explicitly deferred capture to a developer), emit **real UIA activities with placeholder selectors and `TODO Indicate` markers** — never `Log` stubs.

**Forbidden:** a workflow whose UI-interaction steps are `Log("LoginWorkflow: type username")` with a `// TODO[selectors]:` comment. The workflow passes build/validate and runs cleanly, but does nothing. This is the most expensive kind of stub — it looks complete, the validator says it's fine, and the failure mode is silent.

**Required:** the **real** UIA activity (`NTypeInto`, `NClick`, `NGetText`, `NApplicationCard`, etc.) with the target descriptor's selector left as a placeholder string and a `TODO Indicate` marker embedded in the activity's `DisplayName` (XAML) or in a `// TODO[Indicate]` comment immediately adjacent to the coded call. A developer opens Studio, clicks **Indicate** on each marked activity, and the workflow runs.

This applies to **both** XAML and coded modes. The full pattern with XAML and coded examples is in [ui-automation-guide.md](references/ui-automation-guide.md) § Placeholder-Selector Stub Pattern (read in full per Rule 7).

**Hybrid pattern** — XAML orchestration + coded fallback for logic with no matching activity:

    Main.xaml                  ← orchestration (XAML)
      └── InvokeWorkflowFile → ProcessData.cs  ← coded logic

For the full decision flowchart, InvokeCode extraction rules, and detailed hybrid patterns, see [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md).

## Capture-First Fast Path

When the request is "automate this dialog/form" or "build a UI test from these manual steps" — i.e. the bulk of the work is target capture, not coding — **defer authoring-phase prerequisites until target capture is complete**. The capture surface is interactive, app-state-sensitive, and time-bound; project-context discovery and analyzer rules add nothing during capture and steal time from it.

**Fast-path order for capture-first tasks.** Read [ui-automation-guide.md](references/ui-automation-guide.md) and [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) in full first (Rule 7; the second is used in step 3). Then:

1. **Pre-flight Window Baseline** — list top-level windows once; decide whether to launch the app ([§ Pre-flight: Window Baseline](references/ui-automation-guide.md)).
2. **Inventory targets from manual steps** (Test Manager test case, PDD, or written script). Each "Click X" / "Enter Y" / "Select Z" / "Verify W" step maps to one OR element. Group by screen state ([§ Capturing from Manual Test Steps](references/ui-automation-guide.md)).
3. **Capture all targets** screen by screen via `uia-configure-target` and screen advancement ([§ Multi-Step UI Flows](references/uia-configure-target-workflows.md)).
4. **Then enter authoring phase:** project-context discovery (the precondition above), analyzer rules (Critical Rule 3 — Authoring-phase start), write code, validate.

Skip this path when the task has no UI surface (data transforms, IS connector calls, headless file/email automation). Also skip it when the task HAS a UI surface but **no live app to capture against** (app not installed, no GUI, capture deferred to a developer) — there is nothing to capture, so use the § Placeholder-Selector Stub Pattern above instead. The Window Baseline does not tell you if the app is installed and has a GUI — validate that separately (e.g. look for the executable on disk) or ask the user.

## Session Pre-warm

First heavy `uip rpa` call pays a ~22s Studio host cold-start (shared across `validate`/`build`/`run`/`activities get-default-xaml`/`analyzer-rules list`). When more than one is expected this session, background a cheap warm-up at session start so the tax hides behind planning:

```bash
uip rpa activities find --query log --output json > /dev/null 2>&1 &
```

**Skip** when 0 or 1 heavy `uip rpa` calls are expected (read-only Q&A, single-file inspection) — the warm-up doesn't reclaim its cost.

## Critical Rules

**Rule numbering.** Common Rules use 1–12. `### Coded-Specific Rules` continues 13–19. `### XAML-Specific Rules` is an independent 16–24 sequence, so numbers 16/17/18/19 appear in both mode-specific sections — the `[Coded]` / `[XAML]` prefix on each rule disambiguates. Cross-references in this file ("Common Rule 10", "Common Rule 12", "Rule 21", "Rule 24") always point to a uniquely-numbered rule.

### Common Rules (Both Modes)

1. **NEVER create a project without confirming none exists.** Follow Step 0 resolution: check explicit path, project name, then CWD for `project.json`. Only create when confirmed no project matches AND user explicitly requests creation.
2. **ALWAYS use `uip rpa init`** to create new projects — never write `project.json` or scaffolding manually.
   - **Before creating, decide if a template is needed.** If the user names a template ("REFramework", "Robotic Enterprise Framework", "based on the X template"), an industry/domain pattern (SAP, ERP, banking, mainframe), or otherwise hints at a non-blank starter, run `uip rpa templates search --query "<term>" --output json` first. Selection rule against `Data[*]`:
     - **User named a specific non-Official template** (e.g. "Enhanced REFramework", "Lite ReFrameWork") AND a `Marketplace` item's `title` or `packageId` substring-matches the user's specific qualifier → ask the user (Official + that Marketplace item are both candidates). Do NOT auto-pick.
     - **Exactly one `source == "Official"` match AND user did not name a non-Official template** → use it; pass `--template-package-id <packageId> --template-package-version <version>` to `init`. Proceed without asking.
     - **Multiple `Official` matches OR only `Marketplace` matches** → present candidates (`packageId`, `version`, `source`, `title`) to the user and ask which to use. Never silently pick a Marketplace template.
     - **No matches** → fall back to a built-in `--template-id` and tell the user nothing was found.
   - Built-in `--template-id` keywords map without a search: `library` → `LibraryProcessTemplate`, `test automation` / `test project` → `TestAutomationProjectTemplate`, otherwise `BlankTemplate`. When `--template-package-id` is set, `--template-id` is ignored. Full decision flow: [environment-setup.md § Template selection](references/environment-setup.md).
2a. **Pass `--target-framework` AND `--expression-language` explicitly on every `uip rpa init` — never omit them.** Both are immutable after creation (Rule 23); omitting `--target-framework` silently yields a **Windows** project. Choose framework by where the automation runs: cross-platform / non-Windows runtime (Linux, container, serverless) or Studio Web editing → **`Portable`** (Cross-platform); Windows runtime using Windows-only capabilities (Excel COM, classic Office, WPF / `PresentationFramework`, Windows-only UIA) or Studio Desktop as the edit surface → **`Windows`** (not editable in Studio Web). A request needing *both* a cross-platform runtime and a Windows-only capability is contradictory — surface it, don't silently pick. **Windows - Legacy is a last resort** (explicit ask or hard .NET 4.6.1 need; never inferred from VB.NET or non-"X" classic activities) — create it in Legacy mode, not modern `init`. No signal → `AskUserQuestion` (Windows vs Cross-platform), framed around the runtime host. `--expression-language`: default `VisualBasic`, `CSharp` only on explicit request.
3. **Phase-gated validation: analyzer rules run at AUTHORING-phase start, not session start.** Three-phase validation:
   - **Authoring-phase start** (immediately before creating or editing any workflow file — `.cs` with `[Workflow]`/`[TestCase]`, or `.xaml`): `uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json` to list the enabled Workflow Analyzer rules. Apply every `error` and `warning` rule during authoring so generated code passes `analyze` and `build` on the first attempt. Run once at this point; re-run only when project dependencies change. **DO NOT run at session start** — the call can take a minute or more (use `--scope <Activity|Workflow|Coded Workflow|Project>` to narrow if it times out, see [cli-reference.md § analyzer-rules list](references/cli-reference.md)). For capture-first tasks (target capture from manual test steps, dialog automation), this prerequisite is deferred until capture is complete — see § Capture-First Fast Path below.
   - **Per-file** (after every create or edit): `uip rpa validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` until 0 errors. Catches structural XAML, missing references, analyzer rules, schema violations. Fix one thing per iteration.
   - **Project-level build** (after per-file `validate` is clean across all files in the edit session, and before declaring done): `uip rpa build "<PROJECT_DIR>" --output json` until clean. Catches what `validate` misses (unknown members, invalid enums, CacheMetadata / member resolution, attribute-form C# JIT) — full list at [validation-guide.md § Errors `build` catches that `validate` misses](references/validation-guide.md). If `build` errors, identify the offending file from the output and re-run `validate --file-path` on it.
   - **5-attempt cap per loop** — 5 attempts for each file's per-file `validate` loop; a separate 5 attempts for the project-level `build` loop. Fix one root cause per iteration.
   - **Smoke-test shortcut:** A successful `uip rpa run` substitutes for the standalone end-of-session `build` — `run` compiles internally. Prefer `run --skip-build` when `build` has just passed; see [validation-guide.md § Smoke Test](references/validation-guide.md).

   See [references/validation-guide.md](references/validation-guide.md).
4. **ALWAYS validate files as you go AND verify the project builds before declaring done.** After every create or edit: per-file `validate` to clean. Project-level `build` runs once at the end of the edit session (or at any compile-verification gate) — not after every Edit, because `build` is project-scoped and rebuilds the entire project regardless of which file changed. `validate` clean alone is not "validated"; it cannot see member or enum errors — the project-level `build` is mandatory before declaring done. See [references/validation-guide.md](references/validation-guide.md).
5. **Prefer UiPath built-in activities** for Orchestrator integration, UI automation, and document handling. Prefer plain .NET / third-party packages for pure data transforms, HTTP calls, parsing.
5a. **Secrets only via Orchestrator credential/secret assets.** Never hardcode secrets in workflows, expressions, or arguments; never store them in `Config.xlsx` cells (the Assets sheet holds asset *names*, not values); never log them — keep `SecureString` end-to-end and keep secret-bearing variable names inside the `project.json` `excludedLoggedData` masks. Read/write forms, SecureString consumption, log masking: [orchestrator-resources-guide.md](references/orchestrator-resources-guide.md).
6. **ALWAYS ensure required package dependencies are in `project.json`** before using their activities or services.
6a. **Pre-edit verification gate.** Two authoring actions are hard to roll back once `build` fails — verify before serialization, not after.
   - **Removing a dependency** — grep the project for usages before deleting an entry. A package may be the sole supplier of an activity used elsewhere (`MergePDFs` lives in the IntelligentOCR.StudioWeb family).
   - **Writing a new activity tag** — confirm via `uip rpa activities find --query "<verb>" --output json` and use the returned `ClassName`. Do not derive tag names from Studio display names. See [common-pitfalls.md § Common Activity Name Confusions](references/xaml/common-pitfalls.md).
7. **[UIA] Before writing ANY UIA activity (XAML `<uix:N*>` or coded `uiAutomation.*` / `Descriptors.*`), MUST read [references/ui-automation-guide.md](references/ui-automation-guide.md) IN FULL** — including the mode-specific section (For Coded Workflows or For XAML Workflows) and Running UI Automation Workflows. No exceptions for "simple" UIs. Skipping this rule is the most common cause of hallucinated selectors, wrong target XML, and missing OR descriptors. NEVER hand-write selectors — use `uia-configure-target` exclusively (the guide explains how). This guide is the single entry point for UIA work: it routes you to [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md), [uia-prerequisites.md](references/uia-prerequisites.md), and the package docs in order — the other UIA sections in this file point back here rather than restating the read mandate.
7a. **[UIA] Verify UIA prerequisites before invoking `uia-configure-target`.** The minimum version and the prerequisite check live in [uia-prerequisites.md](references/uia-prerequisites.md) — read it and run that check first (do not hardcode the version from memory; that file is the only source of truth). If `UiPath.UIAutomation.Activities` is below the minimum or `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md` is absent, the `uip rpa uia` CLI is unavailable — and **both** target capture and indication depend on it, so indication is *not* a fallback when the package itself is missing. Ask the user to install/upgrade per uia-prerequisites.md. If they decline or the package cannot be installed, fall back to the **Placeholder-Selector Stub Pattern** (§ above) — real activities with `TODO Indicate` markers need no CLI. Never silently route to a non-existent skill path. Use indication capture only when a compatible UIA package *is* installed but `uia-configure-target` cannot see the element; record `UI capture: indication-only` in the plan header to skip `uia-configure-target` in that case.
8. **Use `--output json`** on all CLI commands whose output is parsed programmatically.
8a. **`run` / `debug start` success/failure verdict comes from the outer `Result` (and equivalently the inner `HasErrors`), NEVER from any log entry's `Level`.** A successful workflow may emit `Log Message` activities at `Error` or `Warning` level as observability — those are workflow-emitted data, not CLI failures. Compile failures, validation failures, and unhandled runtime exceptions all flip `HasErrors` and propagate to the outer `Result`. Treating log-entry levels as a failure signal flips green runs to "failed" and burns retries on healthy workflows. See [cli-reference.md § run](references/cli-reference.md) and [debugging.md § Reading Debug Output Effectively](references/debugging.md).
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
2. **Activity-discovery fan-out.** Rule 21 runs a triple per non-card activity (`activities find` → read `<Activity>.md` → `get-default-xaml`). For K activities, emit all K `find`s as parallel `Bash`, then all K doc `Read`s in parallel, then all K `get-default-xaml`s in parallel — never one activity at a time. See [xaml/workflow-guide.md § Phase 1](references/xaml/workflow-guide.md).

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

### XAML-Specific Rules

16. **[XAML] Activity docs are the source of truth** — check `{projectRoot}/.local/docs/packages/{PackageId}/` first. Always.
17. **[XAML] MUST understand project structure** — read `project.json`, check expression language, scan existing patterns. NEVER generate XAML blind.
18. **[XAML] Start minimal, iterate to correct** — build one activity at a time, validate after each addition.
19. **[XAML] Fix errors by category** — Package → Structure → Type → Activity Properties → Logic.
20. **[XAML] ViewState handling depends on the operation.** When editing existing files, do NOT modify ViewState on nodes you are not changing. When generating new Flowchart/StateMachine/ProcessDiagram workflows, generate ViewState for each node (see [canvas-layout-guide.md](references/xaml/canvas-layout-guide.md)). For Sequences, ViewState is optional.
21. **[XAML] Reading `<Activity>.md` from `{PROJECT_DIR}/.local/docs/packages/...` is a precondition for `activities get-default-xaml` — for every activity not on the common-activity card.**
    - **Card-listed activities:** check [references/common-activity-card.md](references/common-activity-card.md) first; if the activity is on the card, author from the card entry alone — skip `activities find`, skip `activities get-default-xaml`, skip the per-activity MD read.
    - **All other activities:** (1) `activities find` → class name, (2) **read `<Activity>.md` first** and extract a property checklist (required + use-case-relevant), (3) `activities get-default-xaml` → starter element, (4) **diff your checklist against the starter and add what's missing** — an empty checklist means you skipped step 2, go back.
    - **Doc lookup order:** primary `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md`; fallback `references/activity-docs/<PackageId>/<closest-version>/<Activity>.md` for older package versions where `.local/docs` is empty. **Exception — `UiPath.UIAutomation.Activities` has no bundled fallback:** `.local/docs` (present only after the package is installed) is its sole activity-doc source. If it is absent, do not hunt for a bundled copy — follow Rule 7a (install with consent per [uia-prerequisites.md](references/uia-prerequisites.md), or use the Placeholder-Selector Stub Pattern).
    - **Trigger activities are special — read BOTH docs.** When the class name ends in `Trigger`, the namespace contains `.Triggers`, or the description mentions "starts a job" / "Monitor Events" / "Trigger Scope", also read the bundled `references/activity-docs/<PackageId>/<closest-version>/activities/<Activity>.md` **and** the package's bundled `overview.md`. The auto-generated `.local/docs` version is sparse for triggers; the bundled hand-written docs carry placement guidance (entry-point vs. `ui:TriggerScope`), deployment context, and cross-cutting namespace/assembly gotchas that the extractor does not capture. See Common Rule 12 and [trigger-pattern-guide.md](references/trigger-pattern-guide.md).
    - **Skip-tax — concrete:** `activities get-default-xaml` omits any property whose value equals the type default. For `NGetText` the starter is literally `<uix:NGetText HealingAgentBehavior="SameAsCard" />` with **zero** output properties — authoring from this alone produces `NGetText.Value="..."` (does not exist; the property is `Text`), which `validate` accepts and `build` rejects. For `NTypeInto` that's 2 of 20 properties hidden.
    - **Self-extending the card — "this activity feels simple, I'll add it to the card mentally" — is the failure mode.** The card is the only allowlist; for non-card activities the MD read is the only check.
    - Full procedure: [xaml/xaml-basics-and-rules.md § Activity Property Surface](references/xaml/xaml-basics-and-rules.md).
21a. **[XAML] Built-in workflow activities: use the card only for this allowlist.** Fast-path card activities are: `Sequence`, `If`, `Switch<T>`, `TryCatch`, `While`, `DoWhile`, `ForEach<T>`, `Assign`, `LogMessage`, `WriteLine`, `Delay`, `Throw`, `Rethrow`. If the activity is on this list, open [references/common-activity-card.md](references/common-activity-card.md) and author from the card. If it is not on this list, follow full Rule 21. `InvokeWorkflowFile`, `Pick`, `Parallel`, and `ParallelForEach<T>` are intentionally off-card; use full Rule 21. Studio's "While" / "Do While" / "For Each" toolbox items emit UiPath wraps (`UiPath.Core.Activities.InterruptibleWhile` / `InterruptibleDoWhile` / `UiPath.Core.Activities.ForEach<T>`), not the framework `System.Activities.Statements.While`/`DoWhile`/`ForEach<T>`.
22. **[XAML] MUST read [references/xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md)** before generating or editing any XAML.
23. **[XAML] NEVER change `expressionLanguage` or `targetFramework` on an existing project.** Decide both proactively at init time (Common Rule 2a); this rule covers the immutability afterward. Both fields in `project.json` are fixed at creation time and apply to every XAML file in the project — flipping `expressionLanguage` (VisualBasic ↔ CSharp) invalidates every expression, and flipping `targetFramework` (Windows ↔ Portable/cross-platform, or Legacy) invalidates package references and activity compatibility. **Do not attempt in-place conversion.** If the user wants to convert an existing project, confirm with them, copy the project to a temporary folder, create a new project via `uip rpa init --expression-language <VisualBasic|CSharp> --target-framework <Windows|Portable>` (for a target of Windows - Legacy, create it in Legacy mode instead — modern `init` is not the legacy creation path), make sure all the defined workflows in the old project have an equivalent in the new project. Delete the copied project just after the new project has been successfully generated and the user agree with the changes.
24. **[XAML] Wrap every container-activity body/branch in `<Sequence>` — even single-activity bodies.** Studio's designer expects the wrap as a drop zone; Studio's emitter produces it. `validate` and `build` accept the bare form, so neither catches missing wrappers. Applies to creation and editing alike. Slots include `If.Then`/`If.Else`, `While`/`DoWhile` body, `ForEach.Body`, `TryCatch.Try`/`Catch`/`Finally`, `Switch.Default` + each case, `PickBranch.Trigger`/`Action`, `NApplicationCard.Body`. Full table with examples: [xaml/xaml-basics-and-rules.md § Container Activity Bodies — Wrap in Sequence](references/xaml/xaml-basics-and-rules.md).

## Task Navigation

| I need to... | Mode | Read these |
|-------------|------|-----------|
| **Work in a Legacy (.NET 4.6.1) project** | Legacy | [legacy/legacy-mode-guide.md](references/legacy/legacy-mode-guide.md) — entry point. Modern-mode rules below do not apply. |
| **Choose coded vs XAML** | Both | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) |
| **Work in a hybrid project** | Hybrid | [coded-vs-xaml-guide.md](references/coded-vs-xaml-guide.md) → [project-structure.md](references/project-structure.md) |
| **Create a new project** | Both | [environment-setup.md](references/environment-setup.md) |
| **Add/edit a coded workflow** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) → [coded/coding-guidelines.md](references/coded/coding-guidelines.md) |
| **Add a coded test case** | Coded | [coded/operations-guide.md](references/coded/operations-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Set up data-driven testing** | Both | [testing-guide.md § Data-Driven Testing](references/testing-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Create XAML test case (Given-When-Then)** | XAML | [testing-guide.md § XAML Test Case Structure](references/testing-guide.md) — remember: register in `fileInfoCollection` (Common Rule 10) |
| **Use mock testing** | XAML | [testing-guide.md § Mock Testing (WIP)](references/testing-guide.md) — requires CLI command not yet available |
| **Use XAML test activities** | XAML | [testing-guide.md § XAML Test Activities](references/testing-guide.md) |
| **Use execution templates** | XAML | [testing-guide.md § Execution Templates](references/testing-guide.md) |
| **Create/edit XAML workflow** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) |
| **Use a common activity** (`Sequence` / `If` / `Switch<T>` / `TryCatch` / `While` / `DoWhile` / `ForEach<T>` / `Assign` / `LogMessage` / `WriteLine` / `Delay` / `Throw` / `Rethrow`) | XAML | [common-activity-card.md](references/common-activity-card.md) |
| **Create Flowchart/StateMachine** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) |
| **Create/edit Long Running Workflow (ProcessDiagram)** | XAML | [xaml/long-running-workflow-guide.md](references/xaml/long-running-workflow-guide.md) → [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) |
| **Write UI automation** | Both | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) |
| **Build multi-screen UIA XAML workflow** | XAML | [ui-automation-guide.md](references/ui-automation-guide.md) → [uia-configure-target-workflows.md § Multi-Step UI Flows](references/uia-configure-target-workflows.md) |
| **Use Excel/Word/Mail/etc.** | Both | Service table below → `.local/docs/packages/{PackageId}/` → fallback: `references/activity-docs/{PackageId}/{closest}/` |
| **Use Data Fabric entities** | XAML | [xaml/workflow-guide.md](references/xaml/workflow-guide.md) → [activity-docs overview](references/activity-docs/UiPath.DataService.Activities/overview.md) |
| **Query Data Fabric with filters** | XAML | [data-service-filter-builder-guide.md](references/activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) → [QueryEntityRecords](references/activity-docs/UiPath.DataService.Activities/activities/QueryEntityRecords.md) |
| **Read config/secret from Orchestrator (assets/credentials)** | Both | [orchestrator-resources-guide.md](references/orchestrator-resources-guide.md) → [GetRobotAsset](references/activity-docs/UiPath.System.Activities/26.4/activities/GetRobotAsset.md) / [GetRobotCredential](references/activity-docs/UiPath.System.Activities/26.4/activities/GetRobotCredential.md) |
| **Move files via storage bucket** | Both | [orchestrator-resources-guide.md § Storage Buckets](references/orchestrator-resources-guide.md) → `references/activity-docs/UiPath.System.Activities/26.4/activities/{Upload,Download,List,Delete}StorageFile.md` |
| **Work with queue items outside REFramework** (dispatcher, performer hygiene, deadlines) | Both | [orchestrator-resources-guide.md § Queue Patterns](references/orchestrator-resources-guide.md) → [AddQueueItem](references/activity-docs/UiPath.System.Activities/26.4/activities/AddQueueItem.md) / [BulkAddQueueItems](references/activity-docs/UiPath.System.Activities/26.4/activities/BulkAddQueueItems.md) |
| **Start/stop/wait on another Orchestrator process or job** (incl. alerts, ShouldStop) | Both | [orchestrator-resources-guide.md § Jobs & Processes](references/orchestrator-resources-guide.md) → [RunJob](references/activity-docs/UiPath.System.Activities/26.4/activities/RunJob.md) / [StartJob](references/activity-docs/UiPath.System.Activities/26.4/activities/StartJob.md) |
| **Call an IS connector (coded)** | Coded | [coded/integration-service-guide.md](references/coded/integration-service-guide.md) |
| **Call an IS connector (XAML)** | XAML | [is-connector-xaml-guide.md](references/is-connector-xaml-guide.md) → [connector-capabilities.md](references/connector-capabilities.md) |
| **Build an event-triggered workflow** (O365 / Gmail / Salesforce / Jira / Slack / ServiceNow / time / queue / file watcher / UI click) | XAML | [trigger-pattern-guide.md](references/trigger-pattern-guide.md) → `activity-docs/{PackageId}/{closest}/activities/<TriggerActivity>.md` |
| **Inspect Integration Service trigger lifecycle** (webhook vs. polling, filter fields, webhook URL retrieval) | Both | [trigger-pattern-guide.md § Connection Handling](references/trigger-pattern-guide.md) and [§ Server-Side Filtering](references/trigger-pattern-guide.md) |
| **Read or edit an existing `ui:TriggerScope` workflow** | XAML | [trigger-pattern-guide.md § Reading and Editing Existing TriggerScope XAML](references/trigger-pattern-guide.md) |
| **Build/run/validate** | Both | [cli-reference.md](references/cli-reference.md) → [validation-guide.md](references/validation-guide.md) |
| **Profile a slow workflow / verify UI automation correctness** | Both | [debugging.md § Profiling Workflow Performance](references/debugging.md) |
| **Pack & publish project to Orchestrator** | Both | [publishing-guide.md](references/publishing-guide.md) |
| **List project best-practice / analyzer rules** | Both | [cli-reference.md § analyzer-rules list](references/cli-reference.md) |
| **Add a NuGet package** | Coded | [coded/operations-guide.md § Add Dependency](references/coded/operations-guide.md) → [coded/third-party-packages-guide.md](references/coded/third-party-packages-guide.md) |
| **Find / reuse existing tenant libraries** | Both | [tenant-library-search-guide.md](references/tenant-library-search-guide.md) |
| **Invoke a PowerShell script from a workflow** | Both | [powershell-interop-guide.md](references/powershell-interop-guide.md) |
| **List / install Data Fabric entities** | Both | [cli-reference.md § Data Fabric Entities](references/cli-reference.md) |
| **Discover activity APIs** | Coded | [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md) |
| **Troubleshoot coded errors** | Coded | [coded/coding-guidelines.md § Common Issues](references/coded/coding-guidelines.md) |
| **Troubleshoot XAML errors** | XAML | [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) → [validation-guide.md](references/validation-guide.md) |
| **Understand project structure** | Both | [project-structure.md](references/project-structure.md) |

## Coded Workflows Quick Reference

Coded workflows use standard C# development: create file → write code → validate → run. Activity discovery (`activities find`, `activities get-default-xaml`) is XAML-specific — for coded mode, check `{projectRoot}/.local/docs/packages/{PackageId}/coded/coded-api.md` first for service API docs, then fall back to `packages inspect`. See [coded/inspect-package-guide.md](references/coded/inspect-package-guide.md). For `system` service asset/credential/queue/storage-bucket calls, the bundled fallback is [activity-docs/UiPath.System.Activities/26.4/coded/coded-api.md](references/activity-docs/UiPath.System.Activities/26.4/coded/coded-api.md); which resource to use, secret hygiene, and queue patterns: [orchestrator-resources-guide.md](references/orchestrator-resources-guide.md).

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
- [assets/json-template.md](assets/json-template.md) — `entryPoints` and `fileInfoCollection` snippets
- [assets/before-after-hooks-template.md](assets/before-after-hooks-template.md) — Before/After hooks
- [references/project-structure-guide.md](references/project-structure-guide.md) — Project structure design guidelines (mode-agnostic)

## XAML Workflows Quick Reference

XAML workflows follow a **discovery-first, phase-based approach**: Discovery → Generate/Edit → Validate & Fix → Response. See [references/xaml/workflow-guide.md](references/xaml/workflow-guide.md) for the full phase workflow.

### Workflow Types

| Type | When to Use |
|------|-------------|
| **Sequence** | Linear step-by-step logic; most common for simple automations |
| **Flowchart** | Branching/looping logic with multiple decision points |
| **State Machine** | Long-running processes with distinct states and transitions |
| **Long Running Workflow** | BPMN-style horizontal flow; event-driven processes with long waits. Requires `UiPath.FlowchartBuilder.Activities` — see [xaml/long-running-workflow-guide.md](references/xaml/long-running-workflow-guide.md) |

### Expression Language

Check `expressionLanguage` in `project.json`. VB.NET uses `[brackets]` for expressions; C# uses `CSharpValue<T>` / `CSharpReference<T>`. Default for new XAML projects is VB.NET.

### Key CLI Commands

| Command | Purpose |
|---------|---------|
| `activities find --query "<keyword>"` | Discover activities by keyword |
| `activities get-default-xaml --activity-class-name "<class>"` | Get starter XAML for an activity |
| `analyzer-rules list --project-dir "<dir>"` | List enabled Workflow Analyzer rules — run before generating |
| `validate --file-path "<file>"` | Per-file static validation (structure, references, analyzer rules) |
| `build "<PROJECT_DIR>"` | Compile-time validation (member names, enum values, JIT expressions) — run after `validate` is clean |

### Common Activities

| Activity | Package | Purpose |
|----------|---------|---------|
| **UI automation** (Use Application/Browser, Click, Type Into, Get Text, Select Item, …) | `UiPath.UIAutomation.Activities` | **Never author from memory or from this row.** Selectors and targets are captured, not hand-written — read [ui-automation-guide.md](references/ui-automation-guide.md) in full first (Rule 7). |
| If | built-in | Conditional branching |
| Assign | built-in | Set variable/argument values |
| For Each | built-in | Iterate over a collection |
| Invoke Workflow File | built-in | Call another workflow file |
| Create Entity Record | `UiPath.DataService.Activities` | Create a Data Fabric entity record |
| Query Entity Records | `UiPath.DataService.Activities` | Query Data Fabric records with filters — see [filter builder guide](references/activity-docs/UiPath.DataService.Activities/guides/data-service-filter-builder-guide.md) |

### XAML File Anatomy

The XAML file anatomy template (namespace declarations, root Activity element, body structure) is in [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — read it before generating or editing any XAML.

### Key References

- [xaml/xaml-basics-and-rules.md](references/xaml/xaml-basics-and-rules.md) — XAML anatomy, safety rules, editing operations (read before any XAML work)
- [xaml/common-pitfalls.md](references/xaml/common-pitfalls.md) — Activity gotchas, scope requirements, property conflicts
- [reframework-guide.md](references/reframework-guide.md) — REFramework execution modes, SetTransactionStatus queue-guard fix, Config.xlsx leftover trap
- [xaml/csharp-activity-binding-guide.md](references/xaml/csharp-activity-binding-guide.md) — Canonical C# binding forms per common activity property (LogMessage, GetText, StartProcess, …) — flat lookup table + recipes
- [xaml/csharp-expression-pitfalls.md](references/xaml/csharp-expression-pitfalls.md) — C#-specific expression failures (attribute-form VB JIT, ThrowIfNotInTree, OutArgument parse errors)
- [xaml/canvas-layout-guide.md](references/xaml/canvas-layout-guide.md) — Flowchart, State Machine, and Long Running Workflow canvas layout with ViewState
- [xaml/long-running-workflow-guide.md](references/xaml/long-running-workflow-guide.md) — LRW package dependency, node vocabulary, gateway patterns, suspend/resume persistence
- [xaml/jit-custom-types-schema.md](references/xaml/jit-custom-types-schema.md) — JIT custom type discovery

### Multi-Screen UI Automation Workflows

For XAML workflows spanning multiple capture screens, add each screen's activities to the workflow as its targets get registered in the OR — validating with `validate` after each batch. [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) MUST be read IN FULL first (see § Multi-Step UI Flows for the capture loop and the Complete-then-advance rule).

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

1. **Check `{PROJECT_DIR}/.local/docs/packages/{PackageId}/`** — auto-generated, most accurate. Use `Glob` + `Read` (not `Grep` — `.local/` is gitignored).
2. **Fall back to bundled references** at `references/activity-docs/{PackageId}/` — pick the version folder closest to what is installed.

## UI Automation References

UIA references live in two locations. Always cite by location so the reader knows which tree to open:

- **This skill** (`references/`, relative to this SKILL.md) — policy, decision logic, target-capture orchestration, debug/recovery flows.
- **UIA activity pack** (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`, installed via `uip rpa packages install`) — concrete `uip rpa uia` CLI syntax, per-activity property surfaces, coded API surface, and the UIA skill internal procedures. Co-versioned with the package, so always source-of-truth over anything in this skill when they diverge.

### In this skill (`references/`, relative to this SKILL.md)

- [ui-automation-guide.md](references/ui-automation-guide.md) — **the entry point for all UIA work** (Rule 7; read in full first). Mode-specific UIA patterns (coded vs XAML), prohibited-tool list, exploration-tool boundaries, Running & debugging procedure.
- [uia-prerequisites.md](references/uia-prerequisites.md) — Package version requirements, upgrade-consent rules
- [uia-configure-target-workflows.md](references/uia-configure-target-workflows.md) — Target-capture orchestration, multi-step UI flows, indication-fallback routing

### In the UIA activity pack (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/`)

- `overview.md` — Package overview and entry point
- `references/cli-reference.md` — Full `uip rpa uia` CLI: subcommands, flags, accepted values, artifact filenames
- `references/object-repository.md` — Object Repository concepts and CLI flows
- `references/selector-variables.md` — Selector variable substitution
- `references/uia-target-attachment-guide.md` — Attaching OR targets to XAML activities (TargetApp / TargetAnchorable)
- `references/indication-fallback-workflow.md` — Indication-mode capture when `uia-configure-target` is unavailable
- `coded/coded-api.md` — Coded API surface for `uiAutomation.*` service calls
- `activities/<Activity>.md` — Per-activity property surface (`NClick`, `NTypeInto`, `NApplicationCard`, …)
- `activities/common/<Type>.md` — Shared enums and types (`NHealingAgentBehavior`, `Target`, `NClickType`, …)
- `skills/uia-configure-target/{SKILL.md,USAGE.md}` — Target-configuration skill: procedure + invocation modes
- `skills/uia-improve-selector/{SKILL.md,USAGE.md}` — Selector recovery / improvement skill

## Completion Output

**Before reporting "done", verify the plan is complete.** If a plan file at `docs/plans/*.md` drove this work:
1. Re-read the plan and scan its task checkboxes.
2. If any `[ ]` boxes remain AND the plan's header says `Execution autonomy: autonomous` AND no `Stop conditions` item was hit — **do not report done**. Resume execution on the next unchecked task.
3. If unchecked boxes remain because a Stop condition was hit, name the exact stop-condition item in the report.
4. If the plan is fully checked off, or execution autonomy is `interactive`, proceed to the report format below.

When you finish a task, report to the user:
1. **What was done** — files created, edited, or deleted (list file paths)
2. **Validation status** — per-file `validate` result (all files passed, or remaining errors) **and** project-level `uip rpa build` result. Both must be clean to claim verification — `validate` clean alone is insufficient (it does not detect unknown member names or invalid enum values). If `build` has not run since the last edit, say so explicitly rather than claiming success.
3. **Plan completion** — which task checkboxes in `docs/plans/*.md` are now `[x]`; list any still `[ ]` and, for each, the Stop-condition item that interrupted it (or "not reached" if execution was cut short another way)
4. **How to run** — the `uip rpa run` (or `uip rpa debug start`) command (if applicable)
5. **Next steps** — follow-up actions (configure connections, add OR elements, fill placeholders)
6. **Trouble?** — if the user hit issues during this session, mention: "If something didn't work as expected, use `/uipath-feedback` to send a report."

Do NOT use framing like "complete", "done", "finished", or "the automation is built" unless every plan task is checked off. "Partial", "stopped at <task N>", or "blocked by <stop condition>" is the honest framing otherwise.
