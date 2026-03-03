# Mail Activities API Reference

Reference for the `mail` service from `UiPath.Mail.Activities` package.

**Required package:** `"UiPath.Mail.Activities": "[2.5.10]"`

**Auto-imported namespaces:** `UiPath.Mail.Activities.Api`

**Service accessor:** `mail` (type `IMailService`)

---

## Overview

The Mail API provides coded workflow access to send, receive, and manage email messages via multiple protocols. The main entry point is `IMailService`, accessed via the `mail` service accessor.

### Supported Protocols

| Protocol | Method | Receives | Sends | Description |
|---|---|---|---|---|
| **Outlook** | `mail.Outlook()` | Yes | Yes | Full Outlook integration (Windows only). Supports read, send, delete, move, save, mark, categorize. |
| **IMAP** | `mail.Imap(server, port)` | Yes | No | Receive mail via IMAP. Supports folders, filters, mark as read, ordering. |
| **POP3** | `mail.Pop3(server, port)` | Yes | No | Receive mail via POP3. Simpler protocol, supports delete after get. |
| **SMTP** | `mail.Smtp(server, port)` | No | Yes | Send mail via SMTP. Supports sender configuration. |

### Workflow Pattern

1. Select a protocol via `mail.Outlook()`, `mail.Imap(...)`, `mail.Smtp(...)`, or `mail.Pop3(...)`.
2. Call `GetMessages(...)` to receive or `SendMail(...)` to send.
3. For Outlook, use additional management methods (MoveMail, DeleteMail, MarkRead, etc.).

### Options Pattern

All operations accept an optional `*Options` parameter for advanced configuration. All option classes use the fluent builder pattern:

```csharp
var options = new GetOutlookMailOptions()
    .WithFolder("Inbox")
    .WithOnlyUnreadMessages(true)
    .WithTop(10)
    .WithOrder(EOrderByDate.NewestFirst);
```

See [windows-api.md](windows-api.md) for the full Outlook API reference and [portable-api.md](portable-api.md) for IMAP/POP3/SMTP protocols.

For full coded workflow examples, see [examples.md](examples.md).

---

## Key Enum Reference Summary

| Enum | Values | Description |
|---|---|---|
| `EOrderByDate` | `NewestFirst`, `OldestFirst` | Sort order for retrieved messages |
| `SecureSocketEncryption` | `None`, `Auto`, `SslOnConnect`, `StartTls`, `StartTlsWhenAvailable` | Connection encryption mode |
| `MailImportance` | `Low`, `Normal`, `High` | Email importance level |
| `MailSensitivity` | `Normal`, `Personal`, `Private`, `Confidential` | Email sensitivity level |
| `ESaveMessageAsType` | `TextOnly`, `OutlookTemplate`, `Html`, `Mht`, `OutlookMessageFormat`, `OutlookMessageFormatUnicode` | Format for saving Outlook messages |
