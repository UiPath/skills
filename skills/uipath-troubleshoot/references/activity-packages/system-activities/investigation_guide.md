# System Activities Investigation Guide

## Data Correlation

Before using any fetched data, verify it matches the user's reported problem:

- **Activity** — the faulted activity name and namespace match the reported failure (e.g., `UiPath.Core.Activities.GetAsset` vs `UiPath.Core.Activities.GetCredential`)
- **Asset/Credential name** — the name in the error or job trace matches the asset the user is asking about
- **Folder** — the Orchestrator folder where the job ran is the same folder the user referenced
- **Robot account** — the executing robot identity matches the one the user reported (check job details)
- **Timestamp** — the failure occurred during the time window the user reported

If the data doesn't match: **discard it**. Do NOT use unrelated data as a proxy. Report the mismatch and ask for clarification.

## Testing Prerequisites

When testing hypotheses for System Activities issues, gather and verify these before drawing conclusions:

1. **Activity type** — identify the exact activity that faulted (Get Asset vs Get Credential vs Get Robot Asset vs Get Orchestrator Asset)
2. **Asset name and type** — the exact asset name used in the activity, and whether it is Text, Integer, Boolean, or Credential in Orchestrator
3. **Execution folder** — which Orchestrator folder the job ran in, and whether it is a classic or modern folder
4. **Robot identity** — the robot account, its role, and whether it has View permission on Assets in the target folder
5. **Robot connectivity** — whether the robot is Connected + Licensed in the Orchestrator Robots view
6. **Package version** — confirm `UiPath.System.Activities` version; authentication and asset retrieval behavior differs across versions (especially 20.10.x, 2021.10.x, 22.10.x)
7. **Credential store type** — if using an external vault (CyberArk, Azure Key Vault, Thycotic), confirm the vault type and check connectivity separately

## Local File, Compression, and Download Activities

For `Compress/Extract Files`, the modern StudioX file/folder activities, and `Download File from URL` / `Wait for Download`, the fault is on the robot machine's filesystem or network — not Orchestrator. Before concluding:

1. **Resolve the runtime paths** — the exact source, destination, archive, and watched-folder paths the activity used at run time (resolve variables from logs). A path valid on the developer machine is frequently absent on the robot.
2. **Match the exception type to the family** — `CompressionException` (archive ops), `FileSystemException` (modern file/folder ops), `TimeoutException` / rest-call error (download). The exception type routes the playbook; the message text routes the branch.
3. **Check the activity's options** — Overwrite and "Skip unsupported files" for archive/file ops; timeout and watched-folder for downloads.
4. **For generic IO wrappers** (`Failed to copy folder`, `Move/Rename folder exception`), read the inner exception — it carries the real cause (permission, lock, path length).

## Queue and Storage Activities

For `Get Queue Item`, `Set Transaction Status`, and storage-bucket activities: confirm whether the fault is input validation (`Queue Name is required`, `Reason is required when Status is Failed`), a missing Orchestrator connection (`Service URL is empty.` — the job had no service URL), or an Orchestrator API error. Verify the queue/bucket exists in the folder where the job ran and the robot account has permission on it.
