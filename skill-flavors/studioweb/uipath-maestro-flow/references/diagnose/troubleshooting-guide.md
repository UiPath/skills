<!--skill-flavor:troubleshoot-intro:start-->
Diagnostic workflow for failed debug runs and deployed process runs. The Studio Web host injects the session; never run `uip login`.
<!--skill-flavor:troubleshoot-intro:end-->

<!--skill-flavor:step-zero-debug-output:start-->
A faulted `uip maestro flow debug` prints the cause in its run logs and execution trace. **Do not re-run it before you read them.** An unchanged re-run executes the flow again against real systems. The output is plain text: there is no JSON to extract and no instance id for `debug-instance` reads, so diagnose from what it printed and correlate the faulting node with the `.flow` file (Step 3). `TimedOut after <N>s` also exits 1, but the run is still going in the host and the timeout does not stop it: do not troubleshoot it, and do not re-run it. Tell the user to follow the run in Studio Web. Run debug again only after a fresh AskUserQuestion that says it executes the flow again, possibly while the first run is still going.

For a deployed process run, continue with Step 1.
<!--skill-flavor:step-zero-debug-output:end-->
