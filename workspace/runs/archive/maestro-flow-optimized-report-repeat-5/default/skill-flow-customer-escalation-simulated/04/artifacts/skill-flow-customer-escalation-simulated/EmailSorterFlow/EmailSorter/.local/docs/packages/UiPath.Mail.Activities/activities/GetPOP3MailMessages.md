# Get POP3 Email List

`UiPath.Mail.POP3.Activities.GetPOP3MailMessages`

Retrieves a POP3 email message from a specified server.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.POP3

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| Server | Server | InArgument | string | No | | The hostname or IP address of the POP3 mail server (e.g., "pop.gmail.com"). |
| Port | Port | InArgument | int | No | | The port number used to connect to the POP3 server (e.g., 995 for SSL/TLS connections). |
| Email | Email | InArgument | string | No | | The email address used to authenticate with the POP3 server. |
| Password | Password | InArgument | string | No | | The plain text password for POP3 server authentication. Mutually exclusive with SecurePassword. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for POP3 server authentication. Mutually exclusive with Password. |
| UseOAuth | Use OAuth | InArgument | bool | No | | Whether to use OAuth 2.0 authentication instead of basic credentials. |
| Top | Top | InArgument | int | No | 30 | The maximum number of messages to retrieve. |
| DeleteMessages | DeleteMessages | InArgument | bool | No | false | When set to true, messages are deleted from the POP3 server after being retrieved. Use with caution as this is irreversible. |
| IgnoreCRL | Ignore CRL | InArgument | bool | No | false | When set to true, skips certificate revocation list (CRL) checking during SSL/TLS connections. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the mail server to respond before timing out. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| SecureConnection | Secure connection | SecureSocketEncryption | Auto | Specifies the type of SSL/TLS encryption to use when connecting to the POP3 server. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Messages | Messages | List<[MailMessage](types/MailMessage.md)> | The output collection of retrieved [`MailMessage`](types/MailMessage.md) objects. Each contains the email's sender, recipients, subject, body, and attachments. |

## XAML Example

```xml
<pop:GetPOP3MailMessages
    Server="pop.gmail.com"
    Port="[995]"
    Email="user@gmail.com"
    Password="password"
    Top="[10]"
    SecureConnection="Auto"
    DeleteMessages="[False]" />
```

## Notes

- `Password` and `SecurePassword` are mutually exclusive (overload groups).
- POP3 does not support server-side filtering, mark-as-read, or mail folder selection. Use IMAP if you need those features.
- The `DeleteMessages` option is irreversible -- messages deleted from the POP3 server cannot be recovered.
- The activity uses MailKit internally and supports OAuth 2.0 authentication.
- The `Top` property defaults to 30 messages if not specified.
- Related activities: GetIMAPMailMessages, SendMail, SaveMail.
