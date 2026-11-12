# Switch

Switch routes one value among several cases.

Signature: `.switch(name, on, [{ value: string | number | boolean, label?, body }], defaultFn?)`; a case may use `when: Expr` instead of `value`.

```ts
.switch('priority', input('priority'), [
  { value: 'high', body: (b) => b.step('page', script({ code: 'return 1;' })) },
  { value: 'low', body: (b) => b.step('queue', script({ code: 'return 2;' })) },
], (other) => other.step('normal', script({ code: 'return 3;' })))
```

Try cases top to bottom and select the first true condition. A `value` case strictly compares `on` (`===`). Each case (value or when) gets a generated `case-<id>` port. The optional final callback uses `default`. Each case must have exactly one of `value` or `when` (`SWITCH_CASE_FORM` otherwise); a `value` case requires `on`. Pass `undefined` for `on` when every case uses `when`:

```ts
.switch('route', undefined, [
  { when: js`$vars.start.output.amount > 100`, label: 'High', body: (b) => b.step('review', script({ code: 'return 1;' })) },
  { when: js`$vars.start.output.amount <= 100`, label: 'Low', body: (b) => b.step('auto', script({ code: 'return 2;' })) },
])
```

In a new flow, use `when` cases when each of three or more paths needs its own condition (such as ranges or different fields); use `.branch` for two conditions. Decompile preserves `when` cases for designer-drawn switches whose cases are not one shared `<discriminant> === <value>`; keep them.

A decompiled designer-drawn switch may carry case IDs such as `id: "default-1"`. Leave them unchanged to preserve original case IDs so merged edges match the original switch node; do not add IDs to cases written yourself.

## At a glance

Prefer Switch when one discriminant selects three or more paths; Branch is usually clearer for two. Decide whether cases end independently or rejoin a shared successor.
