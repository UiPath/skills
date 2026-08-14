# case-exit-conditions — Planning

Conditions that control **when the entire case completes (or exits non-completing)**. Attach at the case root level, not to any stage.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "case exit condition"** (or close variants: "case exit conditions", "case completion condition", "case close condition").

For stage-level conditions, use [stage-entry-conditions](../stage-entry-conditions/planning.md) / [stage-exit-conditions](../stage-exit-conditions/planning.md). For task-level, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one T-task per sdd.md case-exit row

Every case-exit condition declared in sdd.md gets its own T-task — **including the positive completion rule** carrying `marks-case-complete: true`, whatever its rule type. Never skip a condition because it looks like a default completion shape. If sdd.md wrote the row, `tasks.md` emits the T-task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Complete Rule {N}` (marks-case-complete `true`) / `Exit Rule {N}` (`false`). e.g., "Case resolved", "Closed — escalation path" |
| `marks-case-complete` | sdd.md | `true` for normal completion, `false` for non-completing exits |
| `rule-type` | From catalog below | See §Rule-type catalog |
| `selected-stage-id` | Required for `selected-stage-*` rule-types | Resolved from stage capture map. Use `selected-stages` (a list of stage names) instead when one condition must close on any of several terminals — impl emits one OR'd rule-set per name. |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline) |
| `condition-expression` | Optional on any rule-type | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning). |

## Rule-Type Catalog (case-exit scope)

`ruleType` is **not** gated by `marks-case-complete`. Every rule type below is legal with `marks-case-complete: true`; every one except `required-stages-completed` is also legal with `false`. The frontend's "Complete case when" picker offers exactly these five.

| Rule type | Case completes when | Deterministic? | Extra fields |
|-----------|---------------------|----------------|--------------|
| `required-stages-completed` | every stage with `isRequired: true` has **completed** | yes | — |
| `selected-stage-completed` | the named stage has **completed** | yes | `selectedStageId` |
| `selected-stage-exited` | the named stage has been **exited** (left without completing) | yes | `selectedStageId` |
| `sla-status-change` | the referenced SLA breaches or reaches its at-risk escalation | **no — contingent** | `slaId`, optional `escalationId` |
| `wait-for-connector` | an external connector event arrives | **no — contingent** | connector fields; `conditionExpression` optional |

**Deterministic vs contingent.** A contingent rule fires only if something outside the case graph happens — a clock running out, an external system calling in. It may close the case, but it cannot be relied on to. **Every case needs at least one deterministic completion rule**, unless closure is deliberately delegated to a Case Manager agent (`metadata.caseManagerData.enabled: true`), which decides case resolution outside `caseExitRules` entirely.

> `sla-status-change` at case-exit scope is offered by the Studio Web "Complete case when" picker (verified 2026-08-14). It has not been probed against this skill's v27 emission target — prefer a deterministic rule for the primary closure and treat an SLA-driven close as an addition, not a replacement.

## Choosing the closure shape

This is a **choice**, not a default. Pick before writing any case-exit T-task.

**Use `selected-stage-completed` on each terminal stage** when the case has more than one terminal outcome (executed / rejected / withdrawn), or when any stage can be bypassed by an SLA bump, escalation, stall, or early exit. Declare the terminals with `selected-stages` (plural) on **one** T-task — impl emits one OR'd rule-set per stage inside a **single** condition, so any terminal closes the case:

```markdown
## T<n>: Add case-exit condition — case closes at any terminal
- display-name: "Case Closed"
- marks-case-complete: true
- rule-type: selected-stage-completed
- selected-stages: ["Contract Executed", "Contract Rejected", "Contract Withdrawn"]
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

Keep the alternatives inside one condition. The outer `rules[]` array is OR and that is verified; whether the runtime ORs across *separate* `caseExitRules[]` entries is not, so never split one logical closure across several conditions.

**Use `required-stages-completed`** only when the case has a single terminal outcome and every `isRequired` stage is genuinely unbypassable. It compiles to a literal list of every `isRequired` primary stage, and **an exited stage never satisfies it** — `stagesCompleted` and `stagesExited` are disjoint at runtime with no union on the completion path. One stage that routes onward through a `marks-stage-complete: false` exit permanently blocks this rule. See [stage-exit-conditions/impl-json.md § Exiting is not completing](../stage-exit-conditions/impl-json.md#exiting-is-not-completing).

**Reachability check before you finish.** For every terminal state the case can reach, at least one completion rule must be able to fire. Walk each path in the SDD — including every exception, timeout, stall and rework route — and name the rule that closes it. A path with no rule is a case that hangs; `uip maestro case validate` does not detect it.

## What `marks-case-complete` actually does

It is **designer-side metadata and is not serialized into the executable plan.** FE validation requires at least one condition with `true` (otherwise "Case has no completion rules"), and the rules table renders "Complete Case" vs "Exit Case" from it — but the converter emits **every** `caseExitRules[]` entry into `case.completionConditions` regardless of its value.

Consequence: a `marks-case-complete: false` rule still closes the case at runtime. Set it to `false` to express intent for rejection / withdrawal / cancellation outcomes and to keep the designer readable — never to prevent closure, and never model runtime behaviour on it. The completed-vs-exited distinction the runtime acts on is `caseResolution.type`, which is produced by the scheduler, not by this flag.

## Ordering

Case exit conditions are created **after** all stages exist (so `selectedStageId` can resolve via the stage capture map). In `tasks.md`, place these between stage conditions and SLA.

## tasks.md Entry Format

```markdown
## T<n>: Add case-exit condition — <summary>
- display-name: "<name>"                 # optional — omit when blank; impl defaults to "Complete Rule {N}"/"Exit Rule {N}" per marks-case-complete
- marks-case-complete: true
- rule-type: required-stages-completed
- selected-stage: "<stage-name>"        # only for selected-stage-* rule-types
- selected-stages: ["<stage-a>", "<stage-b>"]  # selected-stage-* only; one OR'd rule-set per name, inside ONE condition
- condition-expression: "=js:vars.X..."  # optional gate on case state, NOT the event payload
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

> Use `selected-stage` **or** `selected-stages`, never both on the same T-task.

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning).

<!-- END: planning.md -->
