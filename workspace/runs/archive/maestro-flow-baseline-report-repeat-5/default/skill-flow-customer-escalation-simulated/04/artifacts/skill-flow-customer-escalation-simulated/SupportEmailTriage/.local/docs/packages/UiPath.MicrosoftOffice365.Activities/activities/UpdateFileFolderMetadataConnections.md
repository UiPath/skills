# Update File/Folder Metadata

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.UpdateFileFolderMetadataConnections`

Updates SharePoint metadata (column values) for a file or folder.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | File or Folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The file or folder whose metadata to update. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `DataRow` | Data Row | `InArgument` | `DataRow` | No | | A DataRow containing the field values to update. Used when columns are specified dynamically. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `DataRow` | The updated metadata values as a DataRow. |

> **Supported `ItemSelectionMode` values:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`, `RelativePath`. `Browse` is also available in Studio but not suitable for AI-generated XAML. `RelativePath` requires a parent folder selected in Studio — also not suitable for AI XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
    xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
-->
<umaf:UpdateFileFolderMetadataConnections x:TypeArguments="sd:DataRow"
    DisplayName="Update Metadata" ConnectionId="{x:Null}"
    DataRow="[dataRow]" Result="[updatedRow]">
  <umaf:UpdateFileFolderMetadataConnections.DriveItemArgument>
    <umafm:DriveItemArgument ItemSelectionMode="ItemUrl">
      <umafm:DriveItemArgument.ItemIdBackup>
        <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode" StoredValue="ItemUrl">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umafm:DriveItemArgument.ItemIdBackup>
      <umafm:DriveItemArgument.ManualEntryItemUrl>
        <InArgument x:TypeArguments="x:String">[fileUrl]</InArgument>
      </umafm:DriveItemArgument.ManualEntryItemUrl>
    </umafm:DriveItemArgument>
  </umaf:UpdateFileFolderMetadataConnections.DriveItemArgument>
</umaf:UpdateFileFolderMetadataConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
