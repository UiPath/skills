---
confidence: high
---

# O365 Drive — File or folder not found

## Context

What this looks like — any of the following message patterns, all originating from Microsoft Graph returning `ItemNotFound` (HTTP 404) for a OneDrive/SharePoint resource:

- `The resource could not be found.` 
- `Cannot find item configured with connection <connection> at path <path>.` 
- `Cannot find item configured with connection <connection>.` 
- `A file with the specified ID does not exist.`

The job faults synchronously the moment the activity tries to resolve the OneDrive/SharePoint resource.

What activities can produce this error:
- **Get File/Folder** (`GetFileFolderConnections`), **Get File/Folder Metadata** (`GetFileFolderMetadataConnections`), **Get File List** (`GetFileListConnections`) — when the configured `Item` (ID, URL, path, or browse selection) doesn't resolve.
- **Download File** (`DownloadFileConnections`) — when the source `Item` doesn't resolve.
- **Move Item** (`MoveItemConnections`), **Copy Item** (`CopyItemConnections`) — when either the source `Item` or the destination `Folder` doesn't resolve.
- **Rename Item** (`RenameItemConnections`) — when the target `Item` doesn't resolve.
- **Delete Item** (`DeleteItemConnections`) — when the target `Item` doesn't resolve.
- **Share Item** (`ShareItemConnections`) — when the target `Item` doesn't resolve.
- **Update File/Folder Metadata** (`UpdateFileFolderMetadataConnections`) — when the target `Item` doesn't resolve.
- **Create Folder** (`CreateFolderConnections`) — when the configured parent `Folder` doesn't resolve.
- **Upload Files** (`UploadFilesConnections`) — when the destination parent `Folder` doesn't resolve.
- **For Each File/Folder** (`ForEachFileFolderConnections`) — when the parent `Folder` doesn't resolve.
- **Check In/Out File** (`CheckinCheckoutFileConnections`) — when the target `File` doesn't resolve.
- **Assign Sensitivity Label** (`AssignSensitivityLabelConnections`), **Get Sensitivity Labels** (`GetSensitivityLabelsConnections`) — when the target `Item` doesn't resolve.
- **Wait For File Created** / **Wait For File Updated** (persistence triggers) — when the watched parent `Folder` doesn't resolve.
- Legacy activities: `DownloadFile`, `ExportAsPdf`, `FindFilesAndFolders`, `ForEachFileFolder`, `CopyItem`, `UploadFile`, `GetItem`, `MoveItem`, `DeleteItem`, `ShareItem`, `CreateFolder`, and other files activities that take a `DriveItem` argument. Legacy activities surface this as a **raw `Microsoft.Graph.ServiceException`** whose message embeds `Code: itemNotFound` plus the same sentence — match the sentence; the raw exception type itself confirms a legacy activity.

What can cause it:
- **Item no longer exists.** The configured ID, URL, path, or browse selection points to a OneDrive/SharePoint item that has been deleted, moved to the recycle bin, or permanently removed. Graph authoritatively returns 404.
- **Stale ID after move/restore.** OneDrive/SharePoint item IDs are mostly durable but can change after a cross-drive move, after a restore from the recycle bin to a different location, or after re-provisioning of the user's OneDrive. An ID captured from a previous run may stop resolving even though the file is visible in the UI.
- **Wrong drive in scope.** The item exists, but in a different drive (a different user's OneDrive, a different SharePoint document library, or a different shared drive) than the one the activity targets. Graph returns 404 because the item ID is scoped to the wrong drive.
- **SharePoint document library / drive name mismatch.** The configured drive name does not match an accessible drive on the SharePoint site. This surfaces as `You do not have access to any Drives named '<name>' inside SharePoint site '<siteUrl>'.`, which is the drive-level analog of this error. The site itself may also not exist (`The specified site <site> does not exist.`).
- **Shared link no longer valid.** The configured shared URL has been revoked, the sharing scope changed, or the link points to an item the connection cannot read. Surfaces as `The specified shared item does not exist.` or as the standard `The resource could not be found.`
- **Path-segment mismatch.** Path-based input is case-insensitive but otherwise exact. Trailing whitespace, mismatched separators, an item renamed since the path was authored, or a path that crosses drive roots will all miss.
- **Insufficient scope.** The connection lacks `Files.Read.All` / `Files.ReadWrite.All` / `Sites.Read.All` / `Sites.ReadWrite.All` for the target resource. Graph can return 404 instead of 403 for cross-tenant or delegated access where the connection cannot enumerate the parent.
- **Folder passed where file is required.** For `DownloadFileConnections` and the legacy `DownloadFile` / `ExportAsPdf`, passing a `DriveItem` that represents a folder produces `A file with the specified ID does not exist.` This is a configuration mistake, not a missing remote resource.

> **Different cause, do not apply this playbook:**
> - `FileFolderExistsConnections` does **not** surface this error. If the user reports a fault from this activity, the cause is something other than item-not-found.
> - `The resource could not be found.` raised by a **Mail** activity (e.g., `MarkAsReadUnreadConnections`, `DeleteEmailConnections`, `MoveEmailConnections`) is a missing message or mail folder, not a Drive item. See [mail-folder-not-found.md](./mail-folder-not-found.md) for the mail-folder case.

## Resolution

The error is unambiguous; no further investigation is needed. Stop the investigation and ask the user to verify the target resource:

1. **Confirm the file or folder still exists** at the expected location in OneDrive / SharePoint. Check the recycle bin — a recently deleted item is the most common cause. A restore from the recycle bin can change the item ID; if the user has a stored ID from before the delete, it will not resolve.
2. **Confirm the configured identifier is correct** — the `Item` argument on the activity must match what's currently in OneDrive/SharePoint. For ID input, the ID must come from the same drive the activity targets. For path input, paths are case-insensitive but otherwise exact: trailing whitespace, mismatched separators, or a renamed segment all cause this error. For browse-card input, ensure the bound resource hasn't been moved out of the original parent.
3. **Confirm the resolved drive/site** is the one the user expects. `UseDriveCard` selections may bind to a different drive than intended (e.g., the user's personal OneDrive vs. a SharePoint document library). For SharePoint, also confirm the site URL and document library name.
4. **Confirm the connection's authenticated account has access** to the resource. A file owned by another user that was never shared with this account, an item in a SharePoint site the connection's account isn't a member of, or a shared link with revoked access will all surface as 404.
5. **Confirm the connection's scopes.** `Files.Read.All` (or `Files.ReadWrite.All`) is required for OneDrive operations; `Sites.Read.All` (or `Sites.ReadWrite.All`) is required for SharePoint operations. Missing scopes can surface as 404 on enumeration even when the resource physically exists.
6. **For `DownloadFileConnections` failing with `A file with the specified ID does not exist.`**, the configured `Item` is a folder, not a file. Ask the user to point the activity at a file, or to use `ForEachFileFolderConnections` followed by a per-file download.

If the user confirms the resource exists in the Drive UI under the resolved account, the connection has the required scopes, and the identifier is correct, the cause is outside the activity — escalate (tenant-level permissions, conditional access, sharing inheritance, or a Graph-side delay after a recent move/rename) rather than continue under this playbook.
