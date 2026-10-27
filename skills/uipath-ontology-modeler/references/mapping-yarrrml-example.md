# YARRRML Mapping — Worked Example

Read this only if `uip ont validate --local` reports a mapping problem and you need a concrete reference, or you judge [`mapping-yarrrml-guide.md`](mapping-yarrrml-guide.md) alone isn't enough for this request. It is a full worked example, not a template to copy verbatim — the class names, entity names, and column names below are specific to the Clinic domain.

The three local entities are `Doctor`, `Patient` and `Prescription`. Keys are plain fields: `Patient.primaryDoctorId`, `Prescription.doctorId` and `Prescription.patientId` are `STRING` fields joined to the target's `Id`. Every `$(column)` below is a field of the entity named in that block's `table:`, or the system field `Id`.

## Full example — Clinic

```yaml
prefixes:
  ont: https://ontology.uipath.com/clinic#

mappings:
  Doctor:
    sources:
      - access: datafabric
        table: Doctor
        referenceFormulation: rr:SQL2008
    s: ont:Doctor/$(Id)
    po:
      - - a
        - ont:Doctor
      - - ont:Doctor.active
        - $(active)
      - - ont:Doctor.licenseNo
        - $(licenseNo)
      - - ont:Doctor.name
        - $(fullName)
      - - ont:Doctor.specialty
        - $(specialty)

  Patient:
    sources:
      - access: datafabric
        table: Patient
        referenceFormulation: rr:SQL2008
    s: ont:Patient/$(Id)
    po:
      - - a
        - ont:Patient
      - - ont:Patient.birthDate
        - $(birthDate)
      - - ont:Patient.bloodGroup
        - $(bloodGroup)
      - - ont:Patient.name
        - $(fullName)
      - p: ont:primaryDoctor
        o:
          mapping: Doctor
          condition:
            function: equal
            parameters:
              - - str1
                - $(primaryDoctorId)
              - - str2
                - $(Id)

  Prescription:
    sources:
      - access: datafabric
        table: Prescription
        referenceFormulation: rr:SQL2008
    s: ont:Prescription/$(Id)
    po:
      - - a
        - ont:Prescription
      - - ont:Prescription.medication
        - $(medication)
      - - ont:Prescription.status
        - $(status)
      - p: ont:prescribedBy
        o:
          mapping: Doctor
          condition:
            function: equal
            parameters:
              - - str1
                - $(doctorId)
              - - str2
                - $(Id)
      - p: ont:prescriptionFor
        o:
          mapping: Patient
          condition:
            function: equal
            parameters:
              - - str1
                - $(patientId)
              - - str2
                - $(Id)
```
