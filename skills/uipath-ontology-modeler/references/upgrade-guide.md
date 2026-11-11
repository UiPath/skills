# Upgrading a deployed ontology solution

Read this when an ontology solution that is already deployed gets a new version. The upgrade itself runs through `uipath-solution` (its *deploy upgrade* flow). This guide covers the one rejection that every ontology solution with a `FILE` field meets.

## `TypeIncompatible` on a `FILE` field

A locally authored entity stores a `FILE` field without the `EntityAttachment` reference that the deployed entity holds. Every upgrade of a solution with such an entity is then rejected at validation:

```text
Conflicts: [TypeIncompatible] entity <E>: … The field '<F>' has incompatible properties that cannot be changed via deployment (ReferenceEntity: existing=EntityAttachment, incoming=(none)). (fix: FixConfiguration, UseExisting)
```

Nothing is installed and the deployment stays on its current version. The attempt is kept as a pending draft, and the draft blocks every other version until it is finished. `deploy upgrade` takes no config file, so finish the draft with `deploy run` under the same name and version:

1. Write the config for the new version and keep the installed entity:
   ```bash
   uip solution deploy config get <PACKAGE> -d "<CONFIG>" --package-version <NEW_VERSION> --output json
   uip solution deploy config set "<CONFIG>" <E> conflictFixingAction UseExisting --output json
   ```
   `<E>` is the entity's `name` in the config file. Repeat the `set` for each entity the conflict names.
2. Re-apply every link the deployment has, for example a federated entity's connection linked to the existing one:
   ```bash
   uip solution deploy config link "<CONFIG>" <CONNECTION> -n <EXISTING_CONNECTION> --folder-path "<CONNECTION_FOLDER>" --output json
   ```
   The file is the whole configuration the draft runs with; a link it leaves out is not carried over.
3. Finish the draft:
   ```bash
   uip solution deploy run -n <DEPLOYMENT> --package-name <PACKAGE> --package-version <NEW_VERSION> --folder-name <FOLDER_NAME> --parent-folder-path "<PARENT>" --config-file "<CONFIG>" --yes --output json
   ```
   Use the same `-n` and `--package-version` as the draft. `--yes` is required: without it the CLI stops with `Package '<PACKAGE>' is already deployed in this tenant` and sends nothing. The same `-n` updates that deployment in its existing folder; it does not create a second one.
4. Confirm with `uip solution deploy status <DEPLOYMENT> --output json`: `PackageVersion` is the new version, `Operation` is `VersionChange` and `OperationStatus` is `Successful`. Then check the ontology state in the deployment folder.

## What `UseExisting` costs

`UseExisting` keeps the installed entity and its rows, and skips the package's version of that entity. A field added, removed or changed on that entity in the new version is not applied. Use it only when the entity is otherwise unchanged. When the entity really changed, stop and tell the user: there is no clean upgrade path for it until the CLI writes the `EntityAttachment` reference for local `FILE` fields. Never drop the `FILE` field to get past the conflict.
