# For Each Row

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Excel.ForEachRowConnections`

Iterates over each row in a specified Excel Online range or table.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Workbook | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The workbook containing the data. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `SheetName` | Sheet Name | `InArgument` | `String` | Yes | | The sheet name or named range containing the data. |
| `Range` | Range | `InArgument` | `String` | No | | The cell range to iterate over (e.g., "A1:D10"). If empty, the entire used range is used. |
| `IncludeHeaders` | Has Headers | `InArgument` | `Boolean` | No | `True` | Whether the first row contains column headers. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Length` | Length | `OutArgument` | `Int32` | The number of rows processed. |

### Body

Each iteration provides:
- `CurrentRow` (`DataRow`) -- the current row.
- `CurrentRowIndex` (`Int32`) -- the zero-based iteration index.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umae="clr-namespace:UiPath.MicrosoftOffice365.Activities.Excel;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umae:ForEachRowConnections x:TypeArguments="sd:DataRow"
    ConnectionId="{x:Null}"
    ItemIdBackup="{x:Reference __ReferenceID0}"
    IncludeHeaders="True"
    SheetName="[sheetName]"
    DisplayName="For Each Row"
    ItemSelectionMode="ItemUrl"
    ManualEntryItemUrl="https://tenant.sharepoint.com/sites/mysite/Shared%20Documents/workbook.xlsx"
>
  <umae:ForEachRowConnections.DriveItemArgument>
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
  </umae:ForEachRowConnections.DriveItemArgument>
  <umae:ForEachRowConnections.Body>
    <ActivityAction x:TypeArguments="sd:DataRow, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="sd:DataRow" Name="CurrentRow" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentRowIndex" />
      </ActivityAction.Argument2>
      <Sequence DisplayName="Do" />
    </ActivityAction>
  </umae:ForEachRowConnections.Body>
</umae:ForEachRowConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
