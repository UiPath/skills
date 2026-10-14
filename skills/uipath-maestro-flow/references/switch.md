# Switch

Switch routes one value among several cases.

Signature:
`.switch(name, on, [{ value: string | number | boolean, label?, body }], defaultFn?)`;
a case may use `when: Expr` instead of `value` (below).

```ts
.switch('priority', input('priority'), [
  { value: 'high', body: (b) => b.step('page', script({ code: 'return 1;' })) },
  { value: 'low', body: (b) => b.step('queue', script({ code: 'return 2;' })) },
], (other) => other.step('normal', script({ code: 'return 3;' })))
```

Prefer Switch when one discriminant selects three or more paths; Branch is
usually clearer for two. Decide whether cases end independently or rejoin a
shared successor.

Cases compare strictly (`===`) from top to bottom. Each case gets a generated
`case-<id>` port; the optional final callback uses `default`.

A case can carry its own condition instead of a value: ``{ when: js`...`, label?,
body }``. The switch takes the first case whose condition is true. Pass
`undefined` for `on` when every case uses `when`:

```ts
.switch('route', undefined, [
  { when: js`$vars.start.output.amount > 100`, label: 'High', body: (b) => b.step('review', script({ code: 'return 1;' })) },
  { when: js`$vars.start.output.amount <= 100`, label: 'Low', body: (b) => b.step('auto', script({ code: 'return 2;' })) },
])
```

A case has exactly one of `value` or `when` (`SWITCH_CASE_FORM` otherwise), and
a `value` case needs an `on`. Decompile writes `when` cases for a designer-drawn
switch whose cases are not one shared `<discriminant> === <value>`; keep them.

A decompiled switch the designer drew may carry `id: "default-1"` (and so on) on
its cases. That keeps the case ids the original file has, so the merged edges
match the original switch node. Leave those `id`s as they are; do not add one to
a case you write yourself.

## At a glance

Split runtime control among cases of one discriminant.

Signature: `.switch(name, on, [{ value, label?, body }], defaultFn?)`; a case may use
`when: Expr` instead of `value`, with `on` = `undefined` when every case does.

```ts
.switch('priority', input('priority'), [
  { value: 'high', body: (b) => b.step('page', script({ code: 'return 1;' })) },
  { value: 'low', body: (b) => b.step('queue', script({ code: 'return 2;' })) },
])
```

Prefer switch when one value selects three or more paths; use branch for two.
