<!--skill-flavor:flow-init-command:start-->
<!--skill-flavor:flow-init-command:end-->

<!--skill-flavor:upload-safety-eval-surface-note:start-->
<!--skill-flavor:upload-safety-eval-surface-note:end-->

<!--skill-flavor:upload-pack-note:start-->
<!--skill-flavor:upload-pack-note:end-->

<!--skill-flavor:upload-refresh-prereq:start-->
Re-scan all projects in the solution and sync resource declarations (connections, processes, queues, etc.) from their `bindings_v2.json` files. Creates new resources for bindings not yet in the solution, imports from Orchestrator when a matching resource exists. **Always run this before `uip flow debug`.**
<!--skill-flavor:upload-refresh-prereq:end-->

<!--skill-flavor:upload-solution-dir-note:start-->
`<SolutionDir>` is the solution root (`/solution`). The command has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.
<!--skill-flavor:upload-solution-dir-note:end-->

<!--skill-flavor:upload-command-section:start-->
<!--skill-flavor:upload-command-section:end-->

<!--skill-flavor:flow-debug-command-usage:start-->
## uip flow debug

Debug the open Flow through the host. **In Studio Web the verb is `uip flow debug`, not `uip maestro flow debug`** — the browser bundle registers each tool under its own prefix, so `flow` is top-level here even though the Node CLI reaches it only under `uip maestro flow`. The three-token form is not intercepted and lands on a command whose debug service is excluded from the bundle, failing with `TypeError: FlowDebugService is not a constructor`. Authentication comes from the active Studio Web session; there is no `uip login` step.

```bash
uip flow debug --output json

# Pass input arguments to the flow
uip flow debug --inputs '{"numberA": 5, "numberB": 7}' --output json

# Target a project other than the active one by name
uip flow debug "<ProjectName>" --inputs '{"numberA": 5}' --output json
```

The positional argument is a **project name in the open solution**, not a directory path, and it defaults to the active project. The host runs the already-saved project, so there is no pack or upload step.

> **Only `-i` / `--inputs` is honoured.** The host interceptor accepts the project name and inputs; `--attachment` is not part of its surface and is ignored without warning, so a file-typed input cannot be bound this way. `--bpmn-file` and a local `.xaml` target are rejected with an explicit message. Inline JSON only — `@file` indirection is not supported.
<!--skill-flavor:flow-debug-command-usage:end-->

<!--skill-flavor:flow-debug-help-pointer:start-->
Run `uip flow debug --help` for the host's exact surface.
<!--skill-flavor:flow-debug-help-pointer:end-->
