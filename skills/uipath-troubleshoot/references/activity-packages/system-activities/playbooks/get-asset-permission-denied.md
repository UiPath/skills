---
confidence: high
---

# Get Asset Failed — Permission Denied

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed because the robot account lacks the required permissions on Assets in the Orchestrator folder.

What this looks like:
- Error message contains `"does not have the required permissions"`, `"You are not authorized!"`, or HTTP 403 `"Forbidden"` (Error code: 0)

What can cause it:
- Robot account role does not include View permission on Assets
- Robot account is not assigned to the folder where the asset lives
- Windows user running the process differs from the registered robot account

What to look for:
- The robot account running the job (from job details in Orchestrator)
- The role assigned to that account in the target folder

## Investigation

1. Identify the robot account running the job (check job details in Orchestrator).
2. In Orchestrator, navigate to the folder > Manage > Accounts & Groups and check the robot account's assigned role.
3. Verify the role includes the **View** permission on Assets.
4. If using folder inheritance, check parent folder permissions as well.

## Resolution

- **If role lacks View Assets:** grant the robot account a role that includes "View Assets" permission in the folder where the asset lives. Common roles with this permission: Automation User, Automation Developer, Administrator.
- **If Windows user mismatch:** align the Windows user running the process with the registered robot account, or reassign the robot.
