# File or Folder Exists

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.FileFolderExistsConnections`

Checks if the specified file or folder exists in OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `Item` | File or folder | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The file or folder to check for existence. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Exists | `OutArgument<Boolean>` | `Boolean` | Indicates whether the specified file or folder exists. |

## Output Model

Returns `true` if the file or folder exists in OneDrive or SharePoint; `false` if it does not exist.

> **Supported `ItemSelectionMode` values:** `ItemUrl` *(recommended for AI XAML)*, `ItemId`, `UseExisting`, `FullPath`, `RelativePath`. `Browse` is also available in Studio but not suitable for AI-generated XAML. `RelativePath` requires a parent folder browsed in Studio — also not suitable for AI XAML.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umaf:FileFolderExistsConnections
    ConnectionId="{x:Null}"
    Result="[exists]"
    DisplayName="File or Folder Exists">
  <umaf:FileFolderExistsConnections.Item>
    <umafm:DriveItemArgument
        ItemSelectionMode="ItemUrl"
        ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/report.xlsx"
        ParentFullPathHint="">
      <umafm:DriveItemArgument.ItemIdBackup>
        <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode"
            StoredValue="ItemUrl">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umafm:DriveItemArgument.ItemIdBackup>
    </umafm:DriveItemArgument>
  </umaf:FileFolderExistsConnections.Item>
</umaf:FileFolderExistsConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Both `FullPath` and `RelativePath` modes are enabled on this activity (via `EnableFullPath` and `EnableRelativePath` in the view model).
- The activity returns `false` (does not throw) when the item is not found — making it safe to use for conditional existence checks without wrapping in a Try/Catch.
