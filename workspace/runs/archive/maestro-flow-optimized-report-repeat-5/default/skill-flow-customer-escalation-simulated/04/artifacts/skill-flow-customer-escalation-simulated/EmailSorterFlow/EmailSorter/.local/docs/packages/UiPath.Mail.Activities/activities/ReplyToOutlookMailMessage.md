# Reply to Outlook Desktop Mail Message

`UiPath.Mail.Outlook.Activities.ReplyToOutlookMailMessage`

Reply to an Outlook email message. Takes a MailMessage object previously retrieved from Outlook (e.g., via Get Outlook Mail Messages).

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Outlook Windows
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | Yes | | The original [MailMessage](types/MailMessage.md) to reply to. Must be a message previously retrieved from Outlook. |
| Body | Body | InArgument | string | No | | The content of the reply message body. This text is added above the original message content. |
| NewSubject | New subject | InArgument | string | No | | The new subject of the email message. |
| AddTo | To | InArgument | string | No | | Additional primary recipients of the email. |
| AddCc | CC | InArgument | string | No | | Additional secondary recipients of the email. |
| AddBcc | BCC | InArgument | string | No | | Additional hidden recipients of the email. |
| ReplyFrom | Reply from | InArgument | string | No | | The sender to reply from. |
| TimeoutMS | TimeoutMS | InArgument | int | No | | The maximum time in milliseconds to wait for the reply operation to complete before timing out. Defaults to 30000 (30 seconds). |
| Files | Attachments | Property | List\<InArgument\<string\>\> | No | | A list of file paths for attachments to include with the reply. |
| AttachmentsCollection | Attachments collection | Property | InArgument\<IEnumerable\<string\>\> | No | | A collection of file paths for attachments, as an alternative to Files for dynamically generated lists. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| ReplyAll | Reply all | bool | | When set to true, the reply is sent to all original recipients. When false, the reply is sent only to the original sender. |
| Importance | Importance | MailImportance | `MailImportance.Normal` | The importance of the mail. |
| IsBodyHtml | IsBodyHtml | bool | | When set to true, the Body property is interpreted as HTML content. When false, the body is treated as plain text. |

## XAML Example

```xml
<olm:ReplyToOutlookMailMessage
    MailMessage="[originalMessage]"
    Body="Thank you for your email."
    ReplyAll="False"
    IsBodyHtml="False" />
```

## Notes

- Windows only -- requires Outlook COM interop
- The [`MailMessage`](types/MailMessage.md) input must be a message previously retrieved from Outlook (e.g., via GetOutlookMailMessages)
- The default timeout is 30000 ms (30 seconds)
- Use `AddTo`, `AddCc`, and `AddBcc` to include additional recipients beyond the original sender/recipients
- `NewSubject` overrides the default "RE: ..." subject line
- Related activities: GetOutlookMailMessages, SendOutlookMail
