# Mark Outlook Desktop Mail as Read or Unread

`UiPath.Mail.Outlook.Activities.MarkOutlookMailAsRead`

Marks the specified mail message as read or unread.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The mail message to mark as read or unread. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| MarkAs | Mark as | MarkMailAs | `MarkMailAs.Read` | The new state of the specified mail message. |

## XAML Example

```xml
<olm:MarkOutlookMailAsRead
    MailMessage="[mailMessage]"
    MarkAs="Read" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- Use `MarkAs` to toggle between Read and Unread states
- Related activities: GetOutlookMailMessages, DeleteOutlookMailMessage
