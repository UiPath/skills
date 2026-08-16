# Subflow

*Behavior and worked examples. Exact signatures, fields, and defaults: [`subflow()`](api.md#subflow-function).*

Subflow packages a child Flow authored in the same source file as one parent
step.

Signature: `subflow(childFlow, { childInput: expression, ... })`.

```ts
const child = flow('normalize').input({ raw: types.string })
  .output({ clean: types.string })
  .step('trim', script({ code: js`return ${input('raw')}.trim();`.js, returns: { clean: 'string' } }))
  .return({ clean: out('trim', 'clean') }).build();
export default flow('parent').input({ text: types.string }).output({ clean: types.string })
  .step('normalized', subflow(child, { raw: input('text') })).return({ clean: out('normalized', 'clean') }).build();
```

Read the child's own inputs with `input(...)`, not a hand-written `$vars.raw`. A
declared input is bound to the node that starts its flow, and a child's start
node is named after the CALLER — `<callerStepId>Start`. The script above emits
`return $vars.normalizedStart.output.raw.trim();`, so hand-writing the reference
would both be wrong and break the moment the parent step is renamed. See
[`manual-trigger.md`](manual-trigger.md).

Use a child for a meaningful contract or a unit of reuse, not as a speed
optimization or an arbitrary split. Local instrumentation observes the parent
step's data path; it does not turn that boundary into a separate deployed job.

Read a child output by its declared name — `out('reverse', 'reversed')`, never a bare
`out('reverse')`. The compiler serializes each call's body under top-level `subflows`.
