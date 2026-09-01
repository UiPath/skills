<!-- Split out of implementation.md so each phase file can be read whole. Phase 2 is in [implementation.md](implementation.md); Phase 3 in [implementation-phase-3.md](implementation-phase-3.md). -->

# Phase 4 — Validate (Steps 12 – 12.1)

Authoritative validation. Full contract — command, retry policy, AskUserQuestion options — in [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). This section is a bridge — do NOT duplicate contract here.

## Step 12 — Full validate

Run validate per [phased-execution.md § Phase 4](phased-execution.md#phase-4--validate). On success: proceed to Step 12.1. On 3rd failure: hard-stop prompt per the same section.

## Step 12.1 — Summarize the issue log

The journal has been on disk since the first section boundary; this step does **not** create it. Flush any buffered issues from the final section, then read the journal back and write the grouped counts into the summary block per [`plugins/logging/impl-json.md` § Summary](plugins/logging/impl-json.md). Counts come from the file, not from reasoning — that is the point of flushing incrementally.

If `tasks/build-issues.md` is absent here, the incremental flush was skipped: reconstruct from on-disk artifacts and stamp the `NOTE:` line per [§ Recovery](plugins/logging/impl-json.md). A build carrying `<UNRESOLVED>` markers or placeholder tasks must not reach Phase 5 with no log.

On Phase 4 success → proceed to Phase 5.

---

# Phase 5 — Publish (Steps 13, 14)

Optional Studio Web upload. Full contract — report fields, prompt options, publish commands, pack/publish warning — in [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). This section is a bridge — do NOT duplicate contract here.

## Step 13 — Completion report + Publish prompt

Print report fields and run AskUserQuestion per [phased-execution.md § Phase 5](phased-execution.md#phase-5--publish). On `Publish to Studio Web` → Step 14. On `Skip to Debug` → Phase 6.

## Step 14 — Publish to Studio Web

Run `uip solution resources refresh` then `uip solution upload <SolutionDir> --output json --output-filter "{Status: Status, Action: Action, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"` per [phased-execution.md § Publish notes](phased-execution.md#publish-notes) — the filter is mandatory or `DesignerUrl` is lost to response truncation. Print `DesignerUrl` and say whether `Action` was `Imported` or `Overwritten`, then proceed to Phase 6.

---

# Phase 6 — Debug (Steps 15, 15a)

Optional CLI debug run. Full contract — prompt options, debug command, safety warning, loop behavior — in [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). This section is a bridge — do NOT duplicate contract here.

## Step 15 — Debug prompt + session

Run AskUserQuestion + debug command per [phased-execution.md § Phase 6](phased-execution.md#phase-6--debug). On `Run debug session` → run `uip solution resources refresh` then `uip maestro case debug`, loop until the user picks `Continue to publish`. On `Continue to publish` → Phase 7. Never auto-run (Rule 12).

## Step 15a — Troubleshoot failed case

When a debug or process run fails, read **[troubleshooting-guide.md](troubleshooting-guide.md)**. Diagnostic priority: incidents → runtime variables → caseplan.json correlation → traces (last resort).

**Diagnose → fix → re-run loop.** After each diagnostic pass, classify root cause and act:

1. **Fixable in `caseplan.json`** (wrong binding, missing condition, malformed expression, incorrect input value): apply targeted fix via matching plugin's `impl-json.md`, re-run `uip maestro case validate`, then re-run Step 15 debug. If the case was already published in Phase 5, ask via **AskUserQuestion** with options — `Re-publish the fixed build`, `Skip re-publish`. On `Re-publish`, re-run Step 14 so Studio Web holds the fixed build (the re-upload overwrites any Studio Web edits made since publish); on `Skip re-publish`, leave Studio Web on the build it already has.
2. **Fixable outside `caseplan.json`** (missing/expired connection, unregistered task type, missing Orchestrator asset, permissions): halt agent edits. Report exact resource + remediation steps to user via **AskUserQuestion** with options — `Resource fixed, re-run debug`, `Abort`.
3. **Inconclusive** (no actionable cause): proceed to next round per retry policy.

> **Known by-design debug fault:** an inline-built api-workflow sibling's task failing with incident `170007` ("job's associated process could not be found") under `case debug` is expected — debug does not provision Api siblings (agent siblings do resolve). Do not spend troubleshoot rounds on it; runtime verification needs a full solution deploy, offered via AskUserQuestion per [phased-execution.md § Debug notes](phased-execution.md#debug-notes) (the contract owner).

**Retry policy.** Up to 3 troubleshoot → fix → debug rounds per failed run. Each round must add new context (different element ID, broader scope, fallback command) or apply different fix — do not repeat identical commands or re-apply same fix. Track round count.

**Per-round timeout.** If debug run exceeds 10 minutes wall-clock, treat round as inconclusive and advance to next round (counts toward 3-round limit). Advisory — do not hard-kill subprocess; classify by elapsed time and move on.

After 3rd inconclusive round (or 3rd debug failure post-fix), halt and ask user with **AskUserQuestion**. Report: instance ID, folder key, incident IDs/messages, faulting element ID, variable snapshot, what was tried each round. Options — `Provide additional context` (user supplies hints; run one more targeted round), `Pause for manual investigation`, `Abort`. Do not propose `caseplan.json` edits without confirmed cause.

---

# Phase 7 — Publish to Orchestrator (Step 16)

Optional `case pack` (BPMN recompile) + `solution pack` + `solution publish` to the tenant solution feed. Full contract — prompt options, publish commands, version bumping, failure handling — in [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). This section is a bridge — do NOT duplicate contract here.

## Step 16 — Publish to Orchestrator

Run AskUserQuestion per [phased-execution.md § Phase 7](phased-execution.md#phase-7--publish-to-orchestrator). On `Publish to Orchestrator` → run `uip solution resources refresh`, then `uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json`, then `uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json`, then `uip solution publish "<packagePath>" --wait --output json`. **Never skip `case pack`** — it compiles `caseplan.json` → `caseplan.json.bpmn`, and it runs on every pass regardless of which earlier phases were skipped. Publish the `solution pack` `.zip`, never the `case pack` `.nupkg`. Read `<packagePath>` from the `solution pack` response `Data.Packages` — never guess the filename. On `Done` → exit skill. Never auto-run (Rule 12).

Stops at publish — `uip solution deploy run` is out of scope.

---

**Preceded by** [implementation-phase-3.md](implementation-phase-3.md) (Phase 3, incl. the Step 12 checks).

<!-- END: implementation-phase-4-7.md -->
