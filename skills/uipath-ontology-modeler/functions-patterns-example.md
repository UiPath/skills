# Functions and Actions — Worked Examples

Read this only if a gate/consistency check fails and you need a concrete reference, or you judge [`functions-patterns.md`](functions-patterns.md) alone isn't enough for this request. These are full worked examples, not templates to copy verbatim — the function/action names and SPARQL/SQL below are specific to the Clinic domain.

## functions.ttl (Clinic)

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/clinic#> .
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
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/clinic#> SELECT (COUNT(*) AS ?n) WHERE { ?p a ont:Prescription ; ont:Prescription.status ?status }" ;
        fno:expects    ( ont:param.countPrescriptionsByStatus.status ) ;
        fno:returns    ( ont:output.countPrescriptionsByStatus.n ) .

ont:param.countPrescriptionsByStatus.status
        a              fno:Parameter ;
        fno:name  "status" ;
        fno:type  "xsd:string" ;
        fno:required   true .

ont:output.countPrescriptionsByStatus.n
        a              fno:Output ;
        rdfs:comment   "Number of prescriptions with the given status." ;
        fno:name  "n" ;
        fno:type  "xsd:integer" .

ont:countPrescriptionsPerDoctor
        a              fno:Function ;
        rdfs:label     "Count prescriptions per doctor" ;
        rdfs:comment   "Returns one row per doctor with that doctor's name and the total number of prescriptions they have prescribed. Use this to answer 'how many prescriptions did each doctor write' or to find the most prescribing doctors. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/clinic#> SELECT ?doctor (COUNT(?p) AS ?n) WHERE { ?p a ont:Prescription ; ont:prescribedBy ?d . ?d a ont:Doctor ; ont:Doctor.name ?doctor } GROUP BY ?doctor" ;
        fno:returns    ( ont:output.countPrescriptionsPerDoctor.doctor ont:output.countPrescriptionsPerDoctor.n ) .

ont:output.countPrescriptionsPerDoctor.doctor
        a              fno:Output ;
        rdfs:comment   "Name of the doctor." ;
        fno:name  "doctor" ;
        fno:type  "xsd:string" .

ont:output.countPrescriptionsPerDoctor.n
        a              fno:Output ;
        rdfs:comment   "Total number of prescriptions issued by this doctor." ;
        fno:name  "n" ;
        fno:type  "xsd:integer" .

ont:listPrescriptionsWithDoctorAndPatient
        a              fno:Function ;
        rdfs:label     "List prescriptions with their doctor and patient" ;
        rdfs:comment   "Returns one row per prescription joined to the doctor who prescribed it and the patient it was prescribed for. Each row has the medication name, the prescription status, the prescribing doctor's name, and the patient's name. Use this to answer questions like 'which doctor prescribed what medication to which patient'. Returns raw rows, not counts. Takes no parameters." ;
        ont:kind       "FUNCTION" ;
        ont:language   "SPARQL" ;
        ont:statement  "PREFIX ont: <https://ontology.uipath.com/clinic#> SELECT ?medication ?status ?doctorName ?patientName WHERE { ?p a ont:Prescription ; ont:Prescription.medication ?medication ; ont:Prescription.status ?status ; ont:prescribedBy ?d ; ont:prescriptionFor ?pat . ?d a ont:Doctor ; ont:Doctor.name ?doctorName . ?pat a ont:Patient ; ont:Patient.name ?patientName }" ;
        fno:returns    ( ont:output.listPrescriptions.medication ont:output.listPrescriptions.status ont:output.listPrescriptions.doctorName ont:output.listPrescriptions.patientName ) .

ont:output.listPrescriptions.medication
        a              fno:Output ;
        rdfs:comment   "Name of the medication prescribed." ;
        fno:name  "medication" ;
        fno:type  "xsd:string" .

ont:output.listPrescriptions.status
        a              fno:Output ;
        rdfs:comment   "Current status of the prescription." ;
        fno:name  "status" ;
        fno:type  "xsd:string" .

ont:output.listPrescriptions.doctorName
        a              fno:Output ;
        rdfs:comment   "Name of the prescribing doctor." ;
        fno:name  "doctorName" ;
        fno:type  "xsd:string" .

ont:output.listPrescriptions.patientName
        a              fno:Output ;
        rdfs:comment   "Name of the patient the prescription is for." ;
        fno:name  "patientName" ;
        fno:type  "xsd:string" .
```

## clinic-updatePrescriptionStatus.ttl (Clinic)

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix cl:    <https://ontology.uipath.com/clinic#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

cl:updatePrescriptionStatus
        a               fno:Function ;
        rdfs:label      "Update the status of a prescription" ;
        rdfs:comment    "Changes the status of a single prescription, identified by its id, to a new status value (for example 'dispensed' or 'cancelled'). Modifies one row. Requires the prescription id and the new status." ;
        ont:kind        "ACTION" ;
        ont:language    "SQL" ;
        ont:statements  ( "UPDATE {{Prescription}} SET {{Prescription.status}} = :newStatus WHERE {{Prescription.id}} = :id" ) ;
        fno:expects     ( cl:param.updatePrescriptionStatus.id cl:param.updatePrescriptionStatus.newStatus ) .

cl:param.updatePrescriptionStatus.id
        a              fno:Parameter ;
        ont:paramName  "id" ;
        ont:paramType  "xsd:integer" ;
        ont:required   true .

cl:param.updatePrescriptionStatus.newStatus
        a              fno:Parameter ;
        ont:paramName  "newStatus" ;
        ont:paramType  "xsd:string" ;
        ont:required   true .
```
