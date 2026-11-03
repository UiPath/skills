# OWL Functional Syntax — Patterns Reference

IRI convention used throughout: `https://ontology.uipath.com/{name}#`

**`{name}` is the exact ontology name slug (the Ontology resource name in the local solution) — verbatim, no transformation. Derive it once before generating any files and use the same value in every artifact file (schema, constraints, mapping, summary, context). A mismatch across files disconnects ontology terms.**

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

`rdfs:label` and `rdfs:comment` are mandatory on every declared class, data property, and object property. They are not optional metadata — without them, the AI agent that reads this ontology cannot answer questions about value domains, grain, cardinality, or join columns.

| Element | rdfs:label | rdfs:comment |
|---|---|---|
| Every `Declaration(Class(:X))` | Required — human name of the class | Required — grain statement first: `"ONE row per {business thing}…"` |
| Every `Declaration(DataProperty(:X))` | Required — human name of the property | Required — pick the matching fact type form (see Data Property Block below) |
| Every `Declaration(ObjectProperty(:X))` | Required — human verb phrase | Required — business sentence + join columns + cardinality note if "exactly one" |

Missing `rdfs:comment` means the AI agent reading this ontology cannot answer questions about value domains, grain, cardinality, or join columns.

---

## OWL 2 QL profile — what is and isn't legal

A syntax check alone does not catch these — forbidden constructs parse cleanly but fail any QL reasoner. `uip ont validate --local` (rule `XF-005`) rejects them; fix every violation before packing.

**QL-legal object property axioms — confirmed by example artifacts, use freely:**
- `InverseObjectProperties(:a :b)` — marks two properties as semantic inverses. Only one of the pair gets a mapping join; see the join rule below
- `SubObjectPropertyOf(:child :parent)` — declares a sub-property hierarchy (e.g. `billedTo ⊑ relatedCustomer`). Each of the two still needs its own mapping join

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
AnnotationAssertion(rdfs:comment :placedBy "Each sales order is placed by exactly one customer. 'Exactly one' is QL-inexpressible as an axiom; recorded here.")
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
Declaration(Class(:Customer))
Declaration(Class(:SalesOrder))
Declaration(ObjectProperty(:placedBy))
Declaration(ObjectProperty(:places))
Declaration(DataProperty(:Customer.customerName))
Declaration(DataProperty(:SalesOrder.orderId))
Declaration(DataProperty(:SalesOrder.status))
```

---

## Object Property Block

```
############################
#   Object Properties
############################

# Object Property: <https://ontology.uipath.com/{name}#{verbPhrase}> ({Human Label})

AnnotationAssertion(rdfs:label :{verbPhrase} "{verb phrase}")
AnnotationAssertion(rdfs:comment :{verbPhrase} "Each {FromClass} {verb phrase} {ToClass}. Join: {FromClass}.{relationshipField} = {ToClass}.Id.")
ObjectPropertyDomain(:{verbPhrase} :{FromClass})
ObjectPropertyRange(:{verbPhrase} :{ToClass})
```

When the relationship is "exactly one", append the cardinality note to the comment:
```
AnnotationAssertion(rdfs:comment :placedBy "Each SalesOrder is placed by one Customer. Join: SalesOrder.customer = Customer.Id. 'Exactly one' is QL-inexpressible; recorded here.")
```

**Join rule.** Every object property between two mapped classes needs its own join in the mapping, on plain columns (`XF-015`). The one exception is a property declared `InverseObjectProperties` of a property that already has a join: the inverse is answered from that join and gets none. Sub-properties are not exempt; `billedTo` and `relatedCustomer` each need a join. See [Inverse properties](#inverse-properties).

**Sub-property** — when one relationship is a specialisation of another:
```
AnnotationAssertion(rdfs:label :billedTo "Billed to")
AnnotationAssertion(rdfs:comment :billedTo "Specialisation of :relatedCustomer. The customer the order is billed to. Join: SalesOrder.billTo = Customer.Id.")
SubObjectPropertyOf(:billedTo :relatedCustomer)
ObjectPropertyDomain(:billedTo :SalesOrder)
ObjectPropertyRange(:billedTo :Customer)
```

- Name with a verb: `placedBy`, `belongsToCategory`, `lineOfOrder`
- Standard `rdfs:comment` form: business sentence + join columns + cardinality note if "exactly one"
- Inverse `rdfs:comment` form: `"Inverse of :{primaryProp}. {One-line meaning.}"` (no join of its own)
- Sub-property `rdfs:comment` form: `"Specialisation of :{parentProp}. {One-line meaning.}"`

---

## Inverse properties

A relationship has one `RELATIONSHIP` field, on the referencing entity (`SalesOrder.customer`). Its inverse exists only in the schema, as `InverseObjectProperties`. The inverse has no field on the other entity, no mapping join and no shape of its own.

```
Declaration(ObjectProperty(:places))

AnnotationAssertion(rdfs:label :places "places")
AnnotationAssertion(rdfs:comment :places "Inverse of :placedBy. A customer places sales orders. No join of its own; answered from placedBy (SalesOrder.customer = Customer.Id).")
InverseObjectProperties(:places :placedBy)
ObjectPropertyDomain(:places :Customer)
ObjectPropertyRange(:places :SalesOrder)
```

- Join only `placedBy`, the side whose entity holds the field. `places` gets none.
- Never add a second field on `Customer` for the inverse. When a user describes the relationship from both sides ("customers have orders, each order has a customer"), it is still one field on `SalesOrder`.
- Comment form: `"Inverse of :{primaryProp}. {One-line meaning.}"`.

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

Examples: `:Customer.customerName`, `:SalesOrder.orderId`, `:SalesOrder.status`

### DataProperty comment forms

**Plain meaning** (most properties):
```
AnnotationAssertion(rdfs:comment :SalesOrder.orderDate "The date and time the order was placed.")
```

**Value domain** — a choice-set field: exact, complete, case-sensitive value names, read from the choice set (`uip df choice-sets list-values <CHOICE_SET> --local --output json`). Range is `xsd:string`:
```
AnnotationAssertion(rdfs:comment :SalesOrder.status "Values of choice set OrderStatus: 'Open' | 'Shipped' | 'Cancelled' (case-sensitive; copy exactly).")
```

**Code list** — cryptic codes with meanings + phrase-to-code bridge:
```
AnnotationAssertion(rdfs:comment :Contract.status "'A' = finished, no problems | 'B' = finished, not paid | 'C' = running, OK | 'D' = running, in debt. 'Running contract' means status IN ('C','D').")
```

**Format / scale** — zero-padding, stored fraction vs percent, date shape:
```
AnnotationAssertion(rdfs:comment :Score.value "Stored 0–1 fraction; multiply by 100 for a percent answer.")
```

**NULL behavior with condition** (state the fact and what to leave undone, to prevent over-filtering):
```
AnnotationAssertion(rdfs:comment :Score.rank "NULL for ~600 rows. NULLs sort last in DESC — highest-score queries need no IS NOT NULL filter; add it only when ranking ascending.")
```

**Boolean**:
```
AnnotationAssertion(rdfs:comment :SalesOrder.isPaid "Compare true/false, never 1/0.")
```

### Choosing the XSD range

| User says | XSD type |
|---|---|
| text, name, description, code, ID (string) | `xsd:string` |
| price, amount, cost, rate, percentage | `xsd:decimal` |
| count, quantity, number of | `xsd:integer` |
| date, timestamp, created at | `xsd:dateTime` |
| date only (no time) | `xsd:date` |
| true/false, flag, enabled | `xsd:boolean` |
| one of a fixed set of values (choice set) | `xsd:string` |
| URL, link, URI | `xsd:anyURI` |

Each range maps to a Data Fabric field type; see [`entity-guide.md`](entity-guide.md) for the mapping (for example `xsd:integer` is `DECIMAL` with `decimalPrecision: 0`, `xsd:dateTime` is `DATETIME_WITH_TZ`).

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
AnnotationAssertion(rdfs:comment :{ClassName} "ONE row per {business thing}, keyed by Id. Maps local entity '{EntityName}'.")
```

Time series (multiple rows per business parent — highest-impact annotation):
```
AnnotationAssertion(rdfs:comment :{ClassName} "TIME SERIES: ~{N} dated rows per {parent}. A per-{parent} question returns duplicates unless SELECT DISTINCT.")
```

---

## Every class must be backed by data — no annotation-only classes

Every `Declaration(Class(...))` must be (a) the domain of ≥1 `DataPropertyDomain`/`ObjectPropertyDomain`, and (b) instantiated in `{name}-mapping.yarrrml.yml` over a local entity. A class that fails either — typically a "role"/"actor" concept (approving manager, external system name, job title) with zero properties and no entity — parses as valid OWL but fails `uip ont validate --local` (`XF-009`, every class needs a backing entity). If the concept is narrative-only, fold it into the relevant property's `rdfs:comment` instead (e.g. `Payment.approvedBy`'s comment) rather than declaring a class.

**Real properties don't mean relationships are modeled.** A `DataProperty` whose value equals another class's key (e.g. a text column that happens to hold another entity's key) is two matching columns, not a relationship, until the entity has a `RELATIONSHIP` field and the schema an `ObjectProperty` (with `ObjectPropertyDomain`/`ObjectPropertyRange`) wired into the mapping as a join. Every object property between two mapped classes needs that join (`XF-015`), and every join needs a declared object property (`XF-014`). See [`relationships-guide.md`](relationships-guide.md).

---

## Many-to-many relationships

When two classes have a mutual "can have many" relationship (e.g. a SalesOrder can contain many Products, and a Product appears on many SalesOrders), OWL 2 QL cannot directly express this as two ObjectProperties — each ObjectProperty has a single domain and range. Model it with a **junction class**.

### Pattern — junction class

Introduce a class that represents the association itself:

```
Classes:
  SalesOrder
  Product
  OrderLine   ← junction: one row per (order, product) pair

ObjectProperties:
  lineOfOrder: OrderLine → SalesOrder
  lineOfProduct: OrderLine → Product
```

In the OWL file:
```
Declaration(Class(:OrderLine))
Declaration(ObjectProperty(:lineOfOrder))
Declaration(ObjectProperty(:lineOfProduct))

AnnotationAssertion(rdfs:label :OrderLine "Order line")
AnnotationAssertion(rdfs:comment :OrderLine "ONE row per (order, product) line. Junction between SalesOrder and Product.")
AnnotationAssertion(rdfs:label :lineOfOrder "Line of order")
AnnotationAssertion(rdfs:comment :lineOfOrder "Links an order line to its order. Join: OrderLine.order = SalesOrder.Id.")
AnnotationAssertion(rdfs:label :lineOfProduct "Line of product")
AnnotationAssertion(rdfs:comment :lineOfProduct "Links an order line to its product. Join: OrderLine.product = Product.Id.")
ObjectPropertyDomain(:lineOfOrder :OrderLine)
ObjectPropertyRange(:lineOfOrder :SalesOrder)
ObjectPropertyDomain(:lineOfProduct :OrderLine)
ObjectPropertyRange(:lineOfProduct :Product)
```

The junction class maps to its own local entity. It holds one `RELATIONSHIP` field per side.

**When to introduce a junction class:**
- User says "X can have many Y AND Y can be shared across many X"
- There is a real association entity with its own `Id`
- The association itself carries extra fields (quantity, unit price, etc.)

**Do not use a junction class when:**
- One side is strictly "many owned by one" (use a plain ObjectProperty with `RELATIONSHIP` field on the many-side entity)
- There is no association entity

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
| DataProperty | `{ClassName}.{propName}` camelCase — **never** `has{Prop}` | `SalesOrder.orderDate`, `SalesOrder.totalAmount` |
| ObjectProperty | camelCase verb phrase | `orderedBy`, `belongsToCategory` |
| Label | natural business phrase, lowercase | `"order date"`, `"placed by"` |
