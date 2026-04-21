# C# Activity Binding Cheatsheet

Canonical binding forms for common activity properties when `expressionLanguage` is `CSharp`. Use this as a quick lookup before writing C# XAML.

## Rule of thumb

For any activity property typed `InArgument<T>` or `OutArgument<T>`:
- **Literal value with a direct type converter** (string literal on `<String>`, enum, number, boolean, `TimeSpan`, `{x:Null}`) → attribute form is safe.
- **Anything non-literal** (variable reference, concatenation, method call, property access) → use the child-element form with `<CSharpValue>` (read) or `<CSharpReference>` (write).

The XAML attribute parser defaults to VB for expression-bearing attribute values, **regardless of the project's expression language**. At runtime, the VB JIT is disabled on non-Legacy projects — so attribute-form expressions fail with `JIT compilation is disabled for non-Legacy projects`. See [common-pitfalls.md § C# Attribute-Form Expressions Are Parsed as VB](common-pitfalls.md#c-attribute-form-expressions-are-parsed-as-vb--jit-failure-at-runtime).

## Binding forms per common property

| Activity | Property | Type | Canonical C# form |
|---|---|---|---|
| `ui:LogMessage` | `Message` | `InArgument<Object>` | Child element — see recipe below |
| `ui:LogMessage` | `Level` | enum | Attribute: `Level="Info"` |
| `ui:WriteLine` | `Text` | `InArgument<String>` | Attribute (literal) or child element (expression) |
| `ui:StartProcess` | `FileName` | `InArgument<String>` | Child element for env-var / composed paths |
| `ui:StartProcess` | `Arguments` | `InArgument<String>` | Attribute for literals, child element for expressions |
| `Delay` | `Duration` | `InArgument<TimeSpan>` | Attribute: `Duration="00:00:02"` — never brackets |
| `Assign` | `To` | `OutArgument<T>` | Child element `<Assign.To>` with `<OutArgument>` + `<CSharpReference>` |
| `Assign` | `Value` | `InArgument<T>` | Child element `<Assign.Value>` with `<InArgument>` + `<CSharpValue>` |
| `If` | `Condition` | `InArgument<Boolean>` | Child element with `<CSharpValue x:TypeArguments="x:Boolean">` |
| `uix:NTypeInto` | `Text` | `InArgument<String>` | Attribute for literals; child element for variables |
| `uix:NTypeInto` | `Target` | `TargetAnchorable` | Child element `<uix:NTypeInto.Target>` — see [uia-target-attachment-guide.md](../uia-target-attachment-guide.md) |
| `uix:NClick` | `Target` | `TargetAnchorable` | Child element `<uix:NClick.Target>` |
| `uix:NClick` | `ClickType` | enum | Attribute: `ClickType="Single"` |
| `uix:NClick` | `MouseButton` | enum | Attribute: `MouseButton="Left"` |
| `uix:NGetText` | `Target` | `TargetAnchorable` | Child element `<uix:NGetText.Target>` |
| `uix:NGetText` | `TextString` | `OutArgument<String>` | Child element — attribute form fails with `Failed to create a 'TextString' from the text '…'` |
| `uix:NApplicationCard` | `TargetApp` | `TargetApp` | Child element `<uix:NApplicationCard.TargetApp>` |
| `uix:NApplicationCard` | `OpenMode` | enum | Attribute: `OpenMode="Always"` |
| `uix:NApplicationCard` | `CloseMode` | enum | Attribute: `CloseMode="Never"` |
| `ui:InvokeWorkflowFile` | `WorkflowFileName` | plain `string` | Attribute with literal path — see [common-pitfalls.md § WorkflowFileName Must Be a Plain String Path](common-pitfalls.md#workflowfilename-must-be-a-plain-string-path) |

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

**Scoping requirement:** when `NGetText` sits inside `<uix:NApplicationCard.Body><ActivityAction><Sequence>`, the `statusText` variable must be declared on that inner `Sequence.Variables`, not on an outer one crossing the `ActivityAction` boundary — otherwise runtime throws `ThrowIfNotInTree`. See [common-pitfalls.md § ThrowIfNotInTree](common-pitfalls.md#throwifnotintree--out-argument-not-attached-at-runtime).

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
