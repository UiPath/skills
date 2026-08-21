# Design-Time Tenant Grounding

Full identity resolution at design time — registry pull, per-resource cache lookups, connection
checks, one batched gate — so a confirmed design carries resolved identities and the build's planning
pass verifies instead of re-discovering.

## Principles

1. Tenant work never blocks entry — nothing about the tenant is a prerequisite for designing.
2. Schema discovery is build work (`tasks describe` / `case spec`) — design resolves identities only.
3. One pull per session; a pull that succeeded this session is reused by the build. Never delay the
   confirmation waiting for a pull.
4. Registry data is evidence, not requirements — never add or rename business work to match tenant
   inventory; never dump catalogs into chat.

## The contract

1. **Intake batch.** Read every supplied document in parallel; extract named systems, resources,
   likely tasks, roles. Named systems seed grounding.
2. **Chain kickoff — background.** One background command: `uip login status --output json && uip
   maestro case registry pull`. Build handoff mode: start it AT LANE ENTRY, batched with the first
   document reads. Every other mode: start it at the first tenant-bound signal (a named
   system/resource/connector, or an inferred runnable/connector/action task); a case with no
   tenant-bound items never pulls. Best-effort — never block on it, never surface its output
   unprompted.
3. **Resolution pass — join, never wait.** When the sketch is complete and the pull succeeded,
   resolve every named or inferred resource in ONE parallel batch of cache lookups; for each connector
   also check enabled connections.

   | Bucket | Definition | Action |
   |---|---|---|
   | Single confident match | 1 exact-name match across all folders, ≥ 1 shared name token; connectors: exactly 1 enabled connection | Adopt: identity + exact folder into SDD cells + a resolution record; disclose as a decision line. The only silent pick |
   | Ambiguous | Multiple matches; cross-folder same name; no token overlap; > 1 enabled connection | Queue for the gate. A name deployed in ≥ 2 folders is always ambiguous — never pick a folder silently |
   | Empty | 0 matches / 0 enabled connections AFTER a successful pull | Queue for the gate |

   Cache files (`~/.uip/case-resources/`): agents `agent-index.json` · API workflows `api-index.json`
   · RPA processes `process-index.json` · orchestration processes `processOrchestration-index.json`
   · child cases `caseManagement-index.json` · Action Apps `action-apps-index.json` · connector
   activities/triggers `typecache-activities-index.json` / `typecache-triggers-index.json`.

4. **The ONE batched gate — at review time.** Queued items ride the Case Review turn
   ([review.md](review.md)) as one AskUserQuestion (≤ 4 questions; overflow carries into the
   confirmation's follow-up), grouped by `(name, type)` with usages listed. Options per group:
   **Pick a match** (candidates with folder FQNs); **Resolve at build** (identity stays `<UNRESOLVED>`
   + a paired review item; the build emits a placeholder); **Create during build** (ONLY for empty
   `agent` / `api-workflow` lookups — records the decision, the build executes it; the lane never
   scaffolds). Never pre-judge by name heuristics — the user's call. Pull unfinished when the review
   is ready → present with resolve-at-build on pending items; never wait.
5. **Visibility.** Every adopted identity, connection, gate decision, and deferral appears in the
   Case Review (Resources and Integrations + Decisions I Made) and lands in SDD Section 2 cells and
   the Section 4 roll-up. The resolution record below is machine-only — never user-facing.

## The resolution record

One record per resolved or attempted lookup, kept in memory by the lane; the build later persists the
set verbatim as `tasks/registry-resolved.json`:

```jsonc
{
  "stage": "<SDD stage name>",
  "task": "<SDD task name>",
  "taskType": "<task type>",
  "cacheFile": "<index basename actually searched>",
  "searchQuery": "<lookup string>",
  "matches": [ /* FULL exact-name match set from the refreshed cache — never a summary */ ],
  "selected": { /* adopted entry */ },        // null after a genuine empty lookup
  "rationale": "<why>",
  "gateDecision": "pick:<name>" | "resolve-at-build" | "create-during-build"  // only when the user answered
}
```

1. `gateDecision` present = the user answered the gate for that item; the build executes it without
   re-asking. A defaulted deferral (no session, failed or pending pull, non-interactive run) carries
   NO `gateDecision` — the build's own gate re-asks it.
2. Cache-state rule: before a successful pull this session, a missing cache file is a failed
   precondition — never a zero-match result. Only after a successful pull may an empty match set enter
   the empty-lookup flow.
3. Deep runtime metadata (agent prompts, package versions, endpoints, release tags) stays out of the
   SDD — the SDD carries name + folder + identity + sub-type; everything else rides this record.

## No session / failures

| Situation | Action |
|---|---|
| Not logged in, CLI absent, pull fails | One plain-language line the moment it happens: "I can't reach your UiPath tenant right now — I'll design with the names you give me and wire resources during the build." Keep concrete intended names; mark identities resolve-at-build (`<UNRESOLVED>` in the file) with paired review items; continue |
| Design-only / draft / plan-only runs | Skip grounding entirely — intended names stay concrete, identities resolve-at-build, report that resource wiring defers to the build run |
| Connector with zero enabled connections | A gate item — never a reason to change the task type |
