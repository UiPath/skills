# UiPath Ontology Modeler

Generates all ontology artifact files from a domain description. You can start from a plain prompt — no SDD required.

---

## Two ways to start

### 1. Prompt — describe your domain directly

Tell the modeler what your domain is about. A short description is enough to get started:

> "Create an ontology for a clinic. We have Doctors, Patients, and Prescriptions. A doctor prescribes prescriptions for patients. Each prescription has a status, a medication name, and a date."

The modeler will:
1. Ask for a name slug and working directory
2. Match your classes to existing Data Fabric entities (or create them)
3. Show you a structured domain model to confirm
4. Generate all artifact files one at a time, with a preview and confirmation before each write

### 2. SDD — start from a design document

If you have a Software Design Document (SDD), use the **`uipath-ontology-authoring`** skill instead. It reads the SDD, extracts the domain, handles login and folder selection, then calls this modeler to generate the files.

Use the modeler directly only when you're describing the domain yourself.

---

## What you get

| File | What it is |
|---|---|
| `{name}.ofn` | OWL 2 QL Functional Syntax — classes, properties, labels, descriptions |
| `{name}-constraints.ttl` | SHACL Turtle — one shape per business rule (required fields, cardinality) |
| `{name}-mapping.yarrrml.yml` | YARRRML — wires each class to a Data Fabric entity and each property to a column |
| `{name}-functions.ttl` | W3C FnO — SPARQL read queries (generated if your description includes query operations) |
| `{name}-{actionName}.ttl` | W3C FnO — SQL write operations, one file per action (generated if your description includes writes) |

---

## Quick start

1. Invoke the skill: `/uipath-ontology-modeler`
2. Describe your domain — or paste a description if you have one
3. Provide a name slug (e.g. `clinic`) and a working directory when asked
4. Review and confirm the domain model
5. Review and confirm each artifact file in order

The modeler never writes a file before you confirm it. You can revise any file before it is written.

---

## Entry points

| Trigger | Skill |
|---|---|
| You describe the domain yourself (prompt) | **`uipath-ontology-modeler`** (this skill) |
| You have an SDD file or Confluence page | **`uipath-ontology-authoring`** |
| You want to re-generate one artifact from an existing model | **`uipath-ontology-modeler`** — skip to the relevant step |

---

## Separation of concerns

Each artifact has a distinct job. The modeler enforces this — do not mix them:

| What | Where |
|---|---|
| What a value means, grain, FK provenance | `rdfs:comment` in `{name}.ofn` |
| Business constraint (must-have, exactly-one) | `{name}-constraints.ttl` SHACL shape |
| Query routing and LIMIT/DISTINCT discipline | USAGE POLICY block in `{name}-mapping.yarrrml.yml` |
| Class → entity, property → column, FK join | `{name}-mapping.yarrrml.yml` bindings |
| What a function returns and when to use it | `rdfs:comment` in `{name}-functions.ttl` |
| Which function answers which question type | USAGE POLICY block in `{name}-functions.ttl` |
| What a SQL action changes | `rdfs:comment` in `{name}-{actionName}.ttl` |
