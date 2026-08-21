# Send Exchange Mail Message

`UiPath.Mail.Exchange.Activities.SendExchangeMail`

Sends an email message from Exchange.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| To | To | InArgument | string | Yes | | The primary recipient email addresses, separated by semicolons. |
| Cc | CC | InArgument | string | No | | The carbon copy (CC) recipient email addresses, separated by semicolons. |
| Bcc | BCC | InArgument | string | No | | The blind carbon copy (BCC) recipient email addresses, separated by semicolons. |
| Subject | Subject | InArgument | string | No | | The subject line of the email message. |
| Body | Body | InArgument | string | No | | The content of the email message body. Can be plain text or HTML depending on the IsBodyHtml setting. |
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | No | | An existing [MailMessage](types/MailMessage.md) to forward. When provided, the email is sent as a forwarded message. |
| Name | Name | InArgument | string | No | | The display name of the sender shown to recipients. |
| From | From | InArgument | string | No | | The sender email address. Used to send emails on behalf of another user when the authenticated account has delegation permissions. |
| SaveCopy | SaveCopy | InArgument | bool | No | false | When set to true, a copy of the sent message is saved in the Sent Items folder. |
| IsDraft | Is draft | InArgument | bool | No | false | When set to true, the message is saved as a draft instead of being sent immediately. |
| Files | Attachments | Property | List\<InArgument\<string\>\> | No | | A list of file paths for attachments to include with the email. |
| AttachmentsCollection | Attachments collection | Property | InArgument\<IEnumerable\<string\>\> | No | | A collection of file paths for attachments, as an alternative to Files for dynamically generated lists. |
| ResourceAttachments | Resource Attachments | Property | InArgument\<IEnumerable\<IResource\>\> | No | | A collection of IResource objects representing attachments to include. |
| ResourceAttachmentList | Resource Attachment List | Property | IEnumerable\<InArgument\<IResource\>\> | No | | A collection of individual IResource argument attachments to include. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| IsBodyHtml | IsBodyHtml | bool | false | When set to true, the Body is interpreted as HTML content. |

### Output

This activity does not produce output properties.

## XAML Example

```xml
<exc:SendExchangeMail
    To="recipient@example.com"
    Subject="Test Subject"
    Body="Hello from Exchange!"
    IsBodyHtml="False"
    SaveCopy="[True]" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- Setting `IsDraft` to true saves the message to the Drafts folder instead of sending it. Consider using `CreateDraft` for a dedicated draft creation workflow.
- The `MailMessage` property enables forwarding an existing message. Provide a [MailMessage](types/MailMessage.md) previously retrieved from Exchange.
- Multiple recipients can be specified by separating email addresses with semicolons.
- Related activities: CreateDraft, GetExchangeMailMessages, ExchangeScope.
