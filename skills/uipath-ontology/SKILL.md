---
name: uipath-ontology
description: "UiPath Ontology (.ofn, .yarrrml.yml, optional summary/context .json and SHACL .ttl). Always invoke to build or update an ontology, even from an SDD or PDD. Models a domain and builds the ontology and its local entities as a UiPath solution with the local (`--local`) `uip ont` and `uip df entities` commands, validates with the ontology service, then packs; also reads a deployed ontology (`uip ont get|list --folder-path`). Input: an SDD, PDD or design document, a plain-language domain, or existing artifact files to clone or rebuild. For publish/deploy/activate of the packed solution→uipath-solution. For PDD→automation SDD design→uipath-planner. For Data Fabric entity or record work outside an ontology→uipath-platform."
when_to_use: "User provides an SDD, PDD or design/domain specification and wants an ontology from it; describes classes, fields, and relationships and wants an ontology; or supplies .ofn/.ttl/.yarrrml.yml files to clone or turn into a solution. Also: 'list the ontologies in folder X', 'show the deployed ontology Y'."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---


# UiPath Ontology

Builds an ontology as a **local UiPath solution**: one ontology resource plus the local Data Fabric entities, choice sets and federated entities it reads, all linked by name. The CLI keeps one zip per ontology; the skill never builds, reads or edits it. Nothing is created on the tenant before deploy.

## When to Use This Skill

- The user supplies an SDD, PDD, design document or domain specification and wants an ontology built from it.
- The user describes a domain (classes, fields, relationships, value lists) in plain language and wants an ontology.
- The user supplies `.ofn`, SHACL `.ttl` or `.yarrrml.yml` files to clone, rebuild or turn into a solution.
- Publish or deploy of the packed solution → `uipath-solution`.

| Mode | Input | Stages |
|---|---|---|
| Document | An SDD, PDD, design document or domain specification (file, Confluence URL or pasted text) | Stages 1–9 in order; Stage 2 confirms the model one table at a time per [document-guide.md](references/document-guide.md) |
| Standalone | Plain-language domain description | Stages 1–9 in order |
| Files | The user supplies the artifact files (clone or rebuild) | Copy the supplied files into `WORKDIR`, derive the entity definitions from the mapping (Stage 2), then Stages 3 and 4, then `artifacts check` on the supplied files (Stage 5), then Stages 6–9 |
| Artifacts only | The user wants the artifact files, no solution. The input may be a document, a description or files; a document is confirmed table by table as in Document mode | Stages 1, 2 and 5. The artifacts are written from the confirmed entity definitions; no solution and no entities (Stages 3–4 are skipped). Stops after Stage 5 |

In Files mode, copy only artifact files (`.ofn`, `.ttl`, `.yarrrml.yml`, `.json`), never symlinks or subfolders. When cloning, rename `{oldName}` to `{name}` in file names, IRIs and `PREFIX ont:` lines, and remove every Data Fabric id from the mapping (keep `table: <Entity>`).

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

## Critical Rules

1. **Every step runs through the `uip` CLI with `--output json`.** No scripts, REST or SDK calls; never write into `resources/files/` or the `.uipx` by hand.
2. **Entities, relationships and choice sets are authored locally with `uip df … --local`.** An entity is an entity project (`<Name>/project.uiproj` + `<Name>.entity`) with its resource at `resources/solution_folder/entity/native/<Name>.json`; federated: `entity/federated/<Name>.json`; choice set: `choiceSet/<Name>.json`. Nothing is created on the tenant before deploy.
3. **Every `uip df` create or update carries `--local`.** No tenant folder scope on any `uip df` command.
4. **Duplicate check before any create** (`uip df choice-sets list --local`, `uip df entities list --local`). Reuse a matching definition; when it differs, ask before changing it. Never a silent update.
5. **The only remote import is a federated entity's connection:** `uip solution resources add --source remote --kind Connection --name <CONNECTION> --folder-path "<CONNECTION_FOLDER>"`. No entity or choice-set import, re-import or refresh.
6. **`uip ont --help` runs first in every mode. `uip login status` runs next, except in Artifacts-only mode** (offline; see Stage 1). Being logged out never blocks Stage 2: the model is confirmed and saved without a tenant, and login is asked for before Stage 3. The connection import, a federated entity's create over a connector source and service validation need login; native entities, choice sets and a federated entity over local native sources only do not.
7. **A relationship is one `RELATIONSHIP` field on the referencing entity**; its inverse lives only in the schema (`InverseObjectProperties`). A federated target means a plain-column join. See [relationships-guide.md](references/relationships-guide.md).
8. **Choice sets are mapped by value name** (`xsd:string`; the schema comment lists the values, each in single quotes: `Values of choice set <C>: 'A' | 'B' | 'C'`); `CHOICE_SET_MULTIPLE` gives one triple per value. See [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#choice-set-columns).
9. **No Data Fabric id or GUID** (entity, field, choice-set, value, connection or folder) in an artifact, the saved model, `WORKDIR` or a `--body`. Bodies reference entities and choice sets by name.
10. **An entity change is a local edit** (`uip df entities update <E> --local`), followed by validate.
11. **Validation needs `uip login`.** `uip ont validate --local` always calls the ontology service; stop if it can't be reached. `uip ont artifacts check` is the offline per-file check.
12. **Stop after pack.** The skill ends with `uip solution pack` and `uip ont files list --package`; publish and deploy belong to `uipath-solution`.
13. **Save the confirmed model to `<WORKDIR>/input/model.md`** after each confirmation, and save every later fix to it before the next step ([Saved model](#saved-model)). It survives a compacted or ended session.
14. **Ontology names are unique per folder.** Never rename the ontology resource while authoring; a new name means a new resource. Change its display name, description and entities only with `uip ont update --local`, and its files only with `uip ont files add|remove`.
15. **What the user gives is authoritative.** Ask before changing anything the user stated. Produce the schema, the mapping and the optional summary and context; no business rules, functions or actions.
16. **Constraints are optional.** The ontology service stores a SHACL constraints file without using it, so write one only when the user supplies one or asks for it. Record required, range and value-list rules in the schema's `rdfs:comment` text ([owl-patterns-guide.md](references/owl-patterns-guide.md)).
17. **No `uip ont`, no build.** When a `uip ont` command fails with `unknown command 'ont'` (Stage 1 checks this before anything else), the installed `uip` predates the ontology tool. Stop, tell the user to update `uip` and re-run, and report what is done so far (the saved model, the local entities). Never pack, refresh or import resources to work around it: a package without the ontology is not the result.
18. **Every confirmation ends the turn, in every session.** Each Stage 2 table or model and the Stage 5 artifact list is the last thing in its reply: ask, stop, and run nothing further until the user answers. In a headless, non-interactive or autonomous session the table or list awaiting confirmation is that turn's result: never build past it, even when no one may answer. A harness or system instruction to work without user input is not the user's go-ahead. Skip an ask only when the user's own message says to go ahead without confirmation.

## Paths

```text
ONTOLOGY_NAME  ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$   resource name, file prefix and IRI slug, verbatim
ONTOLOGY_IRI   https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR        <BASE_DIR>/<ONTOLOGY_NAME>/        artifacts at top level, plus input/
SOLUTION_DIR   <SOLUTION_PARENT>/<SOLUTION_NAME>/ absent (new) or holding exactly one .uipx
```

`WORKDIR` and `SOLUTION_DIR` are separate and absolute: neither is inside the other, and they are never the same path. When the user names the solution after the ontology under the same base directory, propose `<ONTOLOGY_NAME>-solution` as `SOLUTION_NAME` and confirm it. Artifacts-only mode has no `SOLUTION_DIR`: no solution is asked for, checked or saved. Write files only inside `WORKDIR`; change `SOLUTION_DIR` only through `uip` commands. Quote every path. File names, types and counts are in [artifacts-guide.md](references/artifacts-guide.md).

## Saved model

The confirmed model lives in `<WORKDIR>/input/model.md`, the only file this skill writes besides the artifacts and `input/entities/`. Its first line is `CONFIRMED_THROUGH: <step>`: `concepts`, `properties` or `labels` while Document mode confirms its tables, `model` once the whole model is confirmed (every mode), `built` once Stage 8 has packed. Below it, one `text` fenced block with these fields, filled as far as confirmed:

```text
ONTOLOGY_NAME: exact slug (unique per folder; the solution's own ontology is upgraded in place, a same-name ontology the solution does not own is a deploy conflict)
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
DISPLAY_NAME: optional; defaults to ONTOLOGY_NAME
DESCRIPTION: optional
WORKDIR: absolute path of the dedicated {name}/ artifact folder
SOLUTION_DIR: absolute path of the solution folder to create or update; entities and choice sets are authored there locally. Absent in Artifacts-only mode
CLASS_MAP: class -> entityName; names only, no ids
ENTITY_DEFINITIONS: entityName -> confirmed Data Fabric entity body, authored locally as is; names in place of ids (referenceEntityName, referenceFieldName default Id, choiceSetName)
CHOICE_SETS: choiceSetName -> [value names in order]
RELATIONSHIPS: [{ property, from, to, relationshipField, toColumn }] ([] when none); relationshipField is the RELATIONSHIP field on `from` (toColumn Id), or a plain column when `to` is federated
FEDERATED_SOURCES: entityName -> { sources: [ { connector: <connectorKey>, connectionName, object, fields } | { entityName, fields } ], joins: [ { source, relatedSource, sourceField, relatedField, sourceConnectionName, relatedConnectionName } ] } by name ({} when none); a join's sourceConnectionName/relatedConnectionName is the side's connectionName, or its entityName for a native source. A { entityName } source is a local entity in the same solution. fields entries are external field names or { source, name?, type?, direction?, searchable?, sortable?, requiredForRead? } (field options as in uipath-platform's federated entities). Each connectionName is imported into the solution with uip solution resources add --source remote --kind Connection --name <connectionName> --folder-path <CONNECTION_FOLDER>; no id is stored anywhere
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, constraints
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, grain, and class domains (groups): class -> domain label
```

`MAPPING_STATUS: supplied` means check and use the supplied mapping (Files mode); `generate` means write it, and is invalid while a class-to-entity, field, join or identifier choice is ambiguous.

**Every change goes into the file first.** A fix after a failed step (a renamed entity after `NAME_RESERVED`, a class folded into a property after `XF-009`, a user's correction) is saved to `model.md` before the next command, so a retry or a new session starts from it.

**Update, not resume.** When `model.md` reads `CONFIRMED_THROUGH: built` and the user asks to change that ontology, follow [Updating an existing solution](#updating-an-existing-solution); do not offer to resume or start over.

**Resume.** When `WORKDIR` already holds `input/model.md` short of `built`, the folder is this skill's own earlier work. Show its `CONFIRMED_THROUGH` step and the confirmed tables, and ask whether to continue or start over; overwrite it only when the user starts over. A `model.md` with no `SOLUTION_DIR` is Artifacts-only: continuing after `model` re-runs Stage 5 only. Otherwise continuing after `model` re-runs Stages 3–9: an existing `SOLUTION_DIR` is not created again, the duplicate check (Critical Rule 4) reuses the entities and choice sets already authored, and an ontology the solution already has (`uip ont get <Name> --local`) is not created again: `files add` replaces its files. A `WORKDIR` holding files but no `input/model.md` was not written by this skill: ask for another folder.

## Report

At the end, report:

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

Artifacts-only mode has no solution or package; report instead:

```text
WORKDIR: absolute path of the artifact folder
FILES: fileName -> type, with its `uip ont artifacts check` result (clean, or the WARNINGs left)
NOT_CHECKED: the cross-file (`XF-…`) and service checks; they run at `uip ont validate --local` once the files are built into a solution (Files mode)
UNRESOLVED_AMBIGUITIES: [] or the open items
```

## Workflow

Entities come before artifacts: a federated entity's fields are known only after `create --local` reads the connector, and a name or type corrected at create must reach the mapping before it is written.

### Stage 1 — Check the CLI and sign in

In every mode, first check that the installed `uip` has the ontology tool:

```bash
uip ont --help
```

When it fails with `unknown command 'ont'`, stop before asking anything (Critical Rule 17): tell the user to update `uip` and re-run.

```bash
uip login status --output json
```

Artifacts-only mode skips the login check: `artifacts check` is offline. In every other mode, when not logged in, say so and go on to Stage 2: confirming and saving the model needs no tenant. Before Stage 3, ask the user to run `uip login` and wait. The connection import, a federated entity's `create --local` over a connector source (it reads the connection and the connector metadata) and service validation need it. Native entities, choice sets and a federated entity over local native sources only do not. Nothing is created on the tenant.

### Stage 2 — Model and confirm

Collect only what is missing: the document, domain or source files, any entity definitions the user has, `ONTOLOGY_NAME`, optional display name and description, the solution (new name or existing folder; not in Artifacts-only mode) and the base directory. Resolve every path to an absolute path and reject a name that fails the `ONTOLOGY_NAME` pattern, or nested `WORKDIR` and `SOLUTION_DIR`. A `WORKDIR` that already holds `input/model.md` is resumed ([Saved model](#saved-model)); one holding other files is refused.

In Document mode, read the document and confirm the model in three tables per [document-guide.md](references/document-guide.md), saving `model.md` after each (run `mkdir -p "<WORKDIR>/input"` before the first save). In the other modes, show one reviewable model: classes with grain, entity name and domain (the business area the viewer groups the class under, 3–7 per ontology; see [owl-patterns-guide.md](references/owl-patterns-guide.md#domain-annotation)) (never `Order` or `Group`, which the CLI refuses: propose `SalesOrder`-style names, see [entity-guide.md](references/entity-guide.md)), data properties with xsd and field types ([entity-guide.md](references/entity-guide.md)), relationships ([relationships-guide.md](references/relationships-guide.md)), choice sets with their value names, federated sources and joins, and constraints. The confirmed model fixes the entity, field, relationship and choice-set names. In every mode, when the model has a `FILE` field, tell the user before they confirm that later upgrades keep that entity as installed, so fields added to or changed on it are not applied ([entity-guide.md](references/entity-guide.md#xsd-to-data-fabric-type)).

After confirmation, run `mkdir -p "<WORKDIR>/input/entities"`, save `model.md` with `CONFIRMED_THROUGH: model`, and write one entity definition per entity to `<WORKDIR>/input/entities/<Entity>.json` (Files mode derives them from the supplied mapping), with names in place of ids. Stage 4 creates each entity from its file, so write every file.

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
3. Native entities in dependency order (a referenced entity first), previewing each schema before the create. In Document mode the confirmed tables are the preview: create without one. Each body is read from its Stage 2 file: when `<WORKDIR>/input/entities/<E>.json` is missing, write it first, and never pass a native entity's body inline. When a create changes a confirmed name or type (`NAME_RESERVED`, a refused type), ask, then save the change to `model.md` and to that file:
   ```bash
   cd "<SOLUTION_DIR>" && uip df entities create <E> --local --body "$(cat "<WORKDIR>/input/entities/<E>.json")" --output json
   ```
4. Federated entities last, after their connections and native sources. Logged in when a source is a connector source; a federated entity over local native sources only needs no login:
   ```bash
   uip df entities create <F> --local --body '<FEDERATED_BODY>' --output json
   ```
5. Validate the entities: `uip df entities validate --local --output json`.

### Stage 5 — Write the artifacts against the created entities

Before writing anything, list the artifact files (name and type, one line each) and ask the user to confirm them as one batch; wait for the reply. Confirming the model in Stage 2 does not count, and neither does a "go ahead and build" given in reply to a Stage 2 table: that approves the table. Never fold this ask into a Stage 2 question ("confirm these and I'll build"). Skip the ask only when the user already said to go ahead without further confirmation. When the user says stop, stop: `model.md` stays at `model`. Then write the schema, mapping and optional summary and context (constraints only per Critical Rule 16) into `WORKDIR` per [artifacts-guide.md](references/artifacts-guide.md). The mapping uses the created entity and field names exactly (artifacts-only mode: the confirmed definitions from Stage 2); a federated entity's external fields are the ones `create --local` read from the connector.

Two annotations the ontology viewer reads, written in every ontology:

- **Groups:** the schema declares `Declaration(AnnotationProperty(:domain))` and gives every class one `AnnotationAssertion(:domain :<Class> "<Domain>")` from the confirmed domains ([owl-patterns-guide.md](references/owl-patterns-guide.md#domain-annotation)). Without it the viewer draws no groups.
- **Source icons:** each mapping block over a federated entity with a connector source adds `system: <CONNECTOR_KEY>` to its source block, the `connector` of that source in `FEDERATED_SOURCES` ([mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#source-system)). Without it the class shows the Data Fabric icon, not the connector's. Native entities get no `system:`.

Check each file (in Files mode, the supplied files):

```bash
uip ont artifacts check "<PATH>" --output json
```

The file name decides the type, the same way `files add` decides it. Pass `--type summary` or `--type context` only for a `.json` name that ends in neither `-summary` nor `-context`.

Fix every ERROR; show WARNINGs and fix them when the fix is mechanical. In a constraints file, `SHC-006` on a `CHOICE_SET_MULTIPLE` property is expected: never add `sh:maxCount 1` to it ([shacl-patterns-guide.md](references/shacl-patterns-guide.md#every-property-block-carries-shname-and-shmaxcount)). After 3 rounds on the same file with ERRORs left, stop and show them to the user. Artifacts-only mode stops here: tell the user that only the per-file check ran, and that the cross-file and service checks run only when the files are built into a solution (Files mode). Give the Artifacts-only [Report](#report).

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

Clean means no ERROR and `ServiceValidation` is `"Done"`. Validation always calls the service; logged out it fails `ServiceValidationUnavailable`. A local ERROR skips the service call (`serviceValidation` is `"Skipped"` in the failure's `Data`). When the service fails or cannot validate, `Data` still holds the local results.

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

Save `model.md` with `CONFIRMED_THROUGH: built` and give the [Report](#report). When the user asks to deploy, hand off to `uipath-solution` with:

- The ontology name, unique per folder. The solution's own ontology upgrades normally. A same-name ontology the solution does not own is a deploy conflict: the deployer chooses `Replace` or gives a new `name` in the deployment configuration (`RenameInSolution`). A rename onto a name another ontology holds fails the install (`InstallError`): choose another name.
- The entities and choice sets are created in the target folder at deploy from their local resources, or merged into a same-name entity there. Tell the user to check the target folder for same-name entities before deploying: a changed field type there is reported as `EntityConflict`.
- The federated connections, each needing sign-in after deploy (`NeedsSetupToActivate`), unless the deployer links each one in the deployment configuration to an existing signed-in connection of the same connector.
- A solution already deployed is upgraded in place, never deployed again: see [Updating an existing solution](#updating-an-existing-solution).
- The post-deploy check in the deployment folder belongs to `uipath-solution`. The skill runs nothing after this stage.

## Updating an existing solution

The saved model is the record of what was built. When `<WORKDIR>/input/model.md` exists, read it with the current state, save each change to it before running that change, and set `CONFIRMED_THROUGH: built` again after the pack. When it does not exist (a solution built elsewhere), write it from the current state before the first change.

1. Read the current state:
   ```bash
   uip ont get <Name> --local --solution-folder "<SOLUTION_DIR>" --output json
   cd "<SOLUTION_DIR>" && uip df entities list --local --output json
   ```
2. Change locally, then link or unlink the entity. Report, never delete, entities that are no longer linked.
   ```bash
   cd "<SOLUTION_DIR>" && uip df entities create <E> --local --body '<BODY>' --output json   # or: entities update <E>
   uip ont update <Name> --local --add-entity <E> --solution-folder "<SOLUTION_DIR>" --output json   # or: --remove-entity <E>
   ```
3. Attach new or changed files, and remove dropped ones:
   ```bash
   uip ont files add <Name> <FILES…> --local --solution-folder "<SOLUTION_DIR>" --output json
   uip ont files remove <Name> <FILE> --local --solution-folder "<SOLUTION_DIR>" --output json
   ```
4. Validate (Stage 7), then pack (Stage 8) with a version above the deployed one: `uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --version <NEXT_VERSION> --output json`. Without `--version` the pack is `1.0.0` again, which the feed already holds.
5. Hand off to `uipath-solution` to publish the new version and upgrade the existing deployment in place (its *deploy upgrade* flow, by deployment name and `<NEXT_VERSION>`). The upgrade keeps the deployment's folder, its entity data and its resource links (a linked connection stays linked). A new `deploy run` would create a second folder instead.
6. A solution whose entity has a `FILE` field is rejected on every upgrade with `TypeIncompatible`. Tell `uipath-solution` when handing off; its local-entity `FILE`-field scenario finishes the upgrade.

## Errors

Act on each violation's `rule`, `file` and `suggestion` (`Rule`, `File`, `Suggestion` in a success envelope; lower case in a failure's `Data`); never re-implement a check. The full recovery table, one row per rule and error code, is in [errors-guide.md](references/errors-guide.md). The most common:

| Signal | Action |
|---|---|
| `ValidationFailed`, `ArtifactCheckFailed` | The ERRORs are in `Data` (`Data.violations`); fix each per [errors-guide.md](references/errors-guide.md), then `files add` and validate |
| `ServiceValidationUnavailable` | Ask for `uip login`, then validate again; stop if the service stays unreachable |
| `ServiceValidationFailed` | Stop and tell the user; never pack as validated |
| `XF-012`, `XF-013` | Entity missing from the solution or column not a field: author or fix the local entity, link it with `uip ont update --add-entity`, validate |
| `XF-017`, `RELATIONSHIP_CYCLE` | Keep one `RELATIONSHIP` field per relationship; the inverse lives in the schema only |
| `XF-019` | Copy the choice-set value names exactly into `sh:in`, or add the missing value locally |
| `NAME_RESERVED` (in `Instructions`) | Rename the entity (`SalesOrder`, not `Order`), confirm, and use the name everywhere |
| `BLOCKED_AMBIGUITY` | A class-to-entity, join or identifier has no unique answer: stop and ask |
| `unknown command 'ont'` | The installed `uip` has no ontology tool: stop and ask the user to update `uip` (Critical Rule 17); never pack without the ontology |

## Inspecting a deployed ontology

Read-only, logged in. Pass the deployment folder as exactly one of `--folder-path` or `--folder-key`, never with `--local`:

```bash
uip ont list --folder-path "<FOLDER_PATH>" --output json
uip ont get <Name> --folder-path "<FOLDER_PATH>" --output json
```

`list` takes `--limit` and `--offset` and then reports `Pagination`. A deployed ontology is changed only by changing its solution locally (§ Updating an existing solution) and upgrading through `uipath-solution`; never edit it on the tenant.

## Reference Navigation

| Need | Read |
|---|---|
| Modeling from an SDD, PDD or design document: the three confirmation tables and how document phrases map to the model | [document-guide.md](references/document-guide.md) |
| Artifact files, types, counts, write order | [artifacts-guide.md](references/artifacts-guide.md) |
| Entity bodies, field types, reserved names, choice sets, federated bodies, create order | [entity-guide.md](references/entity-guide.md) |
| Which entity holds a relationship, inverses, cycles, federated targets, many-to-many | [relationships-guide.md](references/relationships-guide.md) |
| `{name}.ofn` schema patterns and OWL 2 QL limits | [owl-patterns-guide.md](references/owl-patterns-guide.md) |
| SHACL constraint shapes, only when the user supplies or asks for constraints | [shacl-patterns-guide.md](references/shacl-patterns-guide.md) |
| YARRRML mapping, joins, typed literals, USAGE POLICY | [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md) |
| Optional summary and context files | [summary-context-guide.md](references/summary-context-guide.md) |
| Every rule and error code, and its recovery | [errors-guide.md](references/errors-guide.md) |

## Anti-patterns

- Writing into `resources/files/`, the `.uipx` or the ontology zip by hand (Critical Rule 1).
- A `uip df` command without `--local`, or importing an entity or choice set from the tenant (Critical Rules 3 and 5).
- Writing artifacts before the entities exist: a federated entity's fields are known only after its create (Stage 5).
- A second `RELATIONSHIP` field for an inverse (Critical Rule 7).
- A data property mapped without its xsd range when the range is not `xsd:string` ([mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md#property-object-pairs-po)).
- Packing after `ServiceValidationFailed`, or reporting the solution as validated when `ServiceValidation` is not `"Done"`.
- Publishing or deploying: hand off to `uipath-solution` (Critical Rule 12).
- Building straight through because the session is headless or non-interactive: each confirmation still ends the turn (Critical Rule 18).
