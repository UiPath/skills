# O365MailFolder

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Mail.Models`

Represents an Outlook mail folder. Returned by GetEmailFoldersListConnections.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `String` | The unique identifier of the mail folder. |
| `Account` | `String` | The email address of the user who owns the folder. |
| `Name` | `String` | The display name of the mail folder. |
| `ParentFolderId` | `String` | The ID of the parent folder. |
| `FullPath` | `String` | The full path to the mail folder. |
| `IsHidden` | `Boolean?` | `true` if the folder is hidden. |
| `ChildFolderCount` | `Int32?` | The number of immediate child folders. |
| `TotalItemCount` | `Int32?` | The total number of items in the folder. |
| `UnreadItemCount` | `Int32?` | The number of unread items in the folder. |

## Cross-References

- Returned by GetEmailFoldersListConnections
- Mail folder selection uses [MailFolderArgument](../components/MailFolderArgument.md)
