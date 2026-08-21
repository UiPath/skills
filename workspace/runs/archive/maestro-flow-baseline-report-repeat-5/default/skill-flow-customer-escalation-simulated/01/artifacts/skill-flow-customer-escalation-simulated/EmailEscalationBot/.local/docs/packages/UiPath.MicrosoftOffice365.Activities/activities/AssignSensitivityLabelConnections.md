# Assign Sensitivity Label

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Files.AssignSensitivityLabelConnections`

Assigns, removes, or changes a sensitivity label on a file in OneDrive or SharePoint.

**Connector:** `uipath-microsoft-onedrive`

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ConnectionId` | Connection ID | `InArgument` | `String` | Yes | | The Microsoft 365 connection to use. |
| `Item` | File | `InArgument` | [`O365DriveRemoteItem`](types/O365DriveRemoteItem.md) | Yes | | The file to assign the sensitivity label to. |
| `ActionType` | Action Type | `InArgument` | `SensitivityLabelActionType` | Yes | `Add` | The action: `Add`, `Update`, `Clear`. |
| `SensitivityLabel` | Sensitivity Label | `InArgument` | `String` | When not Clear | | The sensitivity label ID to assign. |
| `Justification` | Justification | `InArgument` | `String` | When downgrading/removing | | Justification text for audit purposes. Required when downgrading or removing a label. |
| `WaitActionToComplete` | Wait for Completion | `InArgument` | `Boolean` | No | `False` | Whether to wait for the sensitivity label action to complete. |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umaf="clr-namespace:UiPath.MicrosoftOffice365.Activities.Files;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365fm="clr-namespace:UiPath.MicrosoftOffice365.Files.Models;assembly=UiPath.MicrosoftOffice365"
-->
<umaf:AssignSensitivityLabelConnections
    ActionType="Add" ConnectionId="{x:Null}"
    SensitivityLabel="[labelId]"
    DisplayName="Assign Sensitivity Label">
  <umaf:AssignSensitivityLabelConnections.Item>
    <InArgument x:TypeArguments="umo365fm:O365DriveRemoteItem">[fileItem]</InArgument>
  </umaf:AssignSensitivityLabelConnections.Item>
</umaf:AssignSensitivityLabelConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
