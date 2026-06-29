**Root Cause:** The job `ERN_O365_CopyItemArgNull` (started manually 2026-06-10 17:12 UTC, unattended, machine MOCK-HOST) faulted because the legacy **Copy Item** (`CopyItem`) activity received a null `DriveItem` input — the upstream **Find Files And Folders** (`FindFilesAndFolders`) search matched nothing, so the variable it was supposed to populate stayed null.

**What went wrong:** Copy Item threw a raw `System.ArgumentNullException: Value cannot be null. (Parameter 'DriveItem')` in `O365_CopyItemArgNull.xaml`, faulting the job.

**Why:** Find Files And Folders searched OneDrive/SharePoint for `no-such-file-zzz-repro` — a query that matched no item. When its search returns zero results, Find Files And Folders leaves its `First` output unset, so the variable `foundItem` stayed null. Copy Item's `DriveItem` property is bound to that same `foundItem` variable; the activity checks `DriveItem` at the start of execution and throws when it is null. Being a legacy (non-Connections) activity, the exception escaped unwrapped and faulted the job.

**Immediate fix:** Fix the search criteria on Find Files And Folders so it matches the item intended for copy (query `no-such-file-zzz-repro` matched nothing, leaving `foundItem` null). Source: `references/activity-packages/o365-activities/playbooks/copy-item-argument-null.md` § Resolution.

**Preventive fix:** Add a null guard (`If foundItem Is Nothing`) between Find Files And Folders and Copy Item, handling the no-match case explicitly (skip, log, or business exception). Validate required activity inputs that depend on external data before use.
