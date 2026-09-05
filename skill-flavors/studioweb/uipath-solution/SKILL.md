<!--skill-flavor:when-to-use-create:start-->
- User wants to add or remove projects in the open solution, or refresh solution resources (Studio Web works on one open solution; creating another is not possible here)
<!--skill-flavor:when-to-use-create:end-->

<!--skill-flavor:cli-surface-probe:start-->
Studio Web runs the post-rename CLI: use the commands and flags as documented in the references, with no probe. The open solution is the only solution — creating another is not possible here.
<!--skill-flavor:cli-surface-probe:end-->

<!--skill-flavor:rename-row-init:start-->
<!--skill-flavor:rename-row-init:end-->

<!--skill-flavor:probe-rule:start-->
1. **Studio Web runs the post-rename CLI.** Use the documented commands directly; the fallback table does not apply.
<!--skill-flavor:probe-rule:end-->

<!--skill-flavor:solution-lifecycle-steps:start-->
```
1. Create projects   → CreateProjects tool / New Project UI
2. resources refresh → Sync bundled artefacts with cloud state (if needed)
3. publish           → uip solution publish (packaging and auth handled by Studio Web)
4. deploy run        → uip solution deploy run (installs the published package into a folder)
```

> **No `pack`, `restore`, `login`, or `upload` steps in Studio Web.** The packager is Node-only and excluded from the browser bundle, authentication is injected by the host, and `/solution` already IS the open project so there is nothing to upload. `publish` and `deploy` both work here.

> **Publish destination — the user's choice.** Run `uip solution publish` with no destination flags first. With one destination it publishes there. With several it publishes nothing and lists them: ask the user in chat which destination to use — personal workspace (visible only to them) vs shared location (visible to others with access) — then rerun with `--location "<key or name>"` (or `--personal-workspace`). Skip the question when the user already named a destination; remember their answer for the rest of the conversation. Unknown flags fail the command — the destination flag is `--location`.

> **Publish is asynchronous.** Success means Unified Build accepted the request and packaging continues in the background — submitted is not shipped. Report destination, version, and request id; verify the terminal state in Studio Web's Publish history.

> **Publishing puts a package in a feed; deploying installs it into a folder.** A feed is a versioned package store, so a published-only package runs nowhere and does not appear in Orchestrator's solutions list. Publishing to the personal workspace auto-deploys, so it needs no deploy step. Publishing to a shared location never auto-deploys — finish it with `uip solution deploy run`, or leave it as a package deliberately.

> **`deploy run` creates a NEW Orchestrator folder every time.** `--folder-name` is required and is never reused: an existing name is collision-renamed, so repeated deploys leave `MyFolder`, `MyFolder_1`, `MyFolder_2` behind in a tenant other people share. It cannot deploy *into* an existing folder — the closest thing is `--parent-folder-path "<path>"` (or `--parent-folder-key`), which nests the new folder under that one; without it the folder is created at the tenant root. Publishing to the shared/tenant location does NOT put anything in the Orchestrator folder named `Shared` — that folder and the shared publish destination are different things, so deploying under it needs `--parent-folder-path "Shared"` explicitly. Confirm the deployment name, the folder name, and the parent path with the user before the first `deploy run`. Deploy from the feed you published to: a package on a personal-workspace feed is invisible to a plain `deploy run`, so pass `--personal-workspace` there too.

> **To ship a later version of a deployed solution, upgrade it — do not `deploy run` again.** Publish the new version, then `uip solution deploy upgrade <deployment-key>` moves the existing deployment in place, keeping its folder and configured values. It defaults to the newest published version; `--version` selects another, and `--personal-workspace` targets a personal-workspace deployment. A second `deploy run` would instead create yet another folder.

> **Pass the deployment's `Key`, not its `InstallDeploymentKey`.** Read the key from `uip solution deploy list` at the time you upgrade: after any version change the record's `Key` changes while `InstallDeploymentKey` keeps pointing at the original install. Reusing a key cached from an earlier `deploy run` fails with `HTTP 400` / errorCode `4005` "Another upgrade has already started for this deployment" — which reads like a stuck upgrade but really means the wrong key.

> **Deploy is asynchronous in two phases.** `deploy run` installs, polls to a terminal status, then activates unless `--skip-activate`; success is `Status: DeploymentSucceeded` with `ActivationStatus: SuccessfulActivate`. If activation fails the deployment still exists — fix the config and run `uip solution deploy activate <name>` rather than redeploying. Check state with `uip solution deploy status` / `deploy list`.
<!--skill-flavor:solution-lifecycle-steps:end-->

<!--skill-flavor:develop-solution-row:start-->
| [Develop a Solution](references/develop-solution.md) | `uip solution project add / import / remove / resources refresh / resources add / resources remove / resources edit`; field-tested gotchas |
<!--skill-flavor:develop-solution-row:end-->
