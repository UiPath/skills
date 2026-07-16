---
name: uipath-ontology-modeler
description: "Use when the user describes a domain in a prompt and wants to generate ontology artifact files (schema.ofn, rules.ttl, mapping.yarrrml.yml, functions.ttl, actions). No SDD required — a plain description of classes, fields, and relationships is enough. Also invoked by uipath-ontology-authoring as the artifact-generation step."
when_to_use: "User describes a domain in plain language ('I have Orders, Customers, Products…') and wants to generate OWL schema, SHACL constraints, or YARRRML mapping. Also use for: regenerating a single artifact, modeling a domain without an SDD, or when the authoring skill passes a confirmed domain model and CLASS_MAP."
allowed-tools: Bash, Read, Write, Edit
user-invocable: true
---

# UiPath Ontology Modeler

Generates all ontology artifact files from a domain description. **You can start from a plain prompt — no SDD required.**

Two entry points:

| How you start | Use |
|---|---|
| Describe your domain in a prompt ("I have Doctors, Patients, Prescriptions…") | **This skill directly** |
| You have an SDD file or Confluence page | `uipath-ontology-authoring` — it reads the SDD then calls this skill |

Artifacts generated:
- `schema.ofn` — OWL 2 QL Functional Syntax (classes, properties, labels, descriptions)
- `rules.ttl` — SHACL constraints (one shape per business rule)
- `mapping.yarrrml.yml` — YARRRML binding (class → entity, property → column, FK joins)
- `functions.ttl` — SPARQL read functions (optional — only if the domain includes query operations)
- `{actionName}.ttl` — SQL write actions (optional — one file per action)

Every file follows a build → preview → check → confirm → write flow. Nothing is written to disk before you confirm it.

> **Called by `uipath-ontology-authoring`?** Skip Steps 1 and 2 — the caller already collected the ontology name, IRI, confirmed domain model (Phases 3–4), confirmed annotations (Phases 5–6), and `CLASS_MAP`. Start at Step 3 directly with those inputs. Do not upload — return the confirmed file paths to the caller.

---

## Design Principle — Separation of Concerns

Each artifact owns exactly one type of information. Never mix them across files:

| Type | What it is | Where it lives |
|---|---|---|
| **Fact** | What a value means, what a class is, grain, value domain, FK provenance | `rdfs:comment` in `schema.ofn` |
| **Constraint** | Business rule that must hold (must have, must be one) | `rules.ttl` SHACL shape |
| **Rule** | How to query, join routing, LIMIT/DISTINCT discipline | USAGE POLICY block in `mapping.yarrrml.yml` |
| **Binding** | Class → entity, property → column, object property → FK join condition | `mapping.yarrrml.yml` source/po blocks |
| **Function fact** | What a function returns, when to use it vs other functions | `rdfs:comment` in `functions.ttl` |
| **Function rule** | Which function answers which question type, query output discipline | USAGE POLICY block in `functions.ttl` |
| **Function binding** | Which ontology terms the SPARQL traverses to answer the question | `ont:statement` in `functions.ttl` |
| **Action fact** | What a SQL action changes, what params it takes | `rdfs:comment` in `{actionName}.ttl` |
| **Action binding** | Which entity table and field columns the SQL writes | `{{Entity.field}}` in `ont:statements` |

**What this means in practice — do not:**
- Put query routing rules in `rdfs:comment` — they belong in USAGE POLICY
- Put FK join logic as OWL axioms in `schema.ofn` — note FK provenance as a fact in `rdfs:comment`, implement the join in mapping
- Put value domain meanings in USAGE POLICY — they belong in `rdfs:comment`
- Put entity IDs or column names in `schema.ofn` — they belong in mapping
- Explain what status codes mean inside a SPARQL rdfs:comment — that fact is already in `schema.ofn`

---

## Step 1 — Gather inputs

**If the user's opening message already describes the domain** (classes, fields, relationships), treat that as the domain description — do not ask for it again. Only ask for what is still missing.

Collect these inputs before generating anything:

| Input | Notes |
|---|---|
| **Domain description** | Classes, their fields, relationships, business rules — extract from the user's prompt if already provided |
| **Ontology name** | Short slug used in `uip ont` commands and as the IRI base (e.g. `clinic`, `ecommerce`) |
| **Working directory** | Where to write the generated files (defaults to current directory) |

Once the name is confirmed, derive the IRI internally — do not ask the user for it:
```
ONTOLOGY_IRI = https://ontology.uipath.com/{name}#
```
Show it once so the user can verify: `IRI: https://ontology.uipath.com/{name}#`

**Login check (silent):**
```bash
uip login status --output json
```
If `loggedIn: true` → continue without interrupting. If false → prompt for login before the entity list step.

**Cross-folder name collision check** — run after login is confirmed:
```bash
uip ont list --output json
```
Scan the result for any ontology whose name matches `{name}` (case-insensitive). If one exists in the **same folder** the backend will reject creation — tell the user and stop. If one exists in a **different folder**, warn explicitly before continuing:

> ⚠ An ontology named `{name}` already exists in folder `{otherFolderKey}` (ID: `{otherOntologyId}`). Creating another with the same name in a different folder means both will share the IRI `https://ontology.uipath.com/{name}#`. Any tool or reasoner that reads both will see the same term IRIs pointing to different data. Confirm you want to proceed, or choose a different name.

Wait for explicit user confirmation before continuing if a cross-folder match is found.

**Entity matching** — run after login is confirmed. Both native and federated entities are valid sources for an ontology:
```bash
uip df entities list --output json
```

Identify each entity's type: `externalFields: []` → **Native**; `externalFields: [{...}]` → **Federated**. For each class extracted from the description, show the matching table:

| Ontology class | Data Fabric entity | Type | Entity ID | Folder ID | Action |
|---|---|---|---|---|---|
| `Doctor` | `Doctor` (match) | Native | `b5b4bd01-...` | `751e18c5-...` | Use existing |
| `Contact` | `Contact` (match) | Federated | `9f1a2c44-...` | `751e18c5-...` | Use existing (read-only) |
| `Patient` | — | — | — | — | Create new (native) |

**Federated entity rules:**
- **Use existing only** — cannot create new federated entities via CLI; they must be set up in the Data Fabric UI linked to an Integration Service connection (SQL Server, Salesforce, SAP, etc.). If a class needs a federated entity that doesn't exist, stop and tell the user.
- **Read-only** — mark as `readOnly: true` in CLASS_MAP; no write actions can target them.
- **YARRRML mapping is identical** — same `access: datafabric`, entityId, folderId syntax; FQS handles federation transparently.

For each **Create new (native)** row, follow the `data-fabric` skill to create the entity and record its ID. Record the completed mapping as `CLASS_MAP`:

```
CLASS_MAP:
  {ClassName}: entityId={uuid}  folderId={uuid}  [readOnly: true]  ← federated only
```

If the description is vague after reading the prompt, ask one clarifying question at a time — do not block on a long questionnaire.

---

## Step 2 — Model the domain

Extract a structured model from the description (or use the model passed in from the authoring skill). Show it to the user and wait for confirmation before generating any file.

```
Classes:
  {ClassName} — {one-line description} [synonyms: ...]
    DataProperties:
      {ClassName}.{propName}: xsd:{type} [required | optional]
    Subclass of: {Parent} (if applicable)

ObjectProperties:
  {verbPhrase}: {FromClass} → {ToClass} [required | optional]

Business rules (→ SHACL):
  {plain-English rule}
```

**System/audit fields — always omit from the ontology:**

Fields like `CreatedAt`, `UpdatedAt`, `CreatedBy`, `UpdatedBy`, and `Id` are system-managed metadata. Do not include them as DataProperties in the ontology — they carry no domain meaning. Only model fields that represent business facts about the entity.

**Mapping rules:**

| User phrase | Model construct |
|---|---|
| "X has a Y" | DataProperty `{X}.{y}` on class X |
| "X belongs to / is linked to Y" | ObjectProperty from X to Y |
| "X must have a Y" | ObjectProperty + `ObjectSomeValuesFrom` + SHACL `minCount 1` |
| "each X has exactly one Y" | `rdfs:comment` stating "exactly one" (QL-inexpressible as axiom) + SHACL `minCount 1; maxCount 1` |
| "Y is a type of Z" | `SubClassOf(:Y :Z)` |
| "X can have many Y AND Y can be shared across many X" (mutual many-to-many) | Junction class mapped to the real association table + two ObjectProperties (see owl-patterns.md) |
| "X can have many Y" (one side only, Y owned by one X) | ObjectProperty, no cardinality restriction |

**Data property naming: `{ClassName}.{propName}` camelCase — never `has{Prop}`.** Examples: `Doctor.licenseNo`, `Patient.birthDate`, `Order.totalAmount`.

**XSD types:**

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

## Step 3 — Generate schema.ofn

Follow [owl-patterns.md](owl-patterns.md) exactly. This step has four sub-steps: build → preview → W3C check → confirm → write.

---

### 3a — Build the OFN content

Construct the full file content in memory (do not write yet). Cover all three requirements:

**1. Properties and relationships — types and cardinality**

- DataProperty: `DataPropertyDomain` + `DataPropertyRange(xsd:{type})` for every property from the confirmed domain model
- ObjectProperty: `ObjectPropertyDomain` + `ObjectPropertyRange` for every relationship
- `InverseObjectProperties` for inverse pairs; `SubObjectPropertyOf` for sub-properties
- Cardinality is QL-inexpressible as axioms — express in `rdfs:comment` text and enforce via SHACL in rules.ttl

**2. Labels, descriptions, and synonyms**

- `rdfs:label` — every class and every property, no exceptions
- `rdfs:comment` — **required** on every class and every property (data and object). Without `rdfs:comment`, the AI agent cannot answer questions about value domains, grain, or FK provenance.
  - Every class: grain statement first (`"ONE row per…"`) then business meaning
  - Every data property: pick the matching fact type form from `owl-patterns.md` (plain meaning, value domain, code list, format/scale, NULL condition, choice set, or boolean)
  - Every object property: business sentence + FK provenance (`"FK: {FromClass}.{FKField} -> {ToClass}.Id."`) + cardinality note if "exactly one"
- `skos:altLabel` — only for classes or properties that have a synonym from the confirmed model; add `Prefix(skos:=…)` to the file header only if at least one synonym exists

**3. Map concepts to source entities**

- ObjectProperty `rdfs:comment` includes FK provenance: `"FK: {FromClass}.{FKField} -> {ToClass}.Id."` — this is what wires the ontology relationship to the physical join column
- Class `rdfs:comment` includes the entity reference: `"… Maps Data Fabric entity '{EntityName}'."`

**File structure order** (fixed — matches real artifact format):

1. Prefix declarations — `:`, `owl:`, `rdf:`, `xml:`, `xsd:`, `rdfs:`, `skos:` (only if synonyms exist)
2. `Ontology(<https://ontology.uipath.com/{name}>` — no top-level `rdfs:label` or `rdfs:comment` inside `Ontology(...)`
3. All `Declaration(Class(...))` — grouped
4. All `Declaration(ObjectProperty(...))` — grouped
5. All `Declaration(DataProperty(...))` — grouped
6. `#### Object Properties ####` — per property: `# Object Property: <IRI> (Label)` comment, `rdfs:label`, `rdfs:comment` (FK form), domain, range, `InverseObjectProperties`/`SubObjectPropertyOf` if applicable
7. `#### Data Properties ####` — per property: `# Data Property: <IRI> (Label)` comment, `rdfs:label`, `rdfs:comment` (fact type form), domain, range
8. `#### Classes ####` — per class: `# Class: <IRI> (Label)` comment, `rdfs:label`, `rdfs:comment` (grain first), `skos:altLabel` per synonym
9. `SubClassOf(...)` axioms last — existential and inheritance only

---

### 3b — Show draft summary to user

Show a structured human-readable summary (not the raw OFN text). Wait for the user to review before running checks.

```
Schema draft: {ontology-name}
IRI: https://ontology.uipath.com/{name}#

Classes ({N}):
  {ClassName}  rdfs:comment: "{grain statement}"  skos:altLabel: {synonyms or —}

Data properties ({N}):
  {ClassName}.{propName}  xsd:{type}  [{required|optional}]  rdfs:comment: "{fact type comment}"

Object properties ({N}):
  {verbPhrase}  {FromClass} → {ToClass}  [{cardinality}]  rdfs:comment: "FK: {FromClass}.{Field} -> {ToClass}.Id."
  {inverseVerb} inverse of {verbPhrase}

SubClassOf axioms ({N}):
  {Child} ⊑ ObjectSomeValuesFrom({prop}, {Range})
```

---

### 3c — W3C OWL 2 QL check (on draft content)

Scan the draft content for W3C OWL 2 QL violations before writing the file. Two checks:

**Check 1 — QL blacklist** (forbidden constructs that pass OWL syntax but fail QL reasoning):

Scan draft for: `ExactCardinality`, `MinCardinality`, `MaxCardinality`, `AllValuesFrom`, `HasValue`, `ObjectOneOf`, `DataOneOf`, `ObjectUnionOf`, `DataUnionOf`, `ObjectHasSelf`, `FunctionalObjectProperty`, `FunctionalDataProperty`, `InverseFunctional`, `TransitiveObjectProperty`, `HasKey`

**Check 2 — Naming convention** (forbidden DataProperty name pattern):

Scan draft for: any `DataProperty(:has[A-Z]…)` — the `has{Prop}` anti-pattern

Report results:

```
W3C OWL 2 QL checks:
  ✓ QL blacklist — no forbidden constructs
  ✓ Naming convention — no has{Prop} DataProperty names
```

or if issues found:

```
W3C OWL 2 QL checks:
  ✗ QL blacklist — found: ObjectExactCardinality on :prescribedBy (line ~42)
    Fix: remove axiom; record "exactly one" in rdfs:comment instead
  ✓ Naming convention — clean
```

Fix any issues in the draft content before proceeding.

---

### 3d — Confirm and write

Show the user:
- The check results (✓ / ✗ per check)
- A one-line summary of what the file will contain

Then ask:

> **Confirm schema.ofn?** ({N} classes, {N} data properties, {N} object properties — W3C checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/schema.ofn`.
On revision request, update the draft and return to step 3b.

---

## Step 4 — Generate rules.ttl

Follow [shacl-patterns.md](shacl-patterns.md) exactly. Same build → preview → check → confirm → write flow as Step 3.

---

### 4a — Build the SHACL content

Construct the full file content in memory. One `sh:NodeShape` per business rule from the confirmed domain model.

**Structure rules:**
- Prefixes: `ont:`, `rdfs:`, `sh:`, `shape:`, `xsd:`
- Shape name: `shape:{ClassName}Must{BehaviorName}` (e.g. `shape:doctorMustBeLicensed`)
- Each shape: `rdfs:label` (human description) + `sh:message` (violation sentence) + `sh:targetClass` + one or more `sh:property` blocks
- Property path always `ont:{ClassName}.{propName}` — must match exactly what is declared in `schema.ofn`
- Cardinality forms:

| Business rule | SHACL |
|---|---|
| Required DataProperty | `sh:minCount 1 ; sh:datatype xsd:{type}` |
| Optional DataProperty | `sh:minCount 0 ; sh:maxCount 1 ; sh:datatype xsd:{type}` |
| Required ObjectProperty | `sh:minCount 1 ; sh:class ont:{Range}` |
| Exactly one | `sh:minCount 1 ; sh:maxCount 1` |
| Numeric, non-negative | `sh:minInclusive 0` |

Every business rule from the confirmed model must have a matching shape. No shape without a corresponding business rule.

---

### 4b — Show draft summary to user

```
SHACL draft: {ontology-name} rules.ttl

Shapes ({N}):
  shape:doctorMustBeLicensed
    target: ont:Doctor
    rule: "Doctor must be licensed"
    message: "A doctor must carry a license number"
    property: ont:Doctor.licenseNo  sh:minCount 1  xsd:string

  shape:prescriptionMustHaveStatus
    target: ont:Prescription
    rule: "Prescription must have a status"
    message: "A prescription must declare a status"
    property: ont:Prescription.status  sh:minCount 1  xsd:string

  shape:prescriptionMustBePrescribedByDoctor
    target: ont:Prescription
    rule: "Prescription must reference exactly one doctor"
    message: "A prescription must be prescribed by exactly one doctor"
    property: ont:prescribedBy  sh:minCount 1 ; sh:maxCount 1  sh:class ont:Doctor
```

---

### 4c — SHACL consistency check (against schema.ofn)

Verify the SHACL draft is consistent with the already-confirmed `schema.ofn`:

**Check 1 — Property path alignment:**
Every `sh:path` value in the draft must match a `Declaration(DataProperty(:…))` or `Declaration(ObjectProperty(:…))` in `schema.ofn`. Any mismatch → `BROKEN` state after deploy.

**Check 2 — Target class alignment:**
Every `sh:targetClass` must match a `Declaration(Class(:…))` in `schema.ofn`.

**Check 3 — Coverage:**
Every business rule from the confirmed model has a shape. No business rule is missing a shape.

Report:

```
SHACL consistency checks:
  ✓ Property paths — all sh:path values declared in schema.ofn
  ✓ Target classes — all sh:targetClass values declared in schema.ofn
  ✓ Coverage — all {N} business rules have a shape
```

Fix any issues in the draft before proceeding.

---

### 4d — Confirm and write

> **Confirm rules.ttl?** ({N} shapes covering {N} business rules — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/rules.ttl`.
On revision request, update the draft and return to step 4b.

---

## Step 5 — Generate mapping.yarrrml.yml

Follow [mapping-yarrrml.md](mapping-yarrrml.md). Same build → preview → check → confirm → write flow.

---

### 5a — Build the YARRRML content

Construct the full file content in memory. Use `entityId` and `folderId` from `CLASS_MAP`.

**Structure rules:**
- Open with a `# USAGE POLICY` comment block (≤30 non-empty lines): join graph, routing for ambiguous terms, grain discipline, output discipline — see `mapping-yarrrml.md`
- `prefixes:` block: `ont: https://ontology.uipath.com/{name}#`
- One `mappings:` block per class:
  - `sources:` — `access: datafabric`, `table: {EntityName}`, `entityId: {uuid}`, `folderId: {uuid}`, `referenceFormulation: rr:SQL2008`
  - `s:` — subject template: `ont:{ClassName}/$(primaryKeyColumn)`
  - `po:` — type triple `a: ont:{ClassName}`, then one pair per data property (`ont:{ClassName}.{propName}: $({columnName})`), then object property joins via `condition: function: equal`

Every `ont:` term used in the mapping must be declared in `schema.ofn`. Column names are case-sensitive — use the exact field name as it appears in the Data Fabric entity.

**This file must be uploaded last** — uploading the mapping flips the ontology from `DRAFT` to `DEPLOYED`.

---

### 5b — Show draft summary to user

```
Mapping draft: {ontology-name} mapping.yarrrml.yml

USAGE POLICY: {first line of policy block}

Mappings ({N} classes):
  Doctor  →  entityId: b5b4bd01-...  folderId: 751e18c5-...
    subject: ont:Doctor/$(Id)
    data:    ont:Doctor.licenseNo ← $(LicenseNo)
             ont:Doctor.name      ← $(Name)
             ont:Doctor.active    ← $(IsActive)

  Prescription  →  entityId: 9f1a-...  folderId: 751e-...
    subject: ont:Prescription/$(Id)
    data:    ont:Prescription.status   ← $(Status)
             ont:Prescription.medication ← $(MedicationName)
    joins:   ont:prescribedBy  ← Doctor where Doctor.Id = $(DoctorId)
             ont:prescriptionFor ← Patient where Patient.Id = $(PatientId)
```

---

### 5c — Mapping consistency check (against schema.ofn)

**Check 1 — Term coverage:**
Every `ont:` predicate in the mapping must be declared in `schema.ofn`. Extract all `ont:` terms from the draft and compare against `Declaration(…)` lines in `schema.ofn`.

**Check 2 — Column name plausibility:**
Every `$(columnName)` must correspond to a field that exists in the Data Fabric entity. Cross-check against the entity field names collected during Phase 2 entity matching.

**Check 3 — All classes mapped:**
Every class in the confirmed domain model has a mapping block. No class left unmapped.

Report:

```
Mapping consistency checks:
  ✓ Term coverage — all ont: predicates declared in schema.ofn
  ✓ Column names — all $(…) fields match entity schema
  ✓ Class coverage — all {N} classes have a mapping block
```

Fix any issues in the draft before proceeding.

---

### 5d — Confirm and write

> **Confirm mapping.yarrrml.yml?** ({N} classes mapped — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/mapping.yarrrml.yml`.
On revision request, update the draft and return to step 5b.

---

## Step 6 — Generate functions.ttl (skip if SDD has no query operations)

Query operations are natural-language questions the SDD says the system (or an AI agent) should answer from the ontology data: "how many X are in state Y", "show me all X with their Y", "which X has the most Y", "list X grouped by Z". If the SDD describes dashboards, summaries, counts, or searches, those are query operations. If the SDD is purely about data structure with no query requirements, skip this step.

If no query operations → skip this step and proceed to Step 7. Otherwise follow [functions-patterns.md](functions-patterns.md) and the same build → preview → check → confirm → write flow.

---

### 6a — Build functions content

Identify all natural-language questions from the SDD that an AI agent should answer from the ontology. Build the full file content in memory before writing.

**Separation of concerns inside functions.ttl:**
- **Fact** (what this function returns, when to use it) → `rdfs:comment` on each function
- **Rule** (which function to call for which question, LIMIT/DISTINCT discipline) → USAGE POLICY header block
- **Binding** (which `ont:` terms the SPARQL traverses) → `ont:statement`

For each function:
- **Name** — `ont:{camelCaseFunctionName}` (verb phrase: `countPrescriptionsByStatus`, `listPrescriptionsWithDoctorAndPatient`)
- **Label** — short human phrase
- **Comment** — per-function fact: what it returns, whether it produces counts or individual rows, what params it needs; do NOT put routing rules here — those go in USAGE POLICY
- **SPARQL SELECT** — inline on `ont:statement`, prefixed with `PREFIX ont: <https://ontology.uipath.com/{name}#>`; bind parameters as unbound triple variables, not in FILTER
- **Parameters** — only if needed; omit `fno:expects` entirely when the function takes none

**File structure** — all functions in a single file:
1. Prefix declarations: `fno:`, `ont:`, `rdfs:`
2. USAGE POLICY comment block — routing rules and output discipline (≤30 non-empty lines; see functions-patterns.md)
3. For each function: `ont:{functionName}` block, then any `ont:param.*` blocks immediately after

---

### 6b — Show draft summary

```
Functions draft: {ontology-name} functions.ttl

Functions ({N}):
  ont:countPrescriptionsByStatus
    label: "Count prescriptions in a given status"
    SPARQL: SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:Prescription ; ont:Prescription.status ?status }
    params: status (xsd:string, required)

  ont:listPrescriptionsWithDoctorAndPatient
    label: "List prescriptions with their doctor and patient"
    SPARQL: SELECT ?medication ?status ?doctorName ?patientName WHERE { ... (3-way join) }
    params: none
```

---

### 6c — Functions consistency check (on draft)

**Check 1 — Property paths:** every `ont:{ClassName}.{propName}` used in any SPARQL WHERE clause must be declared in `schema.ofn`.

**Check 2 — Class references:** every `a ont:{ClassName}` in SPARQL must be a declared class in `schema.ofn`.

**Check 3 — Object properties:** every `ont:{verbPhrase}` used as a property in SPARQL must be declared in `schema.ofn`.

**Check 4 — Parameter binding:** every `?paramName` that appears as an unbound input variable in the WHERE clause must have a matching entry in `fno:expects` and a corresponding `ont:param.*` block.

Report:
```
Functions checks:
  ✓ Property paths — all ont: DataProperty terms declared in schema.ofn
  ✓ Class references — all ont: class terms declared in schema.ofn
  ✓ Object properties — all ont: ObjectProperty terms declared in schema.ofn
  ✓ Parameter binding — all unbound variables have matching fno:expects entries
```

Fix any issues in the draft before proceeding.

---

### 6d — Confirm and write

> **Confirm functions.ttl?** ({N} functions — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

On confirmation, write `{workdir}/functions.ttl`.
On revision request, update the draft and return to step 6b.

---

## Step 7 — Generate action files (skip if SDD has no write operations)

If the SDD does not describe write/update operations, skip this step. One file per action — the file name IS the action's identity. Generate one action at a time through the full build → preview → check → confirm → write cycle.

---

### 7a — Build one action

For each write operation from the SDD:

- **Name** — `ont:{camelCaseActionName}` (verb phrase: `updatePrescriptionStatus`, `createPatientRecord`)
- **File name** — `{actionName}.ttl` (camelCase without the `ont:` prefix, e.g. `updatePrescriptionStatus.ttl`)
- **Label** — short human phrase
- **Comment** — what it changes, what params it takes, whether it modifies one row or many
- **SQL** — on `ont:statements ( "..." )` (plural, always a list even for a single statement)
  - `{{EntityName}}` — entity (table) reference, resolved by runtime from mapping
  - `{{EntityName.fieldName}}` — column reference, must match `{ClassName}.{propName}` naming from schema.ofn
  - `:paramName` — bound parameter, must match `ont:paramName` in the parameter block
- **Parameters** — `fno:expects` + `ont:param.*` block per parameter

---

### 7b — Show draft summary

```
Action draft: updatePrescriptionStatus.ttl

  ont:updatePrescriptionStatus
    kind: ACTION (SQL)
    label: "Update the status of a prescription"
    SQL: UPDATE {{Prescription}} SET {{Prescription.status}} = :newStatus WHERE {{Prescription.id}} = :id
    params:
      id (xsd:integer, required)
      newStatus (xsd:string, required)
```

---

### 7c — Action consistency check (on draft)

**Check 1 — Entity references:** every `{{EntityName}}` in the SQL must correspond to a class in the confirmed domain model.

**Check 2 — Field references:** every `{{EntityName.fieldName}}` must match a `{ClassName}.{propName}` declared in `schema.ofn` (e.g. `{{Prescription.status}}` → `ont:Prescription.status`).

**Check 3 — Parameter alignment:** every `:paramName` in the SQL must have a matching `ont:param.{actionName}.{paramName}` block.

Report:
```
Action checks (updatePrescriptionStatus.ttl):
  ✓ Entity references — Prescription declared in schema.ofn
  ✓ Field references — Prescription.status, Prescription.id declared in schema.ofn
  ✓ Parameter alignment — id and newStatus have matching param blocks
```

---

### 7d — Confirm and write

> **Confirm {actionName}.ttl?** (SQL action, {N} params — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

On confirmation, write `{workdir}/{actionName}.ttl`.
Repeat steps 7a–7d for each remaining action in the SDD.

---

## Step 8 — Gate-check all files (mandatory, all gates must pass)

Run every gate in order. Do not upload until all pass. Fix and regenerate on any failure.

> **Relationship to per-artifact checks:** Steps 3c, 4c, 5c, 6c, and 7c each scanned *draft* content before writing. Step 8 runs checks on the *written files* — confirming disk content matches what was confirmed. Gates 1–2 and 4 are a final sanity pass; Gate 3 is the definitive cross-file check since all files now exist. Gate 5 runs here only in standalone mode (see Gate 5 note below).

### Gate 1 — QL blacklist scan (text scan, no API needed)

Grep `schema.ofn` for forbidden OWL 2 QL constructs before touching the API:

```bash
grep -E "ExactCardinality|MinCardinality|MaxCardinality|AllValuesFrom|HasValue|ObjectOneOf|DataOneOf|ObjectUnionOf|DataUnionOf|ObjectHasSelf|FunctionalObjectProperty|FunctionalDataProperty|InverseFunctional|TransitiveObjectProperty|HasKey" {workdir}/schema.ofn
```

Zero hits required. Any match → fix in schema.ofn (move constraint to `rdfs:comment` text), re-run.

### Gate 2 — Naming convention scan (text scan)

```bash
grep -E "DataProperty\(:has[A-Z]" {workdir}/schema.ofn
```

Zero hits required. Any `has{Prop}` DataProperty name → rename to `{ClassName}.{propName}`, update all three files.

### Gate 3 — Cross-file consistency (text scan)

Every `ont:` term referenced in `mapping.yarrrml.yml` and every `sh:path` in `rules.ttl` must be declared in `schema.ofn`.

```bash
# Extract ont: terms from mapping (data/object properties used)
grep -oE "ont:[A-Za-z0-9._]+" {workdir}/mapping.yarrrml.yml | sort -u

# Extract sh:path values from rules
grep -oE "ont:[A-Za-z0-9._]+" {workdir}/rules.ttl | sort -u

# Check each against schema.ofn declarations
grep "Declaration(" {workdir}/schema.ofn
```

Every term found in mapping or rules must appear in a `Declaration(DataProperty(:...))` or `Declaration(ObjectProperty(:...))` in the schema. Any mismatch → fix before proceeding (a mismatch causes `BROKEN` state after deploy).

### Gate 4 — Annotation completeness (text scan)

Every declared class, data property, and object property must have both `rdfs:label` and `rdfs:comment`:

```bash
# What is declared
grep "Declaration(Class(:" {workdir}/schema.ofn
grep "Declaration(DataProperty(:" {workdir}/schema.ofn
grep "Declaration(ObjectProperty(:" {workdir}/schema.ofn

# What has rdfs:label and rdfs:comment
grep "AnnotationAssertion(rdfs:label :" {workdir}/schema.ofn
grep "AnnotationAssertion(rdfs:comment :" {workdir}/schema.ofn
```

Cross-check: every name that appears in a `Declaration(...)` line must also appear in both an `AnnotationAssertion(rdfs:label ...)` line and an `AnnotationAssertion(rdfs:comment ...)` line. Missing `rdfs:label` or `rdfs:comment` on any class, data property, or object property → add before proceeding.

### Gate 5 — Backend syntactic validate (API call)

> **Called by `uipath-ontology-authoring`?** Stop after Gate 4 — Gate 5 requires the ontology to exist on the backend. Return the confirmed file paths to the authoring skill; it runs Gate 5 in Step 3b after `uip ont create`.

Runs after the text scans pass (standalone mode only at this point). Always returns HTTP 200 — check `Data.valid`, not exit code.

```bash
uip ont artifacts validate {ontology-name} schema.ofn \
  --type schema \
  --media-type text/owl-functional \
  --file {workdir}/schema.ofn

uip ont artifacts validate {ontology-name} rules.ttl \
  --type constraints \
  --media-type text/turtle \
  --file {workdir}/rules.ttl

uip ont artifacts validate {ontology-name} mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/mapping.yarrrml.yml
```

If `Data.valid` is `false`, read `Data.violations`, fix the file, re-run gates 1–5.

---

## Step 9 — Upload

Upload in strict order. Mapping last — it triggers deployment. Functions and actions are freely reorderable relative to each other but must come after constraints and before mapping.

```bash
# 1 — Schema
uip ont artifacts upsert {ontology-name} schema.ofn \
  --type schema \
  --media-type text/owl-functional \
  --file {workdir}/schema.ofn

# 2 — Constraints
uip ont artifacts upsert {ontology-name} rules.ttl \
  --type constraints \
  --media-type text/turtle \
  --file {workdir}/rules.ttl

# 3 — Functions (if generated)
uip ont artifacts upsert {ontology-name} functions.ttl \
  --type functions \
  --media-type text/turtle \
  --file {workdir}/functions.ttl

# 4 — Actions (one upload per file, if generated)
uip ont artifacts upsert {ontology-name} {actionName}.ttl \
  --type actions \
  --media-type text/turtle \
  --file {workdir}/{actionName}.ttl

# 5 — Mapping (deploy trigger — upload last)
uip ont artifacts upsert {ontology-name} mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/mapping.yarrrml.yml
```

Check each response for `"Code": "ArtifactUpserted"`. Then run `uip ont get {ontology-name}` — expected `state`: `DEPLOYED`.

---

## Common mistakes

- **Never `has{Prop}`** — always `{ClassName}.{propName}` for data properties
- Never use `xsd:string` for numeric fields — use `xsd:decimal` or `xsd:integer`
- Don't add `SubClassOf` for optional relationships — only for "must have" / cardinality constraints
- Don't forget `ObjectPropertyDomain` and `ObjectPropertyRange` for every ObjectProperty
- `schema.ofn` and `rules.ttl` must stay in sync: every OWL restriction needs a matching SHACL constraint
- `skos:altLabel` goes on the Class, not the property
- IRI must be identical across all three artifact files — derive once from the name slug, use verbatim
- Mapping must reference only properties declared in `schema.ofn`; a mismatch causes `BROKEN` state
