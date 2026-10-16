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

## Stopping another path at the same Terminate

A Terminate's name is a step name, so another path can stop there with
`.stepToRef(name)` instead of getting a Terminate of its own. The flow then has
ONE Terminate with several incoming edges, as the canvas draws it.
Needs `@uipath/maestro-builder-sdk` 6.32.2 or later; an older SDK refuses the
ref as `REF_INTO_PORT_LIST`, so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.

```ts
.stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).terminate('stopFailed'))
.stepToList('branch-throttled', (b) => b.step('reportThrottled', script({ code })).stepToRef('stopFailed'))
```

- The Terminate may sit inside another path (an HTTP `branch-*`, a
  human-task `outcome-*`, a `.stepSwitch` arm, an `.entryPoint` prefix). A ref
  into a STEP inside a `branch-*` or `outcome-*` list is still
  `REF_INTO_PORT_LIST`; a Terminate runs nothing after itself, so it is allowed.
- Spell each Terminate ONCE. Two `.terminate`s asking for the same name are
  refused (`DUP_STEP`; `compile --no-check` throws). They are not renamed
  `stopFailed2`. Stop the other paths with `.stepToRef('<name>')`. A step and a
  Terminate with one name are `DUP_STEP` too: rename one of them.
- A decompiled brownfield flow uses this form when a second path runs into a
  Terminate another path already stops at. Keep the `.stepToRef('<terminate id>')`
  when you edit.

## At a glance

Stop the entire Flow run, including sibling parallel arms.

Use it only for stop-all intent; prove cancellation with an abort-specific witness.
