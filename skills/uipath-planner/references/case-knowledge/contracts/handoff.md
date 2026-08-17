# Design handoff — the one protocol

THE definition of how a case build request without an `sdd.md` becomes a design and returns to the build.
Both skills point here; neither restates it. (`uipath-planner` = "the lane"; `uipath-maestro-case` = "the
build".)

**[K-HOF-1] Trigger.** The build detects no `sdd.md` at the resolved path (or a case `sdd.draft.md`
finalization request). It hands off IMMEDIATELY — before reading its own references, hunting the
filesystem, or running tenant commands — by loading `uipath-planner` and entering its Case Design Lane in
**Build handoff** mode, in THIS conversation, never a subagent. The in-memory model, resolution ledger, and
the session's registry pull cross the skill boundary for free. The build never designs: no improvised
interview, no design subagents, no generic "Build Plan" checkpoint. If `uipath-planner` is unavailable:
one line saying so, ask the user for an `sdd.md` (or a pasted design to build from), stop.

**[K-HOF-2] The lane owns everything through the SDD write:** best-assumption design with the user,
mandatory other-path sweep, design-time tenant grounding with ONE batched resolution gate, and ONE
confirmation — the decision-first, eight-section **Case Review** (Case Snapshot, Primary Journey, Other
Paths Considered, SLA and Escalations, Rules and Outcomes, Resources and Integrations, Decisions I Made,
Review Flags; + the conditional Caller-obligation block). It names every stage and task with type,
activation/grouping, required status, routing, and SLA context; it deliberately omits the data contract,
variables, and task I/O (complete in `sdd.md`). It is the ONLY approval surface — a user "Yes" to any
generic plan must not create files. The Build options fold in the build-review preference
(`straight through` / `pause at the build preview`; relabeled `Build despite N flagged items` when ⚠ flags
exist). Corrections re-show only changed sections.

**[K-HOF-3] The Build answer IS the consent.** On it the lane writes `sdd.md` at the working root
(write-early cadence; never overwriting an existing one — presence = trust-as-written, abort and surface),
`Status: ready`, and the build resumes immediately in the same conversation — `uip solution init` + its
Phase 1 — with no extra approval prompt (an explicit sign-off request adds exactly one). User-facing
language never mentions the handoff: one continuous flow.

**[K-HOF-4] What crosses the boundary.** (a) `sdd.md` — the contract, trusted as written; (b) the
in-memory model; (c) the resolution ledger entries ([resolution-ledger.md](resolution-ledger.md)) — the
build's Phase 1 persists them verbatim to `tasks/registry-resolved.json` and verifies instead of
re-resolving; (d) the session's registry pull (build reuses the cache when the lane's pull succeeded this
session). Gate decisions the user actually answered are executed without re-asking; defaulted deferrals
(no `gateDecision`) get the build's own gate.

**[K-HOF-5] Scope of the handoff.** Design, standalone-draft, and draft-finalization requests invoked
directly belong to the planner (the build builds only). Cross-product planning beyond the case stays a
plain-text suggestion of `uipath-planner` — no handoff. The build's receipt check for SDDs it did not watch
being written: [sdd-contract.md § Receipt check](sdd-contract.md).

<!-- END: handoff.md -->
