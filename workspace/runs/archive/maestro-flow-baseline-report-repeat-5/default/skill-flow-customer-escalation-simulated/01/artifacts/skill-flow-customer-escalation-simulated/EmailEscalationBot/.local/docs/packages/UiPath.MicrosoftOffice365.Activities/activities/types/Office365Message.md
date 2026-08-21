# Office365Message

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Models`
**Inherits:** `BaseOffice365Message` (which extends `System.Net.Mail.MailMessage`)

Represents an Outlook email message from Microsoft 365. Returned by mail activities such as GetEmailListConnections, GetEmailByIdConnections, ForEachEmailConnections, SendMailConnections, etc.

## Properties

### From Office365Message

| Property | Type | Description |
|----------|------|-------------|
| `MessageId` | `String` | The Office 365 unique ID of the message. |
| `BodyPreview` | `String` | A short preview of the email body. |
| `Flag` | `FollowupFlag` | The follow-up flag status. |
| `Importance` | `MessageImportance?` | The email importance (`Low`, `Normal`, `High`). |
| `IsRead` | `Boolean` | `true` if the email has been read. |
| `ReceivedDateTime` | `DateTime?` | When the email was received (UTC). |
| `SentDateTime` | `DateTime?` | When the email was sent (UTC). |
| `LastModifiedDateTime` | `DateTime?` | When the email was last modified (UTC). |
| `WebLink` | `String` | URL to open the email in Outlook on the web. |
| `Categories` | `IEnumerable<String>` | Categories assigned to the message. |
| `InternetMessageId` | `String` | The Internet Message-ID header. |
| `ConversationId` | `String` | The ID of the conversation thread. |
| `ParentFolderId` | `String` | The ID of the parent mail folder. |
| `Priority` | `MailPriority` | The priority of the email. |

### From BaseOffice365Message (inherited)

| Property | Type | Description |
|----------|------|-------------|
| `Subject` | `String` | The email subject line. |
| `Body` | `String` | The plain-text email body. |
| `BodyAsHtml` | `String` | The HTML version of the email body, if available. |
| `From` | `MailAddress` | The sender address (from `MailMessage`). |
| `FromDisplayName` | `String` | Display name of the sender. |
| `FromAddress` | `String` | Email address of the sender. |
| `SenderDisplayName` | `String` | Display name of the actual sender. |
| `SenderAddress` | `String` | Email address of the actual sender. |
| `To` | `MailAddressCollection` | Recipients of the email. |
| `ToAddressList` | `IEnumerable<String>` | Email addresses of To recipients. |
| `CC` | `MailAddressCollection` | CC recipients. |
| `CCAddressList` | `IEnumerable<String>` | Email addresses of CC recipients. |
| `Bcc` | `MailAddressCollection` | BCC recipients. |
| `BccAddressList` | `IEnumerable<String>` | Email addresses of BCC recipients. |
| `ReplyToList` | `MailAddressCollection` | Reply-to addresses. |
| `ReplyToAddressList` | `IEnumerable<String>` | Email addresses from the reply-to list. |
| `StandardAttachmentCount` | `Int32` | Number of standard (non-inline) attachments. |
| `StandardAttachmentNames` | `IEnumerable<String>` | Filenames of standard attachments. |
| `InlineAttachmentCount` | `Int32` | Number of inline attachments. |
| `InlineAttachmentNames` | `IEnumerable<String>` | Filenames of inline attachments. |
| `AttachmentCount` | `Int32` | Total number of attachments. |
| `AttachmentsNamesList` | `IEnumerable<String>` | Filenames of all attachments. |
| `AttachmentsInfoList` | `List<AttachmentInfoSlim>` | Detailed attachment information. |

> **Note:** The inherited `Attachments` property from `MailMessage` is obsolete and not populated. Use the **Download Email Attachments** activity instead.

## MessageImportance

A value type that maps to Microsoft Graph `Importance` enum.

| Static Property | Description |
|-----------------|-------------|
| `MessageImportance.Low` | Low importance. |
| `MessageImportance.Normal` | Normal importance. |
| `MessageImportance.High` | High importance. |

## Cross-References

- Returned by Outlook mail activities (GetEmailListConnections, ForEachEmailConnections, GetEmailByIdConnections, etc.)
- Filtered by [MailFilterCollection](../filtering/MailFilterCollection.md)
- Attachment filtering uses [FilenameFilterCollection](../filtering/FilenameFilterCollection.md)
- Mail folder selection uses [MailFolderArgument](../components/MailFolderArgument.md)
- Shared mailbox access uses [MailboxArgument](../components/MailboxArgument.md)
