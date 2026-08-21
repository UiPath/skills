# Diagnosis — job-triage-001

## Summary

Job `job-triage-001` (instance `inst-triage-001`, folder `folder-public`,
process `process-vendor-sync`) faulted 32 seconds after starting on
2026-05-01T12:00:00Z.

## Diagnostic ladder traversal

| Step | Command | Result |
|------|---------|--------|
| 1 – Job status | `uip maestro bpmn job status job-triage-001 --folder-key folder-public --output json` | `status: Faulted`, `faultElementId: null` — no element pinned |
| 2 – Instance incidents | `uip maestro bpmn instance incidents inst-triage-001 -f folder-public --output json` | Empty array `[]` — no incident recorded |
| 7 – Verbose traces | `uip maestro bpmn job traces job-triage-001 --output json` | Span for `ServiceTask_CallVendorApi` status `TimedOut`, `durationMs: 30000` |

## Findings

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were required

The job summary listed `status: Faulted` but left `faultElementId` as `null`,
meaning the runtime did not pin the fault to a specific BPMN element in the
summary record. The instance incidents list returned an empty array — no
incident was created, so there was no incident ID to follow up on with
`incident get`. With both cheaper reads exhausted and neither providing a
faulting element or a root-cause message, the diagnostic ladder required
escalating to the verbose per-span trace (`uip maestro bpmn job traces`).
The traces revealed that `ServiceTask_CallVendorApi` reached the outbound
timeout ceiling of 30 000 ms, was aborted, and propagated the fault to the
job — a timeout-style failure that the incident subsystem did not capture as
a structured incident in this run.

## Recommended next steps (read-only diagnosis; no mutations performed)

- **Root cause:** `ServiceTask_CallVendorApi` exceeded its 30 s outbound call
  timeout. The vendor API did not respond in time.
- **Fix ownership:** BPMN source — adjust the timeout configuration on
  `ServiceTask_CallVendorApi`, or add a boundary timer event with an error
  path, then repackage and redeploy.
- **Safe next action (requires explicit user consent):** retry the job only
  after the timeout is tuned or the vendor API availability is confirmed.
