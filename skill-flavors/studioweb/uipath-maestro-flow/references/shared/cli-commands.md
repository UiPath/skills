<!--skill-flavor:flow-init-command:start-->
<!--skill-flavor:flow-init-command:end-->

<!--skill-flavor:upload-safety-eval-surface-note:start-->
<!--skill-flavor:upload-safety-eval-surface-note:end-->

<!--skill-flavor:upload-pack-note:start-->
<!--skill-flavor:upload-pack-note:end-->

<!--skill-flavor:upload-refresh-prereq:start-->
Re-scan all projects in the solution and sync resource declarations (connections, processes, queues, etc.) from their `bindings_v2.json` files. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists. **Always run this before `uip maestro flow debug`.**
<!--skill-flavor:upload-refresh-prereq:end-->

<!--skill-flavor:upload-solution-dir-note:start-->
`<SolutionDir>` is the solution root (`/solution`). The command has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
<!--skill-flavor:upload-solution-dir-note:end-->

<!--skill-flavor:upload-command-section:start-->
<!--skill-flavor:upload-command-section:end-->
