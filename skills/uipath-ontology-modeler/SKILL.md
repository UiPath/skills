---
name: uipath-ontology-modeler
description: "Use when the user describes a domain in a prompt and wants to generate ontology artifact files ({name}.ofn, {name}-constraints.ttl, {name}-mapping.yarrrml.yml, {name}-functions.ttl, actions). No SDD required — a plain description of classes, fields, and relationships is enough. Also invoked by uipath-ontology-authoring as the artifact-generation step."
when_to_use: "User describes a domain in plain language ('I have Orders, Customers, Products…') with no SDD or document. Also use for: regenerating a single artifact, or when the authoring skill passes a confirmed domain model and CLASS_MAP. If the user has an SDD file or document, use uipath-ontology-authoring instead — it reads the SDD then calls this skill."
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
- `{name}.ofn` — OWL 2 QL Functional Syntax (classes, properties, labels, descriptions)
- `{name}-constraints.ttl` — SHACL constraints (one shape per business rule)
- `{name}-mapping.yarrrml.yml` — YARRRML binding (class → entity, property → column, FK joins)
- `{name}-functions.ttl` — SPARQL read functions (optional — only if the domain includes query operations)
- `{name}-{actionName}.ttl` — SQL write actions (optional — one file per action)

Steps 3–7: build → preview → check → confirm → write for each artifact. Nothing is written to disk before you confirm it. Step 8 validates all artifacts simultaneously and upserts in tiers. Step 9 runs the LLM semantic judge across all artifacts in parallel. Step 10 runs final cross-artifact gate checks. Step 11 deploys.

> **Called by `uipath-ontology-authoring`?** Skip the ontology creation sub-step at the end of Step 1 (authoring creates the ontology before invoking you) and skip Steps 1 and 2 domain-gathering — the caller already collected the ontology name, IRI, confirmed domain model (Phases 3–4), confirmed annotations (Phases 5–6), and `CLASS_MAP`. Start at Step 3 directly with those inputs. Steps 8 (parallel validate + tiered upsert) and 9 (Gf semantic eval) run normally — mapping is validated but not upserted. Skip Step 11 — return the confirmed file paths to the authoring skill, which uploads the mapping as the final deploy trigger.

---

## Design Principle — Separation of Concerns

Each artifact owns exactly one type of information. Never mix them across files:

| Type | What it is | Where it lives |
|---|---|---|
| **Fact** | What a value means, what a class is, grain, value domain, FK provenance | `rdfs:comment` in `{name}.ofn` |
| **Constraint** | Business rule that must hold (must have, must be one) | `{name}-constraints.ttl` SHACL shape |
| **Rule** | How to query, join routing, LIMIT/DISTINCT discipline | USAGE POLICY block in `{name}-mapping.yarrrml.yml` |
| **Binding** | Class → entity, property → column, object property → FK join condition | `{name}-mapping.yarrrml.yml` source/po blocks |
| **Function fact** | What a function returns, when to use it vs other functions | `rdfs:comment` in `{name}-functions.ttl` |
| **Function rule** | Which function answers which question type, query output discipline | USAGE POLICY block in `{name}-functions.ttl` |
| **Function binding** | Which ontology terms the SPARQL traverses to answer the question | `ont:statement` in `{name}-functions.ttl` |
| **Action fact** | What a SQL action changes, what params it takes | `rdfs:comment` in `{name}-{actionName}.ttl` |
| **Action binding** | Which entity table and field columns the SQL writes | `{{Entity.field}}` in `ont:statements` |

**What this means in practice — do not:**
- Put query routing rules in `rdfs:comment` — they belong in USAGE POLICY
- Put FK join logic as OWL axioms in `{name}.ofn` — note FK provenance as a fact in `rdfs:comment`, implement the join in mapping
- Put value domain meanings in USAGE POLICY — they belong in `rdfs:comment`
- Put entity IDs or column names in `{name}.ofn` — they belong in mapping
- Explain what status codes mean inside a SPARQL rdfs:comment — that fact is already in `{name}.ofn`

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

**File name derivation — compute once, use everywhere:**

Derive artifact file names from the ontology name slug at the same time as the IRI. Do not use fixed names:

```
{name}.ofn                       ← OWL 2 QL schema
{name}-constraints.ttl           ← SHACL constraints
{name}-mapping.yarrrml.yml       ← YARRRML mapping
{name}-functions.ttl             ← SPARQL functions (if needed)
{name}-{actionName}.ttl          ← SQL action files (one per action, if needed)
```

Show the file list once so the user can verify before any file is written.

**Login check (silent):**
```bash
uip login status --output json
```
If `Data.Status === "Logged in"` → continue without interrupting. If `Data.Status !== "Logged in"` → prompt for login before the entity list step.

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

**Ontology creation (before artifact generation):**

Once CLASS_MAP is confirmed, determine `PRIMARY_FOLDER_KEY` — the folder the ontology record itself is registered in. Use the folder key shared by the entities in CLASS_MAP. If entities span multiple folders, ask the user: "Which folder should the ontology record itself be registered in?"

Then create the ontology stub so backend validation can run inline during Steps 3–7:

```bash
uip ont create {name} --display-name "{name}" --folder-key {PRIMARY_FOLDER_KEY} --output json
```

- `"Code": "OntologyCreated"` → record the returned `id`, continue.
- `409 Conflict` → name already taken (collision check already passed — unexpected); show the error and stop for user guidance.

> Do **not** run this step when called by `uipath-ontology-authoring` — the authoring skill creates the ontology before invoking the modeler.

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

## Step 3 — Generate {name}.ofn

Follow [owl-patterns.md](owl-patterns.md) exactly. This step has four sub-steps: build → preview → W3C check → confirm → write.

---

### 3a — Build the OFN content

Construct the full file content in memory (do not write yet). Cover all three requirements:

**1. Properties and relationships — types and cardinality**

- DataProperty: `DataPropertyDomain` + `DataPropertyRange(xsd:{type})` for every property from the confirmed domain model
- ObjectProperty: `ObjectPropertyDomain` + `ObjectPropertyRange` for every relationship
- `InverseObjectProperties` for inverse pairs; `SubObjectPropertyOf` for sub-properties
- Cardinality is QL-inexpressible as axioms — express in `rdfs:comment` text and enforce via SHACL in {name}-constraints.ttl

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

> **Confirm {name}.ofn?** ({N} classes, {N} data properties, {N} object properties — W3C checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/{name}.ofn`.
On revision request, update the draft and return to step 3b.

---

## Step 4 — Generate {name}-constraints.ttl

Follow [shacl-patterns.md](shacl-patterns.md) exactly. Same build → preview → check → confirm → write flow as Step 3.

---

### 4a — Build the SHACL content

Construct the full file content in memory. One `sh:NodeShape` per business rule from the confirmed domain model.

**Structure rules:**
- Prefixes: `ont:`, `rdfs:`, `sh:`, `shape:`, `xsd:`
- Shape name: `shape:{ClassName}Must{BehaviorName}` (e.g. `shape:doctorMustBeLicensed`)
- Each shape: `rdfs:label` (human description) + `sh:message` (violation sentence) + `sh:targetClass` + one or more `sh:property` blocks
- Property path always `ont:{ClassName}.{propName}` — must match exactly what is declared in `{name}.ofn`
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
SHACL draft: {ontology-name} {name}-constraints.ttl

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

### 4c — SHACL consistency check (against {name}.ofn)

Verify the SHACL draft is consistent with the already-confirmed `{name}.ofn`:

**Check 1 — Property path alignment:**
Every `sh:path` value in the draft must match a `Declaration(DataProperty(:…))` or `Declaration(ObjectProperty(:…))` in `{name}.ofn`. Any mismatch → `BROKEN` state after deploy.

**Check 2 — Target class alignment:**
Every `sh:targetClass` must match a `Declaration(Class(:…))` in `{name}.ofn`.

**Check 3 — Coverage:**
Every business rule from the confirmed model has a shape. No business rule is missing a shape.

Report:

```
SHACL consistency checks:
  ✓ Property paths — all sh:path values declared in {name}.ofn
  ✓ Target classes — all sh:targetClass values declared in {name}.ofn
  ✓ Coverage — all {N} business rules have a shape
```

Fix any issues in the draft before proceeding.

---

### 4d — Confirm and write

> **Confirm {name}-constraints.ttl?** ({N} shapes covering {N} business rules — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/{name}-constraints.ttl`.
On revision request, update the draft and return to step 4b.

---

## Step 5 — Generate {name}-mapping.yarrrml.yml

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
  - `po:` — in this order:
    1. Type triple: `[a, ont:{ClassName}]`
    2. One pair per data property: `[ont:{ClassName}.{propName}, $({columnName})]` (with xsd type as third element for non-string types)
    3. **Object property relationship triples — mandatory for every FK relationship declared in `{name}.ofn`.**

**Object property relationship triples (always required):**

For every ObjectProperty declared in `{name}.ofn` where the child class holds a FK column pointing to the parent class, add a relationship binding block in the **child** class `po:` section — after all data property pairs:

```yaml
- p: ont:{objectPropertyName}
  o:
    mapping: {ParentClassName}
    condition:
      function: equal
      parameters:
        - - str1
          - $({FKColumn})       # FK column in the child entity
        - - str2
          - $({PKColumn})       # PK column in the parent entity (usually Id)
```

- `ont:{objectPropertyName}` must exactly match the ObjectProperty IRI declared in `{name}.ofn` (e.g. `ont:email_forInvoiceClaim`)
- `mapping:` must reference the parent class mapping key (e.g. `InvoiceClaim`)
- This block must appear for **every** ObjectProperty whose domain is this class — no FK relationship may be left as a plain data property binding only
- A class with N FK columns pointing to N parent classes needs N relationship binding blocks

Every `ont:` term used in the mapping must be declared in `{name}.ofn`. Column names are case-sensitive — use the exact field name as it appears in the Data Fabric entity.

**This file must be uploaded last** — uploading the mapping flips the ontology from `DRAFT` to `DEPLOYED`.

---

### 5b — Show draft summary to user

```
Mapping draft: {ontology-name} {name}-mapping.yarrrml.yml

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

### 5c — Mapping consistency check (against {name}.ofn)

**Check 1 — Term coverage:**
Every `ont:` predicate in the mapping must be declared in `{name}.ofn`. Extract all `ont:` terms from the draft and compare against `Declaration(…)` lines in `{name}.ofn`.

**Check 2 — Column name plausibility:**
Every `$(columnName)` must correspond to a field that exists in the Data Fabric entity. Cross-check against the entity field names collected during Phase 2 entity matching.

**Check 3 — All classes mapped:**
Every class in the confirmed domain model has a mapping block. No class left unmapped.

**Check 4 — Object property relationship binding completeness:**
Every ObjectProperty declared in `{name}.ofn` must have a corresponding `p: / o: mapping: / condition:` block in the child class mapping. For each `Declaration(ObjectProperty(:…))` in `{name}.ofn`, verify a `p: ont:{objectPropertyName}` entry exists in the correct class `po:` section. A FK stored as a plain data property binding only (no relationship block) is a gap — flag it and add the missing block.

Report:

```
Mapping consistency checks:
  ✓ Term coverage — all ont: predicates declared in {name}.ofn
  ✓ Column names — all $(…) fields match entity schema
  ✓ Class coverage — all {N} classes have a mapping block
  ✓ Relationship bindings — all {N} ObjectProperties have a p:/o:/condition: block in the child class mapping
```

Fix any issues in the draft before proceeding.

---

### 5d — Confirm and write

> **Confirm {name}-mapping.yarrrml.yml?** ({N} classes mapped — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

Wait for explicit confirmation. On confirmation, write `{workdir}/{name}-mapping.yarrrml.yml`.
On revision request, update the draft and return to step 5b.

---

## Step 6 — Generate {name}-functions.ttl (skip if SDD has no query operations)

Query operations are natural-language questions the SDD says the system (or an AI agent) should answer from the ontology data: "how many X are in state Y", "show me all X with their Y", "which X has the most Y", "list X grouped by Z". If the SDD describes dashboards, summaries, counts, or searches, those are query operations. If the SDD is purely about data structure with no query requirements, skip this step.

If no query operations → skip this step and proceed to Step 7. Otherwise follow [functions-patterns.md](functions-patterns.md) and the same build → preview → check → confirm → write flow.

---

### 6a — Build functions content

Identify all natural-language questions from the SDD that an AI agent should answer from the ontology. Build the full file content in memory before writing.

**Separation of concerns inside {name}-functions.ttl:**
- **Fact** (what this function returns, when to use it) → `rdfs:comment` on each function
- **Rule** (which function to call for which question, LIMIT/DISTINCT discipline) → USAGE POLICY header block
- **Binding** (which `ont:` terms the SPARQL traverses) → `ont:statement`

For each function:
- **Name** — `ont:{camelCaseFunctionName}` (verb phrase: `countPrescriptionsByStatus`, `listPrescriptionsWithDoctorAndPatient`)
- **Label** — short human phrase
- **Comment** — per-function fact: what it returns, whether it produces counts or individual rows, what params it needs; do NOT put routing rules here — those go in USAGE POLICY
- **SPARQL SELECT** — on `ont:statement`; prefixed with `PREFIX ont: <https://ontology.uipath.com/{name}#>`; for equality lookups bind the parameter as an unbound triple variable (`; ont:Prop ?param`); for comparisons (`<`, `>`, `!=`) bind via `FILTER (?field < ?param)`
- **Parameters** — only if needed; omit `fno:expects` entirely when the function takes none; optional params add `ont:required false ; ont:default "{val}"`
- **Returns** — always declare `fno:returns ( ont:ret.{fn}.{var} … )` and a corresponding `ont:ret.*` block (`a fno:Output ; ont:returnName "…" ; ont:returnType "xsd:…"`) for every projected SELECT variable

**File structure** — all functions in a single file:
1. Prefix declarations: `fno:`, `ont:`, `rdfs:`
2. USAGE POLICY comment block — routing rules and output discipline (≤30 non-empty lines; see functions-patterns.md)
3. For each function: `ont:{functionName}` block, then `ont:param.*` blocks, then `ont:ret.*` blocks immediately after

---

### 6b — Show draft summary

```
Functions draft: {ontology-name} {name}-functions.ttl

Functions ({N}):
  ont:countPrescriptionsByStatus
    label: "Count prescriptions in a given status"
    SPARQL: SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:Prescription ; ont:Prescription.status ?status }
    params:  status (xsd:string, required)
    returns: n (xsd:integer)

  ont:listPrescriptionsWithDoctorAndPatient
    label: "List prescriptions with their doctor and patient"
    SPARQL: SELECT ?medication ?status ?doctorName ?patientName WHERE { ... (3-way join) }
    params:  none
    returns: medication (xsd:string), status (xsd:string), doctorName (xsd:string), patientName (xsd:string)
```

---

### 6c — Functions consistency check (on draft)

**Check 1 — Property paths:** every `ont:{ClassName}.{propName}` used in any SPARQL WHERE clause must be declared in `{name}.ofn`.

**Check 2 — Class references:** every `a ont:{ClassName}` in SPARQL must be a declared class in `{name}.ofn`.

**Check 3 — Object properties:** every `ont:{verbPhrase}` used as a property in SPARQL must be declared in `{name}.ofn`.

**Check 4 — Parameter binding:** every `?paramName` that appears as an unbound input variable in the WHERE clause (whether in a triple pattern or a `FILTER`) must have a matching entry in `fno:expects` and a corresponding `ont:param.*` block.

**Check 5 — Return contract (both directions):**
- Forward: every variable projected in `SELECT ?x ?y …` must have a matching `ont:ret.*` block where `ont:returnName` equals the variable name (without `?`).
- Reverse: every `ont:returnName` value in every `ont:ret.*` block must correspond to a variable actually projected in the SELECT. No orphaned return nodes allowed.

Report:
```
Functions checks:
  ✓ Property paths — all ont: DataProperty terms declared in {name}.ofn
  ✓ Class references — all ont: class terms declared in {name}.ofn
  ✓ Object properties — all ont: ObjectProperty terms declared in {name}.ofn
  ✓ Parameter binding — all unbound variables (triple and FILTER) have matching fno:expects entries
  ✓ Return contract (forward) — all projected SELECT variables have matching fno:returns / fno:Output nodes
  ✓ Return contract (reverse) — all ont:returnName values match a projected SELECT variable
```

Fix any issues in the draft before proceeding.

---

### 6d — Confirm and write

> **Confirm {name}-functions.ttl?** ({N} functions — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

On confirmation, write `{workdir}/{name}-functions.ttl`.
On revision request, update the draft and return to step 6b.

---

## Step 7 — Generate action files (skip if SDD/PDD has no write operations)

If the SDD/PDD does not describe write/update operations, skip this step. One file per action — the file name IS the action's identity. Generate one action at a time through the full build → preview → check → confirm → write cycle.

If the PDD has a **Write Operations (Actions)** section with the structured action table format (see [action-table-contract.md](action-table-contract.md)), read each action row directly — no interpretation needed. The 7 fields (Name, Entity, Operation, Description, Target Fields, Identifier, Inputs) map 1:1 to TTL constructs.

---

### 7a — Build one action

For each write operation from the SDD/PDD:

- **Name** — `ont:{camelCaseActionName}` (verb phrase: `updatePrescriptionStatus`, `createPatientRecord`). When PDD has a `Name` field, use it directly; otherwise derive from the operation description.
- **File name** — `{name}-{actionName}.ttl` (e.g. for ontology `clinic` and action `updatePrescriptionStatus` → `clinic-updatePrescriptionStatus.ttl`)
- **Label** — short human phrase (from PDD action title when available)
- **Comment** — what it changes, what params it takes, whether it modifies one row or many. This is what AI agents read to select the right action — be specific, not generic. Source from PDD `Description` field when available, but ensure it answers all three questions.
- **SQL** — on `ont:statements ( "..." )` (plural, always a list even for a single statement)
  - `{{EntityName}}` — the ontology class this action writes to. Must match a `Declaration(Class(:...))` in schema.ofn. Never use real table names.
  - `{{EntityName.fieldName}}` — the property being read or written in the SQL. Must match a `Declaration(DataProperty(:...))` in schema.ofn. The runtime resolves these to physical columns via the mapping.
  - `WHERE {{Entity.identifier}} = :id` — how the target row is identified. Typically the entity's primary key field.
  - `:paramName` — bound parameter from the caller. Must match `ont:paramName` in the parameter block exactly.
- **Parameters** — `fno:expects` + `ont:param.*` block per parameter (from PDD `Inputs` field)
- **Output** — `fno:returns` with `rowsAffected` output is **mandatory**. Use `ont:paramName` (not `ont:returnName`) on the output node — the parser uses the same method for inputs and outputs.

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

**Check 2 — Field references:** every `{{EntityName.fieldName}}` must match a `{ClassName}.{propName}` declared in `{name}.ofn` (e.g. `{{Prescription.status}}` → `ont:Prescription.status`).

**Check 3 — Parameter alignment:** every `:paramName` in the SQL must have a matching `ont:param.{actionName}.{paramName}` block.

Report:
```
Action checks (updatePrescriptionStatus.ttl):
  ✓ Entity references — Prescription declared in {name}.ofn
  ✓ Field references — Prescription.status, Prescription.id declared in {name}.ofn
  ✓ Parameter alignment — id and newStatus have matching param blocks
```

---

### 7d — Confirm and write

> **Confirm {name}-{actionName}.ttl?** (SQL action, {N} params — consistency checks passed)
> Reply `yes` to write the file, or describe any changes needed.

On confirmation, write `{workdir}/{name}-{actionName}.ttl`.

Repeat steps 7a–7d for each remaining action in the SDD.

---

## Step 8 — Parallel G5 validate + tiered upsert

All artifact files are confirmed and on disk. Fire all backend validation calls simultaneously — `validate` checks file content syntactically and has no cross-artifact dependency. Issue all calls in parallel, collect all results, then handle any failures one at a time.

**Issue all validate calls simultaneously:**

```bash
uip ont artifact validate {name} {name}.ofn \
  --type schema --media-type text/owl-functional \
  --file {workdir}/{name}.ofn --output json

uip ont artifact validate {name} {name}-constraints.ttl \
  --type constraints --media-type text/turtle \
  --file {workdir}/{name}-constraints.ttl --output json

uip ont artifact validate {name} {name}-mapping.yarrrml.yml \
  --type mapping --media-type application/yaml \
  --file {workdir}/{name}-mapping.yarrrml.yml --output json

# If functions were generated:
uip ont artifacts validate {name} {name}-functions.ttl \
  --type functions --media-type text/turtle \
  --file {workdir}/{name}-functions.ttl --output json

# If actions were generated (one call per action file):
uip ont artifacts validate {name} {name}-{actionName}.ttl \
  --type actions --media-type text/turtle \
  --file {workdir}/{name}-{actionName}.ttl --output json
```

Always HTTP 200 — check `Data.valid` on each response.

**Show batch results:**

```
G5 validation results:
  ✓ {name}.ofn
  ✓ {name}-constraints.ttl
  ✗ {name}-mapping.yarrrml.yml
    Violations: {Data.violations}
  ✓ {name}-functions.ttl
  ✓ {name}-{actionName}.ttl
```

**Fix failures one at a time:**

For each `✗` file:

```
Backend validation failed — {filename}
Violations:
{Data.violations}

Attempt auto-fix? [yes / no]
(If no: fix manually then reply `done`. On `done`, re-validate.)
```

Auto-fix loop (max 3 attempts):
1. Read `{workdir}/{filename}` + violations
2. Generate corrected content in memory
3. Re-run local gates for this artifact type (3c for schema / 4c for constraints / 5c for mapping / 6c for functions / 7c for actions)
4. Show change summary — one sentence per violation addressed
5. Ask: `Apply this fix? [yes / no]`
   - `yes` → overwrite file, re-validate only that file
   - `no` → show violations, user chooses: try again / fix manually

After 3 failed attempts: "Auto-fix exhausted 3 attempts. Please fix `{filename}` manually, then reply `done`." Wait for `done`, re-validate once.

**Tiered upsert after all files pass:**

Backend validation of constraints, functions, and actions requires the schema to be live — it resolves `ont:` terms against the uploaded schema. Schema must be upserted (Tier 1) before Tier 2 validate calls return meaningful results.

```bash
# Tier 1 — schema first (wait for ArtifactUpserted before proceeding)
uip ont artifact upsert {name} {name}.ofn \
  --type schema --media-type text/owl-functional \
  --file {workdir}/{name}.ofn --output json
```

`"Code": "ArtifactUpserted"` → schema live on backend. Then upsert remaining non-mapping artifacts simultaneously:

```bash
# Tier 2 — parallel (fire simultaneously, wait for all)
uip ont artifact upsert {name} {name}-constraints.ttl \
  --type constraints --media-type text/turtle \
  --file {workdir}/{name}-constraints.ttl --output json

# If functions were generated:
uip ont artifact upsert {name} {name}-functions.ttl \
  --type functions --media-type text/turtle \
  --file {workdir}/{name}-functions.ttl --output json

# If actions were generated:
uip ont artifact upsert {name} {name}-{actionName}.ttl \
  --type actions --media-type text/turtle \
  --file {workdir}/{name}-{actionName}.ttl --output json
```

Mapping is **not upserted here** — held as the deploy trigger until after Step 10. Show summary:

```
G5 upsert complete:
  ✓ {name}.ofn — uploaded
  ✓ {name}-constraints.ttl — uploaded
  ✓ {name}-functions.ttl — uploaded  (if generated)
  ✓ {name}-{actionName}.ttl — uploaded  (if generated)
  ⏸ {name}-mapping.yarrrml.yml — validated, held
```

**If upsert fails partway through (partial upload):**

Run `uip ont artifact list {name} --output json` to see which artifacts are already live. For each artifact already showing in the list, skip its upsert command. Re-run only the upsert commands for the remaining artifacts, then continue to Step 9.

---

## Step 9 — Parallel Gf semantic eval

All non-mapping artifacts are upserted. Run the LLM semantic judge on all artifacts simultaneously — no API calls, reasoning only against the confirmed domain model from Step 2.

**Run all Gf checks in parallel:**

| Artifact | Checks |
|---|---|
| `{name}.ofn` | Class + property completeness, XSD types match domain model, every `rdfs:comment` opens with grain statement or correct fact type form, no phantom terms |
| `{name}-constraints.ttl` | Every "must have" / "required" business rule has a shape; no invented constraints |
| `{name}-mapping.yarrrml.yml` | Every class has mapping block with correct `entityId`/`folderId`; column bindings plausible vs XSD type; FK join direction matches `rdfs:comment` FK provenance; USAGE POLICY references only existing terms |
| `{name}-functions.ttl` | Every described query op has a function; SPARQL traverses correct `ont:` terms; `fno:returns` match projected SELECT variables |
| `{name}-{actionName}.ttl` | SQL targets correct entity and columns; parameters match description; `rdfs:comment` accurate |

**Show batch results:**

```
Gf semantic eval results:
  {name}.ofn
    ✓ Class coverage — all {N} classes present
    ✓ Property coverage — all data and object properties correctly typed
    ✗ rdfs:comment — ont:Prescription.refillCount missing grain context
  {name}-constraints.ttl
    ✓ Coverage — all {N} business rules have a shape
  {name}-mapping.yarrrml.yml
    ✓ Class coverage — all {N} classes have mapping blocks
    ✓ entityId/folderId — all match CLASS_MAP
  {name}-functions.ttl
    ✓ Coverage — all {N} described query operations have a function
  {name}-{actionName}.ttl
    ✓ SQL target — correct entity and columns
```

**Fix failures one at a time:**

For each `✗` artifact: offer agent fix. Fix loop: generate corrected content → re-run local gates for that artifact type → re-run G5 validate + upsert for that artifact only → re-run Gf for that artifact only. Max 3 attempts per artifact.

All checks `✓` across all artifacts → proceed to Step 10.

---

## Step 10 — Gate-check all files (mandatory, all gates must pass)

Run every gate in order. Do not upload mapping until all pass. Fix and re-run on any failure.

> **Relationship to prior checks:** Steps 3c–7c scanned *draft* content before writing. Step 8 ran backend syntactic validation and upserted all artifacts. Step 9 ran per-artifact semantic eval. Step 10 runs on *written files*: Gates 1–4 are a final text-scan sanity pass; Gate 6 is the definitive cross-artifact semantic consistency check (needs all files to exist simultaneously).
>
> **Run order:** G1 → G2 → G3 → G4 → G6. Stop at first failure; fix and re-run from that gate.

### Gate 1 — QL blacklist scan (text scan, no API needed)

Grep `{name}.ofn` for forbidden OWL 2 QL constructs before touching the API:

```bash
grep -E "ExactCardinality|MinCardinality|MaxCardinality|AllValuesFrom|HasValue|ObjectOneOf|DataOneOf|ObjectUnionOf|DataUnionOf|ObjectHasSelf|FunctionalObjectProperty|FunctionalDataProperty|InverseFunctional|TransitiveObjectProperty|HasKey" {workdir}/{name}.ofn
```

Zero hits required. Any match → fix in {name}.ofn (move constraint to `rdfs:comment` text), re-run.

### Gate 2 — Naming convention scan (text scan)

```bash
grep -E "DataProperty\(:has[A-Z]" {workdir}/{name}.ofn
```

Zero hits required. Any `has{Prop}` DataProperty name → rename to `{ClassName}.{propName}`, update all three files.

### Gate 3 — Cross-file consistency (text scan)

Every `ont:` term referenced in `{name}-mapping.yarrrml.yml` and every `sh:path` in `{name}-constraints.ttl` must be declared in `{name}.ofn`.

```bash
# Extract ont: terms from mapping (data/object properties used)
grep -oE "ont:[A-Za-z0-9._]+" {workdir}/{name}-mapping.yarrrml.yml | sort -u

# Extract sh:path values from rules
grep -oE "ont:[A-Za-z0-9._]+" {workdir}/{name}-constraints.ttl | sort -u

# Check each against {name}.ofn declarations
grep "Declaration(" {workdir}/{name}.ofn
```

Every term found in mapping or rules must appear in a `Declaration(DataProperty(:...))` or `Declaration(ObjectProperty(:...))` in the schema. Any mismatch → fix before proceeding (a mismatch causes `BROKEN` state after deploy).

### Gate 4 — Annotation completeness (text scan)

Every declared class, data property, and object property must have both `rdfs:label` and `rdfs:comment`:

```bash
# What is declared
grep "Declaration(Class(:" {workdir}/{name}.ofn
grep "Declaration(DataProperty(:" {workdir}/{name}.ofn
grep "Declaration(ObjectProperty(:" {workdir}/{name}.ofn

# What has rdfs:label and rdfs:comment
grep "AnnotationAssertion(rdfs:label :" {workdir}/{name}.ofn
grep "AnnotationAssertion(rdfs:comment :" {workdir}/{name}.ofn
```

Cross-check: every name that appears in a `Declaration(...)` line must also appear in both an `AnnotationAssertion(rdfs:label ...)` line and an `AnnotationAssertion(rdfs:comment ...)` line. Missing `rdfs:label` or `rdfs:comment` on any class, data property, or object property → add before proceeding.

### Gate 6 — Cross-artifact semantic consistency (LLM judge)

Runs after Gates 1–4 pass. All files exist — judge semantic alignment across them against the confirmed domain model.

**Checks:**
1. **Schema-mapping alignment:** for each data property in `{name}.ofn`, its `rdfs:comment` fact type is consistent with the column it binds to in `{name}-mapping.yarrrml.yml` (e.g. a `"Values: 'Active' | 'Cancelled'"` comment should not map to a numeric column)
2. **Business rule completeness:** every business rule mentioned in the original domain description has a shape in `{name}-constraints.ttl` — none slipped through
3. **Function coverage:** every query operation from the domain description has a function in `{name}-functions.ttl` (skip if no functions generated)
4. **No missing domain concept:** every class, property, and relationship from the domain description is represented across all artifacts
5. **USAGE POLICY coherence:** routing rules in the mapping and functions USAGE POLICY blocks reference only terms and functions that actually exist in the artifact files

**Verdict format:**
```
Gate 6 — Cross-artifact semantic consistency
  ✓ Schema-mapping alignment — all data property types consistent with bound columns
  ✓ Business rule completeness — all {N} rules enforced
  ✗ Missing concept — "Prescription.refillCount" described in domain, not present in schema or mapping
  ✗ USAGE POLICY orphan — routing rule references ont:listExpiredPrescriptions but no such function exists
```

On any `✗`: offer agent fix per affected artifact. Fix loop per artifact: generate corrected content → re-run local gates → re-run G5 (validate → upsert) → re-run Gf for that artifact → re-run Gate 6 in full after all fixes applied.

All checks `✓` → proceed to Step 11.

---

## Step 11 — Deploy (mapping upload)

All artifacts except the mapping were upserted in Step 8 (tiered upsert). The mapping is uploaded last because uploading it triggers `DRAFT → DEPLOYED`.

```bash
uip ont artifact upsert {ontology-name} {name}-mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/{name}-mapping.yarrrml.yml \
  --output json
```

Check response: `"Code": "ArtifactUpserted"`. Then verify:

```bash
uip ont get {ontology-name}
```

Expected `state`: `DEPLOYED`. If `BROKEN` → a mapping term is not declared in schema; check every `ont:` term in `{name}-mapping.yarrrml.yml` against `{name}.ofn` and re-upload mapping. If `DRAFT` → schema or constraints were not uploaded yet; check Steps 3e and 4e completed successfully.

---

## Common mistakes

- **Never `has{Prop}`** — always `{ClassName}.{propName}` for data properties
- Never use `xsd:string` for numeric fields — use `xsd:decimal` or `xsd:integer`
- Don't add `SubClassOf` for optional relationships — only for "must have" / cardinality constraints
- Don't forget `ObjectPropertyDomain` and `ObjectPropertyRange` for every ObjectProperty
- `{name}.ofn` and `{name}-constraints.ttl` must stay in sync: every OWL restriction needs a matching SHACL constraint
- `skos:altLabel` goes on the Class, not the property
- IRI must be identical across all three artifact files — derive once from the name slug, use verbatim
- Mapping must reference only properties declared in `{name}.ofn`; a mismatch causes `BROKEN` state
