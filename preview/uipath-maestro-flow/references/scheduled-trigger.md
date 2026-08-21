# Scheduled Trigger

*Behavior and worked examples. Exact signatures, fields, and defaults: [`scheduled()`](api.md#scheduled-function).*

A scheduled trigger asks the platform scheduler to start a Flow repeatedly.

Signature: `.trigger(scheduled({ every: string }))`.

```ts
export default flow('nightly')
  .trigger(scheduled({ every: 'R/P1D' }))
  .step('rollup', script({ code: 'return { ok: true };' }))
  .build();
```

## Authoring judgment

A timer usually has no caller, so prefer `.var(...)` defaults or tenant-backed
steps over required caller inputs unless the deployment supplies configured
values. Pick the interval from the business requirement rather than from what
is convenient to test.

## Evidence boundary

Local execution starts the graph directly. It proves the scheduled node was
emitted with the authored interval and that the downstream graph runs; it does
not prove the platform scheduler fired. The scheduling claim requires a
deployed run observed at the requested cadence.

`every` is an ISO-8601 repeating interval: `R/PT30M`, `R/PT1H`, `R/P1W`.
