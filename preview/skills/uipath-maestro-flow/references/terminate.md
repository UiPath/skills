# Terminate

Terminate stops the entire run. In a parallel arm it aborts sibling work; it
does not complete the Flow with output values.

Signature: `.terminate(name, label?)`.

```ts
.branch('fatal', input('fatal'),
  (yes) => yes.terminate('abort', 'Abort run'),
  (no) => no.step('continue', script({ code: 'return "ok";' })))
```

Choose Terminate only when the requirement is stop-all rather than return an
answer from one path. A green run alone is weak evidence for this node. Use an
abort-specific witness: for example, show that a sibling side effect never
happened or that the run reached the terminated state without producing normal
Flow outputs.

Inside a parallel arm it aborts sibling arms, whereas `.return(...)` only ends its
own path. Its mappings are terminal metadata, not a readable action result:
`out('<terminate>')` remains invalid.
