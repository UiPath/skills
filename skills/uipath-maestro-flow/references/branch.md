# Branch

Branch makes a two-way runtime decision.

Signature: `.branch(name, condition, thenFn, elseFn?)`. Each callback receives a
sub-builder and may use `.label(text)` for its edge label.

```ts
.branch('large', js`${input('amount')} > 1000`,
  (yes) => yes.step('review', script({ code: 'return "review";' })),
  (no) => no.step('approve', script({ code: 'return "approved";' })))
```

Use Branch when the scenario has two paths. Whether each arm should end locally
or fall through to shared work is a business-flow choice.

The two sequence ports are `true` and `false`. Arm `.label(text)` values become
`trueLabel` and `falseLabel`, defaulting to `True` and `False`.
