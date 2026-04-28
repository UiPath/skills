# Mail — Portable API (IMAP / POP3 / SMTP)

Cross-platform mail protocols using `mail.Imap(...)`, `mail.Pop3(...)`, and `mail.Smtp(...)`. For general info see [mail.md](mail.md).

---

## Connection Options

All portable protocols require a server and port, and support connection configuration via `MailConnectionOptions`.

### MailConnectionOptions

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Server` | `string` | — | `.WithServer(string)` | Mail server hostname |
| `Port` | `int` | — | `.WithPort(int)` | Server port |
| `Email` | `string` | `null` | `.WithEmail(string)` | Email address for authentication |
| `Password` | `string` | `null` | `.WithPassword(string)` | Password for authentication |
| `UseOAuth` | `bool` | `false` | `.WithOAuth(bool)` | Use OAuth authentication |
| `IgnoreCRL` | `bool` | `false` | `.WithIgnoreCRL(bool)` | Ignore certificate revocation list |
| `SecureConnection` | `SecureSocketEncryption` | `Auto` | `.WithSecureConnection(SecureSocketEncryption)` | Encryption mode |
| `Timeout` | `int` | `30000` | `.WithTimeout(int)` | Connection timeout in milliseconds |

Constructor: `new MailConnectionOptions(string server, int port)`

### ImapConnectionOptions (extends MailConnectionOptions)

Additional properties for IMAP:

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `ClientName` | `string` | `null` | `.WithClientName(string)` | IMAP client name |
| `ClientVersion` | `string` | `null` | `.WithClientVersion(string)` | IMAP client version |

Convenience builder: `.WithClient(string name, string version)` — sets both at once.

Constructor: `new ImapConnectionOptions(string server, int port)`

### SecureSocketEncryption Values

| Value | Description |
|---|---|
| `None` | No encryption |
| `Auto` | Automatically determine encryption |
| `SslOnConnect` | Use SSL/TLS immediately on connect |
| `StartTls` | Use STARTTLS upgrade (required) |
| `StartTlsWhenAvailable` | Use STARTTLS if available |

---

## IMAP — Receive Messages

### Getting the IMAP Service

```csharp
// Simple — server and port
var imap = mail.Imap("imap.example.com", 993);

// With connection options
var imap = mail.Imap(
    new ImapConnectionOptions("imap.example.com", 993)
        .WithEmail("user@example.com")
        .WithPassword("password")
        .WithSecureConnection(SecureSocketEncryption.SslOnConnect)
);
```

### `GetMessages()`

Retrieves messages with default options (top 30).

```csharp
var messages = mail.Imap("imap.example.com", 993).GetMessages();
```

### `GetMessages(GetMailOptions options)`

Retrieves messages with basic options.

```csharp
var messages = mail.Imap("imap.example.com", 993)
    .GetMessages(new GetMailOptions().WithTop(50));
```

### `GetMessages(GetImapMailOptions options)`

Retrieves messages with full IMAP-specific options.

```csharp
var imapOptions = new ImapConnectionOptions("imap.example.com", 993)
    .WithEmail("user@example.com")
    .WithPassword("password")
    .WithSecureConnection(SecureSocketEncryption.SslOnConnect);

var messages = mail.Imap(imapOptions).GetMessages(
    new GetImapMailOptions()
        .WithFolder("Inbox")
        .WithOnlyUnreadMessages(true)
        .WithMarkAsRead(true)
        .WithTop(20)
        .WithOrder(EOrderByDate.NewestFirst)
        .WithFilterExpression("SUBJECT \"Invoice\"")
);
```

**Async variant:** `GetMessagesAsync(GetImapMailOptions options, CancellationToken token)`

#### GetImapMailOptions Properties

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Top` | `int` | `30` | `.WithTop(int)` | Maximum number of messages to retrieve |
| `DeleteMessages` | `bool` | `false` | `.WithDeleteMessages(bool)` | Delete messages after retrieval |
| `MarkAsRead` | `bool` | `false` | `.WithMarkAsRead(bool)` | Mark messages as read after retrieval |
| `OnlyUnreadMessages` | `bool` | `true` | `.WithOnlyUnreadMessages(bool)` | Only retrieve unread messages |
| `MailFolder` | `string` | `"Inbox"` | `.WithFolder(string)` | IMAP folder to read from |
| `FilterExpression` | `string` | `null` | `.WithFilterExpression(string)` | IMAP SEARCH filter expression |
| `FilterExpressionCharacterSet` | `string` | `null` | `.WithFilterExpressionCharacterSet(string)` | Character set for filter expression |
| `OrderByDate` | `EOrderByDate` | `NewestFirst` | `.WithOrder(EOrderByDate)` | Sort order by date |

---

## POP3 — Receive Messages

### Getting the POP3 Service

```csharp
// Simple — server and port
var pop3 = mail.Pop3("pop.example.com", 995);

// With connection options
var pop3 = mail.Pop3(
    new MailConnectionOptions("pop.example.com", 995)
        .WithEmail("user@example.com")
        .WithPassword("password")
        .WithSecureConnection(SecureSocketEncryption.SslOnConnect)
);
```

### `GetMessages()`

Retrieves messages with default options (top 30).

```csharp
var messages = mail.Pop3("pop.example.com", 995).GetMessages();
```

### `GetMessages(GetPop3MailOptions options)`

Retrieves messages with POP3-specific options.

```csharp
var messages = mail.Pop3(
    new MailConnectionOptions("pop.example.com", 995)
        .WithEmail("user@example.com")
        .WithPassword("password")
        .WithSecureConnection(SecureSocketEncryption.SslOnConnect)
).GetMessages(
    new GetPop3MailOptions()
        .WithTop(10)
        .WithDeleteMessages(false)
);
```

**Async variant:** `GetMessagesAsync(GetPop3MailOptions options, CancellationToken token)`

#### GetPop3MailOptions Properties

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Top` | `int` | `30` | `.WithTop(int)` | Maximum number of messages to retrieve |
| `DeleteMessages` | `bool` | `false` | `.WithDeleteMessages(bool)` | Delete messages from server after retrieval |

---

## SMTP — Send Messages

### Getting the SMTP Service

```csharp
// Simple — server and port
var smtp = mail.Smtp("smtp.example.com", 587);

// With connection options
var smtp = mail.Smtp(
    new MailConnectionOptions("smtp.example.com", 587)
        .WithEmail("user@example.com")
        .WithPassword("password")
        .WithSecureConnection(SecureSocketEncryption.StartTls)
);
```

### `SendMail(string to, string subject, string body)`

Sends a simple email.

```csharp
mail.Smtp(
    new MailConnectionOptions("smtp.example.com", 587)
        .WithEmail("sender@example.com")
        .WithPassword("password")
        .WithSecureConnection(SecureSocketEncryption.StartTls)
).SendMail("recipient@example.com", "Hello", "Message body");
```

### `SendMail(SendMailOptions options)`

Sends email with base options.

```csharp
smtp.SendMail(
    new SendMailOptions()
        .WithTo(new List<string> { "recipient@example.com" })
        .WithSubject("Report")
        .WithBody("<h1>Monthly Report</h1>")
        .WithHtmlBody(true)
        .WithAttachments(new List<string> { @"C:\report.pdf" })
);
```

### `SendMail(SendSmtpMailOptions options)`

Sends email with SMTP-specific options.

```csharp
smtp.SendMail(
    new SendSmtpMailOptions()
        .WithTo(new List<string> { "recipient@example.com" })
        .WithCc(new List<string> { "cc@example.com" })
        .WithSubject("Report")
        .WithBody("Please review.")
        .WithSender("Automation Bot", "bot@example.com")
);
```

**Async variant:** `SendMailAsync(SendSmtpMailOptions options, CancellationToken token)`

#### SendSmtpMailOptions Properties (extends SendMailOptions)

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `SenderMail` | `string` | `null` | `.WithSenderMail(string)` | Sender email address |
| `SenderName` | `string` | `null` | `.WithSenderName(string)` | Sender display name |

Convenience builder: `.WithSender(string name, string mail)` — sets both at once.

**Static factory:** `SendSmtpMailOptions.FromMailOptions(SendMailOptions options)` — converts a `SendMailOptions` to `SendSmtpMailOptions`.

For base `SendMailOptions` properties (To, Cc, Bcc, Subject, Body, etc.), see [windows-api.md](windows-api.md#sendmailoptions-properties-base).

---

## Base Option Classes

### GetMailOptions (base for all Get options)

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Top` | `int` | `30` | `.WithTop(int)` | Maximum number of messages to retrieve |

### SendMailOptions (base for all Send options)

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `To` | `List<string>` | empty list | `.WithTo(List<string>)` | Recipient email addresses |
| `Cc` | `List<string>` | empty list | `.WithCc(List<string>)` | CC email addresses |
| `Bcc` | `List<string>` | empty list | `.WithBcc(List<string>)` | BCC email addresses |
| `Subject` | `string` | `null` | `.WithSubject(string)` | Email subject |
| `Body` | `string` | `null` | `.WithBody(string)` | Email body |
| `IsBodyHtml` | `bool` | `false` | `.WithHtmlBody(bool)` | Whether body is HTML |
| `ReplyTo` | `List<string>` | empty list | `.WithReplyTo(List<string>)` | Reply-to addresses |
| `Attachments` | `List<string>` | empty list | `.WithAttachments(List<string>)` | File paths to attach |
| `ForwardedMessage` | `MailMessage` | `null` | `.WithForwardedMessage(MailMessage)` | Message to forward |

---

## Interface Hierarchy

```
IMailService
├── .Outlook()  → IOutlookMailService (IMailReceiverService + IMailSenderService + management)
├── .Imap(...)  → IImapMailService (IMailReceiverService)
├── .Pop3(...)  → IPop3MailService (IMailReceiverService)
└── .Smtp(...)  → ISmtpMailService (IMailSenderService)
```
