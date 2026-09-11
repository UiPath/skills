# Error Handling

An error handler is a separate path from the immediately preceding action.

Signature: `.step(name, action).onError(handler => ...)`.
Read the failure with `h.err(field)` — or `err(step, field)` if you prefer to name the step — where field is one of `code`, `message`, `detail`, `category`, `status` (plus `response` and `element`, present at run time though undeclared).
A handler may `.return(...)`, `.terminate(...)`, or `.stepToRef(target)`.

```ts
.step('fetch', http({ url, managed: true }))
.onError((h) => h.step('recover', script({ code: 'return "cached";' }))
  .stepToRef('useValue'))
.step('useValue', script({ code: 'return "done";' }))
```

## Reading the failure

`err()` writes ONE shape — `$vars.<step>.error.<field>` — and the compiler resolves where that family actually publishes the envelope.
Do not hand-write either prefix, and do not read the failed step's `out(...)` inside its own handler: that path runs because the step failed, so its success output was never written (`ERROR_ENVELOPE_VIA_OUTPUT`).

Which variable holds the envelope is a per-node-family runtime fact, measured one debug run per family (2026-09-10):

| family | envelope in | `<step>.error` is |
| --- | --- | --- |
| connector (every one) | `<step>.error` | the envelope |
| `core.action.script` | `<step>.error` | the envelope |
| `uipath.pattern.deep-rag` | `<step>.error` | the envelope |
| `core.subflow` | `<step>.error` | the envelope |
| `core.action.queue.create` | `<step>.error` | the envelope |
| `core.action.http.v2` (`managed: true`) | `<step>.output` | the boolean `true` |
| `core.action.http` (`managed: false`) | nowhere | the boolean `true` |

`serialize` rewrites the read for the exception families, so authored source stays uniform and a family moving is a table edit rather than a fleet-wide rewrite.
A bare `err(step)` is the did-this-fail test and is never rewritten: it reads truthy on every family, the envelope object included.

Plain `http({ managed: false })` publishes no envelope in any version — 1.0.0 and the 1.3 `uip maestro flow migrate` upgrades it to both leave `<step>.output` null — so `check` refuses a handler there (`HTTP_ONERROR_V1`) instead of emitting a read that resolves to nothing.
That node is also gone from the tenant registry, which serves only `core.action.http.v2`; `check` says so (`HTTP_V1_RETIRED`).
Moving to the managed node is a behaviour change, not a rename: a non-2xx stops arriving on the success path with `statusCode` and fails the step instead, so a status branch becomes a handler reading `err(step, 'status')`.

A `.loop()` container CAN carry a handler: `.onError()` after `.loop(...)` wires the container's own error port, and a body step's failure routes to it — measured, the container's envelope carries the body's message in `detail` and the failing body step's id in `element`, and the instance completes instead of faulting. Read it the usual way, `h.err('detail')`.

A `.doWhile()` cannot, and the reason is the handle rather than the variable: `core.logic.dowhile@1.0` declares an error variable but its handles are input, success, start, continue and break, so an edge would leave a handle the node does not have — the shape that fails product validate with "the current manifest does not declare that handle". Handle the failure inside the body, on the step that can fail. The builder refuses it by name.

`.onError(...)` is the `error` port case of `.stepToList(port, handler)`, which
runs a path from any named port. When the failure needs no work of its own, name
the target directly — `.stepToRef('error', 'refund')` — which is a SIDE EXIT: the
success path continues, so chaining carries on after it.

A `.stepToRef(target)` with no port leaves the default `output` port and HANDS THE
PATH OFF, so nothing may follow it in that list. The target may sit anywhere in the
same scope, including BACKWARD of the step that names it — Flow JSON can express
that, so this can author it.

## Choosing the path

Do not add recovery merely because an error port exists. Decide whether the
business operation should fail loud, return an alternate answer, stop all work,
or compensate and rejoin. An exhausted handler ends separately; use
`.stepToRef(...)` only when the failure path should deliberately resume shared
success-path work.

Two limits `check` enforces on a ref, and one it only warns about. It refuses an
unknown target, a target inside another port's path, and a target inside a LOOP
BODY — a loop reads `currentItem` / `currentIndex` per iteration, and an edge
arriving from outside carries no iteration. It WARNS when a ref leaves a loop body
(a break, which Flow has no node for) or crosses a parallel arm boundary (the Merge
waits for every branch it forked). Those are best effort: verify them with
`uip maestro flow validate`.

## Evidence

Test both sides. The failure case should prove the handler receives the expected
service error and reaches its intended terminal or ref behavior. The success
case should prove normal continuation still bypasses the handler. A single green
case cannot establish both paths.
