# Pattern: `high-volume-batch`

Many independent items processed in one run, one sub-process instance per item, aggregated at the end.
Use it when items do not depend on each other and some will fail without the run being a failure.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **Each item runs in its own sub-process instance.** A `loop` on a `.subProcess()`, not a loop drawn with `.goto()`.
  The marker runs the body once per item, each with its own `iterator`; it does **not** by itself stop one item's failure ending the run.
  An unhandled failure propagates outward, so containing it needs a `failure-escalation` net placed inside the iteration.
  Isolation is the loop plus that net, never the loop alone.
- **Every item leaves a result, and aggregation reads them once, after the block completes.** Both exits of the body, the normal end and the net, append the item's outcome to `itemResults`.
  The multi-instance sub-process does not exit until every instance has, which is what makes a single aggregation step correct rather than a race.
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
  .var('itemResults', 'array', { default: [] })
  .var('batchSummary', 'jsonSchema')
  .var('policySatisfied', 'boolean', { default: false })
  .startEvent('start', { name: 'Nightly', timer: { cycle: 'R/P1D' } })
  .scriptTask('fetchBatch', { name: 'Fetch invoices', script: 'return { items: [] };', outputs: { batchItems: '=result.response.items' } })
  // One sub-process instance per item. The net INSIDE it is what keeps one bad item
  // from ending the run: it ends only that iteration. Both exits append the item's
  // result to `itemResults`, which is what `aggregate` counts.
  .subProcess(
    'processEach',
    (sp) =>
      sp
        .flowMode('sequence')
        .startEvent('itemStart')
        .scriptTask('processInvoice', { name: 'Process invoice', script: 'return { ok: true };' })
        .task('recordResult', { name: 'Record result', set: { itemResults: '=js:vars.itemResults.concat([{ item: iterator[0].item, ok: true }])' } })
        .endEvent('itemDone', { name: 'Invoice processed' })
        .eventSubProcess('itemFailures', { error: true, name: 'Item failure' }, (h) =>
          h.task('recordItemFailure', { name: 'Record failed invoice', set: { itemResults: '=js:vars.itemResults.concat([{ item: iterator[0].item, ok: false }])' } })
            .endEvent('itemFailed', { name: 'Invoice failed' })),
    // Sequential, so each iteration appends to the list the one before left.
    { name: 'Process each invoice', loop: { collection: '=vars.batchItems', itemVar: 'item', sequential: true } },
  )
  .scriptTask('aggregate', {
    name: 'Total the results',
    script: 'const ok = vars.itemResults.filter((r) => r.ok).length; return { summary: { total: vars.itemResults.length, ok }, met: ok === vars.itemResults.length };',
    outputs: { batchSummary: '=result.response.summary', policySatisfied: '=result.response.met' },
  })
  // The report runs BEFORE the verdict, so finance gets it on both outcomes.
  .plainTask('sendReport', { name: 'Send summary to finance', element: 'bpmn:sendTask' })
  .choose('policyGate', [
    { when: '=vars.policySatisfied == false', label: 'Policy missed', body: (b) => b.endEvent('endFailed', { name: 'Batch failed' }) },
    { otherwise: true, label: 'Policy met', body: (b) => b.endEvent('endCompleted', { name: 'Batch completed' }) },
  ])
  .build();
```

`loop: { collection, itemVar }` on the sub-process's options is the multi-instance marker; `sequential: true` runs one at a time, which is what lets every iteration append to the same list (see [Getting results to `aggregate`](#getting-results-to-aggregate)).
Inside a looped sub-process the current item is `iterator[0].item` with `itemVar: 'item'` (`iterator[1].item` one nesting level deeper), and the 0-based index is `iterator[0].loopCounter`.
The index counts enclosing loops outermost-first, so nest this pattern inside another loop and `iterator[0]` becomes the outer item: change the body's reads, including both record steps, to `iterator[1]`.
An expression (`set`, a condition, an `outputs` value) reads `iterator` directly, as `recordResult` does.
A script does not: its scope holds only the `args` envelope, which the builder writes as `vars` and `metadata`, and the engine builds a script's `iterator` only from `iterator[N]` keys in that envelope.
To read the item in a script, pass it in with `inputs: { 'iterator[0]': '=iterator[0]' }`, which is what the designer writes; `validate` still warns that `iterator` is undefined, and that warning is a false positive once the key is there.
The body is its own sequence scope: give it its own `.flowMode('sequence')`, start event and end event.

| Node | Builder | Role |
| --- | --- | --- |
| `start` | `.startEvent()` with `timer` | Entry |
| `fetchBatch` | the source step | Placeholder · insertion point |
| `processEach` | `.subProcess(id, fn, { loop })` | Mechanism |
| `processInvoice` | the per-item work inside it | Placeholder |
| `recordResult` | `.task()` with `set`, last in the body | Mechanism |
| `itemFailures` | `.eventSubProcess()` inside the body | Mechanism |
| `recordItemFailure` | `.task()` with `set`, in the net | Mechanism |
| `aggregate` | the statement after the sub-process | Mechanism |
| `sendReport` | a send step, before the gate | Placeholder |
| `policyGate` | `.choose()` | Mechanism |
| `endCompleted`, `endFailed` | `.endEvent()`, named | Mechanism |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `batchItems` | jsonSchema | | The fetched items; the loop's `collection` |
| `itemResults` | array | `[]` | One `{ item, ok }` per item, appended by the body or the net |
| `batchSummary` | jsonSchema | | Totals, success count, failure breakdown |
| `policySatisfied` | boolean | `false` | Did the run meet the configured policy |

`policySatisfied` defaults to `false` so a run whose `aggregate` never wrote it ends as failed, not completed.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| Sequential | — | The shape above |
| Parallel | Must items run several at a time? | Drop `sequential`, and record each result outside the process |

**Parallel.** Drop `sequential: true` and the items run concurrently, but the in-process append no longer collects them ([Getting results to `aggregate`](#getting-results-to-aggregate)).
Write each item's outcome to a store outside the process instead, such as a Data Fabric record per item keyed by a batch id (`.dataService()`), in place of `recordResult` and `recordItemFailure`, and have `aggregate` read the batch's records back.
This variant is not verified end to end.

## What to bind

- **`fetchBatch`**: the source (database query, file, API list, queue); batch size and filters are decided here.
- **The per-item work** inside `processEach`: a UiPath agent, an RPA job, Document Understanding, an API call.
  Place and bind the node; the per-item work happens at runtime, not while authoring.
- **`aggregate`**: count `itemResults`, apply the policy and set `policySatisfied`.
  Best-effort is always true; all-or-nothing is true only with zero failures; quorum is true above a threshold.
  Evaluate it here, in a node, rather than as the loop's `completion` condition.
  A completion condition stops the block early, which is a different thing from judging the run afterwards, and it cannot see the per-item results the policy needs.
- **`sendReport`**: email, chat, dashboard, audit store.

## Adapting it

Drop `fetchBatch` when the items arrive on the trigger rather than being pulled: point `collection` straight at the input variable.
That is the common case when this pattern is nested inside another.

Drop `policyGate` and `endFailed` when every run succeeds by definition and only the counts matter.
Keep `sendReport`.

Keep both `recordResult` and `recordItemFailure` when you change the body: an item that leaves no result is one `aggregate` cannot count.
Add fields to the record (a reason, a skipped flag) as the policy needs them.

## Getting results to `aggregate`

The builder's `loop` has no output collection: `{ collection, itemVar, sequential, completion }` is all it takes, so nothing gathers the iterations' results for you.
The sketch collects them itself: each iteration appends to `itemResults`, and `sequential: true` means each one sees the list as the one before left it.
On the local engine this collected every item, and `aggregate` counted them.

On the local engine, parallel iterations overwrite each other's writes to one variable: three parallel iterations each appending to the list left one entry, the last to finish.
That is not verified on Maestro, whose engine may scope iteration writes differently, so do not rely on a parallel append either way; use the parallel variant's external store.

The append is a `set` expression because it reads `iterator` directly and validates clean.
Declare the list as `array`, whose default is written as JSON; a `jsonSchema` default of `[]` does not arrive as a list.

## Composing

The per-item work is the usual nesting point: `ai-decision-review` or `external-wait` becomes the body of `processEach`, giving every item its own decision or its own wait.

Place the `failure-escalation` net **directly inside** `processEach`, as the example does, so a per-item failure ends that iteration and the run continues.
A net at process level instead would catch the first failure and end the whole instance.
See [composing-guide.md](composing-guide.md#scoping-the-failure-net).
