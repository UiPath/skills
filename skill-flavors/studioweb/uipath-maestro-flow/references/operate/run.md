<!--skill-flavor:ship-orchestrator-path-pointer:start-->
For flows already deployed to Orchestrator:
<!--skill-flavor:ship-orchestrator-path-pointer:end-->

<!--skill-flavor:debug-command-intro:start-->
```bash
uip maestro flow debug "<ProjectName>"
```

The argument is a **project name in the open solution**, not a path, and defaults to the active project. The host runs the saved project and waits for a terminal state (`--timeout <seconds>`, default `120`, clamped to `10`-`150`). Pass only the project name, `--inputs`, `--entry-point` and `--timeout`: the host reads nothing else, and an unknown flag before the project name can be taken for it. Never start a second debug while one is running.
<!--skill-flavor:debug-command-intro:end-->

<!--skill-flavor:debug-inputs-example:start-->
Pass input arguments as inline JSON when the flow has input parameters (`@file` is not supported):

```bash
uip maestro flow debug "<ProjectName>" --inputs '{"numberA": 5, "numberB": 7}'
```
<!--skill-flavor:debug-inputs-example:end-->

<!--skill-flavor:debug-attachments:start-->
File-typed inputs cannot be bound here: the host has no `--attachment`.
<!--skill-flavor:debug-attachments:end-->

<!--skill-flavor:debug-reporting:start-->
The output is plain text: a status line, `Trace ID: <id>` when one was found, `Run logs:` and `Execution trace:`. There is no Studio Web URL or instance id. Lead the summary with the status and the `Trace ID`, if one was printed.
<!--skill-flavor:debug-reporting:end-->

<!--skill-flavor:debug-faults:start-->
A `Faulted` or `Failed` status exits 1, and the cause is in the run logs and execution trace that same output printed: read it there, do not re-run first. `TimedOut after <N>s` also exits 1, but the run is still going in the host and the timeout does not stop it: do not troubleshoot it, and do not re-run it. Tell the user to follow the run in Studio Web. Run debug again only after a fresh AskUserQuestion that says it executes the flow again, possibly while the first run is still going.
<!--skill-flavor:debug-faults:end-->
