# Error Handling

An error handler is separate from the preceding action: `.step(name, action).onError(handler => ...)`. Read failures with `h.err(field)` or `err(step, field)`, where `field` is `code`, `message`, `detail`, `category`, or `status`; `response` and `element` also exist at runtime. A handler may run recovery steps with `h.step(...)`, then `.return(...)`, `.terminate(...)`, or `.stepToRef(target)`.

`element` is the failing step's canvas label (`display.label`), not its id; the two are equal only when the step sets no `label` (`{ label: 'Fail A' }` fails with `element: "Fail A"`). A label is display text anyone editing the canvas can change, so route on `code` or `message`, never `element`.

## At a glance

Route the immediately preceding action's failure through a handler. `.stepToList(port, fn)` runs a path from any port; `.stepToRef(port, target)` is a side exit that leaves success running. Never read the failed step's `out(...)` inside its handler: success output was never written. Choose deliberately among handling, rejoining, returning, terminating, and failing loud; test success and failure.

## Reading the failure

`err()` writes `$vars.<step>.error.<field>`, while the compiler resolves where that family publishes its envelope; do not hand-write either prefix. Bare `err(step)` tests whether the step failed, is never rewritten, and is truthy for every family, including an envelope object.

Measured one debug run per family (2026-09-10):

| family | envelope in | `<step>.error` is |
| --- | --- | --- |
| connector (every one) | `<step>.error` | the envelope |
| `core.action.script` | `<step>.error` | the envelope |
| `uipath.pattern.deep-rag` | `<step>.error` | the envelope |
| `core.subflow` | `<step>.error` | the envelope |
| `core.action.queue.create` | `<step>.error` | the envelope |
| `core.action.http.v2` (`managed: true`) | `<step>.output` | the boolean `true` |

`serialize` rewrites exception-family reads so authored source stays uniform; a family move requires only a table edit. Never read a failed step's `out(...)` in its own handler (`ERROR_ENVELOPE_VIA_OUTPUT`).

`flow validate` warns `EXPRESSION_DIAGNOSTIC` for runtime-filled but undeclared `element` and `response` on any family (`Property 'element' does not exist on type '<Step>_Error'`), and for every managed HTTP envelope field whose rewritten `<step>.output` read is typed only as `{ error }` (`Property 'output' does not exist on type '{ error: <Step>_Error; }'`). Accept exactly these diagnostics on reads written with `err()` or `h.err()`; any other `EXPRESSION_DIAGNOSTIC` is a read that resolves to nothing.

A handled script failure still applies its own `{ updates }`; a sub-flow step and `.loop()` container do not. Put success-only updates on the following step.

Plain `http({ managed: false })` no longer runs: the tenant returns 500 `No handler registered for extension type 'Intsvc.HttpExecution'`, and its registry serves only `core.action.http.v2`. `check` warns `HTTP_V1_RETIRED` and refuses a handler there (`HTTP_ONERROR_V1`). Moving to the managed node is a behaviour change, not a rename: non-2xx responses fail the step instead of reaching success with `statusCode`, so a status branch becomes a handler reading `err(step, 'status')`.

A `.loop()` can carry a handler: `.onError()` after `.loop(...)` wires the container error port, and body failure routes there. Its measured container envelope has the body's message in `detail`, the failing body's canvas label in `element`, and the instance completes; read it with `h.err('detail')`. Inside a loop body, end a step handler with `.continue()` to skip the item and continue to the next ([`loops.md`](loops.md#loop-options)).

A sub-flow handler catches failure in any child step. Measured fields are `detail` (inner step's message), `element` (the failing inner step's canvas label), and `message` (the family's generic text, `Error invoking script task`); the instance completes. To give a run one failure path, put its steps in one child flow, call it as the parent's single step, and attach one `.onError()` there instead of handling every step.

A `.doWhile()` can carry a handler like `.loop()`: `.onError()` after `.doWhile(...)` wires the container error port, and body failure reaches it with `detail` as the body's message and `element` as the failing body step's canvas label. Although `core.logic.dowhile@1.0` lists no `error` handle, it sets `supportsErrorHandling: true`, so the product adds the handle from that flag.

`.onError(...)` is the `error`-port case of `.stepToList(port, handler)`, which runs a path from any named port. If failure needs no work, name the target directly with `.stepToRef('error', 'refund')`; this is a SIDE EXIT, so success continues and chaining carries on.

`.stepToRef(target)` without a port leaves the default `output` port and HANDS THE PATH OFF; nothing may follow it in that list. Its target may be anywhere in the same scope, including BACKWARD of the naming step, because Flow JSON can express that.

## Choosing the path

Do not add recovery merely because an error port exists. Decide whether the operation should fail loud, return an alternate answer, stop all work, or compensate and rejoin. An exhausted handler ends separately; use `.stepToRef(...)` only when failure should deliberately resume shared success-path work.

That separate End maps each flow output from its variable, like every End. A handler that sets outputs with `{ updates }` still answers with them; an unset output produces a `NO_RETURN` warning naming it. Set it with `{ updates }`, end with `.return({ … })`, or hand back with `.stepToRef(...)`.

`check` refuses a ref to an unknown target, a target inside another port's path, or a target inside a LOOP BODY: each iteration reads `currentItem` / `currentIteration`, while an outside edge carries no iteration. It WARNS when a ref leaves a loop body (a break, which Flow has no node for) or crosses a parallel-arm boundary (Merge waits for every forked branch). These are best effort; run `uip maestro flow validate` to verify them.

## Evidence

Test both sides. The failure case must prove the handler receives the expected service error and reaches its intended terminal or ref behavior; the success case must prove normal continuation bypasses the handler. One green case cannot establish both paths.
