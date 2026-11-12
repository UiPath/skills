# Branch

Use `.branch(name, condition, thenFn, elseFn?)` for a two-way runtime decision; each callback receives a sub-builder and may use `.label(text)` for its edge label.

```ts
.branch('large', js`${input('amount')} > 1000`,
  (yes) => yes.step('review', script({ code: 'return "review";' })),
  (no) => no.step('approve', script({ code: 'return "approved";' })))
```

Sequence ports are `true` and `false`; arm labels map to `trueLabel` and `falseLabel`, defaulting to `True` and `False`.

## At a glance

Arms may end locally or fall through to shared work.
