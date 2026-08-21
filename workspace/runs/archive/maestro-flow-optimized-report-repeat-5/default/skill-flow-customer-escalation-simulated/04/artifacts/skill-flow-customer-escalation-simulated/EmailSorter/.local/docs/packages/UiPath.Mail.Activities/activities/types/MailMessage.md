# MailMessage

`System.Net.Mail.MailMessage`

Represents an email message. This is a .NET standard type used throughout the Mail activities package as the primary data structure for reading, sending, and manipulating email messages.

## Properties

| Name | Type | Description |
|------|------|-------------|
| From | MailAddress | The sender's email address. |
| To | MailAddressCollection | The recipients of the email. |
| CC | MailAddressCollection | The carbon copy (CC) recipients. |
| Bcc | MailAddressCollection | The blind carbon copy (BCC) recipients. |
| ReplyToList | MailAddressCollection | The list of reply-to addresses. |
| Subject | string | The subject line of the email. |
| Body | string | The body content of the email (plain text or HTML depending on IsBodyHtml). |
| IsBodyHtml | bool | Indicates whether the Body is in HTML format. |
| Attachments | AttachmentCollection | The collection of file attachments on the email. |
| AlternateViews | AlternateViewCollection | Alternate views of the message content (e.g., both plain text and HTML). |
| Headers | NameValueCollection | The email headers collection. Use `Headers["Date"]` to get the received date and `Headers["Message-ID"]` to get the unique message identifier. |
| Priority | MailPriority | The priority of the email (Normal, Low, or High). |
| DeliveryNotificationOptions | DeliveryNotificationOptions | The delivery notification options (None, OnSuccess, OnFailure, Delay, Never). |
| Sender | MailAddress | The address of the sender (distinct from From when sending on behalf of another). |
| BodyEncoding | Encoding | The encoding used for the message body. |
| SubjectEncoding | Encoding | The encoding used for the subject. |
| HeadersEncoding | Encoding | The encoding used for custom headers. |
| BodyTransferEncoding | TransferEncoding | The transfer encoding for the body content. |

## Common Header Values

Access these via the `Headers` property:

| Header | Example | Description |
|--------|---------|-------------|
| `Date` | `Headers["Date"]` | The date and time the email was sent. |
| `Message-ID` | `Headers["Message-ID"]` | The unique message identifier assigned by the mail server. |
| `In-Reply-To` | `Headers["In-Reply-To"]` | The Message-ID of the email this message replies to. |
| `X-Mailer` | `Headers["X-Mailer"]` | The email client or application that sent the message. |

## Used By

- [GetOutlookMailMessages](../GetOutlookMailMessages.md) -- output mail list
- [GetIMAPMailMessages](../GetIMAPMailMessages.md) -- output mail list
- [GetPOP3MailMessages](../GetPOP3MailMessages.md) -- output mail list
- [GetExchangeMailMessages](../GetExchangeMailMessages.md) -- output mail list
- [SendMail](../SendMail.md) -- constructed and sent
- [SendOutlookMail](../SendOutlookMail.md) -- constructed and sent
- [SendExchangeMail](../SendExchangeMail.md) -- constructed and sent
- [SaveMail](../SaveMail.md) -- input mail to save
- [SaveMailAttachments](../SaveMailAttachments.md) -- input mail to extract attachments from
- [ReplyToOutlookMailMessage](../ReplyToOutlookMailMessage.md) -- input mail to reply to
- [DeleteMail](../DeleteMail.md) -- input mail to delete
- [ForEachEmailX](../ForEachEmailX.md) -- iterated mail item
- [NewIMAPEmailReceivedTrigger](../NewIMAPEmailReceivedTrigger.md) -- trigger output via MailEventInfo
- [OutlookMailMessagesTrigger](../OutlookMailMessagesTrigger.md) -- trigger output via MailEventInfo
