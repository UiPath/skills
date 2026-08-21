# Diagnosis: job-triage-001

## Diagnostic steps taken (priority ladder)

1. **Job status** — `uip maestro bpmn job status job-triage-001 --folder-key folder-public --output json`
   Result: status `Faulted`, `faultElementId: null`, with an explicit note that
   no faulting element was recorded on the job summary. Process key
   `process-vendor-sync`, instance `inst-triage-001`, ran 12:00:00Z–12:00:32Z
   (~32s). Inconclusive on root cause.

2. **Incidents** — `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json`
   Result: `[]` (no incident recorded), confirming the task premise. Followed
   up with `uip maestro bpmn incident summary --output json` and
   `uip maestro bpmn processes incidents process-vendor-sync --output json`,
   both returned `unmocked public-safe BPMN command` (not available in this
   environment). Still inconclusive — no incident data anywhere.

3. **Runtime variables / deployed asset / element-executions / cursors** —
   Attempted `instance get`, `instance variables`, `instance asset`,
   `instance element-executions`, and `instance cursors` for
   `inst-triage-001`. All returned `unmocked public-safe BPMN command` in this
   environment. No additional signal available from these reads.

4. **Traces (last resort)** — `uip maestro bpmn job traces job-triage-001 --output json`
   Result: three spans. `Start_Sync` (4 ms, Completed), `ServiceTask_LoadConfig`
   (120 ms, Completed), and `ServiceTask_CallVendorApi` (30000 ms, status
   `TimedOut`, message: "Outbound call exceeded the 30000 ms timeout and the
   span was aborted."). This is the first evidence identifying an actual
   faulting element.

## Conclusion

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

The job faulted because the `ServiceTask_CallVendorApi` service task exceeded
its 30000 ms outbound call timeout; the span was aborted mid-flight, which is
consistent with the job ending in a `Faulted` state ~32s after start with no
element recorded on the job summary.

## Why traces were needed

Job status confirmed only that the run had faulted, with `faultElementId`
explicitly null — no element identified. The incidents endpoint returned an
empty list, and process/incident-summary reads were unavailable, so there was
no incident record to point at a faulting node. Variable, deployed-asset,
element-execution, and cursor reads were also unavailable in this
environment, leaving no cheaper path to the root cause. Only the verbose job
traces exposed the individual element spans, and only there did the
`ServiceTask_CallVendorApi` span show a non-`Completed` status
(`TimedOut`) with its duration — this is why traces were pulled last, after
every cheaper read had been exhausted and none of them explained the fault.
