# UIA Fast Path Guide

Capture-efficiency overlay for a **single-application UIA XAML workflow** (e.g. open Calculator, compute 5+5, log the result). Orchestrates target capture to cut round-trips. It does NOT compress or replace any read.

**Rule 7 reads are unchanged.** Before any UIA work, read [ui-automation-guide.md](ui-automation-guide.md) and [uia-configure-target-workflows.md](uia-configure-target-workflows.md) IN FULL (SKILL.md Rule 7). This guide adds orchestration on top of them; it is not a substitute.

Applies only when every eligibility condition below holds. Any gate failure — or a mid-build surprise — routes to the full Rule 7 path with no overlay.

## A. Eligibility Gate

ALL must hold. Check in one batch of cheap tool calls: read `project.json` (framework, expression language, dependency count), `Glob` `**/*.xaml` and `**/*.cs` (exclude `.local/` and `.codedworkflows/`), confirm the UIA package + its capture skill file, and one window-baseline listing.

1. **Modern XAML project.** Existing `project.json`; `targetFramework` is `Windows` or `Portable` (NOT `Legacy`); XAML mode (no `[Workflow]`/`[TestCase]` `.cs`).
2. **Single target application.** One OS process; no cross-process helper dialog expected (sign-in, OAuth, UAC, `consent.exe`). Multiple capture screens **within one app** are allowed (menu → dialog), up to ~3 screens / ~10 elements.
3. **Live app on this machine.** GUI present. If not installed / no GUI / capture deferred → use SKILL.md § Placeholder-Selector Stub Pattern, not this guide.
4. **UIA package ready.** `UiPath.UIAutomation.Activities` installed at ≥ the minimum in [uia-prerequisites.md](uia-prerequisites.md) (read it — sole source of the version), AND `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md` exists.
5. **Selector-based capture only.** All targets captured via `uia-configure-target`; no CV-only or Semantic requirements known upfront; no triggers, no Integration Service connectors, no test cases.

**ANY condition fails → STOP. Follow the full path** (SKILL.md Rule 7 chain). Mid-build surprises (a new process appears, CV needed, selectors stay fragile, a date/dropdown/async-disabled control) also route back — read [uia-elements-interaction-guide.md](uia-elements-interaction-guide.md) IN FULL for control-specific cases.

## B. Capture Orchestration Steps

Step 1's background calls fire FIRST — look up only the baseline subcommand's syntax in the package `cli-reference.md`, fire, then do the full reads while both run: the Rule 7 reads (intro above), plus the capture skill's own docs: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-configure-target/SKILL.md`, its `USAGE.md`, and `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/selection-activity-types.md`.

### 1. Background warm-up + analyzer rules (ONE Bash call, at entry)

Fire-and-forget. Warms the Studio host AND produces the Rule 3 analyzer artifact:

```bash
uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json > "<PROJECT_DIR>/.local/analyzer-rules.json" 2>&1 &
```

Harvest the file at authoring time. If not present yet, wait for it. Apply every `error`/`warning` rule during authoring, same as Rule 3. This replaces the SKILL.md § Session Pre-warm warm-up — do not run both.

In the same message, also fire the step-2 window-baseline listing (the UIA snapshot CLI — syntax in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`) as a second background call with output redirected to a file. The UIA design host pays a ~20s cold start on its first call; backgrounding it here hides that behind the reads, and the saved output IS the step-2 baseline — harvest the file instead of re-running the listing.

### 2. Pre-flight window baseline

Harvest step 1's backgrounded baseline (or list top-level windows once via the UIA snapshot CLI — syntax in `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`). The listing prints a window/tab count plus the path of a snapshot file — `Grep` that snapshot file for the target window's title/app to decide; the counts alone don't answer it. Never `Get-Process`/`tasklist`/WMI. Three outcomes:

- **Target window present** → proceed to capture.
- **Target window absent** → launch the app, then proceed.
- **The listing itself errors** (driver/COM failure, not "window absent") → first check for a locked or non-interactive Windows session (`LogonUI` process running = lock screen up) — UIA cannot scan a locked desktop, and every live scan fails until it is unlocked. Locked → surface to the user and pause; do NOT fall back to the stub pattern for a transient lock. Unlocked but scans still fail persistently → SKILL.md Rule 7a runtime-failure fallback.

### 3. Capture each screen's targets in ONE batched run

Run `uia-configure-target` once per screen for ALL of that screen's elements — pass them together in the batch (pipe-separated) element form documented in its `USAGE.md`, so the window is captured once and reused. The capture procedure is NOT compressed: run it exactly as the capture skill specifies, inline in the main conversation — never delegate the whole skill to a subagent (it spawns its own).

For multiple screens, **complete-then-advance**: finish every capture + OR registration for the current screen before advancing the app to the next state via the interact CLI. NEVER hand-write or hand-edit a selector; the capture skill is the only source of selectors and OR registration.

### 4. Author each screen's activities, then attach its OR targets

Author the screen's activities (SKILL.md Rule 21 + the full Rule 7 reads), then attach the OR targets per `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/uia-target-attachment-guide.md` — that doc owns the concrete commands.

- **Follow the attachment guide's fast path (link):** attach the screen first, then all of its element targets in ONE batched call. Never run parallel mutations of the same `.xaml` file.
- **On a link failure for a reference, switch to that guide's embed fallback immediately** for that reference — do not iterate on activity ids or element names.
- **IdRef contract:** every linkable activity carries a unique `sap2010:WorkflowViewState.IdRef` of the form `<ClassName>_<N>` (per-class numbering, unique across the file). Author plans for this — the linker addresses activities by IdRef.

Validate and build per SKILL.md Rule 3 / Rule 4 (per-file `validate` to clean, then project-level `build`). On a runtime selector failure, route to [ui-automation-guide.md § Runtime Selector Failure Recovery](ui-automation-guide.md) — do not hand-edit selectors.

## C. Blank-Scaffold Context Stub

When `.claude/rules/project-context.md` is **absent** AND the project is a blank scaffold — ≤2 workflow files total (`.cs` + `.xaml`, excluding `.local/` and `.codedworkflows/`) AND `project.json` has ≤3 dependencies — do NOT spawn the discovery agent. There is nothing to discover. Write the stub below inline to **both** `.claude/rules/project-context.md` AND `AGENTS.md` (in `AGENTS.md`, wrap it in `<!-- PROJECT-CONTEXT:START -->` / `<!-- PROJECT-CONTEXT:END -->` markers, replacing any existing block). Fill the first-line metadata with real counts so staleness checks keep working.

```markdown
<!-- discovery-metadata: cs=<CS_COUNT> xaml=<XAML_COUNT> deps=<DEPS_COUNT> -->
# Project Context

- **Project:** <PROJECT_NAME>
- **Target framework:** <Windows|Portable>
- **Expression language:** <VisualBasic|CSharp>
- **Main entry:** <MAIN_FILE>
- **Dependencies:** <PACKAGE_ID@VERSION, ...>
- **Conventions:** blank scaffold — no local patterns established yet.
```

If `.claude/rules/project-context.md` exists, follow SKILL.md § Precondition (staleness check) instead. If the project is NOT a blank scaffold, run the full discovery flow.
