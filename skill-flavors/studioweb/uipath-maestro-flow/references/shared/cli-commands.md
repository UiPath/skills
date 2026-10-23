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
## uip solution publish

Publish the active solution to a feed; packaging and auth are handled by Studio Web:

```bash
uip solution publish --output json
uip solution publish --location "<key or name>" --output json
uip solution publish --personal-workspace --output json
```

With no destination flag: one destination publishes there; several publish nothing and list the choices — ask the user, then rerun with `--location`. Unknown flags fail the command. Publish is asynchronous — verify the terminal state in Studio Web's Publish history.

## uip solution deploy run

Install a published package into a NEW Orchestrator folder (shared-location packages only — personal-workspace publishes auto-deploy):

```bash
uip solution deploy run -n "<deployment-name>" --package-name "<package>" --package-version "<version>" --folder-name "<folder>" --parent-folder-path "<parent-path>" --output json
```

Pass `--personal-workspace` when the package was published to the personal workspace. `deploy run` never reuses a folder — see [operate/ship.md — Deploy](../operate/ship.md#deploy--install-the-package-into-a-folder) before the first run.
<!--skill-flavor:upload-command-section:end-->

<!--skill-flavor:flow-debug-command-usage:start-->
## uip maestro flow debug

Debug the open Flow through the host. Authentication comes from the active Studio Web session; there is no `uip login` step.

```bash
uip maestro flow debug

# Pass input arguments to the flow
uip maestro flow debug --inputs '{"numberA": 5, "numberB": 7}'

# Target a project other than the active one by name
uip maestro flow debug "<ProjectName>" --inputs '{"numberA": 5}'
```

The positional argument is a **project name in the open solution**, not a directory path, and it defaults to the active project. The host runs the already-saved project, so there is no pack or upload step.

> **Only the project name, `-i` / `--inputs`, `--entry-point` and `--timeout` are read.** Do not pass `--attachment`: a file-typed input cannot be bound this way, and before the project name its value is taken for the project. `--bpmn-file` and a local `.xaml` target are rejected with an explicit message. Inline JSON only; `@file` indirection is not supported.
<!--skill-flavor:flow-debug-command-usage:end-->

<!--skill-flavor:flow-debug-help-pointer:start-->
Run `uip maestro flow debug --help` for the host's exact surface.
<!--skill-flavor:flow-debug-help-pointer:end-->

<!--skill-flavor:flow-debug-args-note:start-->
File-typed inputs cannot be bound here: the host has no `--attachment`.
<!--skill-flavor:flow-debug-args-note:end-->

<!--skill-flavor:flow-debug-reporting:start-->
The output is plain text: a status line, `Trace ID: <id>` when one was found, `Run logs:` and `Execution trace:`. There is no Studio Web URL or instance id. Lead the summary with the status and the `Trace ID`, if one was printed. `TimedOut after <N>s` also exits 1, but the run is still going in the host and the timeout does not stop it: do not troubleshoot it, and do not re-run it. Tell the user to follow the run in Studio Web. Run debug again only after a fresh AskUserQuestion that says it executes the flow again, possibly while the first run is still going.
<!--skill-flavor:flow-debug-reporting:end-->
