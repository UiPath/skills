<!--skill-flavor:ship-content:start-->
# Ship — Publish and deploy from Studio Web

Shipping has two steps in this host: **publish** puts a versioned package in a feed; **deploy** installs it into an Orchestrator folder. Both run from this CLI. There is no `pack`, `restore`, `login`, or `upload` step — the host packages and authenticates, and `/solution` already IS the open project.

## Pre-flight

1. **Authoring is complete.** `uip maestro flow validate` passes and `uip maestro flow format` was run. If not, send the user back to [author/CAPABILITY.md](../author/CAPABILITY.md).
2. **Solution resources are refreshed** so connection and process resource declarations are in sync with the project bindings:

   ```bash
   uip solution resources refresh --solution-folder <SolutionDir> --output json
   ```

## Publish — put a package in a feed

Run `uip solution publish` with no destination flags first:

```bash
uip solution publish --output json
```

- With one destination it publishes there. With several it publishes nothing and lists them — ask the user which destination to use (personal workspace, visible only to them, vs shared location, visible to others with access), then rerun with `--location "<key or name>"` (or `--personal-workspace`). Skip the question when the user already named a destination; remember their answer for the rest of the conversation.
- Unknown flags fail the command — the destination flag is `--location`.
- **Publish is asynchronous.** Success means the request was accepted and packaging continues in the background — submitted is not shipped. Report destination, version, and request id; verify the terminal state in Studio Web's Publish history.

## Deploy — install the package into a folder

A published-only package runs nowhere and does not appear in Orchestrator's solutions list. Publishing to the personal workspace auto-deploys — no deploy step needed. Publishing to a shared location never auto-deploys — finish it with `uip solution deploy run`, or leave it as a package deliberately:

```bash
uip solution deploy run -n "<deployment-name>" --package-name "<package>" --package-version "<version>" --folder-name "<folder>" --parent-folder-path "<parent-path>" --output json
```

1. **`deploy run` creates a NEW Orchestrator folder every time.** `--folder-name` is never reused: an existing name is collision-renamed (`MyFolder`, `MyFolder_1`, …) in a tenant other people share. It cannot deploy *into* an existing folder — `--parent-folder-path "<path>"` (or `--parent-folder-key`) nests the new folder under that one; without it the folder is created at the tenant root. Confirm the deployment name, the folder name, and the parent path with the user before the first `deploy run`.
2. **Deploy from the feed you published to.** A package on a personal-workspace feed is invisible to a plain `deploy run` — pass `--personal-workspace` there too.
3. **Deploy is asynchronous in two phases.** `deploy run` installs, polls to a terminal status, then activates unless `--skip-activate`; success is `Status: DeploymentSucceeded` with `ActivationStatus: SuccessfulActivate`. If activation fails the deployment still exists — fix the config and run `uip solution deploy activate <name>` rather than redeploying.
4. **Ship a later version by upgrading, not redeploying.** Publish the new version, then `uip solution deploy upgrade <deployment-key>` moves the existing deployment in place (read the `Key` from `uip solution deploy list` at upgrade time). A second `deploy run` would create yet another folder.

## Anti-patterns

- **Never report that publication or deployment is "owned by Studio Web" or unavailable from the CLI.** `uip solution publish` and `uip solution deploy run` both work in this host.
- **Never run `solution upload` or `solution pack` here.** `/solution` already IS the open project; the packager is Node-only and excluded from the browser bundle.
- **Never pick a publish destination or a deploy folder name for the user.** Destinations and the first deployment's folder layout are the user's choice.
- **Never publish a flow that hasn't been validated and formatted.** `flow validate` catches schema errors; `flow format` ensures Studio Web renders nodes correctly.

## What's next

After deploying, the user typically wants to **trigger and monitor** the deployed process — see [run.md](run.md). For deploy configs, activation details, and upgrades, see [/uipath:uipath-solution](/uipath:uipath-solution).
<!--skill-flavor:ship-content:end-->
