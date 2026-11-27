# WordApplicationScope — Required Scope Container

**ALL Word activities must be nested inside `WordApplicationScope`.** There is no standalone mode.

```xml
<p:WordApplicationScope
    AutoSave="True"
    CreateNewFile="False"
    DisplayName="Use Word file"
    FilePath="[wordFilePath]"
    ReadOnly="False"
    SensitivityOperation="None">
  <p:WordApplicationScope.Body>
    <ActivityAction x:TypeArguments="ui:WordDocument">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ui:WordDocument" Name="WordDocumentScope" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested p: Word activities here -->
      </Sequence>
    </ActivityAction>
  </p:WordApplicationScope.Body>
</p:WordApplicationScope>
```

Key attributes:
- `FilePath` — path to the `.docx` file
- `AutoSave` — `True` to save automatically on close
- `CreateNewFile` — `True` to create the file if it doesn't exist
- `ReadOnly` — `True` to open in read-only mode
- `SensitivityOperation` — typically `"None"`
- The delegate argument name is `"WordDocumentScope"` by convention
