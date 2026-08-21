# MailEventInfo

`UiPath.Mail.Activities.Triggers.MailEventInfo`

Argument passed to mail trigger callbacks. Wraps a MailMessage received by a mail trigger. Extends `UiPath.Platform.Triggers.TriggerArgs`.

## Properties

| Name | Type | Description |
|------|------|-------------|
| MailMessage | [MailMessage](MailMessage.md) | The email message that triggered the event. Contains the full message content including headers, body, and attachments. |

## Used By

- [NewIMAPEmailReceivedTrigger](../NewIMAPEmailReceivedTrigger.md) -- output argument when a new IMAP email arrives
- [OutlookMailMessagesTrigger](../OutlookMailMessagesTrigger.md) -- output argument when a new Outlook email arrives
- [NewO365EmailTrigger](../NewO365EmailTrigger.md) -- output argument when a new Office 365 email arrives
- [NewGmailTrigger](../NewGmailTrigger.md) -- output argument when a new Gmail email arrives
