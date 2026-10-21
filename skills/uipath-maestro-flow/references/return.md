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

Any dangling tail gets an End automatically, unless the flow calls
`.openTails()` (decompile writes it; see
[brownfield.md](brownfield.md#a-path-without-an-end-stays-open)). An explicit
`.return(...)` is required only when values must be bound. Multiple path ends are emitted as `end`, `end2`,
`end3`, and so on.

Only an End sets a flow output. When a step sets an output with `{ updates }`,
code reads it as `$vars.<output>`, or a `{ shared }` input or a default feeds
it, the SDK holds the value in a Variable named `<output>Value`, and every End
maps the output from it. You still write the output's own name:

```ts
.output({ summary: types.string })
.step('work', script({ code: 'return "hi";', returns: 'string' }), { updates: { summary: out('work') } })
// emits: summaryValue (inout) = $vars.work.output; each End: summary <- $vars.summaryValue
```

- Read the result by the output's name: `variables.globals.summary` in the
  debug read-back. `summaryValue` can appear beside it; ignore it.
- Do not give anything else the name `<output>Value`: an input, output,
  `.var()`, step, entry point, or trigger id. `check` reports
  `OUTPUT_BACKING_COLLISION`; rename yours.
- An End that does not name an output, and has no such Variable behind it,
  returns `null` for it.

## Ending another path at the same End

Give the End a `name`, and another path can end there with `.stepToRef(name)`
instead of getting an End of its own. The flow then has ONE End with several
incoming edges, as the canvas draws it. Needs `@uipath/maestro-builder-sdk`
6.32.0 or later; an older SDK refuses the ref with `REF_UNKNOWN_TARGET`, so
upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.

```ts
.step('fetch', http({ url, managed: false, branches: [{ name: 'missing', condition: js`$vars.fetch.output.statusCode === 404` }] }))
.stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).stepToRef('done'))
.step('useResult', script({ code }))
.return({}, { name: 'done' })   // reportMissing -> done, useResult -> done
```

- Only a NAMED End is a target. An unnamed `.return()` gets `end`, `end2`, ... in
  emission order, so `.stepToRef('end')` is `REF_UNKNOWN_TARGET` unless an End
  says `{ name: 'end' }`.
- The End may sit inside another port's path. Two side paths that the main
  path never reaches can share one End. Needs `@uipath/maestro-builder-sdk`
  6.32.1 or later; an older SDK refuses the ref (`REF_INTO_PORT_LIST`) and
  renames a differing duplicate End `failed2`, so upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`:

  ```ts
  .stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).return({}, { name: 'failed' }))
  .stepToList('branch-throttled', (b) => b.step('reportThrottled', script({ code })).stepToRef('failed'))
  ```

- Two `.return`s with the same name and different values, label, version or
  updates, or in different scopes (a loop body and the main path), are refused
  (`DUP_END_NAME`; `compile --no-check` throws). They are not renamed
  `failed2`. Identical repeats in one scope are one End. Prefer one `.return`
  and `.stepToRef('<name>')` on the other paths.
- An End's `name` is its node id and is never renamed. A name that a step,
  the trigger or an entry point already uses is refused (`STEP_ID_COLLISION`;
  `compile --no-check` throws). For example, `.step('x', ...).return({}, { name: 'x' })`
  fails `check`. Give the End its own name, such as `endX`. Needs
  `@uipath/maestro-builder-sdk` 6.32.3 or later; an older SDK renames the End
  `x2` with no error, so upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`.
- A decompiled brownfield flow uses this form when a path (an HTTP `branch-*`,
  a human-task `outcome-*`, a `.stepSwitch` arm, an error handler, an
  `.entryPoint` prefix) runs into an End another path already ends at. Keep the
  `.stepToRef('<end id>')` and the End's `name` when you edit.

## At a glance

End the current path and bind declared Flow outputs.

Choose between arm-local returns and a shared continuation based on the graph the scenario needs.
