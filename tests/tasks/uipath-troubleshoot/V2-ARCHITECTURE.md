# uipath-troubleshoot v2 — Architecture & the #1912 Merge

Internal test-side reference. Documents the v1 → v2 architecture change (#1820), the parallel single-file rewrite (#1912), and how #1912's content was merged onto the v2 branch. Shipped skill prose lives in `skills/uipath-troubleshoot/`; this file is authoring documentation only.

## v1 — multi-subagent orchestration (removed)

The original skill ran every investigation through a fixed choreography of seven subagents:

```
triage → scope-checker → hypothesis-generator → [hypothesis-tester × N, sequential]
       → depth-verifier → presenter
```

- **Contracts:** each agent read/wrote state files under `.local/investigations/` (`state.json`, `hypotheses.json`, `evidence.json`, `needs_input.json`) whose shapes were specified in `schemas/*.schema.md`; behavioral invariants lived in `agents/shared.md`.
- **Why it was replaced:** eval data across 184 replay scenarios showed the choreography, not the knowledge, was the cost. 159/184 scenarios passed without the skill, and the 13 stable failures all needed a playbook fact or decision-tree discriminator — not orchestration. Wall time was 25–55 min per investigation, roughly half of all file reads were subagents reloading files another agent already had, and the orchestration shape varied wildly between runs of the same task.

## v2 — tiered signature-index investigator (#1820, this branch)

Keeps the playbook knowledge, removes the choreography. Three tiers:

- **Tier 0 — signature-index routing.** Every playbook declares `signatures:` frontmatter (exception classes, error codes, message fragments, resource keys). `scripts/build-signature-index.py` generates `references/signature-index.md` — a grep-only routing table plus no-signature symptom routing and a signal-extraction cheatsheet — and lints the corpus: every playbook routable or justified `silent: true`, duplicate (kind,value) claims need discriminating notes, exclusion targets must exist, localizable message signatures warn.
- **Tier 1 — single-context investigation (the common case).** `SKILL.md` is a ~150-line protocol run entirely in one context: anchor the entity → extract signals (mandatory AggregateException/inner-exception unwrap; language-invariant signals first, localized text translated before grepping) → route via the index → walk the matched playbook's decision tree → mandatory format-forced verification checklist (cause named verbatim; evidence pinned vs sibling causes; runtime-evidence gate; resolution-branch alignment; causal precedence; fix scope) → present per `references/presenting.md` under the approval gate (user source files are never modified without explicit `AskUserQuestion` approval; decline or non-answer = no edit).
- **Tier 2 — escalation** (`references/escalation.md`, loaded only on defined triggers): 2–4 parallel read-only hypothesis probes + adjudication + a conditional fresh-eyes verifier, with a serial in-context fallback for harnesses without a subagent-spawning tool.

**State** is `.local/investigations/raw/*.json` (full CLI responses) + `notes.md` (running log). No other state files; `agents/` and `schemas/` are deleted.

**Validation posture** (see PR #1820 for full tables): local sentinel 15/15 on the former stable-fail core; full CI suite 179/185 first-pass after the #1891 fix set, every task with ≥1 passing run; per-task CI wall time avg 3.5 min vs 25–55 min under v1.

## #1912 — the single-file rewrite, and where its content went

PR #1912 (`feat/troubleshoot-single-file`, closed unmerged) was an independent rewrite of the same v1 skill: it collapsed the seven subagents into one inline phase machine in SKILL.md (TRIAGE → SCOPE CHECK → GENERATE → TEST → EVALUATE → DEPTH CHECK → RESOLUTION), kept the state files/schemas, and validated 33 scenarios (30 × 1.000). v2 went further in the same direction (no phases-as-state-machine, no schemas), so most of #1912's structure is superseded — but it carried test-harness fixes and behavioral rules v2 lacked. Disposition of every #1912 change:

### Ported onto this branch

| Change | Where it landed |
|---|---|
| **Token-aware mock dispatcher matcher** — `_rule_matches`: token-subset (order-independent, quote-stripped, `--flag=value` split, `--output <v>` neutralized) OR the legacy substring fallback; additive, never under-matches | `tests/tasks/uipath-troubleshoot/_shared/mock_template/m/uip` (cherry-pick) |
| rpa-preflight manifest match strings canonicalized (quotes and `--output json` dropped) | same cherry-pick |
| **Mock-rule ordering fixes** the token matcher made necessary: specific rules before generic in `no-host-pending` (`--state Running`, `--all-fields`) and `uia-rpa-selector-healing-disabled` (`--help` depth chain) — a short rule's token set now matches a superset of invocations, and first match wins | follow-up commit on this branch |
| Maestro guide folder flag normalized `-f` → `--folder-key` | cherry-pick + maestro mock match strings made folder-flag-agnostic (the `-f <key>` tokens dropped) so either spelling dispatches |
| Word guide section rename `## What to Capture` → `## Domain-Specific Data Gathering` (last outlier; all sibling guides already used the new name) | cherry-pick |
| **Payload-conditional output capture** — filtered/small → `--output-filter` + `\| tee`; heavy/unfilterable (traces, logs, stacks, `errorDetails`) → `>` + selective read-back; filter-failure fallback; anti-patterns. Resolves a live v2 contradiction: SKILL Invariant 4 mandated bare `>` for everything while the orchestrator guide mandated `tee` and banned bare `>` | canonical section in generic `investigation_guide.md` § Output Capture; SKILL Invariant 4 rewritten to defer to it; orchestrator guide § Output Capture reduced to a delegation + the traces command switched `tee` → `>` |
| **Standalone-vs-solution source layout discovery** — resources either inline under the project dir or hoisted to a solution wrapper at the working-directory root (one level up from a named project dir); resolve both layouts before treating a playbook-named file as missing ("absence from one layout is not absence"). Took `faulted_excel_o365` from 0.850 to 1.000 on #1912 | generic `investigation_guide.md` § Locating Project Source & Resource Files; wired into SKILL §5.4 (source-required playbooks) between the top-level check and the ask |
| **Correlation-key-first empty-result check** — "an empty result is more often a wrong-key error than a missing entity" | SKILL Invariant 6 |
| **Playbook stale multi-agent references** (review finding on #1912 that applied equally here): `needs_input.json per agents/shared.md`, "the presenter must emit a `## Post-presentation actions` block … the orchestrator must execute it", "the orchestrator MUST call AskUserQuestion", `depth-verifier`, "re-spawns you" — replaced with current nouns (`AskUserQuestion`, `references/presenting.md` § Interactive resolutions, "you", the verification checklist, notes.md) in 7 playbooks | follow-up commit on this branch |

### Already covered by v2 (not re-ported)

- **Playbook-grounded fixes** (#1912 Rule 16) → verification checklist items 4 (resolution aligned) + 6 (fix scope, no unevidenced solution mechanisms) + presenting.md § 2.
- **Runtime-evidence gate** (design-time evidence proves a defect exists, not that it caused this failure) → checklist item 3, near-verbatim.
- **Command allowlist / `--help` ban** → Invariant 3 (No CLI discovery).
- **Anchor policy** (no broad scans, no placeholder gets, bounded authorized locate pass, confirm the candidate) → SKILL §2.
- **`needs_input.json` → `AskUserQuestion`** in the orchestrator guide → v2 had already made the same change.
- **Manifest validator positional-args + bare `--version` fix** → landed on main independently as #1927 (functionally equivalent rework of #1912's commit; main's version kept).
- Orchestrator folder-list filter fields: v2's `Name/Path/Type` correction is newer than #1912's `DisplayName/FullyQualifiedName` variant — v2's kept.

### Superseded (dropped)

- #1912's SKILL.md phase machine, Critical-Rules regrouping, DEPTH CHECK machinery, `core_evidence`/signals state model.
- All `schemas/*.md` edits including the new `depth-check.schema.md` (v2 has no schemas; state is `raw/` + `notes.md`).
- knowledge-base-guide terminology edits (v2's signature-frontmatter rewrite of that file supersedes them).

### Known pre-existing oddities surfaced during the merge (not regressions, not fixed here)

- Four manifests carry duplicate rules with **identical match strings but different response files** (`logon-failure-password-mismatch`, `rpa-foreground-already-running`, `rpa-foreground-misconfigured` — `or folders list`; `null-reference-exception` — `or jobs get` exit 1 then exit 0). The second rule was already unreachable under the old substring matcher (first match wins); behavior is unchanged. The dispatcher has no call-count sequencing, so these look like leftovers from fixture regeneration.
- `sys-getasset-network-connectivity` had two tolerance rules pointing at a nonexistent response file (dispatcher would return exit 2 `fixture_missing`); repointed at the existing faulted-list fixture in this merge since the token matcher changed which invocations reach them.

## Test-harness notes for authors

- **Match strings are token-matched** (see the module docstring in `_shared/mock_template/m/uip`): order-independent, quotes stripped, `--output <v>` ignored. List specific patterns before generic ones — a rule with fewer tokens matches a superset of invocations and first match wins. Prefer dropping volatile flags (e.g. folder flags with both `-f` and `--folder-key` spellings) from match strings when the remaining tokens are unique.
- A shadow-audit one-liner: for rules i < j in one manifest, if `tokens(match_i) ⊆ tokens(match_j)` and they serve different files/exit codes, rule j is unreachable for its canonical invocation.
