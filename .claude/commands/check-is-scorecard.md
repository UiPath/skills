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

## Phase 0 — Staleness guard (run FIRST, before any check)

The reason this command exists: a stale checkout published diagnose at 17% instead of 46%. Verify the tree is current before comparing anything.

1. Run `git fetch origin main`.
2. Run `git rev-list --count HEAD..origin/main`.
3. If the count is `> 0`: **hard-fail**. Print `CHECK 0 staleness  FAIL — local main is <N> commits behind origin/main`, instruct `git pull --ff-only origin main`, and STOP. Do not run Phases 1–4 against a stale tree.
4. If `0`: print `CHECK 0 staleness  PASS (HEAD == origin/main)` and continue.

## Phase 1 — Fetch and parse the enumeration doc (source of truth)

1. Resolve the page id: `--doc` if given, else `CONFLUENCE_PAGE_ID`.
2. Fetch it: `getConfluencePage(cloudId="uipath.atlassian.net", pageId=<id>, contentFormat="html")`. If auth fails, STOP and tell the user to authenticate the Atlassian MCP.
3. From the returned HTML, extract into named sets:
   - **`DOC_TASK_IDS`** — every ``code``-wrapped `task_id` in the feature-table "Coded Test Tasks" cells (values matching `skill-[a-z0-9-]+` or `-connector-*`, `-rpa-is-*` shorthands). Record the mode section (Build/Operate/Diagnose) each appears under.
   - **`DOC_PLAYBOOKS`** — every playbook basename cited (values matching `[a-z-]+` that appear in "Playbook(s)" cells, e.g. `connection-invalid`, `cs-permission-denied`).
   - **`DOC_TALLY`** — the Coverage Summary table: per-mode `Capabilities`, `Direct eval`, and `Eval %` (Build/Operate/Diagnose/Total).
4. Print a one-line summary: `Parsed doc: <n> task_ids, <n> playbooks, tally B/O/D = …`. If any set is empty, WARN (doc may have been reformatted) but continue.

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
