# uipath-rpa Execution Maps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut a canonical uipath-rpa greenfield build from 12–20+ assistant turns to ≤5 (brownfield ≤4) via journey execution maps, a pre-validated pattern card, batch authoring with a single validation gate, and a cross-session memory protocol.

**Architecture:** Four additions to `skills/uipath-rpa/`: (1) `references/execution-maps-guide.md` — one dense per-journey turn plan incl. the memory protocol; (2) `references/common-pattern-card.md` — multi-activity pre-validated XAML snippets extending the proven `common-activity-card.md` mechanism; (3) SKILL.md surgical edits (Rule 18 rewrite, Call Batching → Execution Maps, Rule 21 precedence, greenfield precondition skip, completion memory step); (4) a coder-eval smoke task enforcing the turn budget. Spec: `docs/superpowers/specs/2026-07-02-uipath-rpa-execution-map-design.md`.

**Tech Stack:** Markdown skill docs, `uip` CLI (local 1.0.0-alpha, verified present), coder-eval task YAML, repo validation scripts (`hooks/validate-skill-descriptions.sh`, `scripts/check-skill-status.py`, `scripts/check-cli-verbs.py`), repo slash commands (`/test-coverage`, `/generate-task`, `/lint-task`).

**Execution autonomy: autonomous**

**Stop conditions:**
- `uip rpa init`/`validate`/`build` unusable locally (CLI errors unrelated to authored content) → pattern-card entries cannot be verified; stop card tasks, finish remaining tasks, report.
- A SKILL.md `old_string` no longer matches (upstream drift) → stop that edit, re-read SKILL.md, adapt, continue.

## Global Constraints

- All new prose follows `.claude/rules/token-optimization.md` (terse mode) and `.claude/rules/content-quality.md`.
- SKILL.md hard cap: net ≤ +10 lines (spec Goals #4). Measure with `git diff --stat` at Task 2 end.
- No UIA subcommands/flags/artifact names anywhere (per `skills/uipath-rpa/CLAUDE.md`). UIA activities stay off all cards.
- Skill stays self-contained: no reads of other skills' files; links relative to file location and must resolve.
- Every card snippet MUST be validated by `uip rpa validate` + `uip rpa build` in the scratch project before it enters the card. Unverified entries are dropped, never stamped.
- CLI examples use `--output json` when output is parsed; placeholders `<UPPER_SNAKE_CASE>`.
- Scratch project lives in the session scratchpad dir, never committed.
- Commit after each task; branch `feat/uipath-rpa-execution-maps` (already created, spec committed).

---

### Task 1: Create `references/execution-maps-guide.md`

**Files:**
- Create: `skills/uipath-rpa/references/execution-maps-guide.md`
- Read first (sourcing): `skills/uipath-rpa/references/cli-reference.md` (init/validate/build/packages/analyzer-rules sections), `skills/uipath-rpa/references/environment-setup.md` (§ Template selection)

**Interfaces:**
- Produces: file path `references/execution-maps-guide.md` with anchors `#cross-session-memory` and `#failure-exits` — Tasks 2 and 6 link to them.

- [ ] **Step 1: Source exact CLI syntax.** Read `references/cli-reference.md` and `references/environment-setup.md`. Transcribe exact flags for: `uip rpa init`, `analyzer-rules list`, `packages versions`, `packages install`, `validate`, `build`. Where the draft below disagrees with cli-reference.md, cli-reference.md wins.

- [ ] **Step 2: Write the file.** Content (adjust command syntax per Step 1; keep structure and rule citations):

````markdown
# Execution Maps — Turn-Budgeted Build Journeys

One dense file, read once per build. Fixes which tool calls go in which assistant turn. Budgets (happy path, incl. final report): **greenfield ≤5 turns, brownfield ≤4**. One repair cycle adds ≤2.

> **Tool vocabulary.** Tool names use Claude Code conventions: `Edit` = in-place string replacement, `Write` = full-file write, `Read`/`Glob`/`Grep` = file read/search, `Bash` = shell. On another harness, map each to its equivalent. Harness cannot emit parallel tool calls → keep the same per-turn grouping as consecutive calls; the CLI chains still collapse round-trips.

## Source precedence — every activity you author

1. **Card** — [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md)
2. **Agent memory** — validated snippet from a prior session (see [§ Cross-session memory](#cross-session-memory))
3. **Rule 21 triple** — `activities find` → `<Activity>.md` read → `get-default-xaml`, fanned out in T1

`validate` + `build` gate all three. Card/memory hits skip discovery, never the gate.

## Sequential gates — never batch across these

- `templates search` → `init` (Rule 2): search result (possibly an `AskUserQuestion`) picks `--template-package-id`.
- Rule 2a framework/language question when the request carries no signal.
- Any `AskUserQuestion` or consent gate.
- UIA capture (Rule 7) — out of map scope entirely; UIA journeys keep their own flow.

## Journey: Greenfield XAML (no UIA)

Skip the project-discovery subagent — no project exists (SKILL.md § Precondition). Write `project-context.md` + `AGENTS.md` yourself at T4.

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `uip rpa init` (explicit `--target-framework`, `--expression-language`, Rule 2a) `&&` `analyzer-rules list --project-dir` `&&` one `packages versions --include-prerelease` per request-known package ∥ parallel `Read`: [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md), [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) (Rule 22) ∥ memory recall (if harness has memory) ∥ Rule 21 `find` fan-out for any off-card activity |
| **T2 — Author + install** | One `Write` per workflow file — complete, all activities (Rule 18) ∥ `Edit` `project.json` (`fileInfoCollection` for test cases, Rule 10) ∥ ONE `Bash`: `packages install` per package, version from T1 `versions` output ∥ Rule 21 doc `Read`s + `get-default-xaml` for off-card activities |
| **T3 — Gate** | ONE `Bash`: `validate --file-path "<FILE>" --project-dir "<PROJECT_DIR>" --output json` per file `&&` `build "<PROJECT_DIR>" --output json` |
| **T4 — Report** | § Completion Output + write `project-context.md`/`AGENTS.md` + memory save ([§ Cross-session memory](#cross-session-memory)) |

No `Read` of scaffolded files in T2: init flags were explicit, so `expressionLanguage`/`targetFramework` are known; full-file `Write` replaces scaffolded `Main.xaml`.

**Repair cycle (validate/build failure):** one turn — `Edit` fixes by error category (Rule 19); next turn — re-run the T3 chain. >2 errors with ambiguous origin → bisect: stub out half the new activities, re-validate. Caps: 5 attempts per loop (Rule 3).

## Journey: Brownfield XAML edit

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Context** | § Precondition context check ∥ `Read` `project.json` + target `.xaml` + cards ∥ ONE `Bash`: `analyzer-rules list` ∥ memory recall ∥ off-card `find` fan-out |
| **T2 — Edit** | Batched `Edit`s (anchor each on its own target block — same-file Edits serialize; overlapping anchors fail) ∥ `packages install` `Bash` if new dependencies |
| **T3 — Gate** | ONE `Bash`: per-file `validate` `&&` `build` |
| **T4 — Report** | § Completion Output + memory save |

## Journey: Greenfield coded

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | ONE `Bash` chain: `init` `&&` `analyzer-rules list` `&&` `packages versions` per known package ∥ `Read` [assets/codedworkflow-template.md](../assets/codedworkflow-template.md) + [coded/coding-guidelines.md](coded/coding-guidelines.md) + `.local/docs/.../coded/coded-api.md` for known packages ∥ memory recall |
| **T2 — Author + install** | `Write` each `.cs` (Rules 13–19) ∥ `Edit` `project.json` (`entryPoints` Rule 15, `fileInfoCollection` Rule 10) ∥ `packages install` `Bash` |
| **T3 — Gate** | ONE `Bash`: per-file `validate` `&&` `build` |
| **T4 — Report** | § Completion Output + memory save |

## Journey: Brownfield coded edit

Same as brownfield XAML with coded reads: T1 `Read` target `.cs` + `coded-api.md` for touched services; T2 `Edit`s ∥ install; T3 gate; T4 report.

## Failure exits

| Symptom | Open |
|---|---|
| `validate` structural/reference errors | [validation-guide.md](validation-guide.md) |
| XAML activity gotcha (property conflicts, scope) | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) |
| Coded `CS*` errors | [coded/coding-guidelines.md § Common Issues](coded/coding-guidelines.md) |
| Card snippet rejected by validate/build | Fall back to Rule 21 triple for that activity; report stale entry via `/uipath-feedback` |
| Anything UIA | Rule 7 flow — leave this map |

## Cross-session memory

Harness-conditional: engage only when the harness provides persistent memory; otherwise skip silently.

**Recall — T1 of every journey.** Match saved entries by activity class + package `major.minor`. Hit ⇒ that activity skips the Rule 21 triple. `validate`/`build` still gate.

**Save — after project `build` is clean (T4).** Save only:
1. Validated XAML snippet per off-card activity — key: activity class + package `major.minor` + date.
2. Error→root-cause→fix triples that cost >1 validate attempt.
3. Cross-version package gotchas.

**Never save:** project-specific facts (paths, asset names, connections — belong in `project-context.md`), anything UIA (selectors/targets are per-app), secrets.

**Expiry:** recalled snippet fails validation → delete/overwrite that entry, fall back to Rule 21 triple.
````

- [ ] **Step 3: Verify links resolve.**

Run: `cd skills/uipath-rpa/references && for f in common-activity-card.md common-pattern-card.md xaml/xaml-basics-and-rules.md validation-guide.md xaml/common-pitfalls.md coded/coding-guidelines.md ../assets/codedworkflow-template.md; do [ -f "$f" ] || echo "MISSING $f"; done`
Expected: only `MISSING common-pattern-card.md` (created in Task 3 — acceptable forward link within this branch; re-run after Task 3 with zero output).

- [ ] **Step 4: Verify no retired verbs / no UIA leakage.**

Run: `python3 scripts/check-cli-verbs.py 2>/dev/null || true` and `grep -nE 'interact click|interact type|snapshot capture|Target_Definition|indicate-element|TARGET-[0-9]' skills/uipath-rpa/references/execution-maps-guide.md`
Expected: no matches from the grep; check-cli-verbs reports no new findings.

- [ ] **Step 5: Commit.**

```bash
git add skills/uipath-rpa/references/execution-maps-guide.md
git commit -m "feat(uipath-rpa): add execution maps guide — turn-budgeted build journeys"
```

---

### Task 2: SKILL.md integration edits

**Files:**
- Modify: `skills/uipath-rpa/SKILL.md` (7 surgical edits, A–G)

**Interfaces:**
- Consumes: `references/execution-maps-guide.md` (Task 1), anchor `#cross-session-memory`.
- Produces: Rule 18 new text and § Execution Maps section that Task 6's eval prompt relies on behaviorally.

- [ ] **Step 1: Edit A — Rule 18 rewrite.**

old_string:
```
18. **[XAML] Start minimal, iterate to correct** — build one activity at a time, validate after each addition.
```
new_string:
```
18. **[XAML] Batch-author, single gate** — author the complete workflow in one pass, sourcing each activity card → memory → Rule 21 triple (precedence in [execution-maps-guide.md](references/execution-maps-guide.md)). Then per-file `validate` to clean, then one project `build` (Rule 3 cadence, 5-attempt caps unchanged). On failure: fix by error category (Rule 19); >2 errors with ambiguous origin → bisect (stub out half the new activities, re-validate).
```

- [ ] **Step 2: Edit B — replace § Call Batching with § Execution Maps.** Replace the entire section from the `### Call Batching (Both Modes)` heading up to (not including) `### Coded-Specific Rules` with:

```
### Execution Maps (Both Modes)

**Follow the journey map in [execution-maps-guide.md](references/execution-maps-guide.md) for every build or edit** — it fixes which tool calls batch into which assistant turn (greenfield ≤5 turns, brownfield ≤4). Within a turn: chain dependent `uip` calls with `&&` in one `Bash`; emit independent `Bash`/`Read`/`Edit` calls as parallel tool uses. Split turns only where a call needs an earlier call's stdout or a file mutation. Rule 21 discovery for off-card activities fans out inside T1/T2 — all K `find`s parallel, then all K doc `Read`s, then all K `get-default-xaml`s — never one activity at a time.

**Sequential by design — never batch across:** `templates search` → `init` (Rule 2 decision gate); any `AskUserQuestion` or consent gate; UIA capture flows (Rule 7).
```

- [ ] **Step 3: Edit C — Rule 21 card bullet gains pattern card + memory precedence.**

old_string:
```
    - **Card-listed activities:** check [references/common-activity-card.md](references/common-activity-card.md) first; if the activity is on the card, author from the card entry alone — skip `activities find`, skip `activities get-default-xaml`, skip the per-activity MD read.
```
new_string:
```
    - **Card-listed activities and patterns:** check [references/common-activity-card.md](references/common-activity-card.md) and [references/common-pattern-card.md](references/common-pattern-card.md) first; on a card hit, author from the card entry alone — skip `activities find`, skip `activities get-default-xaml`, skip the per-activity MD read. Precedence: card → agent memory ([execution-maps-guide.md § Cross-session memory](references/execution-maps-guide.md#cross-session-memory)) → full triple. A memory hit substitutes for the triple only; `validate`/`build` still gate.
```

- [ ] **Step 4: Edit D — greenfield skips discovery agent.**

old_string:
```
**If the file does NOT exist** → run the discovery flow below.
```
new_string:
```
**If the file does NOT exist** → if a `project.json` exists, run the discovery flow below. **Greenfield (no `project.json`): skip the discovery agent** — nothing to discover. After the build completes, write both context files yourself (step 3 below) from what you just created: structure, dependencies, entry points.
```

- [ ] **Step 5: Edit E — Rule 4 cadence alignment.**

old_string:
```
4. **ALWAYS validate files as you go AND verify the project builds before declaring done.** After every create or edit: per-file `validate` to clean.
```
new_string:
```
4. **ALWAYS bring every touched file to per-file `validate` clean AND verify the project builds before declaring done.** Cadence per Rule 18: batch-author, then validate.
```
(If the exact sentence differs, adapt: keep the "validate clean + build mandatory" meaning, drop "after every create or edit".)

- [ ] **Step 6: Edit F — Completion Output memory step.** After the numbered pre-report list (item 4, "If the plan is fully checked off…"), insert:

```
Then, if the harness provides persistent memory, save validated patterns per [execution-maps-guide.md § Cross-session memory](references/execution-maps-guide.md#cross-session-memory) before reporting.
```

- [ ] **Step 7: Edit G — Task Navigation row.** Insert as the second row of the Task Navigation table (after the header separator and the Legacy row):

```
| **Plan the build's turn structure** | Both | [execution-maps-guide.md](references/execution-maps-guide.md) — read first for any build/edit journey |
```

- [ ] **Step 8: Verify size budget + frontmatter + links.**

Run: `git diff --stat skills/uipath-rpa/SKILL.md && bash hooks/validate-skill-descriptions.sh && python3 scripts/check-skill-status.py`
Expected: net line delta ≤ +10; description hook passes (frontmatter untouched); status check passes (no status change).

- [ ] **Step 9: Commit.**

```bash
git add skills/uipath-rpa/SKILL.md
git commit -m "feat(uipath-rpa): route builds through execution maps; batch-author with single validate gate"
```

---

### Task 3: Pattern card batch 1 — System-package patterns + validation harness

**Files:**
- Create: `skills/uipath-rpa/references/common-pattern-card.md`
- Scratch (not committed): `<SCRATCHPAD>/patterncard/` UiPath project

**Interfaces:**
- Consumes: entry format precedent from `references/common-activity-card.md` (package anchor, snippet, notes, long-form pointer).
- Produces: card file with H3 entry per pattern; Task 4 appends to it; Task 2's Edit C links to it.

- [ ] **Step 1: Locate source docs.** For each batch-1 pattern, confirm the doc file exists and note the exact activity class:

Run: `ls skills/uipath-rpa/references/activity-docs/UiPath.System.Activities/26.4/activities/ | grep -iE 'text|file|csv|datatable|adddatarow|filter|build|queue|transaction|retry|invokeworkflow'`

Batch-1 patterns (all `UiPath.System.Activities` 26.4 unless the grep shows CSV lives elsewhere — follow the grep):
1. **Text file read → transform → write/append** (`ReadTextFile`, `WriteTextFile`, append variant)
2. **File ops** (path-exists check, copy/move/delete, create directory)
3. **CSV read/write**
4. **DataTable build → add rows → filter**
5. **Queue produce** (`AddQueueItem`) and **queue consume loop** (`GetTransactionItem` + `SetTransactionStatus` — cite the reframework-guide queue-guard note)
6. **Retry wrap** (`RetryScope` around a fragile action)
7. **Invoke Workflow File with in/out arguments**

Read each pattern's activity `.md` docs in one parallel batch.

- [ ] **Step 2: Scaffold scratch validation project.**

Run (scratchpad dir from session): `cd <SCRATCHPAD> && mkdir -p patterncard && cd patterncard && uip rpa init . --project-name PatternCard --target-framework Windows --expression-language VisualBasic --output json` (exact init syntax per cli-reference.md — adapt if init takes a directory arg differently).
Expected: `project.json` scaffolded; note installed `UiPath.System.Activities` version.

- [ ] **Step 3: Author one probe workflow per pattern.** For each pattern, write `<SCRATCHPAD>/patterncard/Pattern_<Name>.xaml` containing the candidate snippet inside a complete `<Activity>` root (root boilerplate from `common-activity-card.md` § How to read the snippets). Property-complete per the activity docs: include every required property and use-case-relevant optionals — starter-XAML omission of defaults is exactly the trap the card exists to avoid.

- [ ] **Step 4: Validate every probe.**

Run: `cd <SCRATCHPAD>/patterncard && for f in Pattern_*.xaml; do uip rpa validate --file-path "$f" --project-dir . --output json; done && uip rpa build . --output json`
Expected: 0 errors per file, build clean. Fix by error category; 5-attempt cap per file. A pattern that cannot reach clean is dropped from the card (record why in the commit message).

- [ ] **Step 5: Write the card file.** Header mirrors `common-activity-card.md`; per-entry schema:

````markdown
# Common Pattern Card

**Package anchor:** `UiPath.System.Activities` <VERIFIED_VERSION> — every entry below CLI-verified (`validate` + `build` clean) on the stamped version.

Copy-safe multi-activity snippets. **Supersedes the Rule 21 discovery procedure for every activity inside a listed pattern.** For activities outside these patterns, Rule 21 applies. Precedence: card → agent memory → Rule 21 triple ([execution-maps-guide.md](execution-maps-guide.md)). If `validate`/`build` rejects a card snippet: fall back to the Rule 21 triple for that activity and report the stale entry via `/uipath-feedback`.

Snippets are fragments for a complete `<Activity>` root — boilerplate rules identical to [common-activity-card.md § How to read the snippets](common-activity-card.md). VB expression form; C# projects: [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md).

## Card entries

<one-line list of pattern names>

---

### <Pattern name>
**Activities:** `<Namespace.Class>` · `<Namespace.Class>` …
**Packages:** `<PackageId>` <version> 
**Variables:** <name : type — purpose, one line each>

**Snippet:**
```xml
<verified XAML fragment>
```

**Notes:** <wiring, Rule 24 wraps, common property traps — ≤3 lines>
**Long-form:** [`activity-docs/<PackageId>/<ver>/activities/<Activity>.md`](activity-docs/<PackageId>/<ver>/activities/<Activity>.md)
````

Fill one entry per validated pattern with the exact XAML that passed Step 4.

- [ ] **Step 6: Re-run Task 1 Step 3 link check.**
Expected: zero output (pattern card now exists).

- [ ] **Step 7: Commit.**

```bash
git add skills/uipath-rpa/references/common-pattern-card.md
git commit -m "feat(uipath-rpa): pattern card batch 1 — System package patterns, CLI-verified"
```

---

### Task 4: Pattern card batch 2 — Excel, Mail, HTTP

**Files:**
- Modify: `skills/uipath-rpa/references/common-pattern-card.md` (append entries)
- Scratch: same `<SCRATCHPAD>/patterncard/` project

**Interfaces:**
- Consumes: card schema from Task 3; scratch project.
- Produces: final card entry list for the "Card entries" index line.

- [ ] **Step 1: Install packages + read docs.**

Run: `cd <SCRATCHPAD>/patterncard && uip rpa packages versions --package-id UiPath.Excel.Activities --include-prerelease --project-dir . --output json` (same for `UiPath.Mail.Activities`, `UiPath.WebAPI.Activities` — if `packages versions` shows WebAPI under a different id, use the id from `activities find --query http`). Then one `packages install` per package at the latest version.
Read bundled docs in parallel: `activity-docs/UiPath.Excel.Activities/3.6/…`, `activity-docs/UiPath.Mail.Activities/2.8/…`, `activity-docs/UiPath.Web.Activities/2.5/…`; prefer `.local/docs/packages/<PackageId>/` in the scratch project once installed (more accurate).

Batch-2 patterns:
1. **Excel: process scope → read range → for-each row → write range**
2. **Mail: send SMTP message** (notes line points at Outlook/O365 variants' doc paths, no separate snippet)
3. **HTTP request → deserialize JSON**

- [ ] **Step 2: Author probes, validate, append entries.** Same procedure as Task 3 Steps 3–5. Multi-package entries stamp each package version. Update the "Card entries" index line and the header package-anchor line to list all verified package+version pairs.

- [ ] **Step 3: Full-card re-verification.**

Run: `cd <SCRATCHPAD>/patterncard && for f in Pattern_*.xaml; do uip rpa validate --file-path "$f" --project-dir . --output json; done && uip rpa build . --output json`
Expected: still clean with all packages installed (catches cross-package conflicts).

- [ ] **Step 4: Commit.**

```bash
git add skills/uipath-rpa/references/common-pattern-card.md
git commit -m "feat(uipath-rpa): pattern card batch 2 — Excel, Mail, HTTP patterns, CLI-verified"
```

---

### Task 5: `.maintenance/pattern-card-maintenance.md`

**Files:**
- Create: `skills/uipath-rpa/.maintenance/pattern-card-maintenance.md`

- [ ] **Step 1: Write the file.** Full content:

````markdown
# Pattern Card Maintenance

Regeneration procedure for [references/common-pattern-card.md](../references/common-pattern-card.md). Run when: a stamped package ships a new minor/major, a staleness report arrives (`/uipath-feedback` or repo issue), or a new pattern is added.

## Procedure

1. Scratch project (never committed): `uip rpa init` a blank Windows/VisualBasic project in a temp dir.
2. `uip rpa packages install` every package stamped on the card, at the target (new) versions — `--include-prerelease`.
3. One probe workflow per card entry: paste the entry's snippet inside a complete `<Activity>` root (boilerplate per [common-activity-card.md § How to read the snippets](../references/common-activity-card.md)).
4. Gate: per-file `uip rpa validate --file-path "<FILE>" --project-dir "<DIR>" --output json` to 0 errors, then `uip rpa build "<DIR>" --output json` clean.
5. Failing entry → fix from `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md` (post-install, authoritative for the new version), re-gate. Unfixable → remove the entry from the card.
6. Update every entry's version stamp + the header package-anchor line. Entries never carry a version they were not gated against.
7. New pattern candidates qualify by frequency: appears in ≥2 `tests/tasks/uipath-rpa/` tasks or is a documented top user ask. Keep the card ≤ ~15 entries — it is a hot-path read, not a catalog.

## Rules

- CLI-gate before stamp — no exceptions, no "obviously fine" edits.
- UIA activities never enter this card (`skills/uipath-rpa/CLAUDE.md` boundary).
- Prose follows `.claude/rules/token-optimization.md`.
````

- [ ] **Step 2: Commit.**

```bash
git add skills/uipath-rpa/.maintenance/pattern-card-maintenance.md
git commit -m "docs(uipath-rpa): pattern card maintenance procedure"
```

---

### Task 6: Turn-budget eval task

**Files:**
- Create: `tests/tasks/uipath-rpa/execution-map/execution-map_greenfield.yaml` (one task per leaf dir)

**Interfaces:**
- Consumes: behavioral contract from Task 2 (maps followed, validate+build gate) and Task 3 (text-file pattern on card).

- [ ] **Step 1: Coverage + scaffold via repo workflow.** Run `/test-coverage uipath-rpa`, then `/generate-task greenfield XAML build inside the execution-map turn budget (≤8 turns), text-file automation, validate+build clean`. Reconcile the scaffold with the target YAML below (target wins on intent; scaffold wins on schema syntax — exact `agent:` override key, criterion field names — verify against `tests/README.md` and an existing task such as `tests/tasks/uipath-rpa/xaml_test_case.yaml`).

- [ ] **Step 2: Target YAML.**

```yaml
task_id: skill-rpa-execution-map-greenfield
description: >
  Greenfield XAML build must finish inside the execution-map turn budget:
  scaffold, batch-author, and gate (validate + build) a small text-file
  workflow in at most 8 turns, proving the execution map + pattern card
  eliminate per-activity discovery and validation round-trips.
tags: [uipath-rpa, smoke, mode:build]

agent:
  max_turns: 8

initial_prompt: |
  Create a UiPath XAML automation project named TextReport. The workflow must
  read ./input/orders.txt, log its contents, and append a processed marker
  line to the file. The task is not complete until `uip rpa validate` passes
  for the workflow file and `uip rpa build` passes for the project.
  Do NOT ask for approval, confirmation, or feedback.
  Before starting, load the uipath-rpa skill and follow its workflow.

success_criteria:
  - type: file_exists
    description: "Workflow file created"
    path: "TextReport/Main.xaml"
    weight: 1.5
    pass_threshold: 1.0

  - type: command_executed
    description: "Per-file validate ran"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+rpa\s+validate\s+.*--file-path'
    min_count: 1
    weight: 3.0
    pass_threshold: 1.0

  - type: command_executed
    description: "Project build gate ran"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+rpa\s+build\b'
    min_count: 1
    weight: 3.0
    pass_threshold: 1.0

  - type: command_not_executed
    description: "No per-activity discovery for card-covered activities (pattern card supersedes get-default-xaml)"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+rpa\s+activities\s+get-default-xaml'
    weight: 1.0
    pass_threshold: 1.0

  - type: command_executed
    description: "JSON output discipline"
    tool_name: "Bash"
    command_pattern: '(uip|\$UIP)\s+rpa\s+.*--output\s+json'
    min_count: 1
    weight: 1.0
    pass_threshold: 1.0
```

Schema adjustments from Step 1 apply (e.g., if `max_turns` lives at task top level rather than under `agent:`, or `command_not_executed` uses a different shape). If the sandbox needs `input/orders.txt` seeded, copy the seeding mechanism from an existing task/shared scripts; if none exists, change the prompt to have the workflow create the file first, and drop the path assumption. `file_exists` path must match where the map scaffolds the project — adjust after observing the scaffold layout (init may create `TextReport/` at CWD root).

- [ ] **Step 3: Lint.** Run `/lint-task tests/tasks/uipath-rpa/execution-map/execution-map_greenfield.yaml`. Fix all High findings; run `/audit-verbs` only if lint raises CLI-verb reachability.

- [ ] **Step 4: Run the task if the local coder-eval harness is available; otherwise record honestly.** Attempt per `tests/README.md` (make target or runner script). If runnable, also run the same prompt once against the pre-change skill (`git stash` / main checkout of `skills/uipath-rpa/`) and record before/after turn counts for the PR (spec Testing #2). If the harness/env (sandbox, login) is unavailable locally, note "passing-run claim pending CI" in the eventual PR body — do not fabricate a claim.

- [ ] **Step 5: Commit.**

```bash
git add tests/tasks/uipath-rpa/execution-map/execution-map_greenfield.yaml
git commit -m "test(uipath-rpa): smoke task enforcing execution-map turn budget"
```

---

### Task 7: Final sweep + spec coverage check

**Files:**
- Modify (only if sweep finds issues): files from Tasks 1–6

- [ ] **Step 1: Repo validation sweep.**

Run: `bash hooks/validate-skill-descriptions.sh && python3 scripts/check-skill-status.py && python3 scripts/check-cli-verbs.py`
Expected: all pass; no README regeneration needed (no status change).

- [ ] **Step 2: Cross-file consistency.** Grep the new/edited files for: rule-number citations that don't exist in SKILL.md (`grep -oE 'Rule [0-9]+[a-z]?' skills/uipath-rpa/references/execution-maps-guide.md | sort -u` — verify each against SKILL.md), broken relative links (re-run Task 1 Step 3 list plus card links), UIA-forbidden terms (Task 1 Step 4 grep across all new files).

- [ ] **Step 3: Spec coverage check.** Re-read `docs/superpowers/specs/2026-07-02-uipath-rpa-execution-map-design.md` § Design 1–4 and § SKILL.md integration 1–6; point each requirement at a commit. Gaps → fix now.

- [ ] **Step 4: Commit any fixes.**

```bash
git add -A && git commit -m "chore(uipath-rpa): execution-maps final sweep fixes"
```
(Skip commit if the sweep was clean.)
