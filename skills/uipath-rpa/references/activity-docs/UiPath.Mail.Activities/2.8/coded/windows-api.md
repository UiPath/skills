# Mail — Windows (Outlook) API

Full-featured Outlook mail API using `mail.Outlook()` returning `IOutlookMailService`. Windows-only. For general info see [mail.md](mail.md).

---

## Getting the Outlook Service

```csharp
var outlook = mail.Outlook();
```

Returns `IOutlookMailService` which implements both `IMailReceiverService` and `IMailSenderService`, plus Outlook-specific management methods.

---

## Receiving Messages

### `GetMessages()`

Retrieves messages with default options (top 30, unread only, newest first, from Inbox).

```csharp
var messages = mail.Outlook().GetMessages();
```

### `GetMessages(GetMailOptions options)`

Retrieves messages with basic options.

```csharp
var messages = mail.Outlook().GetMessages(new GetMailOptions().WithTop(50));
```

### `GetMessages(GetOutlookMailOptions options)`

Retrieves messages with full Outlook-specific options.

```csharp
var messages = mail.Outlook().GetMessages(
    new GetOutlookMailOptions()
        .WithFolder("Inbox")
        .WithOnlyUnreadMessages(true)
        .WithMarkAsRead(false)
        .WithTop(10)
        .WithOrder(EOrderByDate.NewestFirst)
        .WithGetAttachements(true)
        .WithAccount("my.email@company.com")
        .WithFilter("[Subject] = 'Invoice'")
);
```

**Async variant:** `GetMessagesAsync(GetOutlookMailOptions options, CancellationToken token)`

#### GetOutlookMailOptions Properties

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Top` | `int` | `30` | `.WithTop(int)` | Maximum number of messages to retrieve |
| `Account` | `string` | `null` | `.WithAccount(string)` | Outlook account to use |
| `Filter` | `string` | `null` | `.WithFilter(string)` | Outlook filter expression (DASL or JET) |
| `FilterByMessageIds` | `List<string>` | `null` | `.WithMessageIdsFilter(IEnumerable<string>)` | Filter by specific message IDs |
| `GetAttachements` | `bool` | `false` | `.WithGetAttachements(bool)` | Whether to download attachments |
| `OrderByDate` | `EOrderByDate` | `NewestFirst` | `.WithOrder(EOrderByDate)` | Sort order by date |
| `MailFolder` | `string` | `"Inbox"` | `.WithFolder(string)` | Mail folder to read from |
| `MarkAsRead` | `bool` | `false` | `.WithMarkAsRead(bool)` | Mark retrieved messages as read |
| `OnlyUnreadMessages` | `bool` | `true` | `.WithOnlyUnreadMessages(bool)` | Only retrieve unread messages |

---

## Sending Messages

### `SendMail(string to, string subject, string body)`

Sends a simple email.

```csharp
mail.Outlook().SendMail("recipient@example.com", "Hello", "Message body");
```

### `SendMail(SendMailOptions options)`

Sends email with basic options.

```csharp
mail.Outlook().SendMail(
    new SendMailOptions()
        .WithTo(new List<string> { "recipient@example.com" })
        .WithSubject("Hello")
        .WithBody("<h1>HTML Body</h1>")
        .WithHtmlBody(true)
        .WithAttachments(new List<string> { @"C:\file.pdf" })
);
```

### `SendMail(SendOutlookMailOptions options)`

Sends email with full Outlook-specific options.

```csharp
mail.Outlook().SendMail(
    new SendOutlookMailOptions()
        .WithTo(new List<string> { "recipient@example.com" })
        .WithCc(new List<string> { "cc@example.com" })
        .WithBcc(new List<string> { "bcc@example.com" })
        .WithSubject("Important Update")
        .WithBody("Please review the attached report.")
        .WithAttachments(new List<string> { @"C:\report.pdf" })
        .WithAccount("my.account@company.com")
        .WithImportance(MailImportance.High)
        .WithSensitivity(MailSensitivity.Confidential)
        .AsDraft(false)
        .OnBehalfOf("manager@company.com")
);
```

**Async variant:** `SendMailAsync(SendOutlookMailOptions options, CancellationToken token)`

#### SendMailOptions Properties (Base)

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

#### SendOutlookMailOptions Properties (extends SendMailOptions)

| Property | Type | Default | Builder Method | Description |
|---|---|---|---|---|
| `Account` | `string` | `null` | `.WithAccount(string)` | Outlook account to send from |
| `SentOnBehalfOfName` | `string` | `null` | `.OnBehalfOf(string)` | Send on behalf of another user |
| `Importance` | `MailImportance` | `Normal` | `.WithImportance(MailImportance)` | Low, Normal, or High |
| `IsDraft` | `bool` | `false` | `.AsDraft(bool)` | Save as draft instead of sending |
| `Sensitivity` | `MailSensitivity` | `Normal` | `.WithSensitivity(MailSensitivity)` | Normal, Personal, Private, or Confidential |

**Static factory:** `SendOutlookMailOptions.FromMailOptions(SendMailOptions options)` — converts a `SendMailOptions` to `SendOutlookMailOptions`.

---

## Message Management

These methods are Outlook-specific and available on `IOutlookMailService`.

### MarkRead / MarkUnread

```csharp
mail.Outlook().MarkRead(message);          // Mark as read
mail.Outlook().MarkRead(message, true);    // Mark as read (explicit)
mail.Outlook().MarkUnread(message);        // Mark as unread
```

| Parameter | Type | Description |
|---|---|---|
| `message` | `MailMessage` | The message to mark |
| `read` | `bool` | `true` = read, `false` = unread (default: `true`) |

### DeleteMail

```csharp
mail.Outlook().DeleteMail(message);
```

| Parameter | Type | Description |
|---|---|---|
| `message` | `MailMessage` | The message to delete |

### MoveMail

```csharp
mail.Outlook().MoveMail(message, "Archive");
mail.Outlook().MoveMail(message, "Archive", "my.account@company.com");
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `message` | `MailMessage` | — | The message to move |
| `destinationFolder` | `string` | — | Target folder name |
| `account` | `string` | `""` | Outlook account (empty = default) |

### SaveMail

```csharp
mail.Outlook().SaveMail(message, @"C:\SavedMails");
mail.Outlook().SaveMail(message, @"C:\SavedMails", "invoice.msg",
    ESaveMessageAsType.OutlookMessageFormatUnicode, replaceExisting: true);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `message` | `MailMessage` | — | The message to save |
| `folder` | `string` | — | Folder path to save to |
| `fileName` | `string` | `""` | File name (auto-generated if empty) |
| `saveAsType` | `ESaveMessageAsType` | `OutlookMessageFormatUnicode` | Save format |
| `replaceExisting` | `bool` | `false` | Overwrite existing file |

#### ESaveMessageAsType Values

| Value | Extension | Description |
|---|---|---|
| `TextOnly` | `.txt` | Plain text format |
| `OutlookTemplate` | `.oft` | Outlook template format |
| `Html` | `.html` / `.htm` | HTML format |
| `Mht` | `.mht` | MHTML (web archive) format |
| `OutlookMessageFormat` | `.msg` | Outlook message format |
| `OutlookMessageFormatUnicode` | `.msg` | Outlook message format (Unicode encoded) |

### SetCategories

```csharp
mail.Outlook().SetCategories(message, new List<string> { "Urgent", "Follow-up" });
```

| Parameter | Type | Description |
|---|---|---|
| `message` | `MailMessage` | The message to categorize |
| `categories` | `IReadOnlyCollection<string>` | List of category names to assign |

---

## MailMessage Type

All receive methods return `IReadOnlyCollection<MailMessage>` where `MailMessage` is `System.Net.Mail.MailMessage`.

Key properties on `MailMessage`:

| Property | Type | Description |
|---|---|---|
| `Subject` | `string` | Email subject |
| `Body` | `string` | Email body |
| `IsBodyHtml` | `bool` | Whether the body is HTML |
| `From` | `MailAddress` | Sender address |
| `To` | `MailAddressCollection` | Recipients |
| `CC` | `MailAddressCollection` | CC recipients |
| `Bcc` | `MailAddressCollection` | BCC recipients |
| `ReplyToList` | `MailAddressCollection` | Reply-to addresses |
| `Attachments` | `AttachmentCollection` | Email attachments |
| `Headers` | `NameValueCollection` | Email headers |
| `Priority` | `MailPriority` | Email priority |
