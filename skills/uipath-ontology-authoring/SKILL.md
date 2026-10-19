---
name: uipath-ontology-authoring
description: "UiPath Ontology authoring from documents (SDD, PDD, domain specification). Extracts and confirms classes, properties, relationships, annotations, query and write operations with the user, then delegates artifact generation and the local solution build (Ontology + local Entity resources, packed) to uipath-ontology-modeler. No direct ontology-service calls; deploy only through the solution. For plain-language domains or existing ontology files→uipath-ontology-modeler. For publish/deploy of the packed solution→uipath-solution."
when_to_use: "User provides an SDD, PDD, or design/domain specification and says 'create an ontology from this SDD', 'turn this PDD into an ontology solution', or 'build the ontology and its entities from this spec'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Authoring — Document to Local Ontology Solution

Scope: SDD/PDD/domain specification → confirmed domain model (Phases 3–5) → delegate to `uipath-ontology-modeler` → packed local solution.

<!--skill-flavor:host-support-extra:start-->
<!--skill-flavor:host-support-extra:end-->

## Critical Rules

1. **Never call the ontology service directly.** No ontology CLI service commands, REST calls, or SDK writes. Deployment happens only through `uip solution` publish/deploy, owned by `uipath-solution`.
2. **Wait for explicit user confirmation** after each of Phases 3, 4, and 5 before moving on.
3. **Validate paths in Step 1** before creating anything: absolute paths, `ONTOLOGY_NAME` matches `^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$`, `WORKDIR` and `SOLUTION_DIR` are separate folders (neither inside the other), and `SOLUTION_DIR` is either absent or an existing solution folder with exactly one `.uipx`.
4. **Separation of concerns:** facts go in `{name}.ofn`, rules go in USAGE POLICY blocks (mapping and functions), bindings go in `{name}-mapping.yarrrml.yml`. Never let domain facts drift into USAGE POLICY or routing rules into `rdfs:comment`.
5. **Entities are local and referenced by name.** Never look them up in a tenant; never pass `entityId` or `folderId`.
6. **Do not read or import the modeler's files.** Delegate at runtime with the contract below; if the modeler is unavailable, stop with the prepared model.

## Delegated modeler contract

Pass one complete handoff to `uipath-ontology-modeler`:

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

The modeler writes `PREFLIGHT_HANDOFF_JSON` to `<WORKDIR>/input/handoff.json`, generates artifacts and entity definitions, runs local preflight (including path validation), builds the solution with `uip solution` commands, packs it, and returns `SOLUTION_DIR`, `PACKAGE_PATH`, `ONTOLOGY_KEY`, `ENTITY_KEYS`, `ARTIFACT_INVENTORY`, `GATES`, and `UNRESOLVED_AMBIGUITIES`. If a class, field, identifier, or relationship cannot be inferred uniquely, require a user decision and stop as `BLOCKED_AMBIGUITY`.

---

## Step 1 — Collect the document and paths

Ask in one message:

| Input | Notes |
|---|---|
| **Document** | SDD/PDD file path, Confluence URL, or pasted text |
| **Ontology name** | `ONTOLOGY_NAME`; becomes the IRI slug and file prefix (e.g. `clinic`, `ecommerce`) |
| **Base directory** | Parent of the ontology's own folder (default: the document's directory, or current directory) |
| **Solution** | New solution name, or an existing solution folder to update |

Read the document immediately. Extract the **class names** first; Phases 3–5 build the full model. Also scan for:

- **Query operations (functions):** questions the system or an agent should answer ("how many X in state Y", dashboards, counts). Group by functional area; one functions file per area.
- **Write operations (actions):** mutations ("update status", "create record"). For each: action name, target entity, SQL operation (UPDATE / INSERT / DELETE), fields, identifier field, input parameters. One action file per action.

If neither is present, say so: no function or action files will be generated.

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

The entity name defaults to the class name and must match `^[a-zA-Z][a-zA-Z0-9]{2,99}$`; it becomes the `CLASS_MAP` entityName and the mapping `table:` value.

| Document phrase | Model construct |
|---|---|
| "a/an X", "each X", "X is a" | New class |
| "also known as / aka / alias" | `skos:altLabel` on the class |
| "Y is a type of / subtype of Z" | `SubClassOf(:Y :Z)` |

**Not every noun is a class.** Actors, roles, or external systems mentioned only for narrative ("the AP Clerk captures the invoice") with no properties and no backing entity fail the `CLASS_DEPLOYABILITY` gate. Fold them into the relevant property's `rdfs:comment` instead (e.g. `Payment.approvedBy`: "The Accounts Payable Manager who approved this payment.").

---

## Phase 4 — Define properties and relationships

Show two tables and wait for confirmation.

**Data properties:**

| Class | Property name | XSD type | Required? |
|---|---|---|---|
| `Doctor` | `Doctor.licenseNo` | `xsd:string` | required |
| `Prescription` | `Prescription.status` | `xsd:string` | required |

**Object properties (relationships):**

| Property | From | To | Cardinality | Notes |
|---|---|---|---|---|
| `prescribedBy` | `Prescription` | `Doctor` | exactly one | inverse: `prescribes` |
| `prescriptionFor` | `Prescription` | `Patient` | required | — |

| Document phrase | Model construct |
|---|---|
| "X has a/an Y" | DataProperty `{X}.{propName}` camelCase |
| "X is linked to / belongs to Y" | ObjectProperty from X to Y |
| "X must have a Y" | ObjectProperty, required (`sh:minCount 1`) |
| "each X has exactly one Y" | ObjectProperty, exactly one (`sh:minCount 1; sh:maxCount 1`) |
| "X can have many Y AND Y can be shared across many X" | Junction class mapped to a real association entity + two ObjectProperties — flag to user |
| "X can have many Y" (Y owned by one X) | ObjectProperty, no cardinality |
| "inverse of" | `InverseObjectProperties` + `SubObjectPropertyOf` if subproperty |

Data property naming: always `{ClassName}.{propName}` camelCase, never `has{Prop}`.

| User says | XSD type |
|---|---|
| text, name, string, code, ID | `xsd:string` |
| price, amount, cost, rate | `xsd:decimal` |
| count, quantity, integer | `xsd:integer` |
| date + time / timestamp | `xsd:dateTime` |
| date only | `xsd:date` |
| true/false, flag | `xsd:boolean` |
| URL, link | `xsd:anyURI` |

---

## Phase 5 — Define labels, descriptions, and synonyms

Present one table at a time (classes, then data properties, then object properties) and wait for confirmation after each.

| Class | `rdfs:label` | `rdfs:comment` (grain first) | `skos:altLabel` |
|---|---|---|---|
| `Doctor` | `"Doctor"` | `"ONE row per doctor, keyed by Id."` | `"physician"` |

| Property | `rdfs:label` | `rdfs:comment` | `skos:altLabel` |
|---|---|---|---|
| `Prescription.status` | `"Status"` | `"Values: 'Active' \| 'Cancelled' \| 'Filled' (case-sensitive)."` | — |
| `prescribedBy` | `"Prescribed by"` | `"Each Prescription is prescribed by one Doctor. FK: Prescription.DoctorId -> Doctor.Id."` | — |

`rdfs:comment` forms:

| Fact type | Form |
|---|---|
| Plain meaning | `"{What this field stores.}"` |
| Value domain (enum) | `"Values: 'A' \| 'B' \| 'C' (case-sensitive; copy exactly)."` |
| Code list | `"'A' = meaning \| 'B' = meaning. '{Phrase}' means code IN ('A','B')."` |
| Format / scale | `"Stored 0–1 fraction; multiply by 100 for a percent answer."` |
| NULL with condition | `"NULL for ~N rows. NULLs sort last in DESC."` |
| Choice set (NumberId) | `"NumberId. 1=Pending, 2=Shipped, 3=Delivered. Compare integers, not labels."` |
| Boolean | `"Compare true/false, never 1/0."` |

---

## Step 2 — Build the local solution (delegate to `uipath-ontology-modeler`)

Delegate with the contract above: confirmed model (Phases 3–4), annotations (Phase 5), operations, `ONTOLOGY_IRI`, `WORKDIR`, `SOLUTION_DIR`, `CLASS_MAP`, `MAPPING_STATUS: generate`, and `PREFLIGHT_HANDOFF_JSON`.

> If `uipath-ontology-modeler` is not available, stop and return: "Building the ontology solution requires the uipath-ontology-modeler sibling skill. The domain model is prepared; activate that skill and retry the delegation."

Require every gate passed, `UNRESOLVED_AMBIGUITIES: none`, and a `PACKAGE_PATH`. Report `SOLUTION_DIR`, `PACKAGE_PATH`, the ontology and entity resource keys, and the artifact inventory.

Stop after pack. Deploy only when the user asks, by handing off to `uipath-solution` (publish, then `deploy run`).

## Common errors

| Error | Cause | Fix |
|---|---|---|
| Modeler returns `PATHS` failure | Overlapping or misnamed `WORKDIR`/`SOLUTION_DIR`, or `SOLUTION_DIR` is a non-solution folder | Re-derive paths in Step 1 and delegate again |
| Modeler returns `LOCAL_ENTITIES` failure | A mapping `table:` is not a local entity, an entity is unused, or a column is not a field | Fix the class-to-entity map or fields in the handoff; delegate again |
| Modeler returns `BLOCKED_AMBIGUITY` | A class, field, identifier, or relationship has no unique answer | Ask the user for the listed decision; delegate again |
| A class needs an external system's data | Federated entities are not supported in this local flow | Stop and tell the user; do not create anything in Data Fabric |
