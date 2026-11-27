# Variables and Scoping

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
