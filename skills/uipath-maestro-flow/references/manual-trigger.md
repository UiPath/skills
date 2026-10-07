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
same reference spelled the long way. Do not read an input as a bare `$vars.name`.
It resolves only by accident — a manual trigger also emits a process-level copy of
each input — and is null under any other trigger. The designer reports it as
"Property 'name' does not exist", and `check`, `compile` and `uip maestro flow
validate` all refuse it. `$vars.name` is the spelling for a `.var()` or an output.

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

## At a glance

The default start node accepts on-demand caller input; omit `.trigger(...)`.

Signature: `flow(id).input({...}).step(...).build()`.

Choose it when a caller, test, or another process should start each run.

## Multiple entry points

A flow may have more than one root. `.trigger()` / `.input()` stay the DEFAULT
root; `.entryPoint(id, trigger, { inputs?, version? }, prefixFn?)` adds another
— its own trigger node, its own scoped inputs (read them with
`entryInput('<id>', '<name>')`, i.e. `$vars.<id>.output.<name>`), and an
optional prefix that runs before the root joins the first shared step. A prefix
that ends terminally (or hands off with `.stepToRef(...)`) joins nothing.

Every root's inputs need their own names. Inputs, outputs and vars share one
namespace, `uip maestro flow validate` refuses two globals with the same id even
on different triggers, and each entry point's caller-facing input is keyed by
that id. So two roots cannot both take `amount`; `check` reports
`ENTRY_POINT_INPUT_COLLISION`.

To run a root other than the default, pass `--entry-point <id>` (the `id` you
gave `.entryPoint`; the default root's trigger is `start`) to
`uip maestro flow debug` or `uip maestro flow process run`.

### One input, whichever root fired: `{ shared }`

This is the default way to hand the shared body "the input, whichever root
started the run". Mark each root's input with the variable it feeds, and read
that variable in the body:

```ts
export default flow('refund-intake')
  .input({ amount: { type: types.number, shared: 'refundAmount' } })             // default root
  .entryPoint('review', manual(), {
    inputs: { reviewedAmount: { type: types.number, shared: 'refundAmount' } },  // second root
  })
  .output({ summary: types.string })
  .step('summarize', script({ code: 'return "refund of " + $vars.refundAmount;', returns: 'string' }))
  .return({ summary: out('summarize') })
  .build();
```

`manual()` is the factory `.entryPoint` takes for an on-demand root; the
default root still omits `.trigger(...)`.

- **The SDK declares the variable** once, unless a `.var('refundAmount', …)` or
  `.output({ refundAmount })` already exists. Declare the `.var()` yourself to give
  it a default.
- **The copy is one row per root on its TRIGGER node**, in
  `variables.variableUpdates[<triggerId>]`. This is the same construct `{ updates }`
  writes for a step. Here `start` gets `refundAmount ← $vars.start.output.amount`
  and `review` gets `refundAmount ← $vars.review.output.reviewedAmount`.
- **The copy runs before that root's prefix**, so a prefix can read
  `$vars.refundAmount` too.
- **Read it as a var:** `v('refundAmount')` in an Expr slot, `$vars.refundAmount`
  in script code. Do not write a copy step or a `.var()` + `entryInput(...)`
  `{ updates }` by hand; the default root has no prefix to hold one.
- **A root that feeds nothing** leaves the variable at its default, or null.

`check` codes (`compile` throws on the errors even when its `check` pass is skipped):

| code | level | means |
|---|---|---|
| `SHARED_INPUT_TYPE_MISMATCH` | error | an input's type differs from the variable's |
| `SHARED_INPUT_TARGET_IS_INPUT` | error | the variable is named after an input |
| `SHARED_INPUT_SAME_ROOT` | error | one root feeds the variable from two inputs |
| `SHARED_INPUT_IN_SUBFLOW` | error | `shared` on a subflow child's input (a subflow has one root, its caller) |
| `SHARED_INPUT_ROOT_MISSING` | warning | some root feeds nothing and the variable has no default |

Decompile turns a trigger-level copy of exactly this shape back into
`{ shared }`; any other update on a trigger node is reported, not dropped.

### Reshaping per root: a prefix

When a root's input needs *reshaping* before the body can use it (a lookup, a
default, a different shape), not a plain copy, give that root a prefix. The
prefix runs on that root only, then joins the first shared step:

```ts
flow('order-intake')
  .input({ order: types.object })                       // default (manual) root
  .entryPoint('nightly', scheduled({ every: 'R/P1D' }), {
    inputs: { batchDate: types.string },
  }, (b) => b.step('loadBatch', script({
    code: 'return { note: $vars.nightly.output.batchDate };', returns: 'object' })))
  .step('normalize', script({ code: 'return 1;' }))     // shared body
```

The two combine: `shared` copies what is the same on every root, and a prefix
reshapes the rest.
