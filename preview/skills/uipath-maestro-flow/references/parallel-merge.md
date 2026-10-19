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
