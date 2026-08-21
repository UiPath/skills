# Create Exchange Draft

`UiPath.Mail.Exchange.Activities.CreateDraft`

Creates an Exchange draft email message.

**Package:** `UiPath.Mail.Activities`
**Category:** Mail.Exchange
**Platform:** Windows only

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| To | To | InArgument | string | No | | The primary recipient email addresses, separated by semicolons. |
| Cc | CC | InArgument | string | No | | The carbon copy (CC) recipient email addresses, separated by semicolons. |
| Bcc | BCC | InArgument | string | No | | The blind carbon copy (BCC) recipient email addresses, separated by semicolons. |
| Subject | Subject | InArgument | string | No | | The subject line of the draft email. |
| Body | Body | InArgument | string | No | | The content of the draft email body. Can be plain text or HTML depending on the IsBodyHtml setting. |
| MailMessage | Mail message | InArgument | [MailMessage](types/MailMessage.md) | No | | An existing [MailMessage](types/MailMessage.md) to use as the basis for the draft. When provided, the draft is created as a forward of this message. |
| Name | Name | InArgument | string | No | | The display name of the sender shown to recipients. |
| From | From | InArgument | string | No | | The sender email address. Used to create drafts on behalf of another user. |
| AttachmentsCollection | Attachments | Property | InArgument\<IEnumerable\<string\>\> | No | | A collection of file paths for attachments, as an alternative to Files. |
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
<exc:CreateDraft
    To="recipient@example.com"
    Subject="Draft Subject"
    Body="Hello from Exchange!"
    IsBodyHtml="False" />
```

## Notes

- Windows only -- requires Exchange Web Services (EWS).
- ExchangeScope: when placed inside an ExchangeScope, the activity inherits the authenticated connection. When used standalone, connection properties from the base ExchangeActivity are used.
- The `MailMessage` property enables creating a draft that forwards an existing [MailMessage](types/MailMessage.md).
- Multiple recipients can be specified by separating email addresses with semicolons.
- Related activities: SendExchangeMail, GetExchangeMailMessages, ExchangeScope.
