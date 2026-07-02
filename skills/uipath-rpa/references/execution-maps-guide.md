# Execution Maps — Turn-Budgeted Build Journeys

One dense file, read once per build. Fixes which tool calls go in which assistant turn. Budgets (happy path, incl. final report): **greenfield ≤5 turns, brownfield ≤4**. One repair cycle adds ≤2.

> **Tool vocabulary.** Tool names use Claude Code conventions: `Edit` = in-place string replacement, `Write` = full-file write, `Read`/`Glob`/`Grep` = file read/search, `Bash` = shell. On another harness, map each to its equivalent. Harness cannot emit parallel tool calls → keep the same per-turn grouping as consecutive calls; the CLI chains still collapse round-trips.

## Source precedence — every activity you author

1. **Card** — [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md)
2. **Agent memory** — validated snippet from a prior session (see [§ Cross-session memory](#cross-session-memory))
3. **Rule 21 triple** — `activities find` → `<Activity>.md` read → `get-default-xaml`, fanned out inside T1/T2

`validate` + `build` gate all three. Card/memory hits skip discovery, never the gate.

## Sequential gates — never batch across these

- `templates search` → `init` (Rule 2): runs only when the user names a template or domain pattern; its result (possibly an `AskUserQuestion`) picks `--template-package-id`.
- Rule 2a framework/language question when the request carries no signal.
- Any `AskUserQuestion` or consent gate.
- UIA state advances and indication (see [§ Journey: UIA capture + build](#journey-uia-capture--build-xaml)) — capture screens are gated by real application state.

## Journey: Greenfield XAML (no UIA)

Skip the project-discovery subagent — no project exists (SKILL.md § Precondition). Write `project-context.md` + `AGENTS.md` yourself at T4.

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `uip rpa init --name "<NAME>" --location "<PARENT_DIR>" --template-id BlankTemplate --expression-language <VisualBasic\|CSharp> --target-framework <Windows\|Portable> --output json` (Rule 2a — both flags explicit) `&&` `uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json` `&&` one `uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json` per request-known package ∥ parallel `Read`: [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md), [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) (Rule 22) ∥ memory recall (harness has memory) ∥ Rule 21 `activities find` fan-out for off-card activities |
| **T2 — Author + install** | One `Write` per workflow file — complete, all activities (Rule 18) ∥ `Read` `project.json` (anchors for the T2/T3 edits; skip re-reading scaffolded `Main.xaml` — the `Write` replaces it) ∥ `Edit` `project.json` (`fileInfoCollection` for test cases, Rule 10; `dependencies` stays CLI-owned via `packages install`) ∥ ONE `Bash`: `uip rpa packages install` for all needed packages at the T1-chosen versions — flag shape per [cli-reference.md § packages install](cli-reference.md#packages-install); it drifts across CLI builds, so on `Invalid packages input` re-check `uip rpa packages install --help` ∥ Rule 21 doc `Read`s + `get-default-xaml` for off-card activities |
| **T3 — Gate** | ONE `Bash`: `uip rpa validate --file-path "<RELATIVE_FILE>" --project-dir "<PROJECT_DIR>" --output json` per file `&&` `uip rpa build "<PROJECT_DIR>" --output json`. `--file-path` RELATIVE to project dir — absolute paths falsely fail (separator bug, [cli-reference.md § validate](cli-reference.md#validate)) |
| **T4 — Report** | § Completion Output + write `project-context.md`/`AGENTS.md` + memory save ([§ Cross-session memory](#cross-session-memory)) |

- First chain call pays the cold Helm restore (30–90 s) — the chain hides it behind one turn; do not split to "check progress".
- `init` can return `success: false` yet create files (partial success) — before retrying, check `project.json` exists ([environment-setup.md](environment-setup.md)).
- Dependencies land via `packages install` only — never hand-edit `project.json` `dependencies`.

**Repair cycle (validate/build failure):** one turn — `Edit` fixes by error category (Rule 19); next turn — re-run the T3 chain. >2 errors with ambiguous origin → bisect: stub out half the new activities, re-validate. Caps: 5 attempts per loop (Rule 3).

## Journey: Brownfield XAML edit

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Context** | § Precondition context check ∥ `Read` `project.json` + target `.xaml` + cards ∥ ONE `Bash`: `analyzer-rules list --project-dir "<PROJECT_DIR>" --output json` ∥ memory recall ∥ off-card `activities find` fan-out |
| **T2 — Edit** | Batched `Edit`s (anchor each on its own target block — same-file Edits serialize; overlapping anchors fail) ∥ `packages install` `Bash` if new dependencies |
| **T3 — Gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` |
| **T4 — Report** | § Completion Output + memory save |

## Journey: Greenfield coded

`init` always scaffolds XAML — same command as above; coded mode = add `.cs` files after ([environment-setup.md](environment-setup.md)).

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `init` (flags as XAML journey) `&&` `analyzer-rules list` `&&` `packages versions` per known package ∥ `Read` [assets/codedworkflow-template.md](../assets/codedworkflow-template.md) + [coded/coding-guidelines.md](coded/coding-guidelines.md) ∥ memory recall |
| **T2 — Author + install** | `Write` each `.cs` (Rules 13–19) ∥ `Read` `project.json` ∥ `Edit` `project.json` (`entryPoints` Rule 15, `fileInfoCollection` Rule 10) ∥ `packages install` `Bash` ∥ `Read` `.local/docs/packages/<PackageId>/coded/coded-api.md` for installed services |
| **T3 — Gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` |
| **T4 — Report** | § Completion Output + memory save |

## Journey: Brownfield coded edit

Brownfield XAML journey with coded reads: T1 `Read` target `.cs` + `.local/docs/.../coded/coded-api.md` for touched services; T2 `Edit`s ∥ install; T3 gate; T4 report.

## Journey: UIA capture + build (XAML)

Budget shape: **~3 fixed turns + ~3 turns per capture-screen + 2-turn debug cycle.** Capture is serialized ACROSS screens by application state (Complete-then-advance, [uia-configure-target-workflows.md](uia-configure-target-workflows.md)) — never try to batch across an advance. Concrete UIA CLI syntax is package-owned: `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/references/cli-reference.md`.

| Turn | Emit in ONE assistant message |
|---|---|
| **T0 — Reads + pre-flight** | Parallel `Read`: [ui-automation-guide.md](ui-automation-guide.md) + [uia-configure-target-workflows.md](uia-configure-target-workflows.md) (Rule 7, in full) + package skill docs (`.local/docs/.../skills/uia-configure-target/{SKILL,USAGE}.md`) ∥ prerequisites check ([uia-prerequisites.md](uia-prerequisites.md)) ∥ ONE `Bash`: window baseline via the UIA snapshot CLI ∥ build the element inventory/checklist from manual steps ([ui-automation-guide.md § Capturing from Manual Test Steps](ui-automation-guide.md)) |
| **Per capture-screen** | (a) capture bundle — run the `uia-configure-target` flow for ALL of this screen's checklist elements in one pass (batch `\|` pattern; per-screen batched OR entry points), through OR registration; (b) ONE state advance via the interact CLI — only to reach the next screen, never to test behavior |
| **T-author — after ALL screens captured** | Scaffold/authoring prerequisites (Capture-First Fast Path order) ∥ batch-author every screen's activities in one pass (Rule 18), embed path for OR target attachment |
| **T-gate** | ONE `Bash`: per-file `validate` (relative `--file-path`) `&&` `build` |
| **Debug cycle (consent-gated, § Running UI Automation Workflows)** | ONE `Bash` chain: window baseline `&&` `debug start` `&&` `execution cancel` `&&` re-list windows; next turn: diff, close stray windows via the interact CLI, report |

- Default is author-once-after-capture — all OR refs are already in conversation. Fall back to per-screen authoring interleave only on long captures (5+ screens) where context pressure is real; the `validate`/`build` gate still runs ONCE at the end either way.
- Indication fallback (user physically clicks) and every interact advance are sequential gates — never batched, never parallel.
- Selector failures at debug time → the `uia-improve-selector` flow (never hand-edit selectors).

## Failure exits

| Symptom | Open |
|---|---|
| `validate` structural/reference errors | [validation-guide.md](validation-guide.md) |
| XAML activity gotcha (property conflicts, scope) | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) |
| Coded `CS*` errors | [coded/coding-guidelines.md § Common Issues](coded/coding-guidelines.md) |
| CLI error (`timeout`, `EPIPE`, `401`, `not in the project folder`) | [cli-reference.md § CLI Error Recovery](cli-reference.md#cli-error-recovery) |
| Card snippet rejected by validate/build | Fall back to Rule 21 triple for that activity; report stale entry via `/uipath-feedback` |
| UIA selector fails at debug time | `uia-improve-selector` flow per [ui-automation-guide.md § Runtime Selector Failure Recovery](ui-automation-guide.md) — never hand-edit |

## Cross-session memory

Harness-conditional: engage only when the harness provides persistent memory; otherwise skip silently.

**Recall — T1 of every journey.** Match saved entries by activity class + package `major.minor`. Hit ⇒ that activity skips the Rule 21 triple. `validate`/`build` still gate.

**Save — after project `build` is clean (T4).** Save only:

1. Validated XAML snippet per off-card activity — key: activity class + package `major.minor` + date.
2. Error→root-cause→fix triples that cost >1 validate attempt.
3. Cross-version package gotchas.

**Never save:** project-specific facts (paths, asset names, connections — belong in `project-context.md`), UIA selectors/targets/OR references (per-app), UIA CLI syntax (package-owned, co-versioned), secrets. Process-level UIA lessons (e.g., a failure mode and its fix direction) MAY be saved.

**Expiry:** recalled snippet fails validation → delete/overwrite that entry, fall back to Rule 21 triple.
