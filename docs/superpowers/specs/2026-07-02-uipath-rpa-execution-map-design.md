# uipath-rpa Execution Map — Design

**Date:** 2026-07-02
**Status:** Draft — awaiting user review
**Scope:** `skills/uipath-rpa` only (first pilot; other skills follow later)

## Problem

Building anything with `uipath-rpa` costs 12–20+ assistant turns and many `uip` CLI calls. Cost drivers, with current-state anchors:

1. **Discovery CLI round-trips** — per-activity triple (`activities find` → read `<Activity>.md` → `get-default-xaml`) per Rule 21; `analyzer-rules list`; `packages versions/install`; each heavy call pays a ~22s Studio cold start (SKILL.md § Session Pre-warm).
2. **Reference reading** — several read-in-full mandates (`xaml-basics-and-rules.md`, `workflow-guide.md`, …) before authoring anything.
3. **One-activity-at-a-time authoring** — XAML Rule 18: "build one activity at a time, validate after each addition" → N activities ≈ N validate turns.
4. **Turn serialization** — SKILL.md § Call Batching covers only two batch points; no end-to-end turn plan. `uipath-maestro-flow` already solved this with rule #10 + a "Three-turn execution map" (`greenfield.md`); `uipath-rpa` has no equivalent.
5. **Precondition overhead** — project-discovery subagent round-trip even for greenfield builds where no project exists yet.

## Goals & success criteria

1. **Canonical greenfield XAML build (3–5 non-UIA activities): ≤5 assistant turns happy path** (including final report), ≤8 `uip` invocations, `validate` + `build` clean. One repair cycle adds ≤2 turns.
2. Brownfield edit (add/modify 1–3 activities): ≤4 turns.
3. Enforced by a coder-eval smoke task with a `max_turns` budget (see § Testing).
4. SKILL.md net size does not grow by more than ~10 lines — new content lives in `references/`.

## Non-goals

- UI Automation journeys. Capture is interactive and app-state-serialized by nature; UIA package details are forbidden in this skill per `skills/uipath-rpa/CLAUDE.md`. UIA keeps its read-in-full mandates (Rules 7/7a) untouched.
- Other skills (maestro-flow deepening, agents, api-workflow) — later phases.
- A repo-shipped machine-generated full activity catalog (rejected — see § Alternatives).
- Weakening the final quality gate: per-file `validate` clean + project `build` clean remain mandatory before "done".

## Decisions log

| Decision | Choice | Source |
|---|---|---|
| Primary target | File reads + CLI round trips + one-at-a-time loop + pattern memorization | user |
| Scope | `uipath-rpa` only first | user |
| Memorization mechanisms | Cross-session agent memory + in-context one-dense-map-file | user |
| Validate-loop relaxation | **Author-all, validate-once, bisect on failure** | **agent-substituted (user AFK) — confirm at review** |
| Turn budget numbers | ≤5 greenfield / ≤4 brownfield | agent-proposed — confirm at review |

## Design

Four components. All new prose follows `.claude/rules/token-optimization.md`.

### 1. Execution maps — `references/execution-maps-guide.md` (new)

One dense file the agent reads once per build ("in-context memorization"). Four journeys:

- **Greenfield XAML** (no UIA)
- **Brownfield XAML edit**
- **Greenfield coded**
- **Brownfield coded edit**

Each journey carries:

- **Turn table** (T1/T2/T3/T4), maestro-flow style: exactly which tool calls go in ONE assistant message per turn.
- **Canonical T1 chain** — one `Bash`: pre-warm `&` + `uip rpa init` (with `--target-framework`/`--expression-language` per Rule 2a) `&&` `analyzer-rules list` `&&` `packages versions/install` for request-known packages; parallel `Read`s of the activity card, pattern card, and journey-relevant reference sections.
- **Scoped read list** — the minimal references REQUIRED for the happy path (the map + cards replace full reads of `workflow-guide.md`/`xaml-basics-and-rules.md` for card/pattern-covered work); explicit failure exits name which reference to open when leaving the happy path (validate errors → `validation-guide.md`; activity gotcha → `xaml/common-pitfalls.md`; off-card activity → Rule 21 triple).
- **Decision gates that must stay sequential** — `templates search` → `init` (Rule 2), any `AskUserQuestion`, UIA capture (out of scope → route to Rule 7 flow).
- **Tool-vocabulary note** cloned from maestro-flow SKILL.md so maps stay harness-portable.

Happy-path turn shape (greenfield XAML):

| Turn | Emits |
|---|---|
| T1 | Pre-warm + init/analyzer/packages chain (one `Bash`) ∥ card + pattern-card `Read`s |
| T2 | Author complete workflow — one `Write` of `Main.xaml` (or batched `Edit`s) ∥ `project.json` edits |
| T3 | One `Bash`: `validate --file-path` per file `&&` `build` |
| T4 | Completion report (SKILL.md § Completion Output) |

`Read` of scaffolded files is unnecessary when authoring via full `Write` and init flags were explicit (expression language/target framework already known).

### 2. Pattern card — `references/common-pattern-card.md` (new)

Extends the proven `common-activity-card.md` mechanism from single activities to **multi-activity patterns**. Structure mirrors the activity card: package anchor + verified version per entry, property-complete snippet, variables block, notes, long-form pointer.

- **Candidate patterns (~12 initial):** Excel read-range→for-each-row→write-range; CSV read/write; text file read/write/append; file ops (exists/copy/move/delete); HTTP request + JSON deserialize; send mail (SMTP, with Outlook/O365 variant notes); DataTable build/filter/add-row; queue produce (AddQueueItem) and consume loop (GetTransactionItem + SetTransactionStatus); RetryScope wrap; InvokeWorkflowFile with arguments. Final list picked at implementation by frequency in `tests/tasks/uipath-rpa/` + known top user asks.
- **Supersession rule:** for a card-listed pattern, skip the Rule 21 discovery triple for every activity inside the pattern snippet. Precedence: **activity/pattern card → agent memory → Rule 21 triple**.
- **Staleness guard:** every entry stamps package id + verified version. `validate`/`build` is the runtime guard — on rejection of a card snippet, fall back to the Rule 21 triple for that activity and report the stale entry (`/uipath-feedback` + repo issue).
- **Maintenance:** `.maintenance/pattern-card-maintenance.md` documents regeneration: scratch project, author each pattern, `validate` + `build` clean, update version stamps. Manual, human-reviewed — no build system (repo rule).
- UIA activities stay off-card (CLAUDE.md boundary).

### 3. Batch authoring + single validation gate (Rule 18 rewrite)

Replace XAML Rule 18 "Start minimal, iterate to correct — one activity at a time, validate after each addition" with:

> **[XAML] Batch-author, single gate.** Author the complete workflow in one pass. Then per-file `validate` to clean, then one project `build` (Rule 3 cadence otherwise unchanged, 5-attempt caps stay). On validate/build failure: fix by error category (Rule 19); if the offending activity is ambiguous across >2 errors, bisect — re-validate with half the new activities stubbed out. Card/pattern/memory-sourced activities carry low hallucination risk; this is what makes batch authoring safe.

Companion edits: SKILL.md § Call Batching "per-file validate / per-activity authoring loop" do-not-batch bullet is superseded; § Call Batching itself collapses to a pointer at the execution maps (keeping the sequential-by-design gates list).

### 4. Cross-session memory protocol (section inside execution-maps-guide.md)

Harness-conditional — engages only when the harness provides persistent memory; silently skipped otherwise (graceful degradation, per repo self-containment rules).

- **Save, after project `build` is clean:** (a) validated XAML snippet per off-card activity, keyed by activity class + package major.minor + date; (b) error→root-cause→fix triples that cost >1 validate attempt; (c) cross-version gotchas.
- **Recall, at authoring-phase start:** match by activity class + package major. Hit ⇒ skip `find`/`get-default-xaml`/doc read for that activity. `validate` + `build` still gate everything — memory never bypasses validation.
- **Never memorize:** project-specific facts (paths, asset names, connections — those belong in `project-context.md`), anything UIA (selectors/targets are per-app; CLAUDE.md boundary), secrets.
- **Expiry:** on validation failure of a recalled snippet, delete/overwrite that memory entry.

### SKILL.md integration (target net delta ≈ 0; hard cap +10 lines per Goals #4)

1. § Call Batching → replaced by short § Execution Maps routing to the new guide (shorter than current text).
2. Rule 18 rewritten (component 3).
3. Rule 21 amended: pattern card added as an allowlist source; card → memory → triple precedence.
4. § Precondition: greenfield (no `project.json` found) skips the discovery subagent; agent writes `project-context.md` itself at completion from what it just created.
5. § Completion Output: add conditional "save memory entries" step.
6. Task Navigation: one new row for the execution maps guide.

## Error handling & risks

| Risk | Mitigation |
|---|---|
| Stale card/pattern snippet vs installed package | Version stamp per entry; `validate`/`build` runtime guard; fallback to Rule 21 triple; staleness report path |
| Batch-author failure harder to localize | Error-category fix flow (Rule 19) + bounded bisect; 5-attempt caps unchanged |
| Stale memory across package versions | Keys include package major.minor; validation gate; delete-on-failure expiry |
| Map contradicts existing rules | Implementation pass audits every SKILL.md rule cross-reference; maps cite rules, never restate them |
| Harness without memory/parallel-tool support | Memory protocol conditional; maps state per-turn intent so serial harnesses still minimize CLI calls |
| SKILL.md bloat | Hard budget: net ≤ +10 lines |

## Testing

Per `.claude/rules/test-writing.md` workflow (`/test-coverage` → `/generate-task` → `/lint-task` → run):

1. **New smoke task** `tests/tasks/uipath-rpa/...`: canonical greenfield XAML build with a `max_turns` override enforcing the turn budget; criteria: workflow file exists with expected activities (`file_contains`), `validate` and `build` executed clean (`command_executed`), `--output json` usage check.
2. **Baseline:** run the same prompt against the pre-change skill once to record current turn count in the PR (before/after claim).
3. Existing uipath-rpa tasks re-run to catch regressions from the Rule 18/21 changes.

## Alternatives considered

- **B — Batching-only port of maestro-flow rule #10.** Rejected as insufficient: leaves discovery triples, read-in-full cost, and the per-activity validate loop untouched (user asked for all four cost classes).
- **C — Repo-shipped machine-generated activity catalog JSON (full property surfaces).** Rejected: drifts against per-project installed package versions; heavy regeneration burden; contradicts the co-versioned-docs philosophy in `skills/uipath-rpa/CLAUDE.md`. The human-verified pattern card + validation guard captures most of the value at a fraction of the risk.

## Open questions for review

1. Validate-loop choice: confirm **author-all/validate-once** over the tiered variant (card-known batch freely, unknown activities keep incremental loop). Agent-substituted while you were AFK.
2. Turn budgets (≤5 greenfield / ≤4 brownfield) — right bar?
3. Initial pattern list (~12 candidates above) — additions/removals?
4. OK to skip the project-discovery subagent for greenfield builds?
