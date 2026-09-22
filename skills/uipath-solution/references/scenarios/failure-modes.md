# Cross-cutting failure modes

Symptoms that don't fit a single scenario but bite often enough to call out. Use this as triage when you don't yet know which scenario applies.

| Symptom | Likely cause | Fix |
|---|---|---|
| `[1009] <kind> <name>: Invalid argument 'Value'` at deploy | Virtual resource without `value` set ([virtual-resource](virtual-resource.md)) | `deploy config set <file> <name> value <val>` or `deploy config link <file> <name> --name <existing>` |
| Deployment sits in `OperationStatus: Draft` and won't activate | Deploy-time validation rejected a resource; the install never completed | Read the reasons (`Validation:` / `Conflicts:` — in `Instructions` on a tenant deploy, in `Message` on a `--wait`ed `--personal-workspace` / `--feed` one), fix them with `deploy config set` / `link`, then `deploy run --config-file <file>` again — see [A deploy that stops in `Draft`](../pack-and-deploy.md#a-deploy-that-stops-in-draft) |
| `deploy run --personal-workspace` / `--feed` reports `Status: DeploymentStarted` and nothing ever appears | Fire-and-forget is the default on those feeds — the command returns at request acceptance, so a later validation failure is never reported | Pass `--wait` to make the CLI poll and report the reason, or check `uip solution deploy list` for `OperationStatus` — with the same `--personal-workspace` / `--feed` flag, since `deploy list` is tenant-scoped without one and will not show the row at all |
| `Folder already exists` at deploy | `--folder-name` collides with an existing folder under `--parent-folder-path` | Pick a different `--folder-name`, or `solution deploy uninstall <existing>` first |
| Suffix `_N` keeps growing on re-refresh (`_1`, `_2`, `_3`...) | Old CLI version (pre-suffix-amplification fix) | Upgrade `@uipath/cli` to a build that ships the SDK bump (`resource-builder-sdk` ≥ `2025.11.0-alpha3780`); the current refresh is idempotent on cloud key |
| Tool dialog in Studio Web doesn't open for one of two same-name tools | SW UI bug — affects pure-SW solutions too ([same-name-across-folders](same-name-across-folders.md)) | Verified at deploy/runtime — ignore the UI symptom; check the tool resolves correctly via `resources list --source remote` after deploy |
| Refresh imports 0 of N bindings, no warnings | `bindings_v2.json` not at expected path (project root, not nested) | Move file to `<ProjectName>/bindings_v2.json`; `agent validate` regenerates it for agent projects |
| `processKey` collision on `solution publish` | Republishing same name+version | Bump version (`solution pack --version 1.0.1 …`); the feed rejects duplicate `name+version` pairs |

> See the individual scenario files for setup, root-cause walkthroughs, and verification steps.
