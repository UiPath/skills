# Send SMTP Email

`UiPath.Mail.SMTP.Activities.SendMail`

Sends an email message by using the SMTP protocol.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.SMTP

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| To | To | InArgument | string | Yes (for Forward) | | The primary recipient email addresses, separated by semicolons. |
| Cc | Cc | InArgument | string | No | | The carbon copy (CC) recipient email addresses, separated by semicolons. |
| Bcc | Bcc | InArgument | string | No | | The blind carbon copy (BCC) recipient email addresses, separated by semicolons. |
| Subject | Subject | InArgument | string | No | | The subject line of the email message. |
| Body | Body | InArgument | string | No | | The content of the email message body. Can be plain text or HTML depending on the IsBodyHtml setting. |
| Email | Email | InArgument | string | No | | The email address used to authenticate with the SMTP server. |
| Password | Password | InArgument | string | No | | The plain text password for SMTP server authentication. |
| SecurePassword | Secure password | InArgument | SecureString | No | | The password as a SecureString for SMTP server authentication, providing better in-memory security. |
| Server | Server | InArgument | string | No | | The hostname or IP address of the SMTP mail server (e.g., "smtp.gmail.com"). |
| Port | Port | InArgument | int | No | | The port number used to connect to the SMTP server (e.g., 587 for STARTTLS, 465 for SSL). |
| Name | Name | InArgument | string | No | | The display name of the sender shown to recipients in their mail client. |
| From | From | InArgument | string | No | | The sender email address that appears in the From field. If not specified, the Email property value is used. |
| Action | Source email action | InArgument | MailAction | No | MailAction.Forward | Specifies whether this is a forward or reply action when a [`MailMessage`](types/MailMessage.md) is provided. |
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | No | | An existing [`MailMessage`](types/MailMessage.md) object to forward or reply to. Required for Reply/ReplyAll actions. |
| Files | Attachments | Property | List\<InArgument\<string\>\> | No | | A list of file paths for attachments to include with the email. |
| AttachmentsCollection | Attachments Collection | InArgument | IEnumerable\<string\> | No | | A collection of file paths for attachments. Use when the attachment list is dynamically generated. |
| ResourceAttachments | Resource Attachments | Property | InArgument\<IEnumerable\<IResource\>\> | No | | A collection of IResource objects representing attachments to include with the email. |
| ResourceAttachmentList | Resource Attachment List | Property | IEnumerable\<InArgument\<IResource\>\> | No | | A collection of individual IResource argument attachments to include with the email. |
| UseOAuth | Use OAuth | InArgument | bool | No | | Whether to use OAuth 2.0 authentication instead of basic credentials. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the mail server to respond before timing out. |
| ReplyTo | Reply to | InArgument | string | No | | The email address(es) that will receive replies to this message. Separated by semicolons. |
| IgnoreCRL | Ignore CRL | InArgument | bool | No | false | When set to true, skips certificate revocation list (CRL) checking during SSL/TLS connections. |
| ContinueOnError | ContinueOnError | InArgument | bool | No | | Specifies to continue executing the remaining activities even if the current activity failed. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| IsBodyHtml | IsBodyHtml | bool | false | When set to true, the Body property is interpreted as HTML content. |
| SecureConnection | Secure connection | SecureSocketEncryption | Auto | Specifies the type of SSL/TLS encryption to use when connecting to the SMTP server. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| Result | Status code | string | The output SMTP status code as a string (e.g., "250" for success). |

## XAML Example

```xml
<smp:SendMail
    Server="smtp.gmail.com"
    Port="[587]"
    Email="user@gmail.com"
    Password="password"
    To="recipient@example.com"
    Subject="Test Subject"
    Body="Hello, World!"
    IsBodyHtml="False"
    SecureConnection="Auto" />
```

## Notes

- When `Action` is set to `MailAction.Forward`, the `To` property is required.
- When `Action` is set to `MailAction.Reply` or `MailAction.ReplyAll`, the [`MailMessage`](types/MailMessage.md) property is required.
- `Password` and `SecurePassword` are mutually exclusive (overload groups).
- Attachments are cleared when replying (not forwarding) to prevent re-sending original attachments.
- The activity uses MailKit internally and supports OAuth 2.0 authentication.
- Related activities: GetPOP3MailMessages, GetIMAPMailMessages, SaveMail.
