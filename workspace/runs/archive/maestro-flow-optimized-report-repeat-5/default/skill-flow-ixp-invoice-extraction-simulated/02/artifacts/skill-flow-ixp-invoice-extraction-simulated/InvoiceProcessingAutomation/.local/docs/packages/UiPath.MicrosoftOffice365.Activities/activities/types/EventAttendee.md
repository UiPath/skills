# EventAttendee

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Represents an attendee of a calendar event, including their identity, attendance type, and response status. Used in [O365EventItem](O365EventItem.md).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `User` | `User` | The attendee's identity (Name and Address). |
| `Type` | `EventAttendeeType` | The attendee type. |
| `Status` | `EventAttendeeStatus` | The attendee's response status. |

## EventAttendeeType Enum

| Value | Description |
|-------|-------------|
| `Required` | Required attendee. |
| `Optional` | Optional attendee. |
| `Resource` | Resource attendee (e.g., a conference room). |
| `Unknown` | Unknown attendee type. |

## EventAttendeeStatus Enum

| Value | Description |
|-------|-------------|
| `None` | No response status. |
| `Organizer` | The attendee is the organizer. |
| `TentativelyAccepted` | Tentatively accepted. |
| `Accepted` | Accepted. |
| `Declined` | Declined. |
| `NotResponded` | Has not responded. |

## User Type

| Property | Type | Description |
|----------|------|-------------|
| `Name` | `String` | Display name. |
| `Address` | `String` | Email address. |

## Cross-References

- Used by [O365EventItem](O365EventItem.md) (`Attendees` and `AttendeesPlusOrganizer` properties)
