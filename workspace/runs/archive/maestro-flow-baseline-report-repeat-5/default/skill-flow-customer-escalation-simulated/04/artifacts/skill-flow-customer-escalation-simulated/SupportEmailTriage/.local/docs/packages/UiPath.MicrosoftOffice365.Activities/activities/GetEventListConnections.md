# Get Event List

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.GetEventListConnections`

Gets the list of calendar events within a date range. Supports filtering via condition builder or OData query.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `CalendarArgument` | Calendar | | [`CalendarArgument`](components/CalendarArgument.md) | No | | Specifies the calendar to search. See [CalendarArgument](components/CalendarArgument.md) for input modes. |
| `StartDate` | Start Date | Input | `InArgument<DateTimeOffset>` | Yes | | The date and time as of when to search for events. |
| `EndDate` | End Date | Input | `InArgument<DateTimeOffset>` | Yes | | The date and time until which to search for events. |
| `MaxResults` | Max Results | Options | `InArgument<int>` | No | `50` | The maximum number of events to retrieve. |
| `PreferredReturnTimezone` | Preferred Return Timezone | Options | `InArgument<string>` | No | `UTC` | The timezone used to display event start and end times. |
| `Filter` | Filter | | [`EventFilterCollection`](filtering/EventFilterCollection.md) | | | Condition-based filter. See [EventFilterCollection](filtering/EventFilterCollection.md). |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `EventList` | Event List | Output | `OutArgument<List<`[`O365EventItem`](types/O365EventItem.md)`>>` | The processed event list. |

## Output Model

See [`O365EventItem`](types/O365EventItem.md) for the event object structure.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umace="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umac:GetEventListConnections
    ConnectionId="{x:Null}"
    MaxResults="50" EventList="[events]"
    DisplayName="Get Event List">
  <umac:GetEventListConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umace:EventFilterMode" StoredValue="ConditionBuilder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umace:EventFilterMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umac:GetEventListConnections.FilterSelectionBackup>
</umac:GetEventListConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- `StartDate` and `EndDate` are required.
- Default MaxResults is 50. Set to 0 or a negative value to retrieve all events.
- Supports filtering via condition builder or OData query.
