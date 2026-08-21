# Diagnosis — job-triage-001

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were needed

The two cheaper reads were both inconclusive:

1. **Job status** (`uip maestro bpmn job status job-triage-001`) returned
   `"status": "Faulted"` but `"faultElementId": null` — the job summary did not
   record which element faulted.
2. **Instance incidents** (`uip maestro bpmn instance incidents inst-triage-001`)
   returned an empty array (`[]`) — no incident was created for this run.

Because neither the job summary nor the incident stream named a faulting
element, the verbose span traces (`uip maestro bpmn job traces job-triage-001`)
were pulled as a last resort.  The trace spans showed that `Start_Sync` (4 ms)
and `ServiceTask_LoadConfig` (120 ms) both completed normally, while
`ServiceTask_CallVendorApi` reached `TimedOut` status at exactly 30 000 ms —
matching the configured outbound-call timeout.  The process engine aborted the
span without surfacing the failure back to the job summary or creating an
incident, which is why the cheaper reads returned nothing useful.

**Root cause:** `ServiceTask_CallVendorApi` timed out on its outbound vendor API
call (30 000 ms limit reached). The fix belongs in BPMN source or cloud
configuration (increase the task timeout or add a timeout boundary-event
handler); no package regeneration or cloud configuration change is needed as a
first step.
