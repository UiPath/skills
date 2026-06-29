# Exception Table + Guided Flow — Approach & Findings

Exploratory work (the "third approach" to optimizing `uipath-troubleshoot`). Branch deliverable; not merged. Captures the design, validation, the key variance finding, and why it motivates the next approach (deterministic hybrid tree).

## Approach

Two coupled changes on top of the baseline:

1. **Central exception table** (`references/exception-table.md`) — one greppable, cross-product signature index: `signature (code / exception FQN / HRESULT / message-regex) → kind → domain → playbook → fast_path? → minimal-confirm`. Two jobs: (a) **fast-path** — a `fast_path: yes` row that is the unambiguous top match is an exact cause-naming single-cause signature; triage runs the one confirm inline, writes `H1`, → depth-check → resolution; (b) **routing index** — every row (incl. `fast_path: no`) gives triage a direct signature→playbook lookup. Guardrail rules in the file: `fast_path: yes` only for exact + cause-naming + single-cause + originating signatures; wrappers/opaque/symptoms are `fast_path: no` and run the full loop.

2. **Guided deterministic flow** — the generic guide (`references/investigation_guide.md`) gains a canonical ordered **Investigation Flow** (classify → resolve identity → gather core evidence bundle → match exception-table → branch); each system guide leads with its specialized ordered flow (Orchestrator: folder/job → `jobs get` + error logs → table match → branch; stuck/cancelled = `fast_path:no` symptom → traverse to child). Triage (step B) follows the guide's flow instead of freelancing; matching (step E) greps the table first.

Intent: make triage **deterministic** (gather per guide → grep table → branch) instead of open-ended (read every domain summary + reason per playbook), and centralize fast-path knowledge in one extensible file.

## Files (this branch)
- NEW `references/exception-table.md`
- `references/investigation_guide.md` — canonical Investigation Flow
- `references/products/orchestrator/investigation_guide.md` — leads with ordered flow
- `agents/triage.md` — § E signature-lookup (table-first) + § B follow-the-guide-flow
- `SKILL.md` — § FAST PATH (inline-confirmed signature → depth-check → resolution) + multi-system child-traversal discipline (applied proactively)
- `schemas/state.schema.md` — `fast_path` block + doc

## Validation (coder-eval, on main; parallel + sequential)

Decisions are correct and the guardrails hold:
- **Fast-path fires on exact cause-naming signatures:** orch `no-host-pending` (no-host message → job-pending-no-host) fast-pathed 1.0/51 turns; IS `connector-general-disabled` (DAP-GE-3005) fast-pathed 1.0 (47 turns one run).
- **Opaque/multi-cause correctly NOT fast-pathed → full loop:** IS `connector-null-reference` (NRE) 1.0/0.85 generic; orch `logon-failure-password-mismatch` (medium multi-branch) `eligible:false` → generic 1.0; excel `sheet-typo` generic 1.0.
- **Multi-system guardrail held:** `maestro-stuck-rpa-job` `fast_path:no` → full loop → scope expanded to ui-automation → correct child-UIA root cause (0.925/1.0; 3-domain). The proactive child-traversal discipline prevented the regression that the dedicated-agent approach hit.

## THE KEY FINDING — LLM-driven matching is inconsistent

The same `connector-general-disabled` task **fast-pathed at 47 turns in one run and did NOT fast-path at all (143 turns) in another** — identical task, identical table. Decisions are *mostly* right but **whether the fast-path fires is not deterministic.** Run-to-run variance across the suite was large and independent of parallel load: turns swung ±2× (47↔143), scores swung (NRE 1.0↔0.85, maestro 1.0↔0.925). Isolated (sequential) runs only cut wall-clock ~15–30%; the variance is agent-behavior, not contention.

**Implication:** LLM-driven routing has a consistency ceiling. The exception table is the right *data*, but having the LLM decide *whether/how* to use it is the source of the variance. A **deterministic executor** that walks the table/tree would fire the fast-path every time, on the same evidence — removing the variance and making the deterministic part testable without LLM noise.

## Conclusion → next approach

This attempt validated that (a) a central exception table is sound and safe, (b) a guided deterministic flow is good design, but (c) **LLM-as-the-matcher is inconsistent**. The natural next step is the **hybrid deterministic decision-tree / expert-system** (see the feasibility analysis): a deterministic executor walks `dispatch → gather → branch → leaf` for the code/exception-routable subset; at any node it can't resolve from evidence, an **LLM takes over — either continuing down the path (choosing the child branch from evidence) or jumping to another node/leaf** — while preserving grounded, evidence-based, consistent resolution. The exception table from this attempt becomes the tree's `dispatch` root; the 185 tests' `manifest.json` files become the deterministic regression harness.

Status: built on bare `main`. Full run log / feasibility synthesis: `tests/reports/` (local) + the session transcript.
