# Upgrading a solution whose local entity has a `FILE` field

A Data Fabric entity authored locally (`uip df entities create --local`) stores a `FILE` field without the `EntityAttachment` reference that the deployed entity holds. Every upgrade of a solution with such an entity is rejected at validation, the first deploy is not:

```text
Conflicts: [TypeIncompatible] entity <E>: … The field '<F>' has incompatible properties that cannot be changed via deployment (ReferenceEntity: existing=EntityAttachment, incoming=(none)). (fix: FixConfiguration, UseExisting)
```

Nothing is installed, the deployment stays on its current version, and the attempt is kept as a pending draft that owns the deployment. Ontology solutions meet this whenever an entity they read has a `FILE` field.

## Fix

1. Ask the user whether entity `<E>` changed in the new version. When it did, stop: see [What `UseExisting` costs](#what-useexisting-costs).
2. Write the config for the new version and keep the installed entity:
   ```bash
   uip solution deploy config get <PACKAGE> -d "<CONFIG>" --package-version <NEW_VERSION> --output json
   uip solution deploy config set "<CONFIG>" <E> conflictFixingAction UseExisting --output json
   ```
   `<E>` is the entity's `name` in the config file. Repeat the `set` for each entity the conflict names.
3. Re-apply every link the deployment has, for example a federated entity's connection linked to the existing signed-in one:
   ```bash
   uip solution deploy config link "<CONFIG>" <CONNECTION> -n <EXISTING_CONNECTION> --folder-path "<CONNECTION_FOLDER>" --output json
   ```
   The file is the whole configuration the draft runs with; a link it leaves out is not carried over.
4. Finish the draft with `deploy run --config-file` under the draft's `--name` and `--package-version`, per [A deploy that stops in `Draft`](../pack-and-deploy.md#a-deploy-that-stops-in-draft). `--yes` is required on that rerun.
5. Confirm with `uip solution deploy status <DEPLOYMENT> --output json`: `PackageVersion` is the new version, `Operation` is `VersionChange` and `OperationStatus` is `Successful`.

## What `UseExisting` costs

`UseExisting` keeps the installed entity and its rows, and skips the package's version of that entity. A field added, removed or changed on that entity in the new version is not applied. Use it only when the entity is otherwise unchanged. When the entity really changed, tell the user there is no clean upgrade path for it until the CLI writes the `EntityAttachment` reference for local `FILE` fields. Never drop the `FILE` field to get past the conflict.
