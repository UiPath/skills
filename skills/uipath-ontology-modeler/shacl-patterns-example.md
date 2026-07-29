# SHACL Patterns — Worked Example

Read this only if a gate/consistency check fails and you need a concrete reference, or you judge [`shacl-patterns.md`](shacl-patterns.md) alone isn't enough for this request. It is a full worked example, not a template to copy verbatim — the class names, shape names, and rules below are specific to the Clinic domain.

## Full Example — Clinic rules.ttl

```turtle
@prefix ont:   <https://ontology.uipath.com/clinic#> .
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
