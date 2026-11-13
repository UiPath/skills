---
name: uipath-ontology-authoring
description: "UiPath Ontology authoring from documents (SDD, PDD, domain specification). Extracts and confirms classes, properties with Data Fabric types, relationships, choice sets, federated sources and annotations with the user, then delegates artifact generation, the local solution build (ontology, entities, choice sets), service validation and pack to uipath-ontology-modeler. For plain-language domains or existing ontology files→uipath-ontology-modeler. For publish/deploy/activate of the packed solution→uipath-solution. For PDD→automation SDD design→uipath-planner."
when_to_use: "User provides an SDD, PDD, or design/domain specification and says 'create an ontology from this SDD', 'turn this PDD into an ontology solution', or 'build the ontology and its entities from this spec'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Authoring — Document to Local Ontology Solution

Scope: SDD/PDD/domain specification → confirmed domain model (Steps 2–4) → delegate to `uipath-ontology-modeler` → validated, packed local solution. Nothing is created on the tenant before deploy.

## When to Use This Skill

- The user supplies an SDD, PDD, design document or domain specification and wants an ontology built from it.
- The document names entities, field lists, value lists or external systems that the ontology must read.
- A plain-language domain with no document, or existing `.ofn`/`.ttl`/`.yarrrml.yml` files → `uipath-ontology-modeler`.

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

## Critical Rules

1. **Never call a service and never run `uip ont` or `uip df` writes.** The modeler runs the CLI. Publish, deploy and activate belong to `uipath-solution`.
2. **Wait for explicit user confirmation** after each of Steps 2, 3 and 4 before moving on.
3. **Validate paths in Step 1** before delegating: absolute paths, `ONTOLOGY_NAME` matches `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`, `WORKDIR` and `SOLUTION_DIR` are different folders (neither inside the other, and not the same path), and `SOLUTION_DIR` is either absent or an existing solution folder with exactly one `.uipx`.
4. **Capture facts and rules apart.** Record domain facts (meaning, grain, value domains) in `ANNOTATIONS`, required/range/value-list rules in `DOMAIN_MODEL` constraints, and query or join guidance as a separate note in `DOMAIN_MODEL`. The modeler places each in its artifact.
5. **No ids.** Entities, choice sets and connections are referenced by name; never pass or write an entity, field, choice-set, connection or folder id. What the document states about an entity is authoritative.
6. **Do not read or import the modeler's files.** Delegate at runtime with the contract below; if the modeler is unavailable, stop with the prepared model.
7. **The ontology name is unique per folder.** Tell the user; a same-name ontology the solution does not own is a deploy conflict that the deployer settles with `Replace` or `RenameInSolution`.
8. **The modeler authors the entities and choice sets locally in the solution.** Nothing is created on the tenant before deploy.

## Delegated modeler contract

Pass one complete handoff to `uipath-ontology-modeler`:

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

The modeler writes the artifacts, the local entities and choice sets, runs the CLI flow (ontology resource and its files, validation with the ontology service, pack) and returns:

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

If a class, field, join column, choice-set value or identifier cannot be inferred uniquely, require a user decision and stop as `BLOCKED_AMBIGUITY`.

---

## Step 1 — Collect the document and paths

Ask in one message:

| Input | Notes |
|---|---|
| **Document** | SDD/PDD file path, Confluence URL, or pasted text |
| **Ontology name** | `ONTOLOGY_NAME`; becomes the IRI slug and file prefix (e.g. `clinic`, `ecommerce`); unique per folder |
| **Display name, description** | Optional; the display name defaults to the ontology name |
| **Base directory** | Parent of the ontology's own folder (default: the document's directory, or current directory) |
| **Solution** | New solution name, or an existing solution folder to update (default name: `<ONTOLOGY_NAME>-solution`) |

Read the document immediately. Extract the **class names** first; Steps 2–4 build the full model. Also capture any **entity definitions or field lists** (tables, JSON bodies, column lists), **value lists** (choice sets) and **external data sources** (a system, connector and connection the document names). Entity definitions given in full go to `ENTITY_DEFINITIONS` verbatim; fields described in words keep every stated name, type and required flag; anything you propose from the domain is shown for confirmation.

Derive once, resolve to absolute paths, validate per Critical Rule 3, and confirm with the user:

```text
ONTOLOGY_IRI = https://ontology.uipath.com/<ONTOLOGY_NAME>#
WORKDIR      = <BASE_DIR>/<ONTOLOGY_NAME>/
SOLUTION_DIR = <BASE_DIR>/<SOLUTION_NAME>/   (or the existing solution folder)
```

When `SOLUTION_NAME` equals `ONTOLOGY_NAME`, both paths are the same folder: propose `<ONTOLOGY_NAME>-solution` instead and confirm it.

The IRI must be identical in every artifact and is immutable. Do not create files yourself; the modeler creates `WORKDIR` and everything in it.

---

## Step 2 — Define business concepts

Extract all classes. Show this table and wait for confirmation:

| Class | Entity name | Domain | Description (one line) | Synonyms | Subclass of |
|---|---|---|---|---|---|
| `Doctor` | `Doctor` | Care team | Medical practitioner licensed to treat patients | physician, doc | — |
| `Prescription` | `Prescription` | Treatment | A medication order issued by a doctor | script | — |

The entity name defaults to the class name and must match `^[a-zA-Z][a-zA-Z0-9_]{2,99}$`; it becomes the `CLASS_MAP` entityName and the mapping `table:` value.

The **domain** is the business area the ontology viewer groups the class under (one region per domain). Take 3–7 domains from the document's sections or process stages (`Master data`, `Purchasing`, `Intake`), give every class exactly one, and spell each identically across its classes. It is passed in `ANNOTATIONS` and becomes the schema's `:domain` annotation. Group by business area, not by source system: a federated class's connector is shown by its own icon.

| Document phrase | Model construct |
|---|---|
| "a/an X", "each X", "X is a" | New class |
| "also known as / aka / alias" | `skos:altLabel` on the class |
| "Y is a type of / subtype of Z" | `SubClassOf(:Y :Z)` |

**Not every noun is a class.** Actors, roles, or external systems mentioned only for narrative ("the AP Clerk captures the invoice") with no properties and no backing entity fail the modeler's validation (`XF-009`: every class needs a backing entity). Fold them into the relevant property's `rdfs:comment` instead (e.g. `Payment.approvedBy`: "The Accounts Payable Manager who approved this payment.").

---

## Step 3 — Define properties and relationships

Show these tables and wait for confirmation.

**Data properties:**

| Class | Property name | XSD type | Data Fabric type | Required? |
|---|---|---|---|---|
| `Doctor` | `Doctor.licenseNo` | `xsd:string` | `STRING` | required |
| `Prescription` | `Prescription.quantity` | `xsd:integer` | `DECIMAL` (`decimalPrecision: 0`) | — |
| `Prescription` | `Prescription.status` | `xsd:string` | `CHOICE_SET_SINGLE` (`PrescriptionStatus`) | required |

**Choice sets** (one per fixed value list):

| Choice set | Values (in order) | Used by | Select |
|---|---|---|---|
| `PrescriptionStatus` | `Active`, `Cancelled`, `Filled` | `Prescription.status` | single |

Value names are letters and digits and start with a letter. A property that allows several values from the list uses `CHOICE_SET_MULTIPLE`.

**Object properties (relationships):**

| Property | From | To | `relationshipField` | To column | Cardinality | Notes |
|---|---|---|---|---|---|---|
| `prescribedBy` | `Prescription` | `Doctor` | `doctor` (`RELATIONSHIP` on `Prescription`) | `Id` | exactly one | inverse: `prescribes` |
| `prescriptionFor` | `Prescription` | `Patient` | `patient` (`RELATIONSHIP` on `Prescription`) | `Id` | required | — |
| `treatedAt` | `Visit` | `Clinic` (federated) | `clinicKey` (plain column) | `ClinicKey` | exactly one | federated target |

Each relationship is one `relationshipField` on the referencing entity (`from`), and `RELATIONSHIPS` carries that field. The inverse is noted in the table and lives only in the schema (`InverseObjectProperties`); never a second field. When `to` is a federated entity, `relationshipField` is a plain column joined to its key column. Use an FK field name the document gives; otherwise propose one and ask.

**Federated sources** (only when the document names external data a class reads; otherwise skip):

| Entity | Source | `connectionName` | Object | Fields | Joins |
|---|---|---|---|---|---|
| `Clinic` | connector `<CONNECTOR_KEY>` | `<CONNECTION_NAME>` | `<OBJECT_NAME>` | `ClinicKey`, `Name` | — |

Record the connection by name; the modeler imports it into the solution and tells the user it needs sign-in after deploy. A source may instead be a local entity in the same solution (`entityName` source). If the document names a source but no connection, ask for the connection name and the folder that holds it.

| Document phrase | Model construct |
|---|---|
| "X has a/an Y" | DataProperty `{X}.{propName}` camelCase |
| "X is linked to / belongs to Y" | ObjectProperty from X to Y, one `relationshipField` on X |
| "X must have a Y" | ObjectProperty, required (`sh:minCount 1`) |
| "each X has exactly one Y" | ObjectProperty, exactly one (`sh:minCount 1; sh:maxCount 1`) |
| "X can have many Y AND Y can be shared across many X" | Junction class backed by its own entity with two `RELATIONSHIP` fields and two joins; flag to user |
| "X can have many Y" (Y owned by one X) | ObjectProperty on Y pointing at X, no cardinality |
| "X is one of / has a status of A, B, C" | Choice set with value names |
| "inverse of" | `InverseObjectProperties` + `SubObjectPropertyOf` if subproperty |

Data property naming: always `{ClassName}.{propName}` camelCase, never `has{Prop}`. Field names are letters and digits only, with no underscores.

| User says | XSD type | Data Fabric type |
|---|---|---|
| text, name, string, code, ID, URL, link | `xsd:string` / `xsd:anyURI` | `STRING` |
| long free text | `xsd:string` | `MULTILINE_TEXT` |
| price, amount, cost, rate | `xsd:decimal` | `DECIMAL` |
| count, quantity, integer | `xsd:integer` | `DECIMAL` (`decimalPrecision: 0`) |
| date + time / timestamp | `xsd:dateTime` | `DATETIME_WITH_TZ` |
| date only | `xsd:date` | `DATE` |
| true/false, flag | `xsd:boolean` | `BOOLEAN` |
| one of a fixed list of values | `xsd:string` | `CHOICE_SET_SINGLE` |
| several of a fixed list | `xsd:string` | `CHOICE_SET_MULTIPLE` |
| link to another class | — | `RELATIONSHIP` |

Never use `UUID`, `INTEGER` or `DATETIME`. If a supplied entity uses a type outside this table, ask the user which type to use; never substitute silently, and never replace a relationship or a choice set with `STRING`.

---

## Step 4 — Define labels, descriptions, and synonyms

Present one table at a time (classes, then data properties, then object properties) and wait for confirmation after each.

| Class | `rdfs:label` | `rdfs:comment` (grain first) | `skos:altLabel` |
|---|---|---|---|
| `Doctor` | `"Doctor"` | `"ONE row per doctor, keyed by Id."` | `"physician"` |

| Property | `rdfs:label` | `rdfs:comment` | `skos:altLabel` |
|---|---|---|---|
| `Prescription.status` | `"Status"` | `"Values: 'Active' \| 'Cancelled' \| 'Filled' (case-sensitive)."` | — |
| `prescribedBy` | `"Prescribed by"` | `"Each Prescription is prescribed by one Doctor. Join: Prescription.doctor = Doctor.Id."` | — |

`rdfs:comment` forms:

| Fact type | Form |
|---|---|
| Plain meaning | `"{What this field stores.}"` |
| Value domain (choice set) | `"Values: 'A' \| 'B' \| 'C' (case-sensitive; copy exactly)."` |
| Code list | `"'A' = meaning \| 'B' = meaning. '{Phrase}' means code IN ('A','B')."` |
| Format / scale | `"Stored 0–1 fraction; multiply by 100 for a percent answer."` |
| NULL with condition | `"NULL for ~N rows. NULLs sort last in DESC."` |
| Boolean | `"Compare true/false, never 1/0."` |

---

## Step 5 — Build the solution (delegate to `uipath-ontology-modeler`)

Delegate with the contract above: `ONTOLOGY_NAME`, `ONTOLOGY_IRI`, `DISPLAY_NAME`, `DESCRIPTION`, `WORKDIR`, `SOLUTION_DIR`, `CLASS_MAP`, `ENTITY_DEFINITIONS` (Data Fabric types; names in place of ids), `CHOICE_SETS`, `RELATIONSHIPS` with `relationshipField`, `FEDERATED_SOURCES` with each `connectionName`, `MAPPING_STATUS: generate`, the confirmed `DOMAIN_MODEL` (Steps 2–3) and `ANNOTATIONS` (Step 4).

Invoke the `uipath-ontology-modeler` skill (Skill tool) and pass the filled handoff block as its input, in Delegated mode. Do not run its stages yourself.

> If `uipath-ontology-modeler` is not available, stop and return: "Building the ontology solution requires the uipath-ontology-modeler sibling skill. The domain model is prepared; activate that skill and retry the delegation."

Require `UNRESOLVED_AMBIGUITIES: []`, a `PACKAGE_PATH`, a `PACKED_FILES` listing, and `VALIDATION: Done`. Report `SOLUTION_DIR`, `PACKAGE_PATH`, the ontology name, the entities, choice sets and connections, and the packed files.

When the return falls short:

| Return | Action |
|---|---|
| `UNRESOLVED_AMBIGUITIES` not empty | Ask the user each listed decision, update the confirmed model, delegate again |
| `VALIDATION` not `Done` | Show the remaining ERRORs; fix the model per Common errors and delegate again. After 2 delegations that fail the same way, stop and report |
| No `PACKAGE_PATH` or `PACKED_FILES` | The build stopped before pack: report the modeler's last error; never report the solution as packed |

**Stop after pack.** Deploy only when the user asks, by handing off to `uipath-solution` (publish, then deploy). It owns the deployment and the post-deploy check. Tell the user before handing off:

- The ontology name is unique per folder. A same-name ontology the solution does not own is a deploy conflict: the deployer chooses `Replace` or a new name (`RenameInSolution`).
- Each federated connection needs sign-in after deploy.

## Common errors

| Error | Cause | Fix |
|---|---|---|
| Modeler reports `XF-001`–`XF-010` | Missing or extra artifacts, IRI or namespace drift, OWL 2 QL constructs, unlabelled or undeclared terms, an undeployable class | Fix the confirmed model (Steps 2–4) if the cause is a modeling decision; delegate again |
| Modeler reports `XF-012`/`XF-013` | A class has no matching entity, or a mapped column is not a field of its entity | Fix the class-to-entity map or the entity fields in the handoff; delegate again |
| Modeler reports `XF-014`/`XF-015` | A relationship has no join, or a join has no relationship | Add or fix `relationshipField` and the join in `RELATIONSHIPS`; delegate again |
| Modeler reports `XF-017` | The `RELATIONSHIP` fields form a cycle: an inverse modeled as a second field, or a longer loop (A → B → C → A) | Keep one `relationshipField` per relationship and note the inverse in the schema only; for a longer loop, ask the user which relationship drops its field; delegate again |
| Modeler reports `XF-019` | Choice-set values differ from the constraints | Fix the value names in `CHOICE_SETS` and the Step 4 comment; delegate again |
| Modeler returns `BLOCKED_AMBIGUITY` | A class, field, join column, choice-set value or identifier has no unique answer | Ask the user for the listed decision; delegate again |
| The document names an external system without a connection | A federated source needs a `connectionName` | Ask for the connection name and the folder that holds it |
| The document asks for query functions, write actions or business rules | Not produced by this skill | Say so; business constraints go to SHACL |

## Anti-patterns

- Running `uip ont` or `uip df` writes, or writing artifact files, yourself: the modeler owns them (Critical Rule 1).
- Moving to the next step before the user confirms the current table (Critical Rule 2).
- Declaring a class for an actor or system named only in narrative: fold it into a property's `rdfs:comment` (Step 2).
- Replacing a stated relationship or value list with a `STRING` field (Step 3).
- Delegating with open ambiguities: stop with `BLOCKED_AMBIGUITY` instead.
