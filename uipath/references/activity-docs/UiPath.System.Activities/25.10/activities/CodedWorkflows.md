# Coded Workflows (via uipath-coded-workflows skill)

For anything beyond simple inline snippets, use **coded workflows** — full C# files (`.cs`) that inherit from `CodedWorkflow` and are managed by the `uipath-coded-workflows` skill.

**Invoke the `uipath-coded-workflows` skill** for creating, editing, or managing coded workflow files. That skill handles:
- Project initialization and configuration (`project.json`, dependencies)
- Creating `.cs` workflow files with proper `[Workflow]` attributes and `.cs.json` metadata
- Service injection (`excel`, `mail`, `uiAutomation`, etc.) via NuGet package dependencies
- Coded Source Files (helper classes, models, utilities — plain C# without `CodedWorkflow` base)
- Validation, building, and running coded workflows
- Test case creation with `[TestCase]` attributes

## Invoking a Coded Workflow from XAML

Once a coded workflow `.cs` file exists in the project, invoke it from an XAML workflow using `ui:InvokeWorkflowFile` — the same activity used to call other `.xaml` workflows. Point `WorkflowFileName` at the `.cs` file:

```xml
<ui:InvokeWorkflowFile WorkflowFileName="MyCodedWorkflow.cs" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="in_FilePath">
        <CSharpValue x:TypeArguments="x:String">inputPath</CSharpValue>
      </InArgument>
      <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">
        <CSharpReference x:TypeArguments="x:Boolean">wasSuccessful</CSharpReference>
      </OutArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

For VB projects, use bracket syntax for argument bindings instead of `CSharpValue`/`CSharpReference`:
```xml
<InArgument x:TypeArguments="x:String" x:Key="in_FilePath">[inputPath]</InArgument>
<OutArgument x:TypeArguments="x:Boolean" x:Key="out_Success">[wasSuccessful]</OutArgument>
```

**Key points:**
- `WorkflowFileName` is relative to the project root — use the `.cs` file path (e.g., `"Workflows/ProcessData.cs"`)
- Arguments are passed via the same `Dictionary<string, Argument>` pattern as XAML-to-XAML invocation
- The `x:Key` must match the argument name defined in the coded workflow's `.cs.json` metadata
- The coded workflow's `Execute` method receives arguments and returns outputs through the standard `CodedWorkflow` mechanism

## When to Use Coded Workflows

- Complex business logic (validation rules, data transformations, calculations)
- API integrations requiring HttpClient, authentication, retry logic, pagination
- Code that needs NuGet packages (e.g., `Newtonsoft.Json`, `CsvHelper`, `Dapper`)
- Reusable logic shared across multiple XAML workflows
- Logic that benefits from unit testing
- Working with custom models, DTOs, or complex data structures
- Anything where XML-escaped inline code becomes a liability
