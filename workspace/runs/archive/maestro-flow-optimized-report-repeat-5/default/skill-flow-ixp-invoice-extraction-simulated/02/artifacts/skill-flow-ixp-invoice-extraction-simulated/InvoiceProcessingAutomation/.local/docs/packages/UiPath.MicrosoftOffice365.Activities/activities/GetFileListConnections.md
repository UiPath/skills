# Get File List

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.GetFileListConnections`

Returns a collection of files and/or folders from OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The folder to list files from. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `Filter` | Filter | `Property` | [`FileFilterArgument`](filtering/FileFilterArgument.md) | No | | Filter criteria for files and folders. See [FileFilterArgument](filtering/FileFilterArgument.md). |
| `MaxResults` | Max Results | `InArgument` | `Int32` | No | `200` | Maximum number of items to return. |
| `WhatToReturn` | What to Return | `InArgument` | `FindFilesAndFoldersResultType` | No | `Files` | Whether to return files, folders, or both: `Files`, `Folders`, `FilesAndFolders`. |
| `IncludeSubfolders` | Include Subfolders | `InArgument` | `Boolean` | No | `False` | When true, includes items from subfolders. |
| `TrimDuplicates` | Trim Duplicates | `InArgument` | `Boolean` | No | `False` | When true, removes duplicate results. |
| `SimpleSearch` | Search | `InArgument` | `String` | No | | A keyword-based search query. |
| `SortOptions` | Sort Options | `Property` | `SortOrder` | No | `Ascending` | Sort order by name: `Ascending`, `Descending`, `None`. |
| `SearchMode` | Search Mode | `Property` | `SearchSelectionMode` | No | `UseMetadata` | Controls how the filter is applied: `UseMetadata` (column-based OData filter via `Filter`), `UseSimple` (simple keyword search via `SimpleSearch`), `FreeTextFilter` (full-text string via `FreeTextFilter`), `QueryFilter` (KQL expression via `QueryFilter`), `DynamicMetadataFilter` (column-by-name filter via `DynamicMetadataFilter`). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md)`[]` | The collection of matching files and/or folders. **XAML variable:** declare as `scg:List(umo365fm:O365DriveRemoteItem)` — WF4 does not support array type arguments. |

> **Supported `ItemSelectionMode` values:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`, `RelativePath`. `Browse` is also available in Studio but not suitable for AI-generated XAML. `RelativePath` requires a parent folder selected in Studio — also not suitable for AI XAML.

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
<umaf:GetFileListConnections
    ConnectionId="{x:Null}"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/Invoices"
    Result="[fileList]"
    DisplayName="Get File or Folder List"
    MaxResults="200" WhatToReturn="Files">
  <umaf:GetFileListConnections.DriveItemArgument>
    <umafm:DriveItemArgument
        ItemSelectionMode="ItemUrl"
        ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/Invoices"
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
  </umaf:GetFileListConnections.DriveItemArgument>
  <umaf:GetFileListConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umafe:SearchSelectionMode" StoredValue="UseMetadata">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:SearchSelectionMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umaf:GetFileListConnections.FilterSelectionBackup>
</umaf:GetFileListConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
