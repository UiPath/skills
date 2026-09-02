---
name: uipath-ontology-modeler
description: "Use when the user describes an ontology domain in plain language and wants local ontology artifact files, or when authoring supplies a confirmed delegated handoff for artifact generation. Do not use for SDD/PDD ingestion, Data Fabric entity setup, new-ontology deployment orchestration, or existing-ontology CRUD."
when_to_use: "Use for plain-domain modeling, local artifact generation, artifact regeneration, and delegated generation after a confirmed CLASS_MAP and workdir are supplied by ontology authoring."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# UiPath Ontology Modeler

Generate and validate ontology artifacts. This skill has two modes:

| Mode | Input | Start at |
|---|---|---|
| Standalone | Plain-language domain description | Step 1 |
| Delegated | Confirmed handoff from `uipath-ontology-authoring` | Step 3 |

Artifacts:

- `{name}.ofn` — OWL 2 QL schema
- `{name}-constraints.ttl` — SHACL constraints
- `{name}-mapping.yarrrml.yml` — YARRRML bindings
- `{name}-functions*.ttl` — optional SPARQL read functions
- `{name}-{actionName}.ttl` — optional SQL write actions

## Delegated handoff contract

When called by ontology authoring, require one complete handoff object. Do not rediscover or mutate its setup:

```text
ONTOLOGY_NAME: exact slug
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
WORKDIR: dedicated {name}/ output directory
CLASS_MAP: class -> entityName, entityId, folderId, readOnly (optional, rare)
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, rules
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, and grain
OPERATIONS: grouped query operations and structured write actions, if any
DEPLOYMENT_MODE: delegated; generate artifacts and run local preflight only; authoring owns backend validation and all uploads
PREFLIGHT_HANDOFF_JSON: machine-readable JSON with CLASS_MAP, FIELD_METADATA, and explicit RELATIONSHIPS ([] when none)
```

Reject an incomplete handoff before writing files. `MAPPING_STATUS: supplied` means validate the provided mapping and requires a mapping path or complete mapping contents. `MAPPING_STATUS: generate` means generate it from handoff metadata and requires machine-readable `CLASS_MAP` entries with entityName/entityId/folderId, `FIELD_METADATA` (with exactly one identifier) for every mapped class, and explicit `RELATIONSHIPS` metadata (`[]` when none); it is invalid when a class-to-entity, field, relationship, or identifier choice is ambiguous. In delegated mode, start at Step 3, preserve the supplied IRI and workdir, validate the provided mapping or generate it from handoff metadata, run local preflight, and return the confirmed file paths, gate results, and exact `artifact_inventory` to the caller. Never upload the mapping. Never make backend calls or upload artifacts in delegated mode.

When `MAPPING_STATUS: generate`, the generated mapping must use the supplied ontology IRI, folder key, entity IDs, schema terms, and exact field names. When `MAPPING_STATUS: supplied`, validate the provided mapping instead. Return this handoff result:

```text
MAPPING_PATH: absolute path
MAPPING_STATUS: PRESENT_VALID | PRESENT_INVALID | BLOCKED_AMBIGUITY
MAPPING_GATE: PASS | FAIL
UNRESOLVED_AMBIGUITIES: none | numbered list with the missing decision
```

`PRESENT_INVALID` and `BLOCKED_AMBIGUITY` are stop states: repair or request the missing decision before backend calls. Missing mapping is not itself an error when the generation metadata is complete.

If the caller is unavailable, return an actionable handoff error; do not create a partial ontology or claim deployment.

## Design rules

Keep concerns separated:

| Information | Artifact |
|---|---|
| Domain facts, grain, value meaning, FK provenance | OFN `rdfs:comment` |
| Business constraints | SHACL |
| Query/join/output policy | Mapping or function USAGE POLICY |
| Entity and column bindings | Mapping |
| Query implementation | Function `ont:statement` |
| SQL write implementation | Action `ont:statements` |

Do not model system fields (`Id`, `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`) as domain properties. Do not model narrative-only actors, roles, or systems without properties and a mapped entity. Turn FK-shaped fields into object properties unless a packed multi-valued FK cannot be joined.

## Step 1 — Gather standalone inputs

Collect only missing values:

- domain description: classes, fields, relationships, rules, query operations, and write operations;
- ontology slug, maximum 64 characters and without `/`;
- base directory, defaulting to the current directory.

Derive once and show for confirmation:

```text
ONTOLOGY_IRI = https://ontology.uipath.com/{name}#
WORKDIR      = {base directory}/{name}/
```

All artifacts go in `WORKDIR`. In standalone mode, perform login, folder selection, collision checking, and entity matching/creation before artifact generation. Do not create the ontology stub until the supplied mapping is validated or the mapping is generated from handoff metadata, and local preflight passes. Exclude the default folder, confirm the target folder, and record native versus federated entities. Federated entities are readable and writable through FQS, the same as native ones; treat `readOnly` as an explicit per-source exception, not a property of federation.

Show the structured domain model and wait for confirmation before writing. Derive artifact filenames from the slug; do not use fixed names.

## Step 2 — Model the domain

Produce a reviewable summary containing:

- classes with one-row grain and business meaning;
- data properties with camelCase names and XSD types;
- object properties with direction, cardinality notes, and FK provenance;
- subclass axioms;
- business rules mapped to SHACL;
- query operations grouped by functional area;
- write actions with name, entity, operation, target fields, identifier, and inputs.

Use `xsd:string`, `xsd:decimal`, `xsd:integer`, `xsd:dateTime`, `xsd:date`, `xsd:boolean`, or `xsd:anyURI` according to meaning. Keep cardinality enforcement in SHACL; OWL 2 QL does not use exact/min/max cardinality axioms.

## Step 3 — Generate artifacts

Read only the references needed for the artifact being generated:

- [OWL patterns](references/owl-patterns-guide.md)
- [SHACL patterns](references/shacl-patterns-guide.md)
- [YARRRML mapping](references/mapping-yarrrml-guide.md)
- [Functions and actions](references/functions-patterns-guide.md)
- [Action contract](references/action-table-contract-guide.md)

Use the same build → preview → local check → user confirmation → write sequence for each artifact. Present one combined draft summary and obtain one batch confirmation before writing.

Generate schema, constraints, mapping, optional functions, and optional actions. Use one function file per functional area or one combined file; choose once per ontology. Generate one action file per write operation. Read the paired `*-example.md` only when a gate fails or the base pattern is insufficient.

## Step 4 — Required local gates

Before returning artifacts or uploading tier-2 artifacts, invoke the neutral preflight utility against the exact workdir and upload set:

```bash
python3 tools/ontology_preflight.py \
  --workdir {workdir} --ontology-name {name} --mapping-mode auto \
  --handoff '{"CLASS_MAP": {...}, "FIELD_METADATA": {...}, "RELATIONSHIPS": []}'
```

Read its JSON `status`, `gate_results`, `mapping_status`, `artifact_inventory`, `errors`, and `warnings`. In delegated mode, return `artifact_inventory` to authoring as its exact backend validation/upload set; in standalone mode, use it locally. Repair every failed gate and rerun preflight; reporting a failure without repairing it is not completion. If mapping is `GENERATE_MAPPING`, generate it from the handoff metadata, then rerun preflight. Stop with `BLOCKED_AMBIGUITY` before any backend call when the metadata cannot determine a safe mapping.

Run all gates against the exact files that will be uploaded:

1. **QL gate:** reject OWL constructs outside OWL 2 QL, including cardinality, universal restrictions, nominals, unions, keys, transitivity, and functional-property axioms.
2. **Naming gate:** reject `has{Prop}` data-property names.
3. **Cross-file gate:** every term used by mapping, constraints, functions, or actions must be declared in the OFN schema.
4. **Annotation gate:** every class and property has `rdfs:label` and `rdfs:comment`.
5. **Class deployability gate:** every class is the domain of at least one property and is instantiated in the mapping.
6. **Relationship gate:** every FK-shaped relationship has an object property and mapping join, or an explicit packed-FK exemption.
7. **Semantic gate:** check domain completeness, constraint coverage, column alignment, policy coherence, and function/action consistency.

Fix failures before backend calls. A `DEPLOYED` state does not prove that relationships were modeled.

## Step 5 — Validate and upload

After local preflight passes, use `artifact_inventory` as the exact artifact list. In standalone mode only, create the ontology stub, then validate every inventory artifact in parallel with `uip ont artifact validate --output json`; require `Data.valid: true` for each artifact, not merely HTTP success. If any backend validation fails, repair the local artifact and rerun preflight before validating again.

```bash
uip ont create {name} --display-name "{display name}" --description "{description}" --folder-key {folder key} --output json
```

Upload in tiers:

1. schema;
2. constraints, functions, and actions in parallel;
3. mapping last only in standalone mode.

Use the exact upload set returned by preflight. Do not create the ontology stub or upload any artifact until the local preflight passes. In standalone mode, upload mapping last only after all other artifacts are validated and uploaded; in delegated mode, return the mapping to authoring with `MAPPING_GATE: PASS`, its `artifact_inventory`, and no backend validation/upload.

In delegated mode, stop after local preflight and return:

```text
ARTIFACTS: absolute paths
GATES: all seven gate results
ARTIFACT_INVENTORY: exact preflight artifact_inventory
BACKEND_VALIDATION: not run
UPLOADED: none
HELD: mapping
```

In standalone mode, upload the mapping last, then confirm the ontology state with `uip ont get`. Report any `DRAFT`, `BROKEN`, or validation state with the failed artifact and corrective action.

After deployment, verify both `uip ont get {name}` reports `DEPLOYED` and `uip ont artifact list {name}` contains the exact expected artifact inventory. A missing artifact or unexpected extra artifact is a deployment failure requiring correction.

## Routing boundary

- SDD/PDD/design document → `uipath-ontology-authoring`.
- Plain domain description → this skill.
- Existing ontology/artifact CRUD or SDK operations → `uipath-ontologies`.
- Deploying already-generated files → `uipath-ontology-authoring`, which owns the deployment gates.
