# Manual Trigger

The manual trigger is the default start node. It represents an on-demand call
from a person, test, API, or parent automation; there is no factory call.

Signature: omit `.trigger(...)` and declare caller values with `.input(...)`.

```ts
export default flow('lookup').input({ id: types.string }).output({ value: types.string })
  .step('read', script({ code: 'return $vars.start.output.id;' }))
  .return({ value: out('read') }).build();
```

Choose this trigger only when something will supply each run's inputs. A local
run is a valid execution of that contract, but it does not prove that any
external caller or deployment integration exists.

A flow's declared inputs are published as the trigger node's OUTPUT, so
`input('name')` reads `$vars.start.output.name` — `out('start', 'name')` is the
same reference spelled the long way. Both spellings run: the bare `$vars.name`
resolves identically on the real runtime. Prefer the trigger form anyway — it is
what the designer TYPES the expression scope as, so a bare read is the one the
canvas reports as "Property 'name' does not exist".

This holds for EVERY trigger kind, not just the manual one. A declared input is
bound to whichever node starts the flow (that binding is the `triggerNodeId` on
the emitted variable), so an `onEvent(...)` flow reads its inputs through its
trigger too. The difference is only in what ELSE is there: an event trigger's
output carries the connector's payload alongside the declared inputs, so
`$vars.start.output.subject` and `$vars.start.output.queueName` can both be
live references on the same node.

The node's id is `start` by default and is addressable. Rename it with
`.triggerId('intake')` and every input reference follows
(`$vars.intake.output.name`).

Inside a `subflow` body the same form addresses the CHILD's own start node,
which the compiler names `<callerStepId>Start` — `input()` renders it for you,
so this matters only if you hand-write a `$vars.…` string in a child script.
