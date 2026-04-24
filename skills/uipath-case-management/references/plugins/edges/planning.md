# edges — Planning

Edges connect nodes in the case graph — Trigger → Stage, Stage → Stage, Stage → ExceptionStage, etc. Every stage must have at least one inbound edge or it will be orphaned.

## When to Use

Always. Every `tasks.md` has one edge entry per transition in the sdd.md flow graph. One plugin covers both edge variants (`TriggerEdge` and `Edge`) — the CLI infers the type from the source node.

## Edge Types (CLI-inferred)

| Source node type | Target node type | JSON type |
|-------------------|------------------|-----------|
| Trigger | Stage | `case-management:TriggerEdge` |
| Stage | Stage | `case-management:Edge` |

You do not specify the edge type — `uip maestro case edges add` figures it out from the `--source` node's type.

## Wiring Constraints

**Exception / secondary stages have no edges at all — neither inbound nor outbound.** Do not create any edge where `--source` or `--target` is an exception stage.

- ❌ `--source <exception-stage-id>` — never.
- ❌ `--target <exception-stage-id>` — never (applies to TriggerEdge and Edge alike).
- ✅ Exception stages are **reached via an interrupting entry condition** on the exception stage itself, not via an edge. See [stage-entry-conditions plugin](../conditions/stage-entry-conditions/planning.md).
- ✅ Exception stages **exit via a `return-to-origin` exit condition**, not via an outbound edge. See [stage-exit-conditions plugin](../conditions/stage-exit-conditions/planning.md).

If the sdd.md describes an exception stage with edges, flag to the user: re-model as a regular stage, or use the conditions-only pattern above.

### Orphan check scope

The orphan check in the planning pipeline applies to **regular stages only** — every regular stage must be the target of at least one edge. Exception stages intentionally have no edges and are not orphans.

This constraint is also documented in the [stages plugin](../stages/planning.md#wiring-constraints-for-exception--secondary-stages).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `source` | sdd.md flow arrow origin | Trigger ID or stage name |
| `target` | sdd.md flow arrow destination | Stage name |
| `label` | sdd.md edge label | Optional. Human-readable label on the connector. |
| `source-handle` | sdd.md (rarely specified) | `right` (default) \| `left` \| `top` \| `bottom` |
| `target-handle` | sdd.md (rarely specified) | `left` (default) \| `right` \| `top` \| `bottom` |

## Labels

Edge labels are **display-only** — they do not control routing. Routing conditions live on the source stage's `exitConditions`, not on the edge. Use labels to annotate the intent ("Approved", "Rejected", "On timeout") so the diagram in Studio Web is readable.

## Handles

Handle directions control visual rendering (where the edge emerges from the source, where it enters the target). Defaults (`right` / `left`) match the horizontal left-to-right canvas layout. Only override when the sdd.md specifies a specific routing, e.g., an exception branch going down to a lower stage.

## Ordering

Edges are created **after** all stages exist so both endpoints can resolve. Each edge references the initial Trigger node (created by `cases add` in T01) or stage IDs captured in the stages capture map.

## tasks.md Entry Format

```markdown
## T<n>: Add edge "<source>" → "<target>"
- source: "<trigger-id-or-stage-name>"
- target: "<stage-name>"
- label: "<optional label>"
- source-handle: right      # optional
- target-handle: left       # optional
- order: after T<m>
- verify: Confirm Result: Success, capture EdgeId
```

## Multi-Trigger Cases

When the sdd.md has multiple entry points (manual + timer + event), each non-default trigger is added via its plugin ([`plugins/triggers/`](../triggers/)), returning a `TriggerId`. Each trigger needs its own outgoing edge to the relevant first stage. Record one edge entry per trigger.

## Orphan Check

After all edges are planned, cross-check: every **regular stage** (`--type stage`) in `tasks.md §4.4` must appear as a `target` in at least one edge entry. Missing → sdd.md has an orphan regular stage; flag to the user.

Exception stages are **excluded** from this check — they intentionally have no edges. Any exception stage present in `tasks.md` that also appears in an edge entry is an error (see Wiring Constraints above).
