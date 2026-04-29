# C# Activity Binding Guide

**Scope:** XAML workflow files in projects whose `project.json` has `expressionLanguage: CSharp`. The canonical binding forms below describe how to write XAML expressions — they do **not** apply to VB XAML projects (use `[bracket]` shorthand there) and they do **not** apply to coded workflows (`.cs` files), which are plain C# and do not involve `CSharpValue` / `CSharpReference` elements at all.

Use this as a quick lookup before writing or editing XAML in a C#-expression project.

## Rule of thumb

For any activity property typed `InArgument<T>` or `OutArgument<T>`:
- **Literal value with a direct type converter** (string literal on `<String>`, enum, number, boolean, `TimeSpan`, `{x:Null}`) → attribute form is safe.
- **Anything non-literal** (variable reference, concatenation, method call, property access) → use the child-element form with `<CSharpValue>` (read) or `<CSharpReference>` (write).

The XAML attribute parser defaults to VB for expression-bearing attribute values, **regardless of the project's expression language**. At runtime, the VB JIT is disabled on non-Legacy projects — so attribute-form expressions fail with `JIT compilation is disabled for non-Legacy projects`. See [csharp-expression-pitfalls.md](csharp-expression-pitfalls.md).

## Property-surface sourcing

Which properties exist on a given activity, the `<Activity>.md` lookup order, and how to handle `Cannot set unknown member` errors caused by property-name drift between package versions: see [xaml-basics-and-rules.md § Activity Property Surface](xaml-basics-and-rules.md#activity-property-surface-and-starter-xaml). The 5-step workflow there applies to both VB and C# XAML projects — the binding tables below assume you have already established the property surface from `<Activity>.md`.

## Binding forms by property type

| Property type | Attribute form (literal only) | Child-element form (expression) |
|---|---|---|
| `InArgument<String>` | Literal: `Foo="hello"` | `<InArgument x:TypeArguments="x:String"><CSharpValue x:TypeArguments="x:String">expr</CSharpValue></InArgument>` |
| `InArgument<Object>` | Not safe — `Object` has no direct type converter | `<InArgument x:TypeArguments="x:Object"><CSharpValue x:TypeArguments="x:Object">expr</CSharpValue></InArgument>` |
| `InArgument<Boolean>` | Literal: `Foo="True"` | `<InArgument x:TypeArguments="x:Boolean"><CSharpValue x:TypeArguments="x:Boolean">a &gt; b</CSharpValue></InArgument>` |
| `InArgument<Int32>` / numeric | Literal: `Timeout="30"` | `<InArgument x:TypeArguments="x:Int32"><CSharpValue x:TypeArguments="x:Int32">expr</CSharpValue></InArgument>` |
| `InArgument<TimeSpan>` | Literal: `Duration="00:00:02"` — never bracket form | Rare |
| `InArgument<TEnum>` | Literal: `Level="Info"`, `MouseButton="Left"` | Rare |
| `OutArgument<T>` | Often rejected — use child element | `<OutArgument x:TypeArguments="x:String"><CSharpReference x:TypeArguments="x:String">var</CSharpReference></OutArgument>` |
| Plain `string` (not `InArgument<String>`) | Literal: `WorkflowFileName="path.xaml"` | — |
| Complex objects (`TargetAnchorable`, `ActivityAction`, dictionaries) | — | Always child element |

**Type-class mistakes:**

- `InArgument<Object>` (e.g. `LogMessage.Message`) — writing `<InArgument x:TypeArguments="x:String">` instead of `x:Object` fails validation.
- `OutArgument<T>` writeback — attribute form (`Result="[var]"`) fails with `Failed to create a '<Prop>' from the text '...'`. Use child element with `<CSharpReference>`.
- `OutArgument` / `InOutArgument` on `InvokeWorkflowFile.Arguments` — must be a variable reference (lvalue), not a constructed expression. See [§ OutArgument Bindings Must Be Variable References](common-pitfalls.md#outargument-bindings-must-be-variable-references).
- Empty `<InArgument x:TypeArguments="x:String"></InArgument>` — passes per-file `get-errors` but fails project `analyze` with `Value for a required activity argument 'Value' was not supplied`. Use `[String.Empty]`. See [§ Empty Argument Values](common-pitfalls.md#empty-argument-values).
- Plain `string` (e.g. `InvokeWorkflowFile.WorkflowFileName`) — wrap in `[brackets]` or `&quot;...&quot;` and Studio silently breaks path resolution. Use the literal path. See [§ WorkflowFileName Must Be a Plain String Path](common-pitfalls.md#workflowfilename-must-be-a-plain-string-path).

## Recipes

### LogMessage with a C# expression

```xml
<ui:LogMessage DisplayName="Log status" Level="Info">
  <ui:LogMessage.Message>
    <InArgument x:TypeArguments="x:Object">
      <CSharpValue x:TypeArguments="x:Object">"Todo count now: " + statusText</CSharpValue>
    </InArgument>
  </ui:LogMessage.Message>
</ui:LogMessage>
```

**Common mistake:** `<InArgument x:TypeArguments="x:String">` — `Message` is `Object`, not `String`. `x:Object` is required.

### Get Text → variable

```xml
<uix:NGetText DisplayName="Read status" HealingAgentBehavior="SameAsCard">
  <uix:NGetText.Target>
    <uix:TargetAnchorable .../>
  </uix:NGetText.Target>
  <uix:NGetText.TextString>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">statusText</CSharpReference>
    </OutArgument>
  </uix:NGetText.TextString>
</uix:NGetText>
```

**Scoping requirement:** when `NGetText` sits inside `<uix:NApplicationCard.Body><ActivityAction><Sequence>`, the `statusText` variable must be declared on that inner `Sequence.Variables`, not on an outer one crossing the `ActivityAction` boundary — otherwise runtime throws `ThrowIfNotInTree`. See [csharp-expression-pitfalls.md](csharp-expression-pitfalls.md#throwifnotintree--variable-declared-outside-the-activityaction-scope).

### Assign with a C# expression

```xml
<Assign DisplayName="Compose message">
  <Assign.To>
    <OutArgument x:TypeArguments="x:String">
      <CSharpReference x:TypeArguments="x:String">logMessage</CSharpReference>
    </OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">"Added: " + todoText</CSharpValue>
    </InArgument>
  </Assign.Value>
</Assign>
```

### StartProcess with a composed path

```xml
<ui:StartProcess DisplayName="Start server">
  <ui:StartProcess.FileName>
    <InArgument x:TypeArguments="x:String">
      <CSharpValue x:TypeArguments="x:String">System.Environment.GetEnvironmentVariable("LOCALAPPDATA") + @"\MyApp\start.cmd"</CSharpValue>
    </InArgument>
  </ui:StartProcess.FileName>
</ui:StartProcess>
```

### If with a boolean expression

```xml
<If DisplayName="Check count">
  <If.Condition>
    <InArgument x:TypeArguments="x:Boolean">
      <CSharpValue x:TypeArguments="x:Boolean">count &gt; 0</CSharpValue>
    </InArgument>
  </If.Condition>
  <If.Then>
    <Sequence>
      <!-- ... -->
    </Sequence>
  </If.Then>
</If>
```

> **XAML escaping:** `<`, `>`, `&`, `"` must be escaped inside `<CSharpValue>` element content (`&lt;`, `&gt;`, `&amp;`, `&quot;`).
