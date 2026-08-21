# Modify Event

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.ModifyEventConnections`

Modifies an existing calendar event. Supports changing title, times, attendees (overwrite or add/remove), location, description, attachments, categories, importance, sensitivity, and show-as status.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Event` | Event | Input | [`InArgument<O365EventItem>`](types/O365EventItem.md) | Yes | | The calendar event to modify. |
| `Title` | Title | Input | `InArgument<string>` | No | | The updated name of the event. |
| `StartDateTime` | Start Date Time | Input | `InArgument<DateTimeOffset>` | No | | The updated start date and time. |
| `EndDateTime` | End Date Time | Input | `InArgument<DateTimeOffset>` | No | | The updated end date and time. |
| `Timezone` | Timezone | Input | `InArgument<string>` | No | | The timezone for the event. |
| `AllDayEvent` | All Day Event | Input | `InArgument<bool>` | No | | Whether the event takes all day. |
| `Recurrence` | Recurrence | Input | `InArgument<string>` | No | | The recurrence details. |
| `ChangeRequiredAttendees` | Change Required Attendees | Options | `EventPropertyChange` | No | `NoChange` | How to modify the required attendees list. |
| `OverwriteRequiredAttendees` | Overwrite Required Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The required attendees to replace when overwriting. |
| `AddRequiredAttendees` | Add Required Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The required attendees to add. |
| `RemoveRequiredAttendees` | Remove Required Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The required attendees to remove. |
| `ChangeOptionalAttendees` | Change Optional Attendees | Options | `EventPropertyChange` | No | `NoChange` | How to modify the optional attendees list. |
| `OverwriteOptionalAttendees` | Overwrite Optional Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The optional attendees to replace when overwriting. |
| `AddOptionalAttendees` | Add Optional Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The optional attendees to add. |
| `RemoveOptionalAttendees` | Remove Optional Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The optional attendees to remove. |
| `ChangeResourceAttendees` | Change Resource Attendees | Options | `EventPropertyChange` | No | `NoChange` | How to modify the resource attendees list. |
| `OverwriteResourceAttendees` | Overwrite Resource Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The resource attendees to replace when overwriting. |
| `AddResourceAttendees` | Add Resource Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The resource attendees to add. |
| `RemoveResourceAttendees` | Remove Resource Attendees | Options | `InArgument<IEnumerable<string>>` | No | | The resource attendees to remove. |
| `Location` | Location | Options | `InArgument<string>` | No | | The updated location. |
| `MeetingUrl` | Meeting URL | Options | `InArgument<string>` | No | | The updated online meeting URL. |
| `IsOnlineMeeting` | Is Online Meeting | | `InArgument<bool>` | No | `False` | Whether the event should be an online meeting. |
| `Description` | Description | Options | `InArgument<string>` | No | | The updated description. |
| `ChangeAttachments` | Change Attachments | Options | `EventPropertyChange` | No | `NoChange` | How to modify the event attachments. |
| `ChangeCategories` | Change Categories | Options | `EventPropertyChange` | No | `NoChange` | How to modify the event categories. |
| `OverwriteCategories` | Overwrite Categories | Options | `InArgument<IEnumerable<string>>` | No | | Categories to replace when overwriting. |
| `AddCategories` | Add Categories | Options | `InArgument<IEnumerable<string>>` | No | | Categories to add. |
| `RemoveCategories` | Remove Categories | Options | `InArgument<IEnumerable<string>>` | No | | Categories to remove. |
| `Importance` | Importance | Options | `InArgument<Importance?>` | No | | The importance of the event. |
| `ShowAs` | Show As | Options | `InArgument<FreeBusyStatus?>` | No | | The event status displayed in the calendar. |
| `Sensitivity` | Sensitivity | Options | `InArgument<Sensitivity?>` | No | | The sensitivity label. |
| `PreferredReturnTimezone` | Preferred Return Timezone | Options | `InArgument<string>` | No | `UTC` | Return event in the preferred timezone. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Result` | Event | Output | [`OutArgument<O365EventItem>`](types/O365EventItem.md) | The modified event. |

## Output Model

See [`O365EventItem`](types/O365EventItem.md) for the event object structure.

## Enum Reference

| Enum | Values |
|---|---|
| `EventPropertyChange` | `NoChange`, `Overwrite`, `AddRemove` |
| `Importance` | `Low`, `Normal`, `High` |
| `FreeBusyStatus` | `Free`, `Tentative`, `Busy`, `Oof`, `WorkingElsewhere`, `Unknown` |
| `Sensitivity` | `Normal`, `Personal`, `Private`, `Confidential` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:ModifyEventConnections
    ConnectionId="{x:Null}"
    Title="Updated Meeting Title"
    ChangeRequiredAttendees="NoChange"
    DisplayName="Modify Event" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Event` property is required.
- Use `EventPropertyChange` to control how attendees, attachments, and categories are modified.
- Only properties with non-null values will be updated.
