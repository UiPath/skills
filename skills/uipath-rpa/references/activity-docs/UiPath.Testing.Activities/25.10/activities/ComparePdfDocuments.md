# Compare PDF Documents

Compares two PDF documents (baseline vs. target) to determine their equivalence. Supports text comparison at line/word/character granularity, optional inclusion of images/widgets, and comparison rules to exclude dynamic sections. Optionally uses Autopilot AI to interpret differences semantically.

**Class:** `UiPath.Testing.Activities.ComparePdfDocuments`
**Assembly:** `UiPath.Testing.Activities`
**Category:** Testing > Verification

```xml
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"
```

---

## Input

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `BaselinePath` | `InArgument<IResource>` | Yes | — | The baseline (reference) PDF document. Accepts a file path or resource reference. |
| `TargetPath` | `InArgument<IResource>` | Yes | — | The target PDF to compare against the baseline. |
| `ComparisonType` | `ComparisonType` | Yes* | — | Granularity of text comparison: `Line`, `Word`, or `Character`. *Hidden when `InterpretDifferencesWithAutopilot` is `true`. |
| `InterpretDifferencesWithAutopilot` | `Boolean` | No | `false` | If `true`, uses Autopilot AI to semantically interpret differences. When enabled, `ComparisonType` is hidden and `SemanticDifferences` is populated. |
| `ContinueOnFailure` | `InArgument<Boolean>` | No | `true` | If `true`, the workflow continues even when differences are found. |
| `IgnoreIdenticalItems` | `InArgument<Boolean>` | No | `true` | If `true`, identical content (lines/items) is excluded from the diff output. |
| `IncludeImages` | `InArgument<Boolean>` | No | `true` | If `true`, images and URI widgets are included in the comparison. |
| `IgnoreImagesLocation` | `InArgument<Boolean>` | No | `false` | If `true`, the position and page of images/URI widgets are ignored (only their presence is compared). Only relevant when `IncludeImages` is `true`. |
| `OutputFolderPath` | `InArgument<String>` | Yes | `"."` | Directory path where output diff files will be saved. |
| `Rules` | `List<InArgument<ComparisonRule>>` | No | — | *(Legacy)* Individual comparison rules added via the designer. |
| `RulesList` | `InArgument<List<ComparisonRule>>` | No | — | A list of `ComparisonRule` objects (from **Create Comparison Rule**) to exclude dynamic sections. |

## Output

| Property | Type | Description |
|----------|------|-------------|
| `Result` | `OutArgument<Boolean>` | `true` if documents are equivalent, `false` if differences were found. |
| `Differences` | `OutArgument<IEnumerable<Difference>>` | List of text differences. Each `Difference` has `Operation` (`Equal`, `Inserted`, `Deleted`) and `Text`. Populated when `InterpretDifferencesWithAutopilot` is `false`. |
| `SemanticDifferences` | `OutArgument<SemanticDifferences>` | Semantic interpretation from Autopilot. Only populated when `InterpretDifferencesWithAutopilot` is `true`. |

---

## Valid Configurations

**Standard comparison** (`InterpretDifferencesWithAutopilot = false`):
- `ComparisonType` must be set to `Line`, `Word`, or `Character`.
- `Differences` output is populated; `SemanticDifferences` is not.

**Autopilot-interpreted comparison** (`InterpretDifferencesWithAutopilot = true`):
- `ComparisonType` is hidden and ignored.
- `SemanticDifferences` output is populated; `Differences` is not.

These two modes are mutually exclusive.

---

## Enum: `ComparisonType`

| Value | Description |
|-------|-------------|
| `Line` | Compares extracted text line by line. |
| `Word` | Compares extracted text word by word. |
| `Character` | Compares extracted text character by character. |

---

## XAML Example

```xml
<!-- Standard line-by-line PDF comparison -->
<uta:ComparePdfDocuments
  DisplayName="Compare PDF Documents"
  BaselinePath="&quot;Baseline\invoice_baseline.pdf&quot;"
  TargetPath="[generatedPdfPath]"
  ComparisonType="Line"
  ContinueOnFailure="True"
  IgnoreIdenticalItems="True"
  IncludeImages="True"
  IgnoreImagesLocation="False"
  OutputFolderPath="&quot;Output\PDFDiff&quot;"
  Result="[pdfCompareResult]"
  Differences="[pdfDiffs]" />

<!-- With comparison rules to ignore dynamic content -->
<uta:ComparePdfDocuments
  DisplayName="Compare PDF with Rules"
  BaselinePath="&quot;Baseline\report.pdf&quot;"
  TargetPath="[reportPath]"
  ComparisonType="Line"
  RulesList="[New List(Of ComparisonRule) From {dateRule, idRule}]"
  OutputFolderPath="&quot;Output\PDFDiff&quot;"
  Result="[pdfResult]"
  Differences="[pdfDiffs]" />

<!-- Autopilot semantic interpretation -->
<uta:ComparePdfDocuments
  DisplayName="Compare PDF (Autopilot)"
  BaselinePath="&quot;Baseline\doc.pdf&quot;"
  TargetPath="[targetDoc]"
  InterpretDifferencesWithAutopilot="True"
  OutputFolderPath="&quot;Output\PDFDiff&quot;"
  Result="[pdfResult]"
  SemanticDifferences="[semanticResult]" />
```
