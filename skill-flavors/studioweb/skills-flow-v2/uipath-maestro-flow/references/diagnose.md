<!--skill-flavor:debug-redirect:start-->
```bash
uip flow debug <Project> --output json > /tmp/flow-debug.json
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
each added node. Fix such a new file once with
`uip maestro flow format <Name>.flow` — see
[`operate.md`](operate.md#lay-out-the-emitted-flow-first). Never run it on a
merged file: it lays out the canvas of the user again.
<!--skill-flavor:misshapen-format:end-->
