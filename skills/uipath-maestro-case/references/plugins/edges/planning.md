# edges — Planning

Edges connect nodes in the case graph — Trigger → Stage, Stage → Stage, Stage → ExceptionStage, etc. Every stage must have at least one inbound edge or it will be orphaned.

## When to Use

Always. Every `tasks.md` has one edge entry per transition in the sdd.md flow graph. One plugin covers both edge variants (`TriggerEdge` and `Edge`) — the type is inferred from the source node's type in `schema.nodes`.

## Edge Types (inferred from source)

| Source node type | Target node type | JSON type |
|-------------------|------------------|-----------|
| Trigger | Stage | `case-management:TriggerEdge` |
| Stage | Stage | `case-management:Edge` |

The plugin's `impl-json.md` resolves the source node's `type` field in `schema.nodes` and writes the matching edge `type` automatically. The planning T-entry only records `source` and `target` names.

## Wiring Constraints

**Exception / secondary stages have no edges at all — neither inbound nor outbound.** Do not create any edge where `source` or `target` is an exception stage.

- ❌ `source: "<exception-stage-name>"` — never.
- ❌ `target: "<exception-stage-name>"` — never (applies to TriggerEdge and Edge alike).
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
| `label` | inferred (see § Labels) | Optional. Emit when sdd.md states one or an inference rule applies; otherwise leave blank. |
| `source-handle` | sdd.md (rarely specified) | `right` (default) \| `left` \| `top` \| `bottom` |
| `target-handle` | sdd.md (rarely specified) | `left` (default) \| `right` \| `top` \| `bottom` |

## Labels

Edge labels are **display-only** — they do not control routing. Routing conditions live on the source stage's `exitConditions`, not on the edge. Labels annotate intent so the diagram in Studio Web is readable (Studio Web renders this as the connector's "Name").

Labels may be blank. Emit one only when sdd.md states it explicitly or an inference rule below applies.

### Inference rules (apply in order)

1. **TriggerEdge** (source is a Trigger node) → label = `"Start"`. For multi-trigger cases, label = trigger displayName (e.g., `"Manual"`, `"On timer"`, `"On <event>"`).
2. **Stage→Stage with branching exit conditions in sdd.md** → label = matching branch outcome from the source stage's exit-condition text. Examples: `"Approved"`, `"Rejected"`, `"Timeout"`, `"Escalated"`. One edge per outcome → one label per outcome.

If sdd.md states an explicit edge label, use it verbatim and skip inference. Otherwise (e.g., Stage→Stage with single outbound and no branching), leave the label blank.

### Anti-patterns

- **Do NOT infer from edge index** (`"Edge 1"`, `"Edge 2"`) — meaningless to the user.
- **Do NOT read exit-condition text from another T-entry** — read directly from sdd.md, preserve plugin isolation.
- **Do NOT fabricate a label** when no inference rule applies — leave it blank.

## Handles

Handle directions control visual rendering (where the edge emerges from the source, where it enters the target). Defaults (`right` / `left`) match the horizontal left-to-right canvas layout. Only override when the sdd.md specifies a specific routing, e.g., an exception branch going down to a lower stage.

## Ordering

Edges are created **after** all stages exist so both endpoints can resolve. Each edge references the initial Trigger node (created by the triggers plugin at T02) or stage IDs captured in the stages capture map.

## tasks.md Entry Format

```markdown
## T<n>: Add edge "<source>" → "<target>"
- source: "<trigger-id-or-stage-name>"
- target: "<stage-name>"
- label: "<inferred or sdd.md-stated label>"   # optional, omit line when blank
- source-handle: right      # optional
- target-handle: left       # optional
- order: after T<m>
- verify: Confirm Result: Success, capture EdgeId
```

## Multi-Trigger Cases

When the sdd.md has multiple entry points (manual + timer + event), each non-default trigger is added via its plugin ([`plugins/triggers/`](../triggers/)), returning a `TriggerId`. Each trigger needs its own outgoing edge to the relevant first stage. Record one edge entry per trigger.

## Orphan Check

After all edges are planned, cross-check: every **regular stage** (type `stage`) in `tasks.md §4.4` must appear as a `target` in at least one edge entry. Missing → sdd.md has an orphan regular stage; flag to the user.

Exception stages are **excluded** from this check — they intentionally have no edges. Any exception stage present in `tasks.md` that also appears in an edge entry is an error (see Wiring Constraints above).
