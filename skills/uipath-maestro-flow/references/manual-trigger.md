# Manual Trigger

The manual trigger is the default start node: an on-demand call from a person, test, API, or parent automation, with no factory call. Omit `.trigger(...)` and declare caller values with `.input(...)`; use `.trigger(manual(), { updates })` only when the default root needs its own variable rows ([below](#other-variable-updates-on-a-trigger)).

```ts
export default flow('lookup').input({ id: types.string }).output({ value: types.string })
  .step('read', script({ code: 'return $vars.start.output.id;' }))
  .return({ value: out('read') }).build();
```

Declared inputs are the trigger node's OUTPUT: `input('name')` reads `$vars.start.output.name`, and `out('start', 'name')` is equivalent. Never read one as bare `$vars.name`; it works only accidentally because a manual trigger emits a process-level copy and is null under other triggers. The designer reports `Property 'name' does not exist`; `check`, `compile`, and `uip maestro flow validate` refuse it. `$vars.name` is for a `.var()` or output.

This applies to every trigger kind. Inputs bind to the starting node (`triggerNodeId` on the emitted variable), so an `onEvent(...)` flow also reads them through its trigger. Its output may additionally contain connector payload fields, such as `$vars.start.output.subject` and `$vars.start.output.queueName`, alongside declared inputs.

The default node id is `start`; rename it with `.triggerId('intake')`, then use `$vars.intake.output.name`. In a `subflow` body, the child start node is `<callerStepId>Start`; `input()` renders this automatically, but hand-written child-script `$vars.…` strings must use that name.

## At a glance

Signature: `flow(id).input({...}).step(...).build()`.

Choose it only when something supplies every run's inputs. A local run satisfies the contract but does not prove an external caller or deployment integration exists.

## Multiple entry points

A flow may have multiple roots. `.trigger()` / `.input()` remain the DEFAULT root. Add `.entryPoint(id, trigger, { inputs?, version?, updates? }, prefixFn?)` for a root with its own trigger and scoped inputs, read as `entryInput('<id>', '<name>')` or `$vars.<id>.output.<name>`, with an optional prefix before the roots join the first shared step. A terminal prefix or one ending with `.stepToRef(...)` joins nothing.

Every root's inputs need unique names. Inputs, outputs, and vars share one namespace; `uip maestro flow validate` rejects duplicate global ids even across triggers, and each entry point's caller-facing input is keyed by that id. Two roots cannot both use `amount`; `check` reports `ENTRY_POINT_INPUT_COLLISION`.

<!--skill-flavor:manual-trigger-entry-point:start-->
To run a non-default root, pass `--entry-point <id>` (the `.entryPoint` id; the default root is `start` unless `.triggerId(...)` is set) to `uip maestro flow debug` or `uip maestro flow process run`.
<!--skill-flavor:manual-trigger-entry-point:end-->

### One input, whichever root fired: `{ shared }`

This is the default way to hand the shared body "the input, whichever root started the run". Mark each root input with the variable it feeds, then read that variable with `v('refundAmount')` in an Expr slot or `$vars.refundAmount` in script code. `manual()` is the `.entryPoint` factory; the default root still omits `.trigger(...)` unless it needs `{ updates }`.

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

The SDK declares the variable once unless `.var('refundAmount', …)` or `.output({ refundAmount })` already exists. Declare `.var()` to provide a default. If the input feeds an output, the copy writes the output backing Variable, `refundAmountValue` ([return.md](return.md)). Each root gets one copy row at `variables.variableUpdates[<triggerId>]`: `start` writes `refundAmount ← $vars.start.output.amount`, and `review` writes `refundAmount ← $vars.review.output.reviewedAmount`. Copies run before the root prefix, so the prefix can read `$vars.refundAmount`.

For a plain copy use `shared`, not a copy step or hand-written trigger `{ updates }` row; decompile restores only `{ shared }`. A root feeding nothing leaves the variable at its default, or null.

`check` codes (`compile` throws on these errors even when its `check` pass is skipped):

| code | level | means |
|---|---|---|
| `SHARED_INPUT_TYPE_MISMATCH` | error | an input's type differs from the variable's |
| `SHARED_INPUT_TARGET_IS_INPUT` | error | the variable is named after an input |
| `SHARED_INPUT_SAME_ROOT` | error | one root feeds the variable from two inputs |
| `SHARED_INPUT_IN_SUBFLOW` | error | `shared` is used on a subflow child's input; a subflow has one root, its caller |
| `SHARED_INPUT_ROOT_MISSING` | warning | some root feeds nothing and the variable has no default |

Decompile restores a trigger-level copy of exactly this shape as `{ shared }`; any other trigger-node update becomes that trigger's own `{ updates }` (below).

### Other variable updates on a trigger

<!--skill-flavor:trigger-updates-sdk-version:start-->
Needs `@uipath/maestro-builder-sdk` 6.85.7 or later. Check that `entryPoint(` in `dist/flow-sdk.d.ts` of the SDK copy in use takes `'version' | 'label' | 'updates'`. An older SDK refuses `.trigger(spec, { updates })` (`UPDATES_NOT_SUPPORTED`) and compiles `.entryPoint(id, spec, { updates })` with no row. Upgrade it: run `npm install @uipath/maestro-builder-sdk@latest` in a workspace with its own `node_modules` copy (used before the global one), or run `npm install -g @uipath/maestro-builder-sdk@latest`. If upgrading is impossible, set the variable in the first step's `{ updates }` instead.
<!--skill-flavor:trigger-updates-sdk-version:end-->

`.trigger(spec, { updates })` and `.entryPoint(id, spec, { updates })` write other rows on that root's trigger node. Rows run when the root fires, after `{ shared }` copies, in written order, and may read trigger-published values. For instance, take a payload field and keep the variable's own value when the field is missing:

```ts
flow('investigate')
  .input({ payload: types.object })
  .var('doc', types.object)
  .trigger(manual(), { updates: { doc: js`${input('payload')}.document ?? ${v('doc')}` } })
```

This writes `doc ← $vars.start.output.payload.document ?? $vars.doc` under `variableUpdates.start`. `check` validates targets as it does a step's (`UPDATE_INPUT_READONLY`, `UPDATE_UNKNOWN_VAR`). A subflow child's `.trigger(manual(), { updates })` writes rows on its Start node.

### Reshaping per root: a prefix

Use a prefix when a root's input needs reshaping before the shared body—such as a lookup, default, or different shape—rather than a plain copy. It runs only on that root, then joins the first shared step:

```ts
flow('order-intake')
  .input({ order: types.object })                       // default (manual) root
  .entryPoint('nightly', scheduled({ every: 'R/P1D' }), {
    inputs: { batchDate: types.string },
  }, (b) => b.step('loadBatch', script({
    code: 'return { note: $vars.nightly.output.batchDate };', returns: 'object' })))
  .step('normalize', script({ code: 'return 1;' }))     // shared body
```

`shared` copies what is identical across roots; a prefix reshapes the rest.
