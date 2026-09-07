<!--skill-flavor:ct-prerequisites:start-->
- Auth is host-provided — trigger nodes appear in the registry after `registry pull`; a 401/403 means the signed-in user lacks rights
- A healthy IS connection must exist for the connector. Before concluding none exists: derive the connector key from a `registry search` node type (never inferred from the service's brand name — the registry key is frequently prefixed or qualified differently), list with `uip is connections list "<connector-key>" --all-folders --output json`, and retry once with `--refresh`. An empty result from an unverified key or without `--all-folders` is a false negative, not "no connection." Only when absence is confirmed must the user create one before proceeding.
- `uip maestro flow registry pull` must be run to cache trigger node types locally
<!--skill-flavor:ct-prerequisites:end-->

<!--skill-flavor:ct-repull:start-->
If the trigger doesn't appear, re-pull the registry (auth is host-provided — there is no login status to check):

```bash
uip maestro flow registry pull --force
```
<!--skill-flavor:ct-repull:end-->

<!--skill-flavor:ct-debug-impact:start-->
> **Debug impact:** Only `polling` triggers can be debugged. `webhooks` triggers cannot be tested via `uip flow debug` — publish (`uip solution publish --location "<FolderPathOrKey>"`) and fire a real event. Flag this in the plan if the trigger uses webhook mode.
<!--skill-flavor:ct-debug-impact:end-->
