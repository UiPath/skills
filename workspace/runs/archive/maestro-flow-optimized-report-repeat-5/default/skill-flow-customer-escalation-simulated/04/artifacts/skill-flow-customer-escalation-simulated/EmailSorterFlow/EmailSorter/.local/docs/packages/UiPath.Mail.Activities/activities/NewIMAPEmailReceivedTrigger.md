# IMAP Email Received

`UiPath.Mail.Activities.IMAP.NewIMAPEmailReceivedTrigger`

Initiates an automation workflow when a new IMAP email arrives.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.IMAP.Triggers
**Platform:** Cross-platform

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| IncludeAttachments | Include attachments | InArgument | bool | No | `false` | Indicates if the email passed to next activities should contain the attachments. |
| MarkAsRead | Mark as read | InArgument | bool | No | `false` | Indicates whether to mark the retrieved email as read. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| MailFolder | Email folder | string | `"Inbox"` | The folder where the email will arrive. |
| WithAttachmentsOnly | With attachments only | bool | `false` | Indicates whether to consider only emails with attachments. Inline attachments are ignored. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Result | Email | [MailMessage](types/MailMessage.md) | The received email that triggered the event. |

## XAML Example

```xml
<imap:NewIMAPEmailReceivedTrigger
    DisplayName="IMAP Email Received"
    MailFolder="Inbox"
    WithAttachmentsOnly="False"
    MarkAsRead="[False]"
    IncludeAttachments="[False]"
    Result="[receivedEmail]" />
```

## Notes

- This is a trigger activity that starts a workflow when a new email arrives in the specified IMAP folder.
- The `MailFolder` property is validated at design time; a validation error is raised if it is empty.
- The `Filter` and `FilterExpression` properties exist but are not browsable (hidden from the designer).
- Connection details (server, port, credentials) are configured through the connection service, not directly on the activity.
- The trigger uses the `receivedEmail` output variable name internally.
- Related activities: `GetIMAPMailMessages`, `MoveIMAPMailMessageToFolder`, `DeleteImapMailMessage`.
