# Common Activity Card

**Package anchor:** `UiPath.System.Activities` 26.4 (verified against 26.4.1-preview).

Copy-safe snippets for exactly these 10 activities: `Sequence` · `If` · `TryCatch` · `While` · `ForEach<T>` · `Assign` · `LogMessage` · `WriteLine` · `Throw` · `Rethrow`.

**Supersedes the Rule 21 discovery procedure for these activities only:** when authoring one, skip `activities find`, `activities get-default-xaml`, and the per-activity `<Activity>.md` read; copy its snippet here. Every other activity gets full Rule 21 — including `Switch<T>`, `DoWhile`, `MultipleAssign`, and `Delay`, which are NOT on this card. Self-extending this card by personal judgment ("this one feels simple, I'll skip the procedure") is the failure mode.

## How to read the snippets

Insert fragments in a complete `<Activity>` root declaring:

```xml
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

Extra prefixes are on the **Class:** line (Legacy .NET 4.6.1: `assembly=mscorlib`). Add `sap2010:WorkflowViewState.IdRef` to every inserted activity ([xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) Rule 25). Snippets are VB; for C# apply [xaml/csharp-activity-binding-guide.md](xaml/csharp-activity-binding-guide.md). No `ui:` prefix unless shown. Wrap every body/branch slot in `Sequence` (Rule 24), even a single child.

### Sequence
**Class:** `System.Activities.Statements.Sequence`.

```xml
<Sequence DisplayName="Sequence"><!-- child activities in execution order --></Sequence>
```

Declare `<Sequence.Variables>` only for variables it owns.

### If
**Class:** `System.Activities.Statements.If`.

```xml
<If DisplayName="If"><If.Condition><InArgument x:TypeArguments="x:Boolean"><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" /></InArgument></If.Condition><If.Then><Sequence DisplayName="Then"><!-- then branch --></Sequence></If.Then><If.Else><Sequence DisplayName="Else"><!-- else branch --></Sequence></If.Else></If>
```

Omit unused `<If.Else>`; never emit an empty slot. Multiple `else if` → `IfElseIfV2` (off-card, Rule 21).

### TryCatch
**Class:** `System.Activities.Statements.TryCatch`; plus `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`.

```xml
<TryCatch DisplayName="Try Catch"><TryCatch.Try><Sequence DisplayName="Try"><!-- guarded body --></Sequence></TryCatch.Try><TryCatch.Catches><Catch x:TypeArguments="s:Exception"><ActivityAction x:TypeArguments="s:Exception"><ActivityAction.Argument><DelegateInArgument x:TypeArguments="s:Exception" Name="exception" /></ActivityAction.Argument><Sequence DisplayName="Catch"><!-- handler body; reference "exception" --></Sequence></ActivityAction></Catch></TryCatch.Catches><TryCatch.Finally><Sequence DisplayName="Finally"><!-- finally body --></Sequence></TryCatch.Finally></TryCatch>
```

Each `Catch` needs its own `<ActivityAction x:TypeArguments="...">` holding `<DelegateInArgument ... Name="exception" />` (`Name` = handler variable). Specific exception types before `s:Exception`; omit unused `Finally`. More: [error-handling-guide.md](error-handling-guide.md).

### While
**Class:** `UiPath.Core.Activities.InterruptibleWhile` (Studio emits this, not `System.Activities.Statements.While`); `ui:` prefix.

```xml
<ui:InterruptibleWhile DisplayName="While"><ui:InterruptibleWhile.Condition><VisualBasicValue x:TypeArguments="x:Boolean" ExpressionText="counter &lt; 10" /></ui:InterruptibleWhile.Condition><ui:InterruptibleWhile.Body><Sequence DisplayName="Body"><!-- iteration body --></Sequence></ui:InterruptibleWhile.Body></ui:InterruptibleWhile>
```

`MaxIterations` (`InArgument<int>`): `0` = **unlimited** (default); set a positive cap against infinite loops. `CurrentIndex`: zero-based `OutArgument<int>`.

### For Each&lt;T&gt;
**Class:** `UiPath.Core.Activities.ForEach`1` (Studio emits this, not `System.Activities.Statements.ForEach<T>`); `ui:` prefix; plus `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"`.

Change the outer, `ActivityAction`, and `DelegateInArgument` `x:TypeArguments` together:

```xml
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each"><ui:ForEach.Values><InArgument x:TypeArguments="sc:IEnumerable"><VisualBasicValue x:TypeArguments="sc:IEnumerable" ExpressionText="myList" /></InArgument></ui:ForEach.Values><ui:ForEach.Body><ActivityAction x:TypeArguments="x:String"><ActivityAction.Argument><DelegateInArgument x:TypeArguments="x:String" Name="item" /></ActivityAction.Argument><Sequence DisplayName="Body"><!-- iteration body; reference "item" --></Sequence></ActivityAction></ui:ForEach.Body></ui:ForEach>
```

`Values` is non-generic `InArgument<System.Collections.IEnumerable>`, not `IEnumerable<T>`; `T` comes from the outer activity. `Body` must sit in `<ui:ForEach.Body>` (NOT the ContentProperty): a bare `<ActivityAction>` in `<ui:ForEach>` gives `Cannot set unknown member '...Implementation'`. `MaxIterations`/`CurrentIndex` as While; iterator = `DelegateInArgument.Name`.

### Assign
**Class:** `System.Activities.Statements.Assign` — no activity type argument; type its arguments.

```xml
<Assign DisplayName="Assign"><Assign.To><OutArgument x:TypeArguments="x:Int32"><VisualBasicReference x:TypeArguments="x:Int32" ExpressionText="counter" /></OutArgument></Assign.To><Assign.Value><InArgument x:TypeArguments="x:Int32"><VisualBasicValue x:TypeArguments="x:Int32" ExpressionText="counter + 1" /></InArgument></Assign.Value></Assign>
```

`To` must be writable (variable, argument, indexer) — `VisualBasicReference`/`CSharpReference`; the value side uses `VisualBasicValue`/`CSharpValue`. One target per `Assign`. In a Windows project, two or more consecutive assignments may go in one `MultipleAssign` (off-card, Rule 21; Windows-only: Portable fails with `Cannot create unknown type`).

### Log Message
**Class:** `UiPath.Core.Activities.LogMessage`; `ui:` prefix.

```xml
<ui:LogMessage Level="Info" DisplayName="Log Message"><ui:LogMessage.Message><InArgument x:TypeArguments="x:Object"><VisualBasicValue x:TypeArguments="x:Object" ExpressionText="$&quot;Processed {count} items&quot;" /></InArgument></ui:LogMessage.Message></ui:LogMessage>
```

`Level` is `InArgument<LogLevel>` (`Trace` | `Info` | `Warn` | `Error` | `Fatal`), default `Info`, hidden from `get-default-xaml`. `Message` is `InArgument<object>`, not `string`; VB shorthand `[$"x = {x}"]` works; C# uses `<CSharpValue x:TypeArguments="x:Object">`. Use for Orchestrator-visible output.

### Write Line
**Class:** `System.Activities.Statements.WriteLine`.

```xml
<WriteLine DisplayName="Write Line"><WriteLine.Text><InArgument x:TypeArguments="x:String"><VisualBasicValue x:TypeArguments="x:String" ExpressionText="$&quot;processed {count} items&quot;" /></InArgument></WriteLine.Text></WriteLine>
```

Stdout only, invisible in Orchestrator — prefer `LogMessage` there. Do not set `TextWriter`.

### Throw
**Class:** `System.Activities.Statements.Throw`; plus `xmlns:s` (as TryCatch).

```xml
<Throw DisplayName="Throw"><Throw.Exception><InArgument x:TypeArguments="s:Exception"><VisualBasicValue x:TypeArguments="s:Exception" ExpressionText="new InvalidOperationException(&quot;Invoice total is negative&quot;)" /></InArgument></Throw.Exception></Throw>
```

`Exception` is a constructor expression, not a string (`Throw.Exception = "message"` is invalid). A domain type (`BusinessRuleException`) lets handlers tell business from system errors.

### Rethrow
**Class:** `System.Activities.Statements.Rethrow`.

```xml
<Rethrow DisplayName="Rethrow" />
```

No properties; valid only inside a `Catch` body (elsewhere: runtime `InvalidOperationException`); preserves the original stack trace; place it last. To translate the exception, `Throw new <Type>(...)` instead.
