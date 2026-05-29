---
confidence: high
---

# Robot Credentials or Machine User Mismatch

## Context

What this looks like:
- Job faults with "The unattended robot has the wrong machine credentials to execute the job (the username of the machine is not the same as the username in the user credentials)"
- Job stuck in Pending with PendingReason `RobotNoMatchingUsernames` — the robot user account does not match any machine user mapping
- Job stuck in Pending with PendingReason `TemplateNoLicense` — the machine template has zero Unattended runtime slots allocated

All three are manifestations of the same category: the folder's robot/machine configuration cannot execute unattended jobs.

What can cause it:
- No robot user account assigned to the folder
- Robot user account credentials do not match the machine's configured username
- Machine template has zero Unattended runtime slots (`UnattendedSlots: 0`)
- Unattended runtime licenses exhausted at the tenant level

What to look for:
- The exact error message or PendingReason from the job
- Whether the folder has robot users assigned
- Whether the machine template has Unattended slots allocated

## Investigation

1. Identify which variant from the job's error message / PendingReason in triage evidence. For the credential variant, confirm from the job details: compare `OrchestratorUserIdentity` (the assigned robot account) against the host machine's configured user — `LocalSystemAccount` and `HostMachineName`. A mismatch between the assigned robot identity and the machine user is the confirmation. The job also has no `StartTime` and a single Pending `JobHistory` entry — the fault is at dispatch, before any robot session started.

   > **`RobotNoMatchingUsernames` interpretation.** The code only fires when Orchestrator IS comparing an assigned robot account against machine users — so the cause is **credential-mismatch** (the robot's credential-store username does not match the machine user), NOT "no robot assigned to the folder". There is no documented `uip` CLI command to list a folder's assigned robot accounts, so the "no robot account assigned" sub-cause cannot be confirmed or ruled out via CLI — record it under `open_gaps`, never report it as the confirmed cause. Do NOT treat an empty `[]` from any exploratory command as proof of absence; absence is contradicted by the error code itself.

2. `uip or machines list --output json` — check if any machine has `UnattendedSlots > 0`. Use `--scope` to filter by scope (Default, Serverless, AutomationCloudRobot, ElasticRobot)
3. `uip or licenses info --output json` — check available Unattended runtime count at the tenant level. **For `RobotNoMatchingUsernames` specifically, license is NOT the bottleneck** — Orchestrator emits a dedicated license-family code (e.g., `TemplateNoLicense`) when licenses are actually exhausted, not `RobotNoMatchingUsernames`. `Used.Unattended == Allowed` here is the assigned template's own allocated slot, not exhaustion. Do NOT report license exhaustion as a confirmed cause for this PendingReason

## Resolution

- **If `RobotNoMatchingUsernames` or "wrong machine credentials":** the assigned robot account's stored username does not match the host machine's user. Fix with one of:
  - **Update the machine credentials** on the account's unattended robot so the stored Windows username matches the machine's logged-in user.
  - **Manage the folder's assigned accounts** — create a new account or assign the correct account that maps to the machine user.
  - **Run the job using a different account** whose unattended robot already has matching machine credentials.
- **If `TemplateNoLicense` / zero Unattended slots:** allocate Unattended runtime slots to the machine template in Orchestrator > Machines
- **If tenant-level licenses exhausted:** check tenant license allocation and free up or acquire additional Unattended runtime licenses
