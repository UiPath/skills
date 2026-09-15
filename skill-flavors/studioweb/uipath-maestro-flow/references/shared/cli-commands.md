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
