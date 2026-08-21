# For Each Event

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

> **Agent instruction — connection:** Before writing XAML, use the available tooling to resolve or search for a connection ID for the connector listed in this doc. If the connection ID cannot be resolved, leave ConnectionId="{x:Null}".

`UiPath.MicrosoftOffice365.Activities.Calendar.ForEachEventConnections`

Iterates over a collection of calendar events within a date range. Supports filtering via condition builder or OData query.

| Property | Value |
|---|---|
| **Package** | `UiPath.MicrosoftOffice365.Activities` |
| **Category** | Calendar |
| **Connector** | `uipath-microsoft-outlook365` |

## Input Properties

| Property | Display Name | Category | Type | Required | Default | Description |
|---|---|---|---|---|---|---|
| `ConnectionId` | Connection ID | | `InArgument<string>` | Yes | | The Microsoft 365 connection to use. |
| `CalendarArgument` | Calendar | | [`CalendarArgument`](components/CalendarArgument.md) | No | | Specifies the calendar to iterate events from. See [CalendarArgument](components/CalendarArgument.md) for input modes. |
| `StartDate` | Start Date | Input | `InArgument<DateTimeOffset>` | Yes | | The date and time as of when to search for events. |
| `EndDate` | End Date | Input | `InArgument<DateTimeOffset>` | Yes | | The date and time until which to search for events. |
| `MaxResults` | Max Results | Options | `InArgument<int>` | No | `50` | The maximum number of events to retrieve and iterate over. |
| `PreferredReturnTimezone` | Preferred Return Timezone | Options | `InArgument<string>` | No | `UTC` | The timezone used to display event start and end times. |
| `Filter` | Filter | | [`EventFilterCollection`](filtering/EventFilterCollection.md) | | | Condition-based filter. See [EventFilterCollection](filtering/EventFilterCollection.md). |

## Output Properties

| Property | Display Name | Category | Type | Description |
|---|---|---|---|---|
| `Length` | Length | Output | `OutArgument<int>` | The number of events processed. |

## Output Model

Each iteration provides an [`O365EventItem`](types/O365EventItem.md) as `CurrentEvent` and an `int` as `CurrentEventIndex`.

## XAML Example

```xml
<!--
    Namespace declarations for the enclosing root <Activity> element:
    xmlns:umac="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umace="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar.Enums;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:umo365cm="clr-namespace:UiPath.MicrosoftOffice365.Calendar.Models;assembly=UiPath.MicrosoftOffice365"
    xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
-->
<umac:ForEachEventConnections
    ConnectionId="{x:Null}"
    MaxResults="50"
    DisplayName="For Each Event">
  <umac:ForEachEventConnections.FilterSelectionBackup>
    <usau:BackupSlot x:TypeArguments="umace:EventFilterMode" StoredValue="ConditionBuilder">
      <usau:BackupSlot.BackupValues>
        <scg:Dictionary x:TypeArguments="umace:EventFilterMode, scg:List(x:Object)" />
      </usau:BackupSlot.BackupValues>
    </usau:BackupSlot>
  </umac:ForEachEventConnections.FilterSelectionBackup>
  <umac:ForEachEventConnections.Body>
    <ActivityAction x:TypeArguments="umo365cm:O365EventItem, x:Int32">
      <ActivityAction.Argument1>
        <DelegateInArgument x:TypeArguments="umo365cm:O365EventItem" Name="CurrentEvent" />
      </ActivityAction.Argument1>
      <ActivityAction.Argument2>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="CurrentEventIndex" />
      </ActivityAction.Argument2>
      <!-- activities here -->
    </ActivityAction>
  </umac:ForEachEventConnections.Body>
</umac:ForEachEventConnections>
```

## Notes

- Prefer using this activity **outside** of [`Office365ApplicationScope`](Office365ApplicationScope.md). `*Connections` activities authenticate via Integration Service independently — no scope wrapper required. Place inside the scope only when Integration Service is unavailable or when supplying credentials directly (interactive token, username/password, certificate, or app secret) via the scope.
- `StartDate` and `EndDate` are required.
- The `Body` property contains a sequence of activities executed for each event in the iteration.
- Current item variable name defaults to `CurrentEvent` and current index to `CurrentEventIndex`.
