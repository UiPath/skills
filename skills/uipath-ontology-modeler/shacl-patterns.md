# SHACL Patterns Reference — Constraints Artifact

Media-type: `text/turtle` | CLI type flag: `--type constraints`

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
                      sh:datatype xsd:{type} ;
                      sh:minCount 1
                    ] .
```

- Shape name: `shape:{ClassName}Must{BehaviorName}` — business rule as a phrase (e.g. `shape:doctorMustBeLicensed`)
- `rdfs:label`: human-readable description of the rule
- `sh:message`: the violation message displayed to users — write it as a complete sentence
- Property path uses `{ClassName}.{propName}` — **never** just the prop name

---

## Property Constraint Patterns

### Required data property
```turtle
sh:property [
    sh:path     ont:{ClassName}.{propName} ;
    sh:datatype xsd:{type} ;
    sh:minCount 1
] ;
```

### Optional data property (at most one)
```turtle
sh:property [
    sh:path     ont:{ClassName}.{propName} ;
    sh:datatype xsd:{type} ;
    sh:minCount 0 ;
    sh:maxCount 1
] ;
```

### Required object property (relationship)
```turtle
sh:property [
    sh:path     ont:{verbPhrase} ;
    sh:class    ont:{TargetClass} ;
    sh:minCount 1
] ;
```

### Exactly-one object property
```turtle
sh:property [
    sh:path     ont:{verbPhrase} ;
    sh:class    ont:{TargetClass} ;
    sh:minCount 1 ;
    sh:maxCount 1
] ;
```

### Numeric range constraint
```turtle
sh:property [
    sh:path         ont:{ClassName}.{amountProp} ;
    sh:datatype     xsd:decimal ;
    sh:minCount     1 ;
    sh:minInclusive 0
] ;
```

### String pattern constraint
```turtle
sh:property [
    sh:path     ont:{ClassName}.{emailProp} ;
    sh:datatype xsd:string ;
    sh:minCount 1 ;
    sh:pattern  "^[^@]+@[^@]+\\.[^@]+$"
] ;
```

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
                      sh:class    ont:{SideA} ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] ;
    sh:property     [ sh:path     ont:{propToSideB} ;
                      sh:class    ont:{SideB} ;
                      sh:minCount 1 ;
                      sh:maxCount 1
                    ] .
```

Use `sh:minCount 1 ; sh:maxCount 1` on both sides — a junction record that is missing either FK is malformed. Add extra `sh:property` blocks for any additional fields on the junction class (e.g. enrolment date, coverage tier) following the standard required/optional patterns above.

---

## Full Example — Clinic rules.ttl

```turtle
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh:    <http://www.w3.org/ns/shacl#> .
@prefix shape: <https://ontology.uipath.com/shapes#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .

shape:prescriptionMustHaveStatus
    a               sh:NodeShape ;
    rdfs:label      "Prescription must have a status" ;
    sh:message      "A prescription must declare a status" ;
    sh:targetClass  ont:Prescription ;
    sh:property     [ sh:path     ont:Prescription.status ;
                      sh:datatype xsd:string ;
                      sh:minCount 1
                    ] .

shape:patientMustHaveBloodGroup
    a               sh:NodeShape ;
    rdfs:label      "Patient must have a blood group" ;
    sh:message      "A patient record must declare a blood group" ;
    sh:targetClass  ont:Patient ;
    sh:property     [ sh:path     ont:Patient.bloodGroup ;
                      sh:datatype xsd:string ;
                      sh:minCount 1
                    ] .

shape:doctorMustBeLicensed
    a               sh:NodeShape ;
    rdfs:label      "Doctor must be licensed" ;
    sh:message      "A doctor must carry a license number" ;
    sh:targetClass  ont:Doctor ;
    sh:property     [ sh:path     ont:Doctor.licenseNo ;
                      sh:datatype xsd:string ;
                      sh:minCount 1
                    ] .
```
