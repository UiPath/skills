# Convert HTML to PDF

`UiPath.PDF.Activities.PDF.NetCore.ConvertHtmlToPDF`

Converts HTML content to a PDF file. The HTML can be supplied as an inline string or read from a local file, controlled by the **Input mode** selector. Optional header, footer, paper size, margin, scale, and background settings allow full control over the rendered output.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name   | Display Name | Kind         | Type     | Required | Default | Placeholder | Description                                                                  |
| ------ | ------------ | ------------ | -------- | -------- | ------- | ----------- | ---------------------------------------------------------------------------- |
| `Html` | HTML content | `InArgument` | `string` | Yes† | | | The HTML string to convert to PDF. Visible when **Input mode** is `Content`. |
| `FileName` | File (local path) | `InArgument` | `string` | Yes* | | | Local path to an HTML file to convert. Visible when **Input mode** is `File`. Mutually exclusive with `ResourceFile`. |
| `ResourceFile` | File | `InArgument` | `IResource` | Yes* | | | A file resource handle pointing to the HTML file to convert. Visible when **Input mode** is `File`. Mutually exclusive with `FileName`. |

> *†Required when `InputMode` is `Content`. \*Exactly one of `FileName` or `ResourceFile` is required when `InputMode` is `File` (`[OverloadGroup]`).*

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `InputMode` | Input mode | `ItemInputMode` | `Content` | Selects whether the HTML source is an inline string (`Content`) or a file (`File`). Controls which input properties are visible. |
| `PaperSize` | Paper Size | `InArgument<PdfPaperSize>` | `A4` | The paper size used for the PDF output. |
| `Margin` | Margin | `InArgument<int>` | `0` | Page margin in points. |
| `Scale` | Scale | `InArgument<double>` | `1.0` | Page rendering scale. Must be between 0.1 and 2 inclusive. |
| `KeepBackground` | Keep Background | `InArgument<bool>` | `true` | Whether to preserve background color and graphics during conversion. |
| `HeaderHtml` | Html Header Content | `InArgument<string>` | | An HTML document to use as a page header template. Visible when **Header input mode** is `Content`. |
| `HeaderInputMode` | Header input mode | `ItemInputMode` | `Content` | Selects whether the header source is an inline string or a file. |
| `FooterHtml` | Html Footer Content | `InArgument<string>` | | An HTML document to use as a page footer template. Visible when **Footer input mode** is `Content`. |
| `FooterInputMode` | Footer input mode | `ItemInputMode` | `Content` | Selects whether the footer source is an inline string or a file. |
| `OutputFileName` | Output File Path | `InArgument<string>` | | Full path of the output PDF file. If not specified, a default file name is generated. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The resulting PDF file as a local resource. |

## Valid Configurations

**Mode 1 — Inline HTML content (default):**
Set `InputMode` to `Content` and provide the `Html` string. `FileName` and `ResourceFile` are hidden.

**Mode 2 — HTML from a local file path:**
Set `InputMode` to `File` and provide `FileName`. `Html` is hidden. `FileName` and `ResourceFile` are mutually exclusive (`[OverloadGroup]`).

**Mode 3 — HTML from a file resource:**
Set `InputMode` to `File` and provide `ResourceFile`. `Html` is hidden.

The same three modes apply independently to `HeaderInputMode` and `FooterInputMode`.

### Conditional Properties

These properties appear or change behavior based on other property values (controlled by ViewModel rules and dependencies):

- **`Html`** (InArgument\<string\>) — Visible only when `InputMode` is `Content`. When `InputMode` switches to `File`, `Html` is hidden and the `Item` (FileName/ResourceFile) fields appear.
- **`FileName`** (InArgument\<string\>) — Visible only when `InputMode` is `File`.
- **`ResourceFile`** (InArgument\<IResource\>) — Visible only when `InputMode` is `File`.
- **`HeaderHtml`** (InArgument\<string\>) — Visible only when `HeaderInputMode` is `Content`.
- **`FooterHtml`** (InArgument\<string\>) — Visible only when `FooterInputMode` is `Content`.

### Enum Reference

**`ItemInputMode`**: `Content`, `File`

**`PdfPaperSize`**: `A4`, `A3`, `A5`, `A2`, `A6`, `Letter`, `Legal`, `Tabloid`, `Ledger`, `Executive`, `Statement`, `B4`, `B5`, `Number10Envelope`, `DLEnvelope`, `C5Envelope`, `C4Envelope`

## XAML Example

```xml
<pdf:ConvertHtmlToPDF
    DisplayName="Convert Html to PDF"
    Html="[htmlString]"
    OutputFileName="[&quot;C:\output\report.pdf&quot;]"
    PaperSize="A4"
    Scale="[1.0]"
    OutputFile="[outputFile]" />
```

> The `pdf` namespace prefix maps to `clr-namespace:UiPath.PDF.Activities.PDF.NetCore;assembly=UiPath.PDF.Activities`.

## Notes

- `FileName` and `ResourceFile` are decorated with `[OverloadGroup]` — at most one may be bound at runtime. Bind `FileName` for a plain string path, or `ResourceFile` when working with storage buckets and file resources.
- `Scale` must be ≥ 0.1 and ≤ 2. Values outside this range will cause a runtime error.
- When `OutputFileName` is omitted, a default PDF file name is generated in the current working directory.
- Header and footer HTML templates have their own independent `InputMode` selectors (`HeaderInputMode`, `FooterInputMode`).
