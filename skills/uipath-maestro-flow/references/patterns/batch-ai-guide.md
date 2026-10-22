# Pattern: `batch-ai`

An agent processes every item of a collection in one run, in order or in
parallel, and the results are gathered at the end. Use it when the request says
one bad item must not stop the rest.

Not `batchTransform()`: that node adds AI columns to one CSV in a single step.
Reach for this pattern when each item needs its own agent call, typed result,
or follow-up.

## Why it works

- **The agent runs inside the loop body, once per item.** It reads the loop's
  `currentItem`, not the whole collection.
- **One bad item never ends the batch.** The agent's `error` port continues
  the loop, so a failed item becomes an entry in the results that carries its
  error instead of an output. Without it the first failure faults the run.
- **Results are read after the loop.** The loop collects one entry per item in
  `$vars.<loop>.output`, failed items included. Prefer it to the `.var()`
  accumulator in [loops.md](../loops.md): of a failed step's `{ updates }`, only a
  script's are documented to run ([error-handling.md](../error-handling.md)), so
  the accumulator drops failures unless the error handler writes them too.

## Shape

The `synthesize` variant. `per-item` is the same without `synthesize`:

| Step | Node | Builder | Role |
| --- | --- | --- | --- |
| `loadItems` | the source's node | per SKILL.md's node table | Placeholder · Entry: skip when the collection already exists |
| `processBatch` | `core.logic.loop` | `.loop('processBatch', <items>, body)` | Mechanism |
| `processItem` | `uipath.agent.autonomous`, inside the loop | `inlineAgent({ returns })` + `.onError((h) => h.continue())` | Mechanism |
| `synthesize` | `uipath.agent.autonomous` | `inlineAgent({ inputs, returns })` | Mechanism (`synthesize` only) |
| `endDone` | `core.control.end` | `.return(...)` | Entry |

| From | Port | To |
| --- | --- | --- |
| `loadItems` | | `processBatch` |
| `processBatch` | `start` | `processItem` |
| `processItem` | `success` | `processBatch` `continue` |
| `processItem` | `error` | `processBatch` `continue` |
| `processBatch` | `success` | `synthesize` |
| `synthesize` | `success` | `endDone` |

`processItem` reads `v('processBatch.currentItem')` and returns `result` and
`status` (`ok` or `failed`). `synthesize` takes `out('processBatch')` as an input
and returns `summary`, `exceptions` and `processed`; its prompt says a result
entry that carries an error is a failed item to list under exceptions.

The loop runs items in order. Set `parallel: true` only for independent items
that are not rate-limited.

## Variants

| Variant | Question it answers | Delta |
| --- | --- | --- |
| `per-item` | (default) | No `synthesize`; the step after the pattern reads the loop's results |
| `synthesize` | Is one consolidated answer needed? | The shape above |
| `sample-first` | Must a person check quality before the whole collection is touched? | A sample loop and a quality gate before the full loop |

**`sample-first`.** A first loop, `sampleBatch`, runs over a slice of the
collection (`items.slice(0, 2)` by default) with its own agent step, configured
like `processItem`. A form,
`checkQuality`, shows `out('sampleBatch')`: **Release full run** continues to
`processBatch` over the whole collection, and **Stop** ends at its own End.

## What to bind

- **`loadItems`**: where the collection comes from, such as a Data Fabric read,
  a connector list operation, or an input.
- **`processItem`** and **`synthesize`**: a published agent, else an
  `inlineAgent` with `returns`, never `mock()`. Write the prompts; the
  synthesis prompt keeps failures visible.

## Adapting it

The per-item body can grow: a decision, a connector write, or a review per item.
Every step that can fail inside the body needs the same isolation if one item
must not stop the batch. Put that step's `.onError` inside the body and end it
with `.continue()`, never `.terminate()` or `.return()`; a handler on the loop
container catches the whole loop instead
([error-handling.md](../error-handling.md)).
