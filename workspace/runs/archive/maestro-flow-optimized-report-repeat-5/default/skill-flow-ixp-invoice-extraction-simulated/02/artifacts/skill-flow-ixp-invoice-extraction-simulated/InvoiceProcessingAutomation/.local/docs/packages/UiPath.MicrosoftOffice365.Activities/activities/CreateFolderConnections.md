# Create Folder

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.CreateFolderConnections`

Creates a folder at the specified location in OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `Item` | Parent Folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The parent folder where the new folder will be created. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `NewFolderName` | New Folder Name | `InArgument` | `String` | Yes | | The name to assign to the newly created folder. |
| `ConflictResolution` | Conflict Resolution | `InArgument` | `ConflictBehavior` | No | `Fail` | What to do when a folder with the same name exists: `Fail`, `Replace`, `Rename`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md) | The newly created folder. |

> **Supported `ItemSelectionMode` values for the destination folder:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`. `Browse` is also available in Studio but not suitable for AI-generated XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
-->
<umaf:CreateFolderConnections
    ConnectionId="{x:Null}"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    DisplayName="Create Folder"
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/Projects"
    NewFolderName="[folderName]">
  <umaf:CreateFolderConnections.DriveItemArgument>
    <umafm:DriveItemArgument
        ItemSelectionMode="ItemUrl"
        ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/Projects"
        ParentFullPathHint="">
      <umafm:DriveItemArgument.ItemIdBackup>
        <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
            x:Name="__ReferenceID0" StoredValue="ItemUrl">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umafm:DriveItemArgument.ItemIdBackup>
    </umafm:DriveItemArgument>
  </umaf:CreateFolderConnections.DriveItemArgument>
  <umaf:CreateFolderConnections.FolderBackup>
    <usau:BackupSlot x:TypeArguments="umafe:FolderCreationMode" StoredValue="FolderName">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:FolderCreationMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umaf:CreateFolderConnections.FolderBackup>
</umaf:CreateFolderConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
