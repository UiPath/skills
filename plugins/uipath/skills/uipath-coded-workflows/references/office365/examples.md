# Microsoft 365 Examples

Examples using the `office365` service from `UiPath.MicrosoftOffice365.Activities` package.

**Required package:** `"UiPath.MicrosoftOffice365.Activities": "[3.6.10]"`

> **Prerequisites:** All examples require Integration Service connections configured in UiPath Automation Cloud. The `connections` property provides typed access to configured connections. Studio auto-generates `ConnectionsManager.cs` and `ConnectionsFactory.cs` in `.codedworkflows/` with the available connection names.

---

## Send a Simple Email

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class SendSimpleEmail : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            mailService.SendEmail(
                to: "recipient@example.com",
                subject: "Automation Complete",
                body: "The process finished successfully."
            );

            Log("Email sent.");
        }
    }
}
```

## Send an Email with Builder Pattern

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class SendRichEmail : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            mailService.SendEmail(new SendEmailRequest()
                .WithTo("manager@company.com")
                .WithCc("team-lead@company.com")
                .WithBcc("archive@company.com")
                .WithSubject("Monthly Report - " + DateTime.Now.ToString("MMMM yyyy"))
                .WithBody("<h1>Report</h1><p>All invoices processed.</p>", isHtml: true)
                .WithAttachment("C:\\Reports\\monthly.pdf")
                .WithImportance(MailImportance.High)
            );

            Log("Rich email sent.");
        }
    }
}
```

## Save Email as Draft

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class SaveDraft : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            mailService.SendEmail(
                to: "recipient@example.com",
                subject: "Draft - Needs Review",
                body: "This email is saved as a draft for review.",
                asDraft: true
            );

            Log("Draft saved.");
        }
    }
}
```

## Read and Process Emails

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ReadEmails : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            // Get emails from Inbox, newest first, limit to 20
            var emails = mailService.GetEmails(
                folder: mailService.SystemFolders.Inbox,
                orderBy: OrderBy.NewestFirst,
                markAsRead: true,
                maxResults: 20
            );

            Log($"Found {emails.Count} emails.");

            foreach (var email in emails)
            {
                Log($"From: {email.Item.FromAddress} | Subject: {email.Subject}");

                if (email.Subject.Contains("Invoice"))
                {
                    email.MoveTo(mailService.SystemFolders.Archive);
                    Log($"Archived invoice email: {email.Subject}");
                }
            }
        }
    }
}
```

## Read Emails with Filter

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class FilteredEmails : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            // Note: MailFilter string operators only support Contains and NotContains
            var filter = new MailFilter()
                .BySubject(FilterStringOperator.Contains, "Invoice")
                .And()
                .ByFrom(FilterStringOperator.Contains, "accounting")
                .And()
                .ByDate(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-7));

            var emails = mailService.GetEmails(filter: filter, maxResults: 50);

            Log($"Found {emails.Count} matching emails.");

            foreach (var email in emails)
            {
                Log($"Invoice email: {email.Subject} from {email.Item.FromAddress}");
            }
        }
    }
}
```

## Forward and Reply to Email

```csharp
using System;
using System.Linq;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ForwardAndReply : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            var newest = mailService.GetNewestEmail(markAsRead: true);

            if (newest != null)
            {
                // Forward to manager
                mailService.ForwardEmail(newest,
                    body: "Please review this message.",
                    to: "manager@company.com");

                // Reply to sender
                mailService.ReplyToEmail(newest,
                    body: "Thank you, we received your message and will respond shortly.");

                Log($"Forwarded and replied to: {newest.Subject}");
            }
        }
    }
}
```

## Download Email Attachments

```csharp
using System;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class DownloadAttachments : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            var filter = new MailFilter()
                .WithAttachments(true)
                .And()
                .BySubject(FilterStringOperator.Contains, "Report");

            var emails = mailService.GetEmails(filter: filter, maxResults: 5);

            foreach (var email in emails)
            {
                var attachments = mailService.DownloadEmailAttachments(email);

                foreach (var kvp in attachments)
                {
                    var savePath = Path.Combine("C:\\Downloads", kvp.Key.Name);
                    using (var fileStream = File.Create(savePath))
                    {
                        kvp.Value.CopyTo(fileStream);
                    }
                    Log($"Saved attachment: {kvp.Key.Name}");
                }
            }
        }
    }
}
```

## Create a Calendar Event

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class CreateCalendarEvent : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var calendarService = office365.Calendar(mailConn);

            var defaultCal = calendarService.GetDefaultCalendar();

            var meeting = calendarService.CreateEvent(defaultCal,
                new CreateEventRequest()
                    .WithTitle("Sprint Review")
                    .WithStartDate(DateTime.Today.AddDays(1).AddHours(14))
                    .WithEndDate(DateTime.Today.AddDays(1).AddHours(15))
                    .WithTimezone("Eastern Standard Time")
                    .WithDescription("<p>Review sprint deliverables.</p>", isHtml: true)
                    .AddRequiredAttendees("alice@company.com", "bob@company.com")
                    .AddOptionalAttendees("charlie@company.com")
                    .WithImportance(Importance.Normal)
                    .ShowAs(FreeBusyStatus.Busy)
            );

            Log($"Created event: {meeting.Item.Subject} at {meeting.Item.StartDateTime}");
        }
    }
}
```

## Get and Update Calendar Events

```csharp
using System;
using System.Linq;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ManageCalendarEvents : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var calendarService = office365.Calendar(mailConn);

            // Get events for next 7 days (top defaults to 50)
            var events = calendarService.GetEvents(
                startDate: DateTime.Today,
                endDate: DateTime.Today.AddDays(7),
                top: 20
            );

            Log($"Found {events.Count} events in the next 7 days.");

            foreach (var evt in events)
            {
                Log($"Event: {evt.Item.Subject} on {evt.Item.StartDateTime}");

                // Update a specific event
                if (evt.Item.Subject.Contains("Sprint Review"))
                {
                    // UpdateEventRequest requires the event in its constructor
                    calendarService.UpdateEvent(evt,
                        new UpdateEventRequest(evt)
                            .WithDescription("Updated agenda: Demo new features.")
                            .AddRequiredAttendees("dave@company.com")
                    );
                    Log("Updated Sprint Review event.");
                }
            }
        }
    }
}
```

## RSVP to Calendar Event

```csharp
using System;
using System.Linq;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class RsvpToEvent : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var calendarService = office365.Calendar(mailConn);

            var events = calendarService.GetEvents(
                startDate: DateTime.Today,
                endDate: DateTime.Today.AddDays(30)
            );

            foreach (var evt in events)
            {
                if (evt.Item.Subject.Contains("Team Meeting"))
                {
                    calendarService.RespondToEvent(evt, new RsvpRequest
                    {
                        Response = EventResponseType.Accept,
                        Comment = "I'll attend.",
                        SendResponseNotification = true
                    });
                    Log($"Accepted: {evt.Item.Subject}");
                }
            }
        }
    }
}
```

## Upload Files to OneDrive

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class UploadToOneDrive : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.OneDrive.Shared_tenant_onmicrosoft_com;
            var driveService = office365.OneDrive(driveConn);

            // Create a folder (default conflict: Fail)
            var reportsFolder = driveService.CreateFolder("MonthlyReports",
                conflictBehavior: ConflictBehavior.Rename);

            // Upload a file (default conflict: Replace)
            var uploadedFile = driveService.UploadFile(
                "C:\\Reports\\report.pdf",
                destination: reportsFolder
            );

            Log($"Uploaded: {uploadedFile.Name} to {reportsFolder.Name}");

            // Share the file with an anonymous view link
            string shareLink = driveService.ShareFile(uploadedFile,
                permission: GranteePermission.View);
            Log($"Share link: {shareLink}");
        }
    }
}
```

## List and Download OneDrive Files

```csharp
using System;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ListOneDriveFiles : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.OneDrive.Shared_tenant_onmicrosoft_com;
            var driveService = office365.OneDrive(driveConn);

            // List PDF files modified in last 30 days
            var filter = new DriveItemFilter()
                .ByFileExtension(FilterStringOperator.Equals, ".pdf")
                .And()
                .ByLastModifiedDate(FilterDateOperator.NewerThan, DateTime.Now.AddDays(-30));

            var files = driveService.GetFiles(filter, maxResults: 10);

            foreach (var file in files)
            {
                Log($"File: {file.FullName}");

                // Download the file
                using (var stream = driveService.DownloadFile(file))
                using (var fileStream = File.Create(Path.Combine("C:\\Downloads", file.Name)))
                {
                    stream.CopyTo(fileStream);
                }
                Log($"Downloaded: {file.Name}");
            }
        }
    }
}
```

## Share Files with Specific People

```csharp
using System;
using System.Collections.Generic;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ShareWithPeople : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.OneDrive.Shared_tenant_onmicrosoft_com;
            var driveService = office365.OneDrive(driveConn);

            var file = driveService.GetFile("https://company.sharepoint.com/sites/team/Shared Documents/report.xlsx");

            // Share with specific people
            string shareLink = driveService.ShareFile(file,
                recipients: new List<string> { "alice@company.com", "bob@company.com" },
                message: "Please review this report.",
                sendSharingInvitationEmail: true,
                permission: GranteePermission.Edit
            );

            Log($"Shared with team: {shareLink}");
        }
    }
}
```

## Work with O365 Cloud Excel

```csharp
using System;
using System.Data;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class CloudExcel : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var excelConn = connections.Excel.Shared_tenant_onmicrosoft_com;
            var excelService = office365.Excel(excelConn);

            // Get workbooks (maxResults defaults to 200)
            var workbooks = excelService.GetWorkbooks(search: "Budget");
            Log($"Found {workbooks.Count} workbooks.");

            foreach (var workbook in workbooks)
            {
                var sheets = excelService.GetSheets(workbook);

                foreach (var sheet in sheets)
                {
                    // Read data from sheet (hasHeaders defaults to true)
                    DataTable data = excelService.ReadRange(workbook, sheet);
                    Log($"Workbook: {workbook.Name}, Sheet: {sheet.Name}, Rows: {data.Rows.Count}");

                    // Write a new row (writeMode defaults to Append)
                    excelService.WriteRow(workbook, sheet,
                        new object[] { "New Item", DateTime.Now.ToString(), 100.00 });
                }
            }
        }
    }
}
```

## Work with SharePoint Lists

```csharp
using System;
using System.Data;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class SharepointList : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var driveConn = connections.OneDrive.Shared_tenant_onmicrosoft_com;
            var spService = office365.Sharepoint(driveConn);

            // Get a SharePoint list
            var list = spService.GetList(
                siteIdentifier: "https://company.sharepoint.com/sites/team",
                listIdentifier: "Tasks",
                useDisplayNamesAsColumnNames: true
            );

            // Read items with filter (created via list.CreateFilter())
            // Note: SharePoint string operators only support Equals and NotEquals
            var filter = list.CreateFilter()
                .By("Status", FilterStringOperator.Equals, "Active")
                .And()
                .By("Priority", FilterIntOperator.GreaterThan, 2);

            DataTable items = spService.GetItems(list, filter: filter);
            Log($"Found {items.Rows.Count} active high-priority tasks.");

            // Add a new item
            DataRow newItem = spService.CreateItem(list);
            newItem["Title"] = "Automation Task";
            newItem["Status"] = "Active";
            newItem["Priority"] = 5;
            spService.AddItem(list, newItem);

            Log("Added new SharePoint list item.");
        }
    }
}
```

## Set Up Automatic Replies (Out of Office)

```csharp
using System;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class AutoReply : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var mailService = office365.Mail(mailConn);

            mailService.TurnOnAutomaticReplies(
                internalMessage: "I'm out of office until Monday. For urgent matters, contact manager@company.com.",
                externalMessage: "Thank you for your email. I'm currently out of office and will respond on Monday.",
                startTime: DateTimeOffset.Now,
                endTime: DateTimeOffset.Now.AddDays(3),
                sendRepliesOutsideOrganization: true
            );

            Log("Automatic replies enabled.");
        }
    }
}
```

## End-to-End: Process Invoices from Email to SharePoint

```csharp
using System;
using System.Data;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.MicrosoftOffice365.Activities.Api;

namespace MyProject
{
    public class ProcessInvoices : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var mailConn = connections.O365Mail.My_Workspace_user_company_com;
            var driveConn = connections.OneDrive.Shared_tenant_onmicrosoft_com;

            var mailService = office365.Mail(mailConn);
            var driveService = office365.OneDrive(driveConn);
            var spService = office365.Sharepoint(driveConn);

            // 1. Get invoice emails
            var filter = new MailFilter()
                .BySubject(FilterStringOperator.Contains, "Invoice")
                .And()
                .WithAttachments(true)
                .And()
                .ByUnread(true);

            var emails = mailService.GetEmails(filter: filter, markAsRead: true, maxResults: 10);
            Log($"Found {emails.Count} invoice emails.");

            // 2. Get SharePoint list for tracking
            var invoiceList = spService.GetList(
                "https://company.sharepoint.com/sites/finance",
                "Invoices",
                useDisplayNamesAsColumnNames: true);

            // 3. Get OneDrive folder for attachments
            var invoiceFolder = driveService.CreateFolder("Invoices_" + DateTime.Now.ToString("yyyy-MM"),
                conflictBehavior: ConflictBehavior.Rename);

            foreach (var email in emails)
            {
                // Save attachments to OneDrive
                var attachments = mailService.DownloadEmailAttachments(email);
                foreach (var kvp in attachments)
                {
                    driveService.UploadFile(kvp.Value, kvp.Key.Name,
                        destination: invoiceFolder,
                        conflictBehavior: ConflictBehavior.Rename);
                    Log($"Uploaded: {kvp.Key.Name}");
                }

                // Add entry to SharePoint list
                DataRow row = spService.CreateItem(invoiceList);
                row["Title"] = email.Subject;
                row["From"] = email.Item.FromAddress;
                row["ReceivedDate"] = email.Item.ReceivedDateTime?.ToString("o");
                row["Status"] = "Pending Review";
                spService.AddItem(invoiceList, row);

                // Archive the email
                email.Archive();
                Log($"Processed invoice: {email.Subject}");
            }

            // 4. Send summary notification
            mailService.SendEmail(
                to: "finance-team@company.com",
                subject: $"Invoice Processing Complete - {emails.Count} invoices",
                body: $"Processed {emails.Count} invoice emails. Attachments saved to OneDrive folder '{invoiceFolder.Name}'."
            );

            Log("Invoice processing complete.");
        }
    }
}
```
