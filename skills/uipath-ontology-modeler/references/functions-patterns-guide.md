# Functions and Actions — Patterns Reference (W3C FnO)

Both artifact types use the W3C Function Ontology (FnO) in Turtle syntax.

IRI convention: `https://ontology.uipath.com/{name}#` — same slug used in schema.ofn.

---

## Functions — SPARQL read queries

Artifact: `{name}-functions.ttl` (combined) or `{name}-functions-{ClassName}.ttl` (per class) | CLI type: `functions` | Media type: `text/turtle`

Functions are governed SPARQL SELECT queries — the runtime reformulates each into a flat FQS SQL at invocation time. Parameters bind as typed literals **before** Ontop reformulates — so the injected value never touches SQL string interpolation. Functions are freely add/removable from a deployed ontology without breaking it.

**File segregation — combined or per class:** both are valid; pick one for the whole ontology, don't mix.
- **Combined** (default): all functions in one `{name}-functions.ttl`. Simplest for small domains or a handful of functions.
- **Per class**: one file per class that has at least one function — `{name}-functions-{ClassName}.ttl` — containing only the functions whose primary SPARQL subject is that class (join functions belong to the class the question is "about", e.g. a function answering "prescriptions per doctor" belongs under `Doctor` if that's the grouping subject, `Prescription` if it's the counted subject — pick by what the function returns one row per). Mirrors the one-file-per-action convention for actions. Prefer this when the domain has functions across many classes (rule of thumb: more than ~2-3 classes involved) — it keeps each file focused and lets an agent re-read just the relevant class's functions instead of the whole set.
- Every function file — combined or per-class — opens with its own USAGE POLICY block (routing rules scoped to that file's functions) and uses the same namespace.

### File header + USAGE POLICY

The file opens with a USAGE POLICY block. This is where **rules** live — not in `rdfs:comment` (which carries per-function facts). The USAGE POLICY is a cross-function routing guide: it tells an AI agent which function to call for which question type and what output discipline to follow.

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/{name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
```

`ont:` is the **ontology's own namespace** — same IRI base as `{name}.ofn` — NOT a generic platform `ont#`. Use `fno:name`, `fno:type`, and `fno:required` (never `ont:paramName`/`ont:paramType`/`ont:required`) on both `fno:Parameter` and `fno:Output` nodes — the backend rejects functions using `ont:paramName`/`ont:paramType` with "function declares no outputs — every function must declare at least one output", since those tokens resolve against the ontology-specific namespace and aren't recognized there. `ont:kind`, `ont:language`, and `ont:statement` on the function node stay `ont:`-prefixed regardless — the backend resolves these three by local name. The SPARQL `PREFIX ont:` inside `ont:statement` strings must also use `<https://ontology.uipath.com/{name}#>` — this is required so `ont:{Class}`/`ont:{Class}.{propName}` inside the SPARQL body resolve against the same schema declarations as everywhere else.

> **Verified 2026-07-29:** this convention (ontology-specific `ont:` + `fno:name`/`fno:type`/`fno:required`) passed `uip ont artifact validate` cleanly across 6 function files and 19 functions in the `s2p-source-to-pay` ontology. The alternative (generic `ont#` + `ont:paramName`/`ont:paramType`) is what caused the "function declares no outputs" failure this fix addresses — do not revert to it.


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
        fno:returns    ( ont:output.{functionName}.{var1} ont:output.{functionName}.{var2} ) .

ont:output.{functionName}.{var1}
        a              fno:Output ;
        rdfs:comment   "{What this output field contains.}" ;
        fno:name       "{var1}" ;
        fno:type       "xsd:{type}" .

ont:output.{functionName}.{var2}
        a              fno:Output ;
        rdfs:comment   "{What this output field contains.}" ;
        fno:name       "{var2}" ;
        fno:type       "xsd:{type}" .
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
        fno:returns    ( ont:output.{functionName}.{var1} ) .

ont:param.{functionName}.{param1}
        a              fno:Parameter ;
        fno:name       "{param1}" ;
        fno:type       "xsd:{type}" ;
        fno:required   true .

ont:output.{functionName}.{var1}
        a              fno:Output ;
        rdfs:comment   "{What this output field contains.}" ;
        fno:name       "{var1}" ;
        fno:type       "xsd:{type}" .
```

Multiple parameters: list them in `fno:expects ( p1 p2 p3 )` and define each `ont:param.*` block immediately after. List all projected variables in `fno:returns ( r1 r2 r3 )` and define each `ont:output.*` block immediately after.

---

### Optional parameter with default

```turtle
ont:param.{functionName}.{param1}
        a              fno:Parameter ;
        fno:name       "{param1}" ;
        fno:type       "xsd:{type}" ;
        fno:required   false .
```

---

### `fno:returns` — output contract

Every function must declare its outputs via `fno:returns`. Each `fno:Output` node names a projected variable from the SELECT and declares its XSD type. This drives: (1) type-checking invoke responses, (2) telling callers the function's signature without reading its SPARQL.

**Output node conventions:**
- Prefix: `ont:output.{functionName}.{varName}` (not `ont:ret.*`)
- Properties: `fno:name` and `fno:type` on both `fno:Output` and `fno:Parameter` nodes
- Each output node must have `rdfs:comment` describing what the field contains
- Format: multi-line one property per line (not single-line)

**The mapping is bidirectional and must be exact:**
- Every variable projected in `SELECT ?x ?y …` must have a matching `ont:output.*` block where `fno:name = "x"` (the variable name without `?`).
- Every `fno:name` value on an output node must correspond to a variable actually projected in the SELECT — no orphaned output nodes.

| `fno:type` value | Use for |
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

Every SPARQL statement goes on `ont:statement`. Begin with the `PREFIX` declaration using `PREFIX ont: <https://ontology.uipath.com/{name}#>`. For short queries, use a single inline string. For complex multi-join queries with `OPTIONAL`, `UNION`, or `HAVING`, use a triple-quoted string.

**Inline (simple queries):**
```turtle
ont:statement  "PREFIX ont: <https://ontology.uipath.com/{name}#> SELECT ?x WHERE { ?x a ont:Class ; ont:Class.field ?field }" .
```

**Triple-quoted (complex queries):**
```turtle
ont:statement  """
  PREFIX ont: <https://ontology.uipath.com/{name}#>
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
For `<`, `>`, `!=`, and range checks, bind via `FILTER`. The parameter variable appears unbound in the WHERE clause and is coerced to the declared `fno:type` before Ontop reformulates.

```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?invoice ?dueDate WHERE {
  ?invoice a ont:Invoice ; ont:Invoice.dueDate ?dueDate ; ont:Invoice.status ?status .
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
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?invoice ?orderedAmount ?receivedAmount WHERE {
  ?invoice a ont:Invoice ; ont:againstPO ?po .
  ?po a ont:PurchaseOrder ; ont:orderedAmount ?orderedAmount .
  OPTIONAL { ?gr a ont:GoodsReceipt ; ont:receiptPO ?po ; ont:receivedAmount ?receivedAmount . }
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
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?entity ?amount WHERE {
  { ?entity a ont:ClassA ; ont:amount ?amount }
  UNION
  { ?entity a ont:ClassB ; ont:amount ?amount }
}
```

### GROUP BY + HAVING
Use `HAVING` to filter on an aggregate result — analogous to SQL `HAVING`. Parameters can appear in `HAVING` expressions.

```sparql
PREFIX ont: <https://ontology.uipath.com/{name}#>
SELECT ?supplier (SUM(?amount) AS ?total) (COUNT(DISTINCT ?invoice) AS ?invoiceCount) WHERE {
  ?supplier a ont:Supplier ; ont:Supplier.name ?name .
  ?invoice a ont:Invoice ; ont:invoiceSupplier ?supplier ; ont:invoicedAmount ?amount .
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

Actions document what write operations are allowed on the ontology data. They give integrations and AI agents a governed, versioned vocabulary of mutations — any system that reads the ontology knows exactly what can be changed and how.

Artifact: `{actionName}.ttl` | CLI type: `actions` | Media type: `text/turtle`

**One file per action.** The file name is the action's identity — `{name}-updatePrescriptionStatus.ttl` contains `{ns}:updatePrescriptionStatus`. Actions are stored, validated (W3C FnO), and **executable** — semantically discoverable by AI agents as tool schemas (name, description, input parameters with types) and invokable via the Actions API. Freely add/removable without breaking a deployed ontology.

**Single-entity, single-record scope.** Each action targets one entity (one `{{Entity}}` in the SQL) and one record (`WHERE pk = :id`). Actions work on both native and federated entities. Reject actions that join multiple entities or target multiple records in a single mutation.

### File header

Actions keep the platform `ont:` namespace for predicates (required for `ont:kind "ACTION"` recognition). A separate `{ns}:` prefix identifies the ontology's own terms.

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix {ns}:  <https://ontology.uipath.com/{name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

#############################
#   Action (write) — an 'actions' definition artifact, one action per file.
#   Stored, validated (W3C FnO), and executable: semantically discoverable
#   by AI agents as tool schemas and invokable via the Actions API.
#############################
```

### Action template

```turtle
{ns}:{actionName}
        a               fno:Function ;
        rdfs:label      "{Human-readable name}" ;
        rdfs:comment    "{What it changes, what parameters it takes, whether it modifies one row or many.}" ;
        ont:kind        "ACTION" ;
        ont:language    "SQL" ;
        ont:statements  ( "{SQL statement 1}" "{SQL statement 2}" ) ;
        fno:expects     ( {ns}:param.{actionName}.{param1} {ns}:param.{actionName}.{param2} ) ;
        fno:returns     ( {ns}:out.{actionName}.rowsAffected ) .

{ns}:param.{actionName}.{param1}
        a              fno:Parameter ;
        ont:paramName  "{param1}" ;
        ont:paramType  "xsd:{type}" ;
        ont:required   true .

{ns}:out.{actionName}.rowsAffected
        a              fno:Output ;
        ont:paramName  "rowsAffected" ;
        ont:paramType  "xsd:integer" .
```

Note: the property is `ont:statements` (plural, a list) — not `ont:statement` (singular used for functions).

`fno:returns` with the `rowsAffected` output is **mandatory** — an action without it is rejected with
`function declares no outputs`. [`action-table-contract-guide.md`](action-table-contract-guide.md)
is the authority on this envelope and on the validation rules; what follows here is the SQL
statement syntax, which is this guide's own.

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

## Full worked examples

A complete worked `functions.ttl` (Clinic, 3 functions) and a complete worked action file (`clinic-updatePrescriptionStatus.ttl`) are in [`functions-patterns-example.md`](functions-patterns-example.md). Read it only if a gate/consistency check fails and you need a concrete reference to self-correct, or you judge the templates above aren't enough to proceed confidently for this request.

---

## Common mistakes

| Mistake | Correct form |
|---|---|
| Missing `fno:returns` on a function | Every function must declare `fno:returns` with typed `fno:Output` nodes |
| `fno:returns` without parentheses (comma-separated) | Use RDF list syntax: `fno:returns ( node1 node2 )` — parentheses are required |
| Output node prefix `ont:ret.` | Use `ont:output.` — correct form is `ont:output.{functionName}.{varName}` |
| `ont:returnName` / `ont:returnType` on output nodes (functions) | Use `fno:name` / `fno:type` on both `fno:Output` and `fno:Parameter` nodes |
| `ont:paramName` / `ont:paramType` on output or param nodes (functions) | Use `fno:name` / `fno:type` — functions use the ontology-specific `ont:` namespace (same as schema.ofn), where `ont:paramName`/`ont:paramType` are NOT recognized and cause "function declares no outputs" |
| `ont:required true` on parameter nodes (functions) | Use `fno:required true` for functions — same reason as above |
| `@prefix ont: <https://ontology.uipath.com/ont#>` in functions | Use `@prefix ont: <https://ontology.uipath.com/{name}#>` — the ontology-specific namespace, same IRI base as schema.ofn; SPARQL `PREFIX ont:` inside `ont:statement` must match |
| *(Actions files are unaffected by the above — actions keep `ont:paramName`/`ont:paramType`/`ont:required` on the generic platform `ont#` namespace per the Actions section below.)* | |
| Single-line output node | Output nodes must be multi-line with `rdfs:comment` describing the returned value |
| Missing `rdfs:comment` on output nodes | Every `fno:Output` node requires `rdfs:comment` explaining what the column contains |
| `http://w3id.org/function/ontology#` for fno: prefix | Use `https://w3id.org/function/ontology#` (https) — backend looks up `https://` FnO resources |
| Singular `ont:statement` for actions | Actions use `ont:statements` (plural, a list) |
| `fno:expects` with no params | Omit `fno:expects` entirely when there are no parameters |
| Using `FILTER` for all params | Use triple binding for equality (`; ont:prop ?param`); use `FILTER` for comparisons (`< > !=`) |
| `:param` or `$param` in SQL | Use `:paramName` (colon, no braces) |
| `{Entity}` in SQL (single braces) | Use `{{Entity}}` (double braces) |
| Real column names in SQL | Use `{{Entity.fieldName}}` — runtime resolves via mapping |
| Multiple actions in one file | One action per file; file name = `{name}-{actionName}.ttl` |
| Functions mixed with actions in functions.ttl | Actions go in their own `{actionName}.ttl` files |
| Omitting `ont:required false` + `ont:default` | Optional params must declare both; the runtime substitutes the default on absent `/invoke` calls |
