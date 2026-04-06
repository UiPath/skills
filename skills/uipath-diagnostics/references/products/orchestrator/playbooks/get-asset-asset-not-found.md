---
confidence: high
---

# Get Asset - Asset Not Found

## Context

What this looks like:
- Job fails at Get Asset / Get Robot Asset with an error such as "Could not find an asset with this name"
- The same process can succeed in one folder and fail in another

What can cause it:
- The asset does not exist in the folder where the job is running
- The asset name in the workflow does not exactly match the Orchestrator asset name
- The process runs in a different folder than expected, so the target asset is out of scope

What to look for:
- Exact asset name from the error message and the workflow configuration
- Job folder context versus the folder where the asset is defined
- Case and spelling differences in the asset name

## Investigation

1. Confirm the failing job folder, then check that an asset with the exact same name exists in that same folder.
2. If not found, verify whether the asset exists in a different folder or has a naming mismatch (case/spaces/typos).

## Resolution

- Create the missing asset in the same folder where the process runs.
- If the asset exists in another folder, move or recreate it in the execution folder, or run the job in the folder where the asset is defined.
- Update the workflow/config key so the asset name exactly matches the Orchestrator asset name.