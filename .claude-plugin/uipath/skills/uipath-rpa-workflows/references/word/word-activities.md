# XAML Word Document Activities

Word document activity patterns for `UiPath.Word.Activities`. Always get full XAML from `uipcli rpa get-default-activity-xaml` — this file covers confirmed patterns from real workflows only.

**Target:** Windows only (not Cross-platform / Studio Web Portable).

## Package

`UiPath.Word.Activities`

## WordApplicationScope — Required Scope Container

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
    <ActivityAction x:TypeArguments="p1:WordDocument">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="p1:WordDocument" Name="WordDocumentScope" />
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

## Activities Inside WordApplicationScope

All activities below must be placed inside the `WordApplicationScope` body `Sequence`.

### WordReadText

Reads all text content from the Word document.

```xml
<p:WordReadText
    DisplayName="Read Text"
    Text="[documentText]" />
```

- `Text` — output `String` variable containing the document's text content

### WordAppendText

Appends text to the end of the document.

```xml
<p:WordAppendText
    DisplayName="Append Text"
    NewLine="True"
    Text="[&quot;New paragraph to append&quot;]" />
```

- `Text` — string expression with the text to append
- `NewLine` — `True` to add a new line before the text

### WordReplaceText

Finds and replaces text within the document.

```xml
<p:WordReplaceText
    DisplayName="Replace Text"
    Found="[wasFound]"
    Replace="[&quot;NewValue&quot;]"
    ReplaceAll="True"
    Search="[&quot;OldValue&quot;]" />
```

- `Search` — string expression for the text to find
- `Replace` — string expression for the replacement text
- `ReplaceAll` — `True` to replace all occurrences; `False` for first occurrence only
- `Found` — output `Boolean` variable indicating whether the search text was found

### WordExportToPdf

Exports the Word document to a PDF file.

```xml
<p:WordExportToPdf
    DisplayName="Export to PDF"
    FilePath="[pdfOutputPath]"
    ReplaceExisting="True" />
```

- `FilePath` — output PDF file path (string expression)
- `ReplaceExisting` — `True` to overwrite an existing file at the path

### WordAddImage

Inserts an image into the document.

```xml
<p:WordAddImage
    DisplayName="Add Image"
    Height="100"
    ImagePath="[imagePath]"
    Width="150" />
```

- `ImagePath` — path to the image file
- `Width`, `Height` — dimensions in points (numeric expressions)

### WordInsertDataTable

Inserts a `DataTable` into the Word document as a table.

```xml
<p:WordInsertDataTable
    DataTable="[dtData]"
    DisplayName="Insert Data Table" />
```

- `DataTable` — `System.Data.DataTable` variable to insert

### WordSetBookmark

Sets the text content of a named bookmark in the document.

```xml
<p:WordSetBookmark
    BookmarkName="[&quot;InvoiceNumber&quot;]"
    DisplayName="Set Bookmark"
    Text="[invoiceNumberValue]" />
```

- `BookmarkName` — name of the bookmark defined in the Word document
- `Text` — string expression for the bookmark's new content

### WordSaveAs

Saves the document under a new file path.

```xml
<p:WordSaveAs
    DisplayName="Save As"
    FilePath="[newFilePath]" />
```

- `FilePath` — new file path (string expression) for the saved copy

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
    <ActivityAction x:TypeArguments="p1:WordDocument">
      <ActivityAction.Argument>
        <DelegateInArgument x:TypeArguments="p1:WordDocument" Name="WordDocumentScope" />
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
| Scope body type | `ActivityAction x:TypeArguments="p1:WordDocument"` with `DelegateInArgument Name="WordDocumentScope"` |
| Template replacement | Use `WordReplaceText` with `ReplaceAll="True"` and placeholder tokens like `{{FieldName}}` |
| Export to PDF | Use `WordExportToPdf` inside scope; set `ReplaceExisting="True"` to overwrite |
| Save vs SaveAs | `AutoSave="True"` on scope saves on close; use `WordSaveAs` to save to a different path |
| Windows only | `UiPath.Word.Activities` does not support Cross-platform / Studio Web Portable target |
| Full XAML | Always use `uipcli rpa get-default-activity-xaml` for complete activity XAML |
