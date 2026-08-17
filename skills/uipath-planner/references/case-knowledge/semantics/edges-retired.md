# Edges — retired

**[K-EDGE-1] Never author edges.** `schema.edges` stays `[]` (the key remains for FE compatibility).
Stage transitions derive entirely from entry/exit conditions; the case start derives from the first
stage's `case-entered` entry, not a TriggerEdge. The FE auto-derives canvas connectors from conditions.

**[K-EDGE-2] Condition-only reachability is therefore load-bearing.** With no edge graph to fall back on,
a malformed or missing entry condition is the only thing that can orphan a stage — the reachability walk
(K-STG-7) is the sole guard.

**[K-EDGE-3] Round-tripped files may contain FE-materialized edge objects.** Treat them as read-only:
never copy, adapt, or author one; model flow with conditions. Defensive stray-edge removal is a build-side
edit operation, not authoring.

<!-- END: edges-retired.md -->
