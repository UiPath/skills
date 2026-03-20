# System Examples

Examples using the `system` service from `UiPath.System.Activities` package.

**Required package:** `"UiPath.System.Activities": "[25.12.2]"`

---

## File Operations

### Copy, Create, and Delete Files

```csharp
using UiPath.Core;
using UiPath.Core.Activities.Storage;

namespace MyProject
{
    public class FileOperationsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Create a folder
            ILocalResource folder = system.CreateFolder(@"C:\Output\Reports");
            Log($"Created folder: {folder.FullPath}");

            // Create a file
            ILocalResource file = system.CreateFile("report.txt", @"C:\Output\Reports");
            Log($"Created file: {file.FullPath}");

            // Write text to the file
            system.WriteTextFile("Hello, World!", file);

            // Read the file back
            IResource fileResource = system.GetResourceForLocalPath(@"C:\Output\Reports\report.txt", PathType.File);
            string content = system.ReadTextFile(fileResource);
            Log($"File content: {content}");

            // Append a line
            system.AppendLine("Additional line.", file);

            // Copy file to another location
            system.CopyFile(@"C:\Output\Reports\report.txt", @"C:\Backup", true);

            // Check if a path exists
            bool exists = system.FileExists(@"C:\Backup\report.txt");
            Log($"Backup exists: {exists}");

            // Delete the original
            system.DeleteFileOrFolder(file);
        }
    }
}
```

### Copy Folder and Check Existence

```csharp
using UiPath.Core;
using UiPath.Core.Activities.Storage;

namespace MyProject
{
    public class FolderOperationsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Copy entire folder with subfolders
            system.CopyFolder(@"C:\Source\Data", @"C:\Backup\Data", overwrite: true, includeSubfolder: true);

            // Check folder exists
            if (system.FolderExists(@"C:\Backup\Data"))
            {
                Log("Folder copied successfully.");
            }

            // Move a file using IResource references
            IResource source = system.GetResourceForLocalPath(@"C:\Backup\Data\temp.csv", PathType.File);
            IResource destination = system.GetResourceForLocalPath(@"C:\Archive", PathType.Folder);
            system.MoveFile(source, destination, overwrite: true);

            // PathExists with out parameter
            bool found = system.PathExists(@"C:\Archive\temp.csv", PathType.File, out ILocalResource resource);
            if (found)
            {
                Log($"Moved file found at: {resource.FullPath}");
            }
        }
    }
}
```

---

## Archive/Compression

### Zip and Unzip Files

```csharp
using System.Collections.Generic;
using UiPath.Core;
using UiPath.Core.Activities.Storage;

namespace MyProject
{
    public class ArchiveWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get file references
            IResource file1 = system.GetResourceForLocalPath(@"C:\Reports\report1.pdf", PathType.File);
            IResource file2 = system.GetResourceForLocalPath(@"C:\Reports\report2.pdf", PathType.File);

            // Compress files into a zip
            ILocalResource zipFile = system.CompressZipFiles(
                new List<IResource> { file1, file2 },
                @"C:\Archives\reports.zip"
            );
            Log($"Archive created: {zipFile.FullPath}");

            // Compress with password and options
            ILocalResource secureZip = system.CompressZipFiles(
                new List<IResource> { file1, file2 },
                @"C:\Archives\secure_reports.zip",
                password: "MyPassword123",
                compressionLevel: ArchiveCompressionLevel.Optimal,
                codePage: CodePages.UTF8,
                overrideExistingFile: true
            );

            // Extract a zip file
            IResource zipResource = system.GetResourceForLocalPath(@"C:\Archives\reports.zip", PathType.File);
            ILocalResource[] extracted = system.ExtractUnzipFiles(zipResource, @"C:\Extracted");
            Log($"Extracted {extracted.Length} files.");

            // Extract with password to a dedicated subfolder
            ILocalResource[] secureExtracted = system.ExtractUnzipFiles(
                system.GetResourceForLocalPath(@"C:\Archives\secure_reports.zip", PathType.File),
                @"C:\Extracted",
                extractToADedicatedFolder: true,
                password: "MyPassword123",
                codePage: CodePages.UTF8
            );
        }
    }
}
```

---

## DataTable Operations

### Build, Sort, and Manipulate DataTables

```csharp
using System.Data;

namespace MyProject
{
    public class DataTableWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Build a DataTable
            var dt = new DataTable();
            dt.Columns.Add("Name", typeof(string));
            dt.Columns.Add("Age", typeof(int));
            dt.Columns.Add("City", typeof(string));

            // Add rows
            DataRow row1 = dt.NewRow();
            row1["Name"] = "Alice";
            row1["Age"] = 30;
            row1["City"] = "New York";
            system.AddDataRow(ref dt, row1);

            DataRow row2 = dt.NewRow();
            row2["Name"] = "Bob";
            row2["Age"] = 25;
            row2["City"] = "London";
            system.AddDataRow(ref dt, row2);

            DataRow row3 = dt.NewRow();
            row3["Name"] = "Alice";
            row3["Age"] = 30;
            row3["City"] = "New York";
            system.AddDataRow(ref dt, row3);

            // Sort by Name ascending
            DataTable sorted = system.SortDataTable(dt, "Name", SortOrder.Ascending);
            Log($"Sorted rows: {sorted.Rows.Count}");

            // Remove duplicates
            DataTable unique = system.RemoveDuplicateRows(sorted);
            Log($"After removing duplicates: {unique.Rows.Count}");

            // Output as CSV string
            string csv = system.OutputDataTable(unique);
            Log($"CSV output:\n{csv}");

            // Remove a column
            system.RemoveDataColumn(ref unique, "City");

            // Remove row at index 0
            system.RemoveDataRow(ref unique, 0);

            // Clear all data
            system.ClearDataTable(ref unique);
        }
    }
}
```

### Merge, Lookup, and Update DataTables

```csharp
using System.Data;

namespace MyProject
{
    public class DataTableMergeLookupWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Create source and destination tables
            var source = new DataTable();
            source.Columns.Add("ID", typeof(int));
            source.Columns.Add("Product", typeof(string));
            source.Rows.Add(1, "Widget");
            source.Rows.Add(2, "Gadget");

            var destination = new DataTable();
            destination.Columns.Add("ID", typeof(int));
            destination.Columns.Add("Product", typeof(string));
            destination.Rows.Add(3, "Sprocket");

            // Merge source into destination
            system.MergeDataTable(source, ref destination, MissingSchemaAction.Add);
            Log($"Merged table has {destination.Rows.Count} rows.");

            // Lookup a value
            object result = system.LookupDataTable(
                destination,
                lookupValue: "Gadget",
                lookupColumnName: "Product",
                targetColumnName: "ID",
                out int rowIndex
            );
            Log($"Found 'Gadget' at row {rowIndex}, ID = {result}");

            // Get and update a row item
            DataRow row = destination.Rows[0];
            object currentValue = system.GetRowItem(row, "Product");
            Log($"Current product: {currentValue}");

            system.UpdateRowItem("Updated Widget", row, "Product");
            Log($"Updated product: {system.GetRowItem(row, "Product")}");
        }
    }
}
```

---

## Text Operations

### Replace, Extract, and Transform Text

```csharp
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace MyProject
{
    public class TextOperationsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            string sampleText = "Contact us at support@example.com or sales@example.com. Visit https://example.com for more info.";

            // Regex replace
            string replaced = system.Replace(sampleText, @"\b\w+@\w+\.\w+\b", "[REDACTED]");
            Log($"Redacted: {replaced}");

            // Find and replace (simple)
            string updated = system.FindAndReplace("example.com", sampleText, "mycompany.com", matchCase: false);
            Log($"Updated: {updated}");

            // Extract emails
            IEnumerable<string> emails = system.ExtractEmails(sampleText, ignoreDuplicates: true);
            foreach (string email in emails)
            {
                Log($"Email: {email}");
            }

            // Extract URLs
            IEnumerable<string> urls = system.ExtractUrls(sampleText, extractBaseURLOnly: true, ignoreDuplicates: true);
            foreach (string url in urls)
            {
                Log($"URL: {url}");
            }

            // Extract text between markers
            string markedText = "START:Hello:END and START:World:END";
            IEnumerable<string> occurrences = system.ExtractTextOccurrences(markedText, "START:", ":END", ignoreDuplicates: false);
            foreach (string item in occurrences)
            {
                Log($"Extracted: {item}");
            }

            // Strip HTML
            string html = "<h1>Title</h1><p>Some <b>bold</b> text.</p>";
            string plain = system.ExtractTextFromHTML(html);
            Log($"Plain text: {plain}");
        }
    }
}
```

### Combine, Split, and Change Case

```csharp
using System.Collections.Generic;
using System.Linq;

namespace MyProject
{
    public class TextTransformWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Split text
            IEnumerable<string> parts = system.SplitText("apple,banana,cherry", SeparatorOptions.Comma);
            Log($"Split into {parts.Count()} parts.");

            // Combine text
            string combined = system.CombineText(parts, SeparatorOptions.Pipe);
            Log($"Combined: {combined}");  // "apple|banana|cherry"

            // Combine with custom separator
            string dashed = system.CombineText(parts, " - ");
            Log($"Dashed: {dashed}");  // "apple - banana - cherry"

            // Change case
            string upper = system.ChangeCase("hello world", ChangeCaseOptions.UPPERCASE);
            Log($"Upper: {upper}");  // "HELLO WORLD"

            string title = system.ChangeCase("hello world", ChangeCaseOptions.TitleCase);
            Log($"Title: {title}");  // "Hello World"
        }
    }
}
```

---

## DateTime Operations

### Format, Extract, and Manipulate Dates

```csharp
using System.Globalization;

namespace MyProject
{
    public class DateTimeWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var today = DateTime.Now;

            // Format date
            string formatted = system.FormatDateAsText(today, "dd-MM-yyyy", CultureInfo.InvariantCulture);
            Log($"Formatted: {formatted}");

            string isoFormat = system.FormatDateAsText(today, "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            Log($"ISO: {isoFormat}");

            // Add days
            DateTime nextWeek = system.AddOrSubtractFromDate(
                today,
                UnitsOfTime.Days,
                7,
                UiPath.Activities.System.Date.AddOrSubtractFromDate.DateOperations.Add
            );
            Log($"Next week: {system.FormatDateAsText(nextWeek, "dd-MM-yyyy", CultureInfo.InvariantCulture)}");

            // Subtract months
            DateTime threeMonthsAgo = system.AddOrSubtractFromDate(
                today,
                UnitsOfTime.Months,
                3,
                UiPath.Activities.System.Date.AddOrSubtractFromDate.DateOperations.Subtract
            );
            Log($"Three months ago: {system.FormatDateAsText(threeMonthsAgo, "dd-MM-yyyy", CultureInfo.InvariantCulture)}");

            // Extract dates from text
            string text = "Meeting on 15-01-2026 and deadline 28-02-2026";
            IEnumerable<DateTime> dates = system.ExtractDateAndTimeFromText(
                "dd-MM-yyyy",
                text,
                CultureInfo.InvariantCulture
            );
            foreach (DateTime date in dates)
            {
                Log($"Extracted date: {date}");
            }
        }
    }
}
```

---

## Queue/Transaction Items

### Add and Process Queue Items

```csharp
using System.Collections.Generic;
using UiPath.Orchestrator.Client.Models;

namespace MyProject
{
    public class QueueProcessingWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Add a queue item with data
            system.AddQueueItem(
                "InvoiceQueue",
                folderPath: null,
                dueDate: DateTime.Now.AddDays(1),
                itemInformationCollection: new Dictionary<string, object>
                {
                    { "InvoiceNumber", "INV-001" },
                    { "Amount", 1500.00 },
                    { "CustomerName", "Acme Corp" }
                },
                deferDate: DateTime.MinValue,
                priority: QueueItemPriority.High,
                reference: "ACME-INV-001",
                timeoutMS: 30000
            );
            Log("Queue item added.");

            // Add a simple queue item
            system.AddQueueItem("InvoiceQueue");

            // Get a transaction item for processing
            QueueItem transaction = system.GetTransactionItem("InvoiceQueue");

            if (transaction != null)
            {
                Log($"Processing: {transaction.Reference}");

                try
                {
                    // Process the item...
                    string invoiceNumber = transaction.SpecificContent["InvoiceNumber"].ToString();
                    ProcessInvoice(invoiceNumber);

                    // Update progress
                    system.SetTransactionProgress(transaction, "Invoice validated, posting...");

                    // Mark as successful
                    system.SetTransactionStatus(transaction, ProcessingStatus.Successful);
                }
                catch (Exception ex)
                {
                    // Mark as failed with business exception (will retry)
                    system.SetTransactionStatus(
                        transaction,
                        ProcessingStatus.Failed,
                        folderPath: null,
                        analytics: null,
                        output: null,
                        details: ex.Message,
                        errorType: ErrorType.BusinessException,
                        reason: "Invoice validation failed",
                        timeoutMS: 30000
                    );
                }
            }
        }

        private void ProcessInvoice(string invoiceNumber)
        {
            Log($"Processing invoice {invoiceNumber}");
        }
    }
}
```

### Bulk Add and Query Queue Items

```csharp
using System.Data;
using System.Collections.Generic;
using UiPath.Orchestrator.Client.Models;

namespace MyProject
{
    public class BulkQueueWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Build a DataTable with queue items
            var dt = new DataTable();
            dt.Columns.Add("InvoiceNumber", typeof(string));
            dt.Columns.Add("Amount", typeof(double));
            dt.Rows.Add("INV-001", 1000.00);
            dt.Rows.Add("INV-002", 2500.00);
            dt.Rows.Add("INV-003", 750.00);

            // Bulk add
            DataTable errors = system.BulkAddQueueItems(dt, "InvoiceQueue", folderPath: null);
            if (errors.Rows.Count > 0)
            {
                Log($"Errors adding {errors.Rows.Count} items.");
            }

            // Query queue items with filters
            IEnumerable<QueueItem> items = system.GetQueueItems(
                "InvoiceQueue",
                folderPath: null,
                duration: null,
                from: DateTime.Today,
                priority: null,
                queueItemStates: QueueItemStates.New,
                to: null,
                filterStrategy: ReferenceFilterStrategy.Contains,
                reference: "INV",
                skip: 0,
                top: 50,
                timeoutMS: 30000
            );

            foreach (QueueItem item in items)
            {
                Log($"Queue item: {item.Reference} - {item.Status}");
            }

            // Wait for an item to appear in queue
            QueueItem waited = system.WaitQueueItem("InvoiceQueue", folderPath: null, pollTimeMS: 5000);
            if (waited != null)
            {
                Log($"Item available: {waited.Reference}");
            }
        }
    }
}
```

### Postpone and Delete Queue Items

```csharp
using System.Collections.Generic;
using System.Linq;
using UiPath.Orchestrator.Client.Models;

namespace MyProject
{
    public class QueueManagementWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get a transaction
            QueueItem item = system.GetTransactionItem("ProcessingQueue");

            if (item != null)
            {
                // Postpone with defer and due dates
                system.PostponeTransactionItem(
                    item,
                    deferDate: DateTime.Now.AddHours(2),
                    folderPath: null,
                    dueDate: DateTime.Now.AddDays(1),
                    timeoutMS: 30000
                );
                Log("Item postponed.");
            }

            // Get and delete items in New state
            IEnumerable<QueueItem> newItems = system.GetQueueItems("CleanupQueue");
            if (newItems.Any())
            {
                system.DeleteQueueItems(newItems);
                Log($"Deleted {newItems.Count()} items.");
            }
        }
    }
}
```

---

## Assets & Credentials

### Get and Set Assets and Credentials

```csharp
using System.Security;

namespace MyProject
{
    public class AssetsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get a text asset
            object apiKeyObj = system.GetAsset("API_Key");
            string apiKey = apiKeyObj.ToString();
            Log($"API Key: {apiKey.Substring(0, 5)}...");

            // Get asset with caching
            object config = system.GetAsset("AppConfig", folderPath: null, cacheStrategy: CacheStrategyEnum.PerRobot);
            Log($"Config: {config}");

            // Set an asset value
            system.SetAsset(150, "ProcessedCount");
            Log("Updated ProcessedCount.");

            // Get credential (tuple return)
            (string userName, SecureString password) = system.GetCredential("DatabaseCredentials");
            Log($"Username: {userName}");

            // Get credential (out parameter return)
            string user = system.GetCredential("ERPCredentials", folderPath: null, out SecureString pwd, CacheStrategyEnum.None, timeoutMS: 30000);
            Log($"ERP user: {user}");

            // Set credential
            system.SetCredential("admin", "newPassword123", "ServiceAccount");
        }
    }
}
```

---

## Jobs & Processes

### Run and Manage Orchestrator Jobs

```csharp
using System.Collections.Generic;
using UiPath.Activities.System.Jobs.Coded;

namespace MyProject
{
    public class JobsWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Run a job and wait for completion
            var (jobData, outputJson) = system.RunJob(
                processName: "DataProcessor",
                orchestratorFolderPath: null,
                inputArguments: new { FilePath = @"C:\Data\input.xlsx", BatchSize = 100 }
            );
            Log($"Job completed. Output: {outputJson}");

            // Start a job without waiting (fire-and-forget)
            var (jobInfo, _) = system.RunJob(
                processName: "ReportGenerator",
                doNotWait: true
            );
            Log($"Job started.");

            // Start job with jobId output
            string processKey = system.StartJob("BackupProcess", folderPath: null, out string jobId);
            Log($"Started job {jobId}, process key: {processKey}");

            // Get running jobs
            IEnumerable<OrchestratorJob> runningJobs = system.GetJobs(
                filter: "State eq 'Running'",
                filterBuilder: null,
                folderPath: null,
                top: 10,
                skip: 0,
                timeoutMS: 30000
            );

            foreach (OrchestratorJob job in runningJobs)
            {
                Log($"Running job: {job.Key}");
            }

            // Stop a job gracefully
            foreach (OrchestratorJob job in runningJobs)
            {
                system.StopJob(job, StopStrategy.Stop);
                Log($"Stop requested for job: {job.Key}");
            }

            // Invoke a local process (blocks until complete)
            system.InvokeProcess("CleanupProcess");
            Log("Cleanup process completed.");
        }
    }
}
```

---

## Storage Buckets

### Upload, Download, and Manage Storage Files

```csharp
using System.Collections.Generic;
using UiPath.Core;
using UiPath.Core.Activities.Storage;

namespace MyProject
{
    public class StorageBucketWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Upload a file to storage bucket
            IResource localFile = system.GetResourceForLocalPath(@"C:\Reports\monthly.pdf", PathType.File);
            system.UploadStorageFile(
                "2026/February/monthly.pdf",
                localFile,
                "ReportsBucket"
            );
            Log("File uploaded.");

            // Download a file from storage bucket
            ILocalResource downloaded = system.DownloadStorageFile(
                "2026/February/monthly.pdf",
                "ReportsBucket",
                folderPath: null,
                destination: @"C:\Downloads"
            );
            Log($"Downloaded to: {downloaded.FullPath}");

            // List files in storage bucket
            IEnumerable<StorageFileInfo> files = system.ListStorageFiles(
                "2026/",
                "ReportsBucket",
                folderPath: null,
                recursive: true,
                filter: "*.pdf",
                timeoutMS: 30000
            );

            foreach (StorageFileInfo fileInfo in files)
            {
                Log($"Storage file: {fileInfo.FullPath}");
            }

            // Write text directly to storage bucket
            system.WriteStorageText(
                "logs/process_log.txt",
                $"Process completed at {DateTime.Now}",
                "LogsBucket"
            );

            // Read text from storage bucket
            string logContent = system.ReadStorageText(
                "logs/process_log.txt",
                "LogsBucket"
            );
            Log($"Log content: {logContent}");

            // Delete a file from storage bucket
            system.DeleteStorageFile("2026/February/monthly.pdf", "ReportsBucket");
            Log("Storage file deleted.");
        }
    }
}
```

---

## Alerts & Orchestrator HTTP

### Raise Alerts and Make HTTP Requests

```csharp
using System.Collections.Generic;

namespace MyProject
{
    public class AlertsAndHttpWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Raise alerts of different severities
            system.RaiseAlert(AlertSeverity.Info, "Process started successfully.");
            system.RaiseAlert(AlertSeverity.Warn, "Processing is taking longer than expected.");
            system.RaiseAlert(AlertSeverity.Error, "Failed to connect to external service.");

            // Make an Orchestrator HTTP GET request
            int statusCode = system.OrchestratorHTTPRequest(
                OrchestratorAPIHttpMethods.GET,
                "/odata/Robots",
                jSONPayload: null,
                folderPath: null,
                out Dictionary<string, string> headers,
                out string result
            );
            Log($"GET /odata/Robots - Status: {statusCode}");
            Log($"Response: {result}");

            // Make an Orchestrator HTTP POST request
            string payload = "{\"Name\": \"NewQueue\", \"Description\": \"Created via API\"}";
            int postStatus = system.OrchestratorHTTPRequest(
                OrchestratorAPIHttpMethods.POST,
                "/odata/QueueDefinitions",
                payload,
                folderPath: null,
                out Dictionary<string, string> postHeaders,
                out string postResult
            );
            Log($"POST status: {postStatus}");
        }
    }
}
```

---

## Network

### Download File from URL

```csharp
using System.Threading;
using UiPath.Core;
using UiPath.Core.Activities.Storage;

namespace MyProject
{
    public class DownloadFileWorkflow : CodedWorkflow
    {
        [Workflow]
        public async void Execute()
        {
            // Download a file from URL
            ILocalResource downloaded = await system.DownloadFileFromURLAsync(
                "https://example.com/data/report.csv",
                fileName: "report.csv",
                conflictResolution: FileConflictBehavior.Replace,
                timeout: 60000
            );
            Log($"Downloaded to: {downloaded.FullPath}");

            // Read the downloaded file
            string content = system.ReadTextFile(downloaded);
            Log($"File size: {content.Length} characters.");
        }
    }
}
```

---

## Complete Example — File Processing Pipeline

```csharp
using System.Data;
using System.Collections.Generic;
using System.Globalization;
using UiPath.Core;
using UiPath.Core.Activities.Storage;
using UiPath.Orchestrator.Client.Models;

namespace MyProject
{
    public class FileProcessingPipeline : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get configuration from Orchestrator assets
            string inputFolder = system.GetAsset("InputFolder").ToString();
            string archiveBucket = system.GetAsset("ArchiveBucket").ToString();

            // Check input folder exists
            if (!system.FolderExists(inputFolder))
            {
                system.RaiseAlert(AlertSeverity.Error, $"Input folder not found: {inputFolder}");
                return;
            }

            // Build a DataTable for tracking
            var tracker = new DataTable();
            tracker.Columns.Add("FileName", typeof(string));
            tracker.Columns.Add("Status", typeof(string));
            tracker.Columns.Add("ProcessedAt", typeof(string));

            // Process files — simulate finding files
            string[] fileNames = { "invoice_001.pdf", "invoice_002.pdf", "invoice_003.pdf" };

            foreach (string fileName in fileNames)
            {
                string filePath = $@"{inputFolder}\{fileName}";

                if (!system.FileExists(filePath))
                {
                    Log($"File not found: {fileName}");
                    continue;
                }

                try
                {
                    // Read the file
                    IResource fileResource = system.GetResourceForLocalPath(filePath, PathType.File);

                    // Upload to storage bucket
                    string datePath = system.FormatDateAsText(DateTime.Now, "yyyy/MM/dd", CultureInfo.InvariantCulture);
                    system.UploadStorageFile($"{datePath}/{fileName}", fileResource, archiveBucket);

                    // Add queue item for downstream processing
                    system.AddQueueItem(
                        "InvoiceProcessing",
                        folderPath: null,
                        dueDate: DateTime.Now.AddHours(4),
                        itemInformationCollection: new Dictionary<string, object>
                        {
                            { "FileName", fileName },
                            { "StoragePath", $"{datePath}/{fileName}" },
                            { "UploadedAt", DateTime.Now.ToString("o") }
                        },
                        deferDate: DateTime.MinValue,
                        priority: QueueItemPriority.Normal,
                        reference: fileName,
                        timeoutMS: 30000
                    );

                    // Track success
                    DataRow row = tracker.NewRow();
                    row["FileName"] = fileName;
                    row["Status"] = "Uploaded";
                    row["ProcessedAt"] = system.FormatDateAsText(DateTime.Now, "HH:mm:ss", CultureInfo.InvariantCulture);
                    system.AddDataRow(ref tracker, row);

                    Log($"Processed: {fileName}");
                }
                catch (Exception ex)
                {
                    DataRow row = tracker.NewRow();
                    row["FileName"] = fileName;
                    row["Status"] = $"Error: {ex.Message}";
                    row["ProcessedAt"] = system.FormatDateAsText(DateTime.Now, "HH:mm:ss", CultureInfo.InvariantCulture);
                    system.AddDataRow(ref tracker, row);

                    system.RaiseAlert(AlertSeverity.Warn, $"Failed to process {fileName}: {ex.Message}");
                }
            }

            // Sort and output tracking report
            DataTable sorted = system.SortDataTable(tracker, "FileName", SortOrder.Ascending);
            string report = system.OutputDataTable(sorted);
            Log($"Processing Report:\n{report}");

            // Write report to storage
            system.WriteStorageText(
                $"reports/processing_{system.FormatDateAsText(DateTime.Now, "yyyyMMdd_HHmmss", CultureInfo.InvariantCulture)}.csv",
                report,
                archiveBucket
            );
        }
    }
}
```

## Complete Example — Queue Transaction Processing with Retry

```csharp
using System.Collections.Generic;
using System.Security;
using UiPath.Core;
using UiPath.Core.Activities.Storage;
using UiPath.Orchestrator.Client.Models;

namespace MyProject
{
    public class TransactionProcessorWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get credentials
            (string userName, SecureString password) = system.GetCredential("ERPCredentials");

            // Process queue items in a loop
            QueueItem transaction = system.GetTransactionItem("OrderQueue");

            while (transaction != null)
            {
                try
                {
                    string orderId = transaction.SpecificContent["OrderId"].ToString();
                    system.SetTransactionProgress(transaction, $"Processing order {orderId}");

                    // Validate order
                    double amount = Convert.ToDouble(transaction.SpecificContent["Amount"]);
                    if (amount <= 0)
                    {
                        throw new Exception("Invalid order amount — business rule violation.");
                    }

                    system.SetTransactionProgress(transaction, $"Posting order {orderId} to ERP");

                    // Download supporting documents
                    ILocalResource doc = system.DownloadStorageFile(
                        $"orders/{orderId}.pdf",
                        "OrderDocuments"
                    );
                    Log($"Downloaded document: {doc.FullPath}");

                    // Mark as successful with output data
                    system.SetTransactionStatus(
                        transaction,
                        ProcessingStatus.Successful,
                        folderPath: null,
                        analytics: new Dictionary<string, object>
                        {
                            { "ProcessingTimeMs", 1500 },
                            { "OrderAmount", amount }
                        },
                        output: new Dictionary<string, object>
                        {
                            { "ERPReference", $"ERP-{orderId}" },
                            { "PostedAt", DateTime.Now.ToString("o") }
                        },
                        details: null,
                        errorType: ErrorType.ApplicationException,
                        reason: null,
                        timeoutMS: 30000
                    );

                    Log($"Successfully processed order {orderId}.");
                }
                catch (Exception ex)
                {
                    // Determine error type
                    bool isBusinessError = ex.Message.Contains("business rule");
                    ErrorType errType = isBusinessError
                        ? ErrorType.BusinessException
                        : ErrorType.ApplicationException;

                    system.SetTransactionStatus(
                        transaction,
                        ProcessingStatus.Failed,
                        folderPath: null,
                        analytics: null,
                        output: null,
                        details: ex.Message,
                        errorType: errType,
                        reason: isBusinessError ? "Business rule violation" : "System error",
                        timeoutMS: 30000
                    );

                    system.RaiseAlert(
                        isBusinessError ? AlertSeverity.Warn : AlertSeverity.Error,
                        $"Transaction failed: {ex.Message}"
                    );
                }

                // Get next transaction
                transaction = system.GetTransactionItem("OrderQueue");
            }

            Log("All queue items processed.");
        }
    }
}
```
