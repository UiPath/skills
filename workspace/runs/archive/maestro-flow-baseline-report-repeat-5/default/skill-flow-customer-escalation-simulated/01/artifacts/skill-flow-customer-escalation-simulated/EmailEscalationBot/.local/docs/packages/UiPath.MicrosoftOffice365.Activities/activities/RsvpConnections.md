# RSVP

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.RsvpConnections`

Responds to a calendar event invitation (accept, tentatively accept, or decline).

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Event` | Event | Input | [`InArgument<O365EventItem>`](types/O365EventItem.md) | Yes | | The calendar event to respond to. |
| `Response` | Response | Input | `InArgument<EventResponseType>` | No | `Accept` | The RSVP response type. |
| `ApplyOnSeries` | Apply On Series | Input | `InArgument<bool>` | No | `False` | Whether to apply the response on the entire event series. |
| `EmailOrganizer` | Email Organizer | Input | `InArgument<bool>` | No | `False` | Whether to send the RSVP response as an email to the organizer. |
| `Comment` | Comment | Input | `InArgument<string>` | No | | An optional comment included in the RSVP response. |
| `NewStartTime` | New Start Time | Event Scheduling | `InArgument<DateTimeOffset>` | No | | A proposed new start time. |
| `NewEndTime` | New End Time | Event Scheduling | `InArgument<DateTimeOffset>` | No | | A proposed new end time. |
| `NewTimezone` | New Timezone | Event Scheduling | `InArgument<string>` | No | | The timezone for the proposed new times. |

## Output Model

This activity does not return an output object.

## Enum Reference

| Enum | Values |
|---|---|
| `EventResponseType` | `Accept`, `TentativelyAccept`, `Decline` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:RsvpConnections
    ConnectionId="{x:Null}"
    Response="Accept"
    DisplayName="RSVP" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Event` property is required.
- The `Comment` property is ignored if `EmailOrganizer` is `False`.
