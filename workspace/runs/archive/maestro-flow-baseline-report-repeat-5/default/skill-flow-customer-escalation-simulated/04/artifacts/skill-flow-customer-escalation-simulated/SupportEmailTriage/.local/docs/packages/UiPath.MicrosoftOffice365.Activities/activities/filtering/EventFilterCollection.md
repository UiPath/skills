# EventFilterCollection

> **Agent instruction — read all linked docs before proceeding:** Follow and read every hyperlinked reference document on this page in full before generating XAML. XAML structural patterns (BackupSlots, StoredValue, x:Reference, all-null attributes, namespace declarations) are defined in the linked component, type, and filter docs — not repeated here. If those linked docs also contain hyperlinks to other reference docs, follow those too.

**Namespace:** `UiPath.MicrosoftOffice365.Activities.Calendar.Filters`
**Inherits:** `BaseFilterCollection<EventFilterElement, EventFilterLogicalOperator>`

Filters calendar events by subject, attendees, importance, show-as status, type, attachments, and all-day flag. Used by activities like GetEventListConnections and ForEachEventConnections.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `LogicalOperator` | `EventFilterLogicalOperator` | Logical operator between conditions (`And`, `Or`). |
| `Filters` | `List<EventFilterElement>` | Zero or more filter conditions to apply. |

## EventFilterElement

Each filter element specifies a field, operator, and value. The applicable operator and value properties depend on the `Criteria` field type.

| Property | Type | Description |
|----------|------|-------------|
| `Criteria` | `EventFilterField` | The field to filter on. |
| `StringOperator` | `EventStringFilterOperator` | Operator for string fields (e.g., `Equals`, `StartsWith`, `Contains`). |
| `EnumOperator` | `EventEnumFilterOperator` | Operator for enum fields (Importance, ShowAs, Type). |
| `BoolOperator` | `EventBoolFilterOperator` | Operator for boolean fields (HasAttachments, AllDay, Organizer). |
| `ImportanceValue` | `EventFilterImportance` | Value for importance filtering. |
| `ShowAsValue` | `EventFilterShowAs` | Value for show-as filtering. |
| `TypeValue` | `EventFilterType` | Value for event type filtering. |
| `InStringValue` | `InArgument<String>` | String value for string-based filters. |

## EventFilterField Enum

| Value | Filter Type | Description |
|-------|------------|-------------|
| `Subject` | String | Filter by event subject. |
| `Attendees` | String | Filter by attendee names/addresses. |
| `Importance` | Enum | Filter by importance (`Low`, `Normal`, `High`). |
| `ShowAs` | Enum | Filter by free/busy status. |
| `Type` | Enum | Filter by event type (`SingleInstance`, `Occurrence`, etc.). |
| `HasAttachments` | Boolean | Filter by whether the event has attachments. |
| `AllDay` | Boolean | Filter by whether the event is all-day. |
| `Organizer` | Boolean | Filter by whether the current user is the organizer. |

## Cross-References

- Filters results of type [O365EventItem](../types/O365EventItem.md)
- Used alongside [CalendarArgument](../components/CalendarArgument.md) for calendar selection
