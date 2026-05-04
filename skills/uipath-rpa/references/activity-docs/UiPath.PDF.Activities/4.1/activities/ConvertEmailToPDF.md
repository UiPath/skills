# Convert Email to PDF

`UiPath.PDF.Activities.PDF.NetCore.ConvertEmailToPDF`

Converts a `MailMessage` object to a PDF file. The activity automatically detects whether the email body is HTML or plain text and applies the appropriate rendering template, preserving the subject, sender, and recipient metadata as a formatted header block. Optional page header/footer HTML templates, paper size, margin, and scale settings are available for layout customization.

**Package:** `UiPath.PDF.Activities`
**Category:** App Integration > PDF

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Placeholder | Description |
|------|-------------|------|------|----------|---------|-------------|-------------|
| `Email` | Email | `InArgument` | `MailMessage` | Yes | | | The email message to convert to PDF. Both HTML and plain-text bodies are supported. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `HeaderHtml` | Html Header Content | `InArgument<string>` | | An HTML string to use as a page header template. |
| `FooterHtml` | Html Footer Content | `InArgument<string>` | | An HTML string to use as a page footer template. |
| `PaperSize` | Paper Size | `InArgument<PdfPaperSize>` | `A4` | The paper size used for the PDF output. |
| `Margin` | Margin | `InArgument<int>` | `0` | Page margin in points. |
| `Scale` | Scale | `InArgument<double>` | `1.0` | Page rendering scale. Must be between 0.1 and 2 inclusive. |
| `KeepBackground` | Keep Background | `InArgument<bool>` | `true` | Whether to preserve background color and graphics during conversion. |
| `OutputFileName` | Output File Path | `InArgument<string>` | | Full path of the output PDF file. If not specified, a default file name is generated. |

### Output

| Name | Display Name | Type | Description |
|------|-------------|------|-------------|
| `OutputFile` | Output File | `ILocalResource` | The resulting PDF file as a local resource. |

### Enum Reference

**`PdfPaperSize`**: `A4`, `A3`, `A5`, `A2`, `A6`, `Letter`, `Legal`, `Tabloid`, `Ledger`, `Executive`, `Statement`, `B4`, `B5`, `Number10Envelope`, `DLEnvelope`, `C5Envelope`, `C4Envelope`

## XAML Example

```xml
<pdf:ConvertEmailToPDF
    DisplayName="Convert Email to PDF"
    Email="[mailMessage]"
    PaperSize="Letter"
    OutputFileName="[&quot;C:\output\email-export.pdf&quot;]"
    OutputFile="[outputFile]" />
```

> The `pdf` namespace prefix maps to `clr-namespace:UiPath.PDF.Activities.PDF.NetCore;assembly=UiPath.PDF.Activities`.

## Notes

- The `Email` argument accepts a `System.Net.Mail.MailMessage` object. Use a mail activity (e.g., Get Mail, Get IMAP Mail Messages) to obtain a `MailMessage`, then pass it directly to this activity.
- The activity inspects `MailMessage.IsBodyHtml` and `AlternateViews` to automatically select either the HTML or plain-text rendering template. No manual mode switch is required.
- Rendered output includes a header block with **Subject**, **From**, and **To** fields extracted from the message.
- `Scale` must be ≥ 0.1 and ≤ 2. Values outside this range will cause a runtime error.
- When `OutputFileName` is omitted, a default PDF file name is generated in the current working directory.
