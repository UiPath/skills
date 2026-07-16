# Functions and Actions — Patterns Reference (W3C FnO)

Both artifact types use the W3C Function Ontology (FnO) in Turtle syntax.

IRI convention: `https://ontology.uipath.com/{name}#` — same slug used in schema.ofn.

---

## Functions — SPARQL read queries

Artifact: `functions.ttl` | CLI type: `functions` | Media type: `text/turtle`

All functions go in a **single file**. Functions are governed SPARQL SELECT queries — the runtime reformulates each into a flat FQS SQL at invocation time. Parameters bind as typed literals. Freely add/removable from a deployed ontology without breaking it.

### File header + USAGE POLICY

The file opens with a USAGE POLICY block. This is where **rules** live — not in `rdfs:comment` (which carries per-function facts). The USAGE POLICY is a cross-function routing guide: it tells an AI agent which function to call for which question type and what output discipline to follow.

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/{name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

#############################
#   Functions (read) — a 'functions' definition artifact (W3C FnO).
#   Uploaded separately from schema/constraints and freely add/removable on a
#   deployed ontology without breaking it. Each is a governed SPARQL SELECT the
#   runtime reformulates to one FQS SQL.
#
#   USAGE POLICY  (routing rules; per-function facts live in rdfs:comment)
#   ROUTING:
#     count...  functions → single-number answers ("how many X are Y")
#     list...   functions → row-level answers ("show me all X with their Y")
#   DISAMBIGUATION (if two functions seem similar, state which phrase maps where):
#     "prescriptions per doctor" → countPrescriptionsPerDoctor (grouped counts, no params)
#     "prescriptions in a status" → countPrescriptionsByStatus (single count, requires status param)
#   OUTPUT:
#     Never add LIMIT unless the user explicitly says "top N" or "first N".
#     Never add DISTINCT unless the target class is a time-series (annotated in schema.ofn).
#   PARAMETERS:
#     Bind as unbound triple variables in the WHERE clause — not via FILTER.
#############################
```

Keep the USAGE POLICY ≤ 30 non-empty lines. Include only sections relevant to the domain — omit sections that don't apply rather than leaving them generic.

### Function with no parameters

```turtle
ont:{functionName}
        a              fno:Function ;
        rdfs:label     "{Human-readable name}" ;
        rdfs:comment   "{What it returns and when to use it. Be specific — used by AI to select the right function.}" ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/{name}#> SELECT ... WHERE { ... }" .
```

No `fno:expects` property when the function takes no parameters — omit it entirely.

### Function with parameters

```turtle
ont:{functionName}
        a              fno:Function ;
        rdfs:label     "{Human-readable name}" ;
        rdfs:comment   "{What it does. Describe params, result rows, when to use it vs other functions.}" ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/{name}#> SELECT ... WHERE { ... ?paramName ... }" ;
        fno:expects    ( ont:param.{functionName}.{param1} ) .

ont:param.{functionName}.{param1}
        a              fno:Parameter ;
        ont:paramName  "{param1}" ;
        ont:paramType  "xsd:{type}" ;
        ont:required   true .
```

Multiple parameters: list them in `fno:expects ( p1 p2 p3 )` and define each `ont:param.*` block immediately after.

---

## SPARQL patterns

Every SPARQL statement is a single inline string on `ont:statement`. Begin with the `PREFIX` declaration.

**Count with filter parameter:**
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:{Class} ; ont:{Class}.{field} ?paramName }
```
The runtime binds `?paramName` from the caller's input — it appears unbound in the WHERE clause, not in a FILTER.

**Aggregate per group (no params):**
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?groupVar (COUNT(?x) AS ?n) WHERE {
  ?x a ont:{Class} ; ont:{Class}.{groupField} ?groupVar
} GROUP BY ?groupVar
```

**Join across two classes (no params):**
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?fieldA ?fieldB WHERE {
  ?x a ont:{ClassA} ; ont:{ClassA}.{fieldA} ?fieldA ; ont:{objectProperty} ?y .
  ?y a ont:{ClassB} ; ont:{ClassB}.{fieldB} ?fieldB
}
```

**Three-way join:**
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?f1 ?f2 ?f3 ?f4 WHERE {
  ?x a ont:{ClassA} ; ont:{ClassA}.{f1} ?f1 ; ont:{ClassA}.{f2} ?f2 ; ont:{propAtoB} ?b ; ont:{propAtoC} ?c .
  ?b a ont:{ClassB} ; ont:{ClassB}.{f3} ?f3 .
  ?c a ont:{ClassC} ; ont:{ClassC}.{f4} ?f4
}
```

### SPARQL naming rules

- Variables: `?camelCase` (e.g. `?doctorName`, not `?doctor_name`)
- Property references: `ont:{ClassName}.{propName}` (exact match with schema.ofn declarations)
- Class references: `ont:{ClassName}` (exact PascalCase match)
- Object properties: `ont:{verbPhrase}` (exact match, no class prefix)

---

## rdfs:comment guidance for functions

Write the comment for an AI agent selecting which function to call. Be explicit:

- What the function **returns** — row shape and whether it is counts/aggregates or individual rows
- **When to use it** — the natural-language questions it answers
- How it relates to **other functions** — "use `list{X}With{Y}` instead to get individual rows"
- What **parameters** it requires

Good:
> "Returns the number of prescriptions that currently have the given status (for example 'active', 'dispensed', or 'cancelled'). Use this to answer 'how many prescriptions are \<status\>'. Requires a status parameter and returns a single count."

Bad:
> "Counts prescriptions by status." — too terse; agent cannot distinguish from a groupBy function.

---

## Actions — SQL write operations

Artifact: `{actionName}.ttl` | CLI type: `actions` | Media type: `text/turtle`

**One file per action.** The file name is the action's identity — `updatePrescriptionStatus.ttl` contains `ont:updatePrescriptionStatus`. Actions are design-time artifacts: stored, validated (W3C FnO), and versioned, but have **no runtime invocation surface**. Freely add/removable without breaking a deployed ontology.

Actions document what write operations are allowed on the ontology data. Even though the runtime does not invoke them directly, they give integrations and AI agents a governed, versioned vocabulary of mutations — so any system that reads the ontology knows exactly what can be changed and how.

### File header

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/{name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

#############################
#   Action (write) — an 'actions' definition artifact, one action per file
#   (fileName is the action's identity). Actions are design-time only: they are
#   stored, validated (W3C) and versioned as artifacts, but have no runtime
#   invocation surface — the runtime executes SPARQL reads and functions only.
#############################
```

### Action template

```turtle
ont:{actionName}
        a               fno:Function ;
        rdfs:label      "{Human-readable name}" ;
        rdfs:comment    "{What it changes, what parameters it takes.}" ;
        ont:kind        "ACTION" ;
        ont:language    "SQL" ;
        ont:statements  ( "{SQL statement 1}" "{SQL statement 2}" ) ;
        fno:expects     ( ont:param.{actionName}.{param1} ont:param.{actionName}.{param2} ) .

ont:param.{actionName}.{param1}
        a              fno:Parameter ;
        ont:paramName  "{param1}" ;
        ont:paramType  "xsd:{type}" ;
        ont:required   true .
```

Note: the property is `ont:statements` (plural, a list) — not `ont:statement` (singular used for functions).

---

## SQL statement syntax

Use entity and field templates — never real table or column names. The runtime resolves them at deploy time.

| Placeholder | Resolves to |
|---|---|
| `{{EntityName}}` | The physical table for the Data Fabric entity |
| `{{EntityName.fieldName}}` | The column for that field (dot notation matches `{ClassName}.{propName}` from schema.ofn) |
| `:paramName` | Bound parameter from `ont:paramName` |

**UPDATE one field:**
```sql
UPDATE {{Prescription}} SET {{Prescription.status}} = :newStatus WHERE {{Prescription.id}} = :id
```

**UPDATE multiple fields:**
```sql
UPDATE {{Order}} SET {{Order.status}} = :status, {{Order.updatedAt}} = :updatedAt WHERE {{Order.id}} = :id
```

**INSERT:**
```sql
INSERT INTO {{Patient}} ({{Patient.name}}, {{Patient.birthDate}}) VALUES (:name, :birthDate)
```

Multiple statements go in the same list: `ont:statements ( "stmt1" "stmt2" )`.

---

## Full examples

### functions.ttl (Clinic)

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

#############################
#   Functions (read) — a 'functions' definition artifact (W3C FnO).
#   Uploaded separately from schema/constraints and freely add/removable on a
#   deployed ontology without breaking it. Each is a governed SPARQL SELECT the
#   runtime reformulates to one FQS SQL.
#
#   USAGE POLICY  (routing rules; per-function facts live in rdfs:comment)
#   ROUTING:
#     count...  functions → single-number answers ("how many X are Y")
#     list...   functions → row-level answers ("which doctor prescribed what")
#   DISAMBIGUATION:
#     "prescriptions per doctor"    → countPrescriptionsPerDoctor (grouped, no params)
#     "prescriptions in a status"   → countPrescriptionsByStatus (single count, requires status)
#   OUTPUT:
#     Never add LIMIT unless the user explicitly says "top N" or "first N".
#     Never add DISTINCT unless the target class is a time-series.
#   PARAMETERS:
#     Bind as unbound triple variables in WHERE — not via FILTER.
#############################

ont:countPrescriptionsByStatus
        a              fno:Function ;
        rdfs:label     "Count prescriptions in a given status" ;
        rdfs:comment   "Returns the number of prescriptions that currently have the given status (for example 'active', 'dispensed', or 'cancelled'). Use this to answer 'how many prescriptions are <status>'. Requires a status parameter and returns a single count row." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:Prescription ; ont:Prescription.status ?status }" ;
        fno:expects    ( ont:param.countPrescriptionsByStatus.status ) .

ont:param.countPrescriptionsByStatus.status
        a              fno:Parameter ;
        ont:paramName  "status" ;
        ont:paramType  "xsd:string" ;
        ont:required   true .

ont:countPrescriptionsPerDoctor
        a              fno:Function ;
        rdfs:label     "Count prescriptions per doctor" ;
        rdfs:comment   "Returns one row per doctor with that doctor's name and the total number of prescriptions they have prescribed. Use this to answer 'how many prescriptions did each doctor write' or to find the most prescribing doctors. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT ?doctor (COUNT(?p) AS ?n) WHERE { ?p a ont:Prescription ; ont:prescribedBy ?d . ?d a ont:Doctor ; ont:Doctor.name ?doctor } GROUP BY ?doctor" .

ont:listPrescriptionsWithDoctorAndPatient
        a              fno:Function ;
        rdfs:label     "List prescriptions with their doctor and patient" ;
        rdfs:comment   "Returns one row per prescription joined to the doctor who prescribed it and the patient it was prescribed for. Each row has the medication name, the prescription status, the prescribing doctor's name, and the patient's name. Use this to answer questions like 'which doctor prescribed what medication to which patient'. Returns raw rows, not counts. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT ?medication ?status ?doctorName ?patientName WHERE { ?p a ont:Prescription ; ont:Prescription.medication ?medication ; ont:Prescription.status ?status ; ont:prescribedBy ?d ; ont:prescriptionFor ?pat . ?d a ont:Doctor ; ont:Doctor.name ?doctorName . ?pat a ont:Patient ; ont:Patient.name ?patientName }" .
```

### updatePrescriptionStatus.ttl (Clinic)

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

ont:updatePrescriptionStatus
        a               fno:Function ;
        rdfs:label      "Update the status of a prescription" ;
        rdfs:comment    "Changes the status of a single prescription, identified by its id, to a new status value (for example 'dispensed' or 'cancelled'). Requires the prescription id and the new status; this modifies data." ;
        ont:kind        "ACTION" ;
        ont:language    "SQL" ;
        ont:statements  ( "UPDATE {{Prescription}} SET {{Prescription.status}} = :newStatus WHERE {{Prescription.id}} = :id" ) ;
        fno:expects     ( ont:param.updatePrescriptionStatus.id ont:param.updatePrescriptionStatus.newStatus ) .

ont:param.updatePrescriptionStatus.id
        a              fno:Parameter ;
        ont:paramName  "id" ;
        ont:paramType  "xsd:integer" ;
        ont:required   true .

ont:param.updatePrescriptionStatus.newStatus
        a              fno:Parameter ;
        ont:paramName  "newStatus" ;
        ont:paramType  "xsd:string" ;
        ont:required   true .
```

---

## Common mistakes

| Mistake | Correct form |
|---|---|
| Singular `ont:statement` for actions | Actions use `ont:statements` (plural, a list) |
| `fno:expects` with no params | Omit `fno:expects` entirely when there are no parameters |
| `FILTER(?x = ?param)` in SPARQL | Bind the param directly in a triple: `; ont:prop ?param` |
| `:param` or `$param` in SQL | Use `:paramName` (colon, no braces) |
| `{Entity}` in SQL (single braces) | Use `{{Entity}}` (double braces) |
| Real column names in SQL | Use `{{Entity.fieldName}}` — runtime resolves via mapping |
| Multiple actions in one file | One action per file; file name = action identity |
| Functions mixed with actions in functions.ttl | Actions go in their own `{actionName}.ttl` files |
