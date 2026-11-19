# Solutions that carry an ontology

An ontology solution carries its entities and choice sets as local resources. At deploy they are created in the target folder, or merged into a same-name entity there, before the ontology installs. Data Fabric entities and choice sets keep their own conflict actions.

**Ontology names are unique per folder.** Deploying to another folder creates a separate ontology.

- A same-name ontology in the target folder that this solution already owns (same resource key) is a normal upgrade. There is no prompt.
- A same-name ontology the solution does not own is a conflict. The deploy pre-check reports it with `allowedActions: [Replace, RenameInSolution]`, and the deploy cannot continue until it is resolved. Ask the user which they want, then set it per resource:

```bash
uip solution deploy config set <config.json> <Ontology> conflictFixingAction Replace
```

Or keep the existing ontology and create a new one under another name:

```bash
uip solution deploy config set <config.json> <Ontology> conflictFixingAction RenameInSolution
uip solution deploy config set <config.json> <Ontology> name <NewName>
```

`Replace` keeps the existing ontology's id and replaces its artifacts. `RenameInSolution` creates a new ontology under the new name. In the solution's resource editor and in Studio Web, every ontology property is read only while authoring; only the `uipath-ontology` skill's `uip ont update --local` and `uip ont files` commands change them. In the deployment configuration a deployer can change `name`, `displayName` and `description`; `entities`, the attached file and `ontologyManifest` stay read only. The ontology service never offers `UseExisting`, `MergeConfiguration` or `RenameExisting` for an ontology: never set them, and never set an ontology's action with `--all`.

**Post-deploy check.** After `deploy run`, confirm the ontology landed with two read-only calls in the deployment folder:

```bash
uip ont get <ONTOLOGY_NAME> --folder-key <DEPLOY_FOLDER_KEY> --output json
uip df entities list --folder-key <DEPLOY_FOLDER_KEY> --output json
```

**Install errors**

- `TypeIncompatible` on an upgrade (`ReferenceEntity: existing=EntityAttachment`): an entity with a `FILE` field; see [local-entity-file-field.md](local-entity-file-field.md).
- `EntityConflict`: a changed field type was merged into a same-name entity in the target folder. Tell the user; never change a field type silently.
- `InstallError` naming an entity, column or choice set as "Missing in the target folder": the solution lacks it. Hand back to `uipath-ontology` to add it locally and pack, then redeploy; without that skill, tell the user which entity, column or choice set the solution lacks.
- `InstallError` for a rename onto a name another ontology holds in that folder: the new name is taken, and the previous version stays installed. Choose another name with `config set <config.json> <Ontology> name <NewName>`, then redeploy.

A federated entity's connection ships in the solution; its `NeedsSetupToActivate` after deploy is handled as in [pack-and-deploy.md Step 4](../pack-and-deploy.md#step-4-deploy-to-orchestrator).
