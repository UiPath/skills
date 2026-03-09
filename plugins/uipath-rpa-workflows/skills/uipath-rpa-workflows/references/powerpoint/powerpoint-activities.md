# XAML PowerPoint Presentation Activities

PowerPoint activity patterns for `UiPath.Presentations.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

**Target:** Windows only (not Cross-platform / Studio Web Portable).

## Package

`UiPath.Presentations.Activities`

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

## Activities Inside PowerPointApplicationScope

All activities must be placed inside the scope body. All require a `Presentation` attribute bound to the `IPresentationQuickHandle` delegate argument.

### InsertTextInPresentation

Inserts or replaces text in a named shape/placeholder on a slide.

```xml
<p:InsertTextInPresentation
    ClearExistingText="False"
    DisplayName="Insert Text"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Content Holder&quot;]"
    SlideIndex="[slideIndex]"
    Text="[textToInsert]" />
```

- `SlideIndex` — 1-based slide number
- `ShapeName` — name of the shape/placeholder as defined in the slide
- `ClearExistingText` — `True` to clear the shape before inserting

### FindAndReplaceTextInPresentation

Finds and replaces text across the entire presentation.

```xml
<p:FindAndReplaceTextInPresentation
    DisplayName="Find and Replace Text"
    MatchCase="False"
    NumberOfReplacements="[replacementCount]"
    Presentation="[PowerPoint]"
    ReplaceAll="True"
    ReplaceWith="[&quot;NewValue&quot;]"
    SearchFor="[&quot;OldValue&quot;]"
    WholeWordsOnly="False" />
```

- `SearchFor` / `ReplaceWith` — string expressions
- `NumberOfReplacements` — output `Int32` count of replacements made

### ReplaceShapeWithMedia

Replaces a shape/placeholder with an image or video file.

```xml
<p:ReplaceShapeWithMedia
    DisplayName="Insert Image"
    Media="[imagePath]"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Picture Holder&quot;]"
    SlideIndex="[slideIndex]" />
```

- `Media` — file path to the image or video
- `ShapeName` — name of the target shape/placeholder

### ReplaceShapeWithDataTable

Inserts a `DataTable` as a table into a shape/placeholder.

```xml
<p:ReplaceShapeWithDataTable
    AppendMode="CreateNewTable"
    DisplayName="Insert Table"
    ExcludeHeaders="False"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Table Holder&quot;]"
    SlideIndex="[slideIndex]"
    StartColumn="1"
    StartRow="0"
    TableToInsert="[dtData]" />
```

- `TableToInsert` — `System.Data.DataTable` variable
- `AppendMode` — `"CreateNewTable"` to create a new table in the shape
- `ExcludeHeaders` — `True` to skip the header row
- `StartRow` — 0-based starting row; `StartColumn` — 1-based starting column

### InsertSlide

Inserts a new slide into the presentation.

```xml
<p:InsertSlide
    DisplayName="Insert Slide"
    InsertType="End"
    InsertedAtPosition="[newSlideIndex]"
    LayoutName="[&quot;(default)&quot;]"
    Presentation="[PowerPoint]"
    SlideMasterName="[&quot;(default)&quot;]" />
```

- `InsertType` — `"End"`, `"Beginning"`, etc.
- `InsertedAtPosition` — output `Int32` with the newly inserted slide's index
- `LayoutName`, `SlideMasterName` — layout/master to use (use `"(default)"`)

### DeleteSlide

Deletes a slide by 1-based index.

```xml
<p:DeleteSlide
    DeletePosition="[slideIndex]"
    DisplayName="Delete Slide"
    Presentation="[PowerPoint]" />
```

### CopyPasteSlide

Copies (or moves) a slide within or between presentations.

```xml
<p:CopyPasteSlide
    DisplayName="Copy Slide"
    DestinationPresentation="[PowerPoint]"
    Move="False"
    SlideToInsert="[destinationIndex]"
    SlideToCopy="[sourceIndex]"
    SourcePresentation="[PowerPoint]" />
```

- `SlideToCopy` — 1-based source slide index; `SlideToInsert` — 1-based destination index
- `Move` — `True` to cut+paste instead of copy
- `SourcePresentation` and `DestinationPresentation` can be the same handle for within-file copies

### PasteIntoSlide

Pastes clipboard content into a shape/placeholder.

```xml
<p:PasteIntoSlide
    DisplayName="Paste Into Slide"
    Presentation="[PowerPoint]"
    ShapeName="[&quot;Content Holder&quot;]"
    SlideIndex="[slideIndex]" />
```

### SavePresentationFileAs

Saves the presentation under a new file path or format.

```xml
<p:SavePresentationFileAs
    DisplayName="Save Presentation As"
    FilePath="[outputPath]"
    Presentation="[PowerPoint]"
    ReplaceExisting="True"
    SaveAsFileType="XmlPresentation" />
```

- `SaveAsFileType` — `"XmlPresentation"` for standard `.pptx` format
- `ReplaceExisting` — `True` to overwrite an existing file

### SavePresentationAsPdf

Exports the presentation as a PDF.

```xml
<p:SavePresentationAsPdf
    DisplayName="Save as PDF"
    PdfPath="[pdfOutputPath]"
    Presentation="[PowerPoint]"
    ReplaceExisting="True" />
```

- `PdfPath` — output PDF file path
- `ReplaceExisting` — `True` to overwrite existing file

### RunMacro

Executes a VBA macro in the presentation. Arguments are passed via nested `RunMacroArgument` children.

```xml
<p:RunMacro
    DisplayName="Run Macro"
    MacroName="[&quot;MacroName&quot;]"
    Presentation="[PowerPoint]"
    Result="[macroResult]">
  <p:RunMacro.Body>
    <ActivityAction>
      <Sequence DisplayName="Arguments">
        <p:RunMacroArgument ArgumentValue="[&quot;arg1&quot;]" DisplayName="Argument 1" />
        <p:RunMacroArgument ArgumentValue="[&quot;arg2&quot;]" DisplayName="Argument 2" />
      </Sequence>
    </ActivityAction>
  </p:RunMacro.Body>
</p:RunMacro>
```

- `MacroName` — VBA function name
- `Result` — output `String` variable with macro return value
- Body contains one `RunMacroArgument` per argument

## Full Example: Open, Update, and Export

```xml
<p:PowerPointApplicationScope
    AutoSave="False"
    CreateIfNotExists="False"
    DisplayName="Use PowerPoint file"
    PresentationPath="[templatePath]"
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
        <p:FindAndReplaceTextInPresentation
            DisplayName="Replace Title"
            Presentation="[PowerPoint]"
            ReplaceAll="True"
            ReplaceWith="[reportTitle]"
            SearchFor="[&quot;{{Title}}&quot;]" />
        <p:ReplaceShapeWithMedia
            DisplayName="Insert Logo"
            Media="[logoPath]"
            Presentation="[PowerPoint]"
            ShapeName="[&quot;Logo Holder&quot;]"
            SlideIndex="1" />
        <p:SavePresentationAsPdf
            DisplayName="Export PDF"
            PdfPath="[outputPdfPath]"
            Presentation="[PowerPoint]"
            ReplaceExisting="True" />
      </Sequence>
    </ActivityAction>
  </p:PowerPointApplicationScope.Body>
</p:PowerPointApplicationScope>
```

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Scope required | ALL PowerPoint activities must be inside `PowerPointApplicationScope` — no standalone activities |
| Scope body type | `ActivityAction x:TypeArguments="p1:IPresentationQuickHandle"` with `DelegateInArgument Name="PowerPoint"` |
| Slide indexing | 1-based (first slide = index 1) |
| Shape targeting | Use `ShapeName` to target named shapes/placeholders; names come from the actual presentation |
| Template replacement | Use `FindAndReplaceTextInPresentation` with `ReplaceAll="True"` and placeholder tokens like `{{FieldName}}` |
| Insert image | Use `ReplaceShapeWithMedia` with the placeholder name and image file path |
| Insert table | Use `ReplaceShapeWithDataTable`; `DataTable` rows map to table rows in the slide |
| Export to PDF | Use `SavePresentationAsPdf` inside scope; set `ReplaceExisting="True"` to overwrite |
| Save vs SaveAs | `AutoSave="True"` on scope saves on close; use `SavePresentationFileAs` to save to a different path/format |
| Macros | Use `RunMacro` with nested `RunMacroArgument` children for each argument |
| Windows only | `UiPath.Presentations.Activities` does not support Cross-platform / Studio Web Portable target |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
