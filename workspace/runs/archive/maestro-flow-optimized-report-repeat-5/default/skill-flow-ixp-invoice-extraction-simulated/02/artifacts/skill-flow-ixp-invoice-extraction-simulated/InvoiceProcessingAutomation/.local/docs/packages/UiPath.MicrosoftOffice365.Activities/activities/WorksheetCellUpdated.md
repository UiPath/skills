# Worksheet Cell Updated (Trigger)

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Excel.Triggers.WorksheetCellUpdated`

Trigger that fires when a cell is updated in the monitored Excel Online workbook.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `DriveItemArgument` | Workbook | `Property` | [`DriveItemArgument`](components/DriveItemArgument.md) | Yes | | The workbook to monitor. See [DriveItemArgument](components/DriveItemArgument.md) for input modes. |
| `SheetName` | Sheet Name | `InArgument` | `String` | No | | The sheet to monitor. If empty, all sheets are monitored. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `UpdatedCell` | Updated Cell | `OutArgument` | `CellInformation` | Information about the updated cell. |
| `Workbook` | Workbook | `OutArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md) | The workbook that triggered the event. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaet="clr-namespace:UiPath.MicrosoftOffice365.Activities.Excel.Triggers;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umafe="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
-->
<umaet:WorksheetCellUpdated ConnectionId="{x:Null}"
    UpdatedCell="[cellInfo]"
    DisplayName="Worksheet Cell Updated">
  <umaet:WorksheetCellUpdated.DriveItemArgument>
    <umafm:DriveItemArgument ItemSelectionMode="ItemUrl">
      <umafm:DriveItemArgument.ItemIdBackup>
        <usau:BackupSlot x:TypeArguments="umafe:EDriveItemMode" StoredValue="ItemUrl">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umafe:EDriveItemMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umafm:DriveItemArgument.ItemIdBackup>
      <umafm:DriveItemArgument.ManualEntryItemUrl>
        <InArgument x:TypeArguments="x:String">[workbookUrl]</InArgument>
      </umafm:DriveItemArgument.ManualEntryItemUrl>
    </umafm:DriveItemArgument>
  </umaet:WorksheetCellUpdated.DriveItemArgument>
</umaet:WorksheetCellUpdated>
```
