# Get IMAP Email List

`UiPath.Mail.IMAP.Activities.GetIMAPMailMessages`

Retrieves an IMAP email message from a specified server.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.IMAP
**Platform:** Cross-platform

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Server | Server | InArgument | string | No | | The hostname or IP address of the IMAP mail server (e.g., "imap.gmail.com"). |
| Port | Port | InArgument | int | No | | The port number used to connect to the IMAP server (e.g., 993 for SSL/TLS connections). |
| MailFolder | Mail folder | InArgument | string | No | `"Inbox"` | The name of the mail folder from which to retrieve messages (e.g., "Inbox", "Sent"). |
| Email | Email | InArgument | string | No | | The email address used to authenticate with the IMAP server. |
| Password | Password | InArgument | string | No | | The plain text password for IMAP server authentication. Mutually exclusive with SecurePassword. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for IMAP server authentication. Mutually exclusive with Password. |
| UseOAuth | Use OAuth | InArgument | bool | No | | Whether to use OAuth 2.0 authentication instead of basic username/password credentials. |
| ClientName | Client name | InArgument | string | No | | An optional client application name sent to the IMAP server during the identification handshake. |
| ClientVersion | Client version | InArgument | string | No | | An optional client application version string sent to the IMAP server during the identification handshake. |
| Top | Top | InArgument | int | No | `30` | The maximum number of messages to retrieve. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the mail server to respond before timing out. |
| FilterExpression | FilterExpression | InArgument | string | No | | An IMAP search filter expression using IMAP SEARCH command syntax (e.g., `SUBJECT "test" FROM "user@example.com"`). |
| FilterExpressionCharacterSet | FilterExpressionCharacterSet | InArgument | string | No | `"UTF-8"` | The character set used to encode the IMAP filter expression. |
| DeleteMessages | DeleteMessages | InArgument | bool | No | | When true, messages are deleted from the server after being retrieved. |
| OnlyUnreadMessages | Only unread messages | InArgument | bool | No | `true` | When true, only unread (unseen) messages are retrieved. |
| MarkAsRead | Mark as read | InArgument | bool | No | | When true, retrieved messages are marked as read on the server. |
| IgnoreCRL | Ignore CRL | InArgument | bool | No | `false` | When true, skips certificate revocation list (CRL) checking during SSL/TLS connections. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| OrderByDate | OrderByDate | EOrderByDate | `NewestFirst` | Specifies the sort order of retrieved messages by date. |
| SecureConnection | Secure connection | SecureSocketEncryption | `Auto` | Specifies the type of SSL/TLS encryption to use when connecting to the IMAP server. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Messages | Messages | List<[MailMessage](types/MailMessage.md)> | The output collection of retrieved [MailMessage](types/MailMessage.md) objects. Each [MailMessage](types/MailMessage.md) contains the email's sender, recipients, subject, body, and attachments. |

## XAML Example

```xml
<imap:GetIMAPMailMessages
    DisplayName="Get IMAP Email List"
    Server="imap.gmail.com"
    Port="993"
    Email="user@example.com"
    Password="password"
    MailFolder="Inbox"
    OnlyUnreadMessages="True"
    MarkAsRead="False"
    Top="30"
    OrderByDate="NewestFirst"
    SecureConnection="Auto"
    Messages="[emailMessages]" />
```

## Notes

- Inherits from `GetMailActivity`, which provides the `Top`, `TimeoutMS`, and `Messages` properties.
- `Password` and `SecurePassword` belong to mutually exclusive overload groups; provide only one.
- The `EnableSSL` property exists but is not browsable (hidden from the designer); use `SecureConnection` instead.
- The `FilterExpression` uses IMAP SEARCH command syntax, not LINQ or SQL-like queries.
- Related activities: `MoveIMAPMailMessageToFolder`, `DeleteImapMailMessage`, `NewIMAPEmailReceivedTrigger`.
