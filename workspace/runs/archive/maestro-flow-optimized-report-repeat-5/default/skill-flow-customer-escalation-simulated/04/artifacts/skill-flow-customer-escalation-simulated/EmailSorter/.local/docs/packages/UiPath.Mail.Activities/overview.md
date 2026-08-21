# UiPath Mail Activities

`UiPath.Mail.Activities`

Send, receive, and manage email messages across multiple protocols: SMTP, IMAP, POP3, Exchange (EWS), and Outlook (COM). Includes triggers for new email events, attachment handling, and message operations (move, delete, mark as read).

## Documentation

- [XAML Activities Reference](activities/) — Per-activity documentation for XAML workflows
- [Coded Workflow API Reference](coded/coded-api.md) — Service API for coded C# workflows (`mail.Smtp(...)`, `mail.Imap(...)`, `mail.Pop3(...)`)
- [Type Reference](activities/types/) — Output and input model types (MailMessage, UiPathMailMessage, MailEventInfo)
- [Filter Reference](activities/filtering/) — Mail filter collections (MailFilterArgument, TriggerMailFilterCollection)

## Activities

### SMTP (Cross-platform)

| Activity | Description |
|----------|-------------|
| [Send SMTP Email](activities/SendMail.md) | Send an email message using SMTP protocol |

### IMAP (Cross-platform)

| Activity | Description |
|----------|-------------|
| [Get IMAP Email List](activities/GetIMAPMailMessages.md) | Retrieve email messages from an IMAP server |
| [Move IMAP Email](activities/MoveIMAPMailMessageToFolder.md) | Move an email to a different folder on an IMAP server |
| [Delete IMAP Email](activities/DeleteImapMailMessage.md) | Delete an email from an IMAP server |
| [IMAP Email Received](activities/NewIMAPEmailReceivedTrigger.md) | Trigger when a new email is received via IMAP |

### POP3 (Cross-platform)

| Activity | Description |
|----------|-------------|
| [Get POP3 Email List](activities/GetPOP3MailMessages.md) | Retrieve email messages from a POP3 server |

### Outlook (Windows only)

| Activity | Description |
|----------|-------------|
| [Send Outlook Email](activities/SendOutlookMail.md) | Send an email using Outlook |
| [Get Outlook Email List](activities/GetOutlookMailMessages.md) | Retrieve email messages from Outlook |
| [Reply to Outlook Email](activities/ReplyToOutlookMailMessage.md) | Reply to an Outlook email message |
| [Mark Outlook Email as Read](activities/MarkOutlookMailAsRead.md) | Mark an Outlook email as read or unread |
| [Set Outlook Email Categories](activities/SetOutlookMailCategories.md) | Set categories on an Outlook email |
| [Delete Outlook Email](activities/DeleteOutlookMailMessage.md) | Delete an email from Outlook |
| [Save Outlook Email](activities/SaveOutlookMailMessage.md) | Save an Outlook email to disk |
| [Move Outlook Email](activities/MoveOutlookMessage.md) | Move an Outlook email to a different folder |
| [Outlook Email Received](activities/OutlookMailMessagesTrigger.md) | Trigger when a new email is received in Outlook |

### Exchange EWS (Windows only)

| Activity | Description |
|----------|-------------|
| [Exchange Scope](activities/ExchangeScope.md) | Establish an Exchange connection for child activities |
| [Send Exchange Email](activities/SendExchangeMail.md) | Send an email using Exchange Web Services |
| [Get Exchange Email List](activities/GetExchangeMailMessages.md) | Retrieve email messages from Exchange |
| [Create Draft](activities/CreateDraft.md) | Create a draft email in Exchange |
| [Delete Exchange Email](activities/DeleteMail.md) | Delete an email from Exchange |
| [Move Exchange Email](activities/MoveMessageToFolder.md) | Move an email to a folder in Exchange |
| [Save Exchange Attachments](activities/SaveExchangeAttachements.md) | Save attachments from an Exchange email |

### General (Cross-platform)

| Activity | Description |
|----------|-------------|
| [Save Email Message](activities/SaveMail.md) | Save an email message to an .eml file |
| [Save Email Attachments](activities/SaveMailAttachments.md) | Save attachments from an email to disk |
| [Get Mail Message from File](activities/GetMailMessageFromFile.md) | Parse a .eml file into a [`MailMessage`](activities/types/MailMessage.md) object |

## Type Reference

| Type | Description |
|------|-------------|
| [`MailMessage`](activities/types/MailMessage.md) | Standard .NET mail message — From, To, Subject, Body, Attachments. Output of Get* activities, input to Send/Delete/Move. |
| [`UiPathMailMessage`](activities/types/UiPathMailMessage.md) | Cross-platform mail message variant for portable workflows |
| [`MailEventInfo`](activities/types/MailEventInfo.md) | Trigger event payload containing the received email |

## Filter Reference

| Filter | Description |
|--------|-------------|
| [`MailFilterArgument`](activities/filtering/MailFilterArgument.md) | Structured filter collection for ForEachEmail — criteria include From, To, Subject, Date, Importance |
| [`TriggerMailFilterCollection`](activities/filtering/TriggerMailFilterCollection.md) | Filter collection for IMAP trigger activities |
