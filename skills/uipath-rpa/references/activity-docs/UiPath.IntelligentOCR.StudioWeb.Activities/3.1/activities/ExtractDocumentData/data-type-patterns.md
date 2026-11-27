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
| `Handler` | `ExtractionResultHandler` | Low-level handler for direct access to the underlying extraction result. |

### Methods

| Method | Return Type | Description |
|--------|-------------|-------------|
| `GetFields()` | `ResultsDataPoint[]` | Returns all non-table extracted fields. |
| `GetTables()` | `ResultsTable[]` | Returns all extracted tables. |
| `GetField(string fieldIdOrName)` | `ResultsDataPoint` | Returns a single field by its ID or name. Case-insensitive. Throws if multiple fields match. |
| `GetTable(string tableIdOrName)` | `ResultsTable` | Returns a single table by its ID or name. Case-insensitive. Throws if multiple tables match. See [Table Access Patterns](#table-access-patterns) for the full `ResultsTable` → `ResultsTableValue` → `ResultsTableCell` type hierarchy. |
| `GetFieldValue(string fieldIdOrName)` | `ResultsValue` | Returns the first value of a field. Returns `null` if the field is missing. Throws if the field is not found. |
| `GetFieldValue(string fieldIdOrName, int index)` | `ResultsValue` | Returns the value at a specific index. Throws if the index is out of range. |
| `GetFieldValues(string fieldIdOrName)` | `ResultsValue[]` | Returns all values of a field. Returns an empty array if the field is missing. |
| `SetFieldValue(string fieldIdOrName, ResultsValue value)` | `void` | Replaces all values of a field with a single value. |
| `SetFieldValue(string fieldIdOrName, ResultsValue value, int index)` | `void` | Sets the value at a specific index. |
| `SetFieldValues(string fieldIdOrName, ResultsValue[] values)` | `void` | Replaces all values of a field. |

### Field Lookup Behavior

`GetField`, `GetFieldValue`, `GetFieldValues`, `GetTable`, and their setter counterparts resolve fields in this order:
1. Match by **full field ID** (case-insensitive)
2. Match by **short field ID** (the part after the last `.` in the field ID, case-insensitive)
3. Match by **field name** (case-insensitive)

If more than one field matches at any step, an `ArgumentException` is thrown.

## Table Access Patterns

Extraction results can contain **tables** (e.g., line items on a receipt or invoice). Accessing table data requires navigating a specific type hierarchy that differs from simple field access.

### Type Chain

```
DictionaryData
  .GetTable("fieldId")        → ResultsTable
    .Values                   → ResultsTableValue[]  (typically one element)
    .GetValue()               → ResultsTableValue     (shorthand for Values(0))

ResultsTableValue
  .NumberOfRows               → Int32                 (includes header row)
  .ColumnInfo                 → ResultsTableColumnInfo[]
  .Cells                      → ResultsTableCell[]    (flat array, row-major order)
  .GetCell(rowIndex, colIndex)→ ResultsTableCell       (helper, avoids manual indexing)
  .GetRow(rowIndex)           → IEnumerable(Of ResultsTableCell)
  .GetRows()                  → IEnumerable(Of ResultsTableCell())

ResultsTableCell
  .Values                     → ResultsValue[]        (typically one element)
  .GetValue()                 → ResultsValue           (shorthand for Values(0))
  .RowIndex                   → Int32
  .ColumnIndex                → Int32
  .IsHeader                   → Boolean
  .IsMissing                  → Boolean

ResultsTableColumnInfo
  .FieldId                    → String                 (column identifier, e.g., "description")
  .FieldName                  → String                 (display name)

ResultsValue
  .Value                      → String                 (the extracted text)
  .Confidence                 → Single
  .OcrConfidence              → Single
  .OperatorConfirmed          → Boolean
```

### Key Points

- **`ResultsTable.Values`** returns `ResultsTableValue[]`, **not** `ResultsValue[]`. Do not confuse with `ResultsDataPoint.Values`.
- **`ResultsTableCell.Values`** returns `ResultsValue[]` (same as simple fields). Access the text with `.Values(0).Value` or the shorthand `.GetValue().Value`.
- **`Cells` is a flat row-major array.** To access a cell manually: `Cells(rowIndex * ColumnInfo.Length + columnIndex)`. Prefer the helper methods `GetCell(row, col)`, `GetRow(row)`, or `GetRows()` instead.
- **Row 0 is the header row.** Data rows start at index 1. `NumberOfRows` includes the header.

### Iterating Table Rows (VB.NET)

Find columns by `FieldId`, then iterate data rows:

```vb
' Get the table and its first value
Dim table As ResultsTable = extractionResults.Data.GetTable("items")
Dim tv As ResultsTableValue = table.GetValue()

' Find column indices by FieldId
Dim descCol As Integer = -1
Dim amountCol As Integer = -1
For i As Integer = 0 To tv.ColumnInfo.Length - 1
    Select Case tv.ColumnInfo(i).FieldId
        Case "description" : descCol = i
        Case "line-amount" : amountCol = i
    End Select
Next

' Iterate data rows (row 0 is the header, skip it)
For row As Integer = 1 To tv.NumberOfRows - 1
    Dim description As String = tv.GetCell(row, descCol).GetValue().Value
    Dim amount As String = tv.GetCell(row, amountCol).GetValue().Value
    ' ... use description and amount
Next
```

### Alternative: Using GetRows()

```vb
Dim table As ResultsTable = extractionResults.Data.GetTable("items")
Dim tv As ResultsTableValue = table.GetValue()

For Each row As ResultsTableCell() In tv.GetRows()
    ' Skip header row
    If row(0).IsHeader Then Continue For
    ' Access cells by column index
    Dim description As String = row(descCol).GetValue().Value
    Dim amount As String = row(amountCol).GetValue().Value
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
