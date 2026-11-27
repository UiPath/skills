# Submit a Connector to the Community Catalog

A connector in the community catalog is one any tenant can install from the Flow canvas.
You submit the same folder you built and published privately. Only a community-route (`--v4`) connector is submitted; a legacy connector stays private.

These steps run only in a terminal: `uip extension` needs the desktop CLI and `submit` needs the `gh` CLI. In Studio Web, stop and tell the user to run them from a terminal.

The "community route" (`--v4`) and the "community catalog" are two things. The route decides how activities run. The catalog is where a finished connector is shared, and it takes only connectors built on that route.

## Before you start

1. The connector is on the community route: `flags.v4Compatible` is `true` in `app/element/element-metadata.json`. If it is not, stop and tell the user a legacy connector cannot be submitted. Do not convert it by setting the flag: the activities need scripts ([v4-flow.md](v4-flow.md)).
2. The connector validates and is published to your own tenant (`uip is connectors publish --wait`), and you tested it there.
3. The user said yes to submitting. After a publish the skill asks once; a publish alone is not a yes.
4. `uip extension` is available. Run `uip extension --help`. If the command is unknown, stop and tell the user their CLI build has no community commands.
5. `gh` is signed in with push access to the index repository. `submit` and `submit --dry-run` both read the index and stop without it. `init` and `validate` need neither `gh` nor a login.

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
# Pick the level with "Choosing the bump" below, and confirm it with the user.
uip extension submit <PUBLISHER>.<NAME> --path <CONNECTOR_DIR> --bump <LEVEL> --output json
```

`submit` returns `Url` (the pull request), `ConnectorKey` and `Version`. Show all three to the user.

## Choosing the bump

The first submit of a node takes no `--bump` and is always `1.0.0`. Every later submit needs one. `submit` takes the highest version the catalog has approved and adds one step: from `1.2.0`, `patch` gives `1.2.1`, `minor` gives `1.3.0`, `major` gives `2.0.0`. The version in the folder plays no part.

An upgrade changes every flow in a tenant that uses the connector, so pick the level from what changed since the catalog's version:

| What changed | Level |
|---|---|
| A fix, a description, the icon. No activity, field, parameter or connection field is added, removed or renamed. | `patch` |
| Something was added and nothing existing changed: a new activity, a new optional field or parameter. | `minor` |
| Something a flow may already use changed: an activity, field or parameter was removed or renamed, an optional one became required, a type changed, or the auth type or a connection field changed. | `major` |

When both an addition and a breaking change are present, the level is `major`.

1. **Read the catalog's copy.** It is in the index repository under `nodes/<PUBLISHER>/<NAME>/`:
   ```bash
   gh api repos/UiPath/uipath-extensions/contents/nodes/<PUBLISHER>/<NAME>/app/element/element.json \
     -H "Accept: application/vnd.github.raw"
   ```
   Read the other files under `app/element/` the same way: `v4/activities.json` and `v4/objects/<RESOURCE>/metadata.json`.
2. **Compare it with the folder.** Compare activities, methods, fields, parameters, the auth type and the connection fields. Ignore the key and the version: the catalog's copy holds `custom-community-…` and its own version, the folder holds `design-<ORG>-<NAME>` and the tenant's.
3. **Propose a level** from the table, with the one change that decides it.
4. **Ask the user to confirm** (`AskUserQuestion`) before `submit`. Never send `major` without a yes, and never lower a level the user chose.
5. **If the catalog's copy cannot be read**, ask the user what changed since the last catalog version. Do not guess a level.

Nothing checks the level today: `submit` accepts any of the three. A wrong `patch` on a breaking change breaks flows in every tenant that upgrades.

## Rules

1. **The folder keeps its own key.** `validate` and `submit` set the catalog key in the copy they check and send. `element.json` and `element-metadata.json` in the folder still hold `design-<ORG>-<NAME>`, so `uip is connectors import` and `publish` keep working.
2. **Never write a `custom-community-` or `design-community-` key by hand.** `builder validate`, `import` and `publish` refuse it. If a folder already holds one, set `key` in `element.json` and `element-metadata.json` back to `design-<ORG>-<NAME>`.
3. **Two version counters.** `latestVersion` in the folder is the version your tenant publishes; bump it for each private re-publish. The catalog version is set by `submit`: `1.0.0` for the first one, then the highest approved version plus `--bump patch|minor|major`. They do not have to match.
4. **Fix findings in the folder.** A gate message may quote the catalog key. The file paths are the folder's own. Change the folder, test in your tenant if the change affects behavior, then run the same command again.
5. **A failed or pending pull request is updated, not replaced.** Run the same `submit` command again. It updates the open pull request and keeps the same version, because an open pull request adds no approved version. Never edit the index branch by hand.
6. **After a merge, the next submit needs `--bump`** and opens a new pull request. Choose the level as in [Choosing the bump](#choosing-the-bump).

## What the catalog does not do

- It does not change your private connector. `custom-<ORG>-<NAME>` stays in your tenant with its own connections.
- It does not move flows. A flow on the private connector stays on it; a flow uses the community connector only after a user installs it from the canvas and picks its activities.

## Anti-patterns

1. Editing the key in the folder to "prepare" it for the catalog (Rule 2).
2. Running `submit` before the connector is published and tested in a tenant.
3. Raising `--bump` to force a new version while the pull request is still open. Re-run the same command with the same level: the version does not change (Rule 5).
4. Validating a fork without its node id, which checks the shared key instead (step 2).
5. Sending `--bump patch` out of habit, or any level without comparing the folder with the catalog's copy and asking the user.
6. Reporting done on `validate` alone. `submit` also checks the index: the version, the fork rule and a key clash.
7. Submitting a legacy connector, or setting `flags.v4Compatible` by hand to make one pass.
