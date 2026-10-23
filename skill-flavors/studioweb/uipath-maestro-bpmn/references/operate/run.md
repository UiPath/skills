<!--skill-flavor:debug-intro:start-->
Use debug when the user wants to run the open BPMN project through the host
with full Studio Web visibility.
<!--skill-flavor:debug-intro:end-->

<!--skill-flavor:local-debug-solution:start-->
In Studio Web the BPMN project already lives in the open solution, so
generated resources, bindings, and debug metadata are available without
creating or importing anything.
<!--skill-flavor:local-debug-solution:end-->

<!--skill-flavor:debug-command-usage:start-->
```bash
uip maestro bpmn debug "<ProjectName>"
uip maestro bpmn debug "<ProjectName>" --inputs '{"orderId": "O-1"}'
uip maestro bpmn debug "<ProjectName>" --entry-point "<File>.bpmn#<StartEventId>"
```

The positional is a project name in the open solution, not a path, and
defaults to the active project. Pass input arguments only after confirming the
values and redacting secrets from summaries. `--inputs` takes inline JSON only;
`@file` is not supported. `--entry-point` takes the `filePath` exactly as
`entry-points.json` spells it; an unknown value lists the valid ones.
`--timeout <seconds>` defaults to `120`, clamped to `10`-`150`. Pass no other
flags. Run `uip maestro bpmn debug --help` for the host's exact surface.

> **Output is plain text, not JSON:** status, `Trace ID: <id>` when one was
> found, run logs, execution trace. Exit 1 means `Faulted` or `Failed`.
> `TimedOut after <N>s` also exits 1 but means the run is still going in the
> host, not faulted: do not troubleshoot it. Re-run with `--timeout 150` only
> if a longer wait could finish; otherwise tell the user to follow the run in
> Studio Web. It returns no instance id or
> Studio Web URL, so `debug-instance` reads have nothing to target. Read
> element outcomes and outputs from the execution trace.
<!--skill-flavor:debug-command-usage:end-->

<!--skill-flavor:debug-instance-inspection:start-->
A Studio Web debug returns no instance id. Inspect it through the run logs and
execution trace `uip maestro bpmn debug` printed.
<!--skill-flavor:debug-instance-inspection:end-->
