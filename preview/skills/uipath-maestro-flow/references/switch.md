# Switch

Switch routes one value among several cases.

Signature:
`.switch(name, on, [{ value: string | number | boolean, label?, body }], defaultFn?)`.

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
