# Turn On Automatic Replies

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.TurnOnAutomaticRepliesConnections`

Activates and configures automatic replies (Out of Office) for the user's mailbox.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `StartTime` | Start Time | Input | `InArgument<DateTimeOffset>` | No | | The date and time when the Out of Office starts. |
| `EndTime` | End Time | Input | `InArgument<DateTimeOffset>` | No | | The date and time when the Out of Office ends. |
| `InternalMessage` | Internal Message | Input | `InArgument<string>` | No | | The automatic replies message to be sent inside the organization. |
| `SendRepliesOutsideOrganization` | Send Replies Outside Organization | Input | `InArgument<bool>` | No | `False` | Whether automatic replies can be sent outside the organization. |
| `SendRepliesToContactsOnly` | Send Replies To Contacts Only | Input | `InArgument<bool>` | No | `False` | Whether automatic replies are sent only to contacts for external users. |
| `ExternalMessage` | External Message | Input | `InArgument<string>` | No | | The automatic replies message to be sent outside the organization. |

## Output Model

This activity does not return an output object.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:TurnOnAutomaticRepliesConnections
    ConnectionId="{x:Null}"
    InternalMessage="I am currently out of office."
    DisplayName="Turn On Automatic Replies" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Requires the `MailboxSettings.ReadWrite` scope.
