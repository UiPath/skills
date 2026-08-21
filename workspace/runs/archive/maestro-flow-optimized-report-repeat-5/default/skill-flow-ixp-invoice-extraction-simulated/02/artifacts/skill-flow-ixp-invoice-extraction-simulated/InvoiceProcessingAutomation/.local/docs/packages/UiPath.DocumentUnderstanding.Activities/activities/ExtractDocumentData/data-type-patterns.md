# Data Type Patterns for Document Understanding Pipelines

When using `ExtractDocumentDataWithDocumentData<T>`, the type argument `T` determines how extraction results are accessed and how downstream validation activities must be typed. This document covers the two patterns and their pipeline-wide implications.

## Overview

| Pattern | Type Argument | `GenerateData` | Field Access | Agent-Compatible |
|---------|--------------|-----------------|--------------|------------------|
| **DictionaryData** | `dux:DictionaryData` | `False` | `GetField("fieldName")`, `GetFieldValue("fieldName")` | Yes (recommended) |
| **Generated Type** | Studio-generated subclass | `True` | `extractionResults.Data.FieldName` | No (requires Studio JIT compilation) |

**For agent-generated workflows, always use `DictionaryData` with `GenerateData="False"`.** The generated type pattern requires Studio's design-time code generation, which is not available when an LLM agent produces XAML directly. Additionally, `GenerateData=True` is incompatible with `ModernDocumentTypeId="use_classification_result"`.

## DictionaryData API Reference

`UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction.DictionaryData`

`DictionaryData` extends `ExtendedExtractionResultsForDocumentData` and provides methods to access extracted fields and tables by name or ID.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `Handler` | `ExtractionResultHandler` | **Recommended modern entry point** for reading and mutating fields and tables. Returns a fluent navigator over the underlying `ExtractionResult` with type-checked facades per field type — `BasicDataPoint`, `TableDataPoint`, `TableValue`, `TableRow`, `FieldGroupDataPoint`, `FieldGroupValue`. See [Table Access Patterns](#table-access-patterns) below and the contracts doc [`ExtractionResultHandler`](../../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md). |

### Methods

**Field methods (modern — return contracts types):**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `GetFields()` | `ResultsDataPoint[]` | Returns all non-table extracted fields. |
| `GetField(string fieldIdOrName)` | `ResultsDataPoint` | Returns a single field by its ID or name. Case-insensitive. Throws if multiple fields match. |
| `GetFieldValue(string fieldIdOrName)` | `ResultsValue` | Returns the first value of a field. Returns `null` if the field is missing. Throws if the field is not found. |
| `GetFieldValue(string fieldIdOrName, int index)` | `ResultsValue` | Returns the value at a specific index. Throws if the index is out of range. |
| `GetFieldValues(string fieldIdOrName)` | `ResultsValue[]` | Returns all values of a field. Returns an empty array if the field is missing. |
| `SetFieldValue(string fieldIdOrName, ResultsValue value)` | `void` | Replaces all values of a field with a single value. |
| `SetFieldValue(string fieldIdOrName, ResultsValue value, int index)` | `void` | Sets the value at a specific index. |
| `SetFieldValues(string fieldIdOrName, ResultsValue[] values)` | `void` | Replaces all values of a field. |

**Table methods (legacy — return deprecated types; prefer `Handler.GetTableValue` instead):**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `GetTables()` | `ResultsTable[]` | **Legacy.** Returns all extracted tables wrapped in the deprecated `ResultsTable` type. Prefer `Handler.GetTables()` which returns `TableDataPoint[]`. |
| `GetTable(string tableIdOrName)` | `ResultsTable` | **Legacy.** Returns a single table as the deprecated `ResultsTable` type. Prefer `Handler.GetTableValue(tableIdOrName)` which returns the modern `TableValue` facade. See [Table Access Patterns](#table-access-patterns) below. |

### Field Lookup Behavior

`GetField`, `GetFieldValue`, `GetFieldValues`, `GetTable`, and their setter counterparts use the same two-pass lookup as the contracts handler — FieldId-or-last-segment, then FieldName, both case-insensitive; ambiguity throws `ArgumentException`. See [`ExtractionResultHandler`](../../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md) for the full lookup-semantics rules.

## Table Access Patterns

Extraction results can contain **tables** (e.g., line items on a receipt or invoice). The recommended path is the modern `Handler` API on `DictionaryData`. The legacy `GetTable(...)` / `ResultsTable` chain is kept for backwards compatibility but should not be used in new code.

### Modern: `DictionaryData.Handler` (recommended)

`DictionaryData.Handler` exposes a fluent navigator (`ExtractionResultHandler`) over the underlying `ExtractionResult`. Tables are reached via `Handler.GetTableValue("name")` and exposed as `TableValue` / `TableRow` / `BasicDataPoint` — typed facades that hide the `ResultsValue.Components` walk.

For the full type surface (lookup semantics, mutation methods, edge cases) see the contracts doc:
[`ExtractionResultHandler`](../../../UiPath.DocumentProcessing.Contracts/classes/ExtractionResultHandler.md).

#### Type chain (modern)

```
DictionaryData
  .Handler                                  → ExtractionResultHandler
      .GetTableValue("items")               → TableValue
          .Rows                             → TableRow[]    (data rows; the [Header] node is hidden)
          .GetRow(rowIndex)                 → TableRow
          .RemoveRow(rowIndex)              → TableValue
          .AddEmptyRow(taxonomyField)       → TableRow      (taxonomyField : Taxonomy.Field)

TableRow
  .Cells                                    → BasicDataPoint[]
  .GetCell(columnIndex)                     → BasicDataPoint
  .GetCell("columnFieldIdOrName")           → BasicDataPoint
  Indexer: row(columnIndex) / row("name")   → BasicDataPoint

BasicDataPoint
  .Value                                    → BasicValue    (null if the cell has no values)
  .Values                                   → BasicValue[]
  .UpdateValue(value, confidence, ...)      → BasicValue    (safe whether missing or populated)

BasicValue
  .Value                                    → String         (the extracted text)
  .Confidence                               → Single
  .OcrConfidence                            → Single
  .OperatorConfirmed                        → Boolean
```

`Handler.GetTableValue(...)` throws `InvalidOperationException` if the table data point exists but has no values. Use `Handler.GetTable(...)` (returns `TableDataPoint`) and check `IsMissing` first if you need to distinguish missing from populated.

#### Iterating table rows (VB.NET)

```vb
Imports UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1

Dim handler As ExtractionResultHandler = extractionResults.Data.Handler
Dim items As TableValue = handler.GetTableValue("items")

For Each row As TableRow In items.Rows
    Dim description As String = row("description").Value?.Value
    Dim amount As String = row("line-amount").Value?.Value
    ' ... use description and amount
Next
```

`row("description")` is the string indexer on `TableRow`. Lookup is case-insensitive and matches by FieldId (full or last-dotted-segment) first, then by FieldName. The header row is **not** returned in `Rows` — only data rows are.

`row("description").Value` returns `null` when the cell has no extracted value. The `?.Value` chain is the safe form.

#### Iterating table rows (C#)

```csharp
using UiPath.DocumentProcessing.Contracts.Extensions.Navigator.V1;

ExtractionResultHandler handler = extractionResults.Data.Handler;
TableValue items = handler.GetTableValue("items");

foreach (TableRow row in items.Rows)
{
    string description = row["description"].Value?.Value;
    string amount      = row["line-amount"].Value?.Value;
    // ... use description and amount
}
```

#### Mutating cells

`BasicDataPoint.UpdateValue(value, confidence, ocrConfidence)` is safe regardless of whether the cell currently has a value — when the cell is missing, it falls back to `AddValue`. Useful for filling in low-confidence rows during a review pass.

```vb
For Each row As TableRow In items.Rows
    Dim qtyCell = row("quantity")
    Dim qty = qtyCell.Value
    If qty IsNot Nothing AndAlso qty.Confidence < 0.6F Then
        qtyCell.UpdateValue(value:=qty.Value, confidence:=0.6F, operatorConfirmed:=True)
    End If
Next
```

### Legacy: `DictionaryData.GetTable("...")` (deprecated)

> **Do not use in new code.** `DictionaryData.GetTables()` returns the deprecated `ResultsDocument.Tables` array, and `GetTable(...)` returns the deprecated `ResultsTable` type. The contracts package flags this entire chain (`ResultsTable` / `ResultsTableValue` / `ResultsTableCell` / `ResultsTableColumnInfo`) as deprecated. The modern path above is the supported one.

Kept here for understanding existing workflows that already use it. The flat-grid types still work at runtime, but new code should switch to `Handler.GetTableValue(...)`.

#### Type chain (legacy)

```
DictionaryData.GetTable("items")          → ResultsTable
  .Values                                  → ResultsTableValue[]    (typically one element)
  .GetValue()                              → ResultsTableValue       (shorthand for Values(0))

ResultsTableValue
  .NumberOfRows                            → Int32                   (includes header row)
  .ColumnInfo                              → ResultsTableColumnInfo[]
  .Cells                                   → ResultsTableCell[]      (flat, row-major)
  .GetCell(rowIndex, colIndex)             → ResultsTableCell
  .GetRow(rowIndex)                        → IEnumerable(Of ResultsTableCell)
  .GetRows()                               → IEnumerable(Of ResultsTableCell())

ResultsTableCell
  .Values                                  → ResultsValue[]
  .GetValue()                              → ResultsValue
  .IsHeader                                → Boolean
  .IsMissing                               → Boolean
```

Quirks of the legacy chain (only relevant if you cannot avoid it):

- `ResultsTable.Values` returns `ResultsTableValue[]`, **not** `ResultsValue[]`. Don't confuse with `ResultsDataPoint.Values`.
- `Cells` is a flat row-major array. Use `GetCell(row, col)` / `GetRow(row)` / `GetRows()` instead of manual indexing.
- **Row 0 is the header row.** Data rows start at index 1. `NumberOfRows` includes the header. (The modern `TableValue.Rows` does not include the header.)

#### Legacy iteration example (kept for reference)

```vb
Dim table As ResultsTable = extractionResults.Data.GetTable("items")
Dim tv As ResultsTableValue = table.GetValue()

Dim descCol As Integer = -1
Dim amountCol As Integer = -1
For i As Integer = 0 To tv.ColumnInfo.Length - 1
    Select Case tv.ColumnInfo(i).FieldId
        Case "description" : descCol = i
        Case "line-amount" : amountCol = i
    End Select
Next

For row As Integer = 1 To tv.NumberOfRows - 1
    Dim description As String = tv.GetCell(row, descCol).GetValue().Value
    Dim amount As String = tv.GetCell(row, amountCol).GetValue().Value
Next
```

### Predefined Extractor Table Fields

The Predefined project extractors define these table fields and column IDs:

**Receipts** (`DocType="receipts"`) — table field: `items`

| Column FieldId | Column Name |
|----------------|-------------|
| `description` | Description |
| `quantity` | Quantity |
| `unit-price` | Unit Price |
| `line-amount` | Line Amount |

**Invoices** (`DocType="invoices"`) — table field: `items`

| Column FieldId | Column Name |
|----------------|-------------|
| `description` | Description |
| `quantity` | Quantity |
| `unit-price` | Unit Price |
| `line-amount` | Line Amount |
| `item-po-no` | Purchase Order Number |
| `line-no` | Line Number |
| `part-no` | Part Number |

**Purchase Orders** (`DocType="purchase_orders"`) — table field: `items`

| Column FieldId | Column Name |
|----------------|-------------|
| `description` | Description |
| `quantity` | Quantity |
| `unit-price` | Unit Price |
| `line-amount` | Line Amount |

> **Note:** For custom DU projects, the table field IDs and column IDs are project-specific. Ask the user for the table field name and column names.

## Pipeline-Wide Type Propagation

The type argument `T` chosen for `ExtractDocumentDataWithDocumentData<T>` must be used consistently across **all** downstream activities that handle extraction results. Mismatched type arguments will cause runtime errors.

| Activity | Generic Parameter | DictionaryData Type Argument |
|----------|-------------------|------------------------------|
| `ExtractDocumentDataWithDocumentData<T>` | `T` | `dux:DictionaryData` |
| `CreateValidationAction<T>` | `T` | `dux:DictionaryData` |
| `WaitForValidationAction<T>` | `T` | `dux:DictionaryData` |
| `ValidateDocumentDataWithDocumentData<T>` | `T` | `dux:DictionaryData` |
| `CreateDocumentValidationArtifacts<T>` | `T` | `dux:DictionaryData` |

Classification validation activities (`CreateClassificationValidationAction`, `WaitForClassificationValidationAction`, `CreateClassificationValidationActionAndWait`) are **not** generic and are unaffected by this choice.

## Variable Declarations for DictionaryData Pipeline

Complete variable block for a pipeline with classification validation and extraction validation:

```xml
<Sequence.Variables>
  <!-- Classification -->
  <Variable x:TypeArguments="duc:DocumentData" Name="classificationResults" />
  <Variable x:TypeArguments="duVal:CreatedClassificationValidationAction" Name="classificationTask" />
  <Variable x:TypeArguments="duc:DocumentData" Name="validatedClassificationResults" />
  <!-- Extraction (DictionaryData) -->
  <Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="extractionResults" />
  <Variable x:TypeArguments="duVal:CreatedValidationAction(dux:DictionaryData)" Name="extractionValidationTask" />
  <Variable x:TypeArguments="dux:IDocumentData(dux:DictionaryData)" Name="validatedExtractionResults" />
</Sequence.Variables>
```

Required XAML namespace prefixes for these variables:

```xml
xmlns:duc="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DocumentClassification;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:dux="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataExtraction;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
xmlns:duVal="clr-namespace:UiPath.IntelligentOCR.StudioWeb.Activities.DataValidation;assembly=UiPath.IntelligentOCR.StudioWeb.Activities"
```

## GenerateData=True Pattern (Studio Only)

When `GenerateData=True`, Studio generates a subclass of `ExtendedExtractionResultsForDocumentData` at design time with strongly-typed properties for each extracted field. The generated type has a dynamic name and assembly (e.g., `AdiTest11InvoicesV3` in assembly `ExtendedExtractionRe.O9Rcc1EXZGC1VPCKY1e5Dfq3`).

This pattern:
- Requires Studio's design-time JIT compilation
- Produces a user/project-specific type name that cannot be predicted
- Enables `extractionResults.Data.InvoiceNumber`, `extractionResults.Data.TotalAmount`, etc.
- All downstream validation activities must use the same generated type as their type argument
- **Incompatible with `ModernDocumentTypeId="use_classification_result"`**

**Agents should never use this pattern.** Always set `GenerateData="False"` and use `DictionaryData` as the type argument.
