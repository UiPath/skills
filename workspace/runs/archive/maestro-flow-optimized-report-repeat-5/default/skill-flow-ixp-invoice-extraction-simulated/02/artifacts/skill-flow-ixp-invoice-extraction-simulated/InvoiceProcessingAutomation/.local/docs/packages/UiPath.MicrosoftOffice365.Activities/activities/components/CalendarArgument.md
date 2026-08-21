# CalendarArgument

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Calendar.Models`

A composition argument object used by calendar activities to specify which calendar to operate on. The `InputMode` property determines which sub-properties are required.

## InputMode (ECalendarMode)

| Mode | Description | Required Properties | AI-XAML Suitable |
|------|-------------|--------------------|--------------------|
| `Browse` | Select a calendar via the Studio designer browser widget. | `BrowserCalendarId` (or `BrowserGroupId` for group calendars) | **Not suitable for AI-generated XAML** |
| `UseExisting` | Pass an existing [O365CalendarItem](../types/O365CalendarItem.md) reference, or leave null for the default calendar. | `Existing` (optional; null = default calendar) | Yes |

## Properties

### Core

| Property | Type | Description |
|----------|------|-------------|
| `InputMode` | `ECalendarMode` | The mode for specifying the calendar. |
| `ConnectionKey` | `String` | The connection ID from when the calendar was selected. |
| `ConnectionDescriptor` | `String` | A user-friendly label for the connection. |

### UseExisting Mode

| Property | Type | Description |
|----------|------|-------------|
| `Existing` | `InArgument<O365CalendarItem>` | An existing calendar item reference. Pass `null` or omit to use the default calendar. |

### Browse Mode (designer-only)

| Property | Type | Description |
|----------|------|-------------|
| `BrowserCalendarId` | `InArgument<String>` | Calendar ID from browser. `[AutopilotIgnored]` |
| `BrowserFriendlyName` | `InArgument<String>` | Display name from browser. |
| `BrowserCalendarGroupId` | `InArgument<String>` | Calendar group ID from browser. `[AutopilotIgnored]` |
| `BrowserGroupId` | `InArgument<String>` | Microsoft 365 group ID from browser. `[AutopilotIgnored]` |

### Other

| Property | Type | Description |
|----------|------|-------------|
| `Backup` | `BackupSlot<ECalendarMode>` | Stores the previous InputMode for undo. |

## XAML Examples

> `Backup` is always present in Studio-generated XAML; include it to match Studio's output. `usau:` maps to `xmlns:usau="clr-namespace:UiPath.Shared.Activities.Utils;assembly=UiPath.MicrosoftOffice365.Activities"`. `umace:` maps to `xmlns:umace="clr-namespace:UiPath.MicrosoftOffice365.Activities.Calendar.Enums;assembly=UiPath.MicrosoftOffice365.Activities"`.

### UseExisting Mode (default calendar)
```xml
<calmodels:CalendarArgument InputMode="UseExisting">
    <calmodels:CalendarArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umace:ECalendarMode" StoredValue="UseExisting">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umace:ECalendarMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
    </calmodels:CalendarArgument.Backup>
</calmodels:CalendarArgument>
```

### UseExisting Mode (specific calendar)
```xml
<calmodels:CalendarArgument InputMode="UseExisting">
    <calmodels:CalendarArgument.Backup>
        <usau:BackupSlot x:TypeArguments="umace:ECalendarMode" StoredValue="UseExisting">
          <usau:BackupSlot.BackupValues>
            <scg:Dictionary x:TypeArguments="umace:ECalendarMode, scg:List(x:Object)" />
          </usau:BackupSlot.BackupValues>
        </usau:BackupSlot>
    </calmodels:CalendarArgument.Backup>
    <calmodels:CalendarArgument.Existing>
        <InArgument x:TypeArguments="calmodels2:O365CalendarItem">[myCalendar]</InArgument>
    </calmodels:CalendarArgument.Existing>
</calmodels:CalendarArgument>
```

## Cross-References

- Selects calendars of type [O365CalendarItem](../types/O365CalendarItem.md)
- Used by calendar activities (CreateEventConnections, GetEventListConnections, ForEachEventConnections, etc.)
- Events are of type [O365EventItem](../types/O365EventItem.md)
- Events can be filtered by [EventFilterCollection](../filtering/EventFilterCollection.md)
