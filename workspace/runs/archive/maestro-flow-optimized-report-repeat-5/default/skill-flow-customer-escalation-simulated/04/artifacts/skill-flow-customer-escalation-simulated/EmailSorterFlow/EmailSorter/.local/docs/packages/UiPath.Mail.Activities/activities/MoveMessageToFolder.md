# Move Message to Folder

`UiPath.Mail.Exchange.Activities.MoveMessageToFolder`

Moves an email message from Exchange to another folder.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [MailMessage](types/MailMessage.md) object to move to a different folder. Must be a message previously retrieved from Exchange. |
| MailFolder | Mail folder | InArgument | string | Yes | | The destination folder path to move the message to (e.g., "Archive", "Inbox/Important"). |
| SharedMailbox | SharedMailbox | InArgument | string | No | | The email address of a shared mailbox. When specified, the folder is resolved within the shared mailbox. |

### Configuration

This activity does not have additional configuration properties.

### Output

This activity does not produce dedicated output properties. The [MailMessage](types/MailMessage.md) input argument is updated in-place with the new Exchange item ID after the move.

## XAML Example

```xml
<exc:MoveMessageToFolder
    MailMessage="[mailMessage]"
    MailFolder="Archive" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- The `MailMessage` must be a [MailMessage](types/MailMessage.md) previously retrieved via `GetExchangeMailMessages`, since it relies on the Exchange item ID stored in the message headers.
- The `MailFolder` property accepts folder paths such as "Archive" or "Inbox/Important". Subfolder paths use "/" as the separator.
- When `SharedMailbox` is specified, the destination folder is resolved within the shared mailbox.
- Related activities: GetExchangeMailMessages, DeleteMail, ExchangeScope.
