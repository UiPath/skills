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

## At a glance

End the current path and bind declared Flow outputs.

Choose between arm-local returns and a shared continuation based on the graph the scenario needs.
