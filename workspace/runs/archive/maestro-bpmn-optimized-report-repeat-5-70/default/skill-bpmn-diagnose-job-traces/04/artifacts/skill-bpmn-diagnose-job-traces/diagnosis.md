# Diagnosis — job-triage-001

## Summary

| Field | Value |
|---|---|
| Job key | `job-triage-001` |
| Instance ID | `inst-triage-001` |
| Folder key | `folder-public` |
| Process key | `process-vendor-sync` |
| Final status | `Faulted` |
| Run window | 2026-05-01 12:00:00 Z → 12:00:32 Z (32 s) |

## Diagnostic ladder results

| Step | Command | Finding |
|---|---|---|
| 1 – Job status | `uip maestro bpmn job status job-triage-001 --folder-key folder-public` | Status = `Faulted`; `faultElementId` = **null** — no faulting element on the summary |
| 2 – Incidents | `uip maestro bpmn instance incidents inst-triage-001 -f folder-public` | Empty array — **no incidents recorded** |
| 7 – Traces | `uip maestro bpmn job traces job-triage-001` | Three spans; third span faulted with `TimedOut` — faulting element and duration recovered |

## Fault

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

## Root cause

`ServiceTask_CallVendorApi` (a service task that calls an outbound vendor API) hit the configured 30 000 ms timeout limit and was aborted by the runtime. This caused the entire job to fault.

## Why traces were needed

The two cheaper reads — job status and incidents — were both inconclusive. The job summary recorded a `Faulted` state but returned `faultElementId: null`, indicating the runtime did not propagate the faulting element up to the job-level summary. The incidents list was empty, meaning no incident record was created for the timeout event. With neither the faulting element ID nor a cause available from those reads, the diagnostic priority ladder required falling back to verbose span-level traces (Step 7). The traces contained a per-element execution record for every span in the run, and the third span — `ServiceTask_CallVendorApi` — clearly showed `status: TimedOut` with a `durationMs` of 30 000 ms, providing both the faulting element identity and its exact timing.

## Recommended next action (read-only conclusion)

The fix belongs in **BPMN source or cloud configuration**: either raise the outbound call timeout on `ServiceTask_CallVendorApi`, add a boundary timer event with a compensating flow, or investigate the upstream vendor API latency. No retry should be attempted until the root cause is addressed.
