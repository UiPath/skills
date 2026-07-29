# YARRRML Mapping — Worked Example

Read this only if a gate/consistency check fails and you need a concrete reference, or you judge [`mapping-yarrrml.md`](mapping-yarrrml.md) alone isn't enough for this request. It is a full worked example, not a template to copy verbatim — the class names, entity IDs, and column names below are specific to the Clinic domain.

## Full example — Clinic

```yaml
prefixes:
  ont: https://ontology.uipath.com/clinic#

mappings:
  Doctor:
    sources:
      - access: datafabric
        table: Doctor
        entityId: b5b4bd01-bd72-f111-ac9a-0022482a9634
        folderId: 751e18c5-7532-4b3e-8795-a300ce62fee2
        referenceFormulation: rr:SQL2008
    s: ont:Doctor/$(doctorId)
    po:
      - - a
        - ont:Doctor
      - - ont:Doctor.active
        - $(active)
      - - ont:Doctor.licenseNo
        - $(licenseno)
      - - ont:Doctor.name
        - $(fullname)
      - - ont:Doctor.specialty
        - $(specialty)
      - p: ont:prescribes
        o:
          mapping: Prescription
          condition:
            function: equal
            parameters:
              - - str1
                - $(doctorId)
              - - str2
                - $(doctorid)

  Patient:
    sources:
      - access: datafabric
        table: Patient
        entityId: 026d0953-bd72-f111-ac9a-0022482a9634
        folderId: 751e18c5-7532-4b3e-8795-a300ce62fee2
        referenceFormulation: rr:SQL2008
    s: ont:Patient/$(patientId)
    po:
      - - a
        - ont:Patient
      - - ont:Patient.birthDate
        - $(birthdate)
      - - ont:Patient.bloodGroup
        - $(bloodgroup)
      - - ont:Patient.name
        - $(fullname)
      - p: ont:primaryDoctor
        o:
          mapping: Doctor
          condition:
            function: equal
            parameters:
              - - str1
                - $(primarydoctorid)
              - - str2
                - $(doctorId)
      - p: ont:treatingDoctor
        o:
          mapping: Doctor
          condition:
            function: equal
            parameters:
              - - str1
                - $(primarydoctorid)
              - - str2
                - $(doctorId)

  Prescription:
    sources:
      - access: datafabric
        table: Prescription
        entityId: 6e3ece90-bd72-f111-ac9a-0022482a9634
        folderId: 751e18c5-7532-4b3e-8795-a300ce62fee2
        referenceFormulation: rr:SQL2008
    s: ont:Prescription/$(prescriptionId)
    po:
      - - a
        - ont:Prescription
      - - ont:Prescription.id
        - $(prescriptionId)
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
                - $(doctorid)
              - - str2
                - $(doctorId)
      - p: ont:prescriptionFor
        o:
          mapping: Patient
          condition:
            function: equal
            parameters:
              - - str1
                - $(patientid)
              - - str2
                - $(patientId)
```
