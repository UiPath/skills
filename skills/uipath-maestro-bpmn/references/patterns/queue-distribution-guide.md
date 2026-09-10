# Pattern: `queue-distribution`

An Orchestrator queue sits between work creation and work processing. Use it
when the two sides run in different runtimes, must scale independently, or when
the queue itself is needed as a durable tracking surface.

## Why it works

These four carry the shape. Change one and you are building something else.

- **The queue is the handover surface, not a message.** Priority, deferred
  scheduling, deduplication, concurrency limits, and durable retry all come from
  the queue and survive either side restarting. That is the reason to pay for a
  queue instead of dispatching directly.
- **One queue item starts one performer instance.** There is no loop in the BPMN
  and deliberately no get-next-item step. Each unit of work is isolated and
  independently tracked, at the cost of one process instance per item — which is
  the trade to weigh when volume is very high.
- **Every item ends by marking its transaction.** Successful, Failed, or
  Postponed. An item whose instance ends without marking stays in-flight in the
  queue and is invisible until something times it out.
- **The two sides are independent.** Whichever side is not Maestro can be an RPA
  robot, an integration, a web app, or a person uploading a file. Neither side
  assumes the other is a Maestro process.

## Shape

Two separate shapes. Which you author depends on which side of the queue Maestro
is on; author both when Maestro is on both.

### Dispatcher — Maestro creates the items

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` + message event definition | Entry |
| `fetch_source` | `bpmn:serviceTask` | Placeholder · insertion point |
| `bulk_add` | `bpmn:serviceTask` | Mechanism |
| `end_queued` | `bpmn:endEvent` | Mechanism |

Linear: `start` → `fetch_source` → `bulk_add` → `end_queued`. No conditions.
One variable, `sourceItems` (jsonSchema), bound as the bulk-add input.

Batches cap at 15,000 items and commit either all-or-nothing or per item. For
one-at-a-time dispatch use the single create-item activity instead — same shape,
different node.

### Performer — Maestro processes the items

The performer's start event **is** the queue trigger, so this shape always begins
the process. It cannot be inserted into an existing path or nested in a
subprocess, and it has no Entry row in the droppable sense.

**The entire performer shape is placeholder structural BPMN — do not search the
registry, `uip or`, or `uip login` for any of it.** This is a queue-themed
process, but nothing in it maps to a queue-specific registry payload:

- The start is a plain `bpmn:startEvent` (an optional `bpmn:messageEventDefinition`
  child is semantic only) — not a registry "queue trigger" type.
- `per_item_action` and the three outcome nodes (`set_successful`, `set_failed`,
  `postpone`) are placeholder `bpmn:serviceTask`s. Marking the queue item's
  transaction status happens at runtime; you do NOT bind
  `Orchestrator.SetTransactionStatus`, `SetQueueItemStatus`, or any queue
  activity, and there is no such template to fetch.

The check grades one start event with nothing flowing back, an exclusive gateway
with three outcome branches each starting with an activity, and three ends — no
`uipath:*` payload anywhere. Author the nodes directly and move on. Do not spend
turns on `registry search`, `registry get`, `uip or queues`, or `uip login`
chasing a queue type — none exists and none is needed.

| Node | Element | Role |
| --- | --- | --- |
| `start` | `bpmn:startEvent` (optional `bpmn:messageEventDefinition`) — structural, no registry payload | Mechanism |
| `per_item_action` | `bpmn:serviceTask` | Placeholder |
| `outcome_gate` | `bpmn:exclusiveGateway` | Mechanism |
| `set_successful` | `bpmn:serviceTask` | Mechanism |
| `set_failed` | `bpmn:serviceTask` | Mechanism |
| `postpone` | `bpmn:serviceTask` | Mechanism |
| `end_succeeded` / `end_failed` / `end_postponed` | `bpmn:endEvent` | Mechanism |

| Sequence flow | Label | Condition |
| --- | --- | --- |
| `start` → `per_item_action` → `outcome_gate` | | |
| `outcome_gate` → `set_successful` | Success | default |
| `outcome_gate` → `set_failed` | Failure | `=vars.itemOutcome == "failure"` |
| `outcome_gate` → `postpone` | Defer | `=vars.itemOutcome == "defer"` |
| each status node → its end event | | |

| Variable | Type | Holds |
| --- | --- | --- |
| `queueItem` | jsonSchema | The triggering item's payload |
| `itemOutcome` | string | `success`, `failure`, or `defer` |

## Variants

Dispatcher and performer are not alternatives — they are the two halves, and
which you author is a question about your architecture rather than the shape.

| Maestro is | Author |
| --- | --- |
| The dispatcher; something else drains | Dispatcher shape |
| The performer, hooked to an existing queue | Performer shape |
| Both sides | Both shapes, as separate processes |

The performer is the brownfield entry point: it attaches Maestro to a queue that
already exists without touching whatever produces the items.

## What to bind

- **The queue** on every queue node. Never invent a queue name or key — it comes
  from discovery or from the user (SKILL.md rule 2).
- **`fetch_source`** — the upstream source, and the shaping of each item's
  payload, priority, deadline, and optional postpone date.
- **`per_item_action`** — the node that does the work at runtime: a UiPath
  agent, Document Understanding, an API call, a HITL task, an RPA job, or a mix.
- **`set_failed`** — include error type, reason, and detail; that is what makes
  a failed transaction diagnosable later.
- **`postpone`** — earliest reprocessing time, and a deadline if the item should
  eventually stop being retried.

The queue activity types this shape needs are newer than the extension list
bundled with the validator, so do not assume the names. Resolve them with
`uip maestro bpmn registry list --output json` and fetch each template with
`registry get` before authoring — see
[registry-workflow.md](../registry-workflow.md).

## Adapting it

Use single-item creation instead of bulk when items arrive one at a time; the
dispatcher shape is otherwise unchanged.

Drop the `defer` branch when nothing about the work is worth retrying later.
Keep success and failure: those two are how the queue learns the item is done.

Add an in-flight progress update inside `per_item_action` when operators need to
watch long-running items move, rather than only seeing start and finish.

## Composing

Place `failure-escalation` **inside** the performer so a failure marks the
transaction Failed and ends that item's instance, leaving the queue free to
continue. Without it, a failure ends the instance without marking, and the item
stays in-flight.

The performer must be the outermost pattern in its process. Everything else it
needs — a review, a wait — is inserted into or nested inside it, never the
reverse. See [composing-guide.md](composing-guide.md).
