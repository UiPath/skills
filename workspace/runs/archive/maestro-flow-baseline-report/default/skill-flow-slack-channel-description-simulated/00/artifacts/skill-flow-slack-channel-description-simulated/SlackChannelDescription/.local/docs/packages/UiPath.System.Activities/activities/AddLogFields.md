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
<ui:AddLogFields xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:AddLogFields.Fields>
    <scg:Dictionary x:TypeArguments="x:String, InArgument"
                    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib">
      <InArgument x:TypeArguments="x:String" x:Key="customerId">[currentCustomerId]</InArgument>
      <InArgument x:TypeArguments="x:String" x:Key="region">"EMEA"</InArgument>
    </scg:Dictionary>
  </ui:AddLogFields.Fields>
</ui:AddLogFields>
```

Author the `Fields` dictionary inline. Each entry is an `InArgument` of the appropriate type, keyed by the custom log-field name. An external `<x:Reference>` to a separately-defined dictionary node is not portable and should be avoided.

## Notes

- Fields added here persist for the lifetime of the workflow execution until explicitly removed with **Remove Log Fields**.
- Use string keys that do not conflict with built-in UiPath log field names (e.g., `robotName`, `processName`).
