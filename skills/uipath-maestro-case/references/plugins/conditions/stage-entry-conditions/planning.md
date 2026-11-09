# stage-entry-conditions — Planning

Conditions controlling **when a stage is entered**; attach one to a stage and fire it when its inbound rule is satisfied.

## When to Use

Use this plugin when sdd.md declares a stage entry condition or a global event entering an interrupting secondary stage. For stage exit, use [stage-exit-conditions](../stage-exit-conditions/planning.md); for task start, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one caseplan element per sdd.md Entry Condition row

Every stage with an **Entry Condition** row gets its own stage-entry condition, including `case-entered` and `is-interrupting: false`. If sdd.md has the row, emit it; never omit it because values look default.

## Required Fields from sdd.md

| Field | Source and requirements |
|---|---|
| `<stage-id>` | Previously captured from the stages plugin; target stage. |
| `display-name` | sdd.md Display Name, optional. Carry a semantic value verbatim; omit blank / `—`; do not invent one. Impl defaults to `Entry rule {N}`; if that pattern is already in SDD, impl renumbers it case-wide ([case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness)). |
| `is-interrupting` | sdd.md, default `false`. `true` for every secondary-stage entry except an `sla-status-change` parallel-oversight row; otherwise `false` only for regular-stage entry. Carry the SDD value; never infer it from rule type or SLA scope. |
| `rationale` | sdd.md Design Rationale; required reviewer context for the rule/interrupt. Not emitted into caseplan JSON. |
| `rule-type` | Choose from the catalog below. |
| `selected-stage-id` | Required by `selected-stage-*`; referenced stage ID. |
| `sla-target` | `sla-status-change` argument 1: `"root"` (case SLA) or the SLA-owning stage name. Required; scopes both lookups to that SLA table. |
| `sla-display-name` | `sla-status-change` argument 2: target SDD `SLA Title` or Variable SLA Rules `Display Name`. Target-unique title resolving to the SLA rule ID emitted from §4.8 during Phase 2. Required. |
| `escalation-display-name` | `sla-status-change` argument 3: target SDD escalation-table `Display Name`, target-unique **at-risk** title resolving to its escalation ID. At-risk only; omit for breach. A breach references only the SLA; supplying an escalation makes it at-risk ([sla-response-shapes.md § Status](../../../sla-response-shapes.md)). |
| `connector fields` | SDD **Connector Rule Detail**: `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter`; resolve via [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline). |
| `condition-expression` | Optional for any rule type: extra `=js:` gate on case state (`=js:vars.X ...`), never the event payload (no `event` namespace). |
| `outputs` | Optional SDD **Connector Rule Outputs**: `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution). |

## Rule-Type Catalog (stage-entry scope)

| Rule type | Meaning | Extra fields |
|---|---|---|
| `case-entered` | Case entry signal; first-stage pattern. | — |
| `selected-stage-completed` | Fires when named upstream stage(s) complete. | `selectedStageIds` |
| `selected-stage-exited` | Fires when named upstream stage(s) exit, even without completion. | `selectedStageIds` |
| `user-selected-stage` | Fires when an upstream stage exits via `wait-for-user` and the user selects this stage next; only stages carrying this rule appear in the picker. | — |
| `wait-for-connector` | Waits for a connector event and binds an IS connector trigger under `uipath`. | Connector fields; `conditionExpression` optional. |
| `sla-status-change` | Fires when the referenced case/stage SLA breaches or reaches its at-risk escalation. Breach uses the 2-arg SDD cell `sla-status-change("<SLA target>","<SLA Title>")`; at-risk uses the 3-arg cell `sla-status-change("<SLA target>","<SLA Title>","<Escalation Display Name>")`. | `sla-target`, `sla-display-name`; `escalation-display-name` **at-risk only**. |

`is-interrupting: true` permits firing while another stage is active and interrupts it; use it on every secondary-stage entry. A candidate secondary stage with `false` is misclassified: use a regular stage/path or `adhoc` task. **Carve-out:** parallel-oversight `sla-status-change` on a secondary lane may be `false` when breached work continues and nothing is paused, taken over, or rerouted (`isRequired: false`, outside the completion set). `validate` accepts either value for `sla-status-change`; sdd.md is authoritative.

> **Global-event rule.** Declare once on the destination secondary stage any connector event that can occur during any primary stage and requires case work/routing, with `is-interrupting: true`. An SLA `enter-stage` response uses `sla-status-change` on the destination; set interruption from whether it stops, pauses, or reroutes active work, not SLA scope. A `start-task` response is not a stage-entry rule; put it on the follow-up task's entry ([task-entry-conditions/planning.md](../task-entry-conditions/planning.md)). Notify-only escalation needs no stage entry. Do not generate the same task or stage-exit rule on every primary stage.

> **First-stage start — `case-entered` is the case-start signal (Rule 21).** The case begins at the stage whose entry condition is `case-entered`, not a Trigger→first-stage edge. **At least one regular stage must carry `case-entered`**, or the case cannot start. Normally emit the first stage's declaration verbatim. If NO stage declares it, flag the user via AskUserQuestion; do NOT silently inject one (Rule 2 — trust sdd.md, no gap-fill). The design-side stage-graph reachability contract (case SDD content contract § Logical integrity, `uipath-planner`) treats no `case-entered` stage as a blocking orphan.

## Ordering

Create stage entry conditions **after** all stages exist (Step 7 in implementation.md), when both source and target stage IDs are captured.

## Fields to Resolve

A condition produces **no `tasks/registry-resolved.json` entry** unless its `rule-type` is `wait-for-connector` (see below). These are reasoning fields only; Phase 2 reads them from `sdd.md` ([planning.md § Step 4](../../../planning.md)).

```text
stage-entry condition on "<stage>" — <summary>
- target-stage: "<stage-name>"
- rationale: "<why this entry rule belongs on this stage>"
- display-name: "<name>"   # optional — omit when SDD Display Name cell is blank; impl defaults to "Entry rule {N}"
- is-interrupting: false
- rule-type: selected-stage-completed
- selected-stage: "<upstream-stage-name>"
- condition-expression: "=js:vars.X..."   # optional gate on case state, NOT the event payload
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

`sla-status-change` uses:

```text
stage-entry condition on "SLA Escalation" — case SLA breached
- target-stage: "SLA Escalation"
- rationale: "The case SLA can breach during any active stage, so one interrupting entry replaces per-stage exits."
- is-interrupting: true
- rule-type: sla-status-change
- sla-target: "root"
- sla-display-name: "Supplier Application SLA"
- verify: Confirm Result: Success, capture ConditionId
```

This is a breach, so omit `escalation-display-name`; the rule references the SLA alone. An at-risk response adds `escalation-display-name: "<At-risk escalation on that same SLA>"`; nothing else changes.

<!-- END: planning.md -->