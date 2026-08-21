# BPMN Job Fault Diagnosis

**Job key:** job-triage-001  
**Instance ID:** inst-triage-001  
**Folder:** folder-public  
**Process:** process-vendor-sync  
**Final status:** Faulted  
**Run window:** 2026-05-01T12:00:00Z → 2026-05-01T12:00:32Z

---

FAULT_ELEMENT: ServiceTask_CallVendorApi
FAULT_TIMING: 30000

---

## Why traces were needed

**Step 1 – Job status** confirmed the job reached `Faulted`, but `faultElementId` was `null`: the job
summary recorded no faulting element.

**Step 2 – Incidents** returned an empty array (`[]`): no incident was created for this fault, so
the incident ladder was exhausted without yielding a root cause.

Steps 3–6 (runtime variables, deployed BPMN asset, element executions, cursors) were not mocked for
this scenario and returned "unmocked" errors, providing no additional signal.

Because the cheaper reads — job status and incidents — established only that the run faulted without
identifying *which* element failed or *why*, the verbose trace pull (Step 7) was the only remaining
diagnostic option. The traces revealed a three-span execution chain:

| Element | Type | Status | Duration (ms) |
|---|---|---|---|
| Start_Sync | startEvent | Completed | 4 |
| ServiceTask_LoadConfig | serviceTask | Completed | 120 |
| **ServiceTask_CallVendorApi** | **serviceTask** | **TimedOut** | **30 000** |

`ServiceTask_CallVendorApi` timed out at exactly 30 000 ms — the configured outbound-call timeout
boundary — and the span was aborted. Because no incident was raised and no faulting element was
written back to the job summary, the fault was invisible to all upstream reads. Only the trace spans
carried the `TimedOut` status and the precise duration.

## Likely root cause

The outbound vendor API call exceeded the 30 s timeout. This is a BPMN source / configuration
concern: the service task's timeout or retry policy in the BPMN extension payload may need
adjustment, or the vendor endpoint itself is unreachable/slow and requires investigation before a
safe retry.

## Safe next action (read-only diagnosis — no mutation performed)

Confirm with the process owner whether to:

1. Increase the timeout on `ServiceTask_CallVendorApi` and re-deploy (BPMN Author fix).
2. Add a boundary timer / error-boundary event to handle timeouts gracefully.
3. Investigate the vendor API for outages before retrying the faulted instance.

No retry, cancel, migrate, or cursor action has been taken.
