<!--skill-flavor:local-debug-solution:start-->
In Studio Web the BPMN project already lives in the open solution at
`/solution/<ProjectDirName>/`, so generated resources, bindings, and debug
metadata are available without creating or importing anything.

Run debug with `uip bpmn run`. Studio Web intercepts it and runs the open
project through its own Debug service, then waits for a terminal state. Do not
use the `maestro bpmn debug` verb here: Studio Web does not intercept it, so it
reaches the browser CLI instead of the Debug service.

```bash
uip bpmn run <ProjectName>
```

`<ProjectName>` is the project's name in the open solution. Omit it to run the
active project. Pass input arguments only after confirming the values and
redacting secrets from summaries. Inputs are inline JSON; `@file` is not
supported:

```bash
uip bpmn run <ProjectName> --inputs '<INPUTS_JSON>'
```

Optional flags: `--entry-point <ENTRY_POINT>`, spelled exactly as in
`entry-points.json`, and `--timeout <SECONDS>` (default 120, clamped to
10–150). There is no `--folder-id` and no `--bpmn-file`.

The output is text, not JSON: a status line, `Trace ID`, `Run logs`, and
`Execution trace`. Exit code 1 means the run failed or did not start. Report
the status and the trace ID. No Studio Web URL is returned, because the run is
already on the open canvas.

> **A successful status is not a correct result.** It proves the process ran,
> NOT that any output variable holds the expected value. Read node results from
> `Execution trace`. If it reads `(no execution traces emitted)`, or the value
> you need is not in it, report that output as unverified.
<!--skill-flavor:local-debug-solution:end-->

<!--skill-flavor:debug-not-validation:start-->
- **Never run `uip bpmn run` as validation.** Use Author validation and packaging checks for correctness;
  a run executes the process.
<!--skill-flavor:debug-not-validation:end-->
