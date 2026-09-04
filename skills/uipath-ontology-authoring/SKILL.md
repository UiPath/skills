---
name: uipath-ontology-authoring
description: "Use when a user provides an SDD, PDD, domain specification, or ontology artifact files and asks to create, validate, clone, map, wire the domain to Data Fabric entities, or deploy a new UiPath Ontology. Use for missing mapping generation, unresolved class/field/relationship ambiguity, and deployment sequencing. Do not use for plain domain prompts or CRUD operations on an existing ontology."
when_to_use: "User provides an SDD or domain spec and wants to author/publish an ontology end-to-end; user says 'create an ontology from this SDD', 'generate ontology artifacts', 'deploy ontology', 'wire ontology to Data Fabric', 'generate mapping'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
user-invocable: true
---

# UiPath Ontology Authoring — SDD to Deployed Ontology

## Routing boundary

- SDD, PDD, design document, or domain specification → this skill.
- Artifact folder intended for a new deployment or clone → this skill.
- Plain-language domain description with no files → `uipath-ontology-modeler`.
- Existing ontology CRUD, API, SDK, or artifact operations → `uipath-ontologies`.
- Write operations needing computation the write surface cannot express route through this skill's classification; the coded leg's Orchestrator work belongs to `uipath-ontology-coded-action-deploy`.

The words **new**, **clone**, **publish**, **deploy**, **mapping missing**, or **artifact folder** indicate authoring when the request concerns a new ontology. Do not hand such requests to existing-ontology CRUD.

Two entry points — pick based on what the user has:

| User has | Entry point |
|---|---|
| An SDD/PDD or domain spec | **A — Step 1 below.** Scope: SDD → silent login check → folder selection → entity matching + creation → domain definition → delegate artifact generation → preflight → create ontology stub → upload mapping as deploy trigger. |
| Already-generated artifact files — cloned from a different ontology, or authored outside this skill — to deploy | **B — "Entry point B" section below.** No SDD, no domain-definition phases — the domain model already exists in the files. The complete preflight contract still applies. |

**Separation of Concerns** — enforce this throughout (both entry points): facts go in `{name}.ofn`, rules go in USAGE POLICY blocks (mapping + functions), bindings go in `{name}-mapping.yarrrml.yml`. Never let domain facts drift into USAGE POLICY, and never let query routing rules drift into `rdfs:comment`.

> **Functions (SPARQL reads):** if the SDD describes query operations, delegate one `.ttl` per functional area.
> **Actions (SQL writes):** if the SDD describes write operations, delegate one `{name}-{actionName}.ttl` per action.

## Delegated modeler contract

Runtime delegation to `uipath-ontology-modeler` is intentional and is the only sibling relationship in this workflow. Do not read or import the modeler's files. Pass one complete handoff containing:

```text
ONTOLOGY_NAME: exact slug
ONTOLOGY_IRI: https://ontology.uipath.com/{name}#
WORKDIR: dedicated {name}/ output directory
CLASS_MAP: class -> entityName, entityId, folderId, readOnly
MAPPING_STATUS: supplied | generate
DOMAIN_MODEL: confirmed classes, properties, relationships, rules
ANNOTATIONS: confirmed labels, comments, synonyms, value domains, and grain
OPERATIONS: grouped query operations and structured write actions, if any; every write action carries kind: SQL | CODED, and every CODED action also carries its reads, its writes union, and its process name
DEPLOYMENT_MODE: delegated; modeler returns local-preflighted artifacts; authoring validates and uploads the inventory, with mapping as the final deploy trigger
PREFLIGHT_HANDOFF_JSON: machine-readable JSON with CLASS_MAP, FIELD_METADATA, and explicit RELATIONSHIPS ([] when none)
```

The modeler emits CODED actions per its coded-action contract guide, with the TTL carrying `ont:language "CODED"` and `ont:processType "CODED_FUNCTION"`. No deployment coordinate appears in the artifact: the folder follows from the ontology at invoke time.

`MAPPING_STATUS: supplied` means validate the provided mapping. `MAPPING_STATUS: generate` means generate it from handoff metadata; it is valid only with a machine-readable handoff JSON containing confirmed OFN classes/properties, `CLASS_MAP` entityName/entityId/folderId values, field metadata with exactly one identifier for every class, and explicit `RELATIONSHIPS` metadata (`[]` when none). The modeler must return `MAPPING_PATH`, `MAPPING_STATUS`, `MAPPING_GATE`, `UNRESOLVED_AMBIGUITIES`, and the exact preflight `artifact_inventory`. If a class, field, identifier, or relationship cannot be inferred uniquely, require a user decision and stop as `BLOCKED_AMBIGUITY`.

If the modeler is unavailable or returns an incomplete handoff, stop before deployment and return the prepared model and an actionable error. Never upload a mapping marked `PRESENT_INVALID`, `BLOCKED_AMBIGUITY`, or with `MAPPING_GATE: FAIL`.

### Authoring preflight contract

First validate the provided mapping when `MAPPING_STATUS: supplied`, or generate it from handoff metadata when `MAPPING_STATUS: generate`; then run local preflight. Do not create the ontology stub or upload an artifact before this succeeds. Run the neutral validator against the exact workdir and intended upload set:

`<TOOLS_DIR>` is the plugin's shared `tools/` directory — `<SKILL_DIR>/../../tools`, where `<SKILL_DIR>` is the folder holding this `SKILL.md`. Invoke it through `python3` with that prefix: the file is not marked executable, and a relative `tools/` does not resolve from the `{workdir}` these steps run in.

```bash
python3 <TOOLS_DIR>/ontology_preflight.py \
  --workdir {workdir} --ontology-name {name} --mapping-mode auto \
  --handoff '{"CLASS_MAP": {...}, "FIELD_METADATA": {...}, "RELATIONSHIPS": []}'
```

Require JSON `status: PASS`, no failed `gate_results`, and mapping status `PRESENT_VALID` after the mapping file exists; consume its exact `artifact_inventory` as the only upload set. If the mapping is missing and metadata is sufficient, pass `MAPPING_STATUS: generate` plus the handoff JSON to the modeler and rerun preflight after generation. Repair every failure and rerun preflight after each repair; do not merely report a failed gate. Only after this local gate passes may authoring create the ontology stub and call backend artifact validation.

---

## Entry point B — cloning or deploying already-generated artifacts (no SDD/PDD)

Trigger: user points to a folder of already-generated artifact files (`{oldName}.ofn`, `{oldName}-constraints.ttl`, `{oldName}-functions.ttl`, `{oldName}-mapping.yarrrml.yml`, optionally `{oldName}-{actionName}.ttl`) — either cloned from a different ontology under a new name, or authored outside the guided flow and never gated — and wants them deployed. The domain model already exists in the files — skip Step 1 (SDD reading) and Phases 3–6 (domain definition) entirely. "The files already exist" is not a reason to skip any gate: a file that already parses and validates gives no other signal that it's missing a mapped class or a relationship. Do this instead:

1. Confirm the new `{name}` slug (same IRI-derivation rule as Step 1) and the target folder (Phase 1, including its cross-folder name-collision check).
2. If cloning from a different ontology: copy each file into `{workdir}`, renaming `{oldName}` → `{name}` in the filename and, inside every file, every occurrence of the old slug — schema/constraints/functions/mapping IRIs, SPARQL `PREFIX ont:` lines, and (for `functions`/`actions`) the `ont:statement`/`ont:statements` bodies. If mapping is absent, set `MAPPING_STATUS: generate` and provide the modeler with the schema/entity metadata needed to create it. If deploying files as originally authored, use `MAPPING_STATUS: supplied` when present.
3. **A rename (or "it already exists") is not sufficient.** Run the preflight command above against the exact files before uploading anything. It catches IRI drift, undeclared terms, missing object properties for FK joins, action output-contract failures, and non-global namespaces. Fix every failed gate locally and rerun preflight. Do this even though a cloned source ontology may already be `DEPLOYED` elsewhere.
4. Check `{name}-constraints.ttl`'s `@prefix shape:` is the global `<https://ontology.uipath.com/shapes#>`, not a per-ontology path.
5. If the folder holds already-generated coded pairs (a `jobs/{actionName}.ts` beside its coded `{name}-{actionName}.ttl`), run Step 2b's deploy delegation before any upload, exactly as a generated inventory does.
6. After preflight passes, create the ontology stub using Step 3a's `uip ont create`. Run backend validation for every artifact and require `Data.Valid: true`; then upsert schema first, constraints/functions/actions in parallel, and mapping last (triggers `DRAFT → DEPLOYED`). Verify `uip ont get {name}` is `DEPLOYED` and `uip ont artifact list {name}` matches the exact upload set. `DEPLOYED` only means internally consistent, not "relationships modeled"; the preflight relationship gate guarantees that.

---

## Run checklist

Everything below is a failure someone has already paid for. Each line is enforced by a gate, a
guide rule, or a refusal further down; this is the short form to check a run against.

**Before generating anything**

- [ ] Settle the folder, and note that the question differs by path (Phase 1). A SQL-only
      inventory picks an **existing** folder. An inventory with any CODED action cannot: the
      deployment creates the folder and cannot be aimed at one that exists, so ask for **a name and
      a parent** instead. Offer `Shared` as the parent: a folder at the root has no user with
      unattended robot permissions and its jobs never start.
- [ ] `uip login status` is the only source of org and tenant.

**Schema**

- [ ] Every class declares `{Class}.id`, annotated `ont:datatype "key"`, range `xsd:string`.
- [ ] Every data property carries `ont:datatype`. Nothing is inferred from the XSD range.
- [ ] No `xsd:anyURI` and no `xsd:boolean` — see the OWL guide for what each one breaks.
- [ ] A reserved name cannot be a Data Fabric entity. Map the class to a differently-named entity
      and record it in `CLASS_MAP`.
- [ ] Integer columns are `DECIMAL` with `decimalPrecision: 0`. The server accepts `INTEGER` but
      the UI cannot render, filter or edit the column.

**Mapping**

- [ ] `{Class}.id` binds to `$(Id)` in every mapping block, or the identity is declared and
      unpopulated.
- [ ] An inverse object property needs its own join, or the semantic gate reports it unaligned.

**Coded actions**

- [ ] `ont:language "CODED"` with `ont:processType "CODED_FUNCTION"`. No deployment coordinate in
      the artifact.
- [ ] A read that cannot be filtered carries `LIMIT`, and the job refuses a read that came back at
      the limit rather than computing from a possibly truncated view.
- [ ] No control characters in any written value.
- [ ] Every edit carries `id`, and `ont:writes` is the union over every branch.

**Deploy**

- [ ] Publish, then deploy to create the folder, then the entities, then
      `uip ont create --folder-key`.
- [ ] Re-release by reusing the **same deployment name** with a new version. Never uninstall to
      re-release: that deletes the folder and the entities in it.
- [ ] Every release reports `ready` before any invoke.

---

## Step 1 — Collect SDD and ontology details

Ask the user for all of the following **in one message**:

| Input | Notes |
|---|---|
| **SDD** | File path, Confluence URL, or pasted text |
| **Ontology name** | Slug: max 64 chars, no `/` (e.g. `clinic`, `ecommerce`) |
| **Display name** | Human label (defaults to `<name>`) |
| **Description** | One sentence |
| **Base directory** | Parent location to create the ontology's own folder under (defaults to the SDD file's directory, or current directory) |

Read the SDD immediately (Read tool for file paths). Extract only the **class names** from it — just enough to drive entity matching in Phase 2. Do not build the full domain model yet.

While reading the SDD, also scan for:

**Query operations (functions — zero or more files):** natural-language questions the SDD says the system or an AI agent should answer (e.g. "how many X in state Y", "list X with their Y", dashboards, summaries, counts). If found, record the described operations and identify natural groupings by functional area (querying, analytics, validation, etc.). Pass one `.ttl` file per functional area to the delegated modeler — there is no limit on the number of function files.

**Write operations (actions — zero or more files, one per action):** mutations the SDD describes (e.g. "update status", "create record", "delete entry"). For each, record: action name, target entity, SQL operation (UPDATE / INSERT / DELETE), fields affected, identifier field, and input parameters. Pass one `{name}-{actionName}.ttl` per action to the delegated modeler — there is no limit on the number of action files.

Classify each recorded write operation as `kind: SQL` or `kind: CODED`.

**The question is whether producing the edit needs computation the write surface cannot express.**
It is not whether the rule is a "business rule" or a "constraint" — neither term is defined here,
and classifying on them puts the boundary in the wrong place. Anything that reaches past a single
statement of literal values, and needs any computation to arrive at what to write, belongs on the
coded leg. The write surface is literals-only SQL today, and the tests below would not move if it
grew procedural extensions: what the coded leg buys is a Turing-complete language, not more SQL
grammar.

Apply these tests in order; first match wins:

1. CODED if the new value must be computed from stored data, the clock, or arithmetic/string construction. The SQL surface is literals-only: no `GETDATE`, no expressions, enforced by Data Fabric's own parser (`SET x = x + 0` and `SET x = CASE...` are both rejected with "Only literal values supported").
2. CODED if the operation reads before writing, branches on what it finds, iterates over rows or items (any per-row loop), may write several rows or several entities, or may legitimately write nothing (converged no-op).
3. CODED if a rule depends on a fact the caller must not be trusted to assert. Values derived from data are computed from declared reads, never from caller parameters: a caller can lie about any fact concerning the data.
4. Otherwise SQL: single entity, single record, caller-supplied literal values. Ambiguous cases default to SQL. Declarative by default; a job in a high-level language (currently supported: TypeScript) only when the edit cannot be expressed before it is computed.

**Refuse rather than classify: an operation that reads after it writes.** A coded action's declared
reads all run before the job starts, and its edits all apply after the job returns. There is no
point at which a job can observe its own writes, or interleave a read between two of them. An SDD
asking for that describes a sequence this shape cannot express, so stop at this gate and say which
operation and which ordering — do not generate a job that would silently read pre-write state and
look correct.

Worked classifications:

| Operation | Verdict | Why |
|---|---|---|
| `updateAccountDescription(id, text)` | SQL | one row, caller supplies the value |
| `setStatus(id, status)` | SQL | same |
| `tagOverdueTicket(ticketId)` | CODED | clock arithmetic, list append, converged no-op |
| `flagBigOrder(invoiceIds)` | CODED | per-row loop over lines, multi-row write |
| `setInvoiceDecision(id, decision, approver)` | CODED | boundary case: looks like a parameter write, but composes a rationale string and screens caller-asserted facts |
| `approveIfUnderLimit(id, amount)` | CODED | rule 3: the amount must come from a read, not the caller |

Two of these are real and worked end to end, TTL beside job, in
`uipath-ontology-modeler`'s `references/coded-action-example.md`: `tagOverdueTicket` and
`flagBigOrder`. The rest are named for their shape only — each verdict follows from the rubric
above, not from a file to open. Two worked pairs are enough context to generate from; more would
be volume without a new shape.

For every CODED operation additionally record: its **reads** (one bind name plus the SELECT intent per read), its **writes union** (every field any branch could touch, not one predicted run), and its **process name** (`PascalCase(actionName)` + `Process`).

If neither is present in the SDD, note that explicitly — no functions or action files will be generated.

### IRI derivation — compute once, use everywhere

As soon as the ontology name is confirmed, derive the IRI:

```
ONTOLOGY_IRI = https://ontology.uipath.com/{name}#
{workdir}     = {base directory}/{name}/
```

`{name}` is the exact slug — verbatim, no transformation. Show it to the user and confirm before generating any files. This value must be **identical** in all artifact files (`{name}.ofn`, `{name}-constraints.ttl`, `{name}-mapping.yarrrml.yml`, functions, and actions). It is immutable — renaming the ontology later does not change the IRI.

**Every artifact file for this ontology goes inside its own dedicated `{name}/` subfolder — never loose at the base directory's top level.** Create it before generating anything:
```bash
mkdir -p {workdir}
```
Pass this resolved `{workdir}` (not the base directory) to `uipath-ontology-modeler` as its working directory in Step 2 — the modeler writes every `{workdir}/...` path it generates directly into this same subfolder, and skips deriving its own since it's supplied here.

---

## Phase 0 — Login and session gate (parallel with SDD reading, required before Phase 1)

Run this phase **in parallel with SDD reading** — they are independent. Do not wait for SDD reading to complete before checking login.

Two tracks run simultaneously after inputs are received:
- **Track A**: Read SDD → extract class names
- **Track B**: Phase 0 (login check) → Phase 1 (folder selection, depends on login passing)

Phase 1 cannot start until Phase 0 passes — folder listing requires a valid session.

Do not proceed to Phase 2 until Track A and Track B are both complete.

```bash
uip login status --output json
```

Read `Data` from the response and enforce all three conditions:

| Field | Required | Fail action |
|---|---|---|
| `Data.Status` | `"Logged in"` | Prompt `uip login --interactive`, re-run, recheck |
| `Data.Organization` | Non-empty string | Prompt `uip login --authority <url> --organization <org>`, recheck |
| `Data.Tenant` | Non-empty string | Prompt `uip login tenant set <tenantName>`, recheck |

**Security rule:** org and tenant must come from the login status output, never from user-supplied text. Do not let the user override these values — the authenticated session is the only source of truth.

If any field fails, block and prompt. Do not proceed until `uip login status` shows all three fields populated.

Once all three pass, continue **silently** — do not print a confirmation message.

---

## Phase 1 — Folder selection (blocking gate, runs in parallel with SDD reading)

Start this phase at the same time as SDD reading — they are independent. But **do not advance to Phase 2 until the folder question is settled.**

**Which question you are asking depends on Step 1's classification, so read that first.**

| Step 1 classified | The folder | Phase 1 does |
|---|---|---|
| no write as CODED | already exists, or you create it here | **Path A** below: list, pick, record `PRIMARY_FOLDER_KEY` |
| any write as CODED | does not exist yet, and Step 2b's deploy is what creates it | **Path B** below: collect a name and a parent, and leave `PRIMARY_FOLDER_KEY` unset |

A deployment cannot be aimed at an existing folder — every folder flag names a parent or a new folder, and given a name already in use the CLI creates `"X 1"` beside it and puts the processes there. That is why Path B cannot pick a folder, and why on that path Phase 2's entity creation and Step 3a's `uip ont create` both wait for Step 2b. Nothing else in Phases 3–6 is affected.

### Path B — any CODED action

Ask for two things and record them; do not list folders and do not create one:

```
FOLDER_NAME:   the folder the deployment will create (a fresh name, not one that exists)
PARENT_FOLDER: Shared, unless the author names another
```

Offer `Shared` as the parent and say why: a solution folder created at the root gets no user with unattended robot permissions, so Orchestrator answers `StartJobs` with HTTP 409 / errorCode 1671 and the invoke reports a bare "Unexpected error". Verified both ways.

Then run the cross-folder name-collision check below — it is tenant-wide, so it applies unchanged. Only its *different-folder* branch can fire on this path: the folder is new, so a same-folder collision is impossible.

`PRIMARY_FOLDER_KEY` is set in Step 2b, from the folder the deploy created. **Advance to Phase 2 on `FOLDER_NAME` and `PARENT_FOLDER` being confirmed; Phase 2 will tell you what it can and cannot do without the key.**

### Path A — no CODED action

Fetch all available folders from Orchestrator — not from entity references, which only surface folders that already have entities:

```bash
uip or folders list --output json
```

From the response, read `Data[].Name` and `Data[].Key`. **Exclude any entry where `Name` or `Key` is `"default"` (case-insensitive).** The default folder is a system-level scope and must not be used for ontology registration.

Present the remaining folders as a numbered list:

```
Available folders:
  1. HireFlow        (key: 751e18c5-...)
  2. Clinic          (key: b5b4bd01-...)
  3. Ecommerce       (key: 9a3c2d11-...)

Which folder should this ontology be created in?
```

If the user's desired folder is not in the list, or if no folders appear after excluding "default", offer to create one:

> "That folder isn't available. Want me to create it now?"

If the user confirms, create the folder with:

```bash
uip or folders create "<FolderName>" --output json
```

To nest it under an existing folder, add `--parent "<ParentName>"` (name or key). Read `Data.Key` from the response and use it as `PRIMARY_FOLDER_KEY`. Do not proceed without a confirmed key.

Record the selected folder key as `PRIMARY_FOLDER_KEY`.

**Gate (Path A): do not move to Phase 2 until `PRIMARY_FOLDER_KEY` is confirmed and is not `"default"`.** On Path B the key does not exist yet; its gate is `FOLDER_NAME` and `PARENT_FOLDER`.

### Cross-folder name collision check — both paths

Run this on Path A once `PRIMARY_FOLDER_KEY` is confirmed, and on Path B once `FOLDER_NAME` is. The query is tenant-wide, so it needs no folder:
```bash
uip ont list --output json
```
Scan the result for any ontology whose name matches `{name}` (case-insensitive):
- **Same folder match** → backend will reject `uip ont create` — tell the user immediately and stop. Ask them to pick a different name.
- **Different folder match** → warn explicitly and wait for confirmation before continuing:

> ⚠ An ontology named `{name}` already exists in folder `{otherFolderKey}` (ID: `{otherOntologyId}`). Creating another with the same name in a different folder means both will share the IRI `https://ontology.uipath.com/{name}#`. Any tool or reasoner that reads both will see the same term IRIs pointing to different data. Confirm you want to proceed, or choose a different name.

**Convergence gate — do not move to Phase 2 until both tracks are complete:**
- Track A: SDD reading done and class names extracted
- Track B: Login verified, then — on Path A, `PRIMARY_FOLDER_KEY` confirmed (not `"default"`, not `00000000-0000-0000-0000-000000000000`); on Path B, `FOLDER_NAME` and `PARENT_FOLDER` confirmed

---

## Phase 2 — Entity matching and creation

Now that the SDD class names are known (from Step 1), match each SDD class against entities in `PRIMARY_FOLDER_KEY`. All entity operations in this phase are scoped to that folder only — do not list or create entities outside it.

**On Phase 1's Path B there is no `PRIMARY_FOLDER_KEY` yet, so this phase splits in two.** Build the matching table now from the SDD alone — a folder that does not exist holds no entities, so every class is **Create new (native)** and there is nothing to match against. Federated classes are the exception worth stating to the author early: they cannot be created at all, by CLI or API, so an SDD needing one is blocked on someone building it in the Data Fabric UI first, and it will live in its own folder rather than the new one. Then **defer every `uip df entities create` until Step 2b has returned the folder key**, and run them against that key. Phases 3–6 need no folder and proceed normally.

```bash
uip df entities list --folder-key {PRIMARY_FOLDER_KEY} --output json
```

Identify each entity's type from the response: `externalFields: []` → **Native**; `externalFields: [{...}]` → **Federated**. Then build the matching table:

| SDD class | Suggested entity | Type | Match | Entity ID | Folder ID | Action |
|---|---|---|---|---|---|---|
| `Doctor` | `Doctor` | Native | exact | `b5b4bd01-...` | `751e18c5-...` | Use existing |
| `Contact` | `Contact` | Federated | exact | `9f1a2c44-...` | `751e18c5-...` | Use existing |
| `Prescription` | — | — | none | — | — | **Create new (native)** |

**Matching rules:** exact name match first; then case-insensitive match; then present candidates if partial match. If no match at all, mark as **Create new (native)**.

**Federated entity rules:**
- **Use existing only** — federated entities connect to external systems (SQL Server, Salesforce, SAP, etc.) via UiPath Integration Service. New federated entities cannot be created via CLI or API — the connection must be set up through the Data Fabric UI. If an SDD class needs a federated entity that doesn't exist yet, stop and tell the user to create it in the portal first.
- **Readable and writable** — a federated class is a first-class target for both. Reads and writes traverse FQS, which resolves the external connection and routes the statement to the source system. Treat native and federated classes the same when planning operations; do not mark a class `readOnly` merely because it is federated.
- **`readOnly` is an exception the author states, not a property of federation.** Set it on a class only when the author says that specific source rejects writes; a connection configured read-only, or a system that exposes no write API. It is never inferred, so most CLASS_MAPs carry it on no class at all.
- **Write actions are allowed** — both SQL write actions (`{name}-{actionName}.ttl`) and coded actions may target a federated class. The write is compiled to bounded DML and executed against the source through its connector, so the source system remains the authority on whether a given write succeeds: a rejection (permissions, a type mismatch, a constraint, a connection configured read-only) surfaces as an upstream error on the failing step, not as a refusal by the platform. Set `readOnly: true` in CLASS_MAP only when the author states a specific source rejects writes — never inferred from federation.
- **YARRRML mapping is identical** — the mapping syntax for a federated entity (`access: datafabric`, `entityId`, `folderId`) is the same as native. The FQS runtime handles the federation transparently, for reads and writes alike. Functions (SPARQL reads) work with federated entities.

**How federated entity connections work:**
A federated entity is backed by an external data source configured in the Data Fabric UI:
1. An Integration Service connection is created for the external system (e.g. SQL Server, Salesforce)
2. The federated entity schema is defined in the portal, mapped to a table or object in that system
3. Once set up, the entity appears in `entities list` with `externalFields` populated and is queryable through FQS

**For each "Create new (native)" row:**
- Propose a field schema based on the data properties the SDD describes for that class
- Show the proposed schema to the author and get explicit confirmation
- Create the entity scoped to `PRIMARY_FOLDER_KEY`:
  ```bash
  uip df entities create {EntityName} --folder-key {PRIMARY_FOLDER_KEY} --body '{...}' --output json
  ```
- Record the returned `entityId` and confirm `folderId` matches `PRIMARY_FOLDER_KEY`

> **Field name alignment:** entity field names created here are preliminary. After Phase 4 finalizes all `{ClassName}.{propName}` camelCase names, check that each created entity's field names match what the YARRRML mapping will use as `$(column)` references. If any names differ, update the entity schema before the modeler generates the mapping in Step 2.

Record the completed mapping — all entities must be in `PRIMARY_FOLDER_KEY`:
```
CLASS_MAP:
  {ClassName}: entityId={uuid}  folderId={PRIMARY_FOLDER_KEY}  [readOnly: true]  ← only if the source rejects writes
```

> **Wait for CLASS_MAP confirmation before moving to Phase 3.**

**Stub deferral:** do not create the ontology stub here. Complete the domain review, generate the mapping, and pass local preflight first. Step 3 creates the stub immediately before backend validation and tiered upload.

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

**Not every noun is a class.** SDDs frequently mention actors, roles, or external systems for narrative context only — "the AP Clerk captures the invoice," "posted to the ERP system" — with no properties of their own and no backing Data Fabric entity. Modeling these as OWL classes produces a class with no property or mapping entry, which passes syntax checks but silently blocks `DEPLOYED`. If a concept has no property beyond a name and won't appear in the mapping, leave it out and fold it into the relevant property's `rdfs:comment` instead (e.g. `Payment.approvedBy`: "The Accounts Payable Manager who approved this payment.").

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
| true/false, flag, boolean | `xsd:string` with `ont:datatype "category"` |
| URL, link | `xsd:string`, with the format in `rdfs:comment` |

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

## Step 2 — Generate all artifact files (delegate to `uipath-ontology-modeler`)

**Delegate to the `uipath-ontology-modeler` skill** using the handoff contract above and pass it:
- Confirmed domain model from Phases 3–4 (classes, data props, object props, business rules)
- Confirmed annotations from Phase 5, updated with verified facts from Phase 6
- `ONTOLOGY_IRI` from Step 1
- `CLASS_MAP` from Phase 2 (entityId + folderId per class)
- `{workdir}` from Step 1 (the ontology's own `{name}/` subfolder, already created) as the working directory for output

> If the `uipath-ontology-modeler` skill is not available, stop before deployment and return: "Artifact generation requires the uipath-ontology-modeler sibling skill. The domain model and setup are prepared; activate that skill and retry the delegation."

The modeler skips its standalone setup and domain-gathering phases. It uses the confirmed handoff directly, validates the provided mapping when `MAPPING_STATUS: supplied` or generates it from handoff metadata when `MAPPING_STATUS: generate`, and runs local preflight with `--handoff` before any backend call. It returns the exact `artifact_inventory`; authoring alone creates the stub, validates, and uploads the inventory in tiers, holding `{name}-mapping.yarrrml.yml` until last.

The modeler generates each artifact following its canonical pattern file:

| Artifact | Pattern file | Count | Authoring upload tier |
|---|---|---|---|
| `{name}.ofn` | Modeler's OWL guide | 1 (always) | Tier 1 (first — schema is context for all others) |
| `{name}-constraints.ttl` | Modeler's SHACL guide | 1 (always) | Tier 2 (parallel with functions + actions) |
| `{name}-[area-]functions.ttl` | Modeler's functions guide | 0 or more — one per functional area | Tier 2 (each file uploaded in parallel) |
| `{name}-{actionName}.ttl` | Modeler's action guide | 0 or more — one per write action | Tier 2 (each file uploaded in parallel) |
| `{workdir}/jobs/{actionName}.ts` | Modeler's coded-action guide | 0 or more, one per coded action | None, jobs are never ontology artifacts |
| `{name}-mapping.yarrrml.yml` | Modeler's mapping guide | 1 (always) | Tier 3 — upload last as deploy trigger |

Row note: coded `{name}-{actionName}.ttl` files are held out of Tier 2 until Step 2b below reports its releases live. The files themselves are not modified — they name a release, not a folder — but uploading one before its job is deployable leaves an action that resolves to nothing at invoke.

Gate ownership and execution:

| Gate | Run by | Checks | Pass condition |
|---|---|---|---|
| G1 — QL blacklist | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | No forbidden OWL 2 QL constructs in `{name}.ofn` | Zero hits |
| G2 — Naming | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | No `has{Prop}` DataProperty names | Zero hits |
| G3 — Cross-file | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | Every `ont:` term in mapping + constraints + functions/actions SPARQL/SQL bodies declared in schema | All found |
| G4 — Annotation | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | Every declared class and property has `rdfs:label` and `rdfs:comment` | All covered |
| G5 — Preflight | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | Local preflight passes and returns exact `artifact_inventory` | preflight pass |
| G6 — Backend validate + tiered upsert | Authoring — backend validation and tiered upsert | Authoring validates and uploads inventory in tiers (schema first, then constraints/functions/actions); mapping is held until authoring uploads it last | `Data.Valid: true` + `ArtifactUpserted` each |
| G7 — Semantic consistency | Modeler — local QL/naming/cross-file/annotation/semantic/preflight gates | LLM judge: domain completeness, constraint coverage, column alignment, USAGE POLICY coherence | All checks `✓` |

**Do not proceed to Step 3 until the modeler confirms preflight passed and returns every generated artifact in its exact `artifact_inventory`:**
```
{workdir}/{name}.ofn           ✓ local preflighted; authoring uploads Tier 1
{workdir}/{name}-constraints.ttl            ✓ local preflighted; authoring uploads Tier 2
{workdir}/{name}-functions.ttl        ✓ local preflighted; authoring uploads Tier 2 (if generated)
{workdir}/{name}-{actionName}.ttl     ✓ local preflighted; authoring uploads Tier 2 (if generated)
{workdir}/{name}-mapping.yarrrml.yml  ✓ local preflighted; authoring uploads Tier 3 last
MAPPING_GATE: PASS
UNRESOLVED_AMBIGUITIES: none
```

---

## Step 2b — Deploy coded action jobs (delegate to `uipath-ontology-coded-action-deploy`)

A SQL-only inventory skips this step untouched and goes straight to Step 3. Run it only when the returned inventory contains coded actions.

**Invoke the `uipath-ontology-coded-action-deploy` skill** with the `Skill` tool and pass it:
- `{workdir}` from Step 1
- the ontology name `{name}`
- every coded pair: `{workdir}/jobs/{actionName}.ts` with its `{workdir}/{name}-{actionName}.ttl`

That skill publishes the `{name}-jobs` Solution, deploys it — **which is what creates the Orchestrator folder** — and awaits every release. It returns that folder's name, path, key and numeric id. It patches nothing: a coded action names its release and says nothing about where the release is deployed, so the TTLs come back unchanged.

**This reorders the rest of the flow.** The folder does not exist until the deploy runs, and a deployment cannot be pointed at an existing folder. So:

1. delegate the deploy, passing Phase 1 Path B's `FOLDER_NAME` and `PARENT_FOLDER`
2. **set `PRIMARY_FOLDER_KEY` to the key of the folder it created.** Everything downstream reads that one variable, so from here on both paths are identical
3. run the `uip df entities create` calls Phase 2 deferred, against `PRIMARY_FOLDER_KEY`
4. `uip ont create {name} --folder-key {PRIMARY_FOLDER_KEY}` (Step 3a)
5. validate and upload the artifacts (Steps 3b, 3c)
6. invoke

Phase 1 Path B already collected the folder's name and parent. Do not ask for an existing folder here, and do not create the folder yourself with `uip or folders create` — the deploy creates it, and a folder that already exists makes the CLI create `"{FOLDER_NAME} 1"` beside it and deploy the processes there, leaving the ontology bound to a folder holding zero processes.

Prose telling the user to run the deploy skill is not a substitute for the `Skill` call — the flow
does not continue until that skill has reported its releases live.

> If the `uipath-ontology-coded-action-deploy` skill is not available, stop before upload and return: "Coded actions require the uipath-ontology-coded-action-deploy sibling skill. The artifacts are generated and locally preflighted, but no release is live and no folder exists to bind the ontology to; activate that skill and retry the delegation."

**Do not rerun the coded preflight here.** Nothing about the pair changed: the deploy skill stages
a copy of each job and edits no artifact, and `ont:processType` was written by the modeler at
generation time and already checked by its gate. A rerun would re-report the modeler's own verdict
and read as fresh evidence of readiness, which it is not.

Readiness is what the deploy skill reported, and only that: the folder exists and every release is
`ready`. A release reported `stale` or `missing` is the gate — stop and say which process, rather
than uploading an action that resolves to nothing at invoke.

---

## Step 3 — Validate and deploy

> **Trigger:** The modeler returned a passing preflight inventory, and any coded actions have a live release from Step 2b. Authoring creates the stub, validates every inventory artifact, uploads schema first, uploads constraints/functions/actions next. Upload mapping last — it transitions `DRAFT → DEPLOYED`.

### 3a — Create the ontology stub

```bash
uip ont create {name} \
  --display-name "{Display Name}" \
  --description "{description}" \
  --folder-key {PRIMARY_FOLDER_KEY} \
  --output json
```

`PRIMARY_FOLDER_KEY` is Phase 1 Path A's selected folder, or — on Path B — the folder Step 2b's deploy created. Either way it is a confirmed key by the time this runs; if it is unset, an earlier gate was skipped.

Proceed only on `Code: OntologyCreated`. The modeler has not called the backend and has not uploaded any artifact.

### 3b — Backend-validate the exact inventory

Authoring backend-validates every artifact in `artifact_inventory`, the coded action TTLs cleared by Step 2b included, and requires `Data.Valid: true` for each response before uploading anything. **The field is capitalised**, and the `{fileName}` positional is required exactly as it is for `upsert` — omit it and every call returns `error: missing required argument 'fileName'`, which still parses, so a naive check reads it as a validation failure and sends the session hunting a phantom artifact bug:

```bash
uip ont artifact validate {name} {fileName} \
  --type {schema|constraints|functions|actions|mapping} \
  --media-type {text/owl-functional|text/turtle|application/yaml} \
  --file {absolute-path-from-artifact_inventory} \
  --output json
```

Run the command once per returned inventory entry. If any `Data.Valid` is not `true` (including a `422`), authoring owns the recovery: read `Data.violations`, repair the identified local artifact, rerun preflight, and repeat all inventory validation; do not upload a partial tier. Authoring may re-delegate only local artifact regeneration to the modeler, which returns a new local-preflighted inventory and makes no backend calls. Authoring then resumes this backend-validation and upload sequence.

### 3c — Upload Tier 1 and Tier 2

Tier 1 — schema first:

```bash
uip ont artifact upsert {name} {name}.ofn \
  --type schema --media-type text/owl-functional \
  --file {workdir}/{name}.ofn --output json
```

Tier 2 — constraints, functions, and actions, the coded action TTLs cleared by Step 2b included; they ride Tier 2 exactly like declarative action files, media type `text/turtle`, `--type actions` (parallel where present):

```bash
uip ont artifact upsert {name} {artifact-name} \
  --type {constraints|functions|actions} --media-type text/turtle \
  --file {absolute-path-from-artifact_inventory} --output json
```

Require `Code: ArtifactUpserted` for every Tier 1 and Tier 2 artifact. Do not upload the mapping in either tier.

### 3d — Tier 3 — mapping only, last (deploy trigger)

After every schema, constraints, function, and action upload succeeds, upload the one mapping inventory entry last:

```bash
uip ont artifact upsert {name} {name}-mapping.yarrrml.yml \
  --type mapping \
  --media-type application/yaml \
  --file {workdir}/{name}-mapping.yarrrml.yml \
  --output json
```
Require `Code: ArtifactUpserted`. This mapping upload is the deploy trigger and must be the final artifact upload; it transitions `DRAFT → DEPLOYED`.

### 3e — Verify deployment

```bash
uip ont get {name}
```

| `state` | Meaning | Action |
|---|---|---|
| `DEPLOYED` | All artifacts accepted, ontology live | Done |
| `BROKEN` | Mapping references a term not in schema | Run `uip ont artifact list {name}` — find the mismatched `ont:` term, fix `{name}-mapping.yarrrml.yml`, re-upload mapping |
| `DRAFT` | Mapping not uploaded yet, or uploaded before schema/rules | Follow this skill's recovery sequence: inspect `uip ont artifact list {name}`, backend-validate the exact preflight inventory again (3b), upsert schema (Tier 1) and rules (Tier 2), then re-upload mapping last (3d). |

### 3f — Final inventory gate

After `DEPLOYED`, run `uip ont artifact list {name} --output json`. Confirm that every file in the preflight upload set is present and no unintended artifact was uploaded. If the state or inventory is wrong, stop and report the exact mismatch; do not claim deployment success.

---

## Artifact reference

| File | `--type` | Media type | Pattern file | Count | Required for deploy |
|---|---|---|---|---|---|
| `{name}.ofn` | `schema` | `text/owl-functional` | delegated modeler | 1 | Yes |
| `{name}-constraints.ttl` | `constraints` | `text/turtle` | delegated modeler | 1 | Yes |
| `{name}-[area-]functions.ttl` | `functions` | `text/turtle` | delegated modeler | 0 or more — one per functional area | No — freely add/removable without breaking a deployed ontology |
| `{name}-{actionName}.ttl` | `actions` | `text/turtle` | delegated modeler | 0 or more — one per write action | No — freely add/removable |
| `{workdir}/jobs/{actionName}.ts` | never uploaded | n/a | delegated modeler (coded-action guide) | 0 or more — one per coded action | No — deployed to Orchestrator by `uipath-ontology-coded-action-deploy` in Step 2b |
| `{name}-mapping.yarrrml.yml` | `mapping` | `application/yaml` | delegated modeler | 1 | Yes — upload last, triggers `DRAFT → DEPLOYED` |

---

## Common errors

| Error | Cause | Fix |
|---|---|---|
| `422` on validate or upload | Backend validation rejected an artifact | Authoring reads `Data.violations`, repairs the local artifact, reruns preflight, then repeats authoring Step 3b backend validation and the tiered upload sequence. It may re-delegate local regeneration to the modeler, but the delegated modeler makes no backend calls. |
| `409` on create | Ontology name taken | `uip ont get {name}` to check; rename or delete first |
| `BROKEN` after deploy | Mapping references undeclared property | Check every `ont:` term in mapping exists in `{name}.ofn` |
| `DRAFT` after mapping upload | schema or constraints not uploaded first | Upload schema and rules, then re-upload mapping |
| `DRAFT` persists though schema/constraints/mapping are all uploaded and every artifact individually validates fine | A class in `{name}.ofn` has zero properties and/or no instantiation in the mapping | Require every class to be the domain of ≥1 property AND appear as `a ont:{ClassName}` in the mapping. Remove or properly back any class that fails either check, then re-upload schema/mapping |
| `Not Found` on any `uip ont` command | Datafabric service not reachable | Backend not deployed on this environment |
