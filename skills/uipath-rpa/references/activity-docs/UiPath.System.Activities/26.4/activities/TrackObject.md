# Track Object

`UiPath.Core.Activities.ProcessTracking.TrackObject`

Adds a new object to the task. This object will appear as metadata information on the task in Process Mining.

**Package:** `UiPath.System.Activities`
**Category:** Process Tracking

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ObjectType` | Object Type | InArgument | `string` | Yes | — | The type label for the object being tracked (e.g., `"invoice"`, `"document"`, `"case"`). |
| `ObjectId` | Object Id | InArgument | `string` | Yes | — | A unique identifier for the object being tracked (e.g., an invoice number or case ID). |
| `ObjectInteraction` | Object Interaction | InArgument | `PTSObjectInteraction` | No | `null` | The type of interaction the current task has with the object (e.g., read, write, create). |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ObjectPropertiesV2` | Object Properties V2 | `InArgument<Dictionary<string, object>>` | — | A dictionary of additional key-value metadata properties to associate with the tracked object. |

## XAML Example

```xml
<ui:TrackObject
    xmlns:ui="clr-namespace:UiPath.Core.Activities.ProcessTracking;assembly=UiPath.System.Activities"
    DisplayName="Track Object"
    ObjectType="[&quot;invoice&quot;]"
    ObjectId="[invoiceNumber]"
    ObjectInteraction="[PTSObjectInteraction.Read]" />
```

## Notes

- **Track Object** must be used inside a **Process Tracking Scope** activity. It associates an object (identified by `ObjectType` and `ObjectId`) with the current task being tracked.
- The tracked object and its metadata appear as enrichment data on the task in UiPath Process Mining dashboards.
- `ObjectInteraction` describes how the automation interacted with the object (e.g., created it, read it, updated it). Refer to the `PTSObjectInteraction` enum values available in the UiPath.System.Activities package.
- `ObjectPropertiesV2` allows attaching arbitrary key-value metadata. Keys and values must be serializable types.
