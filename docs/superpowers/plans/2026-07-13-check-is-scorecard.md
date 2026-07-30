# `/check-is-scorecard` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable `.claude/commands/check-is-scorecard.md` slash command that audits the published IS Product Capability Enumeration (Confluence 90898825832) against fresh-`main` repo state via four reconciliation checks + a staleness guard.

**Architecture:** A single markdown slash-command prompt (no executable code), matching the house pattern of `lint-task.md` / `test-coverage.md`: `# Title`, `**Input:**`/`**Output:**`, source-of-truth note, `---`, numbered `## Phase N` sections. The command instructs the agent to (0) verify the checkout is current, (1–4) run four reconciliations, (5) print a PASS/FAIL table, (6) offer an opt-in fix. Validation = a dry run of the finished command against the real page + repo.

**Tech Stack:** Markdown command prompt; at run time the agent uses the Atlassian MCP (`getConfluencePage`), `git`, `grep`/file reads, and reads `tests/reports/coverage.json`.

## Global Constraints

- File lives at `.claude/commands/check-is-scorecard.md` (sibling of `lint-task.md`, `test-coverage.md`, `generate-confluence-scorecard.md`).
- Six parameters declared at the top with IS defaults (see spec): `CONFLUENCE_PAGE_ID=90898825832`, `TAGS=integration-service,ipe`, `PLAYBOOK_DIR=skills/uipath-troubleshoot/references/products/integration-service/playbooks/`, `REPO_DOC=tests/reports/integration-service-capability-enumeration.md`, `COVERAGE_KEY=uipath-integration-service`, `SCORECARD_ROW=Integration Service (uip is)`.
- Read-only by default; mutation only after an explicit `AskUserQuestion` choice.
- Staleness guard (Phase 0) runs before any check and hard-fails if `HEAD` is behind `origin/main`.
- Follow `.claude/rules/content-quality.md` (prescriptive, numbered, exact commands) and `token-optimization.md` (terse).
- Branch: `feat/check-is-scorecard` (already created; spec already committed).

---

### Task 1: Command skeleton, parameters, and Phase 0 staleness guard

**Files:**
- Create: `.claude/commands/check-is-scorecard.md`

**Interfaces:**
- Consumes: nothing (entry point).
- Produces: the parameter table and Phase 0 that every later phase references by name (`CONFLUENCE_PAGE_ID`, `TAGS`, etc.).

- [ ] **Step 1: Write the header + Input/Output + source-of-truth note**

Write to `.claude/commands/check-is-scorecard.md`:

```markdown
# Check Integration Service Scorecard Accuracy

Audit the published IS Product Capability Enumeration — the source feeding the org Coding-Agents Scorecard's Integration Service row — against live repo state on fresh `main`. Read-only by default; offers an opt-in fix on any mismatch.

**Input:** `$ARGUMENTS` (all optional)
- `--scorecard <pageId>` — also reconcile against a published org scorecard's IS row.
- `--doc <pageId>` — override the enumeration page id (default below).

**Output:** A per-check PASS/FAIL/WARN table printed to chat, with specific mismatches cited. No file writes unless the user explicitly opts into a fix at the end.

This command is the source of truth for the IS scorecard accuracy rubric. Clone it for another cross-cutting row (e.g. ECS / context-grounding) by copying this file and swapping the six parameters below.

---

## Parameters

| Param | IS default |
|---|---|
| `CONFLUENCE_PAGE_ID` | `90898825832` |
| `TAGS` | `integration-service`, `ipe` |
| `PLAYBOOK_DIR` | `skills/uipath-troubleshoot/references/products/integration-service/playbooks/` |
| `REPO_DOC` | `tests/reports/integration-service-capability-enumeration.md` |
| `COVERAGE_KEY` | `uipath-integration-service` |
| `SCORECARD_ROW` | `Integration Service (uip is)` |
```

- [ ] **Step 2: Append Phase 0 (staleness guard)**

```markdown
## Phase 0 — Staleness guard (run FIRST, before any check)

The reason this command exists: a stale checkout published diagnose at 17% instead of 46%. Verify the tree is current before comparing anything.

1. Run `git fetch origin main`.
2. Run `git rev-list --count HEAD..origin/main`.
3. If the count is `> 0`: **hard-fail**. Print `CHECK 0 staleness  FAIL — local main is <N> commits behind origin/main`, instruct `git pull --ff-only origin main`, and STOP. Do not run Phases 1–4 against a stale tree.
4. If `0`: print `CHECK 0 staleness  PASS (HEAD == origin/main)` and continue.
```

- [ ] **Step 3: Verify structure**

Run: `head -60 .claude/commands/check-is-scorecard.md`
Expected: header, Input/Output, source-of-truth note, `---`, Parameters table, Phase 0 all present in order.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "feat(check-is-scorecard): skeleton, params, staleness guard"
```

---

### Task 2: Phase 1 — fetch + parse the Confluence doc

**Files:**
- Modify: `.claude/commands/check-is-scorecard.md` (append Phase 1)

**Interfaces:**
- Consumes: `CONFLUENCE_PAGE_ID` (Param), `--doc` override.
- Produces: three parsed sets the later checks consume by name — `DOC_TASK_IDS` (every `task_id` cited), `DOC_PLAYBOOKS` (every playbook name cited), `DOC_TALLY` (per-mode covered/total + %).

- [ ] **Step 1: Append Phase 1**

```markdown
## Phase 1 — Fetch and parse the enumeration doc (source of truth)

1. Resolve the page id: `--doc` if given, else `CONFLUENCE_PAGE_ID`.
2. Fetch it: `getConfluencePage(cloudId="uipath.atlassian.net", pageId=<id>, contentFormat="html")`. If auth fails, STOP and tell the user to authenticate the Atlassian MCP.
3. From the returned HTML, extract into named sets:
   - **`DOC_TASK_IDS`** — every ``code``-wrapped `task_id` in the feature-table "Coded Test Tasks" cells (values matching `skill-[a-z0-9-]+` or `-connector-*`, `-rpa-is-*` shorthands). Record the mode section (Build/Operate/Diagnose) each appears under.
   - **`DOC_PLAYBOOKS`** — every playbook basename cited (values matching `[a-z-]+` that appear in "Playbook(s)" cells, e.g. `connection-invalid`, `cs-permission-denied`).
   - **`DOC_TALLY`** — the Coverage Summary table: per-mode `Capabilities`, `Direct eval`, and `Eval %` (Build/Operate/Diagnose/Total).
4. Print a one-line summary: `Parsed doc: <n> task_ids, <n> playbooks, tally B/O/D = …`. If any set is empty, WARN (doc may have been reformatted) but continue.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "feat(check-is-scorecard): Phase 1 fetch + parse doc"
```

---

### Task 3: Phase 2 — Check 1 (doc ↔ repo evals) + Check 2 (doc ↔ playbooks)

**Files:**
- Modify: `.claude/commands/check-is-scorecard.md` (append Phase 2)

**Interfaces:**
- Consumes: `DOC_TASK_IDS`, `DOC_PLAYBOOKS` (Phase 1); `TAGS`, `PLAYBOOK_DIR` (Params).
- Produces: `CHECK1_RESULT`, `CHECK2_RESULT` (PASS/FAIL + mismatch lists) for the Phase 5 table.

- [ ] **Step 1: Append Phase 2**

```markdown
## Phase 2 — Checks 1 & 2 (structural reconciliation)

### Check 1 — Doc ↔ repo evals

1. Build `REPO_TASK_IDS`: for each alias in `TAGS`, run
   `grep -rlw "<alias>" tests/tasks --include='*.yaml' | grep -v _shared`,
   then for each file read its `task_id:` and `mode:*` tag. (Note `integration-service` also substring-matches the `integration` tier — require a whole-token match: the tag appears as its own list item or comma-delimited token, NOT inside the word `integration`.)
2. **Stale citations:** every id in `DOC_TASK_IDS` not in `REPO_TASK_IDS` → FAIL, list them.
3. **Mode mismatch:** any id whose repo `mode:*` differs from the doc's mode section → FAIL, list `id (doc=<mode>, repo=<mode>)`.
4. **Un-listed evals:** every id in `REPO_TASK_IDS` not in `DOC_TASK_IDS` → FAIL, list them (doc is missing a real eval). Exclude the false-positive substring matches from step 1's note.
5. `CHECK1_RESULT` = PASS iff no stale, no mismatch, no un-listed.

### Check 2 — Doc ↔ playbooks

1. Build `REPO_PLAYBOOKS` = basenames (no `.md`) of `*.md` in `PLAYBOOK_DIR`.
2. **Missing:** every file in `REPO_PLAYBOOKS` not in `DOC_PLAYBOOKS` → FAIL, list them (doc omits a real playbook — neither covered nor gap-listed).
3. **Phantom:** every name in `DOC_PLAYBOOKS` not in `REPO_PLAYBOOKS` → FAIL, list them (doc cites a playbook that does not exist).
4. `CHECK2_RESULT` = PASS iff no missing, no phantom. Report `<covered>/<total>` represented.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "feat(check-is-scorecard): Phase 2 checks 1-2 (evals, playbooks)"
```

---

### Task 4: Phase 3 — Check 3 (doc ↔ scorecard numbers) + Check 4 (internal consistency)

**Files:**
- Modify: `.claude/commands/check-is-scorecard.md` (append Phase 3)

**Interfaces:**
- Consumes: `DOC_TALLY` (Phase 1); `COVERAGE_KEY`, `SCORECARD_ROW` (Params); `--scorecard` override.
- Produces: `CHECK3_RESULT`, `CHECK4_RESULT` for the Phase 5 table.

- [ ] **Step 1: Append Phase 3**

```markdown
## Phase 3 — Checks 3 & 4 (numeric reconciliation)

### Check 3 — Doc ↔ scorecard numbers

1. If `tests/reports/coverage.json` exists AND has a `skills.<COVERAGE_KEY>` entry: compare its `mode_coverage.{build,operate,diagnose}.pct` and `overall_pct` against `DOC_TALLY`. Any divergence → FAIL, cite `mode: coverage.json=<x>% vs doc=<y>%`.
2. If the entry is ABSENT → WARN (not FAIL): `IS not yet registered cross-cutting in /test-coverage; scorecard uses platform-aggregate floor`. Point at the open registry task.
3. If `--scorecard <id>` given: fetch that page, find the `SCORECARD_ROW` row, and compare its Build/Operate/Diagnose Eval % cells against `DOC_TALLY`. Divergence → FAIL, cite the cell.
4. `CHECK3_RESULT` = PASS iff all present comparisons agree; WARN if only the missing-entry condition fired; FAIL on any divergence.

### Check 4 — Internal consistency (within the doc)

1. For each mode, count the doc's covered feature rows (Has-Evals ✅) and uncovered rows (🔴 / gap table) directly from the feature tables.
2. Compare counted `covered` and `total` against `DOC_TALLY`'s `Direct eval` and `Capabilities` for that mode. Mismatch → FAIL, cite `Diagnose tally <a>/<b> but counted <c> covered / <d> rows`.
3. Verify `Total` row = sum of the three per-mode rows (capabilities and direct-eval columns). Mismatch → FAIL.
4. `CHECK4_RESULT` = PASS iff every mode reconciles and the total sums.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "feat(check-is-scorecard): Phase 3 checks 3-4 (numbers, internal)"
```

---

### Task 5: Phase 4 — verdict table + Phase 5 opt-in fix

**Files:**
- Modify: `.claude/commands/check-is-scorecard.md` (append Phases 4 & 5)

**Interfaces:**
- Consumes: `CHECK{0..4}_RESULT` and their mismatch lists.
- Produces: printed verdict; on FAIL/WARN, a single `AskUserQuestion` gating any mutation.

- [ ] **Step 1: Append Phases 4 & 5**

```markdown
## Phase 4 — Verdict

Print a fixed-width table, one row per check, exactly:

```
CHECK 0 staleness      <PASS|FAIL>  <detail>
CHECK 1 doc↔evals      <PASS|FAIL>  <n stale, n mismatch, n un-listed>
CHECK 2 doc↔playbooks  <PASS|FAIL>  <covered>/<total> represented
CHECK 3 doc↔scorecard  <PASS|WARN|FAIL>  <detail>
CHECK 4 internal       <PASS|FAIL>  <detail>
```

Below the table, under each non-PASS check, list the specific mismatches (one per line: the task_id / playbook / cell and what disagreed). Overall verdict = worst status across checks.

## Phase 5 — Opt-in fix (only if any FAIL/WARN)

Do NOT mutate anything automatically. Ask ONE question with `AskUserQuestion`:

> "Reconcile the discrepancies?"
> - **Patch repo doc** — update `REPO_DOC` markdown to match fresh repo state (then user commits).
> - **Republish Confluence** — push the corrected body to `CONFLUENCE_PAGE_ID` via `updateConfluencePage`.
> - **Do nothing** — leave everything; report only.

Act only on the chosen option. For "Patch repo doc", edit `REPO_DOC` and show a diff — do not commit or push (leave that to the user). For "Republish", update the page with `includeBody:false` and a version message naming the reconciled checks. Never edit the org scorecard page itself.
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "feat(check-is-scorecard): Phase 4-5 verdict + opt-in fix"
```

---

### Task 6: Validate by dry-running the finished command

**Files:**
- (No new files — this task exercises the command end-to-end against the real page + repo.)

**Interfaces:**
- Consumes: the complete `.claude/commands/check-is-scorecard.md`.
- Produces: a confirmed-working command + any inline fixes to the prompt.

- [ ] **Step 1: Confirm fresh main**

Run: `git fetch origin main && git rev-list --count HEAD..origin/main`
Expected: `0` (so Phase 0 passes and the real checks run). If non-zero, `git pull --ff-only` first.

- [ ] **Step 2: Execute the command's phases manually against the real data**

Follow the command file top to bottom: fetch page `90898825832`, parse the three sets, run Checks 1–4 against the repo (`TAGS` grep, `PLAYBOOK_DIR` listing, `coverage.json`, the doc's own tally). Produce the Phase 4 table.

- [ ] **Step 3: Assert the known-good state reconciles**

Expected against today's repo + page: Check 2 PASS (26/26 playbooks represented — 11 covered + the G1–G13 gap rows), Check 4 PASS (Diagnose 12/26 matches counted rows), Check 3 WARN (no `uipath-integration-service` entry in coverage.json yet). If any check FAILs on data we know is correct, the parsing rule is too strict/loose — fix the offending phase text inline and re-run.

- [ ] **Step 4: Commit any prompt fixes**

```bash
git add .claude/commands/check-is-scorecard.md
git commit -m "fix(check-is-scorecard): tighten parsing after dry-run"
```

- [ ] **Step 5: Update CODEOWNERS if required**

Run: `grep -n "commands" CODEOWNERS 2>/dev/null || echo "no commands entry — check house convention"`
If sibling commands have a CODEOWNERS entry pattern, add `.claude/commands/check-is-scorecard.md` to match; else skip.

---

## Self-Review

- **Spec coverage:** Phase 0 = staleness guard ✓; Check 1 doc↔evals = Task 3 ✓; Check 2 doc↔playbooks = Task 3 ✓; Check 3 doc↔scorecard = Task 4 ✓; Check 4 internal = Task 4 ✓; read-only + opt-in fix = Task 5 ✓; six parameters = Task 1 ✓; reusability note = Task 1 Step 1 ✓; Confluence source-of-truth = Phase 1 ✓. All spec sections mapped.
- **Placeholder scan:** none — every phase has its literal command text.
- **Type consistency:** the named sets (`DOC_TASK_IDS`, `DOC_PLAYBOOKS`, `DOC_TALLY`, `REPO_TASK_IDS`, `REPO_PLAYBOOKS`, `CHECK{n}_RESULT`) are defined in Phase 1/2/3 and consumed with the same names in Phases 4–5. Consistent.
