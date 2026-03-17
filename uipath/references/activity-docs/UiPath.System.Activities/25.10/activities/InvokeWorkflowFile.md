# Invoke Workflow File

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
