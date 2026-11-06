# Pattern: `high-volume-batch`

Many independent items processed in one run, fanned out in parallel, aggregated at the end.
Use it when volume makes sequential processing impractical, items do not depend on each other, and some will fail without the run being a failure.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **Each item runs in its own sub-process instance.** A `loop` on a `.subProcess()`, not a loop drawn with `.goto()`.
  The marker gives each item its own scope and lets them run concurrently; it does **not** by itself stop one item's failure ending the run.
  An unhandled failure propagates outward, so containing it needs a `failure-escalation` net placed inside the iteration.
  Isolation is the loop plus that net, never the loop alone.
- **Aggregation happens once, after the block completes.** The multi-instance sub-process does not exit until every instance has, which is what makes a single aggregation step correct rather than a race.
- **The policy decision is separate from the aggregation.** Aggregating counts results; the gate decides whether those counts constitute success.
  Best-effort, all-or-nothing, and quorum are then one condition apart.
- **The summary is sent before the verdict.** The report sits ahead of the policy gate, so it runs on both outcomes.
  A failed batch is the one you most need the numbers for.

## Shape

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('invoice-batch')
  .name('InvoiceBatch')
  .flowMode('sequence')
  .var('batchItems', 'jsonSchema')
  .var('batchSummary', 'jsonSchema')
  .var('policySatisfied', 'boolean', { default: true })
  .startEvent('start', { name: 'Nightly', timer: { cycle: 'R/P1D' } })
  .scriptTask('fetchBatch', { name: 'Fetch invoices', script: 'return { items: [] };', outputs: { batchItems: '=result.items' } })
  // One sub-process instance per item, several at a time. The net INSIDE it is what
  // keeps one bad item from ending the run: it ends only that iteration.
  .subProcess(
    'processEach',
    (sp) =>
      sp
        .flowMode('sequence')
        .startEvent('itemStart')
        .scriptTask('processInvoice', { name: 'Process invoice', script: 'return { ok: true };' })
        .endEvent('itemDone', { name: 'Invoice processed' })
        .eventSubProcess('itemFailures', { error: true, name: 'Item failure' }, (h) =>
          h.task('recordItemFailure', { name: 'Record failed invoice' }).endEvent('itemFailed', { name: 'Invoice failed' })),
    { name: 'Process each invoice', loop: { collection: '=vars.batchItems', itemVar: 'item' } },
  )
  .scriptTask('aggregate', { name: 'Total the results', script: 'return { summary: {}, ok: true };', outputs: { batchSummary: '=result.summary', policySatisfied: '=result.ok' } })
  // The report runs BEFORE the verdict, so finance gets it on both outcomes.
  .plainTask('sendReport', { name: 'Send summary to finance', element: 'bpmn:sendTask' })
  .choose('policyGate', [
    { when: '=vars.policySatisfied == false', label: 'Policy missed', body: (b) => b.endEvent('endFailed', { name: 'Batch failed' }) },
    { otherwise: true, label: 'Policy met', body: (b) => b.endEvent('endCompleted', { name: 'Batch completed' }) },
  ])
  .build();
```

`loop: { collection, itemVar }` on the sub-process's options is the multi-instance marker; `sequential: true` runs one at a time.
Inside a looped sub-process the current item is `iterator[0].item` with `itemVar: 'item'` (`iterator[1].item` one nesting level deeper), and the 0-based index is `iterator[0].loopCounter`.
A script reads it as `iterator`, beside `vars`, never as a bare name.
The body is its own sequence scope: give it its own `.flowMode('sequence')`, start event and end event.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` with `timer` | Entry |
| `fetchBatch` | the source step | Placeholder · insertion point |
| `processEach` | `.subProcess(id, fn, { loop })` | Mechanism |
| `processInvoice` | the per-item work inside it | Placeholder |
| `itemFailures` | `.eventSubProcess()` inside the body | Mechanism |
| `aggregate` | the statement after the sub-process | Mechanism |
| `sendReport` | a send step, before the gate | Placeholder |
| `policyGate` | `.choose()` | Mechanism |
| `endCompleted`, `endFailed` | `.endEvent()`, named | Mechanism |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `batchItems` | jsonSchema | | The fetched items; the loop's `collection` |
| `batchSummary` | jsonSchema | | Totals, success count, failure breakdown |
| `policySatisfied` | boolean | `true` | Did the run meet the configured policy |

## Variants

One shape.
Parallel versus sequential is a property of the loop (`sequential: true`), not a different topology.
Choose sequential when the per-item action hits a rate-limited system or items must be ordered.

## What to bind

- **`fetchBatch`**: the source (database query, file, API list, queue); batch size and filters are decided here.
- **The per-item work** inside `processEach`: a UiPath agent, an RPA job, Document Understanding, an API call.
  Place and bind the node; the per-item work happens at runtime, not while authoring.
- **`aggregate`**: apply the policy and set `policySatisfied`.
  Best-effort is always true; all-or-nothing is true only with zero failures; quorum is true above a threshold.
  Evaluate it here, in a node, rather than as the loop's `completion` condition.
  A completion condition stops the block early, which is a different thing from judging the run afterwards, and it cannot see the per-item results the policy needs.
- **`sendReport`**: email, chat, dashboard, audit store.

## Adapting it

Drop `fetchBatch` when the items arrive on the trigger rather than being pulled: point `collection` straight at the input variable.
That is the common case when this pattern is nested inside another.

Drop `policyGate` and `endFailed` when every run succeeds by definition and only the counts matter.
Keep `sendReport`.

Set each item's exit status inside the body (success, failure, skipped), including in the net, or `aggregate` has nothing to count.

## Composing

The per-item work is the usual nesting point: `ai-decision-review` or `external-wait` becomes the body of `processEach`, giving every item its own decision or its own wait.

Place the `failure-escalation` net **directly inside** `processEach`, as the example does, so a per-item failure ends that iteration and the run continues.
A net at process level instead would catch the first failure and end the whole instance.
See [composing-guide.md](composing-guide.md#scoping-the-failure-net).
