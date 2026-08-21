# O365CalendarItem

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Represents a Microsoft 365 calendar. Returned by GetCalendarsConnections and used with [CalendarArgument](../components/CalendarArgument.md) in `UseExisting` mode.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `String` | The unique identifier of the calendar. A null or empty ID represents the default calendar. |
| `CalendarGroupId` | `String` | The ID of the calendar group, if any. |
| `GroupId` | `String` | The Microsoft 365 group ID, if this is a group calendar. |
| `Account` | `String` | The email address of the user who owns the calendar. |
| `Name` | `String` | Display name of the calendar. |
| `Color` | `String` | The calendar color name. |
| `HexColor` | `String` | The calendar color as a hex RGB value (e.g., `#FF0000`). Empty if never explicitly set. |
| `IsDefault` | `Boolean?` | `true` if this is the default calendar. |
| `CanShare` | `Boolean?` | `true` if the calendar can be shared. |
| `CanEdit` | `Boolean?` | `true` if the calendar can be edited. |
| `CanViewPrivateItems` | `Boolean?` | `true` if private items can be viewed. |
| `IsRemovable` | `Boolean?` | `true` if the calendar can be removed. |
| `IsTallyingResponses` | `Boolean?` | `true` if the calendar is tallying responses. |
| `AllowedOnlineMeetingProviders` | `IEnumerable<String>` | List of allowed online meeting providers. |
| `DefaultOnlineMeetingProvider` | `String` | The default online meeting provider. |
| `Owner` | `User` | The calendar owner (Name and Address). |

## Cross-References

- Returned by GetCalendarsConnections
- Passed into [CalendarArgument](../components/CalendarArgument.md) via `Existing` property in `UseExisting` mode
- Contains events of type [O365EventItem](O365EventItem.md)
