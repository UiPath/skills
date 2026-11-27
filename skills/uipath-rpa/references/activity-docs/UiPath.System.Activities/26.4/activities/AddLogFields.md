# Add Log Fields

`UiPath.Core.Activities.AddLogFields`

Adds custom log fields to each Log Message.

**Package:** `UiPath.System.Activities`
**Category:** Logging

## Properties

### Input

_No input arguments._

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Fields | Fields | `Dictionary<string, InArgument>` | — | A collection of key-value pairs to attach to every subsequent log message as custom fields. |

### Output

_No output properties._

## XAML Example

```xml
<ui:AddLogFields>
  <ui:AddLogFields.Fields>
    <x:Reference>fieldsDictionary</x:Reference>
  </ui:AddLogFields.Fields>
</ui:AddLogFields>
```

## Notes

- Fields added here persist for the lifetime of the workflow execution until explicitly removed with **Remove Log Fields**.
- Use string keys that do not conflict with built-in UiPath log field names (e.g., `robotName`, `processName`).
