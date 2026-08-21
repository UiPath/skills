# FilenameFilterCollection

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Mail.Filters`
**Inherits:** `BaseFilterCollection<FilenameFilterElement, MailFilterLogicalOperator>`

Filters email attachments by filename and extension. Used by mail activities that process attachments, such as DownloadEmailAttachments.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `MailFilterLogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<FilenameFilterElement>` | Zero or more filter conditions to apply. |

## FilenameFilterElement

Each filter element specifies a field, operator, and value.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `FilenameFilterField` | The field to filter on (filename or extension). |
| `StringOperator` | `FilenameStringFilterOperator` | The comparison operator (e.g., `Equals`, `StartsWith`, `Contains`). |
| `Value` | `InArgument<String>` | The string value to compare against. |

## FilenameFilterField Enum

| Value | Description |
|-------|-------------|
| `Filename` | Filter by the attachment filename. |
| `Filetype` | Filter by the attachment file type/extension. |

## Cross-References

- Filters attachments of [Office365Message](../types/Office365Message.md) items
- Used alongside [MailFilterCollection](MailFilterCollection.md) for email-level filtering
- Related to [MailFolderArgument](../components/MailFolderArgument.md) and [MailboxArgument](../components/MailboxArgument.md)
