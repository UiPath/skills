# Timeout Scope

`UiPath.Core.Activities.TimeoutScope`

Creates a scope with limited execution time. It throws a `System.TimeoutException` in case of timeout.

**Package:** `UiPath.System.Activities`
**Category:** System.Timer

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ThrowExceptionAfter | Throw Exception After | InArgument | `TimeSpan` | Yes | — | The duration after which the scope throws a `System.TimeoutException` if the body has not completed. |
| TimeoutMessage | Timeout Message | InArgument | `string` | No | — | The message included in the thrown `TimeoutException` when the time limit is exceeded. |

### Configuration

_No configuration properties._

### Output

_No output properties._

## XAML Example

```xml
<ui:TimeoutScope>
  <ui:TimeoutScope.ThrowExceptionAfter>
    <InArgument x:TypeArguments="s:TimeSpan">[TimeSpan.FromSeconds(30)]</InArgument>
  </ui:TimeoutScope.ThrowExceptionAfter>
  <ui:TimeoutScope.TimeoutMessage>
    <InArgument x:TypeArguments="x:String">Operation timed out after 30 seconds</InArgument>
  </ui:TimeoutScope.TimeoutMessage>
  <!-- child activities -->
</ui:TimeoutScope>
```

## Notes

- This is a container activity. Place the activities to be time-bounded inside its body.
- When the timeout elapses, a `System.TimeoutException` is thrown from within the scope. Use a Try/Catch around the scope to handle this gracefully.
- The `TimeoutMessage` value is surfaced as the exception `Message` property.
