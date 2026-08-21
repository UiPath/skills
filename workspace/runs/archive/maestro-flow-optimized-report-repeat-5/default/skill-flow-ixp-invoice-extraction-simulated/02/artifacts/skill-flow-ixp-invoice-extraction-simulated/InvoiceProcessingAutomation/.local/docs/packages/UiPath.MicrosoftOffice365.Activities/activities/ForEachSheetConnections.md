# For Each Sheet

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Excel.ForEachSheetConnections`

Iterates over all sheets in an Excel Online workbook.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Workbook | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The workbook to iterate sheets from. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Length` | Length | `OutArgument` | `Int32` | The number of sheets processed. |

### Body

Each iteration provides:
- `CurrentItem` (`String`) -- the current sheet name.
- `CurrentItemIndex` (`Int32`) -- the zero-based iteration index.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umae="clr-namespace:UiPath.MicrosoftOffice365.Activities.Excel;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umae:ForEachSheetConnections
    ConnectionId="{x:Null}"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    DisplayName="For Each Sheet"
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/workbook.xlsx"
>
  <umae:ForEachSheetConnections.DriveItemArgument>
    <umafm:DriveItemArgument
        ItemSelectionMode="ItemUrl"
        ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/workbook.xlsx"
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
  </umae:ForEachSheetConnections.DriveItemArgument>
  <umae:ForEachSheetConnections.Body>
    <ActivityAction x:TypeArguments="x:String, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="x:String" Name="CurrentSheet" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentSheetIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do" />
    </ActivityAction>
  </umae:ForEachSheetConnections.Body>
</umae:ForEachSheetConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
