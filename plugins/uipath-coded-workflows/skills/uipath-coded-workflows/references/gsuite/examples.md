# Google Workspace (GSuite) Examples

Examples using the `google` service from `UiPath.GSuite.Activities` package.

**Required package:** `"UiPath.GSuite.Activities": "[3.6.10]"`

> **Prerequisites:** All examples require Integration Service connections configured in UiPath Automation Cloud (Google OAuth). The `connections` property provides typed access to configured connections. Studio auto-generates `ConnectionsManager.cs` and `ConnectionsFactory.cs` in `.codedworkflows/` with the available connection names.

---

## Send a Simple Email via Gmail

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class SendGmailSimple : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            gmailService.SendEmail(
                to: "recipient@example.com",
                subject: "Automation Complete",
                body: "The process finished successfully."
            );

            Log("Email sent via Gmail.");
        }
    }
}
```

## Send a Rich Email with Builder Pattern

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class SendGmailRich : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            gmailService.SendEmail(new SendEmailRequest()
                .WithTo("manager@company.com")
                .WithCc("team-lead@company.com")
                .WithSubject("Monthly Report - " + DateTime.Now.ToString("MMMM yyyy"))
                .WithBody("<h1>Report</h1><p>All tasks completed.</p>", isHtml: true)
                .WithAttachment("C:\\Reports\\monthly.pdf")
                .WithImportance(GMailImportance.High)
            );

            Log("Rich email sent via Gmail.");
        }
    }
}
```

## Read and Process Gmail Messages

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class ReadGmail : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            // Get unread emails from Inbox
            var emails = gmailService.GetEmails(
                folder: gmailService.SystemFolders.Inbox,
                markAsRead: true,
                maxResults: 20
            );

            Log($"Found {emails.Count} emails.");

            foreach (var email in emails)
            {
                Log($"From: {email.Item.FromAddress} | Subject: {email.Subject}");

                if (email.Subject.Contains("Invoice"))
                {
                    email.Archive();
                    Log($"Archived invoice email: {email.Subject}");
                }
            }
        }
    }
}
```

## Read Gmail with Filter

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class FilteredGmail : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            var filter = new MailFilter()
                .BySubject(FilterStringOperator.Contains, "Invoice")
                .And()
                .ByFrom(FilterStringOperator.Contains, "accounting")
                .And()
                .ByUnread(true)
                .And()
                .ByDateAndTime(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-7));

            var emails = gmailService.GetEmails(filter: filter, maxResults: 50);
            Log($"Found {emails.Count} matching emails.");

            foreach (var email in emails)
            {
                Log($"Invoice: {email.Subject} from {email.Item.FromAddress}");
            }
        }
    }
}
```

## Download Gmail Attachments

```csharp
using System;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class DownloadGmailAttachments : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            var filter = new MailFilter()
                .WithAttachments(true)
                .And()
                .ByFilename(FilterStringOperator.Contains, ".pdf");

            var emails = gmailService.GetEmails(filter: filter, maxResults: 5);

            foreach (var email in emails)
            {
                var attachments = gmailService.DownloadEmailAttachments(email);

                foreach (var kvp in attachments)
                {
                    var savePath = Path.Combine("C:\\Downloads", kvp.Key.Name);
                    using (var fileStream = File.Create(savePath))
                    {
                        kvp.Value.CopyTo(fileStream);
                    }
                    Log($"Saved: {kvp.Key.Name}");
                }
            }
        }
    }
}
```

## Create a Google Calendar Event

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class CreateGoogleEvent : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var calendarService = google.Calendar(gmailConn);

            var defaultCal = calendarService.GetDefaultCalendar();

            var meeting = calendarService.CreateEvent(defaultCal,
                new CreateCalendarItem()
                    .WithTitle("Sprint Planning")
                    .WithStartDate(DateTimeOffset.Now.AddDays(1).AddHours(10))
                    .WithEndDate(DateTimeOffset.Now.AddDays(1).AddHours(11))
                    .WithTimezone("America/New_York")
                    .NewDescription("Plan next sprint work items")
                    .AddRequiredAttendees("alice@company.com", "bob@company.com")
                    .AddOptionalAttendees("charlie@company.com")
                    .WithConferenceData(true)
            );

            Log($"Created event: {meeting.Item.Summary} at {meeting.Item.StartDateTime}");
        }
    }
}
```

## Get and Manage Calendar Events

```csharp
using System;
using System.Linq;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class ManageGoogleEvents : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var calendarService = google.Calendar(gmailConn);

            // Get events for next 7 days
            var events = calendarService.GetEvents(
                startDate: DateTimeOffset.Now,
                endDate: DateTimeOffset.Now.AddDays(7),
                top: 20
            );

            Log($"Found {events.Count} events in the next 7 days.");

            foreach (var evt in events)
            {
                Log($"Event: {evt.Item.Summary} on {evt.Item.StartDateTime}");

                // RSVP to an event
                if (evt.Item.Summary.Contains("Team Meeting"))
                {
                    calendarService.RespondToEvent(evt,
                        EventResponseType.Accepted,
                        comment: "I'll be there!");
                    Log("Accepted Team Meeting.");
                }
            }
        }
    }
}
```

## Upload Files to Google Drive

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class UploadToGDrive : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.GoogleDrive.My_Workspace_user_company_com;
            var driveService = google.Drive(driveConn);

            // Create a folder
            var reportsFolder = driveService.CreateFolder("MonthlyReports",
                description: "Auto-generated reports",
                conflictBehavior: ConflictBehavior.Rename);

            // Upload a file
            var uploadedFile = driveService.UploadFile(
                "C:\\Reports\\report.pdf",
                destination: reportsFolder,
                conflictBehavior: ConflictBehavior.Replace
            );

            Log($"Uploaded: {uploadedFile.FullName}");

            // Share with specific people
            string shareLink = driveService.ShareFile(uploadedFile,
                GranteeType.User,
                "colleague@company.com",
                sendNotificationEmail: true,
                role: Role.Reader);

            Log($"Shared with colleague: {shareLink}");
        }
    }
}
```

## List and Download Google Drive Files

```csharp
using System;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class ListGDriveFiles : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.GoogleDrive.My_Workspace_user_company_com;
            var driveService = google.Drive(driveConn);

            // Filter by type and date
            var filter = new DriveItemFilter()
                .ByType(FilterListOptionOperator.Is, FileTypes.GoogleSpreadsheet)
                .And()
                .ByCreationDate(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-30));

            var files = driveService.GetFiles(filter: filter, maxResults: 10);

            foreach (var file in files)
            {
                Log($"File: {file.FullName}");

                // Download Google Sheet as XLSX
                using (var stream = driveService.DownloadFile(file,
                    new DownloadOptions { SpreadsheetExportFormat = GSheetExportFormat.Xlsx }))
                using (var fileStream = File.Create(
                    Path.Combine("C:\\Downloads", file.FullName + ".xlsx")))
                {
                    stream.CopyTo(fileStream);
                }
                Log($"Downloaded as XLSX: {file.FullName}");
            }
        }
    }
}
```

## Work with Google Sheets

```csharp
using System;
using System.Data;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class GoogleSheetsWork : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var sheetsConn = connections.GoogleSheets.My_Workspace_user_company_com;
            var sheetsService = google.Sheets(sheetsConn);

            // Get spreadsheets
            var spreadsheets = sheetsService.GetSpreadsheets();
            Log($"Found {spreadsheets.Count} spreadsheets.");

            foreach (var spreadsheet in spreadsheets)
            {
                if (spreadsheet.Name.Contains("Budget"))
                {
                    var sheets = sheetsService.GetSheets(spreadsheet);

                    foreach (var sheet in sheets)
                    {
                        // Read data
                        DataTable data = sheetsService.ReadRange(spreadsheet, sheet, hasHeaders: true);
                        Log($"Sheet: {sheet.Name}, Rows: {data.Rows.Count}");

                        // Append a new row
                        sheetsService.WriteRow(spreadsheet, sheet,
                            new object[] { "New Item", DateTime.Now.ToString(), 100.00 },
                            writeMode: RangeWriteMode.Append);
                    }
                }
            }
        }
    }
}
```

## Work with Google Docs

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class GoogleDocsWork : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var docsConn = connections.GoogleDocs.My_Workspace_user_company_com;
            var docsService = google.Docs(docsConn);

            // Get documents
            var documents = docsService.GetDocuments();

            foreach (var doc in documents)
            {
                if (doc.Name.Contains("Template"))
                {
                    // Read text content
                    string content = docsService.ReadText(doc);
                    Log($"Document: {doc.Name}, Length: {content.Length}");

                    // Find and replace
                    docsService.FindAndReplaceText(doc,
                        searchTerm: "PLACEHOLDER",
                        replacement: "Actual Value",
                        matchCase: true,
                        recurrences: TextRecurrences.AllRecurrences);

                    Log($"Updated placeholders in: {doc.Name}");
                }
            }
        }
    }
}
```

## Fill a Google Docs Template

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class FillDocTemplate : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var docsConn = connections.GoogleDocs.My_Workspace_user_company_com;
            var driveConn = connections.GoogleDrive.My_Workspace_user_company_com;

            var docsService = google.Docs(docsConn);
            var driveService = google.Drive(driveConn);

            // Get the template document
            var docs = docsService.GetDocuments();
            IDocument template = null;
            foreach (var doc in docs)
            {
                if (doc.Name == "Invoice Template")
                {
                    template = doc;
                    break;
                }
            }

            if (template != null)
            {
                // Copy the template via Drive
                var templateFile = driveService.GetFile(template.Id);
                var rootFolder = driveService.GetFolder();
                var copy = driveService.CopyFile(templateFile, rootFolder, newName: "Invoice-2026-001");

                // Retrieve the copy as a document by searching for it
                var allDocs = docsService.GetDocuments();
                IDocument invoice = null;
                foreach (var doc in allDocs)
                {
                    if (doc.Name == "Invoice-2026-001")
                    {
                        invoice = doc;
                        break;
                    }
                }

                if (invoice != null)
                {
                    // Fill template placeholders (e.g. {{CustomerName}}, {{Amount}})
                    docsService.FillDocumentTemplate(invoice,
                        new Dictionary<string, string>
                        {
                            { "CustomerName", "Acme Corp" },
                            { "InvoiceNumber", "INV-2026-001" },
                            { "Amount", "$1,500.00" },
                            { "DueDate", "March 15, 2026" }
                        },
                        symbol: "{{ }}"
                    );

                    Log("Invoice generated from template.");
                }
            }
        }
    }
}
```

## Set Up Automatic Replies in Gmail

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class GmailAutoReply : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var gmailService = google.Gmail(gmailConn);

            gmailService.TurnOnAutomaticReplies(
                subject: "Out of Office",
                body: "I'm currently out of office. I'll respond when I return on Monday.",
                startTime: DateTimeOffset.Now,
                endTime: DateTimeOffset.Now.AddDays(3),
                sendRepliesOutsideOrganization: true
            );

            Log("Gmail auto-reply enabled.");
        }
    }
}
```

## End-to-End: Process Reports from Gmail to Google Drive and Sheets

```csharp
using System;
using System.Data;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.GSuite.Activities.Api;

namespace MyProject
{
    public class ProcessReports : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var gmailConn = connections.Gmail.My_Workspace_user_company_com;
            var driveConn = connections.GoogleDrive.My_Workspace_user_company_com;
            var sheetsConn = connections.GoogleSheets.My_Workspace_user_company_com;

            var gmailService = google.Gmail(gmailConn);
            var driveService = google.Drive(driveConn);
            var sheetsService = google.Sheets(sheetsConn);

            // 1. Get report emails with attachments
            var filter = new MailFilter()
                .BySubject(FilterStringOperator.Contains, "Weekly Report")
                .And()
                .WithAttachments(true)
                .And()
                .ByUnread(true);

            var emails = gmailService.GetEmails(filter: filter, markAsRead: true, maxResults: 10);
            Log($"Found {emails.Count} report emails.");

            // 2. Create Drive folder for reports
            var folder = driveService.CreateFolder(
                "Reports_" + DateTime.Now.ToString("yyyy-MM"),
                conflictBehavior: ConflictBehavior.Rename);

            // 3. Get tracking spreadsheet
            var spreadsheets = sheetsService.GetSpreadsheets();
            ISpreadsheet tracker = null;
            foreach (var ss in spreadsheets)
            {
                if (ss.Name == "Report Tracker")
                {
                    tracker = ss;
                    break;
                }
            }

            foreach (var email in emails)
            {
                // Save attachments to Drive
                var attachments = gmailService.DownloadEmailAttachments(email);
                foreach (var kvp in attachments)
                {
                    driveService.UploadFile(kvp.Value, kvp.Key.Name,
                        destination: folder,
                        conflictBehavior: ConflictBehavior.Rename);
                    Log($"Uploaded: {kvp.Key.Name}");
                }

                // Log to tracking spreadsheet
                if (tracker != null)
                {
                    var sheets = sheetsService.GetSheets(tracker);
                    foreach (var sheet in sheets)
                    {
                        sheetsService.WriteRow(tracker, sheet,
                            new object[]
                            {
                                email.Item.FromAddress,
                                email.Subject,
                                DateTime.Now.ToString("o"),
                                "Processed"
                            },
                            writeMode: RangeWriteMode.Append);
                        break; // write to first sheet only
                    }
                }

                email.Archive();
                Log($"Processed: {email.Subject}");
            }

            // 4. Send summary
            gmailService.SendEmail(
                to: "team@company.com",
                subject: $"Report Processing Complete - {emails.Count} reports",
                body: $"Processed {emails.Count} report emails. Files saved to Drive folder."
            );

            Log("Report processing complete.");
        }
    }
}
```
