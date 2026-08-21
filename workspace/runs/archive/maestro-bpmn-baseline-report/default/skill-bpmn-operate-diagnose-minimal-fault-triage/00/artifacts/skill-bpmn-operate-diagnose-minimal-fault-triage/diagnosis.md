# BPMN Run Diagnosis

| Field | Value |
|---|---|
| Job key | `job-triage-001` |
| Instance ID | `inst-triage-001` |
| Folder | `folder-public` |
| Process | `process-invoice-triage` |
| Final status | **Faulted** |
| Run duration | 2026-05-01 12:00:00 → 12:01:12 UTC (72 s) |

---

## Faulting BPMN element ID

`Task_InvokeLegacyRpa`

---

## User-visible symptom

The process run ended in **Faulted** status after approximately 72 seconds.
The task named "Invoke legacy RPA" did not complete; the process cursor stopped
at that element and no downstream work was executed.

---

## Likely root cause

Incident `inc-triage-001` (category: `BindingResolution`) reports:

> Resource binding `folderPath` resolved to a folder the process cannot access.

The `Task_InvokeLegacyRpa` service task calls `Orchestrator.StartJob` and
supplies the target Orchestrator folder via the binding expression
`=bindings.LegacyRpaFolder`.  At runtime the binding resolved to a folder path
that the executing process identity does not have permission to access (or the
folder does not exist in the target tenant).  This is a **permission /
configuration mismatch** between the resolved folder path and the Orchestrator
folder ACLs, not a logic error in the BPMN flow itself.

Runtime variable `triageStatus` was `PendingChildProcess` at fault time,
confirming the process had not yet triggered the child RPA job before faulting.

---

## Fix ownership

| Ownership label | Implicated? | Detail |
|---|---|---|
| `BPMN source` | **No** | The binding expression `=bindings.LegacyRpaFolder` and the `Orchestrator.StartJob` service call are structurally correct. No BPMN authoring change is required unless the folder key itself needs to be hardcoded differently. |
| `Generated package metadata` | **No** | `bindings_v2.json` / `entry-points.json` are not implicated; the binding resolved (it produced a value) but the resolved value pointed to an inaccessible folder. |
| `Integration Service enrichment` | **No** | This activity calls `Orchestrator.StartJob` directly (not an Integration Service connector). IS enrichment is not on the failure path. |
| `Cloud configuration` | **Yes** | The Orchestrator folder referenced by the `LegacyRpaFolder` binding either does not exist, has been renamed/moved, or the Robot / process identity running this job lacks the required folder-level permissions (`View` + `StartJob` on the target folder). The fix is to correct the folder path value in the process release binding overrides **or** grant the robot account the necessary permissions on the target Orchestrator folder. |

---

## Safe next operate action

Before retrying the job, a cloud administrator should:

1. Verify that the Orchestrator folder referenced by the `LegacyRpaFolder`
   binding exists and is accessible under `folder-public`.
2. Confirm that the Robot / process identity associated with this release holds
   at minimum **View** and **Start Job** permissions on that target folder.
3. If the folder path is wrong, update the binding override in the process
   release configuration to point to the correct, accessible folder.

Once the folder access issue is resolved, the safe next action is to
**re-trigger a new run** of `process-invoice-triage` (a new job, not a retry of
the faulted instance, since the cursor is stuck at the faulted element).
No BPMN source edits, package regeneration, or re-publication are required.
