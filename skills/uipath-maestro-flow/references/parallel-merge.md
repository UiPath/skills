# Parallel / Merge

Parallel fans control into two or more arms and joins them on a Merge.

Signature: `.parallel(name, [armFn, armFn, ...])`; `name` identifies the Merge.

```ts
.parallel('ready', [
  (a) => a.step('weather', http({ url: weatherUrl, managed: false })),
  (b) => b.step('news', http({ url: newsUrl, managed: false })),
])
.step('combine', script({ code: 'return "ready";' }))
```

Use parallel only when the arms are independent: neither arm may require the
other's result before the join. It expresses graph independence, not a promise
that every executor schedules work concurrently; the local executor processes
arms in authored order.

Work after `.parallel(...)` continues from its `output` port and can read the
outputs of each arm.

When every arm ends, with `.return`, `.terminate`, or a `.stepToRef` into an
End another arm wrote, there is nothing to join. No Merge is emitted, `name`
names no node, and nothing may follow the `.parallel`:

```ts
.step('prepare', script({ code: 'return 1;' }))
.parallel('prepareFork', [
  (a) => a.step('notifyA', script({ code: 'return "a";' })).return({}, { name: 'done' }),
  (b) => b.step('notifyB', script({ code: 'return "b";' })).stepToRef('done'),
])
```

A `.terminate` must be the arm's first call: `check` refuses one behind a step
in a `.parallel` arm (`TERMINATE_NOT_ARM_HEAD`).

Decompile (SDK 6.46.6 or later) writes a canvas fan-out whose arms never meet
again this way, naming the `.parallel` `<node>Fork` after the node the arms
leave. A canvas arm that runs a step before its Terminate is the exception: it
stays an unstructured fan-out (see [brownfield.md](brownfield.md)).

## At a glance

Fan out independent arms and join them at a Merge.

Use it only for independent arms; do not assume the local executor runs them concurrently.

## Options

`.parallel(name, arms, options)` takes `version` and `label` for the Merge, as `.branch()` does, plus `fork`.
Both below need `@uipath/maestro-builder-sdk` 6.44.0 or later; an older SDK ignores `fork` (no fork node is written, and the TypeScript types reject the option),
<!--skill-flavor:fork-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fork-sdk-upgrade:end-->

### A fork node

Studio Web draws a parallel split as a `core.logic.merge` node with one edge in and one edge per arm (its "Parallel" gateway).
`fork` writes that node; without it the arms leave from the previous step's own port, one edge per arm, and the platform runs both shapes the same way.
Use it to keep a canvas flow's shape.
A decompiled canvas fork comes back with it, so leave it as written: dropping it deletes the fork node and rewires every arm.

```ts
.parallel('J1', [
  (a) => a.step('T1', work),
  (b) => b.step('T2', work),
], { fork: { name: 'PAR', label: 'Parallel: run the applicable tasks together' }, label: 'Join: wait for every branch' })
```

The fork's name is a node id like a step's; `check` reports `DUP_STEP` when a step already has it.

### Arms that join at a step instead of a Merge

The canvas also lets two steps feed one step directly, with no Merge node anywhere.
Spell that with arms that each end in `.stepToRef('<step>')`, and that step after the `.parallel`.
When no arm hands the join a tail, compile writes no Merge node, and the refs are the join.
That step then has one incoming edge per arm, and the runtime starts a step once per arriving token (only a gateway waits for every incoming flow), so it runs once per arm — not once after all arms, as a Merge would.
`check` says so (`PARALLEL_REF_JOIN`, a warning); for one run, end each arm on a step of its own and put the shared step after the `.parallel`.

```ts
.parallel('prepareFork', [
  (a) => a.step('script1', work).stepToRef('sendMessage'),
  (b) => b.step('script2', work).stepToRef('sendMessage'),
])
.step('sendMessage', script({ code: 'return [$vars.script1.output, $vars.script2.output];' }))
```

`prepareFork` creates no node, but do not reuse it as a step or variable name: `check` treats `$vars.prepareFork` as a Merge read (`PARALLEL_HAS_NO_OUTPUT`).
Decompile writes this shape as `<source>Fork`, and a merge node with one edge in and one out (a pass-through the designer left behind) as the `rawNode` of its own definition; leave both as written, warning included.
