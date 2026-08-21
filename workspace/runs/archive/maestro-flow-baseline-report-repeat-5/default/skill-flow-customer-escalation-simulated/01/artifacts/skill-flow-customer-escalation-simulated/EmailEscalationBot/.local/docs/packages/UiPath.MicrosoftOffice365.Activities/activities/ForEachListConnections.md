# For Each List

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Sharepoint.ForEachListConnections`

Iterates over all lists in a SharePoint site.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `SiteUrlOrId` | Site URL or ID | `InArgument` | `String` | Yes | | The SharePoint site URL or ID to retrieve lists from. |
| `IncludeColumnsDefinitions` | Include Column Definitions | `InArgument` | `Boolean` | No | `False` | When true, includes column definitions for each list. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Length` | Length | `OutArgument` | `Int32` | The number of lists processed. |

### Body

Each iteration provides:
- `CurrentItem` ([`Office365SharepointList`](types/Office365SharepointList.md)) -- the current list.
- `CurrentListIndex` (`Int32`) -- the zero-based iteration index.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umas="clr-namespace:UiPath.MicrosoftOffice365.Activities.Sharepoint;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365="clr-namespace:UiPath.MicrosoftOffice365.Models;assembly=UiPath.MicrosoftOffice365"
-->
<umas:ForEachListConnections
    ConnectionId="{x:Null}"
    SiteUrlOrId="https://tenant.sharepoint.com/sites/mysite"
    DisplayName="For Each List">
  <umas:ForEachListConnections.Body>
    <ActivityAction x:TypeArguments="umo365:Office365SharepointList, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="umo365:Office365SharepointList" Name="CurrentList" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentListIndex" />
      </ActivityAction.Argument2>
      <!-- activities here -->
    </ActivityAction>
  </umas:ForEachListConnections.Body>
</umas:ForEachListConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
