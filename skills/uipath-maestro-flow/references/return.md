# Return / End

`.return({ outputName: expression, ... })` ends the current path and binds Flow outputs; return in every complete arm, or use a shared successor when common work remains.

```ts
.branch('valid', out('check'),
  (yes) => yes.return({ status: 'accepted' }),
  (no) => no.return({ status: 'rejected' }))
```

`.terminate(...)` aborts the whole run. Dangling tails receive an End unless the flow calls `.openTails()` (decompile writes it; see [brownfield.md](brownfield.md#a-path-without-an-end-stays-open)). Use explicit `.return(...)` only when values must be bound. Multiple path ends emit as `end`, `end2`, `end3`, and so on.

Only an End sets a flow output. If a step sets an output with `{ updates }`, code reads it as `$vars.<output>`, or a `{ shared }` input/default feeds one, the SDK stores it in `<output>Value`; every End maps that output from the Variable. Still declare and write the output's own name:

```ts
.output({ summary: types.string })
.step('work', script({ code: 'return "hi";', returns: 'string' }), { updates: { summary: out('work') } })
// summaryValue (inout) = $vars.work.output; each End: summary <- $vars.summaryValue
```

- Read the result by its output name: `variables.globals.summary` in debug read-back; ignore adjacent `summaryValue`.
- Never use `<output>Value` for an input, output, `.var()`, step, entry point, or trigger id: `check` reports `OUTPUT_BACKING_COLLISION`; rename yours.
- An End with no output name and no backing Variable returns `null` for that output.

## Ending another path at the same End

Name an End so another path can use `.stepToRef(name)` instead of creating its own; one End may have multiple incoming edges. This requires `@uipath/maestro-builder-sdk` 6.32.0 or later; an older SDK refuses the ref with `REF_UNKNOWN_TARGET`.
<!--skill-flavor:named-end-sdk-upgrade:start-->
Run `npm install -g @uipath/maestro-builder-sdk@latest` to upgrade.
<!--skill-flavor:named-end-sdk-upgrade:end-->

```ts
.step('fetch', http({ url, managed: false, branches: [{ name: 'missing', condition: js`$vars.fetch.output.statusCode === 404` }] }))
.stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).stepToRef('done'))
.step('useResult', script({ code }))
.return({}, { name: 'done' })   // reportMissing -> done, useResult -> done
```

- Only a named End is a target. Unnamed `.return()` ends emit `end`, `end2`, ... in emission order; `.stepToRef('end')` is `REF_UNKNOWN_TARGET` unless an End declares `{ name: 'end' }`.
- An End may be inside another port's path, and two side paths that the main path never reaches may share one End. This requires `@uipath/maestro-builder-sdk` 6.32.1 or later; an older SDK refuses the ref (`REF_INTO_PORT_LIST`) and renames a differing duplicate End `failed2`.
<!--skill-flavor:port-end-sdk-upgrade:start-->
  Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`:
<!--skill-flavor:port-end-sdk-upgrade:end-->

  ```ts
  .stepToList('branch-missing', (b) => b.step('reportMissing', script({ code })).return({}, { name: 'failed' }))
  .stepToList('branch-throttled', (b) => b.step('reportThrottled', script({ code })).stepToRef('failed'))
  ```

- Two `.return`s with the same name but different values, label, version, or updates, or in different scopes (such as a loop body and main path), are refused by `check` and `compile` with `DUP_END_NAME`; they are not renamed `failed2`. Identical repeats in one scope are one End. Prefer one `.return` and `.stepToRef('<name>')` elsewhere.
- An End's `name` is its node id and is never renamed. A name used by a step, trigger, or entry point is refused by `check` and `compile` with `STEP_ID_COLLISION`; for example, `.step('x', ...).return({}, { name: 'x' })` fails `check`. Give the End its own name, such as `endX`. This requires `@uipath/maestro-builder-sdk` 6.32.3 or later; an older SDK renames the End `x2` without error.
<!--skill-flavor:end-name-sdk-upgrade:start-->
  Upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`:
<!--skill-flavor:end-name-sdk-upgrade:end-->
- In a decompiled brownfield flow, an HTTP `branch-*`, human-task `outcome-*`, `.stepSwitch` arm, error handler, or `.entryPoint` prefix may reach an End already used by another path. Preserve `.stepToRef('<end id>')` and that End's `name` when editing.

## At a glance

End the current path and bind declared Flow outputs. Use arm-local returns or a shared continuation according to the graph.