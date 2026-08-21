# DriveItemArgument

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Files.Models`

A composition argument object used by OneDrive and SharePoint file activities to specify a file or folder. The `ItemSelectionMode` property determines which sub-properties are required.

## InputMode — ItemSelectionMode (EDriveItemMode)

| Mode | Description | Required Properties | AI-XAML Suitable |
|------|-------------|--------------------|--------------------|
| `Browse` | Select a file/folder via the Studio designer browser widget. | `BrowserItemId`, `BrowserDriveId`, `BrowserDriveName`, `BrowserSiteUrl` | **Not suitable for AI-generated XAML** |
| `ItemId` | Specify a file/folder by its OneDrive/SharePoint item ID. | `ManualEntryItemId` (required); `ManualEntryDriveName`, `ManualEntrySiteUrl` (optional, for SharePoint) | Yes |
| `UseExisting` | Pass an existing [O365DriveRemoteItem](../types/O365DriveRemoteItem.md) reference. | `Item` | Yes |
| `ItemUrl` | Specify a file/folder by its web URL. | `ManualEntryItemUrl` | Yes |
| `FullPath` | Specify a file/folder by its full path from the drive root. Only exposed in activities that explicitly enable this mode (e.g. `FileFolderExistsConnections`, `ForEachFileFolderConnections`). | `ManualEntryItemFullPath` | Yes (where enabled) |
| `RelativePath` | Specify a path relative to a browsed parent folder. | `BrowserParentItemId`, `BrowserParentDriveId`, `ManualEntryItemRelativePath` | No (requires browsed parent) |

## Properties

### Core

| Property | Type | Description |
|----------|------|-------------|
| `ItemSelectionMode` | `EDriveItemMode` | Determines how the drive item is specified. |
| `ConnectionKey` | `String` | The connection key identifying which integration service connection was used at design time. |
| `ConnectionDescriptor` | `String` | A human-readable descriptor for the connection. |

### ItemId Mode

| Property | Type | Description |
|----------|------|-------------|
| `ManualEntryItemId` | `InArgument<String>` | The item identifier. **Required for ItemId mode.** Note: marked `[AutopilotIgnored]` but still the required property for this mode -- use it. |
| `ManualEntryDriveName` | `InArgument<String>` | The document library name (for SharePoint). If set, `ManualEntrySiteUrl` is also required. |
| `ManualEntrySiteUrl` | `InArgument<String>` | The SharePoint site URL (required when `ManualEntryDriveName` is set). |

### ItemUrl Mode

| Property | Type | Description |
|----------|------|-------------|
| `ManualEntryItemUrl` | `InArgument<String>` | The web URL that identifies the file or folder. |

### UseExisting Mode

| Property | Type | Description |
|----------|------|-------------|
| `Item` | `InArgument<O365DriveRemoteItem>` | An existing drive item reference from a previous activity output. |

### FullPath Mode

| Property | Type | Description |
|----------|------|-------------|
| `ManualEntryItemFullPath` | `InArgument<String>` | The full path from the drive root (e.g., `/Documents/Reports/Q1.xlsx`). Only available in activities that enable this mode. |

### RelativePath Mode

| Property | Type | Description |
|----------|------|-------------|
| `BrowserParentItemId` | `InArgument<String>` | The ID of the parent folder (browsed). `[AutopilotIgnored]` |
| `BrowserParentDriveId` | `InArgument<String>` | The drive ID of the parent folder (browsed). `[AutopilotIgnored]` |
| `ManualEntryItemRelativePath` | `InArgument<String>` | The path relative to the parent folder. |

### Browse Mode (designer-only)

| Property | Type | Description |
|----------|------|-------------|
| `BrowserItemId` | `InArgument<String>` | Item ID from browser. `[AutopilotIgnored]` |
| `BrowserDriveId` | `InArgument<String>` | Drive ID from browser. `[AutopilotIgnored]` |
| `BrowserDriveName` | `InArgument<String>` | Drive name from browser. |
| `BrowserSiteUrl` | `InArgument<String>` | Site URL from browser. |
| `BrowserSpecificUrl` | `InArgument<String>` | Specific URL from browser. |
| `BrowserItemFriendlyName` | `InArgument<String>` | Friendly display name from browser. |
| `ReferenceId` | `String` | Internal reference ID. `[AutopilotIgnored]` |
| `FullPathHint` | `String` | Full path hint for fallback resolution. |

### Other

| Property | Type | Description |
|----------|------|-------------|
| `ItemIdBackup` | `BackupSlot<EDriveItemMode>` | Stores previous mode for undo. `[AutopilotIgnored]` |

## XAML Examples

> **Always include `ItemIdBackup`** as the first child of every `<models:DriveItemArgument>` element — Studio always serializes it, so include it to match Studio output. Every `BackupSlot` must include `StoredValue` matching the active mode and a `BackupValues` child with an empty dictionary. `utils:` maps to `xmlns:utils="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"`.
>
> **Activity-level `ItemIdBackup` cross-reference — `BaseBrowserItemActivity` descendants only:** For activities extending `BaseBrowserItemActivity` (e.g. `CopyItemConnections`, `MoveItemConnections`, `DownloadFileConnections`, `GetFileListConnections`, `UploadFilesConnections`), include `ItemIdBackup="{x:Reference __ReferenceID0}"` as a flat attribute on the parent activity element and assign `x:Name="__ReferenceID0"` to the `BackupSlot` inside `DriveItemArgument`.
>
> **Exception — DO NOT add this to trigger or WaitFor activities:** Trigger activities (`RowAddedToTableBottom`, `WorksheetCellUpdated`, `WorksheetCreated`, `FileUpdated`, `NewFileCreated`) and persistence WaitFor activities (`WaitForFileCreated`, `WaitForFileUpdated`, `WaitForRowAddedToTableBottom`, `WaitForWorksheetCellUpdated`, `WaitForWorksheetCreated`) do **not** have `ItemIdBackup` as a property on the activity class. Adding it causes a fatal "Could not find member 'ItemIdBackup'" error. Omit both the flat attr and `x:Name` on the BackupSlot for these activities.
>
> **Exception — `BaseItemArgumentActivity<T>` descendants:** Activities extending `BaseItemArgumentActivity<T>` (`ReadColumnConnections`, `ReadRowConnections`, `CopyRangeConnections`, `FileFolderExistsConnections`, etc.) also do NOT have `ItemIdBackup` on the activity element — omit both.

> **Minimal examples** — only semantically required attributes are shown. Studio adds back serialization noise (`BrowserDriveId`, `ConnectionKey`, etc.) automatically on first save.

### ItemUrl Mode
```xml
<!--
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umafm:DriveItemArgument
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/report.xlsx"
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
```

### UseExisting Mode
```xml
<umafm:DriveItemArgument
    ItemSelectionMode="UseExisting"
    ParentFullPathHint="">
  <umafm:DriveItemArgument.ItemIdBackup>
    <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
        x:Name="__ReferenceID0" StoredValue="UseExisting">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umafm:DriveItemArgument.ItemIdBackup>
  <umafm:DriveItemArgument.Item>
    <InArgument x:TypeArguments="umaf:O365DriveRemoteItem">[existingItem]</InArgument>
  </umafm:DriveItemArgument.Item>
</umafm:DriveItemArgument>
```

### FullPath Mode
```xml
<umafm:DriveItemArgument
    ItemSelectionMode="FullPath"
    ManualEntryItemFullPath="/Documents/Report.xlsx"
    ParentFullPathHint="">
  <umafm:DriveItemArgument.ItemIdBackup>
    <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
        x:Name="__ReferenceID0" StoredValue="FullPath">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umafm:DriveItemArgument.ItemIdBackup>
</umafm:DriveItemArgument>
```

### ItemId Mode
```xml
<umafm:DriveItemArgument
    ItemSelectionMode="ItemId"
    ManualEntryItemId="[itemId]"
    ManualEntryDriveName="Documents"
    ManualEntrySiteUrl="https://contoso.sharepoint.com/sites/mysite"
    ParentFullPathHint="">
  <umafm:DriveItemArgument.ItemIdBackup>
    <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
        x:Name="__ReferenceID0" StoredValue="ItemId">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umafm:DriveItemArgument.ItemIdBackup>
</umafm:DriveItemArgument>
```

## Cross-References

- Selects files/folders of type [O365DriveRemoteItem](../types/O365DriveRemoteItem.md)
- Used by OneDrive/SharePoint file activities (CopyItemConnections, MoveItemConnections, DownloadFileConnections, etc.)
- Files can be filtered by [FileFilterArgument](../filtering/FileFilterArgument.md) and [FileFolderFilterArgument](../filtering/FileFolderFilterArgument.md)
