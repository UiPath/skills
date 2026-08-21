# Move Outlook Desktop Mail Message

`UiPath.Mail.Outlook.Activities.MoveOutlookMessage`

Moves an Outlook email message to a specified folder.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The email message to move. |
| MailFolder | Mail folder | InArgument | string | Yes | | The destination Outlook folder to move the message to. |
| Account | Account | InArgument | string | No | | The email address of the Outlook account to use. When not specified, the default Outlook account is used. |

## XAML Example

```xml
<olm:MoveOutlookMessage
    MailMessage="[mailMessage]"
    MailFolder="Archive" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- The `MailFolder` specifies the destination folder path (e.g., "Archive", "Inbox\Processed")
- Use `Account` to specify which Outlook account's folder structure to use when multiple accounts are configured
- Related activities: GetOutlookMailMessages, DeleteOutlookMailMessage
