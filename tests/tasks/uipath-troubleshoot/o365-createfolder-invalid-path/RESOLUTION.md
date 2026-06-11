**Root Cause:** The Create Folder (`CreateFolderConnections`) activity received an invalid `FolderPath` input — the path contains a segment `' Quarterly'` with a leading space, which the Microsoft Office 365 activity package's own input validation rejects before any folder is created.

**What went wrong:** The last job in folder Shared — process **ERN_O365_CreateFolderInvalidPath** (job a04406a9-4c64-40d0-a7f3-042c3224c13b, started 2026-06-10 18:59:36 UTC, machine MOCK-HOST) — faulted ~3 seconds in with `Office365Exception: Folder path segment ' Quarterly' cannot have leading or trailing whitespace. (Parameter 'FolderPath')`.

**Why:** The Create Folder activity validates each segment of the configured folder path before calling Microsoft Graph. One segment (`' Quarterly'`) has a leading space, so validation threw deterministically in `GraphServiceClientProxy.CreateFolderByPathAsync` — the package's pre-flight path validation, not a Graph-side rejection. Same configuration faults every run, independent of OneDrive/SharePoint state. Exception chain: `Office365Exception → Office365InternalException → System.ArgumentException`. The Microsoft 365 Scope entered fine (no auth issue); not a name conflict or not-found.

**Immediate fix:** Remove the leading space from the `Quarterly` segment in the Create Folder activity's `FolderPath` (e.g., `Reports/Quarterly`, not `Reports/ Quarterly`). Source: `references/activity-packages/o365-activities/playbooks/create-folder-invalid-path.md` § Resolution step 2.

**Preventive fix:** Where the folder path is composed from variables, trim each segment and remove duplicate/trailing separators before passing to Create Folder.
