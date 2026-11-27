# Retry Scope

`UiPath.Core.Activities.RetryScope`

Retries the contained activities as long as the condition is not met or an error is thrown.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ContinueOnError` | Continue On Error | `InArgument` | `bool` | No | — | When `True`, the workflow continues execution even if the activity fails after all retries are exhausted. |
| `NumberOfRetries` | Number of attempts | `InArgument` | `int` | No | `3` (project default) | The maximum number of retry attempts. Configurable via project settings (`Section.RetryScope`, `Property.NumberOfRetries`). |
| `RetryInterval` | Retry interval | `InArgument` | `TimeSpan` | No | `5000` ms (project default) | The time to wait between retry attempts. Configurable via project settings (`Section.RetryScope`, `Property.RetryInterval`). |
| `LogRetriedExceptions` | Log exceptions | `InArgument` | `bool` | No | `False` (project default) | When `True`, exceptions that trigger a retry are logged. Configurable via project settings (`Section.RetryScope`, `Property.LogRetriedExceptions`). |
| `RetriedExceptionsLogLevel` | Log Level | `InArgument` | `LogLevel` | No | `Trace` (project default) | The log level used when logging retried exceptions. Configurable via project settings (`Section.RetryScope`, `Property.RetriedExceptionsLogLevel`). |

## XAML Example

```xml
<ui:RetryScope
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Retry Scope">
  <ui:RetryScope.NumberOfRetries>
    <InArgument x:TypeArguments="x:Int32">
      <VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="3" />
    </InArgument>
  </ui:RetryScope.NumberOfRetries>
  <ui:RetryScope.RetryInterval>
    <InArgument x:TypeArguments="s:TimeSpan">
      <VisualBasicValue x:TypeArguments="s:TimeSpan" ExpressionText="TimeSpan.FromSeconds(5)" />
    </InArgument>
  </ui:RetryScope.RetryInterval>
  <!-- Try body -->
  <!-- Condition body -->
</ui:RetryScope>
```

## Notes

- **Retry Scope** is a container/scope activity with two bodies: a **Try** body (the activities to attempt) and a **Condition** body (an activity returning `bool` that determines whether the attempt succeeded).
- A retry is triggered if the Try body throws an exception **or** if the Condition body returns `False`.
- `NumberOfRetries` and `RetryInterval` support project-level defaults and can be overridden per-instance via the properties panel.
- The `ActivityBody` and `Condition` properties are hidden in the designer (`IsVisible = false`) — they are wired up through the visual canvas, not the properties panel.
