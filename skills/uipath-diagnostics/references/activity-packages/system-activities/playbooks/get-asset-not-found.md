---
confidence: high
---

# Get Asset Failed — Asset Does Not Exist

## Context

A `Get Asset`, `Get Orchestrator Asset`, or `Get Credential` activity failed because the asset was not found in the Orchestrator folder where the job runs.

What this looks like:
- Error message contains `"Could not find an asset with this name"` or `"Could not find the asset"` (Error code: 1002)

What can cause it:
- Asset name in the workflow does not match any asset in the folder (typo, spacing, or rename)
- Asset exists in a different folder than where the job runs
- Asset was recently deleted or moved

What to look for:
- Exact asset name from the activity's AssetName property (in XAML or job traces)
- The Orchestrator folder the job runs in (from job details)

## Investigation

1. Get the exact asset name from the activity's AssetName property (check XAML or job traces).
2. Confirm the folder the job runs in (check the job details in Orchestrator > Jobs).
3. List assets in that folder and verify an asset with that exact name exists.
4. Check for case or spacing differences — asset names are not case-sensitive but spelling must match exactly.
5. If the asset is missing, check whether it exists in a different folder or was recently renamed/deleted.

## Resolution

- **If the asset does not exist in the job folder:** create it there, or run the job in the folder where the asset is defined.
- **If the name does not match:** fix the AssetName property in the workflow to match the Orchestrator asset name exactly.
- **If the asset was deleted:** recreate it with the correct name, type, and value.
