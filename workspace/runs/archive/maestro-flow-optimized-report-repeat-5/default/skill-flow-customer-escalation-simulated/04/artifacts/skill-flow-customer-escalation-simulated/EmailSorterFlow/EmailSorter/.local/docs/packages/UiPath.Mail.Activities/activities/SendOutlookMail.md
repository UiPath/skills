# Send Outlook Desktop Mail Message

`UiPath.Mail.Outlook.Activities.SendOutlookMail`

Sends an email message from Outlook.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| To | To | InArgument | string | No | | The primary recipient email addresses, separated by semicolons. |
| Cc | Cc | InArgument | string | No | | The carbon copy (CC) recipient email addresses, separated by semicolons. CC recipients are visible to all other recipients. |
| Bcc | Bcc | InArgument | string | No | | The blind carbon copy (BCC) recipient email addresses, separated by semicolons. BCC recipients are hidden from other recipients. |
| Subject | Subject | InArgument | string | No | | The subject line of the email message. |
| Body | Body | InArgument | string | No | | The content of the email message body. Can be plain text or HTML depending on the IsBodyHtml setting. |
| Account | Account | InArgument | string | No | | The email address of the Outlook account to use for sending. When not specified, the default Outlook account is used. |
| SentOnBehalfOfName | Send on behalf of | InArgument | string | No | | The email address or display name to appear as the sender. Requires appropriate delegate permissions in the mail system. |
| ReplyTo | Reply to | InArgument | string | No | | The email address(es) that will receive replies to this message. Separated by semicolons if multiple addresses are specified. |
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | No | | An existing [MailMessage](types/MailMessage.md) object to forward. When provided, the email is sent as a forwarded message rather than a new composition. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the mail server to respond before timing out. A value of 0 means no timeout. |
| ContinueOnError | ContinueOnError | InArgument | bool | No | | Specifies to continue executing the remaining activities even if the current activity failed. Only boolean values (True, False) are supported. |
| Files | Attachments | Property | List\<InArgument\<string\>\> | No | | A list of file paths for attachments to include with the email. Each path should point to an existing file on disk. |
| AttachmentsCollection | Attachments Collection | Property | InArgument\<IEnumerable\<string\>\> | No | | A collection of file paths for attachments. Use as an alternative to Files when the attachment list is dynamically generated. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| IsBodyHtml | IsBodyHtml | bool | | When set to true, the Body property is interpreted as HTML content. When false, the body is treated as plain text. |
| IsDraft | Is draft | bool | | When set to true, the message is saved as a draft in the Drafts folder instead of being sent. |
| Importance | Importance | MailImportance | `MailImportance.Normal` | The importance level of the email message (Normal, High, or Low). Defaults to Normal. |
| Sensitivity | Sensitivity | MailSensitivity | `MailSensitivity.Normal` | The sensitivity level of the email message (Normal, Personal, Private, or Confidential). Defaults to Normal. |

## XAML Example

```xml
<olm:SendOutlookMail
    To="recipient@example.com"
    Subject="Test Subject"
    Body="Hello, World!"
    IsBodyHtml="False"
    IsDraft="False" />
```

## Notes

- Windows only -- requires Outlook COM interop
- Outlook must be installed and configured on the machine
- When [`MailMessage`](types/MailMessage.md) is provided, the email is forwarded rather than sent as a new message
- The `IsDraft` property saves the message to the Drafts folder without sending
- `SentOnBehalfOfName` requires delegate/send-on-behalf permissions configured in the mail system
- Related activities: GetOutlookMailMessages, ReplyToOutlookMailMessage
