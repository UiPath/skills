# stages — Planning

A stage node inside the case. Stages contain tasks and connect via entry/exit conditions (Rule 20). Two variants (`stage` and `secondary`) share the same plugin.

## Terminology

| Term | Same as |
|------|---------|
| Regular stage | `case-management:Stage` (default) |
| Secondary stage | `case-management:Stage` with `data.stageType: "secondary"` |

The only difference is `data.stageType`: omitted for a primary/regular stage (do NOT emit `"primary"` — K-TYP-3), `"secondary"` for a secondary stage; both use `type: case-management:Stage`. All other fields (label, description, entry/exit conditions, tasks, SLA) behave identically. Primary and secondary stages can both carry conditional + default `data.slaRules[]`.

Secondary-stage semantics — interrupting exception lane, `isRequired: false`, excluded from `required-stages-completed`, every entry row interrupting with the SLA parallel-oversight carve-out, exits by intent — are K-STG-2/3/4 ([case-knowledge/semantics/stages.md](../../case-knowledge/semantics/stages.md)). Optional non-interrupting work is an `adhoc` task (K-SEQ-4), not a lane.

## When to Pick `secondary` vs `stage`

Use secondary (also "secondary stage") when the sdd.md describes any of:

- A handler for errors, escalations, or rejected items
- A rework / retry loop
- An on-error fallback
- A stage only reached via **interrupting** entry conditions
- A terminal or return lane that moves the case out of the active primary path
- Anything labeled "exception", "fallback", "on-error", or "secondary"

Otherwise default to a regular stage.

When ambiguous, use **AskUserQuestion** with both options + "Something else".

### Wiring constraints (reachability — edges retired)

No stage of either variant has edges; reachability is condition-only (K-EDGE-1/2, K-STG-7). Entry shapes per
lane trigger and global-event-once: K-STG-5/6. Build guidance: an SDD "A → B" arrow becomes B's entry
condition (`selected-stage-completed` / `selected-stage-exited` naming A), plus an A exit condition only
when A diverges; a regular stage with no entry condition is orphaned; onward flow from a returning lane is
`return-to-origin`. Plugins: [stage-entry-conditions](../conditions/stage-entry-conditions/planning.md) ·
[stage-exit-conditions](../conditions/stage-exit-conditions/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `label` | sdd.md stage name | Shown in the UI. |
| `type` | sdd.md intent | `stage` (default) or `secondary` — see above |
| `rationale` | sdd.md Design Rationale | Required reviewer context explaining the stage-kind and routing choice. A global-event secondary stage states why one interrupting entry replaces per-stage duplication. Not emitted into caseplan JSON. |
| `description` | sdd.md stage description | Optional. |
| `isRequired` | sdd.md — explicit `Yes`/`No` per stage, carried verbatim | Written into the node. See note below. |

### Note on `isRequired`

`isRequired` IS written into the stage node's `data.isRequired` at stage creation, and is also consumed by
case exit conditions with `rule-type: required-stages-completed` — the case completes when all stages
flagged `isRequired: true` have completed.

**No silent defaults (K-PAIR-5).** Absent ≡ false at the validator, silently removing the stage from
`required-stages-completed` and breaking case completion. The SDD declares Required per stage (design
default: primary `Yes`, secondary always `No`); every stage T-entry in `tasks.md` carries the explicit
value; a T-entry missing it is a plan defect → AskUserQuestion, never a fallback.

## Registry Resolution

**None.** Stages have no registry representation — no `taskTypeId`, no enrichment.

## Positioning

None. Stage nodes carry no coordinates (SKILL.md Rule 18 layout-strip — emit top-level `layout: {}`; the
FE auto-layouts). The planning entry never carries coordinates.

## Ordering

Stages are created **after** the root case (T01) and **before** any tasks or conditions reference them. Each stage write produces a `StageId` — capture it in the planning/execution capture map. Downstream T-entries (tasks, conditions, SLA) use the stage **name** in `tasks.md`; the implementation phase resolves the name to the captured `StageId`.

## tasks.md Entry Format

```markdown
## T<n>: Create stage "<label>"
- type: stage
- rationale: "<why this is a primary stage and how it is reached/exited>"
- description: "<description from sdd.md>"
- isRequired: <true|false — explicit from sdd.md; missing -> AskUserQuestion (K-PAIR-5)>
- order: after T<m>
- verify: Confirm Result: Success, capture StageId
```

Secondary variant:

```markdown
## T<n>: Create secondary stage "<label>"
- type: secondary
- rationale: "<why this is interrupting and which global/conditional event it handles>"
- description: "<description from sdd.md>"
- isRequired: <true|false — explicit from sdd.md; missing -> AskUserQuestion (K-PAIR-5)>
- order: after T<m>
- verify: Confirm Result: Success, capture StageId
```

## Unresolved Fallback

Stages have no registry lookup, so there is no "unresolved" path. If the sdd.md is missing stage names or descriptions, ask the user with **AskUserQuestion** rather than proceeding with placeholders.

<!-- END: planning.md -->
