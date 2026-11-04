# Execution Maps — what every turn-budgeted build journey shares

Read once per build, then the task's journey in [execution-journeys-catalog.md](execution-journeys-catalog.md) (greenfield or brownfield XAML, greenfield or brownfield coded, UIA capture + build). Happy path, including the final report: **greenfield ≤5 turns, brownfield ≤5**; one repair cycle adds ≤2. Each T-row is one assistant message: all tool calls in one message cost one turn; one call per message costs N.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
> **Tool vocabulary.** `Edit` = in-place replacement, `Write` = full-file write, `Read`/`Glob`/`Grep` = read/search, `Bash` = shell. Map these Claude Code names to the harness equivalents. If parallel calls are unavailable, preserve each grouping as consecutive calls; CLI chains still collapse round-trips.

If a harness rejects a batch for permissions, treat it as an approval gate, not a CLI failure; do not split it to evade approval. For Claude Code Bash calls, offer `/uipath:install-permissions` to install the curated allowlist with user approval; use the harness permission mechanism otherwise.

## Source precedence — every activity you author

Use, in order:
1. **Card** — [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md)
2. **Agent memory** — validated prior-session snippet (see [§ Cross-session memory](#cross-session-memory))
3. **Rule 21 triple** — `activities find` → `<Activity>.md` read → `get-default-xaml`, fanned out inside T1/T2

`validate` + `build` gate all three. Card/memory hits skip discovery, never the gate.

## Gate ≠ runtime proof

A clean `validate` + `build` does not prove runtime behavior. Silent failures that pass both include C# `//` in child/CDATA `InvokeCode` `Code` swallowing later code, `WriteTextFile` with explicit `Encoding` emitting a BOM, and stripped UIA `N*` `Version` failing only at runtime ([xaml/common-pitfalls.md](xaml/common-pitfalls.md)). For observable outputs (written files or entry-point out-arguments) with no external systems/UI, run exactly one `uip rpa run --skip-build` (bare `run` for a XAML test case, [cli-reference.md § Smoke Test](cli-reference.md#smoke-test)), then `cat` every output file; judge that chain in the report turn. Neither run nor output check gets another turn; the journey's gate and report rows ([execution-journeys-catalog.md](execution-journeys-catalog.md)) place them.

## Sequential gates — never batch across these

- Run `templates search` before `init` (Rule 2) only when the user names a template or domain pattern; use its result, including an `AskUserQuestion`, to choose `--template-package-id`.
- Ask the Rule 2a framework/language question when the request has no signal.
- Ask the package version question (SKILL.md § Resolving Packages & Activity Docs, Step 1) before `packages install`. On an existing project, ask it once `packages versions` has returned, since it depends on the installed and available versions. On a greenfield project every needed package is absent: ask it in T1 beside the `init` chain, naming the options (latest stable, latest prerelease), and take their numbers from that chain's `packages versions` output.
- Keep every `AskUserQuestion` and consent gate sequential.
- Keep UIA state advances and indication sequential (see [execution-journeys-catalog.md § Journey: UIA capture + build](execution-journeys-catalog.md#journey-uia-capture--build-xaml)); capture screens require real application state.

## Failure exits

| Symptom | Open |
|---|---|
| `validate` structural/reference errors | [cli-reference.md § Validation Iteration Loop](cli-reference.md#validation-iteration-loop) |
| XAML activity gotcha (property conflicts, scope) | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) |
| Clean gate but wrong/empty runtime output | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) silent-failure sections: § InvokeCode Code Property — Attribute Form Only, § WriteTextFile Emits a UTF-8 BOM, § UIA `N*` Activities Carry a `Version` |
| Coded `CS*` errors | [coded/operations-guide.md § Common Issues and Fixes](coded/operations-guide.md#common-issues-and-fixes) |
| CLI `timeout`, `EPIPE`, `401`, or `not in the project folder` | [cli-reference.md § CLI Error Recovery](cli-reference.md#cli-error-recovery) |
| Card snippet rejected by validate/build | Use the Rule 21 triple for that activity; report the stale entry via `/uipath-feedback` |
| UIA selector fails at debug time | Use the recover selector flow per [uia-policies-catalog.md § Runtime Selector Failure Recovery](uia-policies-catalog.md#runtime-selector-failure-recovery); never hand-edit |

## Cross-session memory

Use memory only when the harness provides persistent memory; otherwise skip silently.

**Recall — T1 of every journey.** Match entries by activity class + package `major.minor`. A hit skips that activity's Rule 21 triple; `validate`/`build` still gate.

**Save — after a clean project `build`, in the report turn.** Emit all qualifying saves as parallel `Write`s in the report message; never use a separate memory turn or one memory file per turn. A first-try clean gate on card-covered activities qualifies nothing. Save only:

1. Validated XAML snippet for each off-card activity, keyed by activity class + package `major.minor` + date.
2. Error→root-cause→fix triples costing >1 validate attempt.
3. Cross-version package gotchas.

Never save project facts (paths, asset names, connections; use `project-context.md`), UIA selectors/targets/OR references (per-app), UIA CLI syntax (package-owned/co-versioned), `uip rpa` flag shapes or run/debug payload fields ([cli-reference.md](cli-reference.md) owns them; report gaps via `/uipath-feedback`), or secrets. Process-level UIA lessons, such as a failure mode and fix direction, may be saved.

**Expiry:** if a recalled snippet fails validation, delete or overwrite it and fall back to the Rule 21 triple.
