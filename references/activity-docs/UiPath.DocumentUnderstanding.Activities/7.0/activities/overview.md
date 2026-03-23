# UiPath.DocumentUnderstanding.Activities — Overview

Document Understanding (DU) activities for classification, extraction, validation, and PDF utilities. Package: `UiPath.DocumentUnderstanding.Activities`.

Always get full XAML from `uip rpa get-default-activity-xaml` — the per-activity files cover confirmed patterns from real workflows only.

## Variable Types

| Type | Namespace prefix | When used |
|------|-----------------|-----------|
| `uisad1:DocumentData` | `uisad1:` | Output of `ClassifyDocument`; contains `DocumentType.DisplayName` and `DocumentType.Confidence` |
| `uisad2:IDocumentData(T)` | `uisad2:` | Output of `ExtractDocumentDataWithDocumentData`; generic extraction result typed to bundle |
| `uisad:CreatedValidationAction(T)` | `uisad:` | Output of `CreateValidationAction` (async create-only variant) |
| `upr:ILocalResource` | `upr:` | Output of PDF utility activities (file handles for exported PDFs, images) |

## File Input Patterns

All DU pipeline activities accept a document file via `IResource`:

```xml
FileInput="[LocalResource.FromPath(filePath)]"
```

All PDF activities use the same pattern:

```xml
PdfFile="[LocalResource.FromPath(filePath)]"
```

Where `filePath` is a `String` variable containing the local file path.

## DU Pipeline Overview

The standard pipeline: **Classify -> Extract -> Validate**

### Activities

#### DU Pipeline (Classify / Extract / Validate)
- [ClassifyDocument](ClassifyDocument.md) — ML or Generative classification
- [ExtractDocumentDataWithDocumentData](ExtractDocumentDataWithDocumentData.md) — ML or Generative extraction
- [ValidateDocumentDataWithDocumentData](ValidateDocumentDataWithDocumentData.md) — Synchronous create+wait validation
- [CreateValidationAction](CreateValidationAction.md) — Async create-only validation
- [WaitForValidationAction](WaitForValidationAction.md) — Async wait-only validation
- [CreateClassificationValidationActionAndWait](CreateClassificationValidationActionAndWait.md) — Classification validation

#### PDF Utilities
- [ExtractPDFText](ExtractPDFText.md)
- [GetPDFPageCount](GetPDFPageCount.md)
- [SetPDFPassword](SetPDFPassword.md)
- [MergePDFs](MergePDFs.md)
- [ExtractPDFPageRange](ExtractPDFPageRange.md)
- [ExtractPDFImages](ExtractPDFImages.md)

## DocType Values

| Value | Use for |
|-------|---------|
| `invoices` | Invoice documents |
| `receipts` | Receipt documents |
| `id_cards` | Identity cards |
| `passports` | Passport documents |
| `purchase_orders` | Purchase order documents |
| `utility_bills` | Utility bill documents |
| `remittance_advices` | Remittance advice documents |
| `bills_of_lading` | Bill of lading documents |
| `checks` | Check documents |
| `generative_extractor` | Custom/unknown document types — use with `GptPromptWithVariables` and `GenerateData="True"` |

## Accessing Extracted Data

```vb
' Access a specific field value
DocumentExtractedData.Data.InvoiceNumber.ToString
DocumentExtractedData.Data.TotalAmount.ToString

' Check document type from classification
DocumentData.DocumentType.DisplayName.Equals("Invoices")

' Check classification confidence (float 0-1)
DocumentData.DocumentType.Confidence

' Gate on low confidence before sending to human validation
If DocumentData.DocumentType.Confidence < 0.7 Then
    ' CreateClassificationValidationActionAndWait
End If
```

## Key Patterns

| Pattern | Notes |
|---------|-------|
| File input | `[LocalResource.FromPath(filePath)]` — always use for `IResource` parameters |
| Pipeline order | ClassifyDocument -> ExtractDocumentDataWithDocumentData -> Validate |
| ML classifier | `ClassifierId="ml-classification"`, empty `scg:Dictionary` for `GptPromptWithVariables`, integer `MinimumConfidence` |
| Generative classifier | `ClassifierId="generative_classifier"`, per-type `InArgument` entries, `Endpoint/ProjectId="{x:Null}"` |
| ML extractor | Named `DocType` (e.g., `"invoices"`), `GenerateData="False"`, empty `scg:Dictionary` for `GptPromptWithVariables` |
| Generative extractor | `DocType="generative_extractor"`, `GenerateData="True"`, per-field `InArgument` entries |
| AutoValidationConfidenceThreshold | Always set via child element as `Nullable(Int32)`, not as an XML attribute |
| Synchronous validation | Use `ValidateDocumentDataWithDocumentData` (combined create+wait) |
| Async validation | Use `CreateValidationAction` + `WaitForValidationAction` pair when workflow must suspend between create and wait |
| Classification validation | Use `CreateClassificationValidationActionAndWait` when `DocumentData.DocumentType.Confidence < 0.7` |
| ClassificationResults type | `uisad1:DocumentData` |
| ExtractionResults type | `uisad2:IDocumentData(Of T)` — use bundle type (e.g., `uisaseib:Invoices`) when known; `x:Object` otherwise |
| PDF output type | `upr:ILocalResource` — output type for SetPDFPassword, MergePDFs, ExtractPDFPageRange |
| Images output type | `IEnumerable(Of upr:ILocalResource)` — output type for ExtractPDFImages |
| MergePDFs inline | Use nested `IndividualPdfFiles` property with `scg:List`; set `CollectionPdfFiles="{x:Null}"` |
| MergePDFs variable | Set `CollectionPdfFiles` to an `IEnumerable(Of IResource)` variable; omit `IndividualPdfFiles` |
| OCR extraction | Set `ApplyOcr="True"` and `OcrEngine="UIPATH_DOCUMENT_OCR"` on `ExtractPDFText` for scanned PDFs |
| Full XAML | Always use `uip rpa get-default-activity-xaml` for complete activity XAML |
