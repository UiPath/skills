# stage-entry-conditions — Planning

Conditions that control **when a stage is entered**. Attach to a stage; fire when the inbound rule is satisfied.

## When to Use

Pick this plugin when the sdd.md declares a stage entry condition or a global event that enters an interrupting secondary stage.

For when a stage **exits**, use [stage-exit-conditions](../stage-exit-conditions/planning.md). For when a specific **task** starts, use [task-entry-conditions](../task-entry-conditions/planning.md).

## No omission — one T-task per sdd.md Entry Condition row

Every stage with an **Entry Condition** declared in sdd.md gets its own stage-entry-condition T-task — **including rule-type `case-entered`** and stages with `is-interrupting: false`. Never skip a condition because the rule-type or field values look like defaults. If sdd.md wrote the row, `tasks.md` emits the T-task.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `<stage-id>` | previously captured from the stages plugin | Target stage |
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Entry Rule {N}`. e.g., "Pre-check", "Interrupt on Fraud" |
| `is-interrupting` | sdd.md (default `false`) | `true` if the condition interrupts the current stage. Required for every secondary-stage entry row, except an `sla-status-change` parallel-oversight row; otherwise `false` is for regular-stage entry only. Carry the sdd.md value — never override it from the rule type or the SLA's scope. |
| `rationale` | sdd.md Design Rationale | Required reviewer context for why this rule/interrupt is used. Not emitted into caseplan JSON. |
| `rule-type` | Pick from the catalog below | See §Rule-type catalog |
| `selected-stage-id` | Required for `selected-stage-*` rule-types | ID of the referenced stage |
| `sla-target` | `sla-status-change` arg 1 | `"root"` (case-level SLA) or the SLA-owning stage name. Scopes both lookups below to that one SLA table. Required for `sla-status-change` |
| `sla-display-name` | `sla-status-change` arg 2 — the target's SDD `SLA Title` (or a Variable SLA Rules `Display Name`) | Target-unique SLA rule title; resolves to the SLA rule ID emitted from §4.8 during Phase 2. Required |
| `escalation-display-name` | `sla-status-change` arg 3 — a `Display Name` from that target's SDD escalation table | Target-unique **at-risk** escalation title; resolves to its escalation ID. **At-risk only** — omit for a breach response. A breach rule references the SLA alone; supplying an escalation converts it into an at-risk rule ([sla-response-shapes.md § Status](../../../sla-response-shapes.md)) |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — resolved via [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline) |
| `condition-expression` | Optional on any rule-type | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning). |

## Rule-Type Catalog (stage-entry scope)

Allowed `ruleType` values and when to pick each:

| Rule type | Meaning | Extra fields |
|-----------|---------|--------------|
| `case-entered` | Fires the moment the case is entered (first stage pattern) | — |
| `selected-stage-completed` | Fires when a specific upstream stage completes | `selectedStageId` |
| `selected-stage-exited` | Fires when a specific upstream stage exits (even without completing) | `selectedStageId` |
| `user-selected-stage` | Fires when an upstream stage exits via a `wait-for-user` exit condition and the user selects this stage as the next one. Only stages carrying this rule appear in the picker. | — |
| `wait-for-connector` | Waits for a connector event (binds an IS connector trigger under `uipath`) | connector fields (above); `conditionExpression` optional |
| `sla-status-change` | Fires when the referenced case/stage SLA breaches, or reaches the referenced at-risk escalation. Breach reads the 2-arg SDD cell `sla-status-change("<SLA target>","<SLA Title>")`; at-risk reads the 3-arg cell `sla-status-change("<SLA target>","<SLA Title>","<Escalation Display Name>")`. | `sla-target`, `sla-display-name`; `escalation-display-name` **at-risk only** |

`is-interrupting: true` means the condition can fire **while another stage is active** and will interrupt it. Use it on every secondary-stage entry row. If a candidate secondary stage would use `is-interrupting: false`, it is misclassified: use a regular stage/path or an `adhoc` task instead. **Carve-out:** an `sla-status-change` row whose response is parallel oversight — the breached work continues, nothing is paused, taken over, or rerouted — is legitimately `is-interrupting: false` on a secondary lane (`isRequired: false`, outside the completion set). `validate` accepts either value on an `sla-status-change` entry, so the sdd.md value is authoritative.

> **Global-event rule.** A connector event that can happen during any primary stage and requires case work/routing is declared once on the destination secondary stage with `is-interrupting: true`. An SLA response that enters a stage (`enter-stage`) uses `sla-status-change` on that destination stage. Set `is-interrupting` from whether the response stops, pauses, or reroutes active work, not from the SLA's scope. A `start-task` response is **not** a stage-entry rule — it belongs on the follow-up task's own entry ([task-entry-conditions/planning.md](../task-entry-conditions/planning.md)). A notify-only escalation needs no stage entry. Do not generate the same task or stage-exit rule on every primary stage.

> **First-stage start — `case-entered` is the case-start signal (Rule 20).** The case begins at the stage whose entry condition is `case-entered`, not a Trigger→first-stage edge. **At least one regular stage must carry `case-entered`**, or the case can never start. The sdd.md's first stage normally declares it — emit it verbatim. If NO stage declares `case-entered`, flag to the user via AskUserQuestion; do NOT silently inject one (Rule 2 — trust the sdd.md, no gap-fill). The reachability walk in the design-side stage-graph contract (case SDD content contract § Logical integrity, `uipath-planner`) treats a case with no `case-entered` stage as a blocking orphan.

## Ordering

Stage entry conditions are created **after** all stages exist (Step 7 in implementation.md). Source/target stage IDs must both be captured by then.

## tasks.md Entry Format

```markdown
## T<n>: Add stage-entry condition for "<stage>" — <summary>
- target-stage: "<stage-name>"
- rationale: "<why this entry rule belongs on this stage>"
- display-name: "<name>"   # optional — omit when SDD Display Name cell is blank; impl defaults to "Entry Rule {N}"
- is-interrupting: false
- rule-type: selected-stage-completed
- selected-stage: "<upstream-stage-name>"
- condition-expression: "=js:vars.X..."   # optional gate on case state, NOT the event payload
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § tasks.md fields (planning)](../../../connector-trigger-planning.md#tasksmd-fields-planning).

`sla-status-change` example:

```markdown
## T<n>: Add stage-entry condition for "SLA Escalation" — case SLA breached
- target-stage: "SLA Escalation"
- rationale: "The case SLA can breach during any active stage, so one interrupting entry replaces per-stage exits."
- is-interrupting: true
- rule-type: sla-status-change
- sla-target: "root"
- sla-display-name: "Supplier Application SLA"
- order: after T<m>
- verify: Confirm Result: Success, capture ConditionId
```

Breach, so **no `escalation-display-name`** — the rule references the SLA alone. An at-risk response adds `escalation-display-name: "<At-risk escalation on that same SLA>"`; nothing else changes.

<!-- END: planning.md -->
