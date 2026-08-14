# Error Handling

An error handler is a separate path from the immediately preceding action.

Signature: `.step(name, action).onError(handler => ...)`. Read the failure with
`err(step, 'code' | 'message' | 'detail' | 'category' | 'status')`; a handler
may `.return(...)`, `.terminate(...)`, or `.rejoin(forwardStep)`.

```ts
.step('fetch', http({ url, managed: true }))
.onError((h) => h.step('recover', script({ code: 'return "cached";' }))
  .rejoin('useValue'))
.step('useValue', script({ code: 'return "done";' }))
```

## Choosing the path

Do not add recovery merely because an error port exists. Decide whether the
business operation should fail loud, return an alternate answer, stop all work,
or compensate and rejoin. An exhausted handler ends separately; use rejoin only
when the failure path should deliberately resume shared success-path work.

## Evidence

Test both sides. The failure case should prove the handler receives the expected
service error and reaches its intended terminal/rejoin behavior. The success
case should prove normal continuation still bypasses the handler. A single green
case cannot establish both paths.
