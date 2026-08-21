# Diagnosis: job-triage-001

## Investigation steps (priority ladder)

1. **Job status** — `uip maestro bpmn job status job-triage-001 --folder-key folder-public --output json`
   Result: status `Faulted`, `faultElementId: null`. The job summary explicitly notes "No faulting element recorded on the job summary." Inconclusive on its own.

2. **Incidents** — `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`
   Result: `[]` — no incidents were recorded for this instance. Inconclusive.

3. **Verbose traces (last resort)** — `uip maestro bpmn job traces job-triage-001 --output json`
   Result: three spans. `Start_Sync` and `ServiceTask_LoadConfig` completed normally. `ServiceTask_CallVendorApi` has status `TimedOut` with `durationMs: 30000` and message "Outbound call exceeded the 30000 ms timeout and the span was aborted."

## Conclusion

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were needed only after the cheaper reads were inconclusive

The job status read confirmed the run faulted but carried no faulting-element ID, and the incidents read returned an empty list, so neither of the cheap, low-cost reads could localize the fault. Only the verbose job traces exposed the per-element span timeline, showing that `ServiceTask_CallVendorApi` ran to its full 30000 ms timeout and was aborted before any incident was ever raised — which explains why the job summary and incident log had nothing to show. Traces were reached last, per the diagnostic priority ladder, only because the cheaper status and incident reads did not explain the fault on their own.
