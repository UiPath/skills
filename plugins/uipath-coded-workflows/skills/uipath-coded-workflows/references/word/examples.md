# Word Examples

Examples using the `word` service from `UiPath.Word.Activities` package.

**Required package:** `"UiPath.Word.Activities": "[2.3.1]"`

---

## Create and Write a Document (Windows API)

```csharp
namespace MyProject
{
    public class CreateWordDocWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseWordDocument("report.docx");

            doc.AppendText("Monthly Sales Report");
            doc.AppendText($"Generated on: {DateTime.Now:MMMM dd, yyyy}");
            doc.AppendText("");
            doc.AppendText("This report summarizes the sales performance for the current month.");
            doc.AppendText("Key highlights are listed below.", true);

            Log("Report created successfully.");
        }
    }
}
```

## Read Document Content (Windows API)

```csharp
namespace MyProject
{
    public class ReadWordDocWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseWordDocument(new WordUseOptions
            {
                Path = "contract.docx",
                ReadOnly = true,
                AutoSave = false
            });

            string content = doc.ReadText();
            Log($"Document has {content.Length} characters");

            // Check if document contains specific text
            if (content.Contains("CONFIDENTIAL"))
            {
                Log("Document is marked as confidential.");
            }
        }
    }
}
```

## Template Processing with Replace (Windows API)

```csharp
namespace MyProject
{
    public class TemplateWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute(string customerName, string invoiceNumber, decimal amount)
        {
            using var doc = word.UseWordDocument("invoice_template.docx");

            // Replace template placeholders
            doc.ReplaceTextInDocument("{{CustomerName}}", customerName);
            doc.ReplaceTextInDocument("{{InvoiceNumber}}", invoiceNumber);
            doc.ReplaceTextInDocument("{{Amount}}", amount.ToString("C"));
            doc.ReplaceTextInDocument("{{Date}}", DateTime.Now.ToString("MMMM dd, yyyy"));

            // Replace only the first occurrence
            doc.ReplaceTextInDocument("{{FirstItem}}", "Premium Package", replaceAll: false);

            Log($"Invoice {invoiceNumber} generated for {customerName}");
        }
    }
}
```

## Bookmark Operations (Windows API)

```csharp
namespace MyProject
{
    public class BookmarkWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseWordDocument("form.docx");

            // Fill bookmarks with data
            doc.SetBookmarkContent("CompanyName", "Acme Corporation");
            doc.SetBookmarkContent("Address", "123 Main Street, Suite 100");
            doc.SetBookmarkContent("ContactName", "John Smith");
            doc.SetBookmarkContent("Phone", "+1 (555) 123-4567");
            doc.SetBookmarkContent("Date", DateTime.Now.ToString("yyyy-MM-dd"));

            Log("Bookmarks populated successfully.");
        }
    }
}
```

## Add Hyperlinks and Pictures (Windows API)

```csharp
namespace MyProject
{
    public class HyperlinksAndPicturesWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseWordDocument("document.docx");

            doc.AppendText("Company Documentation");

            // Add hyperlink at the end of the document
            doc.AddHyperlinkToDocument("Visit our website", "https://www.example.com");

            // Add hyperlink at the start
            doc.AddHyperlinkToDocument("Home", "https://www.example.com/home", Position.Start);

            // Add hyperlink after specific text
            doc.AddHyperlinkToDocument("Click here for details", "https://www.example.com/details",
                Position.After, "For more information");

            // Add a picture at the end
            doc.AddPicture(@"C:\Images\logo.png");

            // Add a picture at the start of the document
            doc.AddPicture(@"C:\Images\header.png", Position.Start);

            // Add a picture at a bookmark location
            doc.AddPicture(@"C:\Images\chart.png", "ChartPlaceholder", Position.Replace);

            Log("Hyperlinks and pictures added.");
        }
    }
}
```

## Insert DataTable into Word (Windows API)

```csharp
using System.Data;

namespace MyProject
{
    public class DataTableInWordWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Build a DataTable
            var dt = new DataTable();
            dt.Columns.Add("Product", typeof(string));
            dt.Columns.Add("Quantity", typeof(int));
            dt.Columns.Add("Price", typeof(decimal));

            dt.Rows.Add("Widget A", 100, 9.99m);
            dt.Rows.Add("Widget B", 250, 14.50m);
            dt.Rows.Add("Widget C", 75, 22.00m);

            using var doc = word.UseWordDocument("report.docx");

            doc.AppendText("Product Inventory Report");
            doc.AppendText($"Date: {DateTime.Now:yyyy-MM-dd}");

            // Insert the DataTable as a Word table at the end
            doc.InsertDataTableInDocument(dt);

            Log("DataTable inserted into Word document.");
        }
    }
}
```

## Save as PDF (Windows API)

```csharp
namespace MyProject
{
    public class SaveAsPdfWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseWordDocument("report.docx");

            // Make changes
            doc.ReplaceTextInDocument("{{Status}}", "Final");

            // Save as PDF
            doc.SaveAsPDF(@"C:\Output\report.pdf");

            // Save as another Word format
            doc.SaveDocumentAs(@"C:\Output\report_copy.docx", WordSaveAsType.XmlDocument);

            Log("Document saved as PDF and DOCX.");
        }
    }
}
```

## Portable API — Basic Operations

```csharp
namespace MyProject
{
    public class PortableWordWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Create a new document using the portable (cross-platform) API
            using var doc = word.UseDocument("notes.docx", createNew: true);

            // Append text (each call adds a new line by default)
            doc.AppendText("Meeting Notes");
            doc.AppendText($"Date: {DateTime.Now:yyyy-MM-dd}");
            doc.AppendText("Attendees: Alice, Bob, Charlie");
            doc.AppendText("");
            doc.AppendText("Discussion Points:");
            doc.AppendText("1. Project timeline review");
            doc.AppendText("2. Budget allocation");
            doc.AppendText("3. Next steps");

            // Append without a new line
            doc.AppendText(" — Action items pending.", false);

            Log("Meeting notes created.");
        }
    }
}
```

## Portable API — Read and Replace

```csharp
namespace MyProject
{
    public class PortableReadReplaceWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = word.UseDocument("template.docx");

            // Read all text
            string content = doc.ReadText();
            Log($"Template length: {content.Length} characters");

            // Replace placeholders
            bool found1 = doc.ReplaceText("{{Name}}", "Jane Doe");
            bool found2 = doc.ReplaceText("{{Company}}", "Tech Corp");

            if (found1 && found2)
            {
                Log("All placeholders replaced successfully.");
            }
            else
            {
                Log("Some placeholders were not found in the document.");
            }
        }
    }
}
```

## Full Workflow — Excel to Word Report

```csharp
using System.Data;

namespace MyProject
{
    public class ExcelToWordReportWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Read data from Excel
            using var workbook = excel.UseExcelFile("sales_data.xlsx");
            DataTable salesData = workbook.Sheet["Sheet1"].ReadRange(hasHeaders: true, visibleRowsOnly: false);

            // Generate Word report
            using var doc = word.UseWordDocument("sales_report.docx");

            doc.AppendText("Sales Report");
            doc.AppendText($"Report Date: {DateTime.Now:MMMM dd, yyyy}");
            doc.AppendText($"Total Records: {salesData.Rows.Count}");

            // Calculate total
            decimal total = 0;
            foreach (DataRow row in salesData.Rows)
            {
                total += Convert.ToDecimal(row["Amount"]);
            }
            doc.AppendText($"Total Sales: {total:C}");

            // Insert data as a table
            doc.InsertDataTableInDocument(salesData);

            // Save as PDF
            doc.SaveAsPDF(@"C:\Output\sales_report.pdf");

            Log($"Report generated: {salesData.Rows.Count} records, total {total:C}");
        }
    }
}
```
