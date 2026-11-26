# Submit a Connector to the Community Catalog

A connector in the community catalog is one any tenant can install from the Flow canvas.
You submit the same folder you built and published privately. It works for a legacy and a community-route (`--v4`) connector alike.

The "community route" (`--v4`) and the "community catalog" are two things. The route decides how activities run. The catalog is where a finished connector is shared.

## Before you start

1. The connector validates and is published to your own tenant (`uip is connectors publish --wait`), and you tested it there.
2. `uip extension` is available. Run `uip extension --help`. If the command is unknown, stop and tell the user their CLI build has no community commands.
3. `gh` is signed in with push access to the index repository. `submit` and `submit --dry-run` both read the index and stop without it. `init` and `validate` need neither `gh` nor a login.

## Node id and key

The node id is `<PUBLISHER>.<NAME>`, lowercase letters and digits only in each part.

| Node id | What it is | Key in the catalog |
|---|---|---|
| `uipath.<NAME>` | The shared connector of a vendor. Only UiPath GitHub org members register it. Anyone improves it with a pull request. | `custom-community-<NAME>` |
| `<PUBLISHER>.<NAME>` | A fork, allowed only when `uipath.<NAME>` already exists. | `custom-community-<NAME>_<PUBLISHER>` |

Ask the user which node id to use. Do not guess the publisher.

## Workflow

```bash
# 1. Once per connector: write uipath-extensions.json and assets/icon.png.
#    The connector's key and version are not changed.
uip extension init <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> --yes

# 2. Run the catalog's gates. Pass the node id for a fork; without it the
#    folder is checked as the shared connector uipath.<name>.
uip extension validate <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> --output json

# 3. Preview: prints the key, the version and the pull request. Opens nothing.
uip extension submit <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> --dry-run --output json

# 4. Submit. The first registration of a node needs --security-contact.
uip extension submit <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> \
  --security-contact <EMAIL> --output json

# A later version of a node the catalog already holds needs --bump.
uip extension submit <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> --bump patch --output json
```

`submit` returns `Url` (the pull request), `ConnectorKey` and `Version`. Show all three to the user.

## Rules

1. **The folder keeps its own key.** `validate` and `submit` set the catalog key in the copy they check and send. `element.json` and `element-metadata.json` in the folder still hold `design-<ORG>-<NAME>`, so `uip is connectors import` and `publish` keep working.
2. **Never write a `custom-community-` or `design-community-` key by hand.** `builder validate`, `import` and `publish` refuse it. If a folder already holds one, set `key` in `element.json` and `element-metadata.json` back to `design-<ORG>-<NAME>`.
3. **Two version counters.** `latestVersion` in the folder is the version your tenant publishes; bump it for each private re-publish. The catalog version is set by `submit`: `1.0.0` for the first one, then the highest approved version plus `--bump patch|minor|major`. They do not have to match.
4. **Fix findings in the folder.** A gate message may quote the catalog key. The file paths are the folder's own. Change the folder, test in your tenant if the change affects behavior, then run the same command again.
5. **A failed or pending pull request is updated, not replaced.** Run the same `submit` command again. It updates the open pull request and keeps the same version, because an open pull request adds no approved version. Never edit the index branch by hand.
6. **After a merge, the next submit needs `--bump`** and opens a new pull request.
7. **`--bump` is for connectors only.** It takes `patch`, `minor` or `major`.

## What the catalog does not do

- It does not change your private connector. `custom-<ORG>-<NAME>` stays in your tenant with its own connections.
- It does not move flows. A flow on the private connector stays on it; a flow uses the community connector only after a user installs it from the canvas and picks its activities.

## Anti-patterns

1. Editing the key in the folder to "prepare" it for the catalog (Rule 2).
2. Running `submit` before the connector is published and tested in a tenant.
3. Passing `--bump` again and again to "retry" — a re-run with the same `--bump` keeps the same version while the pull request is open (Rule 5).
4. Validating a fork without its node id, which checks the shared key instead (step 2).
5. Reporting done on `validate` alone. `submit` also checks the index: the version, the fork rule and a key clash.
