# Check In/Check Out File

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.CheckinCheckoutFileConnections`

Checks in or checks out a file in OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `Item` | File | `InArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md) | Yes | | The file to check in or check out. |
| `ActionType` | Action Type | `InArgument` | `CheckinCheckoutActionType` | Yes | `Checkin` | The action to perform: `Checkin`, `Checkout`. |
| `Comment` | Comment | `InArgument` | `String` | No | | A check-in comment associated with the version. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
-->
<umaf:CheckinCheckoutFileConnections
    ActionType="Checkin" ConnectionId="{x:Null}"
    DisplayName="Check In/Out File">
  <umaf:CheckinCheckoutFileConnections.Item>
    <InArgument x:TypeArguments="umo365fm:O365DriveRemoteItem">[fileItem]</InArgument>
  </umaf:CheckinCheckoutFileConnections.Item>
</umaf:CheckinCheckoutFileConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
