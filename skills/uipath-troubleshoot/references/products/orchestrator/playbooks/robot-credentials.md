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

1. Check the job's error message or PendingReason from triage evidence to identify which variant
2. `uip or folders accounts list <folder-key> --type DirectoryRobot --output json` — list robot accounts assigned to the folder. A **populated** result (one or more `DirectoryRobot` entries, at least one with `MayHaveUnattended: true`) rules OUT the "no robot account assigned" sub-cause and narrows the failure to credential-mismatch: a robot IS assigned but its credential-store Windows username does not match the machine user. **An empty `[]` result is NOT, by itself, proof of absence** — the command may be unavailable on the installed CLI version (returns empty as a fallback), the `--type` filter may have excluded entries, or the OData call may have failed silently. The literal `RobotNoMatchingUsernames` code only fires when Orchestrator IS comparing a robot account against machine users — so absence is contradicted by the error code itself. Treat an empty result as an open gap (record under `open_gaps`), NOT as a confirmed cause.
3. `uip or machines list --output json` — check if any machine has `UnattendedSlots > 0`. Use `--scope` to filter by scope (Default, Serverless, AutomationCloudRobot, ElasticRobot)
4. `uip or licenses info --output json` — check available Unattended runtime count at the tenant level. **For `RobotNoMatchingUsernames` specifically, license is NOT the bottleneck** — Orchestrator emits a dedicated license-family code (e.g., `TemplateNoLicense`) when licenses are actually exhausted, not `RobotNoMatchingUsernames`. `Used.Unattended == Allowed` here is the assigned template's own allocated slot, not exhaustion. Do NOT report license exhaustion as a confirmed cause for this PendingReason

## Resolution

- **If `RobotNoMatchingUsernames` or "wrong machine credentials":** update the robot's credential store username to match the machine user, or assign the correct robot user to the folder
- **If `TemplateNoLicense` / zero Unattended slots:** allocate Unattended runtime slots to the machine template in Orchestrator > Machines
- **If tenant-level licenses exhausted:** check tenant license allocation and free up or acquire additional Unattended runtime licenses
