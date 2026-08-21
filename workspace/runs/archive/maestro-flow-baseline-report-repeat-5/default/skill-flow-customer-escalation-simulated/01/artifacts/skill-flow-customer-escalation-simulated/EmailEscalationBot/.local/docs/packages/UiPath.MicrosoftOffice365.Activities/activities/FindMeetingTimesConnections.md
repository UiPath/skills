# Find Meeting Times

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.FindMeetingTimesConnections`

Finds available meeting time suggestions for a set of attendees within a time window.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Attendees` | Attendees | | `InArgument<IEnumerable<string>>` | No | | The email addresses of the attendees to find meeting times for. |
| `IntervalStart` | Interval Start | | `InArgument<DateTimeOffset>` | No | | The start of the time window in which to search. |
| `IntervalEnd` | Interval End | | `InArgument<DateTimeOffset>` | No | | The end of the time window in which to search. |
| `MeetingDuration` | Meeting Duration | | `InArgument<TimeSpan>` | No | `00:30:00` | The desired duration of the meeting. |
| `Timezone` | Timezone | | `InArgument<string>` | No | | The timezone used to interpret the search interval and returned suggestions. |
| `OrganizerRequired` | Organizer Required | | `InArgument<bool>` | No | `True` | Indicates whether the organizer must be available. |
| `Constraint` | Constraint | | `InArgument<MeetingTimeConstraint>` | No | `Work` | The time constraint applied when searching for meeting times. |
| `Locations` | Locations | | `InArgument<IEnumerable<string>>` | No | | The preferred locations to consider. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `EmptySuggestionsReason` | Empty Suggestions Reason | Output | `OutArgument<string>` | The reason why no meeting time suggestions were returned, if applicable. |

## Output Model

The activity returns an `IEnumerable<MeetingTimeSuggestion>` containing the suggested meeting times.

## Enum Reference

| Enum | Values |
|---|---|
| `MeetingTimeConstraint` | `Work`, `Any` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:FindMeetingTimesConnections
    ConnectionId="{x:Null}"
    MeetingDuration="00:30:00"
    DisplayName="Find Meeting Times" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- If `IntervalStart` and `IntervalEnd` are not specified, defaults to the current time to midnight.
- If `Timezone` is not specified, the user's account timezone is used.
