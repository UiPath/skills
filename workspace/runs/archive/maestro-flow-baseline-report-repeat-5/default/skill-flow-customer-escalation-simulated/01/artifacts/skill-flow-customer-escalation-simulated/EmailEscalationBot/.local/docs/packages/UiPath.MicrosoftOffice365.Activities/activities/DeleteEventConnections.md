# Delete Event

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.DeleteEventConnections`

Deletes or declines a calendar event.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Event` | Event | Input | [`InArgument<O365EventItem>`](types/O365EventItem.md) | Yes | | The calendar event to delete or decline. |
| `DeleteOption` | Delete Option | Input | `InArgument<DeleteOptionType>` | No | `SingleEvent` | The option for event deletion. |
| `Comment` | Comment | Input | `InArgument<string>` | No | | The message sent to the attendees/organizer of the deleted event. |

## Output Model

This activity does not return an output object.

## Enum Reference

| Enum | Values |
|---|---|
| `DeleteOptionType` | `SingleEvent`, `ThisAndFollowingEvents`, `AllEvents` |

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:DeleteEventConnections
    ConnectionId="{x:Null}"
    DeleteOption="SingleEvent"
    DisplayName="Delete Event" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- The `Event` property is required.
- Use `DeleteOption` to control whether to delete a single event, this and following events, or all events in a series.
