# stage-exit-conditions — Planning

> **Required reads** — open each in full (a single `cat`, or the `Read` tool) before writing this
> construct. These are not optional context; the checks that grade this work live in them.
> - [`connector-trigger-planning.md`](../../../connector-trigger-planning.md) — connector resolution before you write the rule

Conditions that control **when and how a stage exits**. Attach to a stage; fire when the inbound rule is satisfied.

## When to Use

Pick this plugin when the sdd.md **literally uses the phrase "stage exit condition"** (or close variants: "stage exit conditions", "stage completion condition", "exit rule on <stage>").

For when a stage **enters**, use [stage-entry-conditions](../stage-entry-conditions/planning.md).

## No omission — one caseplan element per sdd.md Exit Condition row

Every stage with an **Exit Condition** declared in sdd.md gets its own stage-exit condition — **including type `exit-only`, rule-type `required-tasks-completed`, and `marks-stage-complete: true`**. Never skip a condition because it looks like "the obvious default completion." If sdd.md wrote the row, the build emits the element.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `<stage-id>` | Captured from the stages plugin | Target stage |
| `display-name` | sdd.md Display Name column (optional) | Carry the SDD value verbatim. Omit when the SDD cell is blank / `—` — do NOT invent one; impl defaults it to `Complete Rule {N}` (marks-stage-complete `true`) / `Exit Rule {N}` (`false`). |
| `type` | sdd.md exit style | `exit-only` / `wait-for-user` / `return-to-origin` |
| `exit-to-stage-id` | sdd.md routing target (optional) | Required when routing to a specific stage |
| `marks-stage-complete` | sdd.md (default depends on type) | `true` for completion exits, `false` for diverging routes |
| `rule-type` | From catalog below | |
| `selected-tasks-ids` | Required for `selected-tasks-completed` | Comma-separated task IDs. Selected tasks must be non-adhoc siblings in the same stage. |
| `connector fields` | SDD **Connector Rule Detail** block | `type-id` (activity-type-id), `connector-key`, `connection-id`, `object-name`, `event-operation`, `event-mode`, `input-values`, optional `filter` — see [connector-trigger-planning.md § Planning Pipeline](../../../connector-trigger-planning.md#planning-pipeline) |
| `condition-expression` | Optional on any rule-type | Extra `=js:` gate on **case state** (`=js:vars.X ...`) — NOT the event payload (no `event` namespace) |
| `outputs` | SDD **Connector Rule Outputs** block | Optional. `->` (extract field → case var) or `=` (assign expression → case var). See [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution). |

## Exit Type Catalog

| Exit `type` | When to pick |
|-------------|--------------|
| `exit-only` | **Default.** Stage exits normally; the next stage is whichever one's entry condition matches (or `exit-to-stage-id` when set). No edges — routing is condition-driven. |
| `wait-for-user` | Exit requires manual user decision or approval. |
| `return-to-origin` | Rework / exception loop — sends the case back to the previous stage. |

`return-to-origin` uses the completion pairing: `marks-stage-complete: true` with `required-tasks-completed` (or `wait-for-connector`). Never plan it as `false` + `selected-tasks-completed`; that routing shape does not render as a return lane.

> **Routing the origin INTO a decision/signal-routed exception lane.** The origin stage carries the route: a gated divert exit (`marks-stage-complete: false`, `selected-tasks-completed("<decider>")`, `conditionExpression =js:(<signal> === <exception-value>)`, `exit-to-stage-id` → the lane) PLUS its completion exit gated by the inverse `IF`. The two must be mutually exclusive (ungated completion → dual-fire; gated completion with no divert → deadlock). The lane returns via `return-to-origin`. See [stage-exit-conditions/impl-json.md § Divert into an exception lane](impl-json.md#divert-into-an-exception-lane-gated-routing-exit) and the design-side divert-and-return contract (case SDD content contract § Logical integrity step 5, authored by `uipath-planner`).

## Rule-Type Catalog (stage-exit scope)

Allowed `ruleType` values depend on `marks-stage-complete`:

**When `marks-stage-complete: true`:**
| Rule type | Extra fields |
|-----------|--------------|
| `required-tasks-completed` | — |
| `wait-for-connector` | connector fields (fills `uipath`); `conditionExpression` optional |

**When `marks-stage-complete: false` (exit-only, routing):**
| Rule type | Extra fields |
|-----------|--------------|
| `selected-tasks-completed` | `selectedTasksIds` (comma-separated) |
| `wait-for-connector` | connector fields (fills `uipath`); `conditionExpression` optional |

Before planning `selected-tasks-completed`, verify the selected tasks are not ad-hoc/manual tasks. The frontend excludes ad-hoc tasks from selected-task dependency rules; if required routing depends on a human activity, model that human work as a regular `action` task instead of an `adhoc` task.

## Ordering

Stage exit conditions are created **after** all tasks in the stage have been added (so `selected-tasks-ids` can resolve). Planning records task names; implementation looks up captured IDs.

## Fields to Resolve

A condition produces **no `tasks/registry-resolved.json` entry** unless its `rule-type` is `wait-for-connector` (see the note below the block). These are reasoning fields only — Phase 2 reads them from `sdd.md` ([planning.md § Step 4](../../../planning.md)).

```text
stage-exit condition on "<stage>" — <summary>
- target-stage: "<stage-name>"
- display-name: "<name>"                        # optional — omit when blank; impl defaults to "Complete Rule {N}"/"Exit Rule {N}" per marks-stage-complete
- type: exit-only
- exit-to-stage: "<target-stage-name>"          # optional
- marks-stage-complete: true
- rule-type: required-tasks-completed
- selected-tasks: "<Task A>, <Task B>"          # only if rule-type requires
- condition-expression: "=js:vars.X..."         # optional gate on case state, NOT the event payload
- verify: Confirm Result: Success, capture ConditionId
```

> `rule-type: wait-for-connector` also needs the connector fields — see [connector-trigger-planning.md § registry-resolved.json fields (resolution)](../../../connector-trigger-planning.md#registry-resolvedjson-fields-resolution).

<!-- END: planning.md -->
