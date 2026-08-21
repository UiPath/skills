# Assign Sensitivity Label To Email

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.AssignSensitivityLabelToEmailConnections`

Assigns a sensitivity label to a specified email.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `Item` | Email | Input | [`InArgument<Office365Message>`](types/Office365Message.md) | Yes | | The email to assign the sensitivity label to. |
| `SensitivityLabel` | Sensitivity Label | Input | `InArgument<string>` | Yes | | The sensitivity label to assign. |
| `ActionType` | Action Type | Input | `InArgument<SensitivityLabelActionType>` | No | `Update` | The action type for the sensitivity label operation. |
| `MailboxArg` | Mailbox | | [`MailboxArgument`](components/MailboxArgument.md) | No | | Specifies the mailbox to use. See [MailboxArgument](components/MailboxArgument.md) for input modes. |

## Output Model

This activity does not return an output object.

## Enum Reference

| Enum | Values |
|---|---|
| `SensitivityLabelActionType` | `Update`, `Remove` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:AssignSensitivityLabelToEmailConnections
    ConnectionId="{x:Null}"
    SensitivityLabel="Confidential"
    DisplayName="Assign Sensitivity Label To Email" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Both `Item` and `SensitivityLabel` properties are required.
