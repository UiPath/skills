# PowerPoint Examples

Examples using the `powerpoint` service from `UiPath.Presentations.Activities` package.

**Required package:** `"UiPath.Presentations.Activities": "[2.3.1]"`

---

## Create Presentation and Add Slides (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class CreatePresentationWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(new UseOptions
            {
                Path = @"C:\Reports\quarterly_report.pptx",
                CreateIfNotExist = true,
                AutoSave = true
            });

            // Add a title slide
            int titleSlide = presentation.AddNewSlide("Title Slide");
            presentation.AddTextToSlide(titleSlide, "Title 1", "Quarterly Report Q1 2026");
            presentation.AddTextToSlide(titleSlide, "Subtitle 2", "Prepared by Automation Team");

            // Add a content slide at the end
            int contentSlide = presentation.AddNewSlide("Title and Content");
            presentation.AddTextToSlide(contentSlide, "Title 1", "Key Highlights");
            presentation.AddTextToSlide(contentSlide, "Content Placeholder 2",
                "Revenue increased by 15%\nCustomer satisfaction at 92%\nNew product launch on track");

            // Add a blank slide at a specific position
            int blankSlide = presentation.AddNewSlide("Blank", insertPosition: 2,
                addAs: InsertPositionType.SpecifiedIndex);

            Log($"Presentation created with {presentation.NumberOfSlides} slides.");
        }
    }
}
```

## Open Existing Presentation and Replace Text (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class ReplaceTextWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Templates\template.pptx");

            // Replace placeholders with actual values
            int count1 = presentation.ReplaceTextInPresentation("{{CompanyName}}", "Acme Corp");
            int count2 = presentation.ReplaceTextInPresentation("{{Date}}", DateTime.Now.ToString("MMMM yyyy"));
            int count3 = presentation.ReplaceTextInPresentation("{{Author}}", "John Smith", matchCase: true);

            Log($"Replaced {count1 + count2 + count3} text occurrences.");

            // Save as a new file
            presentation.SavePresentationAs(@"C:\Output\filled_report.pptx");
        }
    }
}
```

## Add DataTable to Slide (Windows)

```csharp
using System.Data;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class DataTableSlideWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Templates\report_template.pptx");

            // Build a DataTable
            var dt = new DataTable();
            dt.Columns.Add("Product", typeof(string));
            dt.Columns.Add("Q1 Sales", typeof(int));
            dt.Columns.Add("Q2 Sales", typeof(int));
            dt.Rows.Add("Widget A", 1500, 1800);
            dt.Rows.Add("Widget B", 2200, 2100);
            dt.Rows.Add("Widget C", 900, 1200);

            // Insert as a new table replacing a placeholder shape
            presentation.AddDataTableToSlide(
                slideNumber: 2,
                contentPlaceholder: "Table Placeholder 1",
                tableToAdd: dt,
                behaviour: TableAppendMode.CreateNewTable
            );

            // Append more rows to the same table
            var extraRows = new DataTable();
            extraRows.Columns.Add("Product", typeof(string));
            extraRows.Columns.Add("Q1 Sales", typeof(int));
            extraRows.Columns.Add("Q2 Sales", typeof(int));
            extraRows.Rows.Add("Widget D", 500, 750);

            presentation.AddDataTableToSlide(
                slideNumber: 2,
                contentPlaceholder: "Table Placeholder 1",
                tableToAdd: extraRows,
                behaviour: TableAppendMode.AppendToTable,
                excludeSourceHeaders: true
            );

            Log("DataTable added to slide.");
        }
    }
}
```

## Insert Images and Videos (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class MediaSlideWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\media_report.pptx");

            // Replace a placeholder shape with an image
            presentation.AddImageOrVideoToSlide(
                slideNumber: 1,
                contentPlaceholder: "Picture Placeholder 1",
                imageOrVideoPath: @"C:\Images\company_logo.png"
            );

            // Insert image with specific position and size (in points)
            presentation.AddImageOrVideoToSlide(
                slideNumber: 2,
                contentPlaceholder: "Content Placeholder 2",
                imageOrVideoPath: @"C:\Images\chart.png",
                left: 100f, top: 150f, width: 400f, height: 300f,
                newShapeName: "SalesChart"
            );

            // Insert a video
            presentation.AddImageOrVideoToSlide(
                slideNumber: 3,
                contentPlaceholder: "Media Placeholder 1",
                imageOrVideoPath: @"C:\Videos\product_demo.mp4"
            );

            Log("Media inserted into presentation.");
        }
    }
}
```

## Insert Files and Paste from Clipboard (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class InsertFileWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\report.pptx");

            // Insert a file as an icon (simple)
            presentation.AddFileToSlide(
                slideNumber: 3,
                fileToAdd: @"C:\Data\raw_data.xlsx"
            );

            // Insert a file into a specific placeholder with a custom label
            presentation.AddFileToSlide(
                slideNumber: 3,
                contentPlaceholder: "Content Placeholder 2",
                fileToAdd: @"C:\Data\analysis.xlsx",
                iconLabel: "Detailed Analysis"
            );

            // Paste from clipboard into a specific placeholder
            presentation.PasteItemIntoSlide(
                slideNumber: 4,
                contentPlaceholder: "Content Placeholder 2"
            );

            Log("Files and clipboard content inserted.");
        }
    }
}
```

## Copy Slides Between Presentations (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class CopySlidesWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var source = powerpoint.UsePowerPointPresentation(@"C:\Templates\master_slides.pptx");
            var destination = powerpoint.UsePowerPointPresentation(new UseOptions
            {
                Path = @"C:\Output\combined.pptx",
                CreateIfNotExist = true
            });

            // Copy slide 1 from source to position 1 in destination
            source.CopyPasteSlide(destination, slideToCopy: 1, whereToInsert: 1);

            // Copy slide 3 from source to position 2 in destination
            source.CopyPasteSlide(destination, slideToCopy: 3, whereToInsert: 2);

            // Move slide 5 from source to destination (removes from source)
            source.CopyPasteSlide(destination, slideToCopy: 5, whereToInsert: 3, move: true);

            Log($"Destination now has {destination.NumberOfSlides} slides.");
        }
    }
}
```

## Save and Export (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class SaveExportWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\report.pptx");

            // Save as PDF
            presentation.SavePresentationAsPDF(@"C:\Output\report.pdf");

            // Save as .pptx (modern format)
            presentation.SavePresentationAs(@"C:\Output\report_copy.pptx",
                PresentationSaveAsType.XmlPresentation, replaceExisting: true);

            // Save as .ppt (legacy format)
            presentation.SavePresentationAs(@"C:\Output\report_legacy.ppt",
                PresentationSaveAsType.OldPresentation);

            // Save as macro-enabled
            presentation.SavePresentationAs(@"C:\Output\report_macros.pptm",
                PresentationSaveAsType.MacroEnabledPresentation);

            // Export a range of slides to PDF via SlideOperations
            presentation.SlideOperations.ExportToPdf(@"C:\Output\slides_2_to_5.pdf", 2, 5);

            Log("Presentation saved in multiple formats.");
        }
    }
}
```

## Run Macros (Windows)

```csharp
using System.Collections.Generic;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class MacroWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(new UseOptions
            {
                Path = @"C:\Reports\macro_enabled.pptm",
                AutoSave = true
            });

            // Run a macro without arguments
            presentation.RunPresentationMacro("FormatAllSlides", new List<object>());

            // Run a macro with arguments
            object result = presentation.RunPresentationMacro("GenerateReport",
                new List<object> { "Q1", 2026, true });

            if (result != null)
            {
                Log($"Macro returned: {result}");
            }
        }
    }
}
```

## Format Slide Content (Windows)

```csharp
using System.Collections.Generic;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class FormatContentWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\report.pptx");

            // Change font size of a shape
            presentation.FormatSlideContent(
                slideNumber: 1,
                contentToModify: "Title 1",
                modifications: new List<IFormatSlideModicationModel>
                {
                    new FontSizeModificationModel(28)
                }
            );

            // Apply multiple formatting changes at once
            presentation.FormatSlideContent(
                slideNumber: 2,
                contentToModify: "Content Placeholder 2",
                modifications: new List<IFormatSlideModicationModel>
                {
                    new FontSizeModificationModel(14),
                    new ChangeShapeNameModel("MainContent")
                }
            );

            // Bring a shape to front
            presentation.FormatSlideContent(
                slideNumber: 3,
                contentToModify: "Picture 1",
                modifications: new List<IFormatSlideModicationModel>
                {
                    new ZIndexModificationModel(ZIndexChangeType.BringToFront)
                }
            );

            Log("Formatting applied.");
        }
    }
}
```

## Read Data from Slides (Windows)

```csharp
using System.Data;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class ReadSlideDataWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var presentation = powerpoint.UsePowerPointPresentation(@"C:\Reports\report.pptx");

            // Get text from a specific shape
            string titleText = presentation.SlideOperations.GetText(1, "Title 1");
            Log($"Title: {titleText}");

            // Get a table from a shape as a DataTable
            DataTable tableData = presentation.SlideOperations.GetTable(2, "Table 1");
            Log($"Table has {tableData.Rows.Count} rows and {tableData.Columns.Count} columns.");

            // Get slide layout name
            string layout = presentation.SlideOperations.GetLayout(1);
            Log($"Slide 1 layout: {layout}");

            // Get shape count on a slide
            int shapeCount = presentation.SlideOperations.GetShapeCount(1);
            Log($"Slide 1 has {shapeCount} shapes.");

            // Get font size
            float fontSize = presentation.SlideOperations.GetFontSize(1, "Title 1");
            Log($"Title font size: {fontSize}");
        }
    }
}
```

## Sensitivity Labels (Windows)

```csharp
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class SensitivityLabelWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Open with sensitivity label applied
            var presentation = powerpoint.UsePowerPointPresentation(new UseOptions
            {
                Path = @"C:\Reports\confidential.pptx",
                SensitivityOperation = PptLabelOperation.Add,
                SensitivityLabel = new PptLabelObject
                {
                    LabelId = "your-label-guid-here",
                    Justification = "Contains financial data"
                }
            });

            // Read sensitivity label
            IPptLabelObject currentLabel = presentation.GetSensitivityLabel();
            if (currentLabel != null)
            {
                Log($"Label: {currentLabel.LabelId}, Justification: {currentLabel.Justification}");
            }

            // Update sensitivity label
            presentation.AddSensitivityLabel(new PptLabelObject
            {
                LabelId = "new-label-guid",
                Justification = "Updated classification"
            });
        }
    }
}
```

## Portable API — Basic Operations

```csharp
using System.Data;
using System.Collections.Generic;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class PortableWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = powerpoint.UsePresentationDocument(@"C:\Templates\template.pptx");

            // Add a new slide at the end
            int? slideIndex = doc.AddNewSlide("Title and Content");
            Log($"Added slide at position: {slideIndex}");

            // Add text to the slide
            doc.AddTextToSlide(slideIndex.Value, "Title 1", "Monthly Report", clearExisting: true);
            doc.AddTextToSlide(slideIndex.Value, "Content Placeholder 2", "Key metrics for the month.");

            // Replace text across the presentation
            int replacements = doc.ReplaceTextInPresentation("{{Month}}", "February 2026");
            Log($"Replaced {replacements} occurrences.");

            // Add an image
            doc.AddImageOrVideoToSlide(2, "Picture Placeholder 1", @"C:\Images\chart.png");

            // Delete the last slide
            doc.DeleteSlide(5);

            Log("Portable presentation operations complete.");
            // Changes are saved automatically when doc is disposed
        }
    }
}
```

## Portable API — DataTable and Formatting

```csharp
using System.Data;
using System.Collections.Generic;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class PortableTableFormattingWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            using var doc = powerpoint.UsePresentationDocument(@"C:\Templates\data_template.pptx");

            // Build a DataTable
            var dt = new DataTable();
            dt.Columns.Add("Metric", typeof(string));
            dt.Columns.Add("Value", typeof(string));
            dt.Rows.Add("Revenue", "$1.2M");
            dt.Rows.Add("Expenses", "$800K");
            dt.Rows.Add("Profit", "$400K");

            // Add table to slide
            doc.AddDataTableToSlide(
                slideNumber: 2,
                contentPlaceholder: "Table Placeholder 1",
                tableToAdd: dt,
                excludeHeaders: false,
                behaviour: TableAppendMode.CreateNewTable
            );

            // Format a shape — change font size and rename
            doc.FormatSlideContent(
                slideNumber: 1,
                contentToModify: "Title 1",
                modifications: new List<ISlideContentModicationModel>
                {
                    new ShapeFontSizeModificationModel(32),
                    new ShapeChangeNameModel("ReportTitle")
                }
            );

            Log("Table and formatting applied via portable API.");
        }
    }
}
```

## Complete Example — Monthly Report Generation (Windows)

```csharp
using System.Data;
using System.Collections.Generic;
using UiPath.Presentations;
using UiPath.Presentations.Activities;
using UiPath.Presentations.Activities.API;
using UiPath.Presentations.Activities.API.Models;

namespace MyProject
{
    public class MonthlyReportWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Open template
            var presentation = powerpoint.UsePowerPointPresentation(new UseOptions
            {
                Path = @"C:\Templates\monthly_template.pptx",
                AutoSave = false
            });

            // Replace template placeholders
            presentation.ReplaceTextInPresentation("{{ReportTitle}}", "Monthly Report - February 2026");
            presentation.ReplaceTextInPresentation("{{Author}}", "Automation Team");
            presentation.ReplaceTextInPresentation("{{Date}}", DateTime.Now.ToString("MMMM dd, yyyy"));

            // Add executive summary text
            presentation.AddTextToSlide(2, "Content Placeholder 2",
                "This month saw significant improvements across all key metrics.\n" +
                "Revenue targets exceeded by 12%.\n" +
                "Customer satisfaction scores at an all-time high.");

            // Add sales data table
            var salesData = new DataTable();
            salesData.Columns.Add("Region", typeof(string));
            salesData.Columns.Add("Target", typeof(string));
            salesData.Columns.Add("Actual", typeof(string));
            salesData.Columns.Add("Variance", typeof(string));
            salesData.Rows.Add("North", "$500K", "$560K", "+12%");
            salesData.Rows.Add("South", "$400K", "$380K", "-5%");
            salesData.Rows.Add("East", "$600K", "$650K", "+8%");
            salesData.Rows.Add("West", "$450K", "$490K", "+9%");

            presentation.AddDataTableToSlide(3, "Table Placeholder 1", salesData);

            // Insert chart image
            presentation.AddImageOrVideoToSlide(4, "Picture Placeholder 1",
                @"C:\Reports\Charts\revenue_chart.png");

            // Insert company logo on title slide
            presentation.AddImageOrVideoToSlide(1, "Picture Placeholder 3",
                @"C:\Assets\company_logo.png",
                left: 50f, top: 30f, width: 120f, height: 60f,
                newShapeName: "CompanyLogo");

            // Add an appendix slide with attached data file
            int appendixSlide = presentation.AddNewSlide("Title and Content");
            presentation.AddTextToSlide(appendixSlide, "Title 1", "Appendix — Raw Data");
            presentation.AddFileToSlide(appendixSlide, "Content Placeholder 2",
                @"C:\Reports\Data\raw_sales_data.xlsx", "Raw Sales Data");

            // Batch replace in a specific slide
            presentation.SlideOperations.ReplaceInSlide(5, new Dictionary<string, string>
            {
                { "{{KPI1}}", "92%" },
                { "{{KPI2}}", "$1.2M" },
                { "{{KPI3}}", "4.8/5.0" }
            });

            // Duplicate the KPI slide for another department
            presentation.SlideOperations.DuplicateSlides(5, 5, 1);
            presentation.SlideOperations.ReplaceInSlide(6, new Dictionary<string, string>
            {
                { "92%", "88%" },
                { "$1.2M", "$950K" },
                { "4.8/5.0", "4.5/5.0" }
            });

            // Format the title
            presentation.FormatSlideContent(1, "Title 1",
                new List<IFormatSlideModicationModel>
                {
                    new FontSizeModificationModel(36)
                }
            );

            // Save as new file and export PDF
            presentation.SavePresentationAs(@"C:\Output\Monthly_Report_Feb2026.pptx");
            presentation.SavePresentationAsPDF(@"C:\Output\Monthly_Report_Feb2026.pdf");

            Log($"Report generated with {presentation.NumberOfSlides} slides.");
        }
    }
}
```
