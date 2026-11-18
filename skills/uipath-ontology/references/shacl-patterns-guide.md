# SHACL Patterns Reference — Constraints Artifact

Artifact type: `constraints` | Media type: `text/turtle` | File: `{name}-constraints.ttl` (or `{name}-constraints-{area}.ttl` when split by area)

**Optional.** The ontology service stores a constraints file without parsing or using it. Write one only when the user supplies one or asks for it; otherwise record the rules in the schema's `rdfs:comment` text. The rest of this guide applies when a constraints file is written.

Check each file with `uip ont artifacts check`, attach it with `uip ont files add`, and let `uip ont validate --local` confirm it against the schema and mapping. Every `sh:targetClass`, `sh:path` and `sh:class` must name a term declared in `{name}.ofn`, and every class needs a shape. A `.ttl` that declares no SHACL shape gets `SHC-011` (WARNING): it is probably another artifact type saved under the wrong extension.

---

## File Header

```turtle
@prefix ont:   <https://ontology.uipath.com/{name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix shape: <https://ontology.uipath.com/shapes#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
```

---

## Shape convention — one NodeShape per rule

Each constraint is its own named `NodeShape`. This matches the real artifact format and produces specific, readable violation messages.

```turtle
shape:{ClassMustHaveRule}
    a               sh:NodeShape ;
    rdfs:label      "{Human description of this rule}" ;
    sh:message      "{Violation message shown when this rule fails}" ;
    sh:targetClass  ont:{ClassName} ;
    sh:property     [ sh:path     ont:{ClassName}.{propName} ;
                      sh:name     "{property label}" ;
                      sh:datatype xsd:{type} ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] .
```

- Shape name: `shape:{ClassName}Must{BehaviorName}` in PascalCase — the rule as a phrase (for example `shape:SalesOrderMustHaveCustomer`)
- `rdfs:label`: human-readable description of the rule
- `sh:message`: the violation message displayed to users — write it as a complete sentence
- Property path uses `{ClassName}.{propName}` — **never** just the prop name
- Constraints cover rules about data: required, range, pattern, value list, relationship class.

### Every property block carries `sh:name` and `sh:maxCount`

`uip ont artifacts check` warns on each `sh:property` block without `sh:name` (`SHC-007`) or `sh:maxCount` (`SHC-006`).

1. `sh:name` is the property's `rdfs:label`. Add it to every block.
2. `sh:maxCount 1` goes on every block except a `CHOICE_SET_MULTIPLE` property. Each data property is one entity column, and each relationship is one `RELATIONSHIP` field on the referencing entity, so both hold at most one value per row. The inverse side gets no shape.
3. A `CHOICE_SET_MULTIPLE` property holds several values per row: never give it `sh:maxCount 1`. The `SHC-006` WARNING on that block is expected. Leave it, and do not count it as a fix to make.

---

## Property Constraint Patterns

### Required data property
```turtle
sh:property [
    sh:path     ont:{ClassName}.{propName} ;
    sh:name     "{property label}" ;
    sh:datatype xsd:{type} ;
    sh:minCount 1 ;
    sh:maxCount 1
] ;
```

### Optional data property
```turtle
sh:property [
    sh:path     ont:{ClassName}.{propName} ;
    sh:name     "{property label}" ;
    sh:datatype xsd:{type} ;
    sh:maxCount 1
] ;
```

### Required relationship (exactly one)
```turtle
sh:property [
    sh:path     ont:{verbPhrase} ;
    sh:name     "{verb phrase label}" ;
    sh:class    ont:{TargetClass} ;
    sh:minCount 1 ;
    sh:maxCount 1
] ;
```

An optional relationship drops `sh:minCount 1`.

### Numeric range constraint
```turtle
sh:property [
    sh:path         ont:{ClassName}.{amountProp} ;
    sh:name         "{property label}" ;
    sh:datatype     xsd:decimal ;
    sh:minCount     1 ;
    sh:maxCount     1 ;
    sh:minInclusive 0
] ;
```

### String pattern constraint
```turtle
sh:property [
    sh:path     ont:{ClassName}.{emailProp} ;
    sh:name     "{property label}" ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
    sh:maxCount 1 ;
    sh:pattern  "^[^@]+@[^@]+\\.[^@]+$"
] ;
```

---

## Value list from a choice set

A `CHOICE_SET_SINGLE` field holds one of the values of its choice set (`sh:maxCount 1`). The constraint lists those values by name, exactly as the choice set spells them (case-sensitive), with the choice set's value names in the same order.

```turtle
shape:SalesOrderStatusMustBeListed
    a               sh:NodeShape ;
    rdfs:label      "Sales order status must be an OrderStatus value" ;
    sh:message      "A sales order status must be Open, Shipped or Cancelled" ;
    sh:targetClass  ont:SalesOrder ;
    sh:property     [ sh:path     ont:SalesOrder.status ;
                      sh:name     "status" ;
                      sh:datatype xsd:string ;
                      sh:minCount 1 ;
                      sh:maxCount 1 ;
                      sh:in       ( "Open" "Shipped" "Cancelled" )
                    ] .
```

- Read the names with `uip df choice-sets list-values <CHOICE_SET> --local --output json`. Never type them from memory.
- Use `sh:datatype xsd:string`. The value name is the literal, not an identifier.
- A `CHOICE_SET_MULTIPLE` field is the same shape without `sh:maxCount 1`: each selected value is one triple, and each must be in the list. Its `SHC-006` WARNING is expected ([rule 3 above](#every-property-block-carries-shname-and-shmaxcount)).
- When the choice set gains or loses a value, update the `sh:in` list in the same change.

---

## Junction class shapes (many-to-many)

A junction class has two required object properties — one to each side of the relationship. Write one shape that enforces both.

```turtle
shape:{JunctionClass}MustLinkBothSides
    a               sh:NodeShape ;
    rdfs:label      "{JunctionClass} must link both sides" ;
    sh:message      "Each {JunctionClass} record must reference exactly one {SideA} and one {SideB}" ;
    sh:targetClass  ont:{JunctionClass} ;
    sh:property     [ sh:path     ont:{propToSideA} ;
                      sh:name     "{side A label}" ;
                      sh:class    ont:{SideA} ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] ;
    sh:property     [ sh:path     ont:{propToSideB} ;
                      sh:name     "{side B label}" ;
                      sh:class    ont:{SideB} ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] .
```

Use `sh:minCount 1 ; sh:maxCount 1` on both sides — a junction record that is missing either FK is malformed. Add extra `sh:property` blocks for any additional fields on the junction class (e.g. enrolment date, coverage tier) following the standard required/optional patterns above.

---

## Full worked example

A complete `SalesOps-constraints.ttl` for the Orders domain: `Customer`, `SalesOrder.customer` (a `RELATIONSHIP`) and `SalesOrder.status` (choice set `OrderStatus`). It is a model to adapt, not a file to copy verbatim.

```turtle
@prefix ont:   <https://ontology.uipath.com/SalesOps#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix shape: <https://ontology.uipath.com/shapes#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

shape:CustomerMustHaveName
    a               sh:NodeShape ;
    rdfs:label      "Customer must have a name" ;
    sh:message      "A customer must declare a name" ;
    sh:targetClass  ont:Customer ;
    sh:property     [ sh:path     ont:Customer.customerName ;
                      sh:name     "customer name" ;
                      sh:datatype xsd:string ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] .

shape:SalesOrderMustHaveCustomer
    a               sh:NodeShape ;
    rdfs:label      "Sales order must have a customer" ;
    sh:message      "A sales order must be placed by exactly one customer" ;
    sh:targetClass  ont:SalesOrder ;
    sh:property     [ sh:path     ont:placedBy ;
                      sh:name     "placed by" ;
                      sh:class    ont:Customer ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] .

shape:SalesOrderStatusMustBeListed
    a               sh:NodeShape ;
    rdfs:label      "Sales order status must be an OrderStatus value" ;
    sh:message      "A sales order status must be Open, Shipped or Cancelled" ;
    sh:targetClass  ont:SalesOrder ;
    sh:property     [ sh:path     ont:SalesOrder.status ;
                      sh:name     "status" ;
                      sh:datatype xsd:string ;
                      sh:minCount 1 ;
                      sh:maxCount 1 ;
                      sh:in       ( "Open" "Shipped" "Cancelled" )
                    ] .
```
