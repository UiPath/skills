# SharePoint List Item Updated (Trigger)

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Sharepoint.Triggers.SharepointListItemUpdated`

Trigger that fires when an item is updated in the monitored SharePoint list.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `ListArgument` | List | `Property` | [`ListArgument`](components/ListArgument.md) | Yes | | The SharePoint list to monitor. See [ListArgument](components/ListArgument.md) for input modes. |
| `Filter` | Filter | `Property` | [`ColumnFilterCollection`](filtering/ColumnFilterCollection.md) | No | | Filter criteria for the updated item. See [ColumnFilterCollection](filtering/ColumnFilterCollection.md). |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `DataRow` | The updated list item. |
| `List` | List | `OutArgument` | [`Office365SharepointList`](types/Office365SharepointList.md) | The SharePoint list that triggered the event. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umast="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint.Triggers;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umsm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umsse="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umast:SharepointListItemUpdated x:TypeArguments="sd:DataRow"
    ConnectionId="{x:Null}"
    Result="[updatedItem]"
    DisplayName="SharePoint List Item Updated">
  <umast:SharepointListItemUpdated.ListArgument>
    <umsm:TriggerListArgument ItemSelectionMode="Manually"
        ManualEntryListName="My Tasks"
        ManualEntrySiteUrl="https://tenant.sharepoint.com/sites/mysite">
      <umsm:TriggerListArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umsse:ItemSelectionMode" StoredValue="Manually">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umsse:ItemSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umsm:TriggerListArgument.Backup>
    </umsm:TriggerListArgument>
  </umast:SharepointListItemUpdated.ListArgument>
</umast:SharepointListItemUpdated>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
