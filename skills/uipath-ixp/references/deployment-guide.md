# Deployment Guide

The final step of a project's lifecycle: making a trained model version available beyond the labelling loop. Two distinct targets — pick from what the user needs, they are not interchangeable:

| Target | Command | What it gives you |
| --- | --- | --- |
| **Project** ("publish") | `uip ixp projects publish <project-name> --output json` | Marks the version published *inside* the project — version pinning, `live`/`staging` tags, rollback. Nothing outside the project can call it. |
| **Orchestrator folder** | `uip ixp deployments create <project-name> --version <N> --folder-key <guid> --output json` | Makes the model callable at runtime by activity packs and Maestro Flow. Neither labelling nor `publish` is required first. |

Runtime callers — Maestro Flow nodes and IXP activity packs alike — resolve the model through the **folder** target. Publish additionally when the user wants the version marked published; see the "Publish the model" row in [SKILL.md Task Navigation](../SKILL.md#task-navigation) for tags, rollback, and unpublish.

## Deploy to a folder

Ask which folder when none was identified — the folder decides which runtime callers see the model.

```bash
uip ixp projects list-models <project-name> --output json
uip ixp deployments create <project-name> --version <Version from list-models> \
  --folder-key <guid> --output json
```

Read `--version` from `list-models` immediately before deploying: the trained version advances while the project trains, and right after `projects create` the list can be empty for ~30s until the first version trains (deploy fails; wait and retry once).

Flags, `--folder-key` resolution, and moving an existing deployment to a newer version: [CLI Reference § Deployments](cli-reference.md#deployments) and [§ create vs upgrade](cli-reference.md#create-vs-upgrade).
