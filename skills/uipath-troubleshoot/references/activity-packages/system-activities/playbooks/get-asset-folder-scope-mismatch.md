---
confidence: high
---

# Get Asset Failed — Folder Scope Mismatch

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed because the activity targets the wrong folder or the folder type is incompatible.

What this looks like:
- Error code 1100: `"Folder does not exist or the user does not have access to the folder"`
- Error code 1101: `"An organization unit is required"`

What can cause it:
- `OrchestratorFolderPath` property set to a wrong or nonexistent folder
- Activity created before modern folders were introduced — lacks the FolderPath property entirely (error 1101)
- Asset is in a classic folder but the job runs in a modern folder, or vice versa
- Robot account is not assigned to the folder containing the asset

What to look for:
- The `OrchestratorFolderPath` property value on the activity
- Whether the folder is classic or modern
- Whether the robot account is assigned to the target folder

## Investigation

1. Check the `OrchestratorFolderPath` property of the activity — an incorrect or missing value is the most common cause.
2. Confirm whether the asset is in a classic or modern folder, and whether the job runs in the same type.
3. If error is 1101, the activity was likely created before modern folders were introduced — it lacks the FolderPath property entirely.
4. Verify that the robot account is assigned to the folder containing the asset.

## Resolution

- **If `OrchestratorFolderPath` is wrong:** correct it or leave it blank to use the robot's connected folder.
- **If error is 1101 (old XAML migration):** delete the activity and re-add it from the Activities panel in the current Studio version to generate the FolderPath property.
- **If classic/modern folder mismatch:** recreate the asset in the correct folder type — cross-type access is not supported.
- Assets are **not** auto-migrated during classic-to-modern folder migration; recreate them manually.
