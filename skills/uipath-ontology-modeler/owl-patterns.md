# OWL Functional Syntax — Patterns Reference

IRI convention used throughout: `https://ontology.uipath.com/{name}#`

**`{name}` is the exact name slug passed to `uip ont create` — verbatim, no transformation. Derive it once before generating any files and use the same value in every artifact file (schema, constraints, mapping, functions, actions). A mismatch across files disconnects ontology terms.**

---

## File Header

```
Prefix(:=<https://ontology.uipath.com/{name}#>)
Prefix(owl:=<http://www.w3.org/2002/07/owl#>)
Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)
Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)
Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)
Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)

Ontology(<https://ontology.uipath.com/{name}>

  ... all declarations and axioms ...

)
```

> **`skos:` prefix** — add `Prefix(skos:=<http://www.w3.org/2004/02/skos/core#>)` only when at least one class or property has a synonym (`skos:altLabel`). Omit it otherwise.
>
> **No ontology-level annotations** — do not put `Annotation(rdfs:label ...)` or `Annotation(rdfs:comment ...)` directly inside `Ontology(...)`. The real platform artifacts omit them. Use `AnnotationAssertion(rdfs:label :X ...)` and `AnnotationAssertion(rdfs:comment :X ...)` per class and property in the sections below.

---

## rdfs:label and rdfs:comment — required on every class and every property

`rdfs:label` and `rdfs:comment` are mandatory on every declared class, data property, and object property. They are not optional metadata — without them, the AI agent that reads this ontology cannot answer questions about value domains, grain, cardinality, or FK provenance.

| Element | rdfs:label | rdfs:comment |
|---|---|---|
| Every `Declaration(Class(:X))` | Required — human name of the class | Required — grain statement first: `"ONE row per {business thing}…"` |
| Every `Declaration(DataProperty(:X))` | Required — human name of the property | Required — pick the matching fact type form (see Data Property Block below) |
| Every `Declaration(ObjectProperty(:X))` | Required — human verb phrase | Required — business sentence + FK provenance + cardinality note if "exactly one" |

Missing `rdfs:comment` means the AI agent reading this ontology cannot answer questions about value domains, grain, cardinality, or FK provenance.

---

## OWL 2 QL profile — what is and isn't legal

`uip ont artifacts validate` is syntactic-only — forbidden constructs pass validation but fail any QL reasoner. Scan for violations before uploading.

**QL-legal object property axioms — confirmed by example artifacts, use freely:**
- `InverseObjectProperties(:a :b)` — marks two properties as semantic inverses
- `SubObjectPropertyOf(:child :parent)` — declares a sub-property hierarchy (e.g. `primaryDoctor ⊑ treatingDoctor`)

**Forbidden — never write these:**
- `ObjectExactCardinality` / `DataExactCardinality`
- `ObjectMinCardinality` / `ObjectMaxCardinality` / `DataMinCardinality` / `DataMaxCardinality`
- `ObjectAllValuesFrom` / `DataAllValuesFrom`
- `ObjectHasValue` / `DataHasValue`
- `ObjectOneOf` / `DataOneOf`
- `ObjectUnionOf` / `DataUnionOf`
- `ObjectHasSelf`
- `FunctionalObjectProperty` / `FunctionalDataProperty` / `InverseFunctionalObjectProperty`
- `TransitiveObjectProperty`
- `HasKey`
- Negative assertions

**Express cardinality constraints in annotation text instead:**
```
AnnotationAssertion(rdfs:comment :prescribedBy "Each prescription is issued by exactly one doctor. 'Exactly one' is QL-inexpressible as an axiom; recorded here.")
```

---

## Ordering inside Ontology(...)

Follow the structure of the real artifact files:

1. All `Declaration(Class(...))` statements — grouped at the top
2. All `Declaration(ObjectProperty(...))` statements
3. All `Declaration(DataProperty(...))` statements
4. **`#### Object Properties ####`** section — for each: `AnnotationAssertion(rdfs:label)`, `AnnotationAssertion(rdfs:comment)`, domain, range, then `InverseObjectProperties` / `SubObjectPropertyOf` if applicable
5. **`#### Data Properties ####`** section — for each: `AnnotationAssertion(rdfs:label)`, `AnnotationAssertion(rdfs:comment)`, domain, range
6. **`#### Classes ####`** section — per class: `AnnotationAssertion(rdfs:label)`, `AnnotationAssertion(rdfs:comment)` (grain first), then `skos:altLabel` synonyms if any
7. `SubClassOf(...)` restriction axioms last (existential and inheritance only)

---

## Declaration block (top of file)

All declarations go first before any axioms:

```
Declaration(Class(:Doctor))
Declaration(Class(:Patient))
Declaration(Class(:Prescription))
Declaration(ObjectProperty(:prescribedBy))
Declaration(ObjectProperty(:prescribes))
Declaration(ObjectProperty(:prescriptionFor))
Declaration(DataProperty(:Doctor.licenseNo))
Declaration(DataProperty(:Doctor.name))
Declaration(DataProperty(:Patient.birthDate))
Declaration(DataProperty(:Prescription.status))
```

---

## Object Property Block

```
############################
#   Object Properties
############################

# Object Property: <https://ontology.uipath.com/{name}#{verbPhrase}> ({Human Label})

AnnotationAssertion(rdfs:label :{verbPhrase} "{verb phrase}")
AnnotationAssertion(rdfs:comment :{verbPhrase} "Each {FromClass} {verb phrase} {ToClass}. FK: {FromClass}.{FKField} -> {ToClass}.Id.")
ObjectPropertyDomain(:{verbPhrase} :{FromClass})
ObjectPropertyRange(:{verbPhrase} :{ToClass})
```

When the relationship is "exactly one", append the cardinality note to the comment:
```
AnnotationAssertion(rdfs:comment :prescribedBy "Each Prescription is prescribed by one Doctor. FK: Prescription.DoctorId -> Doctor.Id. 'Exactly one' is QL-inexpressible; recorded here.")
```

**Inverse pair** — when two properties are semantic inverses of each other:
```
AnnotationAssertion(rdfs:label :prescribes "Prescribes")
AnnotationAssertion(rdfs:comment :prescribes "Inverse of :prescribedBy. A doctor prescribes prescriptions.")
InverseObjectProperties(:prescribes :prescribedBy)
ObjectPropertyDomain(:prescribes :Doctor)
ObjectPropertyRange(:prescribes :Prescription)
```

**Sub-property** — when one relationship is a specialisation of another:
```
AnnotationAssertion(rdfs:label :primaryDoctor "Primary doctor")
AnnotationAssertion(rdfs:comment :primaryDoctor "Specialisation of :treatingDoctor. The patient's designated primary doctor.")
SubObjectPropertyOf(:primaryDoctor :treatingDoctor)
ObjectPropertyDomain(:primaryDoctor :Patient)
ObjectPropertyRange(:primaryDoctor :Doctor)
```

- Name with a verb: `orderedBy`, `belongsToCategory`, `prescribedBy`, `prescriptionFor`
- Standard `rdfs:comment` form: business sentence + FK provenance + cardinality note if "exactly one"
- Inverse `rdfs:comment` form: `"Inverse of :{primaryProp}. {One-line meaning.}"`
- Sub-property `rdfs:comment` form: `"Specialisation of :{parentProp}. {One-line meaning.}"`

---

## Data Property Block

**Naming rule: `{ClassName}.{propName}` — never `has{PropName}`.**

```
############################
#   Data Properties
############################

# Data Property: <https://ontology.uipath.com/{name}#{ClassName}.{propName}> ({Human Label})

AnnotationAssertion(rdfs:label :{ClassName}.{propName} "{human label}")
AnnotationAssertion(rdfs:comment :{ClassName}.{propName} "{See comment forms below.}")
AnnotationAssertion(skos:altLabel :{ClassName}.{propName} "{synonym}")
DataPropertyDomain(:{ClassName}.{propName} :{ClassName})
DataPropertyRange(:{ClassName}.{propName} xsd:{type})
```

- Add `skos:altLabel` only when the SDD names a synonym or alias; omit if none
- `rdfs:comment` is required — pick the form that matches what the data contains

Examples: `:Doctor.licenseNo`, `:Patient.birthDate`, `:Prescription.status`

### DataProperty comment forms

**Plain meaning** (most properties):
```
AnnotationAssertion(rdfs:comment :Order.orderDate "The date and time the order was placed.")
```

**Value domain** — exact, complete, case-sensitive enum (verify against real data before writing):
```
AnnotationAssertion(rdfs:comment :Order.orderStatus "Values: 'Pending' | 'Shipped' | 'Delivered' | 'Cancelled' (case-sensitive; copy exactly).")
```

**Code list** — cryptic codes with meanings + phrase-to-code bridge:
```
AnnotationAssertion(rdfs:comment :Contract.status "'A' = finished, no problems | 'B' = finished, not paid | 'C' = running, OK | 'D' = running, in debt. 'Running contract' means status IN ('C','D').")
```

**Format / scale** — zero-padding, stored fraction vs percent, date shape:
```
AnnotationAssertion(rdfs:comment :Score.value "Stored 0–1 fraction; multiply by 100 for a percent answer.")
```

**NULL behavior with condition** (state the fact + the non-action to prevent over-filtering):
```
AnnotationAssertion(rdfs:comment :Score.rank "NULL for ~600 rows. NULLs sort last in DESC — highest-score queries need no IS NOT NULL filter; add it only when ranking ascending.")
```

**Choice set** (Data Fabric CHOICE_SET field — stored as integer NumberId):
```
AnnotationAssertion(rdfs:comment :Order.stage "NumberId. 1=Pending, 2=Shipped, 3=Delivered. Compare integers, not labels.")
```

**Boolean**:
```
AnnotationAssertion(rdfs:comment :Order.isPaid "Compare true/false, never 1/0.")
```

### XSD type mapping

| User says | XSD type |
|---|---|
| text, name, description, code, ID (string) | `xsd:string` |
| price, amount, cost, rate, percentage | `xsd:decimal` |
| count, quantity, number of | `xsd:integer` |
| date, timestamp, created at | `xsd:dateTime` |
| date only (no time) | `xsd:date` |
| true/false, flag, enabled | `xsd:boolean` |
| URL, link, URI | `xsd:anyURI` |

---

## Class Annotation Block

Classes get their annotations in a dedicated section at the end of the property blocks:

```
############################
#   Classes
############################

# Class: <https://ontology.uipath.com/{name}#{ClassName}> ({Human Label})

AnnotationAssertion(rdfs:label :{ClassName} "{Human Label}")
AnnotationAssertion(rdfs:comment :{ClassName} "ONE row per {business thing}, keyed by Id. {What this class represents.}")
AnnotationAssertion(skos:altLabel :{ClassName} "{synonym1}")
```

- `ClassName`: PascalCase, no spaces (e.g., `CustomerOrder`, `RMA_Transaction`)
- Add `skos:altLabel` for every synonym the user mentions or that aids query matching
- `rdfs:comment` must state the **grain** (what one row is) first, then the business meaning

**Grain variants:**

Standard (one row per entity):
```
AnnotationAssertion(rdfs:comment :{ClassName} "ONE row per {business thing}, keyed by Id. Maps Data Fabric entity '{EntityName}'.")
```

Time series (multiple rows per business parent — highest-impact annotation):
```
AnnotationAssertion(rdfs:comment :{ClassName} "TIME SERIES: ~{N} dated rows per {parent}. A per-{parent} question returns duplicates unless SELECT DISTINCT.")
```

---

## Many-to-many relationships

When two classes have a mutual "can have many" relationship (e.g. a Patient can have many InsurancePlans, and an InsurancePlan covers many Patients), OWL 2 QL cannot directly express this as two ObjectProperties — each ObjectProperty has a single domain and range. Model it with a **junction class**.

### Pattern — junction class

Introduce a class that represents the association itself:

```
Classes:
  Patient
  InsurancePlan
  PatientInsurance   ← junction: one row per (patient, plan) pair

ObjectProperties:
  coveredUnder: PatientInsurance → InsurancePlan
  enrolledPatient: PatientInsurance → Patient
```

In the OWL file:
```
Declaration(Class(:PatientInsurance))
Declaration(ObjectProperty(:coveredUnder))
Declaration(ObjectProperty(:enrolledPatient))

AnnotationAssertion(rdfs:label :PatientInsurance "Patient insurance enrolment")
AnnotationAssertion(rdfs:comment :PatientInsurance "ONE row per (patient, plan) enrolment. Junction between Patient and InsurancePlan. Keyed by enrolmentId.")
AnnotationAssertion(rdfs:label :coveredUnder "Covered under")
AnnotationAssertion(rdfs:comment :coveredUnder "Links an enrolment record to its insurance plan. FK: PatientInsurance.planId -> InsurancePlan.Id.")
AnnotationAssertion(rdfs:label :enrolledPatient "Enrolled patient")
AnnotationAssertion(rdfs:comment :enrolledPatient "Links an enrolment record to the patient. FK: PatientInsurance.patientId -> Patient.Id.")
ObjectPropertyDomain(:coveredUnder :PatientInsurance)
ObjectPropertyRange(:coveredUnder :InsurancePlan)
ObjectPropertyDomain(:enrolledPatient :PatientInsurance)
ObjectPropertyRange(:enrolledPatient :Patient)
```

The junction class maps to a real Data Fabric entity (the join/association table). Both FK columns are in that entity.

**When to introduce a junction class:**
- User says "X can have many Y AND Y can be shared across many X"
- There is a real association table in Data Fabric with its own primary key
- The association itself carries extra fields (enrolment date, coverage tier, etc.)

**Do not use a junction class when:**
- One side is strictly "many owned by one" (use a plain ObjectProperty with FK on the many-side entity)
- There is no real association table in Data Fabric

---

## SubClassOf axioms (OWL 2 QL legal forms only)

Add after all Declaration + annotation blocks.

### Existential restriction (QL-legal)
```
SubClassOf(:{Class} ObjectSomeValuesFrom(:{prop} :{Range}))
SubClassOf(:{Class} DataSomeValuesFrom(:{dataProp} xsd:{type}))
```

### Subclass / inheritance (QL-legal)
```
SubClassOf(:{Child} :{Parent})
```

---

## Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Class | PascalCase | `CustomerOrder`, `RMA_Transaction` |
| DataProperty | `{ClassName}.{propName}` camelCase — **never** `has{Prop}` | `Order.orderDate`, `Order.totalAmount` |
| ObjectProperty | camelCase verb phrase | `orderedBy`, `belongsToCategory` |
| Label | natural business phrase, lowercase | `"order date"`, `"prescribed by"` |
