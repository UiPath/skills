# Assign

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
