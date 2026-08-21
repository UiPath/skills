# BPMN Process Run Fault Diagnosis

**Job key:** `job-triage-001`  
**Instance ID:** `inst-triage-001`  
**Folder:** `folder-public`  
**Process:** `process-invoice-triage`  
**Run duration:** 2026-05-01T12:00:00Z → 12:01:12Z (72 s)

---

## Faulting BPMN Element

| Field | Value |
|---|---|
| Element ID | `Task_InvokeLegacyRpa` |
| Element type | Service Task (`Orchestrator.StartJob`) |
| Incident ID | `inc-triage-001` |
| Incident category | `BindingResolution` |

The process cursor is currently parked at `Task_InvokeLegacyRpa` in state **Faulted**. No element after it executed.

---

## User-Visible Symptom

The process instance faulted 72 seconds after start. The variable `triageStatus` is frozen at `PendingChildProcess`, meaning the child RPA job was never launched. No invoice-triage result was produced for `INV-SYNTH-001`.

---

## Likely Root Cause

The service task binds its `folderPath` argument via the expression `=bindings.LegacyRpaFolder` (declared in the BPMN `<uipath:binding>` extension). At runtime the binding resolved to a value, but that value is an Orchestrator folder path the process runtime identity is not permitted to access. The `Orchestrator.StartJob` call was therefore rejected before the child job could be enqueued.

In short: **the Integration Service binding `LegacyRpaFolder` resolves to an Orchestrator folder the process cannot reach.**

---

## Fix Ownership

| Ownership label | Implicated? | Rationale |
|---|---|---|
| `BPMN source` | **No** | The BPMN correctly references `=bindings.LegacyRpaFolder`; the expression syntax and activity declaration are valid. |
| `Generated package metadata` | **No** | No evidence of a packaging error; the asset loaded and the binding name was resolved. |
| `Integration Service enrichment` | **Yes — primary** | The `LegacyRpaFolder` binding value must be updated to point to an Orchestrator folder the process identity can access, or the binding must be re-mapped to a correctly permissioned folder. |
| `Cloud configuration` | **Yes — secondary** | If the intended target folder is correct, the Orchestrator Cloud folder permissions for the process runtime identity must be expanded to include that folder. |

Both `Integration Service enrichment` and `Cloud configuration` are implicated; which one is authoritative depends on whether the binding value itself is wrong (wrong folder path) or the folder path is right but missing a permission grant.

---

## Safe Next Operate Action

Retrieve the current resolved value of the `LegacyRpaFolder` binding from Integration Service and compare it against the list of Orchestrator folders the process runtime identity holds permissions for. No process-mutation, retry, or cursor operation is needed until the binding value or folder permission is corrected.
