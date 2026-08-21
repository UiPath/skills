# Diagnosis: job-triage-001 / inst-triage-001

## Summary

| Field | Value |
|---|---|
| Job key | `job-triage-001` |
| Instance ID | `inst-triage-001` |
| Folder | `folder-public` |
| Final status | **Faulted** |
| Run window | 2026-05-01 12:00–12:01 UTC |

---

## Faulting BPMN element

**`Task_InvokeLegacyRpa`** — service task (`Orchestrator.StartJob`)

Element executions confirm the path: `Start_Manual` completed normally; `Task_InvokeLegacyRpa` faulted immediately after, leaving `triageStatus` stuck at `PendingChildProcess`.

---

## User-visible symptom

The process run reported **Faulted** within 72 seconds of launch. The RPA child job was never dispatched. End users see no invoice-triage output and the process shows no progress past the first task.

---

## Likely root cause

Incident `inc-triage-001` (category `BindingResolution`):

> "Resource binding 'folderPath' resolved to a folder the process cannot access."

The deployed BPMN asset binds the `folderPath` input of `Orchestrator.StartJob` to the expression `=bindings.LegacyRpaFolder`. That binding resolved at runtime — meaning the backing value exists — but the Orchestrator folder it points to is either inaccessible to the running process/robot account or does not exist in the target tenant. This is not a structural BPMN defect; the expression authoring is correct.

---

## Fix ownership

| Ownership label | Implicated? | Notes |
|---|---|---|
| **BPMN source** | No | `=bindings.LegacyRpaFolder` is correctly authored; no structural or expression change needed. |
| **Generated package metadata** | Possibly | If `bindings_v2.json` encodes the wrong folder path value for `LegacyRpaFolder`, regenerate and re-enrich via `uip maestro bpmn registry get` + CLI enrichment before repackaging. |
| **Integration Service enrichment** | No | The connector is `Orchestrator.StartJob` (a native resource, not an Integration Service connector); no IS enrichment is implicated. |
| **Cloud configuration** | **Yes — primary** | The Orchestrator folder that `LegacyRpaFolder` resolves to must exist in the tenant and the process/robot account must hold at least **View** + **Edit** permissions on that folder. Verify folder existence and robot/account ACLs in Orchestrator cloud settings. |

---

## Safe next operate action

**Verify cloud configuration before any retry.**

1. Confirm the target Orchestrator folder exists in the tenant (cloud admin action — no CLI mutation needed for diagnosis).
2. Confirm the process's robot/user account has access to that folder in Orchestrator folder permissions.
3. If the folder path value itself is wrong, update `bindings_v2.json` (`LegacyRpaFolder` resource entry), re-run metadata drift check (`scripts/check_metadata_drift.py`), repack, and redeploy — with explicit user consent before any cloud-side operation.

Do not retry the current faulted instance; the same binding will fail again until cloud configuration or package metadata is corrected.
