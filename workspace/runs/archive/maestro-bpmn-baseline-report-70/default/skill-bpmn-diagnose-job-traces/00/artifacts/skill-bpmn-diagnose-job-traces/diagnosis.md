# Job Fault Diagnosis

**Job key:** job-triage-001  
**Instance ID:** inst-triage-001  
**Folder:** folder-public  
**Final status:** Faulted

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were needed

The diagnostic priority ladder was followed in order from cheapest to most expensive:

1. **Job status** (`uip maestro bpmn job status job-triage-001 --output json`) confirmed the job
   is `Faulted` but returned `"faultElementId": null` — no faulting element was recorded on the
   job summary.

2. **Incidents** (`uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`)
   returned an empty array. No incident was recorded against the instance, which is consistent with
   the scenario description.

These two steps — the entire cheap read path — produced no actionable element identifier. Because
incidents were empty and the job summary carried no fault element, it was impossible to identify
the root cause without the verbose span data. Only then were traces pulled:

```
uip maestro bpmn job traces job-triage-001 --output json
```

The trace spans showed `ServiceTask_CallVendorApi` reaching a `TimedOut` status after exactly
30 000 ms, with the message *"Outbound call exceeded the 30000 ms timeout and the span was aborted."*
The two earlier spans (`Start_Sync` and `ServiceTask_LoadConfig`) completed successfully, making
`ServiceTask_CallVendorApi` the unambiguous root fault.

## Summary

| Field | Value |
|---|---|
| Faulting element | `ServiceTask_CallVendorApi` (service task) |
| Duration at fault | 30 000 ms (hit the 30 s outbound-call timeout) |
| Root cause | The vendor API call timed out; the runtime aborted the span and faulted the job with no incident recorded and no `faultElementId` propagated to the job summary |
| Fix ownership | BPMN source — increase or make configurable the outbound-call timeout on `ServiceTask_CallVendorApi`, or add error-boundary handling for timeout events |
| Safe next action | Author fix in BPMN source; do not retry until the timeout or error handling is addressed |
