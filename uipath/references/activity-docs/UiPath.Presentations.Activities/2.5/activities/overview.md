# XAML PowerPoint Presentation Activities

PowerPoint activity patterns for `UiPath.Presentations.Activities`. Always get full XAML from `uip rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

**Target:** Windows only (not Cross-platform / Studio Web Portable).

## Package

`UiPath.Presentations.Activities`

## Scope Requirement

**ALL PowerPoint activities must be nested inside `PowerPointApplicationScope`.** There is no standalone mode.

The scope body passes an `IPresentationQuickHandle` as a delegate argument (conventionally named `PowerPoint`). All nested activities use this handle via their `Presentation` attribute.

**Slide indexing is 1-based** (first slide = index 1).

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
| Full XAML | Always use `uip rpa get-default-activity-xaml` for complete activity XAML |
