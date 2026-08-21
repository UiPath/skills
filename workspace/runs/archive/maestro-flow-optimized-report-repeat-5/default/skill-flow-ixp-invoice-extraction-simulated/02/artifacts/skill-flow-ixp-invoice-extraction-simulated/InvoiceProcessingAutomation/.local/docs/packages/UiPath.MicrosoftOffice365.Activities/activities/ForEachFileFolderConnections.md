# For Each File/Folder

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.ForEachFileFolderConnections`

Iterates over files and/or folders in a specified OneDrive or SharePoint location.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The folder to iterate over. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `Filter` | Filter | `Property` | [`FileFilterArgument`](filtering/FileFilterArgument.md) | No | | Filter criteria for files and folders. See [FileFilterArgument](filtering/FileFilterArgument.md). |
| `MaxResults` | Max Results | `InArgument` | `Int32` | No | `200` | Maximum number of items to return. |
| `WhatToReturn` | What to Return | `InArgument` | `FindFilesAndFoldersResultType` | No | `FilesAndFolders` | Whether to return files, folders, or both: `Files`, `Folders`, `FilesAndFolders`. |
| `IncludeSubfolders` | Include Subfolders | `InArgument` | `Boolean` | No | `False` | When true, includes items from subfolders. |
| `TrimDuplicates` | Trim Duplicates | `InArgument` | `Boolean` | No | `False` | When true, removes duplicate results. |
| `SimpleSearch` | Search | `InArgument` | `String` | No | | A keyword-based search query. |
| `SortOptions` | Sort Options | `Property` | `SortOrder` | No | `Ascending` | Sort order by name: `Ascending`, `Descending`, `None`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Length` | Length | `OutArgument` | `Int32` | The number of items processed. |

### Body

Each iteration provides:
- `CurrentItem` (`O365DriveRemoteItem`) -- the current file or folder.
- `CurrentItemIndex` (`Int32`) -- the zero-based iteration index.

> **Supported `ItemSelectionMode` values:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`, `FullPath`, `RelativePath`. `Browse` is also available in Studio but not suitable for AI-generated XAML. `RelativePath` requires a parent folder selected in Studio — also not suitable for AI XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umaf:ForEachFileFolderConnections
    ConnectionId="{x:Null}"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    DisplayName="For Each File or Folder"
    IncludeSubfolders="False" ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/Invoices"
    MaxResults="200" SearchMode="UseMetadata"
    SortOptions="Ascending" TrimDuplicates="False"
    WhatToReturn="Files">
  <umaf:ForEachFileFolderConnections.DriveItemArgument>
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
  </umaf:ForEachFileFolderConnections.DriveItemArgument>
  <umaf:ForEachFileFolderConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umafe:SearchSelectionMode" StoredValue="UseMetadata">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:SearchSelectionMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umaf:ForEachFileFolderConnections.FilterSelectionBackup>
  <umaf:ForEachFileFolderConnections.Body>
    <ActivityAction x:TypeArguments="umo365fm:O365DriveRemoteItem, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="umo365fm:O365DriveRemoteItem" Name="CurrentItem" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentItemIndex" />
      </ActivityAction.Argument2>
      <!-- activities here -->
    </ActivityAction>
  </umaf:ForEachFileFolderConnections.Body>
</umaf:ForEachFileFolderConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
