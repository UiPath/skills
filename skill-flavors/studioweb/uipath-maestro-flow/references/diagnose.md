<!--skill-flavor:diagnose-step-0:start-->
`Faulted` on the first line of the `uip maestro flow debug` reply means the
reply in hand holds the reason. The reply is plain text, with no `Data` fields
and no instance id
([CLI-LOOP.md — Reading the reply](CLI-LOOP.md#reading-the-reply)). Find the
faulted element and its message in `Execution trace`. For more detail, run
`uip traces spans get <Trace ID>`. Do not re-run the flow. When you expect a
long reply, redirect it to a file as you start the run, then search the file:
<!--skill-flavor:diagnose-step-0:end-->

<!--skill-flavor:debug-redirect:start-->
```bash
cd /solution/<Project>
uip maestro flow debug "<Project>" > .flow-sdk/flow-debug.txt
```
<!--skill-flavor:debug-redirect:end-->

<!--skill-flavor:diagnose-auth:start-->
Studio Web signs you in, so these need no login step. Every `instance` command
and `incident get` also needs `--folder-key` (`-f`), or it is rejected before
reaching the API. Get the key from `uip or folders list --output json`, or from
the job or process context.
<!--skill-flavor:diagnose-auth:end-->

<!--skill-flavor:skip-registration-fix:start-->
**A project that is not part of the solution.** In Studio Web every project is
created inside the open solution, by `uip maestro flow init` or the designer, so
there is no partial scaffold to repair. If a Flow folder is missing from
`uip solution resources list`, report it rather than rebuilding it.
<!--skill-flavor:skip-registration-fix:end-->

<!--skill-flavor:misshapen-format:start-->
**Misshapen nodes on the canvas.** `compile` writes a placeholder
`ui.position` on each node — all of them on one row — and no top-level `layout`
block. In Studio Web this shows only on a new `.flow` that `compile` wrote
straight, with no merge: `merge` keeps the layout of the original and places
each added node, moving others to fit it; keep those moves. Fix such a new file once with
`uip maestro flow format <Name>.flow` — see
[`operate.md`](operate.md#lay-out-the-emitted-flow-first). Never run it on a
merged file: it lays out the canvas of the user again.
<!--skill-flavor:misshapen-format:end-->
