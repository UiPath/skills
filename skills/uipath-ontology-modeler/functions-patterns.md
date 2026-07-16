# Functions and Actions — Patterns Reference (W3C FnO)

Both artifact types use the W3C Function Ontology (FnO) in Turtle syntax.

IRI convention: `https://ontology.uipath.com/{name}#` — same slug used in schema.ofn.

---

## Functions — SPARQL read queries

Artifact: `functions.ttl` | CLI type: `functions` | Media type: `text/turtle`

All functions go in a **single file**. Functions are governed SPARQL SELECT queries — the runtime reformulates each into a flat FQS SQL at invocation time. Parameters bind as typed literals **before** Ontop reformulates — so the injected value never touches SQL string interpolation. Functions are freely add/removable from a deployed ontology without breaking it.

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
#     Equality lookups: bind as unbound triple variable — ?p ; ont:Prop ?param
#     Comparisons (< > !=): bind via FILTER — FILTER (?field < ?param)
#############################
```

Keep the USAGE POLICY ≤ 30 non-empty lines. Include only sections relevant to the domain — omit sections that don't apply rather than leaving them generic.

---

### Function with no parameters

```turtle
ont:{functionName}
        a              fno:Function ;
        rdfs:label     "{Human-readable name}" ;
        rdfs:comment   "{What it returns and when to use it. Be specific — used by AI to select the right function.}" ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/{name}#> SELECT ?var1 ?var2 WHERE { ... }" ;
        fno:returns    ( ont:ret.{functionName}.{var1}
                         ont:ret.{functionName}.{var2} ) .

ont:ret.{functionName}.{var1}  a fno:Output ; ont:returnName "{var1}" ; ont:returnType "xsd:{type}" .
ont:ret.{functionName}.{var2}  a fno:Output ; ont:returnName "{var2}" ; ont:returnType "xsd:{type}" .
```

No `fno:expects` when the function takes no parameters — omit it entirely.

---

### Function with required parameters

```turtle
ont:{functionName}
        a              fno:Function ;
        rdfs:label     "{Human-readable name}" ;
        rdfs:comment   "{What it does. Describe params, result rows, when to use it vs other functions.}" ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/{name}#> SELECT ?var1 WHERE { ... ?param1 ... }" ;
        fno:expects    ( ont:param.{functionName}.{param1} ) ;
        fno:returns    ( ont:ret.{functionName}.{var1} ) .

ont:param.{functionName}.{param1}
        a              fno:Parameter ;
        ont:paramName  "{param1}" ;
        ont:paramType  "xsd:{type}" ;
        ont:required   true .

ont:ret.{functionName}.{var1}  a fno:Output ; ont:returnName "{var1}" ; ont:returnType "xsd:{type}" .
```

Multiple parameters: list them in `fno:expects ( p1 p2 p3 )` and define each `ont:param.*` block immediately after. List all projected variables in `fno:returns ( r1 r2 r3 )` and define each `ont:ret.*` block immediately after.

---

### Optional parameter with default

```turtle
ont:param.{functionName}.{param1}
        a              fno:Parameter ;
        ont:paramName  "{param1}" ;
        ont:paramType  "xsd:{type}" ;
        ont:required   false ;
        ont:default    "{defaultValue}" .
```

The runtime applies `ont:default` when the caller omits the parameter from `/invoke`.

---

### `fno:returns` — output contract

Every function must declare its outputs via `fno:returns`. Each `fno:Output` node names a projected variable from the SELECT and declares its XSD type. This drives: (1) type-checking invoke responses, (2) telling callers the function's signature without reading its SPARQL.

**The mapping is bidirectional and must be exact:**
- Every variable projected in `SELECT ?x ?y …` must have a matching `ont:ret.*` block where `ont:returnName = "x"` (the variable name without `?`).
- Every `ont:returnName` value must correspond to a variable actually projected in the SELECT — no orphaned return nodes.

| `ont:returnType` value | Use for |
|---|---|
| `"xsd:string"` | Text values |
| `"xsd:integer"` | Integer counts or IDs |
| `"xsd:decimal"` | Currency, amounts, ratios |
| `"xsd:date"` | Date values (`YYYY-MM-DD`) |
| `"xsd:dateTime"` | Date + time |
| `"xsd:boolean"` | True/false |
| `"xsd:anyURI"` | Subject IRIs (e.g. `?invoice`, `?supplier`) |

---

## SPARQL patterns

Every SPARQL statement goes on `ont:statement`. Begin with the `PREFIX` declaration. For short queries, use a single inline string. For complex multi-join queries with `OPTIONAL`, `UNION`, or `HAVING`, use a triple-quoted string.

**Inline (simple queries):**
```turtle
ont:statement  "PREFIX ont: <...#> SELECT ?x WHERE { ?x a ont:Class ; ont:Class.field ?field }" .
```

**Triple-quoted (complex queries):**
```turtle
ont:statement  """
  PREFIX : <https://ontology.uipath.com/{name}#>
  SELECT ?var1 ?var2 WHERE {
    ...
  }""" .
```

---

### Count with equality parameter (triple binding)
For equality lookups, bind the parameter directly in a triple pattern — the unbound variable `?status` is matched against the parameter value at runtime.

```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:{Class} ; ont:{Class}.{field} ?status }
```

### Count with comparison parameter (FILTER binding)
For `<`, `>`, `!=`, and range checks, bind via `FILTER`. The parameter variable appears unbound in the WHERE clause and is coerced to the declared `ont:paramType` before Ontop reformulates.

```sparql
PREFIX : <https://ontology.uipath.com/{name}#>
SELECT ?invoice ?dueDate WHERE {
  ?invoice a :Invoice ; :Invoice.dueDate ?dueDate ; :Invoice.status ?status .
  FILTER (?status != "paid")
  FILTER (?dueDate < ?asOfDate)
}
```

### Aggregate per group (no params)
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?groupVar (COUNT(?x) AS ?n) WHERE {
  ?x a ont:{Class} ; ont:{Class}.{groupField} ?groupVar
} GROUP BY ?groupVar
```

### Join across two classes
```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?fieldA ?fieldB WHERE {
  ?x a ont:{ClassA} ; ont:{ClassA}.{fieldA} ?fieldA ; ont:{objectProperty} ?y .
  ?y a ont:{ClassB} ; ont:{ClassB}.{fieldB} ?fieldB
}
```

### OPTIONAL join (may not exist)
Use `OPTIONAL` when a related entity may not exist for every row (e.g. a goods receipt that hasn't arrived yet). Use `COALESCE` to substitute a default when the optional value is absent.

```sparql
PREFIX : <https://ontology.uipath.com/{name}#>
SELECT ?invoice ?orderedAmount ?receivedAmount WHERE {
  ?invoice a :Invoice ; :againstPO ?po .
  ?po a :PurchaseOrder ; :orderedAmount ?orderedAmount .
  OPTIONAL { ?gr a :GoodsReceipt ; :receiptPO ?po ; :receivedAmount ?receivedAmount . }
}
```

### BIND arithmetic
Use `BIND` to compute derived values inline. `COALESCE` handles optional bindings; `IF` / `ABS` are Ontop-supported arithmetic.

```sparql
BIND (ABS(?invoicedAmount - ?orderedAmount)             AS ?poVariance)
BIND (ABS(?invoicedAmount - COALESCE(?receivedAmount, 0)) AS ?grVariance)
BIND (IF(?poVariance > ?grVariance, ?poVariance, ?grVariance) AS ?maxVariance)
```

### UNION (two independent sub-graphs)
Use `UNION` to combine results from two different triple patterns. Variables shared across branches are projected; variables unique to one branch are unbound (`UNDEF`) in the other.

```sparql
PREFIX : <https://ontology.uipath.com/{name}#>
SELECT ?entity ?amount WHERE {
  { ?entity a :ClassA ; :amount ?amount }
  UNION
  { ?entity a :ClassB ; :amount ?amount }
}
```

### GROUP BY + HAVING
Use `HAVING` to filter on an aggregate result — analogous to SQL `HAVING`. Parameters can appear in `HAVING` expressions.

```sparql
PREFIX : <https://ontology.uipath.com/{name}#>
SELECT ?supplier (SUM(?amount) AS ?total) (COUNT(DISTINCT ?invoice) AS ?invoiceCount) WHERE {
  ?supplier a :Supplier ; :Supplier.name ?name .
  ?invoice a :Invoice ; :invoiceSupplier ?supplier ; :invoicedAmount ?amount .
}
GROUP BY ?supplier
HAVING (SUM(?amount) >= ?minExposure)
```

### Combined complex pattern
All of the above can appear in a single self-contained statement — `UNION` + `OPTIONAL` + `BIND`/`COALESCE`/`IF` + `GROUP BY` + `HAVING`. Every operator shown is Ontop-supported and reformulates to one flat SQL.

---

### SPARQL naming rules

- Variables: `?camelCase` (e.g. `?doctorName`, not `?doctor_name`)
- Property references: `ont:{ClassName}.{propName}` (exact match with schema.ofn declarations)
- Class references: `ont:{ClassName}` (exact PascalCase match)
- Object properties: `ont:{verbPhrase}` (exact match, no class prefix)
- Return variable names must match the SELECT projection exactly

---

## rdfs:comment guidance for functions

Write the comment for an AI agent selecting which function to call. Be explicit:

- What the function **returns** — row shape and whether it is counts/aggregates or individual rows
- **When to use it** — the natural-language questions it answers
- How it relates to **other functions** — "use `list{X}With{Y}` instead to get individual rows"
- What **parameters** it requires and what types they are

Good:
> "Returns the number of prescriptions that currently have the given status (for example 'active', 'dispensed', or 'cancelled'). Use this to answer 'how many prescriptions are \<status\>'. Requires a status parameter and returns a single count."

Bad:
> "Counts prescriptions by status." — too terse; agent cannot distinguish from a groupBy function.

---

## Actions — SQL write operations

Artifact: `{actionName}.ttl` | CLI type: `actions` | Media type: `text/turtle`

**One file per action.** The file name is the action's identity — `updatePrescriptionStatus.ttl` contains `ont:updatePrescriptionStatus`. Actions are design-time artifacts: stored, validated (W3C FnO), and versioned, but have **no runtime invocation surface**. Freely add/removable without breaking a deployed ontology.

Actions document what write operations are allowed on the ontology data. Even though the runtime does not invoke them directly, they give integrations and AI agents a governed, versioned vocabulary of mutations — so any system that reads the ontology knows exactly what can be changed and how.

**Actions must not target federated entities** — the external system rejects writes at runtime. If the SDD describes writes on a federated class, flag it before generating any action file.

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
#     Equality lookups: bind as unbound triple variable — ?p ; ont:Prop ?param
#     Comparisons (< > !=): bind via FILTER — FILTER (?field < ?param)
#############################

ont:countPrescriptionsByStatus
        a              fno:Function ;
        rdfs:label     "Count prescriptions in a given status" ;
        rdfs:comment   "Returns the number of prescriptions that currently have the given status (for example 'active', 'dispensed', or 'cancelled'). Use this to answer 'how many prescriptions are <status>'. Requires a status parameter and returns a single count row." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:Prescription ; ont:Prescription.status ?status }" ;
        fno:expects    ( ont:param.countPrescriptionsByStatus.status ) ;
        fno:returns    ( ont:ret.countPrescriptionsByStatus.n ) .

ont:param.countPrescriptionsByStatus.status
        a              fno:Parameter ;
        ont:paramName  "status" ;
        ont:paramType  "xsd:string" ;
        ont:required   true .

ont:ret.countPrescriptionsByStatus.n  a fno:Output ; ont:returnName "n" ; ont:returnType "xsd:integer" .

ont:countPrescriptionsPerDoctor
        a              fno:Function ;
        rdfs:label     "Count prescriptions per doctor" ;
        rdfs:comment   "Returns one row per doctor with that doctor's name and the total number of prescriptions they have prescribed. Use this to answer 'how many prescriptions did each doctor write' or to find the most prescribing doctors. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT ?doctor (COUNT(?p) AS ?n) WHERE { ?p a ont:Prescription ; ont:prescribedBy ?d . ?d a ont:Doctor ; ont:Doctor.name ?doctor } GROUP BY ?doctor" ;
        fno:returns    ( ont:ret.countPrescriptionsPerDoctor.doctor
                         ont:ret.countPrescriptionsPerDoctor.n ) .

ont:ret.countPrescriptionsPerDoctor.doctor  a fno:Output ; ont:returnName "doctor" ; ont:returnType "xsd:string" .
ont:ret.countPrescriptionsPerDoctor.n       a fno:Output ; ont:returnName "n"      ; ont:returnType "xsd:integer" .

ont:listPrescriptionsWithDoctorAndPatient
        a              fno:Function ;
        rdfs:label     "List prescriptions with their doctor and patient" ;
        rdfs:comment   "Returns one row per prescription joined to the doctor who prescribed it and the patient it was prescribed for. Each row has the medication name, the prescription status, the prescribing doctor's name, and the patient's name. Use this to answer questions like 'which doctor prescribed what medication to which patient'. Returns raw rows, not counts. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/ont#> SELECT ?medication ?status ?doctorName ?patientName WHERE { ?p a ont:Prescription ; ont:Prescription.medication ?medication ; ont:Prescription.status ?status ; ont:prescribedBy ?d ; ont:prescriptionFor ?pat . ?d a ont:Doctor ; ont:Doctor.name ?doctorName . ?pat a ont:Patient ; ont:Patient.name ?patientName }" ;
        fno:returns    ( ont:ret.listPrescriptions.medication
                         ont:ret.listPrescriptions.status
                         ont:ret.listPrescriptions.doctorName
                         ont:ret.listPrescriptions.patientName ) .

ont:ret.listPrescriptions.medication   a fno:Output ; ont:returnName "medication"   ; ont:returnType "xsd:string" .
ont:ret.listPrescriptions.status       a fno:Output ; ont:returnName "status"       ; ont:returnType "xsd:string" .
ont:ret.listPrescriptions.doctorName   a fno:Output ; ont:returnName "doctorName"   ; ont:returnType "xsd:string" .
ont:ret.listPrescriptions.patientName  a fno:Output ; ont:returnName "patientName"  ; ont:returnType "xsd:string" .
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
| Missing `fno:returns` on a function | Every function must declare `fno:returns` with typed `fno:Output` nodes |
| Singular `ont:statement` for actions | Actions use `ont:statements` (plural, a list) |
| `fno:expects` with no params | Omit `fno:expects` entirely when there are no parameters |
| Using `FILTER` for all params | Use triple binding for equality (`; ont:prop ?param`); use `FILTER` for comparisons (`< > !=`) |
| `:param` or `$param` in SQL | Use `:paramName` (colon, no braces) |
| `{Entity}` in SQL (single braces) | Use `{{Entity}}` (double braces) |
| Real column names in SQL | Use `{{Entity.fieldName}}` — runtime resolves via mapping |
| Multiple actions in one file | One action per file; file name = action identity |
| Functions mixed with actions in functions.ttl | Actions go in their own `{actionName}.ttl` files |
| Omitting `ont:required false` + `ont:default` | Optional params must declare both; the runtime substitutes the default on absent `/invoke` calls |
