# Get Single SharePoint List Item

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Sharepoint.GetSingleSharepointListItemConnections`

Retrieves a single item from a SharePoint list by its ID.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `ListArgument` | List | `Property` | [`ListArgument`](components/ListArgument.md) | Yes | | The SharePoint list to retrieve the item from. See [ListArgument](components/ListArgument.md) for input modes. |
| `ItemId` | Item ID | `InArgument` | `String` | Yes | | The ID of the item to retrieve. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `DataRow` | The list item as a DataRow. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umas="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umsm="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint.Models;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umsse="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:sd="clr-namespace:System.Data;assembly=System.Data.Common"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umas:GetSingleSharepointListItemConnections x:TypeArguments="sd:DataRow"
    ConnectionId="{x:Null}"
    ItemId="[itemId]" Result="[listItem]"
    DisplayName="Get Single List Item">
  <umas:GetSingleSharepointListItemConnections.ListArgument>
    <umsm:ListArgument ItemSelectionMode="Manually">
      <umsm:ListArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umsse:ItemSelectionMode" StoredValue="Manually">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umsse:ItemSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
      </umsm:ListArgument.Backup>
      <umsm:ListArgument.ManualEntryListNameOrId>
        <InArgument x:TypeArguments="x:String">["My Tasks"]</InArgument>
      </umsm:ListArgument.ManualEntryListNameOrId>
      <umsm:ListArgument.ManualEntrySiteUrl>
        <InArgument x:TypeArguments="x:String">["https://tenant.sharepoint.com/sites/mysite"]</InArgument>
      </umsm:ListArgument.ManualEntrySiteUrl>
    </umsm:ListArgument>
  </umas:GetSingleSharepointListItemConnections.ListArgument>
</umas:GetSingleSharepointListItemConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
