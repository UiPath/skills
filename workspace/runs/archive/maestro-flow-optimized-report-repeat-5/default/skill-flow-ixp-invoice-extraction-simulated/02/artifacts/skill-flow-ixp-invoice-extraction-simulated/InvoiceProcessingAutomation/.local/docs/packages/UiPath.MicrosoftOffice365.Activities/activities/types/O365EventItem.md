# O365EventItem

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Calendar.Models`

Represents a Microsoft 365 calendar event. Returned as output by calendar activities such as CreateEventConnections, GetEventByIdConnections, GetEventListConnections, ForEachEventConnections, ModifyEventConnections, etc.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `Id` | `String` | The unique identifier of the event. |
| `Subject` | `String` | Event title/subject. |
| `Body` | [EventBody](EventBody.md) | The event body content. |
| `BodyPreview` | `String` | A short preview of the event body. |
| `Start` | [DateTimeTimeZone](DateTimeTimeZone.md) | Start time with timezone information. |
| `StartDateTime` | `DateTime` | Start date and time (derived from `Start`). |
| `End` | [DateTimeTimeZone](DateTimeTimeZone.md) | End time with timezone information. |
| `EndDateTime` | `DateTime` | End date and time (derived from `End`). |
| `Attendees` | `IEnumerable<`[EventAttendee](EventAttendee.md)`>` | List of event attendees. |
| `AttendeesEmailList` | `IEnumerable<String>` | Email addresses of all attendees. |
| `AttendeesPlusOrganizer` | `IEnumerable<`[EventAttendee](EventAttendee.md)`>` | All attendees including the organizer. |
| `AllAttendeesEmailList` | `String` | All attendees' emails as a semicolon-separated string. |
| `AllAttendeesExceptMeEmailList` | `String` | All attendees' emails except the current user, semicolon-separated. |
| `RequiredAttendeesEmailList` | `String` | Required attendees' emails, semicolon-separated. |
| `RequiredAttendeesExceptMeEmailList` | `String` | Required attendees' emails except the current user, semicolon-separated. |
| `OptionalAttendeesEmailList` | `String` | Optional attendees' emails, semicolon-separated. |
| `ResourceAttendeesEmailList` | `String` | Resource attendees' emails, semicolon-separated. |
| `Organizer` | `User` | Event organizer (Name and Address). |
| `OrganizerName` | `String` | Display name of the organizer. |
| `OrganizerAddress` | `String` | Email address of the organizer. |
| `Account` | `String` | The email address of the user who owns the event. |
| `Location` | `String` | Event location. |
| `Categories` | `IEnumerable<String>` | Categories the event belongs to. |
| `Importance` | `String` | Event importance (`Low`, `Normal`, `High`). |
| `Sensitivity` | `String` | Event sensitivity. |
| `Type` | `String` | The type of the event (e.g., `SingleInstance`, `Occurrence`, `SeriesMaster`). |
| `IsCancelled` | `Boolean?` | `true` if the event is cancelled. |
| `IsAllDay` | `Boolean?` | `true` if this is an all-day event. |
| `IsOrganizer` | `Boolean?` | `true` if the current user is the organizer. |
| `IsOnlineMeeting` | `Boolean?` | `true` if this is an online meeting. |
| `OnlineMeetingProvider` | `String` | Online meeting provider name (e.g., `teamsForBusiness`). |
| `OnlineMeetingUrl` | `String` | URL to join the meeting. |
| `OnlineMeeting` | [OnlineMeeting](OnlineMeeting.md) | Detailed online meeting information. |
| `ShowAs` | `String` | Free/busy status (`Free`, `Tentative`, `Busy`, `Oof`, `WorkingElsewhere`, `Unknown`). |
| `Recurrence` | `String` | Recurrence pattern information. |
| `CreatedDateTime` | `DateTimeOffset?` | When the event was created. |
| `LastModifiedDateTime` | `DateTimeOffset?` | When the event was last modified. |
| `HasAttachments` | `Boolean?` | `true` if the event has attachments. |
| `WebLink` | `String` | URL to open the event in Outlook on the web. |
| `ResponseRequested` | `Boolean?` | `true` if a response has been requested by the organizer. |
| `ICalUId` | `String` | iCalendar unique identifier. |
| `SeriesMasterId` | `String` | ID of the series master event, if this is an occurrence. |
| `OccurrenceId` | `String` | Occurrence master ID. |
| `IsReminderOn` | `Boolean?` | `true` if reminders are enabled. |
| `ReminderMinutesBeforeStart` | `Int32?` | Minutes before start when the reminder fires. |
| `AllowNewTimeProposals` | `Boolean?` | `true` if attendees can propose new meeting times. |
| `IsDraft` | `Boolean?` | `true` if the event is a draft. |
| `HideAttendees` | `Boolean?` | `true` if the attendee list is hidden. |

## Cross-References

- Returned by calendar activities (CreateEventConnections, GetEventByIdConnections, GetEventListConnections, etc.)
- Contains [DateTimeTimeZone](DateTimeTimeZone.md), [EventAttendee](EventAttendee.md), [EventBody](EventBody.md), and [OnlineMeeting](OnlineMeeting.md) sub-types
- Filtered by [EventFilterCollection](../filtering/EventFilterCollection.md)
- Calendar selection is done via [CalendarArgument](../components/CalendarArgument.md)
