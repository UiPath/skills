# MailFilterCollection

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Mail.Filters`
**Inherits:** `BaseFilterCollection<MailFilterElement, MailFilterLogicalOperator>`

Filters Outlook email messages by subject, sender, recipient, date, type, and other criteria. Used by activities like GetEmailListConnections and ForEachEmailConnections.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `MailFilterLogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<MailFilterElement>` | Zero or more filter conditions to apply. |

## MailFilterElement

Each filter element specifies a field, operator, and value.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `MailFilterField` | The field to filter on. |
| `StringOperator` | `MailStringFilterOperator` | Operator for string fields (e.g., `Equals`, `StartsWith`, `Contains`). |
| `DateOperator` | `MailDateFilterOperator` | Operator for date fields. |
| `TypeOperator` | `MailTypeFilterOperator` | Operator for type fields. |
| `TypeValue` | `MailType` | The email type value to filter by. |
| `InStringValue` | `InArgument<String>` | String value for string-based filters. |
| `DateValue` | `InArgument<DateTime>` | Date value for date-based filters. |

## MailFilterField Enum

| Value | Description |
|-------|-------------|
| `From` | Filter by sender address. |
| `To` | Filter by To recipient. |
| `Date` | Filter by date received/sent. |
| `CC` | Filter by CC recipient. |
| `BCC` | Filter by BCC recipient. |
| `Subject` | Filter by email subject. |
| `Body` | Filter by email body content. |
| `Categories` | Filter by email categories. |
| `Recipients` | Filter by any recipient (To, CC, BCC). |
| `Attachment` | Filter by attachment name. |
| `Type` | Filter by email type (Email, Im, Meeting, Voicemail, RssFeed, Task). |

## Cross-References

- Filters results of type [Office365Message](../types/Office365Message.md)
- Used alongside [MailFolderArgument](../components/MailFolderArgument.md) and [MailboxArgument](../components/MailboxArgument.md)
- For filtering email attachments by filename, see [FilenameFilterCollection](FilenameFilterCollection.md)
