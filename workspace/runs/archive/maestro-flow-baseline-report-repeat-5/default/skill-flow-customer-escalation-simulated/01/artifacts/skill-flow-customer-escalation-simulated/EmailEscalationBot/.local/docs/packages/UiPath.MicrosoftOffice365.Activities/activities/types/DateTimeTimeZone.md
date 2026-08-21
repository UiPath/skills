# DateTimeTimeZone

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Represents a date/time value paired with its timezone. Used in [O365EventItem](O365EventItem.md) for event start and end times.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `DateTime` | `DateTime` | The date and time value. |
| `TimeZone` | `String` | The timezone identifier (e.g., `Pacific Standard Time`, `UTC`). |

## Cross-References

- Used by [O365EventItem](O365EventItem.md) (`Start` and `End` properties)
