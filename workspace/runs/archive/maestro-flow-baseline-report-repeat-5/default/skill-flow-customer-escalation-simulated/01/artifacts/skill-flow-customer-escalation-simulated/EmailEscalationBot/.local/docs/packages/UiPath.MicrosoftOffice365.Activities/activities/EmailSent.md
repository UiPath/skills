# Email Sent (Trigger)

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Mail.Triggers.EmailSent`

Trigger that fires when an email is sent from the specified mailbox.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Mail |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `MailboxArg` | Mailbox | | [`TriggerMailboxArgument`](components/TriggerMailboxArgument.md) | No | | Specifies the mailbox to use. See [TriggerMailboxArgument](components/TriggerMailboxArgument.md) for input modes. |
| `WithAttachmentsOnly` | With Attachments Only | Options | `bool` | No | `False` | Retrieve only emails with attachments. |
| `IncludeAttachments` | Include Attachments | Options | `InArgument<bool>` | No | `False` | Indicates if the email should contain the attachments. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Result` | Sent Email | Output | [`OutArgument<Office365Message>`](types/Office365Message.md) | The sent email that triggered the activity. |

## Output Model

See [`Office365Message`](types/Office365Message.md) for the email object structure.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umam="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Triggers;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umam:EmailSent
    DisplayName="Email Sent" />
```

## Notes

- This is a trigger activity used to start workflows when an email is sent.
- Supports filtering via the `Filter` property (condition builder).
- In debug mode, retrieves the most recent matching sent email.
