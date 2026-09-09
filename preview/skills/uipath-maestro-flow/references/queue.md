# Queue Item

*Exact signatures, fields, and defaults: [`queueItem()`](api.md#queueitem-function).*

Create work on an Orchestrator queue, optionally waiting for another automation
to process it.

Signature:
`queueItem({ queue, folderPath, key, item, priority?, reference?, deferDate?, dueDate?, wait?, returns? })`.

```ts
.step('enqueue', queueItem({ queue: 'Invoices', folderPath: 'Shared',
  key: queueKey, item: { InvoiceId: input('invoiceId') },
  reference: input('invoiceId'), wait: false }))
```

## Reading what the create returned

The node's output carries the Orchestrator record of the item it created — `Id`,
`Key`, `UniqueKey`, `Reference`, `Status` and the rest of the queue-item schema.
Read a field with `out('<step>', '<Field>')`; do NOT add a script step to
re-derive it, and do not invent a variable for the item:

```ts
.step('enqueue', queueItem({ queue: 'Invoices', folderPath: 'Shared',
  key: queueKey, item: { InvoiceId: input('invoiceId') } }))
.return({ itemKey: out('enqueue', 'Key') })
```

`out('enqueue', 'Key')` is the whole read. It serializes to
`$vars.enqueue.response.Key`, which is the spelling the runtime resolves — so a
hand-written `$vars.enqueue.output.Key`, or a `script()` step that reads the
node and republishes the key, is both longer and wrong.

## Tenant settings

Queue-level settings are not present in source. A queue may require unique
references or enforce an item schema. Inspect it with
`uip or queues list --all-folders`; derive a required reference from run input
rather than using a constant that works only once.

## Whether to wait

Use `wait: true` only when the current Flow needs the consumer's result and a
real automation drains the queue. Otherwise enqueue and let a separate process
own consumption. For a waiting step, decide whether failed/abandoned processing
should be handled or should fault this Flow.

## Evidence boundary

Replay uses a synthesized item/result. Live mode creates a real item and, for a
wait, polls its real state. A green create proves the producer side only; a
green wait also depends on the external consumer and should preserve its item
key and terminal state as evidence.
