---
name: uipath-ontology-authoring
description: "Use when a user provides an SDD (Software Design Document / domain spec) and wants to create a fully deployed UiPath Ontology: read the SDD, select or create Data Fabric entities, generate OWL 2 QL schema (.ofn) + SHACL constraints ({name}-constraints.ttl) + YARRRML mapping ({name}-mapping.yarrrml.yml), validate all artifacts via the backend, and push the ontology."
when_to_use: "User provides an SDD or domain spec and wants to author/publish an ontology end-to-end; user says 'create an ontology from this SDD', 'generate ontology artifacts', 'deploy ontology', 'wire ontology to Data Fabric', 'generate mapping'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
user-invocable: true
---

# UiPath Ontology Authoring — SDD to Deployed Ontology

Scope: SDD → silent login check → folder selection → entity matching + creation → domain definition (4 phases) → invoke `uipath-ontology-modeler` (generates {name}.ofn + {name}-constraints.ttl + {name}-mapping.yarrrml.yml + validates) → create ontology → push.

**Separation of Concerns** — enforce this throughout: facts go in `{name}.ofn`, rules go in USAGE POLICY blocks (mapping + functions), bindings go in `{name}-mapping.yarrrml.yml`. Never let domain facts drift into USAGE POLICY, and never let query routing rules drift into `rdfs:comment`. See the modeler's SoC table for the full breakdown.

> **Functions (SPARQL reads):** if the SDD describes query operations, the modeler generates `{name}-functions.ttl` (all in one file). See `references/functions-actions.md`.
> **Actions (SQL writes):** if the SDD describes write operations, the modeler generates one `{name}-{actionName}.ttl` per action. See `references/functions-actions.md`.

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

`{name}` is the exact slug — verbatim, no transformation. Show it to the user and confirm before generating any files. This value must be **identical** in all three artifact files (`{name}.ofn`, `{name}-constraints.ttl`, `{name}-mapping.yarrrml.yml`). It is immutable — renaming the ontology later does not change the IRI.

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

If only one folder was selected, set `PRIMARY_FOLDER_KEY` to that folder. If multiple were selected, ask: "Which folder should the ontology record itself be registered in?" Record the answer as `PRIMARY_FOLDER_KEY`.

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
- **No write actions** — SQL write actions (`{name}-{actionName}.ttl`) cannot target federated entities. If the SDD describes write operations on a federated class, flag this to the author — those writes must go through the external system directly.
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

**Ontology creation (enables inline validation in the modeler):**

Once CLASS_MAP is confirmed, create the ontology stub so the modeler can validate each artifact against the backend inline during artifact generation:

```bash
uip ont create {name} \
  --display-name "{Display Name}" \
  --description "{description}" \
  --folder-key {PRIMARY_FOLDER_KEY}
```

- `"Code": "OntologyCreated"` → record the returned `id`, proceed to Phase 3.
- `409 Conflict` → name already taken; run `uip ont get {name}` to inspect; stop for user guidance.

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

The modeler skips its own Steps 1 and 2 — it uses the confirmed domain model from Phases 3–4 directly (the ontology was already created at the end of Phase 2). It generates each artifact through a build → preview → check → confirm → write → **backend validate → upsert** flow. Each artifact is upserted to the backend immediately after it passes Gate 5, except `{name}-mapping.yarrrml.yml` which is held (uploading it triggers deploy). The modeler returns once all artifacts are confirmed, validated, and uploaded — only the mapping remains.

The modeler generates:
- `{name}.ofn`, `{name}-constraints.ttl`, `{name}-mapping.yarrrml.yml` — always
- `{name}-functions.ttl` — if the SDD describes query operations an AI agent should answer
- `{name}-{actionName}.ttl` (one per action) — if the SDD describes write/update operations

All five gates summary:

| Gate | Run by | Checks | Pass condition |
|---|---|---|---|
| 1 — QL blacklist | Modeler step 3c | No forbidden OWL 2 QL constructs | Zero hits |
| 2 — Naming | Modeler step 3c | No `has{Prop}` DataProperty names | Zero hits |
| 3 — Cross-file | Modeler step 5c | Every `ont:` term in mapping/rules declared in schema | All found |
| 4 — Annotation | Modeler step 3c | Every declared class and property has `rdfs:label` and `rdfs:comment` | All covered |
| 5 — Backend validate + upsert | Modeler (inline, Steps 3e–7e) | Backend syntactic parse → immediate upsert on valid (except mapping) | `Data.valid: true` + `ArtifactUpserted` each |
| 6 — Semantic consistency | Modeler (inline Steps 3f–7f per artifact; Step 8 cross-artifact) | LLM judge: domain completeness, constraint coverage, column alignment, USAGE POLICY coherence | All checks `✓` |

**Do not proceed to Step 3 until the modeler confirms all artifacts validated and uploaded (except mapping):**
```
{workdir}/{name}.ofn           ✓ validated + uploaded
{workdir}/{name}-constraints.ttl            ✓ validated + uploaded
{workdir}/{name}-functions.ttl        ✓ validated + uploaded  (if generated)
{workdir}/{name}-{actionName}.ttl     ✓ validated + uploaded  (if generated)
{workdir}/{name}-mapping.yarrrml.yml  ✓ validated — awaiting deploy upload
```

---

## Step 3 — Deploy (mapping upload)

> **Trigger:** All artifacts are uploaded except the mapping. Upload mapping last — it transitions the ontology from `DRAFT` to `DEPLOYED`.

### 3a — Upload mapping (deploy trigger)

```bash
uip ont artifacts upsert {name} {name}-mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/{name}-mapping.yarrrml.yml
```
Check response: `"Code": "ArtifactUpserted"` → mapping upload triggers `DRAFT → DEPLOYED`.

### 3b — Verify deployment

```bash
uip ont get {name}
```

| `state` | Meaning | Action |
|---|---|---|
| `DEPLOYED` | All artifacts accepted, ontology live | Done |
| `BROKEN` | Mapping references a term not in schema | Run `uip ont artifacts list {name}` — find the mismatched `ont:` term, fix `{name}-mapping.yarrrml.yml`, re-upload mapping |
| `DRAFT` | Mapping not uploaded yet, or uploaded before schema/rules | Check Steps 3e and 4e in the modeler completed; re-upload mapping |

---

## Artifact reference

| File | `--type` | Media type | Required for deploy |
|---|---|---|---|
| `{name}.ofn` | `schema` | `text/owl-functional` | Yes |
| `{name}-constraints.ttl` | `constraints` | `text/turtle` | Yes |
| `{name}-functions.ttl` | `functions` | `text/turtle` | Optional — generated when SDD describes query operations; freely add/removable without breaking a deployed ontology |
| `{name}-{actionName}.ttl` | `actions` | `text/turtle` | Optional, one file per action — generated when SDD describes write operations; freely add/removable |
| `{name}-mapping.yarrrml.yml` | `mapping` | `application/yaml` | Yes — upload last, triggers `DRAFT → DEPLOYED` |

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `422` on validate or upload | Malformed OWL or Turtle | Read `Data.violations`; the modeler's inline fix loop handles this automatically — re-run the relevant modeler step if bypassed |
| `409` on create | Ontology name taken | `uip ont get {name}` to check; rename or delete first |
| `BROKEN` after deploy | Mapping references undeclared property | Check every `ont:` term in mapping exists in `{name}.ofn` |
| `DRAFT` after mapping upload | schema or constraints not uploaded first | Upload schema and rules, then re-upload mapping |
| `Not Found` on any `uip ont` command | Datafabric service not reachable | Backend not deployed on this environment |
