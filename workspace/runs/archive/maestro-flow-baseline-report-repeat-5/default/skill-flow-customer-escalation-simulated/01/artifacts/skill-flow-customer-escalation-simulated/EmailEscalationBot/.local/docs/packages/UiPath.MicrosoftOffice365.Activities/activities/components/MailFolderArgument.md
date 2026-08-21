# MailFolderArgument

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Mail.Models`

A composition argument object used by Outlook mail activities to specify a mail folder. The `SelectionMode` property determines which sub-properties are required.

## InputMode -- SelectionMode (Mail.Enums.ItemSelectionMode)

| Mode | Description | Required Properties | AI-XAML Suitable |
|------|-------------|--------------------|--------------------|
| `Browse` | Select a mail folder via the Studio designer browser widget. | `BrowserFolder`, `BrowserFolderId` | **Not suitable for AI-generated XAML** |
| `EnterPath` | Specify a mail folder by name or path. | `ManualEntryFolder` | Yes |

## Properties

### Core

| Property | Type | Description |
|----------|------|-------------|
| `SelectionMode` | `ItemSelectionMode` | Determines whether to use browser-based folder selection or manual path entry. |
| `ConnectionKey` | `String` | The connection identifier from when the folder was originally selected. |
| `ConnectionDescriptor` | `String` | A user-friendly label describing the connection. |

### EnterPath Mode

| Property | Type | Description |
|----------|------|-------------|
| `ManualEntryFolder` | `InArgument<String>` | The mail folder path (e.g., `Inbox`, `SentItems`, `Drafts`, or a custom folder name). An empty value means the root mail folder (search in all folders). |

### Browse Mode (designer-only)

| Property | Type | Description |
|----------|------|-------------|
| `BrowserFolderId` | `String` | The unique identifier of the mail folder selected via the browser. `[AutopilotIgnored]` |
| `BrowserFolder` | `InArgument<String>` | The display name of the selected mail folder. |

### Other

| Property | Type | Description |
|----------|------|-------------|
| `Backup` | `BackupSlot<ItemSelectionMode>` | Stores the previous SelectionMode for undo. |

## XAML Examples

> `Backup` is always present in Studio-generated XAML; include it to match Studio's output. `usau:` maps to `xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"`. `mailenums:` maps to `xmlns:mailenums="clr-namespace:UiPath.MicrosoftOffice365.Activities.Mail.Enums;assembly=UiPath.MicrosoftOffice365.Activities"`.

### EnterPath Mode
```xml
<mailmodels:MailFolderArgument SelectionMode="EnterPath">
    <mailmodels:MailFolderArgument.Backup>
        <usau:BackupSlot x:TypeArguments="mailenums:ItemSelectionMode" StoredValue="EnterPath">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="mailenums:ItemSelectionMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
    </mailmodels:MailFolderArgument.Backup>
    <mailmodels:MailFolderArgument.ManualEntryFolder>
        <InArgument x:TypeArguments="x:String">["Inbox"]</InArgument>
    </mailmodels:MailFolderArgument.ManualEntryFolder>
</mailmodels:MailFolderArgument>
```

## Variant: TriggerMailFolderArgument

A simplified version used by mail triggers. Properties are stored directly (not as `InArgument<T>`).

| Property | Type | Description |
|----------|------|-------------|
| `FolderId` | `String` | The unique identifier of the selected mail folder (derived from `BrowserFolderId`). |
| `FolderName` | `String` | The display name of the selected mail folder. |
| `IsBound` | `Boolean` | Whether the folder value is sourced from a data binding. |

## Cross-References

- Used by Outlook mail activities (GetEmailListConnections, ForEachEmailConnections, MoveEmailConnections, etc.)
- Resolves to folders containing [Office365Message](../types/Office365Message.md) items
- Related to [O365MailFolder](../types/O365MailFolder.md) type
- Emails can be filtered by [MailFilterCollection](../filtering/MailFilterCollection.md)
- Shared mailbox access uses [MailboxArgument](MailboxArgument.md)
