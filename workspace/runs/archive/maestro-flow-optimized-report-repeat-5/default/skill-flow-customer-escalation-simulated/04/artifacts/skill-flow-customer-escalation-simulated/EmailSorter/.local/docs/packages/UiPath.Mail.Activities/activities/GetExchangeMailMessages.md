# Get Exchange Mail Messages

`UiPath.Mail.Exchange.Activities.GetExchangeMailMessages`

Retrieves an email message from Exchange.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| CustomFolder | Mail folder | InArgument | string | No | | The name or path of the mail folder to retrieve messages from (e.g., "Inbox", "Inbox/Subfolder"). |
| SharedMailbox | SharedMailbox | InArgument | string | No | | The email address of a shared mailbox to access. When specified, messages are retrieved from the shared mailbox instead of the authenticated user's mailbox. |
| GetAttachements | GetAttachments | InArgument | bool | No | false | When set to true, message attachments are downloaded along with the messages. When false, only message metadata and body are retrieved. |
| IsBodyHtml | IsBodyHtml | InArgument | bool | No | false | When set to true, the message body is retrieved as HTML content. When false, the body is returned as plain text. |
| Top | Top | InArgument | int | No | 30 | The maximum number of messages to retrieve. Defaults to 30. |
| OnlyUnreadMessages | Only unread messages | InArgument | bool | No | true | When set to true, only unread messages are retrieved. |
| MarkAsRead | Mark as read | InArgument | bool | No | false | When set to true, retrieved messages are automatically marked as read on the server. |
| FilterExpression | The filter expression to be used. | InArgument | string | No | | An Exchange Web Services search filter string to narrow down which messages are retrieved (e.g., AQS or property-based filters). |
| FilterByMessageIds | Filter by message ids | InArgument | string[] | No | | An array of Exchange message IDs to retrieve specific messages. When provided, takes precedence over FilterExpression. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| OrderByDate | Order by date | EOrderByDate | OldestFirst | Specifies the sort order of retrieved messages by date. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Messages | Messages | OutArgument\<List\<[MailMessage](types/MailMessage.md)\>\> | The output collection of retrieved [MailMessage](types/MailMessage.md) objects. |

## XAML Example

```xml
<exc:GetExchangeMailMessages
    CustomFolder="Inbox"
    Top="[10]"
    OnlyUnreadMessages="[True]"
    MarkAsRead="[False]"
    IsBodyHtml="[True]"
    GetAttachements="[False]"
    Messages="[messages]" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- The `CustomFolder` property replaces the legacy `MailFolder` enum property and supports folder paths like "Inbox/Subfolder".
- `FilterByMessageIds` takes precedence over `FilterExpression` when both are specified.
- The `SharedMailbox` property allows accessing a shared mailbox if the authenticated user has permissions.
- Related activities: DeleteMail, MoveMessageToFolder, SaveExchangeAttachements, ExchangeScope.
