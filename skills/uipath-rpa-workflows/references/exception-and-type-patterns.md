# Exception and system type patterns

Read this file when: using TryCatch, or getting "type not defined" errors on Exception, DateTime, Guid, Uri.

## The `s:` prefix rule

The `x:` XAML namespace only covers primitives: `x:String`, `x:Int32`, `x:Double`, `x:Boolean`, `x:Object`, `x:TimeSpan`, etc.

For **all other System types**, use `s:` with this xmlns:

```xml
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
```

| Type | Wrong | Correct |
|------|-------|---------|
| Exception | `x:Exception` | `s:Exception` |
| DateTime | `x:DateTime` | `s:DateTime` |
| DateTimeOffset | `x:DateTimeOffset` | `s:DateTimeOffset` |
| Guid | `x:Guid` | `s:Guid` |
| Uri | `x:Uri` | `s:Uri` |

## TryCatch with System.Exception

This is the most common case. The `get-default-activity-xaml` for TryCatch returns this exact pattern:

```xml
<!-- Add to root Activity element -->
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"

<!-- TryCatch structure -->
<TryCatch sap2010:WorkflowViewState.IdRef="TryCatch_1">
  <TryCatch.Try>
    <Sequence DisplayName="Try" sap2010:WorkflowViewState.IdRef="Sequence_2">
      <!-- activities that may throw -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch" sap2010:WorkflowViewState.IdRef="Sequence_3">
          <ui:LogMessage Message="[&quot;Error: &quot; &amp; exception.Message]"
                         sap2010:WorkflowViewState.IdRef="LogMessage_1" />
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
</TryCatch>
```

**Critical**: `s:Exception` appears in THREE places — the `<Catch>`, the `<ActivityAction>`, and the `<DelegateInArgument>`. All three must match.

## DateTime variable

```xml
<!-- xmlns:s must be declared on root Activity -->
<Variable x:TypeArguments="s:DateTime" Name="startTime" />

<!-- VB default value -->
<Variable x:TypeArguments="s:DateTime" Name="startTime" Default="[DateTime.Now]" />
```

## Common errors and fixes

| Error message | Cause | Fix |
|--------------|-------|-----|
| `Type 'x:Exception' not found` | Used `x:` prefix for Exception | Change to `s:Exception`, add `xmlns:s` |
| `Type 'x:DateTime' not found` | Used `x:` prefix for DateTime | Change to `s:DateTime`, add `xmlns:s` |
| `Type 'System.Exception' is not defined` | Missing namespace import | Add `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"` to root AND `<x:String>System</x:String>` to NamespacesForImplementation |
| `Cannot create unknown type '{clr-namespace:System}Exception'` | Wrong xmlns assembly | Ensure assembly is `System.Private.CoreLib` not `mscorlib` or `System` |
