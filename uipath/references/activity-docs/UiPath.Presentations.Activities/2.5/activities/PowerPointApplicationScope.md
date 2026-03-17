## PowerPointApplicationScope — Required Scope Container

**ALL PowerPoint activities must be nested inside `PowerPointApplicationScope`.** There is no standalone mode.

The scope body passes an `IPresentationQuickHandle` as a delegate argument (conventionally named `PowerPoint`). All nested activities use this handle via their `Presentation` attribute.

```xml
<p:PowerPointApplicationScope
    AutoSave="True"
    CreateIfNotExists="False"
    DisplayName="Use PowerPoint file"
    PresentationPath="[presentationPath]"
    ReadOnly="False"
    SensitivityOperation="None"
    UseThemeFile="False"
    Visible="True">
  <p:PowerPointApplicationScope.Body>
    <ActivityAction x:TypeArguments="p1:IPresentationQuickHandle">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="p1:IPresentationQuickHandle" Name="PowerPoint" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <!-- nested p: PowerPoint activities here -->
      </Sequence>
    </ActivityAction>
  </p:PowerPointApplicationScope.Body>
</p:PowerPointApplicationScope>
```

Key attributes:
- `PresentationPath` — path to the `.pptx` file
- `AutoSave` — `True` to save automatically on scope close
- `CreateIfNotExists` — `True` to create the file if it doesn't exist
- `ReadOnly` — `True` to open in read-only mode
- `SensitivityOperation` — typically `"None"`
- `Visible` — `True` to show the PowerPoint window
- `UseThemeFile` — `False` by default; `True` to apply a custom theme
- The delegate argument name is `"PowerPoint"` by convention (type `IPresentationQuickHandle`)

**Slide indexing is 1-based** (first slide = index 1).
