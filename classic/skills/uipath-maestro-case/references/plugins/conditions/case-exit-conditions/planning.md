# case-exit-conditions — Planning

Conditions controlling when the entire case completes or exits without completing. Attach them at the case root, not to a stage.

## When to Use

Use this plugin when sdd.md literally uses "case exit condition" or a close variant: "case exit conditions", "case completion condition", or "case close condition". For stage-level conditions, use [stage-entry-conditions](../stage-entry-conditions/planning.md) / [stage-exit-conditions](../stage-exit-conditions/planning.md); for task-level conditions, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one caseplan element per sdd.md case-exit row

Emit one caseplan element for every case-exit condition in sdd.md, including `required-stages-completed` with `marks-case-complete: true`; never omit a written row, including the default completion shape.

## Required Fields from sdd.md

- `display-name` (sdd.md Display Name column, optional): Carry a semantic SDD value verbatim, e.g. "Case resolved", "Closed — escalation path". Omit when the cell is blank / `—` — do NOT invent one; impl defaults it to `Completion rule {N}` (marks-case-complete `true`) / `Exit rule {N}` (`false`). A cell already holding that default pattern is the SDD echoing the default, so impl renumbers it case-wide ([case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness)).
- `marks-case-complete`: sdd.md `true` for normal completion; `false` for non-completing exits.
- `rule-type`: Use the catalog below.
- `selected-stage-id`: Required for `selected-stage-*` rule-types; resolve from the stage capture map.
- Connector fields: SDD **Connector Rule Detail**: `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, and optional `filter`; see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline).
- `condition-expression`: Optional for any rule-type: extra `=js:` gate on **case state** (`=js:vars.X ...`), not the event payload; there is no `event` namespace.
- `outputs`: Optional SDD **Connector Rule Outputs**: `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

## Rule-Type Catalog (case-exit scope)

Allowed `ruleType` values depend on `marks-case-complete`:

- `true`: `required-stages-completed` (**Preferred**; completes when every stage whose node `data.isRequired` is `true` has completed; no stage list) or `wait-for-connector` (waits for an external connector event to close the case; fills `uipath`; connector fields and optional `conditionExpression`).
- `false`: `selected-stage-completed` (named stage(s) complete), `selected-stage-exited` (named stage(s) exit, even without completing), or `wait-for-connector` (waits for an external connector event; fills `uipath`; connector fields and optional `conditionExpression`). The stage rules use `selectedStageIds`.

## Preferred Pattern

Normally define one completion condition: `required-stages-completed` + `marks-case-complete: true`; each stage's `isRequired` flag (from [`plugins/stages/`](../../stages/planning.md)) determines which stages count.

At least one root `caseExitRules[]` entry must have `marksCaseComplete: true`, or the case cannot close. Stage completion is separate: a stage exit with `marksStageComplete: true` advances the case but does not complete it. Add `marks-case-complete: false` only for explicit non-completing exits such as rejection, withdrawal, or cancellation; they do not replace the positive completion rule.

Choose `marksCaseComplete` by objective achievement, not merely case termination:

| Outcome in the SDD | `marksCaseComplete` |
|---|---|
| Work finished — approved, fulfilled, paid, resolved | `true` |
| Work not done — rejected, withdrawn, cancelled, abandoned, timed out | `false` |
| Handed off, escalated out, or closed by exception | `false` |

**A word like "closed", "ends", or "complete" in the prose is not the signal — the signal is whether the objective was met.** An SDD that says an outcome is *not the same as* normal completion, or names it alongside a separate completion path, is describing a non-completing exit however it phrases the ending: "closed as escalated" ends the case and does not complete it. These are not rare — any case with a rejection or escalation path has one.

## Ordering

Create case exit conditions **after** all stages exist so `selectedStageIds` can resolve through the stage capture map. In execution order, place them between stage conditions and SLA.

## Fields to Resolve

A condition produces **no `tasks/registry-resolved.json` entry** unless its `rule-type` is `wait-for-connector`. These are reasoning fields only; Phase 2 reads them from `sdd.md` ([planning.md § Step 4](../../../planning.md)).

```text
case-exit condition — <summary>
- display-name: "<name>"                 # optional — omit when blank; impl defaults to "Completion rule {N}"/"Exit rule {N}" per marks-case-complete
- marks-case-complete: true
- rule-type: required-stages-completed
- selected-stage: "<stage-name>"        # only for selected-stage-* rule-types
- condition-expression: "=js:vars.X..."  # optional gate on case state, NOT the event payload
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

<!-- END: planning.md -->
