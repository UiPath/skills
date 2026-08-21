# Delete IMAP Email

`UiPath.Mail.IMAP.Activities.DeleteImapMailMessage`

Deletes the given mail message using IMAP.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.IMAP
**Platform:** Cross-platform

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail Message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The [MailMessage](types/MailMessage.md) object to delete from the IMAP server. Must be a message previously retrieved from the server. |
| FromFolder | From Folder | InArgument | string | No | | The name of the IMAP folder from which to delete the message. If not specified, the message is located using its unique identifier. |
| Server | Server | InArgument | string | No | | The hostname or IP address of the IMAP mail server. |
| Port | Port | InArgument | int | No | | The port number used to connect to the IMAP server. |
| Email | Email | InArgument | string | No | | The email address used to authenticate with the IMAP server. |
| Password | Password | InArgument | string | No | | The plain text password for IMAP server authentication. Mutually exclusive with SecurePassword. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for IMAP server authentication. Mutually exclusive with Password. |
| UseOAuth | Use OAuth | InArgument | bool | No | | Whether to use OAuth 2.0 authentication instead of basic credentials. |
| ClientName | Client name | InArgument | string | No | | An optional client application name sent to the IMAP server during identification. |
| ClientVersion | Client version | InArgument | string | No | | An optional client application version string sent to the IMAP server during identification. |
| IgnoreCRL | Ignore CRL | InArgument | bool | No | `false` | When true, skips certificate revocation list (CRL) checking during SSL/TLS connections. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| SecureConnection | Secure connection | SecureSocketEncryption | `Auto` | Specifies the type of SSL/TLS encryption to use when connecting to the IMAP server. |

### Output

This activity has no output properties.

## XAML Example

```xml
<imap:DeleteImapMailMessage
    DisplayName="Delete IMAP Email"
    Server="imap.gmail.com"
    Port="993"
    Email="user@example.com"
    Password="password"
    MailMessage="[emailMessage]"
    FromFolder="Inbox"
    SecureConnection="Auto" />
```

## Notes

- The `MailMessage` property is validated at design time; a validation error is raised if it has no expression set. See [MailMessage](types/MailMessage.md).
- `Password` and `SecurePassword` belong to mutually exclusive overload groups; provide only one.
- This operation is irreversible -- the message is permanently removed from the server.
- Related activities: `GetIMAPMailMessages`, `MoveIMAPMailMessageToFolder`.
