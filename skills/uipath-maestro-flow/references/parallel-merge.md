# Parallel / Merge

Parallel fans control into two or more arms and joins them on a Merge.

Signature: `.parallel(name, [armFn, armFn, ...])`; `name` identifies the Merge.

```ts
.parallel('ready', [
  (a) => a.step('weather', http({ url: weatherUrl, managed: false })),
  (b) => b.step('news', http({ url: newsUrl, managed: false })),
])
.step('combine', script({ code: 'return "ready";' }))
```

Use parallel only when the arms are independent: neither arm may require the
other's result before the join. It expresses graph independence, not a promise
that every executor schedules work concurrently; the local executor processes
arms in authored order.

Work after `.parallel(...)` continues from its `output` port and can read the
outputs of each arm.

When every arm ends, with `.return`, `.terminate`, or a `.stepToRef` into an
End another arm wrote, there is nothing to join. No Merge is emitted, `name`
names no node, and nothing may follow the `.parallel`:

```ts
.step('prepare', script({ code: 'return 1;' }))
.parallel('prepareFork', [
  (a) => a.step('notifyA', script({ code: 'return "a";' })).return({}, { name: 'done' }),
  (b) => b.step('notifyB', script({ code: 'return "b";' })).stepToRef('done'),
])
```

A `.terminate` must be the arm's first call: `check` refuses one behind a step
in a `.parallel` arm (`TERMINATE_NOT_ARM_HEAD`).

Decompile (SDK 6.46.6 or later) writes a canvas fan-out whose arms never meet
again this way, naming the `.parallel` `<node>Fork` after the node the arms
leave. A canvas arm that runs a step before its Terminate is the exception: it
stays an unstructured fan-out (see [brownfield.md](brownfield.md)).

## At a glance

Fan out independent arms and join them at a Merge.

Use it only for independent arms; do not assume the local executor runs them concurrently.
