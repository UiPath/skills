# Diagnosis: job-triage-001 / inst-triage-001

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were required

The diagnostic priority ladder was followed in order:

1. **Job status** (`uip maestro bpmn job status job-triage-001`) confirmed the
   run reached `Faulted` state but returned `faultElementId: null` — the job
   summary carried no pointer to the offending element.

2. **Incidents** (`uip maestro bpmn instance incidents inst-triage-001`) returned
   an empty array — no incident was recorded for this run, so there was no
   incident category, message, or element ID to consult.

Because both cheaper reads were inconclusive, verbose traces were pulled as the
last resort (`uip maestro bpmn job traces job-triage-001`). The trace spans
revealed that `ServiceTask_CallVendorApi` reached status `TimedOut` after
exactly 30 000 ms with the message _"Outbound call exceeded the 30000 ms timeout
and the span was aborted."_ The two earlier spans (`Start_Sync`,
`ServiceTask_LoadConfig`) both completed successfully, confirming the fault is
isolated to the vendor API service task.

## Summary

| Field | Value |
|---|---|
| Job key | job-triage-001 |
| Instance | inst-triage-001 |
| Final status | Faulted |
| Faulting element | `ServiceTask_CallVendorApi` (serviceTask) |
| Duration at fault | 30 000 ms (timeout threshold reached) |
| Root cause | Outbound vendor API call exceeded the configured 30 000 ms timeout |
| Fix ownership | BPMN source (increase or parameterise the timeout) or cloud configuration (adjust the external endpoint / network policy) |
