# Delete Outlook Desktop Mail Message

`UiPath.Mail.Outlook.Activities.DeleteOutlookMailMessage`

Deletes an email message.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The email message to delete. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| PermanentlyDelete | Permanently delete | bool | `false` | Indicates whether to delete the email message permanently. |

## XAML Example

```xml
<olm:DeleteOutlookMailMessage
    MailMessage="[mailMessage]"
    PermanentlyDelete="False" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- When `PermanentlyDelete` is false (default), the message is moved to the Deleted Items folder
- When `PermanentlyDelete` is true, the message is permanently removed and cannot be recovered
- Related activities: GetOutlookMailMessages, MoveOutlookMessage
