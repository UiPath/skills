# Error Handling

An error handler is separate from the preceding action: use `.step(name, action).onError(handler => ...)`. Read failures with `h.err(field)` or `err(step, field)`, where `field` is `code`, `message`, `detail`, `category`, or `status`, plus runtime-only `response` and `element`. `element` is the failing step's canvas `display.label`, not its id. The two are equal only when the step sets no `label`: `.step('failA', script(…), { label: 'Fail A' })` fails with `element: "Fail A"`, not `"failA"`. Labels are editable, so route on `code` or `message`, never `element`. A handler may `.return(...)`, `.terminate(...)`, or `.stepToRef(target)`.

```ts
.step('fetch', http({ url, managed: true }))
.onError((h) => h.step('recover', script({ code: 'return "cached";' }))
  .stepToRef('useValue'))
.step('useValue', script({ code: 'return "done";' }))
```

## At a glance

Route failures through a handler path. `.stepToList(port, fn)` runs a path from any port; `.stepToRef(port, target)` is a side exit that leaves success running. `.stepToRef(target)` uses default `output`, HANDS THE PATH OFF, and must be the list's final operation; its target may be anywhere in the same scope, including BACKWARD of the naming step. Never read failed-step `out(...)` in its handler: success output was never written (`ERROR_ENVELOPE_VIA_OUTPUT`). Choose deliberately between handling, rejoining, returning, terminating, and failing loud; test success and failure.

## Reading the failure

`err()` writes `$vars.<step>.error.<field>`; the compiler resolves the family-specific publication location. Never hand-write either prefix. Bare `err(step)` tests failure, is never rewritten, and is truthy for every family, including envelope values.

| family | envelope in | `<step>.error` is |
| --- | --- | --- |
| connector (every one) | `<step>.error` | the envelope |
| `core.action.script` | `<step>.error` | the envelope |
| `uipath.pattern.deep-rag` | `<step>.error` | the envelope |
| `core.subflow` | `<step>.error` | the envelope |
| `core.action.queue.create` | `<step>.error` | the envelope |
| `core.action.http.v2` (`managed: true`) | `<step>.output` | the boolean `true` |
| `core.action.http` (`managed: false`) | nowhere | the boolean `true` |

`serialize` rewrites exception-family reads, keeping authored source uniform; update the family table rather than fleet-wide source. `flow validate` warns `EXPRESSION_DIAGNOSTIC` for runtime-filled but undeclared `element` and `response` on any family (`Property 'element' does not exist on type '<Step>_Error'`), and for every managed HTTP envelope field because rewritten `<step>.output` is typed only as `{ error }` (`Property 'output' does not exist on type '{ error: <Step>_Error; }'`). Accept exactly these diagnostics on reads written with `err()` or `h.err()`; any other `EXPRESSION_DIAGNOSTIC` resolves to nothing.

When a handled step fails, a script step still applies its own `{ updates }`; a sub-flow and `.loop()` container do not. Put success-only updates on the following step.

Plain `http({ managed: false })` publishes no envelope in any version: 1.0.0 and the 1.3 `uip maestro flow migrate` upgrades it to both leave `<step>.output` null. `check` therefore refuses its handler (`HTTP_ONERROR_V1`) rather than emitting a useless read. The node is retired from the tenant registry, which serves only `core.action.http.v2`; `check` reports `HTTP_V1_RETIRED`. Moving to the managed node makes non-2xx fail instead of reaching success with `statusCode`; read the status branch in a handler with `err(step, 'status')`.

A `.loop()` may carry a handler: `.onError()` after `.loop(...)` wires the container error port; body failures route there, and the instance completes with the body's message in `detail` and failing body label in `element`. Read it with `h.err('detail')`. Inside a loop body, end a step handler with `.continue()` to skip the item and continue to the next ([`loops.md`](loops.md#loop-options)).

A sub-flow handler catches any child-step failure; the instance completes with the inner message in `detail`, inner canvas label in `element`, and generic family `message` (`Error invoking script task`). For one failure path, put steps in one child flow, call it as the parent's single step, and attach one `.onError()` there instead of handling each step.

A `.doWhile()` may carry a handler like `.loop()`: `.onError()` after `.doWhile(...)` wires its error port. Although `core.logic.dowhile@1.0` lists no `error` handle, it sets `supportsErrorHandling: true`, so the product adds one; body failures route with body message in `detail` and canvas label in `element`.

`.onError(...)` is the `error`-port form of `.stepToList(port, handler)`, which runs a path from any named port. If no work is needed, name the target directly with `.stepToRef('error', 'refund')`; this SIDE EXIT leaves success running, so chaining continues afterward.

## Choosing the path

Do not add recovery merely because an error port exists. Decide whether the operation should fail loud, return an alternate answer, stop all work, or compensate and rejoin. An exhausted handler ends separately; use `.stepToRef(...)` only when failure should deliberately resume shared success work.

That separate End maps each flow output from its variable, like every End. A handler that sets outputs with `{ updates }` still answers with them; an unset output produces a `NO_RETURN` warning naming it. Set it with `{ updates }`, end with `.return({ … })`, or hand back with `.stepToRef(...)`.

`check` refuses a ref to an unknown target, a target inside another port's path, or a target inside a LOOP BODY: a loop reads `currentItem` / `currentIteration` per iteration, while an outside edge carries no iteration. It WARNS when a ref leaves a loop body (a break, which Flow has no node for) or crosses a parallel arm boundary (Merge waits for every forked branch). These are best effort; run `uip maestro flow validate` to verify them.

## Evidence

Test both sides. The failure case must prove the handler receives the expected service error and reaches its intended terminal or ref behavior; the success case must prove normal continuation bypasses the handler. One green case cannot establish both paths.