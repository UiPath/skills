# Final Resolution

**Matched playbook:** `references/products/orchestrator/playbooks/job-pending-stale-dispatch.md` (with `job-pending-no-host.md` as the co-matched sibling, eliminated by the discriminator below)

**Scope:** orchestrator → process

## Root cause

Job `0f9d854e-221e-487d-bb2b-fcc76a7d7461` (process **ERN**, entry-point
`Google.xaml`, runtime type Unattended) in the **Shared** folder is stuck
in `Pending` since 2026-05-14T11:07:13Z because:

1. **Originating cause (H1, confirmed):** At dispatch time no Unattended
   host was connected to the `danVM` machine template. Orchestrator
   captured the following `PendingReasons.Errors` on the job and never
   re-evaluated them:
   - `TemplateNoHostsAvailable`
   - `DynamicJobConnectedMachinesInvalid`
   - `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`

2. **Residual cause (H5, active root cause):** A Windows Unattended
   runtime (robot version `26.0.193-cloud.23059`) has since connected to
   the `danVM` template, the robot account has a Windows credential, the
   Assistant is in Machine Key / Service Mode, and the tenant Unattended
   license slot is free (`Used=0 / Allowed=1`). Despite all
   prerequisites being satisfied, the job's `PendingReasons` are a
   frozen snapshot from dispatch time and Orchestrator does NOT
   re-evaluate them on a still-Pending job — JobHistory contains only
   the single original Pending entry. The job will remain Pending until
   the user re-triggers it.

## Eliminated hypotheses

| ID | Hypothesis | Why eliminated |
|----|------------|----------------|
| H2 | Robot connected in Attended (User) mode | User confirmed Machine Key / Service Mode; Orchestrator Sessions shows 1 Unattended session Available. |
| H3 | Robot account missing Windows credential | User confirmed credential is configured on the danVM template robot account. |
| H4 | Tenant Unattended slot held by stale reservation | `uip or licenses info` shows Used=0 / Allowed=1 — slot is free. |

## Recommended fix

The user must **stop job `0f9d854e-221e-487d-bb2b-fcc76a7d7461` in
Orchestrator (Jobs → select → Stop / Kill) and re-trigger the ERN
process from the Shared folder.** A fresh dispatch will perform a new
eligibility check against the current state (host connected, credential
present, license slot free) and the job should transition to Running on
`danVM`.

If a re-triggered job is also Pending with the same `ErrorCodes`,
escalate to a deeper folder/template-to-runtime binding investigation
(the dispatcher still cannot see the runtime).

## Symptoms / signature

- Job `state = Pending`, no state transitions in JobHistory.
- `PendingReasons.Errors` includes `TemplateNoHostsAvailable` (and
  optionally `DynamicJobConnectedMachinesInvalid` /
  `DynamicJobConnectedMachinesWindowsRobotVersionInvalid`).
- Machine template (`danVM`) currently reports a connected runtime
  (`robotVersions` populated).
- Tenant license shows the Unattended slot is free.
- JobHistory contains only the single original Pending entry — proving
  Orchestrator did not re-evaluate.
