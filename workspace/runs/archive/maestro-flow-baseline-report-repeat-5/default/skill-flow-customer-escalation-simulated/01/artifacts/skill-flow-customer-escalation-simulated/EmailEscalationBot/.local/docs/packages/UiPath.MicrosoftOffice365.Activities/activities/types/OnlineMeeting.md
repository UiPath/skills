# OnlineMeeting

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Contains online meeting information for a calendar event, including join URL and dial-in numbers. Used in [O365EventItem](O365EventItem.md).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `JoinUrl` | `String` | The URL to join the online meeting. |
| `ConferenceId` | `String` | The conference ID for the online meeting. |
| `TollNumber` | `String` | The toll number for dial-in. |
| `TollFreeNumber` | `String` | The toll-free number for dial-in. |
| `TollFreeNumbers` | `IEnumerable<String>` | Additional toll-free numbers. |
| `QuickDial` | `String` | Quick dial-in information. |

## Cross-References

- Used by [O365EventItem](O365EventItem.md) (`OnlineMeeting` property)
