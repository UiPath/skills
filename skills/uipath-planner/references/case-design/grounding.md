# Design-time tenant grounding & connector checks

The single home for design-time resolution. The lane does **full identity resolution** — registry pull,
per-resource cache lookups, connection checks, one batched gate — so a confirmed design carries resolved
identities and the build's planning pass becomes verify-only. Ledger shape + gateDecision semantics:
K-LEDG-1..4.

## Principles

1. **Tenant work never blocks Entry.** Nothing about the tenant is a prerequisite for designing.
2. **Schema discovery is NOT design work.** `tasks describe` / `case spec` stay in the build phases;
   design resolves identities only.
3. **Never pull twice per session.** A pull that succeeded this session is reused by the build
   (same-session fast path). Never delay the confirmation waiting for a pull.
4. **Registry data is evidence, not requirements** — never add/rename business work to match tenant
   inventory; never dump catalogs into chat.

## The 5-step contract

1. **Intake batch.** Read every supplied document in parallel; extract named systems, resources, likely
   tasks, roles. Named systems seed grounding.
2. **Chain kickoff — background.** ONE background command: `uip login status --output json && uip maestro
   case registry pull`. **Build handoff mode:** start it AT LANE ENTRY, batched with the first document
   reads (the build needs a fresh registry unconditionally; entry-time start lets resolution land before
   the Case Review). **Every other mode:** start it the FIRST moment the sketch identifies tenant-bound
   work (named system/resource/connector, or an inferred runnable/connector/action task); a case with no
   tenant-bound items never pulls. Best-effort: never block on it, never surface its output unprompted.
3. **Resolution pass — join, never wait.** When the sketch is complete and the pull succeeded, resolve
   every named or inferred resource in ONE parallel batch of cache lookups; for each connector also check
   enabled connections. Bucket each result:

   | Bucket | Definition | Action |
   |---|---|---|
   | Single confident match | 1 exact-name match across all folders, ≥ 1 shared name token; connectors: exactly 1 enabled connection | **Adopt**: identity + exact folder into SDD cells + ledger entry; disclose as a decision line. The only silent pick. |
   | Ambiguous | Multiple matches, cross-folder same-name, no token overlap; > 1 enabled connection | Queue for the gate. A name deployed in ≥ 2 folders is ALWAYS ambiguous — never pick a folder silently. |
   | Empty | 0 matches / 0 enabled connections AFTER a successful pull | Queue for the gate. A missing cache file BEFORE a successful pull is a failed precondition, never a zero-match result (K-LEDG-3). |

   Cache-file map (`~/.uip/case-resources/`):

   | Resource | Index |
   |---|---|
   | Agents | `agent-index.json` |
   | API workflows | `api-index.json` |
   | RPA processes | `process-index.json` |
   | Orchestration processes | `processOrchestration-index.json` |
   | Child cases | `caseManagement-index.json` |
   | Action Apps (HITL) | `action-apps-index.json` |
   | Connector activities / triggers | `typecache-activities-index.json` / `typecache-triggers-index.json` |

4. **Resolution gate — the ONE batched ask, at review time.** Present queued items WITH the Case Review —
   one AskUserQuestion (≤ 4 questions; overflow carries into the confirmation's follow-up), grouped by
   `(name, type)` with usages listed. Options per group:
   - **Pick a match** — candidates listed with folder FQNs; user picks one or `resolve at build`.
   - **Resolve at build** — identity stays `<UNRESOLVED>` + paired review item; the build emits a
     placeholder the user upgrades later.
   - **Create during build** — ONLY for empty `agent` / `api-workflow` lookups; records the decision, the
     BUILD executes inline-create (the lane never scaffolds or spawns build subagents). Non-creatable
     kinds (RPA process, action, case-management, connectors, agentic process) show `resolve at build`
     only.

   Never pre-judge by name heuristics — the user's call. Pull not finished when the review is ready → do
   not wait; present with `resolve at build` on pending items. `gateDecision` is recorded ONLY for items
   the user actually answered (K-LEDG-2); every defaulted deferral records `resolve at build` WITHOUT one,
   so the build's own gate re-asks it. The gate runs ONCE for what the user ruled on — the build must not
   re-ask those and MUST still ask about everything defaulted.
5. **Visibility.** Every adopted identity, connection, gate decision, and deferral appears in the Case
   Review (Resources and Integrations + Decisions I Made) and lands in SDD Section 2 cells + the Section 4
   roll-up. The ledger itself is machine-only — never user-facing.

## No-session / failure behavior

| Situation | Action |
|---|---|
| Not logged in, CLI absent, pull fails | One plain-language line the moment it happens (`I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build.`). Keep concrete intended names; mark every identity `resolve at build` (`<UNRESOLVED>` in the file) + paired review items; continue — the design stays complete. Never let `resolve at build` rows be the first signal. |
| Design-only / draft / plan-only runs | Skip grounding entirely — preserve intended names, mark identities `resolve at build`, report that resource wiring defers to the build run. |
| Connector with zero enabled connections | A gate item — never a reason to change the task type. |

<!-- END: grounding.md -->
