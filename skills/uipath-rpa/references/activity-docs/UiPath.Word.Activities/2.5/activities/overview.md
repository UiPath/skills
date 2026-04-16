# XAML Word Document Activities

Word document activity patterns for `UiPath.Word.Activities`. Always get full XAML from `uip rpa get-default-activity-xaml --use-studio` — this file covers confirmed patterns from real workflows only.

**Target:** Windows only (not Cross-platform / Studio Web Portable).

## Package

`UiPath.Word.Activities`

## Namespace Declarations

Word activities use **URI-based XML namespaces**, not CLR-based ones. Using CLR namespaces (e.g., `clr-namespace:UiPath.Word.Activities;assembly=UiPath.Word.Activities`) will cause "Could not find type" errors even when the package is installed.

**Required namespace declarations:**

| Prefix | URI | Purpose |
|--------|-----|---------|
| `p` | `http://schemas.uipath.com/workflow/activities/word` | All Word activities (`WordApplicationScope`, `WordAppendText`, etc.) |
| `ui` | `http://schemas.uipath.com/workflow/activities` | `WordDocument` type used in scope body `ActivityAction`/`DelegateInArgument` |

```xml
xmlns:p="http://schemas.uipath.com/workflow/activities/word"
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

**CRITICAL:** The `WordDocument` type lives under the `ui:` prefix (`http://schemas.uipath.com/workflow/activities`), NOT under the `p:` Word namespace. This means `ActivityAction x:TypeArguments="ui:WordDocument"`, not `p:WordDocument` or `ui:WordDocument`.

## Full Example: Generate Report with Text and Data Table

```xml
<!-- Delete existing file to start fresh -->
<ui:Delete DisplayName="Delete existing report" Path="[reportPath]" ContinueOnError="True" />

<p:WordApplicationScope
    AutoSave="True"
    CreateNewFile="True"
    DisplayName="Write report"
    FilePath="[reportPath]"
    ReadOnly="False"
    SensitivityOperation="None">
  <p:WordApplicationScope.Body>
    <ActivityAction x:TypeArguments="ui:WordDocument">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ui:WordDocument" Name="WordDocumentScope" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <p:WordAppendText DisplayName="Append Summary" NewLine="True" Text="[summaryText]" />
        <p:WordInsertDataTable DataTable="[dtFormatted]" DisplayName="Insert Data Table"
            InsertRelativeTo="Document" Position="End" />
      </Sequence>
    </ActivityAction>
  </p:WordApplicationScope.Body>
</p:WordApplicationScope>
```

## Full Example: Replace and Export Workflow

```xml
<p:WordApplicationScope
    AutoSave="False"
    CreateNewFile="False"
    DisplayName="Use Word file"
    FilePath="[templatePath]"
    ReadOnly="False"
    SensitivityOperation="None">
  <p:WordApplicationScope.Body>
    <ActivityAction x:TypeArguments="ui:WordDocument">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="ui:WordDocument" Name="WordDocumentScope" />
      </ActivityAction.Argument>
      <Sequence DisplayName="Do">
        <p:WordReplaceText
            DisplayName="Replace Invoice Number"
            Found="[wasFound]"
            Replace="[invoiceNumber]"
            ReplaceAll="True"
            Search="[&quot;{{InvoiceNumber}}&quot;]" />
        <p:WordReplaceText
            DisplayName="Replace Date"
            Found="[wasFound]"
            Replace="[invoiceDate.ToString(&quot;yyyy-MM-dd&quot;)]"
            ReplaceAll="True"
            Search="[&quot;{{InvoiceDate}}&quot;]" />
        <p:WordExportToPdf
            DisplayName="Export to PDF"
            FilePath="[outputPdfPath]"
            ReplaceExisting="True" />
      </Sequence>
    </ActivityAction>
  </p:WordApplicationScope.Body>
</p:WordApplicationScope>
```

## Key Patterns

| Pattern | Notes |
|---------|-------|
| Scope required | ALL Word activities must be inside `WordApplicationScope` — no standalone activities |
| Scope body type | `ActivityAction x:TypeArguments="ui:WordDocument"` — `WordDocument` is under `ui:`, NOT the `p:` Word namespace |
| URI namespaces required | Use `xmlns:p="http://schemas.uipath.com/workflow/activities/word"` — CLR-based namespaces (`clr-namespace:...`) cause "Could not find type" errors |
| Fresh file on each run | `CreateNewFile="True"` does NOT overwrite existing files — it appends. Always delete the file first with `ui:Delete` (`ContinueOnError="True"`) before `WordApplicationScope` to avoid stale content accumulation |
| DataTable position | `WordInsertDataTable` defaults to `Position="Start"` — use `Position="End"` when inserting after other content to avoid collisions |
| Format DataTable for Word | Create a string-column copy of your DataTable with pre-formatted values (`"$1,234.56"`, `"+2.50%"`, `"40.1M"`) — raw numeric columns produce ugly unreadable output |
| Template replacement | Use `WordReplaceText` with `ReplaceAll="True"` and placeholder tokens like `{{FieldName}}` |
| Export to PDF | Use `WordExportToPdf` inside scope; set `ReplaceExisting="True"` to overwrite |
| Save vs SaveAs | `AutoSave="True"` on scope saves on close; use `WordSaveAs` to save to a different path |
| Windows only | `UiPath.Word.Activities` does not support Cross-platform / Studio Web Portable target |
| Full XAML | Always use `uip rpa get-default-activity-xaml --use-studio` for complete activity XAML |
