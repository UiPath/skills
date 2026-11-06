# Pattern: `queue-distribution`

An Orchestrator queue sits between work creation and work processing.
Use it when the two sides run in different runtimes, must scale independently, or when the queue itself is needed as a durable tracking surface.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **The queue is the handover surface, not a message.** Priority, deferred scheduling, deduplication, concurrency limits, and durable retry all come from the queue and survive either side restarting.
  That is the reason to pay for a queue instead of dispatching directly.
- **One queue item starts one performer instance.** There is no loop in the process and deliberately no get-next-item step.
  Each unit of work is isolated and independently tracked, at the cost of one process instance per item, which is the trade to weigh when volume is very high.
- **Every item ends by marking its transaction.** Successful, Failed, or Postponed.
  An item whose instance ends without marking stays in flight in the queue and is invisible until something times it out.
- **The two sides are independent.** Whichever side is not Maestro can be an RPA robot, an integration, a web app, or a person uploading a file.
  Neither side assumes the other is a Maestro process.

## Shape

Two separate shapes.
Which you author depends on which side of the queue Maestro is on; author both, as separate processes, when Maestro is on both.

### Dispatcher: Maestro creates the items

`start` → `fetchSource` → the enqueue → `endQueued`, with no conditions.
One item at a time is `.queueItem(id, { queue, folder, item })`; `folder` is required.
A batch is `.activity(id, 'Orchestrator.BulkAddQueueItems', { inputs })`, since it has no typed method; read its fields with `uip maestro bpmn registry get Orchestrator.BulkAddQueueItems --output json`.
One variable, `sourceItems` (jsonSchema), is the bulk input.

### Performer: Maestro processes the items

The performer's start event **is** the queue trigger, so this shape always begins the process.
It cannot be inserted into an existing path or nested in a sub-process.
The start stays a plain `.startEvent()`: the queue binding is configured outside the BPMN, and the registry has no queue-trigger type.

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('claim-worker')
  .name('ClaimWorker')
  .flowMode('sequence')
  .input('queueItem', 'jsonSchema', { name: 'Queue item' })
  .var('itemOutcome', 'string', { default: 'success' })
  .var('failureReason', 'string')
  // The queue trigger is configured outside the BPMN; the start stays plain.
  .startEvent('start', { name: 'Queue item added' })
  .scriptTask('perItemAction', { name: 'Handle claim', script: 'return { outcome: "success", reason: null };', outputs: { itemOutcome: '=result.outcome', failureReason: '=result.reason' } })
  // Every branch BEGINS with the activity that marks the transaction.
  .choose('outcomeGate', [
    { when: '=vars.itemOutcome == "failure"', label: 'Failure', body: (b) => b.activity('setFailed', 'Orchestrator.SetTransactionStatus', { name: 'Mark failed', inputs: { QueueItem: '=vars.queueItem', Status: 'Failed', Reason: '=vars.failureReason' } }).endEvent('endFailed', { name: 'Item failed' }) },
    { when: '=vars.itemOutcome == "defer"', label: 'Defer', body: (b) => b.activity('postpone', 'Orchestrator.PostponeTransactionItem', { name: 'Postpone item', inputs: { QueueItem: '=vars.queueItem', PostponeDate: '=js:new Date(Date.now() + 3600000).toISOString()' } }).endEvent('endPostponed', { name: 'Item postponed' }) },
    { otherwise: true, label: 'Success', body: (b) => b.activity('setSuccessful', 'Orchestrator.SetTransactionStatus', { name: 'Mark successful', inputs: { QueueItem: '=vars.queueItem', Status: 'Successful' } }).endEvent('endSucceeded', { name: 'Item succeeded' }) },
  ])
  .build();
```

Each outcome arm BEGINS with the activity that marks the transaction.
Three arms going straight to three end events is not the mechanism; telling the queue is.
`Orchestrator.SetTransactionStatus` and `Orchestrator.PostponeTransactionItem` are registry types with no typed method, so they go through `.activity()` with the registry's field names as `inputs`.
Neither needs discovery.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | plain `.startEvent()` | Mechanism |
| `perItemAction` | the work | Placeholder |
| `outcomeGate` | `.choose()` | Mechanism |
| `setSuccessful`, `setFailed` | `.activity(id, 'Orchestrator.SetTransactionStatus', …)` | Mechanism |
| `postpone` | `.activity(id, 'Orchestrator.PostponeTransactionItem', …)` | Mechanism |
| `endSucceeded`, `endFailed`, `endPostponed` | `.endEvent()`, named | Mechanism |

| Variable | Type | Holds |
| --- | --- | --- |
| `queueItem` | jsonSchema | The triggering item, the `QueueItem` each marking step names |
| `itemOutcome` | string | `success`, `failure`, or `defer` |
| `failureReason` | string | Why it failed, for `setFailed` |

`QueueItem` takes the triggering item (an object carrying its `Id`).
How the trigger hands that item to the process is configured with the trigger, outside the BPMN; bind `queueItem` to whatever carries it.
Until something assigns it, `validate` warns `VARIABLE_NOT_SET` on each marking step.

## Variants

Dispatcher and performer are not alternatives: they are the two halves, and which you author is a question about your architecture rather than the shape.

| Maestro is | Author |
| --- | --- |
| The dispatcher; something else drains | Dispatcher shape |
| The performer, hooked to an existing queue | Performer shape |
| Both sides | Both shapes, as separate processes |

The performer is the brownfield entry point: it attaches Maestro to a queue that already exists without touching whatever produces the items.

## What to bind

- **The queue** on every enqueue node.
  Never invent a queue name or folder: it comes from discovery or from the user.
- **`fetchSource`**: the upstream source, and the shaping of each item's payload, priority, deadline, and optional postpone date.
- **`perItemAction`**: the node that does the work at runtime: a UiPath agent, Document Understanding, an API call, a human task, an RPA job, or a mix.
- **`setFailed`**: fill `Reason`, and `ErrorType` and `Details` where you have them; that is what makes a failed transaction diagnosable later.
- **`postpone`**: `PostponeDate`, the earliest reprocessing time, and `DueDate` if the item should eventually stop being retried.
- **`Orchestrator.SetTransactionProgress`** (via `.activity()`): an in-flight progress update, where operators need to watch long items move.

## Adapting it

Use `.queueItem()` instead of the bulk add when items arrive one at a time; the dispatcher shape is otherwise unchanged.
`wait: true` on `.queueItem()` waits for the item to be processed, which turns the queue into a call and is a different pattern.

Drop the `defer` arm when nothing about the work is worth retrying later.
Keep success and failure: those two are how the queue learns the item is done.

## Composing

Place `failure-escalation` **inside** the performer so a failure marks the transaction Failed and ends that item's instance, leaving the queue free to continue.
The net's own path must mark it: put a `SetTransactionStatus` step with `Status: 'Failed'` before its end event.
Without it, a failure ends the instance without marking, and the item stays in flight.

The performer must be the outermost pattern in its process.
Everything else it needs, a review or a wait, is inserted into or nested inside it, never the reverse.
See [composing-guide.md](composing-guide.md).
