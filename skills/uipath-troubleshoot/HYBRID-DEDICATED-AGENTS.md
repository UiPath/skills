# Hybrid Dedicated-Agent Architecture — Approach & Findings

Exploratory work (the "second approach" to optimizing `uipath-troubleshoot` runtime). Branch deliverable; not merged to main. Captures the design, what was built, validation results, the regression we hit and fixed, and the conclusions.

## 1. Problem

The troubleshoot skill is **reasoning/ceremony-bound**: a single obvious diagnosis (e.g. "connection disabled") still costs ~500–800s because the orchestrator serially spawns triage → generator → tester(s) → depth-verifier → presenter, each re-reading `shared.md` + its agent file + playbooks and running a multi-step plan. The dominant cost is **LLM round-trip latency × cold-start sub-agent hops**, not CLI work (an obvious case made ~2 CLI calls across ~60+ turns).

## 2. Approach — hybrid dedicated agent + generic fallback

- **Dedicated per-product investigation agent** = a fast, product-specialized path for *known/easy* signatures. Lives as a **product file**: `references/products/<product>/investigation_agent.md`. Confirms the known root cause in one specialized step instead of the generic generate→test loop.
- **Generic pipeline stays as the fallback** for products without a dedicated agent and for any opaque / multi-cause / no-known-resolution case.
- **scope-checker and depth-verifier remain shared** and gate everything — the fast path never skips the symptom≠cause depth check.

This reconciles "dedicated per-platform agents" with the repo's **agents-stay-generic mandate**: the core `agents/` roster is product-agnostic; product specifics live in the product file. Adding a product's fast path = drop in one file, **zero core-agent edits**.

### Routing (the key mechanism)
1. Triage classifies + extracts signals + matches playbooks + expands scope (unchanged generic front-end).
2. **Triage § E.1 route-early**: if (a) a **cause-naming** signal exists, (b) the **top-ranked** matched playbook is `high`-confidence **single-cause**, and (c) the product that **owns the top playbook** has an `investigation_agent.md`, then triage stops gathering (skips Pass-2/confirmatory fetches), writes `state.json.routing = {path:"dedicated", product, outcome:"pending"}`, and hands off. Routing follows the **top playbook's product**, so a cross-domain root cause routes to the *root-cause* product, not the surfacing one.
3. **Orchestrator ROUTING**: `routing.path=="dedicated"` → spawn that product's agent → `resolved` (→ depth-check → resolution) or `escalate` (→ generic loop). Otherwise → generic pipeline.

Because route-early only fires on a high-confidence single-cause top match, the dedicated agent **never adds a hop** to opaque/multi-cause cases — they go straight to generic.

## 3. What was built (this branch)
- `agents/triage.md` — § E.1 route-early.
- `SKILL.md` — § ROUTING; writers table + phase-machine note; restored full-loop discipline (see §6).
- `schemas/state.schema.md` — `routing` block.
- `references/products/integration-service/investigation_agent.md` — dedicated IS agent (DAP-GE/DAP-RT/invalid/auth-expired fast-resolve; escalate NRE/aggregate/remote/medium).
- `references/products/orchestrator/investigation_agent.md` — dedicated OR agent (robot-credentials, job-pending-no-host, job-pending-stale-dispatch; escalate logon-multi-branch/queue/stuck/exit-code).

## 4. The route-early speed lever (the real win)
The dedicated agent **alone** did not speed anything up — the first pilot run routed dedicated/resolved but took 796s (= baseline) because triage still did its full exhaustive gather (it even pinged the connection itself), then the dedicated agent re-confirmed as an *extra hop*. Adding **route-early** (triage stops at the cause-naming signal and hands the confirm to the dedicated agent) cut the same case to **504s (−37%), CLI calls 24→5, score still 1.0**. Lesson: the bottleneck is triage over-gather + per-agent ceremony, not the generate/test hops.

## 5. Validation (coder-eval, default.yaml; ~+20% wall-clock under parallel batching)

| Case | Domain | Route | Score | Notes |
|---|---|---|---|---|
| connector-general-disabled | IS | dedicated/resolved | 1.0 | 504s isolated; the route-early win |
| connector-aggregate | IS | dedicated/resolved | 1.0 | unwrapped AggregateException → inner DAP-GE |
| connector-null-reference | IS | generic | 1.0 | opaque NRE — correctly NOT fast-resolved (no overhead) |
| connector-runtime-notfound | IS | generic | 1.0 | conservative route-early miss (safe) |
| no-host-pending | orchestrator | dedicated/resolved | 1.0 | NEW domain — drop-in agent, zero core edits |
| no-login-pending | orchestrator | dedicated/resolved | 1.0 | robot-credentials |
| logon-failure-password-mismatch | orchestrator | generic | 0.925 | medium multi-branch — correctly generic |
| invokevba-trust-access / -method-name / lookuprange-not-installed | excel | dedicated/resolved | 1.0 ×3 | proved mechanism works for activity packages too |
| excel-rr-sheet-typo | excel | generic | 1.0 | medium — correctly generic |
| faulted_excel_o365 | multi-system | dedicated→IS | 0.925 | routed to ROOT-CAUSE product (IS), not reporting (O365) |
| **maestro-stuck-rpa-job** | **OR+UIA+Maestro** | generic | **1.0** | after the §6 fix (was 0.4 before) |

**No false fast-resolves** — every opaque/multi-cause case correctly fell to generic. The safety property held.

## 6. Regression we hit — and the lesson

The hybrid changes **regressed the hard 3-system case** (`maestro-stuck-rpa-job`): **0.4**, scope missed **UI Automation**, 31 turns, wrong "parent cancelled" root cause — vs clean baseline **1.0**, scope `[orchestrator, maestro, ui-automation]`, 194 turns, correct **child UIA selector** root cause. Confirmed by stashing the changes and re-running clean.

**Cause:** SKILL.md edits **diluted the "Never skip the hypothesis loop" discipline** and over-promoted the loop-skip note, biasing the orchestrator to confirm a shallow parent-level cause and stop. NOT a routing bug; NOT triage E.1 (route-early didn't fire on this low-confidence case).

**Fix:** restored **full-loop-as-default** (loop-skip applies ONLY when `routing.path=="dedicated"` AND the dedicated agent resolved) and added an explicit **multi-system clause**: a stuck/hung/cancelled parent is a *symptom*; the loop MUST traverse into the referenced child job, fetch its logs/traces, expand scope to the child's domain, and test the child fault as the upstream cause before confirming. Re-test recovered to **1.0 / 3-domain / 208 turns / correct child-UIA root cause**.

> **THE LESSON:** for a root-cause skill, easy-case speed framing must never dilute hard-case full-loop + child-job-traversal discipline. **Correctness on hard multi-system cases outranks speed on easy ones.** Always regression-test a genuine multi-system case (not just easy single-domain) before trusting an optimization.

## 7. Conclusions
- **Dedicated agents are worth it only for platform products** with cause-naming error-code taxonomies (Integration Service, Orchestrator, Maestro) — NOT per activity package. Activity packages (excel, word, mail, …) are overwhelmingly medium/multi-cause; a per-package agent helps only a handful of HIGH signatures while adding maintenance. Built + validated an excel agent (3 HIGH cases at 1.0) then **removed it**; excel falls back to generic at 1.0. (Routing's graceful fallback means a missing dedicated agent costs nothing.)
- **The ceremony floor is ~500s even isolated** for a fast-resolve (≈5 cold-start sub-agent spawns + per-agent instruction re-reads + ~16 task-tracking calls). Going below it requires cutting *hops* (fewer agents), which trades against the separation-of-powers rigor.
- **Multi-system fast-resolve has a completeness tradeoff**: fast-resolving a cross-domain case (faulted_excel_o365) scored 0.925 vs 1.0 when run fully generic — the dedicated agent confirms the root cause but doesn't explore propagation domains. Open question: skip route-early when scope spans multiple propagation domains.

## 8. How to extend
Add a platform product's fast path: create `references/products/<product>/investigation_agent.md` following the IS/OR pattern (signature→playbook fast-resolve table + escalate table + canonical `routing` write). No SKILL.md or other agent edits needed — routing is file-existence based.

## 9. Status
All changes on this branch; built on bare `main` (does not include the genericization on `refactor/troubleshoot-generic-presenter` or the earlier fast-path on `feat/troubleshoot-fastpath`). Full run log + spec: `tests/reports/troubleshoot-hybrid-architecture-spec.md` (local/gitignored).
