# Pattern: `high-volume-batch`

Process independent items in one run with one sub-process instance per item, then aggregate; use this when one failure need not fail the run.

## Why it works

These four carry the shape.
Change one and you are building something else.

- **Each item runs in its own sub-process instance:** `loop` on a `.subProcess()`, never a `.goto()` loop. The marker runs once per item with its own `iterator` but does not contain failures; an unhandled failure propagates outward, so put a `failure-escalation` net directly inside the iteration.
- **Every item leaves a result; aggregate once, after the block:** normal and net exits append to `itemResults` (Parallel: write to the store), and the multi-instance sub-process waits for all instances.
- **Policy is separate from aggregation:** aggregation counts results; a policy gate decides success. Best-effort, all-or-nothing, and quorum differ only in that condition.
- **Summary before verdict:** send the report ahead of the policy gate so it runs on both outcomes.

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
    { name: 'Process each invoice', loop: { collection: '=js:vars.batchItems', itemVar: 'iterator[0]', sequential: true } },
  )
  .scriptTask('aggregate', {
    name: 'Total the results',
    script: 'const ok = vars.itemResults.filter((r) => r.ok).length; return { summary: { total: vars.itemResults.length, ok }, met: ok === vars.itemResults.length };',
    outputs: { batchSummary: '=result.response.summary', policySatisfied: '=result.response.met' },
  })
  .plainTask('sendReport', { name: 'Send summary to finance', element: 'bpmn:sendTask' })
  .choose('policyGate', [
    { when: '=js:vars.policySatisfied == false', label: 'Policy missed', body: (b) => b.endEvent('endFailed', { name: 'Batch failed' }) },
    { otherwise: true, label: 'Policy met', body: (b) => b.endEvent('endCompleted', { name: 'Batch completed' }) },
  ])
  .build();
```

`loop: { collection, itemVar }` on sub-process options is the multi-instance marker. `sequential: true` runs one at a time so each append sees the preceding list (see [Getting results to `aggregate`](#getting-results-to-aggregate)). Name the loop the way Studio Web does: `itemVar: 'iterator[0]'`, `iterator[1]` for nested loops; every connected loop, including ancestor, descendant, or sibling, has its own index. Expressions (`set`, conditions, and `outputs`) read the item as `iterator[0].item` and its 1-based position as `iterator[0].loopCounter`.

Preserve `itemVar: 'iterator[N]'` and its reads for Studio Web-created or `decompile`-seeded looped sub-processes. A looped task outside a looped sub-process has no `inputElement` on the canvas and reads `iterator.item`; `decompile` seeds `itemVar: 'item'`, recompiling to `inputElement="item"` and moving the item to `iterator["item"]["item"]`, so rewrite its reads to that form. For another `itemVar`, such as `'invoice'`, the outer key is that value and the inner key stays `item`: `iterator["invoice"]["item"]`; `iterator[0]` and `iterator["invoice"]["invoice"]` read `null`.

Scripts do not see `iterator` directly: their scope contains only the `args` envelope, and the engine builds script `iterator` entries only from `iterator[N]` keys in its inputs. Pass the item with `inputs: { 'iterator[0]': '=iterator[0]' }` and read `iterator[0].item`; `validate` still warns that `iterator` is undefined, a false positive when the key is present. A wrong iterator read fails nothing: it yields `null` (or `"undefined"` after `String()`), every check passes and the run completes. Prove a loop by reading per-item results with `debug-instances variables-all` after a Maestro debug run; local `flow-debug` reads loops differently ([offline checks](../operate.md#debug--a-controlled-studio-web-run)).

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
| `aggregate` | `.scriptTask()` after the sub-process, never a `.task()` with `set` | Mechanism |
| `sendReport` | a send step, before the gate | Placeholder |
| `policyGate` | `.choose()` | Mechanism |
| `endCompleted`, `endFailed` | `.endEvent()`, named | Mechanism |

| Variable | Type | Default | Holds |
| --- | --- | --- | --- |
| `batchItems` | jsonSchema | | The fetched items; the loop's `collection` |
| `itemResults` | array | `[]` | One `{ item, ok }` per item, appended by the body or the net |
| `batchSummary` | jsonSchema | | Totals, success count, failure breakdown |
| `policySatisfied` | boolean | `false` | Did the run meet the configured policy |
| `batchId` | string | | Parallel only: tags this run's records for the read-back |

`policySatisfied` defaults to `false` so a run whose `aggregate` never wrote it ends as failed, not completed.

## Variants

| Variant | Question | Delta |
| --- | --- | --- |
| Sequential | — | Shape above |
| Parallel | Must items run concurrently? | With a named store, drop `sequential` and record outside the process; without one, stay sequential |

**Parallel.** Drop `sequential: true` for concurrent items, but do not append in-process ([Getting results to `aggregate`](#getting-results-to-aggregate)). If no store is named, do not invent an entity or connection, and do not stop to ask: keep `sequential: true` and put on the final report's `Assumed:` line that items run one at a time because no store was named.

With a store, write each outcome as one Data Fabric record per item: use a `.dataService()` `op: 'create'` in place of `recordResult` (`ok: true`) and another in place of `recordItemFailure` (`ok: false`). Declare `.var('batchId', 'string')`; set it before the sub-process with `.task('newBatch', { set: { batchId: '=js:"BATCH-" + Date.now()' } })`; write it on every record. After the sub-process, read the batch with a `.dataService()` `query`, ``where: "=js:`batchId = '${vars.batchId}'`"``, and `limit` at or above the batch size; the default is 100 and silently drops the rest.

Keep `aggregate` as a `.scriptTask()` that totals records from `vars.<queryId>_response` and writes `batchSummary` and `policySatisfied` through `outputs`, as in the Shape. A `.task()` without `set` compiles to a no-op `bpmn:task` and leaves `policySatisfied` false. On a tenant entity the response is a bare array of records, `[]` when none; read `.length` and `.filter` directly. The total is `vars.batchItems.length`, not the record count: fewer records means an item left no result and counts as failure, so `met` requires `ok === vars.batchItems.length`. This variant is not verified end to end.

## What to bind

- **`fetchBatch`**: bind a database query, file, API list, or queue; batch size and filters belong to this node.
- **Per-item work** inside `processEach`: bind a UiPath agent, RPA job, Document Understanding, or API call. Place and bind the node; it runs at runtime, not while authoring.
- **`aggregate`**: a `.scriptTask()` that counts `itemResults` (Parallel: query records), applies policy, and sets `policySatisfied` through `outputs`. Best-effort is always true; all-or-nothing is true only with zero failures; quorum is true above its threshold. Evaluate it in a node, not the loop's `completion` condition: completion stops the block early and cannot see the results needed for post-run policy.
- **`sendReport`**: bind email, chat, dashboard, or audit store.

## Adapting it

If items arrive on the trigger, drop `fetchBatch` and point `collection` directly at the input variable; this is common when nested in another pattern.

If every run succeeds by definition and only counts matter, drop `policyGate` and `endFailed`, but keep `sendReport`.

When changing the body, keep `recordResult` and `recordItemFailure` (Parallel: their store writes): an item with no result cannot be counted by `aggregate`. Add fields to the record, such as a reason or skipped flag, as policy requires.

## Getting results to `aggregate`

The builder's `loop` has no output collection: `{ collection, itemVar, sequential, completion }` is all it accepts. The sketch collects results by appending in each iteration; `sequential: true` exposes the preceding list to the next iteration. A Maestro debug run over `[1, -2, 3]` completed with three results, caught `-2` in the net, and had `aggregate` count 3 / 2 ok.

Parallel iterations overwrite writes to one variable because the variable store is last-writer-wins; a Maestro run appending 12 parallel items kept 11. Never append to one variable in parallel: use the external store or keep `sequential: true` when no store is named.

The append is a `set` expression because it reads `iterator` directly and validates clean. Declare the list as `array`, whose default is written as JSON; a `jsonSchema` default of `[]` does not arrive as a list.

## Composing

The per-item work is the usual nesting point: `ai-decision-review` or `external-wait` becomes the body of `processEach`, giving every item its own decision or wait.

Place the `failure-escalation` net **directly inside** `processEach` so a per-item failure ends that iteration and the run continues. A net at process level catches the first failure and ends the whole instance. See [composing-guide.md](composing-guide.md#scoping-the-failure-net).
