# Return / End

Return ends the current path and binds the Flow's declared outputs.

Signature: `.return({ outputName: expression, ... })`.

```ts
.branch('valid', out('check'),
  (yes) => yes.return({ status: 'accepted' }),
  (no) => no.return({ status: 'rejected' }))
```

Returning in each arm is appropriate when those paths are complete. Let arms
fall through to a shared successor when they need common work before the final
answer. This is different from `.terminate(...)`: Return completes its path
with values; Terminate aborts the whole run.

Any dangling tail gets an End automatically; an explicit `.return(...)` is required
only when values must be bound. Multiple path ends are emitted as `end`, `end2`,
`end3`, and so on.
