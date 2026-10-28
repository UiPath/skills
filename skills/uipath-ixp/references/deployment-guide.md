# Deployment Guide

The final step of a project's lifecycle: making a trained model version available beyond the labelling loop. Two distinct targets — pick from what the user needs, they are not interchangeable:

| Target | Command | What it gives you |
| --- | --- | --- |
| **Project** ("publish") | `uip ixp projects publish <project-name> --output json` | Marks the version published and, with `--tag`, moves the `live`/`staging` tag — the tagged version is what the DU framework, and DU activities that call through it, resolve. Also the rollback mechanism. |
| **Orchestrator folder** | `uip ixp deployments create <project-name> --version <N> --folder-key <guid> --output json` | Makes the model callable by folder-resolving runtime callers — Maestro Flow among them. Neither labelling nor `publish` is required first. |

Runtime callers split by how they address the model: folder-resolving callers (Maestro Flow nodes; anything reading folder deployments) see only the **folder** target, and tag-resolving callers (the DU framework API and its activities) see only the **project** target's tags. Neither substitutes for the other — pick per consumer, or do both. See the "Publish the model" row in [SKILL.md Task Navigation](../SKILL.md#task-navigation) for tags, rollback, and unpublish.

## Deploy to a folder

Ask which folder when none was identified — the folder decides which folder-resolving callers see the model. Running non-interactively (CI/headless — no user available to answer) with no folder identified by the request or an inbound handoff: stop and report the missing folder key. Never guess one, and never create a folder to fill the gap.

```bash
uip ixp projects list-models <project-name> --output json
uip ixp deployments create <project-name> --version <Version from list-models> \
  --folder-key <guid> --output json
```

Read `--version` from `list-models` immediately before deploying: the trained version advances while the project trains, and right after `projects create` the list can be empty for ~30s until the first version trains (deploy fails; wait and retry once).

Flags, `--folder-key` resolution, and moving an existing deployment to a newer version: [CLI Reference § Deployments](cli-reference.md#deployments) and [§ create vs upgrade](cli-reference.md#create-vs-upgrade).
