---
name: uipath-ontology-modeler
description: "UiPath Ontology modeler (.ofn, SHACL .ttl, .yarrrml.yml, functions/actions .ttl). Models a domain and builds the ontology as a local UiPath solution: Ontology resource + local Entity resources via `uip solution`, validated by local preflight, then packed. Input: plain-language domain, existing artifact files to clone or rebuild, or an authoring handoff. No direct ontology-service calls; deploy only through the solution. For SDD/PDD/design documents→uipath-ontology-authoring. For publish/deploy of the packed solution→uipath-solution."
when_to_use: "User describes classes, fields, and relationships and wants an ontology; supplies .ofn/.ttl/.yarrrml.yml files to clone or turn into a solution; or uipath-ontology-authoring delegates a confirmed handoff."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# UiPath Ontology Modeler

Builds an ontology as a **local UiPath solution**: one `Ontology` resource holding the artifact files, plus one local `Entity` resource per class, linked as its dependencies. Nothing is created in a tenant. At deploy (via the solution), the entity service installs the entities, then the ontology service installs the ontology and resolves each mapping `table:` by entity name.

`<SKILL_DIR>` is the folder containing this SKILL.md.

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

| Mode | Input | Start at |
|---|---|---|
| Standalone | Plain-language domain description | Step 1 |
| Files | Existing artifact files (clone or rebuild) | Step 1, then "Files mode" |
| Delegated | Confirmed handoff from `uipath-ontology-authoring` | Step 3 |

## Critical Rules

1. **Never call the ontology service directly.** No ontology CLI service commands, REST calls, or SDK writes. The only deployment path is `uip solution pack` → publish → deploy, owned by `uipath-solution`.
2. **Validate paths before writing anything.** `WORKDIR` and `SOLUTION_DIR` are absolute, separate folders (neither inside the other). Write artifacts only inside `WORKDIR`; write to `SOLUTION_DIR` only through `uip solution` commands. Quote every path in shell commands.
3. **Run preflight with `--solution-dir` before the first `uip solution` command** and stop on any failed gate. Use its `paths.solution_state` (`new` | `existing`) to choose between Step 5 and "Updating an existing solution".
4. **Entities are always local and referenced by name.** Never put `entityId` or `folderId` in the mapping or handoff. Never switch to `--source remote`.
5. **Link entities before attaching files.** `files add` of the mapping fails with `UnresolvedEntityReference` until every mapping `table:` is linked.
6. **Never return success without a successful pack.** If a step fails, report which resources and files exist; never leave a partial solution silently.
7. **Stop after pack.** Deploy only when the user asks, by handing off to `uipath-solution`.

## Paths and artifacts

```text
ONTOLOGY_NAME  ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$   (IRI slug and file prefix; immutable)
ONTOLOGY_IRI   https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR        <BASE_DIR>/<ONTOLOGY_NAME>/        artifacts at top level, plus input/ and entities/ only
SOLUTION_DIR   <SOLUTION_PARENT>/<SOLUTION_NAME>/ absent (new) or containing exactly one .uipx (existing)
```

| File in `WORKDIR` | `--file-type` | Count |
|---|---|---|
| `{name}.ofn` — OWL 2 QL schema | `schema` | exactly 1 |
| `{name}-constraints[-{area}].ttl` — SHACL | `constraints` | 1 or more |
| `{name}-mapping.yarrrml.yml` — YARRRML, `table:` = entity name | `mapping` | exactly 1 |
| `{name}-functions[-{ClassName}].ttl` — SPARQL reads | `functions` | 0 or more |
| `{name}-{actionName}.ttl` — SQL writes, one per action | `actions` | 0 or more |
| `{name}-business-rules[-{area}].ttl` | `business-rules` | 0 or more |
| `{name}-summary.txt` | `summary` | 0 or 1 |
| `{name}-context.json` | `context` | 0 or 1 |
| `input/handoff.json` — machine-readable handoff | — | 1 |
| `entities/{EntityName}.json` + `.patch.json` — written by the entities script | — | 1 per class |

`{name}` is `ONTOLOGY_NAME`. Preflight rejects any other file, extension, or folder in `WORKDIR`.

## Delegated handoff contract

When called by ontology authoring, require one complete handoff. Do not rediscover or mutate its setup:

```text
ONTOLOGY_NAME: exact slug
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
WORKDIR: absolute path of the dedicated {name}/ artifact folder
SOLUTION_DIR: absolute path of the solution folder to create or update
CLASS_MAP: class -> entityName (and optional displayName); no IDs
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, rules
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, and grain
OPERATIONS: grouped query operations and structured write actions, if any
PREFLIGHT_HANDOFF_JSON: machine-readable JSON with CLASS_MAP, FIELD_METADATA (type, required, displayName, exactly one identifier per class), and explicit RELATIONSHIPS ([] when none)
```

Reject an incomplete handoff before writing files. `MAPPING_STATUS: supplied` means validate the provided mapping; `generate` means generate it from handoff metadata and is invalid when a class-to-entity, field, relationship, or identifier choice is ambiguous.

Return:

```text
SOLUTION_DIR: absolute path
PACKAGE_PATH: absolute path of the packed .zip
ONTOLOGY_KEY: resource key
ENTITY_KEYS: entityName -> resource key
ARTIFACT_INVENTORY: exact preflight artifact_inventory
GATES: preflight gate results
UNRESOLVED_AMBIGUITIES: none | numbered list with the missing decision
```

## Design rules

| Information | Artifact |
|---|---|
| Domain facts, grain, value meaning, FK provenance | OFN `rdfs:comment` |
| Business constraints | SHACL |
| Query/join/output policy | Mapping or function USAGE POLICY |
| Entity and column bindings | Mapping (`table:` = entity name) |
| Entity structure (fields, types, relationships) | `entities/{EntityName}.json` |
| Query implementation | Function `ont:statement` |
| SQL write implementation | Action `ont:statements` |

Do not model system fields (`Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`) as domain properties; use `$(Id)` as the subject key. Turn FK-shaped fields into object properties and list them in `RELATIONSHIPS`.

If a class must read from an external (federated) system, stop and tell the user: a federated entity needs an Integration Service connection and cannot be authored in a solution.

## Step 1 — Gather inputs

Collect only missing values: domain (classes, fields, relationships, rules, query and write operations) or source files; `ONTOLOGY_NAME`; new solution name or existing solution folder; base directory (default: current directory). Resolve every path to an absolute path, then show for confirmation:

```text
ONTOLOGY_IRI = https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR      = <BASE_DIR>/<ONTOLOGY_NAME>/
SOLUTION_DIR = <SOLUTION_PARENT>/<SOLUTION_NAME>/
```

Reject before creating anything: a name that fails the `ONTOLOGY_NAME` pattern, `WORKDIR` equal to or nested with `SOLUTION_DIR` (for example a solution named like the ontology in the same base directory), or an existing `WORKDIR` that holds files you did not generate. Then run `mkdir -p "<WORKDIR>/input"`.

### Files mode — clone or rebuild from existing artifacts

1. Copy only artifact files (`.ofn`, `.ttl`, `.yarrrml.yml`, `.txt`, `.json`) from the source folder into `WORKDIR`; never copy symlinks or subfolders.
2. When cloning, rename `{oldName}` → `{name}` in file names and in every IRI, `PREFIX ont:` line, and statement body.
3. Remove any `entityId` or `folderId` keys from the mapping; each source keeps only `access`, `table: {EntityName}`, and `referenceFormulation`.
4. Build `input/handoff.json` from the schema and mapping (one entity per mapped `table:`, fields from mapped columns, types from schema ranges) and confirm it with the user.
5. Continue at Step 3 with `MAPPING_STATUS: supplied` (or `generate` when no mapping file exists).

## Step 2 — Model the domain

Produce a reviewable summary:

- classes with one-row grain, business meaning, and entity name (default: the class name; must match `^[a-zA-Z][a-zA-Z0-9]{2,99}$`);
- data properties with camelCase names, XSD types (`xsd:string`, `xsd:decimal`, `xsd:integer`, `xsd:long`, `xsd:dateTime`, `xsd:date`, `xsd:boolean`, `xsd:anyURI`), and required flags;
- object properties with direction, cardinality notes, and the FK field that carries them;
- subclass axioms; business rules mapped to SHACL; query operations; write actions.

Wait for confirmation, then write `<WORKDIR>/input/handoff.json`:

```json
{
  "CLASS_MAP": {"Order": {"entityName": "Order"}},
  "FIELD_METADATA": {"Order": {"Id": {"identifier": true}, "orderNumber": {"type": "xsd:string", "required": true, "displayName": "Order Number"}, "customer": {"displayName": "Customer"}}},
  "RELATIONSHIPS": [{"from": "Order", "field": "customer", "to": "Customer"}]
}
```

## Step 3 — Generate artifacts and entities

In delegated mode, first apply Step 1's path checks to the handoff's `WORKDIR` and `SOLUTION_DIR`, run `mkdir -p "<WORKDIR>/input"`, and write `PREFLIGHT_HANDOFF_JSON` to `<WORKDIR>/input/handoff.json`.

Read only the references needed:

- [OWL patterns](references/owl-patterns-guide.md)
- [SHACL patterns](references/shacl-patterns-guide.md)
- [YARRRML mapping](references/mapping-yarrrml-guide.md)
- [Functions and actions](references/functions-patterns-guide.md)
- [Action contract](references/action-table-contract-guide.md)

Present one combined draft summary and obtain one batch confirmation before writing. In the mapping, each source is `access: datafabric`, `table: {EntityName}`, `referenceFormulation: rr:SQL2008`. Every `$(column)` is a field name from the entity definition, exactly as written (case-sensitive), or `Id`.

Write the entity definitions (reads `input/handoff.json`, rewrites `entities/`, removes stale entity files):

```bash
python3 "<SKILL_DIR>/scripts/ontology_entities.py" --workdir "<WORKDIR>"
```

Require `"status": "PASS"`; on `FAIL`, fix the model or handoff and rerun.

## Step 4 — Preflight gates

```bash
python3 "<SKILL_DIR>/scripts/ontology_preflight.py" --workdir "<WORKDIR>" --ontology-name "<ONTOLOGY_NAME>" --solution-dir "<SOLUTION_DIR>" --mapping-mode auto
```

Read `status`, `gate_results`, `mapping_status`, `artifact_inventory`, `paths`, `errors`, `warnings`. Repair every failed gate and rerun; reporting a failure without repairing it is not completion. If `mapping_status` is `GENERATE_MAPPING`, generate the mapping from `input/handoff.json` and rerun. Stop with `BLOCKED_AMBIGUITY` when the metadata cannot determine a safe mapping.

Gates: `PATHS` (WORKDIR/SOLUTION_DIR layout), `ARTIFACT_INVENTORY` (file names, extensions, counts), `IRI_CONSISTENCY`, `OWL_2_QL`, `DATA_PROPERTY_NAMING`, `CLASS_ANNOTATIONS`, `MAPPING_TERMS`, `LOCAL_ENTITIES` (every `table:` is a local entity, every entity is used, every column is a field, no IDs), `CROSS_FILE_TERMS`, `CLASS_DEPLOYABILITY`, `RELATIONSHIP`, `ACTION_CONTRACT`, `SEMANTIC_CONSISTENCY`, `NAMESPACE`.

## Step 5 — Build the local solution

Run each command with `--output json` and check `Result: Success`. Read each resource key from `Data.Key` of its `resources add` output: entity keys for `ENTITY_KEYS`, the ontology key for `ONTOLOGY_KEY`.

<!--skill-flavor:solution-create:start-->
1. When `paths.solution_state` is `new`, create the solution from its parent folder:
   ```bash
   cd "<SOLUTION_PARENT>" && uip solution init "<SOLUTION_NAME>" --output json
   ```
<!--skill-flavor:solution-create:end-->
2. For each `entities/<ENTITY_NAME>.json`, add the entity and patch it with its `.patch.json`:
   ```bash
   uip solution resources add --source local --kind Entity --name "<ENTITY_NAME>" --solution-folder "<SOLUTION_DIR>" --output json
   uip solution resources edit "<ENTITY_KEY>" --patch - --solution-folder "<SOLUTION_DIR>" --output json < "<WORKDIR>/entities/<ENTITY_NAME>.patch.json"
   ```
   `resources add` is idempotent: an existing entity with the same name returns its key, and the patch updates it.
3. Add the ontology:
   ```bash
   uip solution resources add --source local --kind Ontology --name "<ONTOLOGY_NAME>" --solution-folder "<SOLUTION_DIR>" --output json
   ```
4. Link every entity:
   ```bash
   uip solution resources edit "<ONTOLOGY_KEY>" --add-entity <ENTITY_NAME> <ENTITY_NAME_2> --solution-folder "<SOLUTION_DIR>" --output json
   ```
5. Attach every file in `artifact_inventory`, always passing `--file-type` (several types share `.ttl`):
   ```bash
   uip solution resources files add "<ONTOLOGY_KEY>" --file "<WORKDIR>/<FILE>" --file-type <TYPE> --solution-folder "<SOLUTION_DIR>" --output json
   ```
6. Check `uip solution resources files list "<ONTOLOGY_KEY>" --solution-folder "<SOLUTION_DIR>" --output json` returns `Warnings: []`.

### Updating an existing solution

Re-patch every entity and add entity resources for new classes. Then, in order:

1. Link new entities with `--add-entity`.
2. Add or replace files with `files add` (same file name replaces).
3. Remove files no longer in `artifact_inventory`: `uip solution resources files remove "<ONTOLOGY_KEY>" --file-name "<FILE>" --solution-folder "<SOLUTION_DIR>" --output json`.
4. Unlink dropped classes with `--remove-entity`; report (do not delete) entity resources that are no longer linked.
5. Check `files list` returns `Warnings: []`.

## Step 6 — Pack

```bash
uip solution pack "<SOLUTION_DIR>" "<SOLUTION_DIR>/out" --output json
```

Report `SOLUTION_DIR` and `PACKAGE_PATH`. Stop. Deploy only when the user asks, by handing off to `uipath-solution` (publish, then `deploy run`).

## Common errors

| Error | Cause | Fix |
|---|---|---|
| Preflight `PATHS` fails | Wrong folder name, extra folder, overlapping `WORKDIR`/`SOLUTION_DIR`, folder that is not a solution, or missing `entities/` | Fix the path or layout named in the diagnostic; rerun preflight |
| Preflight `ARTIFACT_INVENTORY` name, extension, or `Unclassified artifact file` error | A non-artifact file in `WORKDIR`, a mapping not ending `.yarrrml.yml`, or a file without the `{name}` prefix | Rename or move the file (the handoff lives in `input/`) |
| `Resource metadata not found for Kind: ontology` on `resources add --kind Ontology` | The CLI or tenant does not expose the Ontology resource kind yet | Stop and report; internal preview builds can set `UIP_SOLUTION_METADATA_OVERLAY` to an ontology metadata overlay file |
| `UnresolvedEntityReference` on `files add` | The mapping names an entity not yet linked | `uip solution resources edit "<ONTOLOGY_KEY>" --add-entity <ENTITY_NAME> ...`, then re-add the file |
| `InlineEntityCreationDisabled` on `resources add --kind Entity` or `resources edit --patch` | The CLI is logged in to a tenant whose Data Fabric disallows inline entity creation; deploying there would fail too | Ask a Data Fabric admin to enable inline entity creation (`solution-inline-entity-creation`), or build logged out knowing deploy depends on that flag |
