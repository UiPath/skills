# Excel Examples

Examples using the `excel` service from `UiPath.Excel.Activities` package.

**Required package:** `"UiPath.Excel.Activities": "[3.3.1]"`

---

## Read and Process Data (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class ReadExcelWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("invoices.xlsx");

            // Read a range as DataTable with headers
            DataTable dt = workbook.Sheet["Invoices"].ReadRange(hasHeaders: true, visibleRowsOnly: false);

            Log($"Found {dt.Rows.Count} invoices");

            decimal total = 0;
            foreach (DataRow row in dt.Rows)
            {
                string customer = row["Customer"].ToString();
                decimal amount = Convert.ToDecimal(row["Amount"]);
                total += amount;
                Log($"Invoice for {customer}: {amount:C}");
            }

            // Write total to a cell
            workbook.Sheet["Invoices"].Cell["E1"].WriteCell("Total");
            workbook.Sheet["Invoices"].Cell["F1"].WriteCell(total.ToString());
        }
    }
}
```

## Write DataTable to Excel (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class WriteExcelWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Build a DataTable
            var dt = new DataTable();
            dt.Columns.Add("Name", typeof(string));
            dt.Columns.Add("Email", typeof(string));
            dt.Columns.Add("Score", typeof(int));

            dt.Rows.Add("Alice", "alice@example.com", 95);
            dt.Rows.Add("Bob", "bob@example.com", 87);
            dt.Rows.Add("Charlie", "charlie@example.com", 92);

            // Write to a new Excel file
            using var workbook = excel.UseExcelFile("results.xlsx");
            workbook.Sheet["Sheet1"].WriteRange(dt, append: false, excludeHeaders: false);

            Log("Data written to results.xlsx");
        }
    }
}
```

## Iterate Rows with ForEachRow (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class IterateRowsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("data.xlsx");

            // ForEachRow iterates over rows in a range
            workbook.Sheet["Sheet1"].ForEachRow(hasHeaders: true, action: (row, index) =>
            {
                string name = row["Name"]?.ToString();
                string status = row["Status"]?.ToString();

                if (status == "Pending")
                {
                    Log($"Row {index}: {name} is pending — processing...");
                    // Write back to the Status column
                    row["Status"] = "Processed";
                }
            });
        }
    }
}
```

## Multi-Sheet Operations (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class MultiSheetWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("report.xlsx");

            // Read from one sheet
            DataTable sourceData = workbook.Sheet["RawData"].ReadRange(hasHeaders: true, visibleRowsOnly: false);

            // Create a summary on another sheet
            workbook.AddSheet("Summary");
            workbook.Sheet["Summary"].Cell["A1"].WriteCell("Total Records");
            workbook.Sheet["Summary"].Cell["B1"].WriteCell(sourceData.Rows.Count.ToString());
            workbook.Sheet["Summary"].Cell["A2"].WriteCell("Generated");
            workbook.Sheet["Summary"].Cell["B2"].WriteCell(DateTime.Now.ToString("yyyy-MM-dd HH:mm"));

            // Copy filtered data to another sheet
            workbook.AddSheet("Filtered");
            var filtered = sourceData.Select("Amount > 1000");
            if (filtered.Length > 0)
            {
                DataTable filteredDt = filtered.CopyToDataTable();
                workbook.Sheet["Filtered"].WriteRange(filteredDt, append: false, excludeHeaders: false);
            }

            Log($"Report generated with {sourceData.Rows.Count} records");
        }
    }
}
```

## Named Table Operations (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class TableWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("sales.xlsx");

            // Read from a named table
            DataTable salesData = workbook.Table["SalesTable"].ReadRange(hasHeaders: true, visibleRowsOnly: false);

            // Filter the table
            workbook.Sheet["Sheet1"].FilterTable("SalesTable", "Region", "North");

            // Read only visible (filtered) rows
            DataTable filteredSales = workbook.Table["SalesTable"].ReadRange(hasHeaders: true, visibleRowsOnly: true);
            Log($"North region has {filteredSales.Rows.Count} sales");

            // Sort the table
            workbook.Sheet["Sheet1"].Sort("A:A", ascending: true);
        }
    }
}
```

## Find and Replace (Windows API)

```csharp
namespace MyProject
{
    public class FindReplaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("template.xlsx");

            // Find and replace placeholders
            workbook.Sheet["Sheet1"].FindReplace(
                "{{CompanyName}}",
                "Acme Corporation",
                FindReplaceOptions.ReplaceAll
            );

            workbook.Sheet["Sheet1"].FindReplace(
                "{{Date}}",
                DateTime.Now.ToString("MMMM dd, yyyy"),
                FindReplaceOptions.ReplaceAll
            );

            // Lookup a value
            object result = workbook.Sheet["Sheet1"].VLookup(
                "ProductA",
                "A:C",
                3,
                MatchType.ExactlyEqual
            );
            Log($"ProductA price: {result}");
        }
    }
}
```

## Save As PDF (Windows API)

```csharp
namespace MyProject
{
    public class SaveAsPdfWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var workbook = excel.UseExcelFile("report.xlsx");

            // Save the entire workbook as PDF
            workbook.SaveAsPdf(@"C:\Output\report.pdf", PdfSaveQuality.StandardQuality);

            // Save as a different Excel format
            workbook.SaveAs(@"C:\Output\report_copy.xlsx", ExcelSaveAsType.OpenXmlWorkbook);
        }
    }
}
```

## Portable API — Basic Read/Write

```csharp
using System.Data;
using System.Drawing;

namespace MyProject
{
    public class PortableExcelWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var wb = excel.UseWorkBook("data.xlsx");

            // Read a range as DataTable
            DataTable dt = wb.ReadRange("Sheet1", "A1:D10", addHeaders: true, preserveFormat: false);
            Log($"Read {dt.Rows.Count} rows");

            // Read a single cell
            object cellValue = wb.ReadCell("Sheet1", "B2", preserveFormat: true);
            Log($"Cell B2: {cellValue}");

            // Read a cell formula
            string formula = wb.ReadCellFormula("Sheet1", "C2");
            Log($"Formula in C2: {formula}");

            // Write to a cell
            wb.WriteCell("Sheet1", "E1", "Processed");

            // Write a DataTable
            wb.WriteRange("Sheet1", "G1", dt, addHeaders: true);

            // Append rows to existing data
            wb.AppendRange("Sheet1", dt);

            // Set cell color
            wb.SetRangeColor("Sheet1", "A1:D1", Color.LightBlue);
        }
    }
}
```

## Portable API — CSV Operations

```csharp
using System.Data;

namespace MyProject
{
    public class CsvWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Read a CSV file
            DataTable csvData = ExcelFile.ReadCSV(
                "input.csv",
                addHeaders: true,
                delimiter: DelimitatorOptions.Comma
            );

            Log($"CSV has {csvData.Rows.Count} rows and {csvData.Columns.Count} columns");

            // Process the data
            foreach (DataRow row in csvData.Rows)
            {
                Log($"{row[0]} - {row[1]}");
            }

            // Write to a CSV file
            ExcelFile.WriteCSV(
                "output.csv",
                csvData,
                addHeaders: true,
                delimiter: DelimitatorOptions.Comma
            );
        }
    }
}
```

## Excel Process Scope with Macros

```csharp
namespace MyProject
{
    public class MacroWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Create an Excel process scope with macros enabled
            using var excelProcess = excel.ExcelProcessScope(new ScopeOptions
            {
                DisplayAllerts = false,
                ShowExcelWindow = false,
                MacroSetting = MacroSetting.EnableAll
            });

            using var workbook = excel.UseExcelFile(new UseOptions
            {
                Path = "macro_report.xlsm",
                ExcelProcess = excelProcess,
                SaveChanges = true
            });

            // Execute a macro
            workbook.ExecuteMacro("GenerateReport");

            // Read the results
            var results = workbook.Sheet["Results"].ReadRange(hasHeaders: true, visibleRowsOnly: false);
            Log($"Macro generated {results.Rows.Count} rows");
        }
    }
}
```
