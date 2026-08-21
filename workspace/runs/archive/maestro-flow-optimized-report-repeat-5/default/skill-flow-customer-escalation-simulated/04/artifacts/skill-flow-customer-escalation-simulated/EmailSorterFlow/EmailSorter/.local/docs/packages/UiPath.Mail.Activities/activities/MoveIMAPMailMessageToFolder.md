# Move IMAP Email

`UiPath.Mail.IMAP.Activities.MoveIMAPMailMessageToFolder`

Moves an IMAP email message to a specified folder.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.IMAP
**Platform:** Cross-platform

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [MailMessage](types/MailMessage.md) object to move. Must be a message previously retrieved from the server. |
| MailFolder | Mail folder | InArgument | string | No | | The destination folder to move the message to (e.g., "Archive", "Important"). |
| FromFolder | FromFolder | InArgument | string | No | | The source folder from which to move the message. Required to locate the message on the server. |
| Server | Server | InArgument | string | No | | The hostname or IP address of the IMAP mail server. |
| Port | Port | InArgument | int | No | | The port number used to connect to the IMAP server. |
| Email | Email | InArgument | string | No | | The email address used to authenticate with the IMAP server. |
| Password | Password | InArgument | string | No | | The plain text password for IMAP server authentication. Mutually exclusive with SecurePassword. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for IMAP server authentication. Mutually exclusive with Password. |
| UseOAuth | Use OAuth | InArgument | bool | No | | Whether to use OAuth 2.0 authentication instead of basic credentials. |
| ClientName | ClientName | InArgument | string | No | | An optional client application name sent to the IMAP server during identification. |
| ClientVersion | ClientVersion | InArgument | string | No | | An optional client application version string sent to the IMAP server during identification. |
| IgnoreCRL | Ignore CRL | InArgument | bool | No | `false` | When true, skips certificate revocation list (CRL) checking during SSL/TLS connections. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| EnableSSL | EnableSSL | bool | `true` | Indicates whether to use SSL when connecting to the IMAP server. Deprecated in favor of SecureConnection. |
| SecureConnection | Secure connection | SecureSocketEncryption | `Auto` | Specifies the type of SSL/TLS encryption to use when connecting to the IMAP server. |

### Output

This activity has no output properties.

## XAML Example

```xml
<imap:MoveIMAPMailMessageToFolder
    DisplayName="Move IMAP Email"
    Server="imap.gmail.com"
    Port="993"
    Email="user@example.com"
    Password="password"
    MailMessage="[emailMessage]"
    FromFolder="Inbox"
    MailFolder="Archive"
    SecureConnection="Auto" />
```

## Notes

- The `MailMessage` property is validated at design time; a validation error is raised if it has no expression set. See [MailMessage](types/MailMessage.md).
- `Password` and `SecurePassword` belong to mutually exclusive overload groups; provide only one.
- The `EnableSSL` property is browsable but deprecated; prefer using `SecureConnection` instead.
- Related activities: `GetIMAPMailMessages`, `DeleteImapMailMessage`.
