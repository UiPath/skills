# Resolution ledger — the one entry shape

THE definition of the resolution record that crosses the design→build boundary. The planner's lane keeps
it in memory; the build persists it verbatim as `tasks/registry-resolved.json` and extends it.

**[K-LEDG-1] Entry shape — exact keys, one object per resolved/attempted lookup:**

```jsonc
{
  "stage": "<SDD stage name>",          // associates the entry to one SDD declaration
  "task": "<SDD task name>",
  "taskType": "<K-TYP-1 value>",
  "cacheFile": "<basename actually searched, e.g. agent-index.json>",
  "searchQuery": "<the lookup string>",
  "matches": [ /* FULL exact-name match set from the refreshed cache — never a summary */ ],
  "selected": { /* adopted entry */ },  // or null after a genuine empty lookup
  "rationale": "<why>",
  "gateDecision": "pick:<name>" | "resolve-at-build" | "create-during-build"  // ONLY if the user answered
}
```

**[K-LEDG-2] `gateDecision` presence = user consent.** It exists ONLY for items the user actually answered
at the design-time resolution gate; the build executes it without re-asking (`resolve-at-build` →
placeholder; `create-during-build` → inline-create flow; `pick:` → bind that entry). A defaulted deferral
— no session, failed/pending pull, non-interactive run — carries NO `gateDecision` and gets the build's own
gate in full. Never treat a defaulted `resolve at build` as a user decision.

**[K-LEDG-3] Cache-state rule.** Before a successful `registry pull` this session, a missing cache
directory/file is a failed refresh precondition — never a zero-match result. Only after a successful pull
may an empty exact-name match set enter the empty-lookup flow. `matches` always reflects the cache
refreshed this session.

**[K-LEDG-4] Deep metadata stays out of the SDD.** Runtime metadata that does not affect plan replication
(agent prompts, package versions, endpoints, release tags) lives in this file under the task's entry, plus
each resolved contract's I/O (from `tasks describe` / `case spec`) and `review_items[]`. The SDD carries
name + folder + identity + sub-type only.

<!-- END: resolution-ledger.md -->
