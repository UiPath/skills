# Execution Maps — Turn-Budgeted Build Journeys

One dense file, read once per build. Fixes which tool calls go in which assistant turn. Budgets (happy path, incl. final report): **greenfield ≤5 turns, brownfield ≤4**. One repair cycle adds ≤2. Each T-row = ONE assistant message: N tool calls in one message cost 1 turn, one call per message costs N.

> **Tool vocabulary.** Tool names use Claude Code conventions: `Edit` = in-place string replacement, `Write` = full-file write, `Read`/`Glob`/`Grep` = file read/search, `Bash` = shell. On another harness, map each to its equivalent. Harness cannot emit parallel tool calls → keep the same per-turn grouping as consecutive calls; the CLI chains still collapse round-trips.

## Source precedence — every activity you author

1. **Card** — [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md)
2. **Agent memory** — validated snippet from a prior session (see [§ Cross-session memory](#cross-session-memory))
3. **Rule 21 triple** — `activities find` → `<Activity>.md` read → `get-default-xaml`, fanned out inside T1/T2

`validate` + `build` gate all three. Card/memory hits skip discovery, never the gate.

## Gate ≠ runtime proof

A clean `validate` + `build` does NOT prove runtime behavior. Known silent failures pass BOTH: `InvokeCode` `Code` in child/CDATA form no-ops, `WriteTextFile` with explicit `Encoding` emits a BOM, a stripped UIA `N*` `Version` fails only at runtime ([xaml/common-pitfalls.md](xaml/common-pitfalls.md)). When the deliverable has observable outputs (files written, entry-point out-arguments) and runs without external systems or UI, the gate turn ends with ONE `uip rpa run` and the report turn checks the actual outputs — see the T3/T4 rows below.

## Sequential gates — never batch across these

- `templates search` → `init` (Rule 2): runs only when the user names a template or domain pattern; its result (possibly an `AskUserQuestion`) picks `--template-package-id`.
- Rule 2a framework/language question when the request carries no signal.
- Any `AskUserQuestion` or consent gate.
- UIA state advances and indication (see [§ Journey: UIA capture + build](#journey-uia-capture--build-xaml)) — capture screens are gated by real application state.

## Journey: Greenfield XAML (no UIA)

Skip the project-discovery subagent — nothing to discover yet ([environment-setup.md § Skip gate](environment-setup.md): no `project.json` before T1, only the untouched scaffold after it). Write `project-context.md` + `AGENTS.md` yourself at T4.

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `uip rpa init --name "<NAME>" --location "<PARENT_DIR>" --template-id BlankTemplate --expression-language <VisualBasic\|CSharp> --target-framework <Windows\|Portable> --output json` (Rule 2a — both flags explicit) `&&` `uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output markdown` `&&` one `uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json` per request-known package ∥ parallel `Read` — ALL THREE, never a subset (skipping the pattern card re-opens per-activity discovery): [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md), [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) (Rule 22) ∥ memory recall (harness has memory) ∥ Rule 21 `activities find` fan-out for off-card activities |
| **T2 — Author + install** | Design fork FIRST for row-processing tasks: complex bulk row processing (per-row parse + validate + branch + accumulate) escalates to code per [data-manipulation-guide.md § Code vs activity chains](data-manipulation-guide.md) — the pattern card's `ForEach` shapes cover only the simple one-`If`/`Switch` case. Then: one `Write` per workflow file — complete, all activities (Rule 18) ∥ `Read` `project.json` (anchors for the T2/T3 edits; skip re-reading scaffolded `Main.xaml` — the `Write` replaces it) ∥ `Edit` `project.json` (`fileInfoCollection` for test cases, Rule 10; `dependencies` stays CLI-owned via `packages install`) ∥ ONE `Bash`: `uip rpa packages install` for all needed packages at the T1-chosen versions — flag shape per [cli-reference.md § packages install](cli-reference.md#packages-install); it drifts across CLI builds, so on `Invalid packages input` re-check `uip rpa packages install --help` ∥ Rule 21 doc `Read`s + `get-default-xaml` for off-card activities |
| **T3 — Gate** | ONE `Bash`: `uip rpa validate --file-path "<RELATIVE_FILE>" --project-dir "<PROJECT_DIR>" --output markdown` per file `&&` `uip rpa build "<PROJECT_DIR>" --output markdown` `&&` — when outputs are observable and no external system/UI is needed — `uip rpa run` on the entry point (§ Gate ≠ runtime proof). `--file-path` RELATIVE to project dir — absolute paths falsely fail (separator bug, [cli-reference.md § validate](cli-reference.md#validate)) |
| **T4 — Report** | Check the T3 run's actual outputs against the request (files, out-arguments) BEFORE reporting — wrong/empty output with a clean gate is a silent-failure signature (§ Failure exits) + § Completion Output + write `project-context.md`/`AGENTS.md` + memory save ([§ Cross-session memory](#cross-session-memory)) |

- First chain call pays the cold Helm restore (30–90 s) — the chain hides it behind one turn; do not split to "check progress".
- `init` can return `success: false` yet create files (partial success) — before retrying, check `project.json` exists ([environment-setup.md](environment-setup.md)).
- Dependencies land via `packages install` only — never hand-edit `project.json` `dependencies`.

**Repair cycle (validate/build failure):** one turn — `Edit` fixes by error category (Rule 19 — Package first: a skipped `packages install` fails the gate before any activity issue); a gate failure on a card-covered activity does NOT reopen discovery (`activities find`/`get-default-xaml`) — recheck the card entry; next turn — re-run the T3 chain. >2 errors with ambiguous origin → bisect: stub out half the new activities, re-validate. Caps: 5 attempts per loop (Rule 3).

## Journey: Brownfield XAML edit

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Context** | SKILL.md § Precondition context check — the skip gate first, then the discovery subagent, which writes `project-context.md` + `AGENTS.md` itself ([environment-setup.md § Project Context Discovery](environment-setup.md)) ∥ `Read` `project.json` + target `.xaml` + cards ∥ ONE `Bash`: `analyzer-rules list --project-dir "<PROJECT_DIR>" --output markdown` ∥ memory recall ∥ off-card `activities find` fan-out |
| **T2 — Edit** | Batched `Edit`s (anchor each on its own target block — same-file Edits serialize; overlapping anchors fail) ∥ `packages install` `Bash` if new dependencies |
| **T3 — Gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` `&&` optional `run` per § Gate ≠ runtime proof |
| **T4 — Report** | Output check (if T3 ran) + § Completion Output + memory save |

## Journey: Greenfield coded

`init` always scaffolds XAML — same command as above; coded mode = add `.cs` files after ([environment-setup.md](environment-setup.md)).

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `init` (flags as XAML journey) `&&` `analyzer-rules list` `&&` `packages versions` per known package ∥ `Read` [assets/codedworkflow-template.md](../assets/codedworkflow-template.md) + [coded/operations-guide.md § Coding Guidelines](coded/operations-guide.md#coding-guidelines) ∥ memory recall |
| **T2 — Author + install** | `Write` each `.cs` (Rules 13–19) ∥ `Read` `project.json` ∥ `Edit` `project.json` (`entryPoints` Rule 15, `fileInfoCollection` Rule 10) ∥ `packages install` `Bash` ∥ `Read` `.local/docs/packages/<PackageId>/coded/coded-api.md` for installed services |
| **T3 — Gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` `&&` optional `run` per § Gate ≠ runtime proof |
| **T4 — Report** | Output check (if T3 ran) + § Completion Output + memory save |

## Journey: Brownfield coded edit

Brownfield XAML journey with coded reads: T1 `Read` target `.cs` + `.local/docs/.../coded/coded-api.md` for touched services; T2 `Edit`s ∥ install; T3 gate; T4 report.

## Journey: UIA capture + build (XAML)

Budget shape: **~3 fixed turns + ~3 turns per capture-screen + 2-turn debug cycle.** Capture is serialized ACROSS screens by application state (Complete-then-advance — the target-capture orchestration reference, routed from the UIA package guide) — never try to batch across an advance. Concrete UIA CLI syntax is package-owned — route from the package guide (`{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Documentation).

| Turn | Emit in ONE assistant message |
|---|---|
| **T0 — Reads + pre-flight** | Parallel `Read`: [uia-starter-guide.md](uia-starter-guide.md) + the UIA package's core guide (Rule 7, both in full) + the target-capture orchestration reference it mandates ∥ prerequisites check ([uia-starter-guide.md § UIA Prerequisites](uia-starter-guide.md), Rule 7a) ∥ ONE `Bash`: window baseline via the UIA snapshot CLI ∥ build the element inventory/checklist from the user's manual steps |
| **Per capture-screen** | (a) capture bundle — run the `uia-configure-target` flow for ALL of this screen's checklist elements in one pass, through OR registration; (b) ONE state advance via the interact CLI — only to reach the next screen, never to test behavior |
| **T-author — after ALL screens captured** | Scaffold/authoring prerequisites (Capture-First Fast Path order) ∥ batch-author every screen's activities in one pass (Rule 18), embed path for OR target attachment |
| **T-gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` |
| **Debug cycle (consent-gated, [uia-starter-guide.md § Running UI Automation Workflows](uia-starter-guide.md))** | ONE `Bash` chain: window baseline `&&` `debug start` `&&` `execution cancel` `&&` re-list windows; next turn: diff, close stray windows via the interact CLI, report |

- Default is author-once-after-capture — all OR refs are already in conversation. Fall back to per-screen authoring interleave only on long captures (5+ screens) where context pressure is real; the `validate`/`build` gate still runs ONCE at the end either way.
- Screens after the first (same window): carry the OR screen reference from the previous capture into the next `uia-configure-target` invocation — it skips the OR screen lookup. Invocation shape and argument: the package's `uia-configure-target` invocation guide (routed from the package guide § Documentation).
- Indication fallback (user physically clicks) and every interact advance are sequential gates — never batched, never parallel.
- Selector failures at debug time → the recover selector flow (never hand-edit selectors).

## Failure exits

| Symptom | Open |
|---|---|
| `validate` structural/reference errors | [cli-reference.md § Validation Iteration Loop](cli-reference.md#validation-iteration-loop) |
| XAML activity gotcha (property conflicts, scope) | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) |
| Gate clean but runtime output wrong/empty | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) silent-failure sections: § InvokeCode Code Property — Attribute Form Only, § WriteTextFile Emits a UTF-8 BOM, § UIA `N*` Activities Carry a `Version` |
| Coded `CS*` errors | [coded/operations-guide.md § Common Issues and Fixes](coded/operations-guide.md#common-issues-and-fixes) |
| CLI error (`timeout`, `EPIPE`, `401`, `not in the project folder`) | [cli-reference.md § CLI Error Recovery](cli-reference.md#cli-error-recovery) |
| Card snippet rejected by validate/build | Fall back to Rule 21 triple for that activity; report stale entry via `/uipath-feedback` |
| UIA selector fails at debug time | Recover selector flow per [uia-starter-guide.md § Runtime Selector Failure Recovery](uia-starter-guide.md#runtime-selector-failure-recovery) — never hand-edit |

## Cross-session memory

Harness-conditional: engage only when the harness provides persistent memory; otherwise skip silently.

**Recall — T1 of every journey.** Match saved entries by activity class + package `major.minor`. Hit ⇒ that activity skips the Rule 21 triple. `validate`/`build` still gate.

**Save — after project `build` is clean (T4).** Save only:

1. Validated XAML snippet per off-card activity — key: activity class + package `major.minor` + date.
2. Error→root-cause→fix triples that cost >1 validate attempt.
3. Cross-version package gotchas.

**Never save:** project-specific facts (paths, asset names, connections — belong in `project-context.md`), UIA selectors/targets/OR references (per-app), UIA CLI syntax (package-owned, co-versioned), secrets. Process-level UIA lessons (e.g., a failure mode and its fix direction) MAY be saved.

**Expiry:** recalled snippet fails validation → delete/overwrite that entry, fall back to Rule 21 triple.
