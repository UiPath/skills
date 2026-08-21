# Get Outlook Desktop Mail Messages

`UiPath.Mail.Outlook.Activities.GetOutlookMailMessages`

Retrieves an email message from Outlook.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailFolder | Mail folder | InArgument | string | Yes | "Inbox" | The name or path of the Outlook folder to retrieve messages from (e.g., "Inbox", "Inbox\Subfolder"). Defaults to "Inbox". |
| Account | Account | InArgument | string | No | | The email address of the Outlook account to use. When not specified, the default Outlook account is used. |
| Filter | Filter | InArgument | string | No | | A DASL filter string to narrow down which messages are retrieved. Uses Outlook's query syntax (e.g., "[Subject] = 'Test'"). |
| FilterByMessageIds | Filter by message ids | InArgument | string[] | No | | An array of Outlook message Entry IDs to retrieve specific messages. When provided, takes precedence over Filter. |
| Top | Top | InArgument | int | No | 30 | The maximum number of messages to retrieve. Defaults to 30. Use this to limit the number of results when only a subset of messages is needed. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the mail server to respond before timing out. A value of 0 means no timeout is applied. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| OnlyUnreadMessages | Only unread messages | bool | true | When set to true, only unread messages are retrieved. Defaults to true. |
| MarkAsRead | Mark as read | bool | | When set to true, retrieved messages are automatically marked as read in Outlook. |
| OrderByDate | Order by date | EOrderByDate | NewestFirst | Specifies the sort order of retrieved messages by date. Defaults to NewestFirst. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Messages | Messages | List<[MailMessage](types/MailMessage.md)> | The output collection of retrieved [MailMessage](types/MailMessage.md) objects. Each [MailMessage](types/MailMessage.md) contains the email's sender, recipients, subject, body, and attachments. |

## XAML Example

```xml
<olm:GetOutlookMailMessages
    MailFolder="Inbox"
    Top="[30]"
    OnlyUnreadMessages="True"
    MarkAsRead="False"
    OrderByDate="NewestFirst">
  <olm:GetOutlookMailMessages.Messages>
    <OutArgument x:TypeArguments="scg:List(sn:MailMessage)">[messages]</OutArgument>
  </olm:GetOutlookMailMessages.Messages>
</olm:GetOutlookMailMessages>
```

## Notes

- Windows only -- requires Outlook COM interop
- Returns a list of [MailMessage](types/MailMessage.md) objects from the specified folder
- The `Filter` property uses Outlook DASL query syntax, not SQL
- When `FilterByMessageIds` is provided, it takes precedence over the `Filter` property
- Default behavior retrieves only unread messages; set `OnlyUnreadMessages` to false to get all messages
- Related activities: SendOutlookMail, MoveOutlookMessage, DeleteOutlookMailMessage
