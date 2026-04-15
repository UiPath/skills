---
confidence: high
---

# Get Asset Failed — Per-Robot Asset Has No Value

## Context

A `Get Asset` or `Get Orchestrator Asset` activity failed because the asset is configured with per-robot values and the executing robot has no value assigned.

What this looks like:
- Error message contains `"The asset does not have a value associated with this robot"`

What can cause it:
- Asset uses "Per Robot" (or "Per Account/Machine") value mode but no entry exists for the executing robot
- New robot was added to the folder without updating the asset's per-robot value table

What to look for:
- The asset name and its value mode (Global vs Per Robot) in Orchestrator
- Whether the executing robot has a value entry in the asset

## Investigation

1. Navigate to Orchestrator > folder > Assets and open the asset.
2. Confirm the asset is configured with "Per Robot" (or "Per Account/Machine") values.
3. Check whether the robot executing the job has a value entry assigned.

## Resolution

- **If no value entry for the robot:** add a value entry for the executing robot in the asset's per-robot value table.
- **If per-robot values are not required:** switch the asset to a global value.
