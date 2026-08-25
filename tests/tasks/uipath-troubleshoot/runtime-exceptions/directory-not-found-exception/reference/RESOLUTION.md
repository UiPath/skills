# Final Resolution

Root Cause: The `Assign` **List Inbound Files** in `Main.xaml` runs `Directory.GetFiles(folderPath)` with `folderPath = "D:\Reports\2026\Inbound"`. That directory does not exist on the unattended robot host (host `MOCK-HOST`), so `Directory.GetFiles` throws `System.IO.DirectoryNotFoundException: Could not find a part of the path 'D:\Reports\2026\Inbound'.`

Evidence:

### Orchestrator
- Process **InboundFileSweep**, release version **10003**, folder **Shared**, job key `c3e4a5b6-3333-4abc-9def-000000000003` ended `Faulted`.
- Host **MOCK-HOST**, ErrorCode `Robot`, RuntimeType `Unattended`. Job `InputArguments = {}`.
- `EntryPointPath = Main.xaml`.

### Runtime Exceptions (Root Cause)
- `System.IO.DirectoryNotFoundException` — "Could not find a part of the path 'D:\Reports\2026\Inbound'.".
- Faulted activity: `Assign` **List Inbound Files** inside `Sequence "Main Sequence"` in `Main.xaml`.
- The fault is in user workflow code (the `Assign` value expression resolved by `CSharpValue.Execute` → `InArgument.TryPopulateValue` → `ActivityInstance.ResolveArguments`), not inside an activity package.

Immediate fix:

1. The path is hardcoded to a developer-machine location absent on the robot. Source the folder from a per-environment config/asset, use a UNC path for unattended runs (mapped drives are not available in the robot session), and validate `Directory.Exists(folderPath)` before listing.
  - Where: `Main.xaml`, `Sequence "Main Sequence"` → `Assign` **List Inbound Files**.
  - Who: RPA developer.
  - Source: `references/runtime-exceptions/playbooks/directory-not-found-exception.md` § Resolution.

Investigation summary:

| # | Hypothesis | Confidence | Status | Root Cause? |
|---|---|---|---|---|
| H1 | `Assign` **List Inbound Files** expression throws `System.IO.DirectoryNotFoundException` in user workflow code | High | Confirmed | Yes |
| H2 | Fault originates inside an activity package (not user code) | Low | Rejected | No — stack frames are `CSharpValue`/`ResolveArguments` over the user expression |
