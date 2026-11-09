# stage-exit-conditions — Planning

Conditions controlling stage exit; attach one to a stage and fire it when its inbound rule is satisfied.

## When to Use

Use only when sdd.md literally says “stage exit condition” or a close variant: “stage exit conditions”, “stage completion condition”, or “exit rule on <stage>”. For stage entry, use [stage-entry-conditions](../stage-entry-conditions/planning.md).

## No omission — one caseplan element per sdd.md Exit Condition row

Every stage with an **Exit Condition** row gets its own stage-exit condition, including `exit-only`, `required-tasks-completed`, and `marks-stage-complete: true`. Never omit a written row as an obvious default; the build emits it.

## Required Fields from sdd.md

- `<stage-id>`: captured from the stages plugin; target stage.
- `display-name`: optional sdd.md Display Name, carried verbatim; omit blank / `—`; never invent. Implementation defaults to `Completion rule {N}` when `marks-stage-complete` is `true`, otherwise `Exit rule {N}`. If the cell already contains that pattern, echo the default; implementation renumbers it case-wide ([case-schema.md § Condition name uniqueness](../../../case-schema.md#condition-name-uniqueness)).
- `type`: `exit-only`, `wait-for-user`, or `return-to-origin`.
- `exit-to-stage-id`: optional routing target; required when routing to a specific stage.
- `marks-stage-complete`: sdd.md value; default depends on type. Use `true` for completion exits and `false` for diverging routes.
- `rule-type`: from the stage-exit catalog.
- `selected-tasks-ids`: required for `selected-tasks-completed`; comma-separated task IDs, each a non-adhoc sibling in the same stage.
- Connector fields from the SDD **Connector Rule Detail** block: `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, and optional `filter`; see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline).
- `condition-expression`: optional for any rule type: extra `=js:` gate on case state (`=js:vars.X ...`), never the event payload (no `event` namespace).
- `outputs`: optional SDD **Connector Rule Outputs** block: `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

## Exit Type Catalog

- `exit-only`: **Default.** Normal exit; the next stage is whichever entry condition matches, or `exit-to-stage-id` when set. Use no edges: routing is condition-driven.
- `wait-for-user`: manual user decision or approval is required.
- `return-to-origin`: rework / exception loop sending the case to the previous stage.

`return-to-origin` requires `marks-stage-complete: true` with `required-tasks-completed` or `wait-for-connector`. Never use `false` + `selected-tasks-completed`; that shape does not render as a return lane.

> **Routing the origin INTO a decision/signal-routed exception lane.** The origin stage carries the route: a gated divert exit (`marks-stage-complete: false`, `selected-tasks-completed("<decider>")`, `conditionExpression =js:(<signal> === <exception-value>)`, `exit-to-stage-id` → the lane) plus its completion exit gated by the inverse `IF`. They must be mutually exclusive: ungated completion causes dual-fire; gated completion without divert causes deadlock. The lane returns via `return-to-origin`. See [stage-exit-conditions/impl-json.md § Divert into an exception lane](impl-json.md#divert-into-an-exception-lane-gated-routing-exit) and the design-side divert-and-return contract (case SDD content contract § Logical integrity step 5, authored by `uipath-planner`).

## Rule-Type Catalog (stage-exit scope)

Allowed `ruleType` depends on `marks-stage-complete`:

| `marks-stage-complete` | Allowed `rule-type` | Required fields |
|---|---|---|
| `true` | `required-tasks-completed` | — |
| `true` | `wait-for-connector` | Connector fields (fills `uipath`); optional `conditionExpression`. |
| `false` (exit-only, routing) | `selected-tasks-completed` | `selectedTasksIds` (comma-separated). |
| `false` (exit-only, routing) | `wait-for-connector` | Connector fields (fills `uipath`); optional `conditionExpression`. |

Before planning `selected-tasks-completed`, verify selected tasks are not ad-hoc/manual. The frontend excludes ad-hoc tasks from selected-task dependency rules; if required routing depends on human activity, model it as a regular `action` task instead of `adhoc`.

## Ordering

Create stage exit conditions **after** all tasks in the stage so `selected-tasks-ids` can resolve. Planning records task names; implementation looks up captured IDs.

## Fields to Resolve

A condition produces **no `tasks/registry-resolved.json` entry** unless `rule-type` is `wait-for-connector` (see the note below the block). These are reasoning fields only; Phase 2 reads them from `sdd.md` ([planning.md § Step 4](../../../planning.md)).

```text
stage-exit condition on "<stage>" — <summary>
- target-stage: "<stage-name>"
- display-name: "<name>"                        # optional — omit when blank; impl defaults to "Completion rule {N}"/"Exit rule {N}" per marks-stage-complete
- type: exit-only
- exit-to-stage: "<target-stage-name>"          # optional
- marks-stage-complete: true
- rule-type: required-tasks-completed
- selected-tasks: "<Task A>, <Task B>"          # only if rule-type requires
- condition-expression: "=js:vars.X..."         # optional gate on case state, NOT the event payload
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields; see [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

<!-- END: planning.md -->