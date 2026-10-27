---
name: uipath-ontology-modeler
description: "UiPath Ontology modeler (.ofn, SHACL .ttl, .yarrrml.yml, optional summary/context .json). Models a domain and builds the ontology and its local entities as a UiPath solution with the local (`--local`) `uip ont` and `uip df entities` commands, validates with the ontology service, then packs. Input: plain-language domain, existing artifact files to clone or rebuild, or an authoring handoff. For SDD/PDD/design documents→uipath-ontology-authoring. For publish/deploy/activate of the packed solution→uipath-solution."
when_to_use: "User describes classes, fields, and relationships and wants an ontology; supplies .ofn/.ttl/.yarrrml.yml files to clone or turn into a solution; or uipath-ontology-authoring delegates a confirmed handoff."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# UiPath Ontology Modeler

Builds an ontology as a **local UiPath solution**: one ontology resource, plus one local Data Fabric entity per class, linked by name. The CLI keeps one zip per ontology (`ontology.json` and the artifacts at its root, with an empty `operations/` folder). The skill never builds, reads or edits that zip. Nothing is created in a tenant before deploy.

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

| Mode | Input | Start at |
|---|---|---|
| Standalone | Plain-language domain description | Step 1 |
| Files | Existing artifact files (clone or rebuild) | Step 1, then "Files mode" |
| Delegated | Confirmed handoff from `uipath-ontology-authoring` | Step 3 |

## Critical Rules

1. **Every step runs through the `uip` CLI with `--output json`.** No scripts, no REST, no SDK calls, no hand-made zip. Never write into `ResourceFiles/` or the `.uipx` by hand.
2. **Always validate with the ontology service.** Be logged in. Never skip service validation or validate offline. If the service can't be reached, stop and tell the user.
3. **Entities are local and referenced by name.** Author them as local Data Fabric entities (Step 4). Never read the tenant for entities. Never write `entityId` or `folderId`.
4. **What the user gives is authoritative.** Use a supplied entity body as is. Ask before changing anything the user stated.
5. **Field types are only the nine local types** (see [entity-format-guide.md](references/entity-format-guide.md)). No relationship or choice-set fields in M1.
6. **Produce only the five artifact types:** schema, constraints, mapping, and optionally summary (JSON) and context. No business rules, functions or actions; business constraints go to SHACL.
7. **The ontology name must be unique in the tenant.** Tell the user. The CLI can't check it offline. Service validation warns with `SVC-002` when the name is taken, and at deploy `uipath-solution` resolves a conflict by renaming (`RenameInSolution`).
8. **Stop after pack.** Publish, deploy and activate belong to `uipath-solution`. Then confirm the result in the deployment folder.

## Paths and artifacts

```text
ONTOLOGY_NAME  ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$   (IRI slug and file prefix; unique in the tenant)
ONTOLOGY_IRI   https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR        <BASE_DIR>/<ONTOLOGY_NAME>/        artifacts at top level, plus input/
SOLUTION_DIR   <SOLUTION_PARENT>/<SOLUTION_NAME>/ absent (new) or containing exactly one .uipx (existing)
```

The resource name `<Name>` and the file prefix and IRI slug `<name>` are the same `ONTOLOGY_NAME`, written verbatim (same case).

`WORKDIR` and `SOLUTION_DIR` are absolute and separate (neither inside the other). Write artifacts only inside `WORKDIR`; change `SOLUTION_DIR` only through `uip` commands. Quote every path.

| File in `WORKDIR` | `--type` | Media type | Count |
|---|---|---|---|
| `{name}.ofn` — OWL 2 QL schema | `schema` | `text/owl-functional` | exactly 1 |
| `{name}-constraints[-{area}].ttl` — SHACL | `constraints` | `text/turtle` | 1 or more |
| `{name}-mapping.yarrrml.yml` — YARRRML, `table:` = entity name | `mapping` | `application/yaml` | exactly 1 |
| `{name}-summary.json` | `summary` | `application/json` | 0 or 1 |
| `{name}-context.json` — JSON-LD `@context` | `context` | `application/json` | 0 or 1 |
| `input/handoff.json` — the confirmed model (not packed) | — | — | 1 |
| `input/entities/{EntityName}.json` — the entity's update body (`addFields`) | — | — | 1 per class |

`{name}` is `ONTOLOGY_NAME`. Summary and context are covered in [summary-context-guide.md](references/summary-context-guide.md).

## Delegated handoff contract

When called by ontology authoring, require one complete handoff. Do not rediscover or mutate its setup:

```text
ONTOLOGY_NAME: exact slug (unique in the tenant; a conflict is resolved by renaming at deploy)
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
DISPLAY_NAME: optional; defaults to ONTOLOGY_NAME
DESCRIPTION: optional
WORKDIR: absolute path of the dedicated {name}/ artifact folder
SOLUTION_DIR: absolute path of the solution folder to create or update
CLASS_MAP: class -> entityName; no IDs
ENTITY_SOURCE: entityName -> described | supplied | generated
ENTITY_DEFINITIONS: entityName -> local entity body (local types only); supplied bodies verbatim
RELATIONSHIPS: [{ property, from, to, fromColumn, toColumn }] ([] when none)
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, constraints
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, and grain
```

Reject an incomplete handoff before writing files. `MAPPING_STATUS: supplied` means check and use the provided mapping; `generate` means write it from the handoff, and is invalid when a class-to-entity, field, join column or identifier choice is ambiguous.

Return:

```text
SOLUTION_DIR: absolute path
PACKAGE_PATH: absolute path of the packed .zip
ONTOLOGY_NAME: the ontology resource name (the deployed name can differ after RenameInSolution)
ENTITIES: entity names in the solution, with ENTITY_SOURCE
PACKED_FILES: the files list --package listing
VALIDATION: last entities validate and ontology validate results (service validation ran)
UNRESOLVED_AMBIGUITIES: none | numbered list with the missing decision
```

## Design rules

| Information | Artifact |
|---|---|
| Domain facts, grain, value meaning, join provenance | OFN `rdfs:comment` |
| Business constraints, value lists (`sh:in`) | SHACL |
| Query, join and output policy | Mapping USAGE POLICY |
| Entity and column bindings, joins on plain columns | Mapping (`table:` = entity name) |
| Entity structure (fields and local types only) | `input/entities/{EntityName}.json` |

Do not model system fields (`Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`) as domain properties; use `$(Id)` as the subject key.

**Relationships are owned by the ontology.** Model a foreign key as a plain local field (for example `Order.customerId`, `STRING`), plus an object property in the schema, joined in the mapping on plain columns (`Order.customerId = Customer.Id`). See [relationships-guide.md](references/relationships-guide.md).

If a class must read from an external (federated) system, stop and tell the user: a federated entity needs an Integration Service connection and is not authorable locally. If the user asks for functions, actions or business rules, say they are not in M1; constraints go to SHACL.

## Step 1 — Gather inputs

Collect only missing values: domain (classes, fields, relationships, constraints) or source files; any entity definitions the user already has; `ONTOLOGY_NAME`, optional display name and description; new solution name or existing solution folder; base directory (default: current directory). Resolve every path to an absolute path, then show for confirmation:

```text
ONTOLOGY_IRI = https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR      = <BASE_DIR>/<ONTOLOGY_NAME>/
SOLUTION_DIR = <SOLUTION_PARENT>/<SOLUTION_NAME>/
```

Tell the user the name must be unique in the tenant; a conflict is resolved by renaming at deploy. Reject before creating anything: a name that fails the `ONTOLOGY_NAME` pattern, `WORKDIR` equal to or nested with `SOLUTION_DIR`, or an existing `WORKDIR` that holds files you did not generate. Then run `mkdir -p "<WORKDIR>/input/entities"`.

### Files mode — clone or rebuild from existing artifacts

1. Copy only artifact files (`.ofn`, `.ttl`, `.yarrrml.yml`, `.json`) from the source folder into `WORKDIR`; never copy symlinks or subfolders. Leave out business rules, functions and actions files (not in M1). A plain-text summary is not accepted: rewrite it as `{name}-summary.json`.
2. When cloning, rename `{oldName}` → `{name}` in file names and in every IRI and `PREFIX ont:` line.
3. Remove any `entityId` or `folderId` keys from the mapping; each source keeps only `access`, `table: {EntityName}`, and `referenceFormulation`.
4. Build the entity bodies: use any the user supplies (`supplied`); otherwise derive them from the mapped columns and schema ranges (`generated`) and confirm them.
5. Continue at Step 3 with `MAPPING_STATUS: supplied` (or `generate` when no mapping file exists).

## Step 2 — Model the domain

Produce one reviewable summary:

- classes with one-row grain, business meaning, and entity name (default: the class name; must match `^[a-zA-Z][a-zA-Z0-9_]{2,99}$`);
- data properties with camelCase names, XSD types, the local field type each maps to, and required flags;
- object properties with direction, cardinality notes, and **join columns** (for example `Order.customerId = Customer.Id`). Use a named FK field as is; otherwise propose `{targetClass}Id` joined to the target's `Id` and ask;
- subclass axioms and business constraints mapped to SHACL.

Record `ENTITY_SOURCE` per entity, following [entity-format-guide.md](references/entity-format-guide.md):

| `ENTITY_SOURCE` | Meaning | What to do |
|---|---|---|
| `supplied` | The user gave an entity definition (JSON body, table, or a local entity already in the solution) | Use it as the body as is. If a type isn't one of the nine local types, ask which local type to use; never substitute silently |
| `described` | The user described fields in words | Keep every stated name, type and required flag. Fill gaps (display names, lengths) and show them |
| `generated` | You proposed the entity from the domain | Generate it, show it, and get one confirmation |

The schema and mapping follow the entity and field names exactly (case-sensitive), not the other way round. Wait for confirmation, then write `<WORKDIR>/input/handoff.json` (the confirmed `CLASS_MAP`, `ENTITY_SOURCE`, `RELATIONSHIPS` with join columns) and one `<WORKDIR>/input/entities/<Entity>.json` update body per entity: `displayName`, `description` and `addFields` (see [entity-format-guide.md](references/entity-format-guide.md); a supplied `fields` list moves unchanged under `addFields`).

## Step 3 — Write each artifact, then check it

In delegated mode, first apply Step 1's path checks to the handoff's `WORKDIR` and `SOLUTION_DIR`, run `mkdir -p "<WORKDIR>/input/entities"`, and write `ENTITY_DEFINITIONS` to `input/entities/` as update bodies (supplied fields verbatim, under `addFields`).

Read only the references needed:

- [OWL patterns](references/owl-patterns-guide.md)
- [SHACL patterns](references/shacl-patterns-guide.md)
- [YARRRML mapping](references/mapping-yarrrml-guide.md)
- [Relationships](references/relationships-guide.md)
- [Summary and context](references/summary-context-guide.md)

Present one combined draft summary and obtain one batch confirmation before writing. In the mapping, each source is `access: datafabric`, `table: {EntityName}`, `referenceFormulation: rr:SQL2008`. Every `$(column)` is a field of that entity, exactly as written, or `Id`. Every object property between mapped classes has a join on plain columns.

Check every file you write (offline UiPath-convention check):

```bash
uip ont artifacts check <name>.ofn --content-type text/owl-functional --type schema --file "<WORKDIR>/<name>.ofn" --output json
uip ont artifacts check <name>-constraints.ttl --content-type text/turtle --type constraints --file "<WORKDIR>/<name>-constraints.ttl" --output json
uip ont artifacts check <name>-mapping.yarrrml.yml --content-type application/yaml --type mapping --file "<WORKDIR>/<name>-mapping.yarrrml.yml" --output json
uip ont artifacts check <name>-summary.json --content-type application/json --type summary --file "<WORKDIR>/<name>-summary.json" --output json
```

Fix every ERROR before moving on (see the recovery table). Show WARNINGs to the user and fix them when the fix is mechanical.

## Step 4 — Solution and local entities

Every command takes `--output json`; check `Result: Success`. The `uip df entities` commands have no `--solution-folder` flag: run them from the solution folder. The `uip ont` commands take `--solution-folder "<SOLUTION_DIR>"`.

<!--skill-flavor:solution-create:start-->
1. When `SOLUTION_DIR` does not exist yet, create the solution from its parent folder:
   ```bash
   cd "<SOLUTION_PARENT>" && uip solution init "<SOLUTION_NAME>" --output json
   ```
<!--skill-flavor:solution-create:end-->
2. From the solution folder, create each new entity (`create` takes no body), then add its fields with `update --body`:
   ```bash
   cd "<SOLUTION_DIR>"
   uip df entities create <Entity> --local --output json
   uip df entities update <Entity> --local --body "$(cat "<WORKDIR>/input/entities/<Entity>.json")" --output json
   ```
   The body for a new entity uses `addFields`, for example:
   ```json
   {"displayName": "Order", "description": "ONE row per customer order.", "addFields": [{"name": "customerId", "type": "STRING", "lengthLimit": 64, "isRequired": true}, {"name": "orderDate", "type": "DATETIME_WITH_TZ"}]}
   ```
   For an entity that already exists in the solution, never re-create it: run only `update` with `addFields`, `updateFields` or `removeFields`.
   At deploy an entity merges into a same-name entity in the folder and a changed field type is rejected; warn the user when they change a field type.

## Step 5 — Ontology resource and its files

```bash
uip ont create <Name> --local --entity <E1> --entity <E2> [--display-name "<d>"] [--description "<d>"] --solution-folder "<SOLUTION_DIR>" --output json
uip ont files add <Name> "<WORKDIR>/<name>.ofn" "<WORKDIR>/<name>-constraints.ttl" "<WORKDIR>/<name>-mapping.yarrrml.yml" --local --solution-folder "<SOLUTION_DIR>" --output json
```

Add the optional summary and context files the same way. `files add` runs the per-file check again and rebuilds the zip; if any file has an ERROR, nothing is attached. Pass `--type` only when the type is ambiguous (`ArtifactTypeUnresolved`). Never pass `--folder operations` (not in M1). Re-adding the same file name replaces it.

## Step 6 — Validate until clean

First make sure the user is logged in:

```bash
uip login status --output json
```

If not logged in, ask the user to run `uip login` and wait. Then loop on both until clean:

```bash
uip ont validate --local --solution-folder "<SOLUTION_DIR>" --output json
(cd "<SOLUTION_DIR>" && uip df entities validate --local --output json)
```

Read `Data` of the ontology result. It is clean when there is no ERROR from either `source` (`local` or `service`) and `ServiceValidation` is `"Done"` (never `"Skipped"`). After each repair: edit the file in `WORKDIR`, rerun `artifacts check`, re-add it with `files add`, then validate again. Entity changes go through `uip df entities update --local`. A `SVC-002` warning does not block: tell the user a rename at deploy will be needed, and carry on.

If the service is unavailable (`ServiceValidationUnavailable`, `ServiceValidationFailed`), stop and tell the user. Never fall back to offline validation and never pack as validated.

## Step 7 — Pack and confirm the packed contents

```bash
uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --dry-run --output json
uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --output json
uip ont files list <Name> --package "<PACKAGE_PATH>" --output json
```

The listing (`Data.artifacts`, with `fileName` and `type`) must contain exactly the validated artifacts; it never lists `ontology.json`. A mismatch means an artifact changed after validation: go back to Step 5.

Stop after pack. Report `SOLUTION_DIR`, `PACKAGE_PATH`, `PACKED_FILES` and `VALIDATION`.

## Step 8 — Hand off publish, deploy and activate to `uipath-solution`

Only when the user asks to deploy, load `uipath-solution` and let it publish `PACKAGE_PATH` as is, then deploy (which activates by default). The modeler runs none of these commands. Add two facts to the handoff:

- The ontology name must be free in the tenant, or already live in the same target folder. Otherwise deploy reports a name conflict whose only allowed action is `RenameInSolution`. `uipath-solution` asks the user for a new name and sets `conflictFixingAction` `RenameInSolution` and the new `name` for this resource in the deploy config (per resource, never with `--all`).
- The deployment folder becomes the ontology's data-query folder.

## Step 9 — Confirm in the deployment folder

After `uipath-solution` reports the deployment active, confirm with live, read-only reads:

```bash
uip ont get <Name> --folder-key <key> --output json
uip df entities list --folder-key <key> --output json
```

`<Name>` is the deployed name: the new one if the deploy used `RenameInSolution`.

## Updating an existing solution

1. From the solution folder: `uip df entities update <Entity> --local --body …` per changed entity; for a new one, `uip df entities create <Entity> --local`, then `update --body` with `addFields`.
2. Link or unlink entities: `uip ont update <Name> --local --add-entity <E> --remove-entity <E>`. Report (do not delete) entities that are no longer linked.
3. `uip ont files add` for new or changed files (same file name replaces); `uip ont files remove <Name> <file> --local` for dropped files.
4. Run the Step 6 validate loop, then Step 7.

## Errors

The skill acts on each violation's `rule`, `file` and `suggestion`; it never re-implements a check. C0 violations come from `artifacts check`, `files add` and `validate`; C1 error codes come in the `Code` of a failure envelope.

### Recovery table

| Signal | Source | Action |
|---|---|---|
| `OFN-001`, `OFN-002`, `OFN-004`, `OFN-005`, `OFN-009` | local | Fix `{name}.ofn` per [owl-patterns-guide.md](references/owl-patterns-guide.md) (IRI on `ontology.uipath.com`, `ClassName.fieldName` names, labels, no `has{Prop}` names); `artifacts check`; `files add`; validate |
| `SHC-002`, `SHC-003`, `SHC-004`, `SHC-006`, `SHC-007`, `SHC-008`, `SHC-009`, `SHC-010` | local | Fix the named constraints file per [shacl-patterns-guide.md](references/shacl-patterns-guide.md) (one `sh:NodeShape` with one `sh:targetClass`, labels, counts, `sh:class` on relationship paths); same loop |
| `MAP-002`, `MAP-004`, `MAP-005`, `MAP-006` | local | Fix the mapping per [mapping-yarrrml-guide.md](references/mapping-yarrrml-guide.md) (`access: datafabric`, `table: <Entity>`, no IDs, subject template, `a <Class>`, joins instead of inline IRIs); same loop |
| `CTX-001`, `CTX-002`, `CTX-003`, `CTX-005`, `CTX-006`, `CTX-007` | local | Rewrite `{name}-context.json` per [summary-context-guide.md](references/summary-context-guide.md), or drop it with `uip ont files remove` |
| `SUM-001`, `SUM-002` | local | Rewrite `{name}-summary.json` as a JSON object, or drop it with `uip ont files remove` |
| `XF-001` (missing required file or wrong count) | local | Write or remove files so there is exactly one schema, at least one constraints file, one mapping, at most one summary and one context; `files add` / `files remove` |
| `XF-002` (`ontology.json` differs from the resource) | local | WARNING: re-run `uip ont files add` with any artifact to rebuild the zip. ERROR: the zip was not written by the CLI; rebuild it with `files add` for every artifact |
| `XF-003`, `XF-004` (IRI, `shape:` namespace) | local | Use `https://ontology.uipath.com/<name>#` everywhere and `https://ontology.uipath.com/shapes#` for `shape:` |
| `XF-005` (OWL 2 QL) | local | Remove the forbidden construct from the schema; record the rule in `rdfs:comment` or SHACL instead |
| `XF-006`, `XF-008` (undeclared terms) | local | Declare the term in the schema, or fix the name used in the mapping or constraints |
| `XF-007` (missing label or comment) | local | Add `rdfs:label` and `rdfs:comment` to every class and property |
| `XF-009` (class not deployable) | local | Give the class a property and a mapping block backed by an entity, or fold it into a property's `rdfs:comment` |
| `XF-010` (property unmapped, class without shape) | local | Map every schema property; give every class a `sh:targetClass` shape |
| `XF-011` (`entityId` or `folderId` in the mapping) | local | Remove them; keep `table: <Entity>` only |
| `XF-012`, `XF-013` (`table:` not a current linked entity, or a column that is not a field) | local | If the entity is `supplied`, fix the mapping to its names. Otherwise ask, then fix the mapping or `uip df entities update --local`. Link with `uip ont update <Name> --local --add-entity <E>` |
| `XF-014`, `XF-015` (join on an undeclared object property, or an object property with no join) | local | Declare the object property or add the join per [relationships-guide.md](references/relationships-guide.md); add the key field to the entity if missing (ask if `supplied`) |
| `SVC-001` (any `source: "service"` violation) | service | W3C syntax problem in the named file. Fix the syntax; same loop |
| `SVC-002` WARNING (name already used in the tenant, folder by id) | service | Tell the user: if the target folder is that folder, deploy upgrades in place; otherwise a rename at deploy will be needed (`uipath-solution`, `RenameInSolution`). Carry on; not a blocker for pack |
| `ServiceValidationUnavailable` (not logged in) | C1 | Ask the user to run `uip login`, then rerun. Ignore the hint's offline option |
| `ServiceValidationFailed` (network, server, permission) | C1 | Stop and tell the user. Do not pack as validated |
| `ValidationFailed` | C1 | ERRORs are in `Data`; fix each per the rows above and validate again |
| `ArtifactCheckFailed` | C1 | ERRORs are in `Data.violations`; nothing was attached. Fix them, then `files add` again |
| `ArtifactTypeUnresolved` | C1 | Pass `--type`, or rename the file to the `{name}-summary.json` / `{name}-context.json` form |
| `ArtifactTypeAlreadyPresent` | C1 | Re-add under the existing file name to replace it, or `files remove` the old one first |
| `InvalidArtifactFileName` | C1 | Rename the file to the `{name}-…` convention; never name a file `ontology.json` |
| `ArtifactTypeNotSupported`, `FolderNotSupported` | C1 | Not in M1. Drop the functions, actions or business rules file; never pass `--folder operations` |
| `ArtifactNotFound` | C1 | The file is not in the zip; check `uip ont files list <Name> --local` and use the listed name |
| `NoParentSolution` | C1 | `--solution-folder` holds no `.uipx`; fix `SOLUTION_DIR` or create the solution (Step 4) |
| `OntologyNotFound` | C1 | Create the resource first (Step 5), or fix the name from `uip ont list --local` |
| `OntologyNameTaken` | C1 | The name is already used in the solution: ask for another name, or update the existing resource |
| `InvalidOntologyName` | C1 | Pick a name matching the `ONTOLOGY_NAME` pattern |
| `EntityNotFound` | C1 | Create the entity with `uip df entities create --local` and `update --local --body` (Step 4), or fix the name from the list in `Instructions` |
| `LocalFlagRequired` | C1 | Add `--local` to the authoring command |
| `ConfirmationRequired` | C1 | `uip ont delete` needs `--yes`; ask the user before deleting |
| `ResourceFileMissing`, `InvalidResourceArchive` | C1 | Rebuild the zip with `uip ont files add` for every artifact |
| `InvalidAttachedFile`, `FileAttachNotSupported`, `ResourceNotFound` | C1 (SDK) | The attach was refused; read `Instructions`, fix the solution state (for example a missing resource), and re-run `files add` |
| `PackageNotFound`, `OntologyNotInPackage` | C1 | Pass the `PACKAGE_PATH` that pack reported; if the ontology is missing, pack again after Step 6 |
| `uip df entities validate --local` problem | Data Fabric CLI | Fix with `uip df entities update --local`; for an unsupported type, pick a local type with the user |
| `InlineEntityCreationDisabled` | Data Fabric CLI | The tenant lacks inline entity creation (`solution-inline-entity-creation`). Stop and ask a Data Fabric admin; deploy would fail too |
| Packed listing differs from the validated set | `files list --package` | Re-add the changed file, validate, pack again |
| `BLOCKED_AMBIGUITY` | skill | A class-to-entity, join column or identifier has no unique answer: stop and ask for the decision |
