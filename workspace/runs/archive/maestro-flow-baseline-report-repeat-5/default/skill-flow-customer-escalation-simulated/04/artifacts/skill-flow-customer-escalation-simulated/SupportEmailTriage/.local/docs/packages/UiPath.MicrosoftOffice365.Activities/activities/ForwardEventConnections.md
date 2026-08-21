# Forward Event

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.ForwardEventConnections`

Forwards a calendar event to new attendees.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `Event` | Event | Input | [`InArgument<O365EventItem>`](types/O365EventItem.md) | Yes | | The event to forward. |
| `Attendees` | Attendees | Input | `InArgument<IEnumerable<string>>` | Yes | | Attendees to forward the event to. |
| `ApplyOnSeries` | Apply On Series | Input | `InArgument<bool>` | No | `False` | Forward single instance or entire series. |
| `Comment` | Comment | Input | `InArgument<string>` | No | | Optional comment when forwarding. |

## Output Model

This activity does not return an output object.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:ForwardEventConnections
    ConnectionId="{x:Null}"
    DisplayName="Forward Event" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Both `Event` and `Attendees` are required.
