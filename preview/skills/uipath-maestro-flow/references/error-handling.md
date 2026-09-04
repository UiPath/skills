# Error Handling

An error handler is a separate path from the immediately preceding action.

Signature: `.step(name, action).onError(handler => ...)`. Read the failure with
`err(step, 'code' | 'message' | 'detail' | 'category' | 'status')`; a handler
may `.return(...)`, `.terminate(...)`, or `.stepToRef(target)`.

```ts
.step('fetch', http({ url, managed: true }))
.onError((h) => h.step('recover', script({ code: 'return "cached";' }))
  .stepToRef('useValue'))
.step('useValue', script({ code: 'return "done";' }))
```

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
