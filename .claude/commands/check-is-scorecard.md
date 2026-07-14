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
