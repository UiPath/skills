# OWL 2 QL + R2RML — generation reference

The ontology carries **meaning** (from the author's answers); the R2RML carries
the **binding** (from the entity schema). Same selected entities feed both.

## 1. Type mapping

`FieldDataType.Name` → ontology `DataPropertyRange` and R2RML `rr:datatype`.

| `FieldDataType.Name` | xsd datatype | R2RML `rr:datatype` |
|---|---|---|
| STRING / TEXT / EMAIL / PHONE | `xsd:string` | `xsd:string` (often omittable — default) |
| INTEGER / AUTONUMBER | `xsd:integer` | `xsd:integer` |
| DECIMAL / FLOAT | `xsd:decimal` | `xsd:decimal` |
| BOOLEAN | `xsd:boolean` | `xsd:boolean` |
| DATE | `xsd:date` | `xsd:date` |
| DATETIME | `xsd:dateTimeStamp` | `xsd:dateTime` |
| UNIQUEIDENTIFIER / GUID | `xsd:string` | `xsd:string` |
| CHOICE_SET_SINGLE | (see Choice sets) | `xsd:integer` (the NumberId) |
| CHOICE_SET_MULTIPLE | (see Choice sets) | `xsd:integer`, repeated |
| RELATIONSHIP / FK | **ObjectProperty** | referencing object map (join) |
| (type the author leaves unstated) | `xsd:string` + `rdfs:comment` | `xsd:string` |

Boolean rule worth a comment: compare to literal `true`/`false`, never `1`/`0`.

## 2. OWL 2 QL profile

The CLI does **not** check the profile (`verify` is syntactic only) — emit valid
QL so the ontology is sound.

**Allowed:** `Declaration`, `SubClassOf`, `EquivalentClasses`,
`DisjointClasses`, `SubObjectPropertyOf`, `EquivalentObjectProperties`,
`InverseObjectProperties`, `ObjectPropertyDomain`, `ObjectPropertyRange`,
`DisjointObjectProperties`, `SymmetricObjectProperty`, `AsymmetricObjectProperty`,
`ReflexiveObjectProperty`, `IrreflexiveObjectProperty`, `SubDataPropertyOf`,
`EquivalentDataProperties`, `DataPropertyDomain`, `DataPropertyRange`,
`DisjointDataProperties`, `AnnotationAssertion`.

**Avoid (outside QL):** `FunctionalObjectProperty`,
`InverseFunctionalObjectProperty`, `FunctionalDataProperty`,
`TransitiveObjectProperty`, all cardinality (`Object/DataMin/Max/Exact`),
`HasKey`, `ObjectHasSelf`, `ObjectAllValuesFrom`/`DataAllValuesFrom`,
`ObjectOneOf`/`DataOneOf`, `SameIndividual`/`DifferentIndividuals`.

If the author states a constraint QL can't hold (e.g. "exactly one customer",
"status must be one of …"), record it as an `rdfs:comment` in v1. (A future
version emits these as a SHACL slot.)

## 3. Ontology axioms — patterns

```
Declaration(Class(:Order))
AnnotationAssertion(rdfs:comment :Order "A purchase placed by a customer. Maps Data Fabric entity 'Order'.")

Declaration(DataProperty(:orderTotal))
DataPropertyDomain(:orderTotal :Order)
DataPropertyRange(:orderTotal xsd:decimal)
AnnotationAssertion(rdfs:comment :orderTotal "Gross amount. Maps Order.Total.")

Declaration(ObjectProperty(:placedBy))           # relationship
ObjectPropertyDomain(:placedBy :Order)
ObjectPropertyRange(:placedBy :Customer)
AnnotationAssertion(rdfs:comment :placedBy "Each order is placed by one customer. Maps Order FK -> Customer.")
```

- Default Ontology IRI: `http://uipath.com/datafabric/<name>`.
- **Provenance:** the `Maps <Entity>.<Field>` note in `rdfs:comment` ties each term to its source and keeps the OFN and R2RML in agreement.
- **Disambiguate** property names across classes (`customerName`, not a second bare `name`).

## 4. R2RML — patterns

Turtle. Prefixes:

```turtle
@prefix rr:   <http://www.w3.org/ns/r2rml#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix :     <http://uipath.com/datafabric/NAME#> .
```

**One TriplesMap per entity.** Entity `Name` = logical table; primary key `Id` =
subject template; field `Name` = column.

```turtle
:OrderMap a rr:TriplesMap ;
  rr:logicalTable [ rr:tableName "Order" ] ;
  rr:subjectMap [
    rr:template "http://uipath.com/datafabric/NAME/Order/{Id}" ;
    rr:class    :Order
  ] ;
  # scalar field
  rr:predicateObjectMap [
    rr:predicate :orderTotal ;
    rr:objectMap [ rr:column "Total" ; rr:datatype xsd:decimal ]
  ] .
```

**Relationship (FK join)** — object map references the target TriplesMap, joined
on the FK column -> target's `Id`:

```turtle
  rr:predicateObjectMap [
    rr:predicate :placedBy ;
    rr:objectMap [
      rr:parentTriplesMap :CustomerMap ;
      rr:joinCondition [ rr:child "CustomerId" ; rr:parent "Id" ]
    ]
  ] .
```

**Choice set field** — the column holds the integer NumberId:

```turtle
  rr:predicateObjectMap [
    rr:predicate :status ;
    rr:objectMap [ rr:column "Status" ; rr:datatype xsd:integer ]
  ] .   # NumberId, not the label. Value meanings captured in the OFN comments.
```

**Cross-folder relationship** — when the target entity lives in a different
folder than the parent, the live binding needs the target's folder key
(`referenceFolderKey` in `uip df`). Record it as a Turtle comment on the join so
the mapping is reproducible:

```turtle
  # cross-folder: target Customer lives in folder <FolderB-key> (referenceFolderKey)
  rr:predicateObjectMap [ rr:predicate :placedBy ; rr:objectMap [
    rr:parentTriplesMap :CustomerMap ;
    rr:joinCondition [ rr:child "CustomerId" ; rr:parent "Id" ] ] ] .
```

## 5. Self-check before publish

`uip ontology verify` covers only the OFN. Check the R2RML by hand:

- Valid Turtle (prefixes declared, statements end with `.`).
- Every `rr:TriplesMap` names a **selected** entity; `rr:tableName` = that entity's `Name`.
- Every `rr:column` is a real field on that entity.
- Every `rr:joinCondition` `rr:child` is a real FK field; the `rr:parentTriplesMap` exists in the file and its `rr:parent` is the target's PK (`Id`).
- Every ontology term used as an `rr:predicate`/`rr:class` is declared in the OFN.
