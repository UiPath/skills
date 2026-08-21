# Get Calendars

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.GetCalendarsConnections`

Gets the user's calendars, optionally including group calendars.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `IncludeGroupCalendars` | Include Group Calendars | Input | `bool` | No | `False` | Specifies whether to include group calendars in the returned list. |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Calendars` | Calendars | Output | `OutArgument<List<O365CalendarItem>>` | The list of calendars retrieved for the user. |
| `DefaultCalendar` | Default Calendar | Output | `OutArgument<O365CalendarItem>` | The user's default calendar, if one exists. |

## Output Model

Each `O365CalendarItem` represents a calendar with its properties.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
-->
<umac:GetCalendarsConnections
    ConnectionId="{x:Null}"
    IncludeGroupCalendars="False"
    DisplayName="Get Calendars" />
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- Returns both personal and group calendars when `IncludeGroupCalendars` is `True`.
