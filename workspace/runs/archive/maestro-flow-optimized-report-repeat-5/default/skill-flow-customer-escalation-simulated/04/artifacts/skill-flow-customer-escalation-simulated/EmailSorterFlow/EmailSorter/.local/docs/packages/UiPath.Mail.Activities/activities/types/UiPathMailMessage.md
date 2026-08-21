# UiPathMailMessage

`UiPath.Mail.UiPathMailMessage`

A cross-platform email message that extends System.Net.Mail.MailMessage. This type is used by newer Mail activities and provides the same properties as MailMessage with display ordering and category metadata for the UiPath designer.

Inherits all properties from [MailMessage](MailMessage.md).

## Simplified Properties

These properties are re-declared with `[Category(PropertyCategory.Simplified)]` for designer display ordering. They delegate to the base MailMessage implementation.

| Name | Type | Description |
|------|------|-------------|
| To | MailAddressCollection | The recipients of the email. (Order 1) |
| From | MailAddress | The sender's email address. (Order 2) |
| ReplyToList | MailAddressCollection | The list of reply-to addresses. (Order 3) |
| Body | string | The body content of the email. (Order 4) |
| Subject | string | The subject line of the email. (Order 5) |
| CC | MailAddressCollection | The carbon copy (CC) recipients. (Order 6) |
| Bcc | MailAddressCollection | The blind carbon copy (BCC) recipients. (Order 7) |

## Constructor

| Signature | Description |
|-----------|-------------|
| `UiPathMailMessage(MailMessage message)` | Creates a UiPathMailMessage by copying all properties from an existing MailMessage, including To, CC, Bcc, ReplyToList, Attachments, AlternateViews, Headers, encoding, and priority settings. |

## Used By

- [GetMailMessageFromFile](../GetMailMessageFromFile.md) -- output type for parsed .eml files
