# Subflow

*Behavior and worked examples. Exact signatures, fields, and defaults: [`subflow()`](api.md#subflow-function).*

Subflow packages a child Flow authored in the same source file as one parent
step.

Signature: `subflow(childFlow, { childInput: expression, ... })`.

```ts
const child = flow('normalize').input({ raw: types.string })
  .output({ clean: types.string }).step('trim', script({ code: 'return $vars.raw.trim();' }))
  .return({ clean: out('trim') }).build();
export default flow('parent').input({ text: types.string }).output({ clean: types.string })
  .step('normalized', subflow(child, { raw: input('text') })).return({ clean: out('normalized', 'clean') }).build();
```

Use a child for a meaningful contract or a unit of reuse, not as a speed
optimization or an arbitrary split. Local instrumentation observes the parent
step's data path; it does not turn that boundary into a separate deployed job.

Read a child output by its declared name — `out('reverse', 'reversed')`, never a bare
`out('reverse')`. The compiler serializes each call's body under top-level `subflows`.
