# InvokeCode Activity

`ui:InvokeCode` executes inline VB.NET or C# code within a workflow. Part of `UiPath.System.Activities` (`xmlns:ui="http://schemas.uipath.com/workflow/activities"`).

InvokeCode is best suited as a quick escape hatch for simple, self-contained code. When a dedicated activity has unresolvable type issues, missing output properties, or complex configuration that resists XAML-level fixes, a few lines in InvokeCode can solve it in one pass. But if the code grows beyond a handful of lines or needs real dependencies, use a coded workflow instead.

## Language Attribute

By default, InvokeCode infers the language from the project's `expressionLanguage` setting in `project.json`, so omitting the `Language` attribute is usually fine. However, if you do set it explicitly, use the correct enum values — they differ from `project.json`:

| project.json `expressionLanguage` | InvokeCode `Language` value |
|-----------------------------------|-----------------------------|
| `"VisualBasic"` | `"VBNet"` |
| `"CSharp"` | `"CSharp"` |

**IMPORTANT:** `"VisualBasic"` is NOT a valid `Language` value — it will pass Studio validation but fail at runtime with: *"VisualBasic is not a valid value for NetLanguage"*. This is a known mismatch between project.json naming and the runtime enum.

```xml
<!-- WRONG — passes Studio validation but fails at runtime -->
<ui:InvokeCode Language="VisualBasic" Code="..." />

<!-- CORRECT — explicit language -->
<ui:InvokeCode Language="VBNet" Code="..." />

<!-- ALSO CORRECT — language inferred from project -->
<ui:InvokeCode Code="..." />
```

## XAML Structure

```xml
<ui:InvokeCode ContinueOnError="{x:Null}"
  DisplayName="My Code Block"
  sap2010:WorkflowViewState.IdRef="InvokeCode_1"
  Code="Dim result As String = &quot;hello&quot;">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <!-- Arguments here -->
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

## Arguments Dictionary

Arguments pass data between the workflow and the inline code. Each argument maps a string key (used as a variable name in the code) to an `InArgument`, `OutArgument`, or `InOutArgument`.

```xml
<ui:InvokeCode.Arguments>
  <scg:Dictionary x:TypeArguments="x:String, Argument">
    <!-- Input: workflow variable -> code variable (read-only) -->
    <InArgument x:TypeArguments="x:String" x:Key="inputUrl">[myUrlVariable]</InArgument>

    <!-- Output: code variable -> workflow variable (write-only) -->
    <OutArgument x:TypeArguments="x:String" x:Key="httpResponse">[httpResponse]</OutArgument>

    <!-- InOut: both directions -->
    <InOutArgument x:TypeArguments="x:Int32" x:Key="counter">[counter]</InOutArgument>
  </scg:Dictionary>
</ui:InvokeCode.Arguments>
```

**Rules:**
- The `x:Key` is the variable name available inside the code block
- The `[bracketValue]` binds to a workflow variable (VB projects) or use `<CSharpValue>`/`<CSharpReference>` (C# projects)
- Types must match exactly between the argument declaration and the workflow variable
- Arguments with complex types (DataTable, JObject, etc.) work the same way — just change `x:TypeArguments`

## Code Attribute Escaping

The `Code` attribute contains the full source code as an XML attribute value. XML special characters must be escaped:

| Character | Escape | Example |
|-----------|--------|---------|
| Newline | `&#xA;` | Line breaks between statements |
| `"` | `&quot;` | String literals in code |
| `&` | `&amp;` | String concatenation (VB `&`), logical AND |
| `<` | `&lt;` | Comparisons (rare in attribute form) |
| `>` | `&gt;` | Comparisons (rare in attribute form) |

**Example — VB multi-line code:**
```xml
Code="Dim x As Integer = 5&#xA;Dim y As String = &quot;hello&quot;&#xA;Console.WriteLine(x.ToString() &amp; &quot; &quot; &amp; y)"
```

Equivalent VB code:
```vb
Dim x As Integer = 5
Dim y As String = "hello"
Console.WriteLine(x.ToString() & " " & y)
```

## Good Use Cases for InvokeCode

These are the sweet spot — simple, self-contained, no external dependencies:

**Quick string/data transforms:**
```xml
Code="System.IO.File.WriteAllText(filePath, content)"
```

**DataTable row manipulation:**
```xml
Code="For Each row As DataRow In dt.Rows&#xA;    row(&quot;Column1&quot;) = row(&quot;Column1&quot;).ToString().Trim()&#xA;Next"
```

**Simple HTTP fetch (when NetHttpRequest has type issues):**
```xml
<ui:InvokeCode ContinueOnError="{x:Null}"
  DisplayName="Fetch Data via HTTP"
  sap2010:WorkflowViewState.IdRef="InvokeCode_1"
  Code="Using wc As New System.Net.WebClient()&#xA;    wc.Headers.Add(&quot;User-Agent&quot;, &quot;Mozilla/5.0&quot;)&#xA;    responseBody = wc.DownloadString(url)&#xA;End Using">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="url">[requestUrl]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="responseBody">[httpResponse]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```
**Required namespace import:** `System.Net`
**Required assembly reference:** `System.Net.WebClient`

## Code Style Guidelines

InvokeCode content must be clean, readable, and well-structured — even though it lives inside an XML attribute. Never write dense single-line code.

**Rules:**
1. **Always use multi-line code** — use `&#xA;` for line breaks. One statement per line.
2. **Add comments** — explain each logical step with VB (`'`) or C# (`//`) comments. Comments also use `&#xA;` for the preceding newline.
3. **Use descriptive variable names** — `cleaned`, `totalAmount`, `filteredRows` instead of `x`, `t`, `r`.
4. **Structure consistently** — declare variables first, then logic, then assign output arguments last.
5. **Indent with spaces** — use 2-4 spaces for blocks (For/Next, If/End If, Using/End Using) to show nesting.

**Bad — single-line, no comments, cryptic names:**
```xml
Code="o = i.Trim().ToUpper().Replace(&quot;OLD&quot;, &quot;NEW&quot;)"
```

**Good — multi-line, commented, descriptive:**
```xml
Code="' Remove leading/trailing whitespace&#xA;Dim cleaned As String = rawInput.Trim()&#xA;&#xA;' Normalize to uppercase&#xA;Dim uppercased As String = cleaned.ToUpper()&#xA;&#xA;' Apply text replacement&#xA;result = uppercased.Replace(&quot;OLD&quot;, &quot;NEW&quot;)"
```

Equivalent VB code:
```vb
' Remove leading/trailing whitespace
Dim cleaned As String = rawInput.Trim()

' Normalize to uppercase
Dim uppercased As String = cleaned.ToUpper()

' Apply text replacement
result = uppercased.Replace("OLD", "NEW")
```

**C# equivalent style:**
```xml
Code="// Remove leading/trailing whitespace&#xA;var cleaned = rawInput.Trim();&#xA;&#xA;// Normalize to uppercase&#xA;var uppercased = cleaned.ToUpper();&#xA;&#xA;// Apply text replacement&#xA;result = uppercased.Replace(&quot;OLD&quot;, &quot;NEW&quot;);"
```

## When NOT to Use InvokeCode

Stop and switch to a coded workflow when:
- The code exceeds ~15 lines — XML-escaped inline code becomes unreadable and unmaintainable
- You need NuGet packages or third-party libraries not available in the inline context
- The logic involves multiple classes, interfaces, or dependency injection
- You need unit testing or structured error handling
- The same logic is needed in multiple workflows (code reuse)
- You're doing complex API integrations with authentication, retries, pagination

## Namespace Requirements

Add to `TextExpression.NamespacesForImplementation` as needed by your code:

| Code Uses | Namespace Import |
|-----------|-----------------|
| `System.Net.WebClient` | `System.Net` |
| `System.IO.File` | `System.IO` |
| `DataTable`, `DataRow` | `System.Data` |
| `JObject`, `JArray`, `JToken` | `Newtonsoft.Json.Linq` |
| `Regex` | `System.Text.RegularExpressions` |
