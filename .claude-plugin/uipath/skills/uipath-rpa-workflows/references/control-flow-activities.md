# XAML Activities

Core control flow activities and their usage patterns.

## Core Control Flow Activities (UiPath.System.Activities)

These activities are part of `UiPath.System.Activities` (always installed). You can write them directly **without** calling `uipcli rpa get-default-activity-xaml`. Use these templates as-is — just replace the placeholder expressions with your actual logic.

**Expression syntax notes (C# projects):**
- Inside `<InArgument>` / `<InOutArgument>` elements, use explicit `<CSharpValue>` (read/evaluate):
  ```xml
  <InArgument x:TypeArguments="x:String">
    <CSharpValue x:TypeArguments="x:String">myVariable.ToString()</CSharpValue>
  </InArgument>
  ```
- Inside `<OutArgument>` / `<InOutArgument>` elements for lvalue (write target), use `<CSharpReference>`:
  ```xml
  <OutArgument x:TypeArguments="x:String">
    <CSharpReference x:TypeArguments="x:String">myVariable</CSharpReference>
  </OutArgument>
  ```
- `CSharpValue` and `CSharpReference` are in the default activities namespace (no prefix needed)
- Do **NOT** use `[bracket]` shorthand — brackets create `VisualBasicValue` nodes at deserialization time, which fail validation for C#-only syntax (`null`, `?.`, `??`, `typeof()`, etc.)
- Simple non-argument properties (`Direction == "Property"`) like `DisplayName`, `Level`, etc. are plain attribute strings — no expression wrapper needed

**xmlns prefixes used below** (these should be present in all workflow files created):
```
xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"   (default — Assign, If, Sequence, etc.)
xmlns:ui="http://schemas.uipath.com/workflow/activities"          (UiPath — ForEach, LogMessage, etc.)
xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"
xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"
xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"
xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
```

### Assign

Sets a variable or argument value. No namespace prefix (default WF4 activity).

```xml
<!-- Simple string assignment -->
<Assign DisplayName="Set Name">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">myVariable</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">"Hello World"</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>

<!-- Expression assignment -->
<Assign DisplayName="Set Current Date">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">currentDate</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">DateTime.Now.ToString()</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>

<!-- Array assignment -->
<Assign DisplayName="Set Days">
  <Assign.To>
    <OutArgument x:TypeArguments="s:String[]">
      <CSharpReference x:TypeArguments="s:String[]">dayNames</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="s:String[]">
      <CSharpValue x:TypeArguments="s:String[]">new string[] { "Mon", "Tue", "Wed" }</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>

<!-- Int32 assignment -->
<Assign DisplayName="Set Counter">
  <Assign.To>
    <OutArgument x:TypeArguments="x:Int32">
      <CSharpReference x:TypeArguments="x:Int32">counter</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:Int32">
      <CSharpValue x:TypeArguments="x:Int32">counter + 1</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>
```

**Key rules:**
- `Assign.To` always uses `OutArgument` with `x:TypeArguments` matching the variable type
- `Assign.Value` always uses `InArgument` with matching `x:TypeArguments`
- The type in `To` and `Value` must match — mismatches cause validation errors
- Common type mappings: `x:String`, `x:Int32`, `x:Boolean`, `x:Double`, `x:Object`, `s:DateTime`, `s:String[]`, `scg:List(x:String)`

### If / Else

Conditional branching. No namespace prefix.

```xml
<If DisplayName="Check Condition">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">myValue &gt; 10</CSharpValue>
    </InArgument>
  </If.Condition>
  <If.Then>
    <Sequence DisplayName="Then">
      <!-- Activities when condition is true -->
    </Sequence>
  </If.Then>
  <If.Else>
    <Sequence DisplayName="Else">
      <!-- Activities when condition is false -->
    </Sequence>
  </If.Else>
</If>
```

**Key rules:**
- Condition is always `InArgument x:TypeArguments="x:Boolean"` — expression must evaluate to bool
- `If.Then` and `If.Else` each accept **one** child activity — wrap multiple activities in a `<Sequence>`
- `If.Else` is optional (can be omitted for if-without-else)

### Log Message

Writes to the UiPath execution log. Uses `ui:` namespace prefix.

```xml
<!-- Simple string message -->
<ui:LogMessage DisplayName="Log Message" Level="Info">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <CSharpValue x:TypeArguments="x:Object">"Processing started"</CSharpValue>
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>

<!-- Expression with variable interpolation -->
<ui:LogMessage DisplayName="Log Status" Level="Warn">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <CSharpValue x:TypeArguments="x:Object">"Processed " + count.ToString() + " items"</CSharpValue>
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>
```

**Key rules:**
- Message type is always `x:Object` (not `x:String`) — accepts any expression
- `Level` attribute: `Trace`, `Info`, `Warn`, `Error`, `Fatal` (default: `Info`)
- String interpolation: use C# string concatenation (`+`), not `$""` interpolation (XAML doesn't support it)

### For Each

Iterates over a collection. Uses `ui:` namespace prefix. The `x:TypeArguments` on the `ForEach` element specifies the **item type**.

```xml
<!-- ForEach over strings -->
<ui:ForEach x:TypeArguments="x:String" DisplayName="For Each item">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <CSharpValue x:TypeArguments="sc:IEnumerable">myStringList</CSharpValue>
    </InArgument>
  </ui:ForEach.Values>
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:String">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:String" Name="item" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Use "item" variable here -->
        <ui:LogMessage DisplayName="Log Item">
          <ui:LogMessage.Message>
            <InArgument x:TypeArguments="x:Object">
              <CSharpValue x:TypeArguments="x:Object">item</CSharpValue>
            </InArgument>
          </ui:LogMessage.Message>
        </ui:LogMessage>
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>

<!-- ForEach over integers -->
<ui:ForEach x:TypeArguments="x:Int32" DisplayName="For Each number">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <CSharpValue x:TypeArguments="sc:IEnumerable">Enumerable.Range(0, 10)</CSharpValue>
    </InArgument>
  </ui:ForEach.Values>
  <ui:ForEach.Body>
    <ActivityAction x:TypeArguments="x:Int32">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="x:Int32" Name="num" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Body">
        <!-- Use "num" variable here -->
      </Sequence>
    </ActivityAction>
  </ui:ForEach.Body>
</ui:ForEach>
```

**Key rules:**
- `x:TypeArguments` on `ui:ForEach`, `ActivityAction`, and `DelegateInArgument` must ALL match the item type
- `ForEach.Values` is always `InArgument x:TypeArguments="sc:IEnumerable"` regardless of item type
- The `DelegateInArgument` `Name` is the loop variable name — usable inside the Body
- Body must contain exactly **one** activity — wrap multiple activities in a `<Sequence>`
- `CurrentIndex="{x:Null}"` is optional (stores current iteration index if set to a variable)

### While

Repeats while condition is true. No namespace prefix.

```xml
<While DisplayName="While Processing">
  <While.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">counter &lt; maxItems</CSharpValue>
    </InArgument>
  </While.Condition>
  <Sequence DisplayName="While Body">
    <!-- Activities to repeat -->
  </Sequence>
</While>
```

**Key rules:**
- Condition is `InArgument x:TypeArguments="x:Boolean"` — same as If
- Body accepts **one** child activity — wrap in `<Sequence>` for multiple
- Remember XML escaping: `<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`

### Do While

Executes body first, then checks condition. No namespace prefix.

```xml
<DoWhile DisplayName="Do While">
  <DoWhile.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">retryCount &lt; 3</CSharpValue>
    </InArgument>
  </DoWhile.Condition>
  <Sequence DisplayName="Do Body">
    <!-- Activities to repeat (executed at least once) -->
  </Sequence>
</DoWhile>
```

### Switch

Multi-branch based on an expression value. No namespace prefix.

```xml
<Switch x:TypeArguments="x:String" DisplayName="Switch on Status">
  <Switch.Expression>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">status</CSharpValue>
    </InArgument>
  </Switch.Expression>
  <Switch.Default>
    <Sequence DisplayName="Default">
      <ui:LogMessage DisplayName="Log Unknown">
        <ui:LogMessage.Message>
          <InArgument x:TypeArguments="x:Object">
            <CSharpValue x:TypeArguments="x:Object">"Unknown status"</CSharpValue>
          </InArgument>
        </ui:LogMessage.Message>
      </ui:LogMessage>
    </Sequence>
  </Switch.Default>
  <x:String x:Key="Active">
    <Sequence DisplayName="Active Case">
      <!-- Activities for "Active" -->
    </Sequence>
  </x:String>
  <x:String x:Key="Inactive">
    <Sequence DisplayName="Inactive Case">
      <!-- Activities for "Inactive" -->
    </Sequence>
  </x:String>
</Switch>
```

**Key rules:**
- `x:TypeArguments` must match the switch expression type
- Case keys use `x:Key` attribute with the matching value
- `Switch.Default` is optional but recommended
- For `x:Int32` switch: use `<x:Int32 x:Key="1">...</x:Int32>` etc.

### Try Catch

Error handling. No namespace prefix.

```xml
<TryCatch DisplayName="Try Catch">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <!-- Activities that may throw -->
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Catch">
          <ui:LogMessage DisplayName="Log Error" Level="Error">
            <ui:LogMessage.Message>
              <InArgument x:TypeArguments="x:Object">
                <CSharpValue x:TypeArguments="x:Object">exception.Message</CSharpValue>
              </InArgument>
            </ui:LogMessage.Message>
          </ui:LogMessage>
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <Sequence DisplayName="Finally">
      <!-- Cleanup activities (always runs) -->
    </Sequence>
  </TryCatch.Finally>
</TryCatch>
```

**Key rules:**
- `Catch x:TypeArguments` specifies the exception type — `s:Exception` catches all
- The `DelegateInArgument` `Name` is the exception variable (usable in the Catch body)
- Can have multiple `<Catch>` blocks for different exception types
- `TryCatch.Finally` is optional
- `s:` prefix requires `xmlns:s="clr-namespace:System;assembly=System.Private.CoreLib"`

### Throw / Rethrow

Throw an exception. No namespace prefix.

```xml
<!-- Throw a new exception -->
<Throw DisplayName="Throw Error">
  <Throw.Exception>
    <InArgument x:TypeArguments="s:Exception">
      <CSharpValue x:TypeArguments="s:Exception">new Exception("Something went wrong")</CSharpValue>
    </InArgument>
  </Throw.Exception>
</Throw>

<!-- Rethrow (only valid inside a Catch block) -->
<Rethrow DisplayName="Rethrow" />
```

### Delay

Pauses execution. No namespace prefix.

```xml
<Delay DisplayName="Wait 5 Seconds">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromSeconds(5)</CSharpValue>
    </InArgument>
  </Delay.Duration>
</Delay>

<Delay DisplayName="Wait 1 Minute">
  <Delay.Duration>
    <InArgument x:TypeArguments="s:TimeSpan">
      <CSharpValue x:TypeArguments="s:TimeSpan">TimeSpan.FromMinutes(1)</CSharpValue>
    </InArgument>
  </Delay.Duration>
</Delay>
```

### Invoke Workflow File

Calls another `.xaml` workflow. Uses `ui:` namespace prefix.

```xml
<ui:InvokeWorkflowFile DisplayName="Invoke ProcessData" WorkflowFileName="ProcessData.xaml" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="in_FilePath">
        <CSharpValue x:TypeArguments="x:String">inputPath</CSharpValue>
      </InArgument>
      <InArgument x:TypeArguments="x:Int32" x:Key="in_Count">
        <CSharpValue x:TypeArguments="x:Int32">itemCount</CSharpValue>
      </InArgument>
      <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">
        <CSharpReference x:TypeArguments="x:Boolean">wasSuccessful</CSharpReference>
      </OutArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

**Key rules:**
- `WorkflowFileName` is relative to the project root
- Arguments are passed via a `Dictionary<string, Argument>` — the `x:Key` must match the argument name in the invoked workflow
- Use `InArgument` for input, `OutArgument` for output, `InOutArgument` for bidirectional
- Requires `xmlns:scg="clr-namespace:System.Collections.Generic;assembly=System.Private.CoreLib"`

### Variables and Scoping

Variables are declared inside the `.Variables` block of their container activity:

```xml
<Sequence DisplayName="My Sequence">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="name" />
    <Variable x:TypeArguments="x:Int32" Name="counter" Default="0" />
    <Variable x:TypeArguments="x:Boolean" Name="isDone" Default="False" />
    <Variable x:TypeArguments="s:String[]" Name="items" />
    <Variable x:TypeArguments="s:DateTime" Name="startTime">
      <Variable.Default>
        <CSharpValue x:TypeArguments="s:DateTime">DateTime.Now</CSharpValue>
      </Variable.Default>
    </Variable>
    <Variable x:TypeArguments="scg:List(x:String)" Name="results">
      <Variable.Default>
        <CSharpValue x:TypeArguments="scg:List(x:String)">new List&lt;string&gt;()</CSharpValue>
      </Variable.Default>
    </Variable>
  </Sequence.Variables>
  <!-- Activities that use these variables -->
</Sequence>
```

**Common variable types:**

| Type in XAML | C# Type | xmlns prefix |
|---|---|---|
| `x:String` | `string` | `x:` (built-in) |
| `x:Int32` | `int` | `x:` |
| `x:Boolean` | `bool` | `x:` |
| `x:Double` | `double` | `x:` |
| `x:Object` | `object` | `x:` |
| `s:DateTime` | `DateTime` | `s:` |
| `s:String[]` | `string[]` | `s:` |
| `s:Exception` | `Exception` | `s:` |
| `scg:List(x:String)` | `List<string>` | `scg:` |
| `scg:Dictionary(x:String, x:Object)` | `Dictionary<string, object>` | `scg:` |

**Variable vs Argument Guidelines:**

- **Variables:** Scope-local, defined in `<Sequence.Variables>` or `<Flowchart.Variables>`
- **Arguments:** Cross-workflow, defined in `<x:Members>` at workflow root
- **Naming:** Use `in_`, `out_`, `io_` prefixes for arguments (avoid confusion)
- **Direction:** IN (read-only), OUT (write-only), IN/OUT (read-write)
- **Case Sensitive:** Argument names are case-sensitive
