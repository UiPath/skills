# Diagnosis: job-triage-001

## Summary

| Field | Value |
|---|---|
| Job Key | job-triage-001 |
| Instance ID | inst-triage-001 |
| Folder | folder-public |
| Process | process-vendor-sync |
| Final Status | Faulted |
| Run window | 2026-05-01T12:00:00Z → 2026-05-01T12:00:32Z |

## Result

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Why traces were needed

**Step 1 — job status** confirmed the run faulted (`"status": "Faulted"`) but
`faultElementId` was `null`; the job summary carried no pointer to the offending
BPMN element.

**Step 2 — incidents** returned an empty array (`[]`); no incident record was
created for this run, so there was no incident message or element ID to read.

With both the cheaper reads exhausted and neither yielding a faulting element,
verbose traces (Step 7 of the diagnostic ladder) were the only remaining source
of per-element execution data. The trace spans identified `ServiceTask_CallVendorApi`
as the element that timed out after exactly 30 000 ms — matching the 32-second
wall-clock window seen in the job summary — making traces the decisive diagnostic
artefact in this case.

## Root cause

`ServiceTask_CallVendorApi` exhausted its outbound-call timeout (30 000 ms).
The runtime aborted the span and faulted the job, but the incident subsystem did
not capture a record, leaving the job summary with a null `faultElementId`.

## Recommended fix (BPMN source)

Increase the timeout configured on `ServiceTask_CallVendorApi`, add retry
boundary-event handling, or investigate why the vendor API is slow. No lifecycle
mutation (retry, cancel, migrate) should be performed until the root cause is
addressed in the BPMN source.
