# EventBody

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Represents the body content of a calendar event. Used in [O365EventItem](O365EventItem.md).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `BodyType` | `String` | The content type of the body (`html` or `text`). |
| `Body` | `String` | The body content. |

## Cross-References

- Used by [O365EventItem](O365EventItem.md) (`Body` property)
