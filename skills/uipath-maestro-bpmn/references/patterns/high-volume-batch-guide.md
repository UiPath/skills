# Pattern: `high-volume-batch`

Many independent items processed in one run, fanned out in parallel, aggregated
at the end. Use it when volume makes sequential processing impractical, items do
not depend on each other, and some will fail without the run being a failure.

## Why it works

These four carry the shape. Change one and you are building something else.

- **Each item runs in its own subprocess instance.** A multi-instance marker on
  a container, not a loop drawn on the canvas. One item's failure is contained
  in its own instance, so it cannot take the run down with it.
- **Aggregation happens once, after the block completes.** The multi-instance
  container does not exit until every instance has, which is what makes a single
  aggregation step correct rather than a race.
- **The policy decision is separate from the aggregation.** Aggregating counts
  results; the gateway decides whether those counts constitute success.
  Best-effort, all-or-nothing, and quorum are then one condition apart.
- **The summary is sent before the verdict.** The report node sits ahead of the
  policy gateway, so it runs on both outcomes. A failed batch is the one you
  most need the numbers for.

## Shape

Roles: **Entry** — omit when inserting into a process that already runs.
**Mechanism** — changing it changes the pattern. **Placeholder** — bind it, or
skip it if the process already does this.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `fetch_batch` | `bpmn:serviceTask` | Placeholder · insertion point |
| `process_each` | `bpmn:subProcess`, multi-instance | Mechanism |
| `aggregate` | `bpmn:serviceTask` | Mechanism |
| `send_report` | `bpmn:sendTask` | Placeholder |
| `policy_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `end_completed` | `bpmn:endEvent` | Mechanism |
| `end_failed` | `bpmn:endEvent` | Mechanism |

`process_each` holds a minimal body — a start event, one action node, an end
event — and carries the multi-instance marker. The action node is a
**Placeholder**.

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `fetch_batch` → `process_each` → `aggregate` → `send_report` → `policy_gate` | | |
| `policy_gate` → `end_completed` | Yes | default |
| `policy_gate` → `end_failed` | No | `=vars.policySatisfied == false` |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `batchItems` | jsonSchema | | The fetched items; bind as the multi-instance input collection |
| `batchSummary` | jsonSchema | | Totals, success count, failure breakdown |
| `policySatisfied` | boolean | `true` | Did the run meet the configured policy |

The multi-instance marker and its collection binding are a **registry gap** —
no template exists for them. Author them from the canvas contract in
[structural-bpmn.md](../structural-bpmn.md#multi-instance--loop-characteristics-registry-gap--canvas-supports-it),
and read the current item inside the body with `iterator[0].item` per
[expression-authoring.md](../expression-authoring.md).

## Variants

One shape. Parallel versus sequential is a property of the multi-instance
marker, not a different topology: set `isSequential` and optionally cap
concurrency. Choose sequential when the per-item action hits a rate-limited
system or items must be ordered.

## What to bind

- **`fetch_batch`** — the source: database query, file, API list, queue. Batch
  size and filters are decided here.
- **The action node** inside `process_each` — a UiPath agent, an RPA job,
  Document Understanding, an API call. Place and bind the node; the per-item
  work happens at runtime, not while authoring.
- **`aggregate`** — apply the policy and set `policySatisfied`. Best-effort
  always true; all-or-nothing true only with zero failures; quorum true above a
  threshold.
- **`send_report`** — email, chat, dashboard, audit store.

Fetch payloads through [registry-workflow.md](../registry-workflow.md).

## Adapting it

Drop `fetch_batch` when the items arrive on the trigger rather than being
pulled — bind the multi-instance collection straight to the input variable.
That is the common case when this pattern is nested inside another.

Drop `policy_gate` and `end_failed` when every run succeeds by definition and
only the counts matter. Keep `send_report`.

Set each item's exit status inside the body — success, failure, skipped — or
`aggregate` has nothing to count.

## Composing

The per-item action is the usual nesting point: `ai-decision-review` or
`external-wait` becomes the body of `process_each`, giving every item its own
decision or its own wait.

Place a `failure-escalation` net **inside** `process_each` so a per-item failure
is handled per item and the run continues. A net at process level instead would
catch the first failure and end the whole instance. See
[composing-guide.md](composing-guide.md#scoping-the-failure-net).
