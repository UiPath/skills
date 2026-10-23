<!--skill-flavor:troubleshoot-intro:start-->
Diagnostic workflow for failed debug runs and deployed process runs. The Studio Web host injects the session; never run `uip login`.
<!--skill-flavor:troubleshoot-intro:end-->

<!--skill-flavor:step-zero-debug-output:start-->
A faulted `uip maestro flow debug` prints the cause in its run logs and execution trace. **Do not re-run it before you read them.** An unchanged re-run executes the flow again against real systems. The output is plain text: there is no JSON to extract and no instance id for `debug-instance` reads, so diagnose from what it printed and correlate the faulting node with the `.flow` file (Step 3). `TimedOut after <N>s` also exits 1 but means the run is still going in the host, not faulted: do not troubleshoot it. Re-run with `--timeout 150` only if a longer wait could finish; otherwise tell the user to follow the run in Studio Web.

For a deployed process run, continue with Step 1.
<!--skill-flavor:step-zero-debug-output:end-->
