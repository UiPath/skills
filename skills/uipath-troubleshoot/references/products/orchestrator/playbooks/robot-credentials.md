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
2. `uip or machines list --output json` — check if any machine has `UnattendedSlots > 0`. Use `--scope` to filter by scope (Default, Serverless, AutomationCloudRobot, ElasticRobot)
3. `uip or licenses info --output json` — check available Unattended runtime count at the tenant level

## Resolution

- **If `RobotNoMatchingUsernames` or "wrong machine credentials":** update the robot's credential store username to match the machine user, or assign the correct robot user to the folder
- **If `TemplateNoLicense` / zero Unattended slots:** allocate Unattended runtime slots to the machine template in Orchestrator > Machines
- **If tenant-level licenses exhausted:** check tenant license allocation and free up or acquire additional Unattended runtime licenses
