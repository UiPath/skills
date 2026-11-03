---
name: uipath-ontology-authoring
description: "UiPath Ontology authoring from documents (SDD, PDD, domain specification). Extracts and confirms classes, properties, relationships with their join columns, entity definitions, and annotations with the user, then delegates artifact generation, the local solution build (ontology + local entities), service validation and pack to uipath-ontology-modeler. For plain-language domains or existing ontology files→uipath-ontology-modeler. For publish/deploy/activate of the packed solution→uipath-solution. For PDD→automation SDD design→uipath-planner."
when_to_use: "User provides an SDD, PDD, or design/domain specification and says 'create an ontology from this SDD', 'turn this PDD into an ontology solution', or 'build the ontology and its entities from this spec'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Authoring — Document to Local Ontology Solution

Scope: SDD/PDD/domain specification → confirmed domain model (Phases 3–5) → delegate to `uipath-ontology-modeler` → validated, packed local solution.

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

## Critical Rules

1. **Never call a service.** The modeler runs the CLI; the ontology service is reached only through the modeler's service validation. Publish, deploy and activate belong to `uipath-solution`.
2. **Wait for explicit user confirmation** after each of Phases 3, 4, and 5 before moving on.
3. **Validate paths in Step 1** before creating anything: absolute paths, `ONTOLOGY_NAME` matches `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`, `WORKDIR` and `SOLUTION_DIR` are separate folders (neither inside the other), and `SOLUTION_DIR` is either absent or an existing solution folder with exactly one `.uipx`.
4. **Separation of concerns:** facts go in `{name}.ofn`, business constraints go in SHACL, query and join policy goes in the mapping's USAGE POLICY, bindings and joins go in `{name}-mapping.yarrrml.yml`. Never let domain facts drift into USAGE POLICY or routing rules into `rdfs:comment`.
5. **Entities are local and referenced by name.** Never look them up in a tenant; never pass `entityId` or `folderId`. What the document states about an entity is authoritative.
6. **Do not read or import the modeler's files.** Delegate at runtime with the contract below; if the modeler is unavailable, stop with the prepared model.
7. **The ontology name must be unique in the tenant.** Tell the user; a conflict is resolved by renaming at deploy.

## Delegated modeler contract

Pass one complete handoff to `uipath-ontology-modeler`:

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

The modeler writes the artifacts and the entity bodies, runs the CLI flow (local entities, the ontology resource and its files, validation with the ontology service, pack), and returns `SOLUTION_DIR`, `PACKAGE_PATH`, `ONTOLOGY_NAME`, `ENTITIES` (with `ENTITY_SOURCE`), `PACKED_FILES`, `VALIDATION`, and `UNRESOLVED_AMBIGUITIES`. If a class, field, join column, or identifier cannot be inferred uniquely, require a user decision and stop as `BLOCKED_AMBIGUITY`.

---

## Step 1 — Collect the document and paths

Ask in one message:

| Input | Notes |
|---|---|
| **Document** | SDD/PDD file path, Confluence URL, or pasted text |
| **Ontology name** | `ONTOLOGY_NAME`; becomes the IRI slug and file prefix (e.g. `clinic`, `ecommerce`); must be unique in the tenant |
| **Display name, description** | Optional; the display name defaults to the ontology name |
| **Base directory** | Parent of the ontology's own folder (default: the document's directory, or current directory) |
| **Solution** | New solution name, or an existing solution folder to update |

Read the document immediately. Extract the **class names** first; Phases 3–5 build the full model. Also capture any **entity definitions or field lists** in the document (tables, JSON bodies, column lists). Record each entity as `supplied` (a definition given in full: use it as is), `described` (fields described in words: keep every stated name, type and required flag), or `generated` (proposed by you from the domain). This becomes `ENTITY_SOURCE`.

Derive once, resolve to absolute paths, validate per Critical Rule 3, and confirm with the user:

```text
ONTOLOGY_IRI = https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR      = <BASE_DIR>/<ONTOLOGY_NAME>/
SOLUTION_DIR = <BASE_DIR>/<SOLUTION_NAME>/   (or the existing solution folder)
```

The IRI must be identical in every artifact and is immutable. Do not create files yourself; the modeler creates `WORKDIR` and everything in it.

---

## Phase 3 — Define business concepts

Extract all classes. Show this table and wait for confirmation:

| Class | Entity name | Description (one line) | Synonyms | Subclass of |
|---|---|---|---|---|
| `Doctor` | `Doctor` | Medical practitioner licensed to treat patients | physician, doc | — |
| `Prescription` | `Prescription` | A medication order issued by a doctor | script | — |

The entity name defaults to the class name and must match `^[a-zA-Z][a-zA-Z0-9_]{2,99}$`; it becomes the `CLASS_MAP` entityName and the mapping `table:` value.

| Document phrase | Model construct |
|---|---|
| "a/an X", "each X", "X is a" | New class |
| "also known as / aka / alias" | `skos:altLabel` on the class |
| "Y is a type of / subtype of Z" | `SubClassOf(:Y :Z)` |

**Not every noun is a class.** Actors, roles, or external systems mentioned only for narrative ("the AP Clerk captures the invoice") with no properties and no backing entity fail the modeler's validation (`XF-009`: every class needs a backing entity). Fold them into the relevant property's `rdfs:comment` instead (e.g. `Payment.approvedBy`: "The Accounts Payable Manager who approved this payment.").

---

## Phase 4 — Define properties and relationships

Show two tables and wait for confirmation.

**Data properties:**

| Class | Property name | XSD type | Local type | Required? |
|---|---|---|---|---|
| `Doctor` | `Doctor.licenseNo` | `xsd:string` | `STRING` | required |
| `Prescription` | `Prescription.status` | `xsd:string` | `STRING` | required |
| `Prescription` | `Prescription.quantity` | `xsd:integer` | `DECIMAL` (`decimalPrecision: 0`) | — |

**Object properties (relationships):**

| Property | From | To | Join columns | Cardinality | Notes |
|---|---|---|---|---|---|
| `prescribedBy` | `Prescription` | `Doctor` | `Prescription.doctorId` = `Doctor.Id` | exactly one | inverse: `prescribes` |
| `prescriptionFor` | `Prescription` | `Patient` | `Prescription.patientId` = `Patient.Id` | required | — |

Relationships belong to the ontology: the entity holding the key gets a plain field (for example `doctorId`, `STRING`), and the mapping joins on it. Use an FK field the document names as is; otherwise propose `{targetClass}Id` joined to the target's `Id` and ask. Entities carry no relationship or choice-set fields.

| Document phrase | Model construct |
|---|---|
| "X has a/an Y" | DataProperty `{X}.{propName}` camelCase |
| "X is linked to / belongs to Y" | ObjectProperty from X to Y, joined on a key field of X |
| "X must have a Y" | ObjectProperty, required (`sh:minCount 1`) |
| "each X has exactly one Y" | ObjectProperty, exactly one (`sh:minCount 1; sh:maxCount 1`) |
| "X can have many Y AND Y can be shared across many X" | Junction class backed by its own entity with two key fields and two joins — flag to user |
| "X can have many Y" (Y owned by one X) | ObjectProperty, no cardinality |
| "inverse of" | `InverseObjectProperties` + `SubObjectPropertyOf` if subproperty |

Data property naming: always `{ClassName}.{propName}` camelCase, never `has{Prop}`.

| User says | XSD type | Local type |
|---|---|---|
| text, name, string, code, ID | `xsd:string` | `STRING` |
| long free text | `xsd:string` | `MULTILINE_TEXT` |
| price, amount, cost, rate | `xsd:decimal` | `DECIMAL` |
| count, quantity, integer | `xsd:integer` | `DECIMAL` (`decimalPrecision: 0`) |
| date + time / timestamp | `xsd:dateTime` | `DATETIME_WITH_TZ` |
| date only | `xsd:date` | `DATE` |
| true/false, flag | `xsd:boolean` | `BOOLEAN` |
| URL, link | `xsd:anyURI` | `STRING` |
| one of a fixed list of values | `xsd:string` | `STRING` (values in `rdfs:comment`, `sh:in`) |

If a supplied entity uses a type outside the local types, ask the user which local type to use; never substitute silently.

---

## Phase 5 — Define labels, descriptions, and synonyms

Present one table at a time (classes, then data properties, then object properties) and wait for confirmation after each.

| Class | `rdfs:label` | `rdfs:comment` (grain first) | `skos:altLabel` |
|---|---|---|---|
| `Doctor` | `"Doctor"` | `"ONE row per doctor, keyed by Id."` | `"physician"` |

| Property | `rdfs:label` | `rdfs:comment` | `skos:altLabel` |
|---|---|---|---|
| `Prescription.status` | `"Status"` | `"Values: 'Active' \| 'Cancelled' \| 'Filled' (case-sensitive)."` | — |
| `prescribedBy` | `"Prescribed by"` | `"Each Prescription is prescribed by one Doctor. Join: Prescription.doctorId = Doctor.Id."` | — |

`rdfs:comment` forms:

| Fact type | Form |
|---|---|
| Plain meaning | `"{What this field stores.}"` |
| Value domain (enum) | `"Values: 'A' \| 'B' \| 'C' (case-sensitive; copy exactly)."` |
| Code list | `"'A' = meaning \| 'B' = meaning. '{Phrase}' means code IN ('A','B')."` |
| Format / scale | `"Stored 0–1 fraction; multiply by 100 for a percent answer."` |
| NULL with condition | `"NULL for ~N rows. NULLs sort last in DESC."` |
| Boolean | `"Compare true/false, never 1/0."` |

---

## Step 2 — Build the local solution (delegate to `uipath-ontology-modeler`)

Delegate with the contract above: the confirmed model (Phases 3–4), annotations (Phase 5), `ONTOLOGY_IRI`, `DISPLAY_NAME`, `DESCRIPTION`, `WORKDIR`, `SOLUTION_DIR`, `CLASS_MAP`, `ENTITY_SOURCE`, `ENTITY_DEFINITIONS`, `RELATIONSHIPS` with join columns, and `MAPPING_STATUS: generate`.

> If `uipath-ontology-modeler` is not available, stop and return: "Building the ontology solution requires the uipath-ontology-modeler sibling skill. The domain model is prepared; activate that skill and retry the delegation."

Require `UNRESOLVED_AMBIGUITIES: none`, a `PACKAGE_PATH`, a `PACKED_FILES` listing, and `VALIDATION` showing that service validation ran with no errors. Report `SOLUTION_DIR`, `PACKAGE_PATH`, the ontology name, the entities, and the packed files.

Stop after pack. Deploy only when the user asks, by handing off to `uipath-solution` (publish, then deploy, which activates); it resolves a tenant name conflict by renaming at deploy. The modeler then confirms the ontology and its entities in the deployment folder.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| Modeler reports `XF-001`–`XF-010` | Missing or extra artifacts, IRI or namespace drift, OWL 2 QL constructs, unlabelled or undeclared terms, an undeployable class | Fix the confirmed model (Phases 3–5) if the cause is a modeling decision; delegate again |
| Modeler reports `XF-012`/`XF-013` | A class has no matching entity, or a mapped column is not a field of its entity | Fix the class-to-entity map or the entity fields in the handoff; delegate again |
| Modeler reports `XF-014`/`XF-015` | A relationship has no join, or a join has no relationship | Add or fix the join columns in `RELATIONSHIPS`; delegate again |
| Modeler reports `SVC-002` | The ontology name is already used in the tenant | Tell the user a rename at deploy will be needed; not a blocker for pack |
| Modeler returns `BLOCKED_AMBIGUITY` | A class, field, join column, or identifier has no unique answer | Ask the user for the listed decision; delegate again |
| A class needs an external system's data | Federated entities are not supported in this local flow | Stop and tell the user; do not create anything in Data Fabric |
| The document asks for query functions, write actions or business rules | Not in M1 | Say so; business constraints go to SHACL |
