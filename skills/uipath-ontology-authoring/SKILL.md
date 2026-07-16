---
name: uipath-ontology-authoring
description: "Use when a user provides an SDD (Software Design Document / domain spec) and wants to create a fully deployed UiPath Ontology: read the SDD, select or create Data Fabric entities, generate OWL 2 QL schema (.ofn) + SHACL constraints (rules.ttl) + YARRRML mapping (mapping.yarrrml.yml), validate all artifacts via the backend, and push the ontology."
when_to_use: "User provides an SDD or domain spec and wants to author/publish an ontology end-to-end; user says 'create an ontology from this SDD', 'generate ontology artifacts', 'deploy ontology', 'wire ontology to Data Fabric', 'generate mapping'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Authoring — SDD to Deployed Ontology

Scope: SDD → silent login check → folder selection → entity matching + creation → domain definition (4 phases) → invoke `uipath-ontology-modeler` (generates schema.ofn + rules.ttl + mapping.yarrrml.yml + validates) → create ontology → push.

**Separation of Concerns** — enforce this throughout: facts go in `schema.ofn`, rules go in USAGE POLICY blocks (mapping + functions), bindings go in `mapping.yarrrml.yml`. Never let domain facts drift into USAGE POLICY, and never let query routing rules drift into `rdfs:comment`. See the modeler's SoC table for the full breakdown.

> **Functions (SPARQL reads):** if the SDD describes query operations, the modeler generates `functions.ttl` (all in one file). See `references/functions-actions.md`.
> **Actions (SQL writes):** if the SDD describes write operations, the modeler generates one `{actionName}.ttl` per action. See `references/functions-actions.md`.

---

## Step 1 — Collect SDD and ontology details

Ask the user for all of the following **in one message**:

| Input | Notes |
|---|---|
| **SDD** | File path, Confluence URL, or pasted text |
| **Ontology name** | Slug: max 64 chars, no `/` (e.g. `clinic`, `ecommerce`) |
| **Display name** | Human label (defaults to `<name>`) |
| **Description** | One sentence |
| **Working directory** | Where to write generated artifact files (defaults to the SDD file's directory, or current directory) |

Read the SDD immediately (Read tool for file paths). Extract only the **class names** from it — just enough to drive entity matching in Phase 2. Do not build the full domain model yet.

### IRI derivation — compute once, use everywhere

As soon as the ontology name is confirmed, derive the IRI:

```
ONTOLOGY_IRI = https://ontology.uipath.com/{name}#
```

`{name}` is the exact slug — verbatim, no transformation. Show it to the user and confirm before generating any files. This value must be **identical** in all three artifact files (`schema.ofn`, `rules.ttl`, `mapping.yarrrml.yml`). It is immutable — renaming the ontology later does not change the IRI.

---

## Phase 0 — Login check (silent)

Run silently — do not interrupt the author if already logged in.

```bash
uip login status --output json
```

- If `loggedIn: true` → continue to Phase 1 without any message.
- If `loggedIn: false` or wrong tenant → prompt the author:

```bash
uip login                          # interactive login
uip login tenant set {tenantName}  # switch tenant if needed
uip login status --output json     # confirm
```

Only block the flow if login is actually needed.

**Cross-folder name collision check** — run after login is confirmed:
```bash
uip ont list --output json
```
Scan the result for any ontology whose name matches `{name}` (case-insensitive):
- **Same folder match** → backend will reject `uip ont create` — tell the user immediately and stop. Ask them to pick a different name.
- **Different folder match** → warn explicitly and wait for confirmation before continuing:

> ⚠ An ontology named `{name}` already exists in folder `{otherFolderKey}` (ID: `{otherOntologyId}`). Creating another with the same name in a different folder means both will share the IRI `https://ontology.uipath.com/{name}#`. Any tool or reasoner that reads both will see the same term IRIs pointing to different data. Confirm you want to proceed, or choose a different name.

---

## Phase 1 — Folder selection

```bash
uip df entities list --output json
```

Extract unique `FolderKey` values from the response (includes both native and federated entities) and present them as a numbered list:

```
Available folders:
  1. HireFlow        (key: 751e18c5-...)
  2. Clinic          (key: b5b4bd01-...)
  3. Ecommerce       (key: 9a3c2d11-...)

Which folder(s) should this ontology scope to? (select one or more)
```

Record the selected folder keys as `SELECTED_FOLDERS`.

> **Wait for folder selection before moving to Phase 2.**

---

## Phase 2 — Entity matching and creation

Now that the SDD class names are known (from Step 1), match each SDD class against the entities in `SELECTED_FOLDERS`. Both native and federated entities are valid sources for an ontology.

```bash
uip df entities list --folder-key {key} --output json
```

Run for each folder in `SELECTED_FOLDERS`. Identify each entity's type from the response: `externalFields: []` → **Native**; `externalFields: [{...}]` → **Federated**. Then build the matching table:

| SDD class | Suggested entity | Type | Match | Entity ID | Folder ID | Action |
|---|---|---|---|---|---|---|
| `Doctor` | `Doctor` | Native | exact | `b5b4bd01-...` | `751e18c5-...` | Use existing |
| `Contact` | `Contact` | Federated | exact | `9f1a2c44-...` | `751e18c5-...` | Use existing (read-only) |
| `Prescription` | — | — | none | — | — | **Create new (native)** |

**Matching rules:** exact name match first; then case-insensitive match; then present candidates if partial match. If no match at all, mark as **Create new (native)**.

**Federated entity rules:**
- **Use existing only** — federated entities connect to external systems (SQL Server, Salesforce, SAP, etc.) via UiPath Integration Service. New federated entities cannot be created via CLI or API — the connection must be set up through the Data Fabric UI. If an SDD class needs a federated entity that doesn't exist yet, stop and tell the user to create it in the portal first.
- **Read-only** — federated entity data is managed by the external system. Mark these classes as `readOnly: true` in CLASS_MAP. SHACL constraints will apply structurally but violations cannot be fixed by writing through the platform.
- **No write actions** — SQL write actions (`{actionName}.ttl`) cannot target federated entities. If the SDD describes write operations on a federated class, flag this to the author — those writes must go through the external system directly.
- **YARRRML mapping is identical** — the mapping syntax for a federated entity (`access: datafabric`, `entityId`, `folderId`) is the same as native. The FQS runtime handles the federation transparently. Functions (SPARQL reads) work with federated entities.

**How federated entity connections work:**
A federated entity is backed by an external data source configured in the Data Fabric UI:
1. An Integration Service connection is created for the external system (e.g. SQL Server, Salesforce)
2. The federated entity schema is defined in the portal, mapped to a table or object in that system
3. Once set up, the entity appears in `entities list` with `externalFields` populated and is queryable through FQS

**For each "Create new (native)" row:**
- Propose a field schema based on the data properties the SDD describes for that class
- Show the proposed schema to the author and get explicit confirmation
- Invoke the `data-fabric` skill to create the entity
- Record the returned `entityId` and `folderId`

> **Field name alignment:** entity field names created here are preliminary. After Phase 4 finalizes all `{ClassName}.{propName}` camelCase names, check that each created entity's field names match what the YARRRML mapping will use as `$(column)` references. If any names differ, update the entity schema before the modeler generates the mapping in Step 2.

Record the completed mapping:
```
CLASS_MAP:
  {ClassName}: entityId={uuid}  folderId={FOLDER_KEY}  [readOnly: true]  ← federated only
```

> **Wait for CLASS_MAP confirmation before moving to Phase 3.**

---

## Phase 3 — Define business concepts

Extract all classes from the SDD. Show this table and wait for confirmation:

| Class | Description (one line) | Synonyms | Subclass of |
|---|---|---|---|
| `Doctor` | Medical practitioner licensed to treat patients | physician, doc | — |
| `Prescription` | A medication order issued by a doctor | script | — |

**SDD → class mapping:**

| SDD phrase | Model construct |
|---|---|
| "a/an X", "each X", "X is a" | New class |
| "also known as / aka / alias" | `skos:altLabel` on the class |
| "Y is a type of / subtype of Z" | `SubClassOf(:Y :Z)` |

> **Wait for explicit user confirmation before moving to Phase 4.**

---

## Phase 4 — Define properties and relationships

Using the confirmed classes from Phase 3, extract all properties and relationships. Show two tables and wait for confirmation:

**Data properties:**

| Class | Property name | XSD type | Required? |
|---|---|---|---|
| `Doctor` | `Doctor.licenseNo` | `xsd:string` | required |
| `Doctor` | `Doctor.active` | `xsd:boolean` | required |
| `Prescription` | `Prescription.status` | `xsd:string` | required |

**Object properties (relationships):**

| Property | From | To | Cardinality | Notes |
|---|---|---|---|---|
| `prescribedBy` | `Prescription` | `Doctor` | exactly one | inverse: `prescribes` |
| `prescriptionFor` | `Prescription` | `Patient` | required | — |

**SDD → property mapping:**

| SDD phrase | Model construct |
|---|---|
| "X has a/an Y" | DataProperty `{X}.{propName}` camelCase |
| "X is linked to / belongs to Y" | ObjectProperty from X to Y |
| "X must have a Y" | ObjectProperty, cardinality = required (`sh:minCount 1`) |
| "each X has exactly one Y" | ObjectProperty, cardinality = exactly one (`sh:minCount 1; sh:maxCount 1`) |
| "X can have many Y AND Y can be shared across many X" (mutual many-to-many) | Junction class mapped to real association table + two ObjectProperties — flag to user, confirm a real association entity exists in Data Fabric |
| "X can have many Y" (one side only, Y owned by one X) | ObjectProperty, no cardinality |
| "inverse of" | `InverseObjectProperties` + `SubObjectPropertyOf` if subproperty |

**Data property naming:** always `{ClassName}.{propName}` camelCase. Never `has{Prop}`.

**XSD types:**

| User says | XSD type |
|---|---|
| text, name, string, code, ID | `xsd:string` |
| price, amount, cost, rate | `xsd:decimal` |
| count, quantity, integer | `xsd:integer` |
| date + time / timestamp | `xsd:dateTime` |
| date only | `xsd:date` |
| true/false, flag, boolean | `xsd:boolean` |
| URL, link | `xsd:anyURI` |

> **Wait for explicit user confirmation before moving to Phase 5.**

---

## Phase 5 — Define labels, descriptions, and synonyms

Using the confirmed classes and properties from Phases 3–4, define the annotations that go into the OWL file. **Present one table at a time** — show class annotations first, wait for confirmation, then data properties, then object properties. This keeps each review manageable for large domains.

**Class annotations:**

| Class | `rdfs:label` | `rdfs:comment` (grain first) | `skos:altLabel` |
|---|---|---|---|
| `Doctor` | `"Doctor"` | `"ONE row per doctor, keyed by Id."` | `"physician"` |
| `Prescription` | `"Prescription"` | `"ONE row per prescription, keyed by Id."` | `"script"` |

**Data property annotations:**

| Property | `rdfs:label` | `rdfs:comment` (pick fact type) | `skos:altLabel` |
|---|---|---|---|
| `Doctor.licenseNo` | `"License #"` | `"Unique license number issued by the medical board."` | — |
| `Prescription.status` | `"Status"` | `"Values: 'Active' \| 'Cancelled' \| 'Filled' (case-sensitive)."` | — |

Fact type forms for `rdfs:comment` — pick the one that fits:

| Fact type | Form |
|---|---|
| Plain meaning | `"{What this field stores.}"` |
| Value domain (enum) | `"Values: 'A' \| 'B' \| 'C' (case-sensitive; copy exactly)."` |
| Code list | `"'A' = meaning \| 'B' = meaning. '{Phrase}' means code IN ('A','B')."` |
| Format / scale | `"Stored 0–1 fraction; multiply by 100 for a percent answer."` |
| NULL with condition | `"NULL for ~N rows. NULLs sort last in DESC — no IS NOT NULL filter for highest; add it only ascending."` |
| Choice set (NumberId) | `"NumberId. 1=Pending, 2=Shipped, 3=Delivered. Compare integers, not labels."` |
| Boolean | `"Compare true/false, never 1/0."` |

**Object property annotations:**

| Property | `rdfs:label` | `rdfs:comment` |
|---|---|---|
| `prescribedBy` | `"Prescribed by"` | `"Each Prescription is prescribed by one Doctor. FK: Prescription.DoctorId -> Doctor.Id. 'Exactly one' is QL-inexpressible; recorded here."` |
| `prescribes` | `"Prescribes"` | `"Inverse of :prescribedBy. A doctor prescribes prescriptions."` |

> **Wait for explicit user confirmation before moving to Phase 6.**

---

## Phase 6 — Verify facts against real data

Spot-check every annotation from Phase 5 that could be wrong if taken from the SDD alone. Use `CLASS_MAP` from Phase 2 for entity and folder IDs — no new lookups needed.

```bash
# Value domains — low-cardinality columns only
uip df records query {entityId} \
  --body '{"selectedFields":["{fieldName}"],"groupBy":["{fieldName}"]}' \
  --folder-key {FOLDER_KEY} --output json

# Grain — check for multiple rows per business parent
uip df records list {entityId} --limit 5 --folder-key {FOLDER_KEY} --output json

# Choice set label map
uip df choice-sets list-values {choiceSetId} --folder-key {FOLDER_KEY} --output json
```

Update any Phase 5 annotation that differs from what the actual data shows. Record the final verified annotation values.

**Greenfield domains (no data yet):** if `records list` returns empty or the entities have no records, skip the query steps. Mark any value-domain or code-list comment as `[UNVERIFIED — confirm when data is loaded]` and proceed. The author can re-run Phase 6 later to replace placeholders once real data exists.

> **Wait for explicit user confirmation of verified annotations before moving to Step 2.**

---

## Step 2 — Generate all artifact files (invoke `uipath-ontology-modeler`)

**Invoke the `uipath-ontology-modeler` skill** and pass it:
- Confirmed domain model from Phases 3–4 (classes, data props, object props, business rules)
- Confirmed annotations from Phase 5, updated with verified facts from Phase 6
- `ONTOLOGY_IRI` from Step 1
- `CLASS_MAP` from Phase 2 (entityId + folderId per class)
- Working directory for output (from Step 1)

The modeler skips its own Steps 1 and 2 — it uses the confirmed domain model from Phases 3–4 directly. It generates each artifact through a build → preview → check → confirm → write flow, presenting each preview to the author before writing. It returns only after the author has confirmed all artifact files and they are written to disk.

The modeler generates:
- `schema.ofn`, `rules.ttl`, `mapping.yarrrml.yml` — always
- `functions.ttl` — if the SDD describes query operations an AI agent should answer
- `{actionName}.ttl` (one per action) — if the SDD describes write/update operations

**Do not proceed to Step 3 until the modeler returns confirmed file paths for all three artifacts:**
```
{workdir}/schema.ofn        ✓ confirmed
{workdir}/rules.ttl         ✓ confirmed
{workdir}/mapping.yarrrml.yml  ✓ confirmed
```

---

## Step 3 — Create ontology and validate via SDK

> **Trigger:** All three artifact files are confirmed and written to disk. Now use the `uip ont` SDK to create the ontology on the backend and validate each file before uploading.

### 3a — Create the ontology

```bash
uip ont create {name} \
  --display-name "{Display Name}" \
  --description "{description}" \
  --folder-key {PRIMARY_FOLDER_KEY}
```

`{PRIMARY_FOLDER_KEY}` is the ontology's home folder. If only one folder was selected in Phase 1, use it. If multiple were selected, ask the author: "Which folder should the ontology itself be registered in?" (the CLASS_MAP handles per-class folder routing; this is only the ontology record's home folder).

Check the response:
- `"Code": "OntologyCreated"` → record the returned `id` (GUID), proceed to 3b
- `409 Conflict` → ontology name already taken; run `uip ont get {name}` to inspect, then either delete it (`uip ont delete {name}`) or choose a different name

### 3b — Backend syntactic validate (Gate 5)

Gates 1–4 ran inside the modeler (text scans, no API). Gate 5 needs the ontology to exist, so it runs here. Validate all three files against the backend parser. The API always returns HTTP 200 — check `Data.valid`, not the exit code.

```bash
uip ont artifacts validate {name} schema.ofn \
  --type schema \
  --media-type text/owl-functional \
  --file {workdir}/schema.ofn
```
Expected: `Data.valid: true`. If false → read `Data.violations`, fix `schema.ofn` in the modeler (re-run modeler steps 3a–3d), then re-validate.

```bash
uip ont artifacts validate {name} rules.ttl \
  --type constraints \
  --media-type text/turtle \
  --file {workdir}/rules.ttl
```
Expected: `Data.valid: true`. If false → fix `rules.ttl` in the modeler (re-run modeler steps 4a–4d), then re-validate.

```bash
# If functions.ttl was generated:
uip ont artifacts validate {name} functions.ttl \
  --type functions \
  --media-type text/turtle \
  --file {workdir}/functions.ttl
```
Expected: `Data.valid: true`. If false → fix `functions.ttl` in the modeler (re-run modeler steps 6a–6d), then re-validate.

```bash
# For each action file generated:
uip ont artifacts validate {name} {actionName}.ttl \
  --type actions \
  --media-type text/turtle \
  --file {workdir}/{actionName}.ttl
```
Expected: `Data.valid: true`. If false → fix the action file in the modeler (re-run modeler steps 7a–7d), then re-validate.

```bash
uip ont artifacts validate {name} mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/mapping.yarrrml.yml
```
Expected: `Data.valid: true`. If false → fix `mapping.yarrrml.yml` in the modeler (re-run modeler steps 5a–5d), then re-validate.

**Do not proceed to Step 4 until all generated files return `Data.valid: true`.**

All five gates summary:

| Gate | Run by | Checks | Pass condition |
|---|---|---|---|
| 1 — QL blacklist | Modeler step 3c | No forbidden OWL 2 QL constructs | Zero hits |
| 2 — Naming | Modeler step 3c | No `has{Prop}` DataProperty names | Zero hits |
| 3 — Cross-file | Modeler step 5c | Every `ont:` term in mapping/rules declared in schema | All found |
| 4 — Annotation | Modeler step 3c | Every declared class and property has `rdfs:label` and `rdfs:comment` | All covered |
| 5 — Backend validate | **Here (step 3b)** | Backend syntactic parse of all generated files | `Data.valid: true` each |

---

## Step 4 — Upload artifacts via SDK

> **Trigger:** All five gates passed. Upload in strict order — mapping last because uploading it transitions the ontology from `DRAFT` to `DEPLOYED`.

### 4a — Upload schema

```bash
uip ont artifacts upsert {name} schema.ofn \
  --type schema \
  --media-type text/owl-functional \
  --file {workdir}/schema.ofn
```
Check response: `"Code": "ArtifactUpserted"` → continue. Any error → fix and re-run step 3b before retrying.

### 4b — Upload constraints

```bash
uip ont artifacts upsert {name} rules.ttl \
  --type constraints \
  --media-type text/turtle \
  --file {workdir}/rules.ttl
```
Check response: `"Code": "ArtifactUpserted"` → continue.

### 4c — Upload functions (if generated)

```bash
uip ont artifacts upsert {name} functions.ttl \
  --type functions \
  --media-type text/turtle \
  --file {workdir}/functions.ttl
```
Check response: `"Code": "ArtifactUpserted"` → continue. Skip this step if functions.ttl was not generated.

### 4d — Upload actions (one per file, if generated)

```bash
uip ont artifacts upsert {name} {actionName}.ttl \
  --type actions \
  --media-type text/turtle \
  --file {workdir}/{actionName}.ttl
```
Repeat for each action file. Check `"Code": "ArtifactUpserted"` on each. Skip if no actions were generated.

### 4e — Upload mapping (deploy trigger)

```bash
uip ont artifacts upsert {name} mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/mapping.yarrrml.yml
```
Check response: `"Code": "ArtifactUpserted"` → mapping upload triggers `DRAFT → DEPLOYED`.

### 4f — Verify deployment

```bash
uip ont get {name}
```

| `state` | Meaning | Action |
|---|---|---|
| `DEPLOYED` | All artifacts accepted, ontology live | Done |
| `BROKEN` | Mapping references a term not in schema | Run `uip ont artifacts list {name}` — find the mismatched `ont:` term, fix `mapping.yarrrml.yml`, re-upload mapping |
| `DRAFT` | Mapping not uploaded yet, or uploaded before schema/rules | Re-upload schema and rules first, then mapping |

---

## Artifact reference

| File | `--type` | Media type | Required for deploy |
|---|---|---|---|
| `schema.ofn` | `schema` | `text/owl-functional` | Yes |
| `rules.ttl` | `constraints` | `text/turtle` | Yes |
| `functions.ttl` | `functions` | `text/turtle` | Optional — generated when SDD describes query operations; freely add/removable without breaking a deployed ontology |
| `{actionName}.ttl` | `actions` | `text/turtle` | Optional, one file per action — generated when SDD describes write operations; freely add/removable |
| `mapping.yarrrml.yml` | `mapping` | `application/yaml` | Yes — upload last, triggers `DRAFT → DEPLOYED` |

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `422` on validate or upload | Malformed OWL or Turtle | Read `Data.violations`; fix syntax |
| `409` on create | Ontology name taken | `uip ont get {name}` to check; rename or delete first |
| `BROKEN` after deploy | Mapping references undeclared property | Check every `ont:` term in mapping exists in `schema.ofn` |
| `DRAFT` after mapping upload | schema or constraints not uploaded first | Upload schema and rules, then re-upload mapping |
| `Not Found` on any `uip ont` command | Datafabric service not reachable | Backend not deployed on this environment |
