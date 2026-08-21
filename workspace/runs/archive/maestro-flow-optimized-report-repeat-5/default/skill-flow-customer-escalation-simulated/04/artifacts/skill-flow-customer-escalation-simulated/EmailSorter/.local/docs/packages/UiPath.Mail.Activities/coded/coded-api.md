# Mail Coded Workflow API

**Package:** `UiPath.Mail.Activities`
**Service accessor:** `mail`
**Service interface:** `IMailService`
**Auto-imported namespace:** `UiPath.Mail.Activities.Api`

## Overview

The `mail` service provides protocol-specific sub-services for sending and receiving email in coded workflows. Call `mail.Smtp(...)`, `mail.Imap(...)`, or `mail.Pop3(...)` to get a protocol-specific service, then use that service's methods to send or retrieve messages.

**API pattern:** Factory methods → protocol sub-service → operations

```csharp
// Get messages via IMAP
var imapService = mail.Imap("imap.example.com", 993);
var messages = imapService.GetMessages(new GetImapMailOptions { Top = 10 });

// Send via SMTP
var smtpService = mail.Smtp("smtp.example.com", 587);
smtpService.SendMail("recipient@example.com", "Subject", "Body");
```

---

## IMailService Methods

The root `mail` accessor exposes factory methods that return protocol-specific sub-services.

### `IPop3MailService Pop3(string server, int port = 110)`

Creates a service for retrieving POP3 email messages.

**Parameters:**
- `server` (`string`) — The email server host
- `port` (`int`, default: `110`) — The port for POP3 connection

**Returns:** `IPop3MailService`

### `IPop3MailService Pop3(MailConnectionOptions options)`

Creates a POP3 service using a connection options object.

**Parameters:**
- `options` ([`MailConnectionOptions`](#mailconnectionoptions)) — Connection configuration including server, port, credentials, SSL

**Returns:** `IPop3MailService`

### `ISmtpMailService Smtp(string server, int port = 25)`

Creates a service for sending email via SMTP.

**Parameters:**
- `server` (`string`) — The email server host
- `port` (`int`, default: `25`) — The port for SMTP connection

**Returns:** `ISmtpMailService`

### `ISmtpMailService Smtp(MailConnectionOptions options)`

Creates an SMTP service using a connection options object.

**Parameters:**
- `options` ([`MailConnectionOptions`](#mailconnectionoptions)) — Connection configuration

**Returns:** `ISmtpMailService`

### `IImapMailService Imap(string server, int port = 143)`

Creates a service for retrieving IMAP email messages.

**Parameters:**
- `server` (`string`) — The email server host
- `port` (`int`, default: `143`) — The port for IMAP connection

**Returns:** `IImapMailService`

### `IImapMailService Imap(ImapConnectionOptions options)`

Creates an IMAP service using connection options with IMAP-specific settings.

**Parameters:**
- `options` ([`ImapConnectionOptions`](#imapconnectionoptions)) — Connection configuration with optional client name/version

**Returns:** `IImapMailService`

---

## Sub-Service Interfaces

### IPop3MailService

Extends `IMailReceiverService`. Retrieves email messages from a POP3 server.

| Method | Returns | Description |
|--------|---------|-------------|
| `GetMessages()` | `IReadOnlyCollection<MailMessage>` | Retrieve messages with default options (top 30) |
| `GetMessages(GetMailOptions options)` | `IReadOnlyCollection<MailMessage>` | Retrieve messages with base options |
| `GetMessages(GetPop3MailOptions options)` | `IReadOnlyCollection<MailMessage>` | Retrieve messages with POP3-specific options |
| `GetMessagesAsync(CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async variant with defaults |
| `GetMessagesAsync(GetMailOptions options, CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async with base options |
| `GetMessagesAsync(GetPop3MailOptions options, CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async with POP3 options |

### ISmtpMailService

Extends `IMailSenderService`. Sends email messages using the SMTP protocol.

| Method | Returns | Description |
|--------|---------|-------------|
| `SendMail(string to, string subject, string body)` | `void` | Send a simple email |
| `SendMail(SendMailOptions options)` | `void` | Send with base options |
| `SendMail(SendSmtpMailOptions options)` | `void` | Send with SMTP-specific options |
| `SendMailAsync(string to, string subject, string body, CancellationToken token)` | `Task` | Async simple send |
| `SendMailAsync(SendMailOptions options, CancellationToken token)` | `Task` | Async with base options |
| `SendMailAsync(SendSmtpMailOptions options, CancellationToken token)` | `Task` | Async with SMTP options |

### IImapMailService

Extends `IMailReceiverService`. Retrieves, deletes, and moves email messages via IMAP.

| Method | Returns | Description |
|--------|---------|-------------|
| `GetMessages()` | `IReadOnlyCollection<MailMessage>` | Retrieve messages with default options |
| `GetMessages(GetMailOptions options)` | `IReadOnlyCollection<MailMessage>` | Retrieve with base options |
| `GetMessages(GetImapMailOptions options)` | `IReadOnlyCollection<MailMessage>` | Retrieve with IMAP-specific options |
| `GetMessagesAsync(CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async with defaults |
| `GetMessagesAsync(GetMailOptions options, CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async with base options |
| `GetMessagesAsync(GetImapMailOptions options, CancellationToken token)` | `Task<IReadOnlyCollection<MailMessage>>` | Async with IMAP options |
| `DeleteMail(MailMessage message, string fromFolder = "")` | `void` | Delete a message from a folder (defaults to Inbox) |
| `DeleteMailAsync(MailMessage message, string fromFolder = "", CancellationToken token = default)` | `Task` | Async delete |
| `MoveMail(MailMessage message, string destinationFolder, string fromFolder = "")` | `void` | Move a message to another folder |
| `MoveMailAsync(MailMessage message, string destinationFolder, string fromFolder = "", CancellationToken token = default)` | `Task` | Async move |

---

## Options Classes

### MailConnectionOptions

Connection configuration for SMTP, IMAP, and POP3 services. Constructor requires `server` and `port`.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Server` | `string` | (required) | The email server host |
| `Port` | `int` | (required) | The port for the connection |
| `Email` | `string` | `null` | The email account for authentication |
| `Password` | `string` | `null` | The account password. If `UseOAuth` is `true`, this must be an OAuth2 access token |
| `UseOAuth` | `bool` | `false` | Whether to use an OAuth2 access token instead of a password |
| `IgnoreCRL` | `bool` | `false` | Whether to ignore Certificate Revocation List validation |
| `SecureConnection` | [`SecureSocketEncryption`](#enum-reference) | `Auto` | The SSL/TLS encryption mode |
| `Timeout` | `int` | `30000` | Connection timeout in milliseconds |

### ImapConnectionOptions

Extends [`MailConnectionOptions`](#mailconnectionoptions) with IMAP-specific settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| *(all from MailConnectionOptions)* | | | |
| `ClientName` | `string` | `null` | The IMAP client implementation name |
| `ClientVersion` | `string` | `null` | The IMAP client implementation version |

### GetMailOptions

Base options for retrieving email messages.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `Top` | `int` | `30` | The number of messages to retrieve |

### GetPop3MailOptions

Extends [`GetMailOptions`](#getmailoptions) with POP3-specific settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| *(all from GetMailOptions)* | | | |
| `DeleteMessages` | `bool` | `false` | Whether to mark retrieved messages for deletion on the server |

### GetImapMailOptions

Extends [`GetMailOptions`](#getmailoptions) with IMAP-specific settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| *(all from GetMailOptions)* | | | |
| `DeleteMessages` | `bool` | `false` | Whether to mark retrieved messages for deletion |
| `MarkAsRead` | `bool` | `false` | Whether to mark retrieved messages as read |
| `OnlyUnreadMessages` | `bool` | `true` | Whether to retrieve only unread messages |
| `MailFolder` | `string` | `"Inbox"` | The mail folder to retrieve from |
| `FilterExpression` | `string` | `null` | IMAP search filter expression |
| `FilterExpressionCharacterSet` | `string` | `null` | MIME character set for the filter expression |
| `OrderByDate` | [`EOrderByDate`](#enum-reference) | `NewestFirst` | Message ordering by date |

### SendMailOptions

Base options for sending email messages.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `To` | `List<string>` | `[]` | The primary recipients |
| `Cc` | `List<string>` | `[]` | The CC recipients |
| `Bcc` | `List<string>` | `[]` | The BCC recipients |
| `Subject` | `string` | `null` | The email subject |
| `Body` | `string` | `null` | The email body |
| `IsBodyHtml` | `bool` | `false` | Whether the body is HTML |
| `ReplyTo` | `List<string>` | `[]` | Reply-to addresses |
| `Attachments` | `List<string>` | `[]` | File paths to attach |
| `ForwardedMessage` | `MailMessage` | `null` | A message to forward |

### SendSmtpMailOptions

Extends [`SendMailOptions`](#sendmailoptions) with SMTP-specific settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| *(all from SendMailOptions)* | | | |
| `SenderMail` | `string` | `null` | The sender email address |
| `SenderName` | `string` | `null` | The sender display name |

### SendOutlookMailOptions

Extends [`SendMailOptions`](#sendmailoptions) with Outlook-specific settings.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| *(all from SendMailOptions)* | | | |
| `Account` | `string` | `null` | The Outlook account to send from |
| `SentOnBehalfOfName` | `string` | `null` | The display name of the sender |
| `Importance` | `MailImportance` | `Normal` | The email importance level |
| `IsDraft` | `bool` | `false` | Whether to save as draft instead of sending |
| `Sensitivity` | `MailSensitivity` | `Normal` | The email sensitivity level |

---

## Enum Reference

| Enum | Values |
|------|--------|
| `SecureSocketEncryption` | `None`, `Auto`, `SslOnConnect`, `StartTls`, `StartTlsWhenAvailable` |
| `EOrderByDate` | `NewestFirst`, `OldestFirst` |
| `MailImportance` | `Low`, `Normal`, `High` |
| `MailSensitivity` | `Normal`, `Personal`, `Private`, `Confidential` |

---

## Common Patterns

### Retrieve emails via IMAP

```csharp
[Workflow]
public void Execute()
{
    var imapService = mail.Imap(new ImapConnectionOptions("imap.gmail.com", 993)
    {
        Email = "user@gmail.com",
        Password = "app-password",
        SecureConnection = SecureSocketEncryption.SslOnConnect
    });

    var messages = imapService.GetMessages(new GetImapMailOptions
    {
        Top = 10,
        OnlyUnreadMessages = true,
        MailFolder = "Inbox",
        OrderByDate = EOrderByDate.NewestFirst
    });

    foreach (var msg in messages)
    {
        Log($"From: {msg.From}, Subject: {msg.Subject}");
    }
}
```

### Send email via SMTP

```csharp
[Workflow]
public void Execute()
{
    var smtpService = mail.Smtp(new MailConnectionOptions("smtp.gmail.com", 587)
    {
        Email = "user@gmail.com",
        Password = "app-password",
        SecureConnection = SecureSocketEncryption.StartTls
    });

    smtpService.SendMail(new SendSmtpMailOptions
    {
        To = new List<string> { "recipient@example.com" },
        Subject = "Monthly Report",
        Body = "<h1>Report</h1><p>See attached.</p>",
        IsBodyHtml = true,
        Attachments = new List<string> { @"C:\Reports\report.pdf" },
        SenderMail = "user@gmail.com",
        SenderName = "Reports Bot"
    });
}
```

### Quick send (simple overload)

```csharp
[Workflow]
public void Execute()
{
    var smtpService = mail.Smtp("smtp.company.com", 25);
    smtpService.SendMail("manager@company.com", "Task Complete", "The automation has finished.");
}
```

### Retrieve and delete POP3 messages

```csharp
[Workflow]
public void Execute()
{
    var pop3Service = mail.Pop3("pop.example.com", 995);

    var messages = pop3Service.GetMessages(new GetPop3MailOptions
    {
        Top = 5,
        DeleteMessages = true
    });

    Log($"Retrieved {messages.Count} messages (marked for deletion on server)");
}
```

### Move IMAP messages to a folder

```csharp
[Workflow]
public void Execute()
{
    var imapService = mail.Imap(new ImapConnectionOptions("imap.example.com", 993)
    {
        Email = "user@example.com",
        Password = "password",
        SecureConnection = SecureSocketEncryption.SslOnConnect
    });

    var messages = imapService.GetMessages(new GetImapMailOptions
    {
        Top = 50,
        OnlyUnreadMessages = true,
        FilterExpression = "SUBJECT \"Invoice\""
    });

    foreach (var msg in messages)
    {
        imapService.MoveMail(msg, "Invoices", "Inbox");
    }

    Log($"Moved {messages.Count} invoice emails to Invoices folder");
}
```
