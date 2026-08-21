# Upload Files

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.UploadFilesConnections`

Uploads files to a specified folder in OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Destination Folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The folder to upload files to. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `FilesInputMode` | Files Input Mode | `Property` | `FilesInputMode` | No | `MultipleByVariable` | How to specify the files: `Single`, `MultipleByVariable`, `MultipleByBuilder`. |
| `MultipleFilesToUpload` | Files | `InArgument` | `IEnumerable<IResource>` | When MultipleByVariable | | A collection of file resources to upload. |
| `Metadata` | Metadata | `InArgument` | `DataTable` | No | | SharePoint metadata to upload along with the files. |
| `ConflictResolution` | Conflict Resolution | `InArgument` | `ConflictBehavior` | No | `Replace` | What to do when a file with the same name exists: `Fail`, `Replace`, `Rename`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `FirstResult` | First Result | `OutArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md) | The first uploaded file, or null if none were uploaded. |
| `AllResults` | All Results | `OutArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md)`[]` | All uploaded files. |

> **Supported `ItemSelectionMode` values for the destination folder:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`. `Browse` is also available in Studio but not suitable for AI-generated XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:umo365fe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<!-- AllResults variable: declare as scg:List(umo365fm:O365DriveRemoteItem) — WF4 does not support array type arguments -->
<o365files:UploadFilesConnections DisplayName="Upload Files" ConnectionId="[conn]"
    FilesInputMode="MultipleByVariable" FirstResult="[firstFile]" AllResults="[allFiles]"
    MultipleFilesToUpload="[filesToUpload]">
    <o365files:UploadFilesConnections.FilesBackup>
        <utils:BackupSlot x:TypeArguments="umo365fe:FilesInputMode" />
    </o365files:UploadFilesConnections.FilesBackup>
    <o365files:UploadFilesConnections.DriveItemArgument>
        <models:DriveItemArgument ItemSelectionMode="ItemUrl">
            <models:DriveItemArgument.ItemIdBackup>
                <utils:BackupSlot x:TypeArguments="enums:EDriveItemMode" />
            </models:DriveItemArgument.ItemIdBackup>
            <models:DriveItemArgument.ManualEntryItemUrl>
                <InArgument x:TypeArguments="x:String">[destinationFolderUrl]</InArgument>
            </models:DriveItemArgument.ManualEntryItemUrl>
        </models:DriveItemArgument>
    </o365files:UploadFilesConnections.DriveItemArgument>
</o365files:UploadFilesConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
