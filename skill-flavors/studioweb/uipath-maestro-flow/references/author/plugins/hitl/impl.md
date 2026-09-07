<!--skill-flavor:hitl-impl-http-fallback:start-->
<!--skill-flavor:hitl-impl-http-fallback:end-->

<!--skill-flavor:hitl-impl-debug-table:start-->
| Error | Cause | Fix |
| --- | --- | --- |
| Node type not found in registry (Option 2) | App not published or registry stale | If in same solution: `uip solution resources list --kind App --output json`. Otherwise: `uip maestro flow registry pull --force` (auth is host-provided; a 401/403 means missing rights) |
| Task never completes | Human has not submitted the form | Check task assignment in Orchestrator |
| Output missing expected fields | App form does not match expected schema | Verify app form fields match what the flow expects |
| `outcome-completed` port unwired (Option 1) | Missing edge on output handle | Wire the `outcome-completed` output handle; an unwired `outcome-completed` blocks the flow indefinitely |
| Run never finishes; instance stays `Running` until the timeout, ports all wired | A HITL node sits in a flow nothing will attend — no assignee, or an unattended run (schedule, `flow debug`, eval) | Confirm a human will open the task. If the run is unattended, use a mechanism that completes on its own — see [planning.md](planning.md#when-to-select) |
<!--skill-flavor:hitl-impl-debug-table:end-->
