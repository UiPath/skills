---
name: uipath-ontology-modeler
description: "UiPath Ontology modeler (.ofn, SHACL .ttl, .yarrrml.yml, optional summary/context .json). Models a domain and builds the ontology and its local entities as a UiPath solution with the local (`--local`) `uip ont` and `uip df entities` commands, validates with the ontology service, then packs. Input: plain-language domain, existing artifact files to clone or rebuild, or an authoring handoff. For SDD/PDD/design documents→uipath-ontology-authoring. For publish/deploy/activate of the packed solution→uipath-solution. For Data Fabric entity or record work outside an ontology→uipath-platform."
when_to_use: "User describes classes, fields, and relationships and wants an ontology; supplies .ofn/.ttl/.yarrrml.yml files to clone or turn into a solution; or uipath-ontology-authoring delegates a confirmed handoff."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---


# UiPath Ontology Modeler

Builds an ontology as a **local UiPath solution**: one ontology resource plus the local Data Fabric entities, choice sets and federated entities it reads, all linked by name. The CLI keeps one zip per ontology; the skill never builds, reads or edits it. Nothing is created on the tenant before deploy.

## When to Use This Skill

- The user describes a domain (classes, fields, relationships, value lists) in plain language and wants an ontology.
- The user supplies `.ofn`, SHACL `.ttl` or `.yarrrml.yml` files to clone, rebuild or turn into a solution.
- `uipath-ontology-authoring` delegates a confirmed handoff.
- An SDD, PDD or design document → `uipath-ontology-authoring`. Publish or deploy of the packed solution → `uipath-solution`.

| Mode | Input | Stages |
|---|---|---|
| Standalone | Plain-language domain description | Stages 1–9 in order |
| Files | The user supplies the artifact files (clone or rebuild) | Copy the supplied files into `WORKDIR`, derive the entity definitions from the mapping (Stage 2), then Stages 3 and 4, then `artifacts check` on the supplied files (Stage 5), then Stages 6–9 |
| Delegated | Confirmed handoff from `uipath-ontology-authoring` | Stages 1–9 in order; Stage 2 starts from the confirmed handoff |
| Artifacts only | The user wants the artifact files, no solution | Stages 1, 2 and 5. The artifacts are written from the confirmed entity definitions; no solution and no entities (Stages 3–4 are skipped). Stops after Stage 5 |

In Files mode, copy only artifact files (`.ofn`, `.ttl`, `.yarrrml.yml`, `.json`), never symlinks or subfolders. When cloning, rename `{oldName}` to `{name}` in file names, IRIs and `PREFIX ont:` lines, and remove every Data Fabric id from the mapping (keep `table: <Entity>`).

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

## Critical Rules

1. **Every step runs through the `uip` CLI with `--output json`.** No scripts, REST or SDK calls; never write into `resources/files/` or the `.uipx` by hand.
2. **Entities, relationships and choice sets are authored locally with `uip df … --local`.** An entity is an entity project (`<Name>/project.uiproj` + `<Name>.entity`) with its resource at `resources/solution_folder/entity/native/<Name>.json`; federated: `entity/federated/<Name>.json`; choice set: `choiceSet/<Name>.json`. Nothing is created on the tenant before deploy.
3. **Every `uip df` create or update carries `--local`.** No tenant folder scope on any `uip df` command.
4. **Duplicate check before any create** (`uip df choice-sets list --local`, `uip df entities list --local`). Reuse a matching definition; when it differs, ask before changing it. Never a silent update.
5. **The only remote import is a federated entity's connection:** `uip solution resources add --source remote --kind Connection --name <CONNECTION> --folder-path "<CONNECTION_FOLDER>"`. No entity or choice-set import, re-import or refresh.
6. **`uip login status` runs first.** The connection import, a federated entity's create over a connector source and service validation need login; native entities, choice sets and a federated entity over local native sources only do not.
7. **A relationship is one `RELATIONSHIP` field on the referencing entity**; its inverse lives only in the schema (`InverseObjectProperties`). A federated target means a plain-column join. See [relationships-guide.md](references/relationships-guide.md).
8. **Choice sets are mapped by value name** (`xsd:string`, `sh:in`); `CHOICE_SET_MULTIPLE` gives one triple per value. See [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#choice-set-columns).
9. **No Data Fabric id or GUID** (entity, field, choice-set, value, connection or folder) in an artifact, the handoff, `WORKDIR` or a `--body`. Bodies reference entities and choice sets by name.
10. **An entity change is a local edit** (`uip df entities update <E> --local`), followed by validate.
11. **Validation needs `uip login`.** `uip ont validate --local` always calls the ontology service; stop if it can't be reached. `uip ont artifacts check` is the offline per-file check.
12. **Stop after pack.** The modeler ends with `uip solution pack` and `uip ont files list --package`; publish and deploy belong to `uipath-solution`.
13. **The handoff block is identical in this skill and `uipath-ontology-authoring`.**
14. **Ontology names are unique per folder.** Never rename the ontology resource while authoring; a new name means a new resource. Change its display name, description and entities only with `uip ont update --local`, and its files only with `uip ont files add|remove`.
15. **What the user gives is authoritative.** Ask before changing anything the user stated. Produce only schema, constraints, mapping and optional summary and context; no business rules, functions or actions.

## Paths

```text
ONTOLOGY_NAME  ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$   resource name, file prefix and IRI slug, verbatim
ONTOLOGY_IRI   https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR        <BASE_DIR>/<ONTOLOGY_NAME>/        artifacts at top level, plus input/
SOLUTION_DIR   <SOLUTION_PARENT>/<SOLUTION_NAME>/ absent (new) or holding exactly one .uipx
```

`WORKDIR` and `SOLUTION_DIR` are separate and absolute: neither is inside the other, and they are never the same path. When the user names the solution after the ontology under the same base directory, propose `<ONTOLOGY_NAME>-solution` as `SOLUTION_NAME` and confirm it. Write files only inside `WORKDIR`; change `SOLUTION_DIR` only through `uip` commands. Quote every path. File names, types and counts are in [artifacts-guide.md](references/artifacts-guide.md).

## Delegated handoff contract

Require one complete handoff and reject an incomplete one before writing files. `MAPPING_STATUS: supplied` means check and use the supplied mapping; `generate` means write it, and is invalid while a class-to-entity, field, join or identifier choice is ambiguous.

```text
ONTOLOGY_NAME: exact slug (unique per folder; the solution's own ontology is upgraded in place, a same-name ontology the solution does not own is a deploy conflict)
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
DISPLAY_NAME: optional; defaults to ONTOLOGY_NAME
DESCRIPTION: optional
WORKDIR: absolute path of the dedicated {name}/ artifact folder
SOLUTION_DIR: absolute path of the solution folder to create or update; entities and choice sets are authored there locally
CLASS_MAP: class -> entityName; names only, no ids
ENTITY_DEFINITIONS: entityName -> confirmed Data Fabric entity body, authored locally as is; names in place of ids (referenceEntityName, referenceFieldName default Id, choiceSetName)
CHOICE_SETS: choiceSetName -> [value names in order]
RELATIONSHIPS: [{ property, from, to, relationshipField, toColumn }] ([] when none); relationshipField is the RELATIONSHIP field on `from` (toColumn Id), or a plain column when `to` is federated
FEDERATED_SOURCES: entityName -> { sources: [ { connector: <connectorKey>, connectionName, object, fields } | { entityName, fields } ], joins: [ { source, relatedSource, sourceField, relatedField, sourceConnectionName, relatedConnectionName } ] } by name ({} when none); a join's sourceConnectionName/relatedConnectionName is the side's connectionName, or its entityName for a native source. A { entityName } source is a local entity in the same solution. fields entries are external field names or { source, name?, type?, direction?, searchable?, sortable?, requiredForRead? } (field options as in uipath-platform's federated entities). Each connectionName is imported into the solution with uip solution resources add --source remote --kind Connection --name <connectionName> --folder-path <CONNECTION_FOLDER>; no id is stored anywhere
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, constraints
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, grain, and class domains (groups): class -> domain label
```

Return:

```text
SOLUTION_DIR: absolute path of the packed solution folder
PACKAGE_PATH: absolute path of the packed solution zip
ONTOLOGY_NAME: the ontology resource name
ENTITIES: entityName -> native | federated, authored locally in the solution
CHOICE_SETS: choiceSetName -> [value names], authored locally in the solution
CONNECTIONS: connectionName -> folder it was imported from; each needs sign-in after deploy (NeedsSetupToActivate)
PACKED_FILES: fileName -> type, from uip ont files list --package
VALIDATION: Done, with any remaining WARNING
UNRESOLVED_AMBIGUITIES: [] or the open items
```

## Workflow

Entities come before artifacts: a federated entity's fields are known only after `create --local` reads the connector, and a name or type corrected at create must reach the mapping before it is written.

### Stage 1 — Sign in

```bash
uip login status --output json
```

When not logged in, ask the user to run `uip login` and wait. The connection import, a federated entity's `create --local` over a connector source (it reads the connection and the connector metadata) and service validation need it. Native entities, choice sets and a federated entity over local native sources only do not. Nothing is created on the tenant.

### Stage 2 — Model and confirm

Collect only what is missing: the domain or source files, any entity definitions the user has, `ONTOLOGY_NAME`, optional display name and description, the solution (new name or existing folder) and the base directory. Resolve every path to an absolute path and reject a name that fails the `ONTOLOGY_NAME` pattern, nested `WORKDIR` and `SOLUTION_DIR`, or a `WORKDIR` holding files you did not write. In Delegated mode, apply the same checks to the handoff and start from its confirmed model.

Show one reviewable model: classes with grain, entity name and domain (the business area the viewer groups the class under, 3–7 per ontology; see [owl-patterns-guide.md](references/owl-patterns-guide.md#domain-annotation)) (never `Order` or `Group`, which the CLI refuses: propose `SalesOrder`-style names, see [entity-guide.md](references/entity-guide.md)), data properties with xsd and field types ([entity-guide.md](references/entity-guide.md)), relationships ([relationships-guide.md](references/relationships-guide.md)), choice sets with their value names, federated sources and joins, and constraints. The confirmed model fixes the entity, field, relationship and choice-set names.

After confirmation, run `mkdir -p "<WORKDIR>/input/entities"` and write one entity definition per entity to `<WORKDIR>/input/entities/<Entity>.json` (Files mode derives them from the supplied mapping), with names in place of ids.

### Stage 3 — Init the solution and import connections

Artifacts-only mode skips Stages 3–4 (no solution, no entities) and goes to Stage 5.

<!--skill-flavor:solution-create:start-->
1. When `SOLUTION_DIR` does not exist yet, create the solution from its parent folder:
   ```bash
   cd "<SOLUTION_PARENT>" && uip solution init "<SOLUTION_NAME>" --output json
   ```
<!--skill-flavor:solution-create:end-->
2. For each `connectionName` in `FEDERATED_SOURCES`, find the folder that holds it (`uip is connections list --output json` lists candidates; ask when several match or the folder is unclear), then import it. This is the `uipath-solution` connection flow:
   ```bash
   uip solution resources add --source remote --kind Connection --name <CONNECTION> --folder-path "<CONNECTION_FOLDER>" --output json
   ```
3. Confirm with `uip solution resources list --kind Connection --source local --output json`.

### Stage 4 — Author entities locally

The `uip df` commands take no `--solution-folder`: prefix each with `cd "<SOLUTION_DIR>" &&`, since the shell's working directory may differ. Follow [entity-guide.md](references/entity-guide.md) for bodies and create order.

1. Duplicate check:
   ```bash
   uip df choice-sets list --local --output json
   uip df entities list --local --output json
   uip df choice-sets list-values <C> --local --output json
   ```
   Reuse a matching definition; ask before `update --local` when it differs.
2. Choice sets, then their values one by one, in order:
   ```bash
   uip df choice-sets create <C> --local --display-name "<DISPLAY_NAME>" --output json
   uip df choice-set-values create <C> <VALUE> --local --output json
   ```
3. Native entities in dependency order (a referenced entity first), previewing each schema before the create:
   ```bash
   uip df entities create <E> --local --body '<BODY>' --output json
   ```
4. Federated entities last, after their connections and native sources. Logged in when a source is a connector source; a federated entity over local native sources only needs no login:
   ```bash
   uip df entities create <F> --local --body '<FEDERATED_BODY>' --output json
   ```
5. Validate the entities: `uip df entities validate --local --output json`.

### Stage 5 — Write the artifacts against the created entities

Write the schema, constraints, mapping and optional summary and context into `WORKDIR` per [artifacts-guide.md](references/artifacts-guide.md), after one batch confirmation. The mapping uses the created entity and field names exactly (artifacts-only mode: the confirmed definitions from Stage 2); a federated entity's external fields are the ones `create --local` read from the connector.

Two annotations the ontology viewer reads, written in every ontology:

- **Groups:** the schema declares `Declaration(AnnotationProperty(:domain))` and gives every class one `AnnotationAssertion(:domain :<Class> "<Domain>")` from the confirmed domains ([owl-patterns-guide.md](references/owl-patterns-guide.md#domain-annotation)). Without it the viewer draws no groups.
- **Source icons:** each mapping block over a federated entity with a connector source adds `system: <CONNECTOR_KEY>` to its source block, the `connector` of that source in `FEDERATED_SOURCES` ([mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#source-system)). Without it the class shows the Data Fabric icon, not the connector's. Native entities get no `system:`.

Check each file (in Files mode, the supplied files):

```bash
uip ont artifacts check <FILE> --content-type <MIME> --type <T> --file "<PATH>" --output json
```

Fix every ERROR; show WARNINGs and fix them when the fix is mechanical. After 3 rounds on the same file with ERRORs left, stop and show them to the user. Artifacts-only mode stops here.

### Stage 6 — Create the ontology resource and add its files

```bash
uip ont create <Name> --local --entity <E1> --entity <E2> [--display-name "<DISPLAY_NAME>"] [--description "<DESCRIPTION>"] --solution-folder "<SOLUTION_DIR>" --output json
uip ont files add <Name> <FILES…> --local --solution-folder "<SOLUTION_DIR>" --output json
```

`files add` checks every file again; one ERROR attaches nothing. Re-adding a file name replaces it (`Replaced`). The cross-file rules (`XF-…`) run at validate.

### Stage 7 — Validate until clean

```bash
uip ont validate --local --solution-folder "<SOLUTION_DIR>" --output json
```

Clean means no ERROR and `ServiceValidation` is `"Done"`. Validation always calls the service; logged out it fails `ServiceValidationUnavailable`. A local ERROR skips the service call (`ServiceValidation` is `"Skipped"`). When the service fails or cannot validate, `Data` still holds the local results.

- An entity fix is a local edit: `uip df entities update <E> --local --body '<CHANGE>' --output json`, then validate. A federated entity: `uip df entities delete <F> --local --yes`, then create it again. A choice-set fix: `uip df choice-set-values create <C> <VALUE> --local --output json`.
- An artifact fix: edit the file in `WORKDIR`, `artifacts check`, `files add`, then validate.
- Stop after 5 validate rounds with ERRORs left, or 2 rounds that report the same ERROR unchanged. Show the remaining ERRORs and return them in `UNRESOLVED_AMBIGUITIES`; never pack.

### Stage 8 — Pack and confirm the contents

```bash
uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --dry-run --output json
uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --output json
uip ont files list <Name> --package "<PACKAGE_PATH>" --output json
```

Show the dry-run listing first. `PACKAGE_PATH` is the zip the real pack reports in `Data.Packages` (one path for this solution). The packed listing must equal the validated set; a mismatch means a file changed after validation (see the recovery table).

### Stage 9 — Stop after pack and hand off to `uipath-solution`

Return the block above. When the user asks to deploy, hand off to `uipath-solution` with:

- The ontology name, unique per folder. The solution's own ontology upgrades normally. A same-name ontology the solution does not own is a deploy conflict: the deployer chooses `Replace` or gives a new `name` in the deployment configuration (`RenameInSolution`). A rename onto a name another ontology holds fails the install (`InstallError`): choose another name.
- The entities and choice sets are created in the target folder at deploy from their local resources, or merged into a same-name entity there.
- The federated connections, each needing sign-in after deploy (`NeedsSetupToActivate`), unless the deployer links each one in the deployment configuration to an existing signed-in connection of the same connector.
- A solution already deployed is upgraded in place, never deployed again: see [Updating an existing solution](#updating-an-existing-solution).
- The post-deploy check in the deployment folder belongs to `uipath-solution`. The modeler runs nothing after this stage.

## Updating an existing solution

1. Read the current state: `uip ont get <Name> --local --solution-folder "<SOLUTION_DIR>"` and `uip df entities list --local`.
2. Change locally: `uip df entities create|update <E> --local --body '<BODY>'`, then `uip ont update <Name> --local --add-entity <E>` (or `--remove-entity`). Report, never delete, entities that are no longer linked.
3. `uip ont files add` for new or changed files; `uip ont files remove <Name> <FILE> --local` for dropped ones.
4. Validate (Stage 7), then pack (Stage 8) with a version above the deployed one: `uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --version <NEXT_VERSION> --output json`. Without `--version` the pack is `1.0.0` again, which the feed already holds.
5. Hand off to `uipath-solution` to publish the new version and upgrade the existing deployment in place (its *deploy upgrade* flow, by deployment name and `<NEXT_VERSION>`). The upgrade keeps the deployment's folder, its entity data and its resource links (a linked connection stays linked). A new `deploy run` would create a second folder instead.
6. A solution with a `FILE` field is rejected on every upgrade with `TypeIncompatible` (`ReferenceEntity: existing=EntityAttachment, incoming=(none)`). Nothing is installed and the attempt stays as a pending draft. Finish it per [upgrade-guide.md](references/upgrade-guide.md): `UseExisting` for that entity, the deployment's links again, then the same name and version.

## Errors

Act on each violation's `rule`, `file` and `suggestion` (`Rule`, `File`, `Suggestion` in a success envelope; lower case in a failure's `Data`); never re-implement a check. Per-file rules come from `artifacts check`, `files add` and `validate`; cross-file rules from `validate`. Error codes come in the `Code` of a failure envelope; `NAME_RESERVED` and the field-name rules of `uip df` come in its `Instructions`.

### Recovery table

| Signal | Source | Action |
|---|---|---|
| `OFN-001`, `OFN-002`, `OFN-004`, `OFN-005`, `OFN-009` | local | Fix `{name}.ofn` per [owl-patterns-guide.md](references/owl-patterns-guide.md); `artifacts check`, `files add`, validate |
| `SHC-002`, `SHC-003`, `SHC-004`, `SHC-006`, `SHC-007`, `SHC-008`, `SHC-009`, `SHC-010` | local | Fix the constraints file per [shacl-patterns-guide.md](references/shacl-patterns-guide.md); same loop |
| `MAP-002`, `MAP-004`, `MAP-005`, `MAP-006` | local | Fix the mapping per [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md); same loop |
| `CTX-001`, `CTX-002`, `CTX-003`, `CTX-005`, `CTX-006`, `CTX-007`, `SUM-001`, `SUM-002` | local | Fix the context or summary per [summary-context-guide.md](references/summary-context-guide.md), or drop it with `uip ont files remove`; same loop |
| `MAP-012` | local | Remove every Data Fabric id from the mapping; keep `table: <Entity>` |
| `XF-001` | local | Exactly one schema, one or more constraints, one mapping, at most one summary and one context; `files add` / `files remove` |
| `XF-002` | local | WARNING: re-run `uip ont files add` to rebuild the zip. ERROR: rebuild it with `files add` for every artifact |
| `XF-003`, `XF-004` | local | Use `https://ontology.uipath.com/<name>#` and `https://ontology.uipath.com/shapes#` for `shape:` |
| `XF-005` | local | Remove the construct outside OWL 2 QL; record the rule in `rdfs:comment` or SHACL |
| `XF-006`, `XF-008` | local | Declare the term in the schema, or fix the name in the mapping or constraints |
| `XF-007` | local | Add `rdfs:label` and `rdfs:comment` to every class and property |
| `XF-009` | local | Give the class a property and a mapping block over a local entity, or fold it into a comment |
| `XF-010` | local | Map every property; give every class a `sh:targetClass` shape |
| `XF-012`, `XF-013` | local | The entity is missing from the solution or the column isn't a field. Add the local entity (`uip df entities create <E> --local --body '<BODY>'`) and link it (`uip ont update <Name> --local --add-entity <E>`), or fix the name; when the field is genuinely missing, after confirmation `uip df entities update <E> --local --body '<CHANGE>'` adding it, then validate |
| `XF-014`, `XF-015` | local | Declare the object property or add the join per [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#joins) |
| `XF-017` | local | A relationship cycle among the ontology's entities. After confirmation, remove one RELATIONSHIP field of the loop locally (`uip df entities update <E> --local --body '<CHANGE>'` with `removeFields`), keep the inverse in the schema ([owl-patterns-guide.md](references/owl-patterns-guide.md#inverse-properties)), then validate |
| `XF-019` | local | Copy the choice-set value names exactly into `sh:in`; add a missing value with `uip df choice-set-values create <C> <VALUE> --local`, or author a missing choice set with `uip df choice-sets create <C> --local` and its values, then validate |
| `ZIP-001` | local | The zip exceeds the service limits. Split large constraint files or trim summary and context, then `uip ont files add` again |
| `SVC-001` | service | Every service finding is `SVC-001` on the named file. Fix the syntax it names; same loop |
| `ENTITY_ID_IGNORED` | service | An `SVC-001` WARNING naming it; same fix as `MAP-012` |
| `ValidationFailed` | CLI | The ERRORs are in `Data`; fix each per the rows above, then validate |
| `ServiceValidationUnavailable` | CLI | Service validation needs `uip login`; ask for it, then validate again; stop if the service stays unreachable |
| `ServiceValidationFailed` | CLI | The service could not validate; `Instructions` carries its answer (`Not Found` when the tenant has no validate endpoint) and `Data` the local results. Stop and tell the user; never pack as validated |
| `ArtifactCheckFailed` | CLI | The ERRORs are in `Data.violations`; nothing was attached. Fix them, then `files add` again |
| `ArtifactTypeUnresolved`, `InvalidArtifactFileName` | CLI | Rename the file to the `{name}-…` convention (`{name}-summary.json`, `{name}-context.json`) or pass `--type`; never name a file `ontology.json` |
| `ArtifactTypeAlreadyPresent` | CLI | Re-add under the existing file name, or `files remove` the old one first |
| `ArtifactTypeNotSupported` | CLI | Drop the file; only the five artifact types are supported |
| `ArtifactNotFound` | CLI | Check `uip ont files list <Name> --local` and use the listed name |
| `NoParentSolution` | CLI | `--solution-folder` holds no `.uipx`; fix `SOLUTION_DIR` or init the solution (Stage 3) |
| `OntologyNotFound` | CLI | Create the resource (Stage 6), or fix the name from `uip ont list --local` |
| `OntologyNameTaken` | CLI | The name is used in the solution: ask for another, or update the existing resource |
| `InvalidOntologyName` | CLI | Use a name matching the `ONTOLOGY_NAME` pattern |
| `EntityNotFound` | CLI | Author it locally with `uip df entities create <E> --local --body '<BODY>'` (Stage 4), or fix the name |
| `LocalFlagRequired` | CLI | Add `--local` |
| `LocalAndFolderKeyConflict`, `LocalAndPackageConflict` | CLI | Drop the flag that doesn't belong to the local flow |
| `InvalidFolderKey` | CLI | The local flow passes no folder key; drop it |
| `ConfirmationRequired` | CLI | `uip ont delete` needs `--yes`; ask the user first |
| `ResourceFileMissing`, `InvalidResourceArchive` | CLI | Rebuild the zip with `uip ont files add` for every artifact |
| `InvalidAttachedFile`, `FileAttachNotSupported`, `ResourceNotFound` | CLI | The attach was refused; read `Instructions`, fix the solution state, then `files add` again |
| `PackageNotFound`, `OntologyNotInPackage` | CLI | Pass the `PACKAGE_PATH` pack reported; if the ontology is missing, validate and pack again |
| `OntologyManifestNotWritten` | CLI | Re-run `uip ont files add`; if it repeats, stop and report the CLI version |
| `Ambiguous match`, `No remote resource found with key` | connection import | Pass `--folder-path "<CONNECTION_FOLDER>"` to the `--kind Connection` import, or `--cloud-key` from the listed candidates |
| `CONNECTION_NOT_FOUND`, or a federated connection missing from the solution | `uip df` | Import the connection (Stage 3), then create the federated entity again |
| `Not logged in` on a federated `uip df entities create … --local` | `uip df` | A connector source makes that create read the connection and the source object's fields from the tenant; ask for `uip login`, then retry. A federated entity over local native sources only never needs it |
| `NAME_RESERVED` (in `Instructions`) | `uip df` | The entity is named `Order` or `Group`. Propose a domain name (`SalesOrder`), confirm it, use it in the class map, every body and the mapping, then create it |
| `REFERENCE_TARGET_NOT_FOUND`, `CHOICE_SET_NOT_FOUND` | `uip df` | The create order is wrong or a name is misspelled: create the target entity or choice set first, then retry |
| `RELATIONSHIP_CYCLE` | `uip df` | The field would close a reference cycle. Keep the relationship on one side and express the inverse with `InverseObjectProperties` ([relationships-guide.md](references/relationships-guide.md)) |
| `RELATIONSHIP_TARGET_FEDERATED` | `uip df` | A federated entity can't be a `RELATIONSHIP` target: use a plain column joined to its key column |
| `FEDERATED_UPDATE_NOT_SUPPORTED` | `uip df` | After confirmation, `uip df entities delete <F> --local --yes`, then create it again with the changed body |
| `ENTITY_IN_USE`, `CHOICE_SET_IN_USE` | `uip df` | Another entity's field still references it: after confirmation, change that field first (`uip df entities update <E> --local`) |
| `CHOICE_SET_NAME_TAKEN`, `CHOICE_SET_VALUE_NAME_TAKEN`, `ENTITY_NAME_TAKEN`, "Entity '<E>' already exists" | `uip df` | The duplicate check was skipped: reuse the existing choice set, value or entity (names are unique regardless of case) |
| `INVALID_NAME` | `uip df` | The choice-set name breaks the naming rules or is a reserved keyword: pick a domain name per [entity-guide.md](references/entity-guide.md) |
| `INVALID_FEDERATED_SOURCE`, `INVALID_JOIN`, `UNSUPPORTED_SOURCE_COLUMN` | `uip df` | Fix the federated body: each source names an `entityName` or a `connectionName` + `object`, each join side names a source of this entity, and no source column is a relationship or choice-set field |
| `referenceEntityName` or `choiceSetName` unknown, or local choice sets or federated create unknown | `uip df` | The `uip` build cannot author these locally. Stop and ask for a newer CLI; never substitute `STRING` |
| `TypeIncompatible` (upgrade rejected, `Conflicts:`) | deploy, via `uipath-solution` | A `FILE` field's `EntityAttachment` reference. Entity otherwise unchanged: finish the draft per [upgrade-guide.md](references/upgrade-guide.md). Entity really changed: tell the user; never drop the field |
| `EntityConflict` | deploy, via `uipath-solution` | A changed field type met a same-name entity in the target folder. Tell the user; never change a field type silently |
| `InstallError` "Missing in the target folder" | deploy, via `uipath-solution` | The entity, column or choice set is not in the solution. Add it locally (`uip df entities create|update <E> --local`), validate, pack, and redeploy through `uipath-solution` |
| `InstallError` "a rename onto a name another ontology holds in that folder" | deploy, via `uipath-solution` | The name set in the deployment configuration is taken in the target folder; the previous version stays installed. Choose another name in the deployment configuration and redeploy through `uipath-solution` |
| Packed listing differs from the validated set | `files list --package` | `files add` again, validate, pack |
| `BLOCKED_AMBIGUITY` | skill | A class-to-entity, join or identifier has no unique answer: stop and ask |

## Reference Navigation

| Need | Read |
|---|---|
| Artifact files, types, counts, write order | [artifacts-guide.md](references/artifacts-guide.md) |
| Entity bodies, field types, reserved names, choice sets, federated bodies, create order | [entity-guide.md](references/entity-guide.md) |
| Which entity holds a relationship, inverses, cycles, federated targets, many-to-many | [relationships-guide.md](references/relationships-guide.md) |
| `{name}.ofn` schema patterns and OWL 2 QL limits | [owl-patterns-guide.md](references/owl-patterns-guide.md) |
| SHACL constraint shapes | [shacl-patterns-guide.md](references/shacl-patterns-guide.md) |
| YARRRML mapping, joins, typed literals, USAGE POLICY | [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md) |
| Optional summary and context files | [summary-context-guide.md](references/summary-context-guide.md) |

## Anti-patterns

- Writing into `resources/files/`, the `.uipx` or the ontology zip by hand (Critical Rule 1).
- A `uip df` command without `--local`, or importing an entity or choice set from the tenant (Critical Rules 3 and 5).
- Writing artifacts before the entities exist: a federated entity's fields are known only after its create (Stage 5).
- A second `RELATIONSHIP` field for an inverse (Critical Rule 7).
- A data property mapped without its xsd range when the range is not `xsd:string` ([mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#property-object-pairs-po)).
- Packing after `ServiceValidationFailed`, or reporting the solution as validated when `ServiceValidation` is not `"Done"`.
- Publishing or deploying: hand off to `uipath-solution` (Critical Rule 12).
