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

## Ending another path at the same End

Give the End a `name`, and another path can end there with `.stepToRef(name)`
instead of getting an End of its own. The flow then has ONE End with several
incoming edges, as the canvas draws it.

```ts
.step('fetch', http({ url, managed: false, branches: [{ name: 'missing', condition: js`$vars.fetch.output.statusCode === 404` }] }))
.stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).stepToRef('done'))
.step('useResult', script({ code }))
.return({}, { name: 'done' })   // reportMissing -> done, useResult -> done
```

- Only a NAMED End is a target. An unnamed `.return()` gets `end`, `end2`, ... in
  emission order, so `.stepToRef('end')` is `REF_UNKNOWN_TARGET` unless an End
  says `{ name: 'end' }`.
- `check` refuses a ref to a name that two Ends, or a step and an End, share
  (`REF_AMBIGUOUS_TARGET`).
- A decompiled brownfield flow uses this form when a side path (an HTTP
  `branch-*`, a human-task `outcome-*`, an error handler) runs into the End the
  main path ends at. Keep the `.stepToRef('<end id>')` and the End's `name` when
  you edit.

## At a glance

End the current path and bind declared Flow outputs.

Choose between arm-local returns and a shared continuation based on the graph the scenario needs.
