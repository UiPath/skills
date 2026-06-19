# stages — Planning

A stage node inside the case. Stages contain tasks and connect via edges. Two variants (`stage` and `exception`) share the same plugin.

## Terminology

| Term | Same as |
|------|---------|
| Regular stage | `case-management:Stage` (default) |
| Exception stage | `case-management:ExceptionStage` |
| Secondary stage | Alias for exception stage. Sometimes used in sdd.md. |

The only difference between `stage` and `exception` is the JSON `type` value (`case-management:Stage` vs `case-management:ExceptionStage`). All other fields (label, description, entry/exit conditions, tasks, SLA) behave identically. `ExceptionStage` can carry `slaRules` (expression-driven SLA) the same as a regular Stage; conditional SLA rules themselves are root-only.

## When to Pick `exception` vs `stage`

Use exception (also "secondary stage") when the sdd.md describes any of:

- A handler for errors, escalations, or rejected items
- A rework / retry loop
- An on-error fallback
- A stage only reached via **interrupting** entry conditions
- Anything labeled "exception", "fallback", "on-error", or "secondary"

Otherwise default to a regular stage.

When ambiguous, use **AskUserQuestion** with both options + "Something else".

### Wiring constraints for exception / secondary stages

Exception stages **have no edges** — neither inbound nor outbound. They are fully detached from the edge graph:

- ❌ No edge into an exception stage (not from Triggers, not from regular stages, not from other exception stages).
- ❌ No edge out of an exception stage to any stage.
- ✅ **Reached via an interrupting entry condition** on the exception stage itself (fires based on case state, not by traversing an edge). See [stage-entry-conditions plugin](../conditions/stage-entry-conditions/planning.md).
- ✅ **Exits via a `return-to-origin` exit condition** — routes the case back to the stage it came from, through the exit condition rule, not a new edge. See [stage-exit-conditions plugin](../conditions/stage-exit-conditions/planning.md).

If the sdd.md describes an exception stage that is connected to other stages via edges, or that flows onward to another stage, flag this to the user. Options:

- Re-model the node as a regular stage (so edges are allowed).
- Use a `return-to-origin` exit and let the origin stage's existing edges handle the onward flow.

This constraint is also documented in the [edges plugin](../edges/planning.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `label` | sdd.md stage name | Shown in the UI. |
| `type` | sdd.md intent | `stage` (default) or `exception` — see above |
| `description` | sdd.md stage description | Optional. |
| `isRequired` | sdd.md (default `true` for regular, `false` for exception) | **Planning-only metadata.** See note below. |

### Note on `isRequired`

`isRequired` is written into the stage node's `data.isRequired` and is consumed downstream by case exit conditions with `rule-type: required-stages-completed` — the case completes when all stages flagged `isRequired: true` have completed.

Record `isRequired` in `tasks.md` for each stage. Use:
- `true` — **Default for regular stages.** Stage is on the main flow path and must complete for case completion.
- `false` — **Default for exception stages.** Exception / optional / fallback / rework stages only reached via conditional/interrupting entry conditions.

Implementation phase consumes this value when adding case-exit-conditions; the stage itself is created without it.

## Registry Resolution

**None.** Stages have no registry representation — no `taskTypeId`, no enrichment.

## Auto-Positioning

Stage position is auto-computed by the impl-json recipe: `x = 100 + (existingStageCount * 500), y = 200`. The planning entry does not carry coordinates unless the sdd.md specifies explicit ones.

## Ordering

Stages are created **after** the root case (T01) and **before** any edges, tasks, or conditions reference them. Each stage write produces a `StageId` — capture it in the planning/execution capture map. Downstream T-entries (edges, tasks, conditions, SLA) use the stage **name** in `tasks.md`; the implementation phase resolves the name to the captured `StageId`.

## tasks.md Entry Format

```markdown
## T<n>: Create stage "<label>"
- type: stage
- description: "<description from sdd.md>"
- isRequired: <true|false from sdd.md; false if unspecified>
- order: after T<m>
- verify: Confirm Result: Success, capture StageId
```

Exception variant:

```markdown
## T<n>: Create exception stage "<label>"
- type: exception
- description: "<description from sdd.md>"
- isRequired: <true|false from sdd.md; false if unspecified>
- order: after T<m>
- verify: Confirm Result: Success, capture StageId
```

## Unresolved Fallback

Stages have no registry lookup, so there is no "unresolved" path. If the sdd.md is missing stage names or descriptions, ask the user with **AskUserQuestion** rather than proceeding with placeholders.
