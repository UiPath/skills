# Mail Examples

Examples using the `mail` service from `UiPath.Mail.Activities` package.

**Required package:** `"UiPath.Mail.Activities": "[2.5.10]"`

---

## Send Email via Outlook

```csharp
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class SendOutlookEmailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            mail.Outlook().SendMail(
                new SendOutlookMailOptions()
                    .WithTo(new List<string> { "recipient@example.com" })
                    .WithSubject("Monthly Report")
                    .WithBody("Please find the report attached.")
                    .WithAttachments(new List<string> { @"C:\Reports\report.pdf" })
            );

            Log("Email sent successfully.");
        }
    }
}
```

## Send HTML Email with CC and BCC via Outlook

```csharp
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class SendHtmlEmailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            mail.Outlook().SendMail(
                new SendOutlookMailOptions()
                    .WithTo(new List<string> { "manager@company.com" })
                    .WithCc(new List<string> { "team@company.com" })
                    .WithBcc(new List<string> { "archive@company.com" })
                    .WithSubject("Weekly Status Update")
                    .WithBody("<h1>Status Update</h1><p>All tasks completed.</p>")
                    .WithHtmlBody(true)
                    .WithImportance(MailImportance.High)
            );
        }
    }
}
```

## Save Email as Draft in Outlook

```csharp
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class SaveDraftWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            mail.Outlook().SendMail(
                new SendOutlookMailOptions()
                    .WithTo(new List<string> { "recipient@example.com" })
                    .WithSubject("Draft - Review Needed")
                    .WithBody("This is a draft email for review.")
                    .AsDraft(true)
            );

            Log("Draft saved.");
        }
    }
}
```

## Read Outlook Mail and Process

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class ReadOutlookMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var messages = mail.Outlook().GetMessages(
                new GetOutlookMailOptions()
                    .WithFolder("Inbox")
                    .WithOnlyUnreadMessages(true)
                    .WithTop(20)
                    .WithOrder(EOrderByDate.NewestFirst)
            );

            Log($"Found {messages.Count} unread messages.");

            foreach (MailMessage message in messages)
            {
                Log($"From: {message.From} | Subject: {message.Subject}");

                if (message.Subject.Contains("Invoice"))
                {
                    mail.Outlook().MoveMail(message, "Invoices");
                    Log($"Moved invoice email to Invoices folder.");
                }
            }
        }
    }
}
```

## Read Mail with Filter and Mark as Read

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class FilteredMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var messages = mail.Outlook().GetMessages(
                new GetOutlookMailOptions()
                    .WithFolder("Inbox")
                    .WithFilter("[Subject] = 'Approval Required'")
                    .WithMarkAsRead(true)
                    .WithGetAttachements(true)
                    .WithTop(10)
            );

            foreach (MailMessage message in messages)
            {
                Log($"Processing: {message.Subject}");

                // Save attachments
                foreach (var attachment in message.Attachments)
                {
                    Log($"Attachment: {attachment.Name}");
                }
            }
        }
    }
}
```

## Forward an Email via Outlook

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class ForwardMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            // Get the latest unread message
            var messages = mail.Outlook().GetMessages(
                new GetOutlookMailOptions()
                    .WithOnlyUnreadMessages(true)
                    .WithTop(1)
            );

            foreach (MailMessage message in messages)
            {
                // Forward it to another recipient
                mail.Outlook().SendMail(
                    new SendOutlookMailOptions()
                        .WithTo(new List<string> { "colleague@company.com" })
                        .WithSubject($"FW: {message.Subject}")
                        .WithBody("Please review the forwarded message below.")
                        .WithForwardedMessage(message)
                );

                Log($"Forwarded: {message.Subject}");
            }
        }
    }
}
```

## Delete and Manage Outlook Messages

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class ManageMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var outlook = mail.Outlook();

            var messages = outlook.GetMessages(
                new GetOutlookMailOptions()
                    .WithFolder("Inbox")
                    .WithOnlyUnreadMessages(false)
                    .WithTop(50)
            );

            foreach (MailMessage message in messages)
            {
                if (message.Subject.Contains("SPAM"))
                {
                    outlook.DeleteMail(message);
                    Log($"Deleted: {message.Subject}");
                }
                else if (message.Subject.Contains("Archive"))
                {
                    outlook.MoveMail(message, "Archive");
                    outlook.MarkRead(message);
                    Log($"Archived: {message.Subject}");
                }
            }
        }
    }
}
```

## Save Outlook Messages to Disk

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;
using UiPath.Mail.Outlook.Enums;

namespace MyProject
{
    public class SaveMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var messages = mail.Outlook().GetMessages(
                new GetOutlookMailOptions()
                    .WithFolder("Inbox")
                    .WithTop(5)
            );

            foreach (MailMessage message in messages)
            {
                // Save as Unicode .msg file
                mail.Outlook().SaveMail(message, @"C:\SavedMails",
                    saveAsType: ESaveMessageAsType.OutlookMessageFormatUnicode,
                    replaceExisting: true);

                Log($"Saved: {message.Subject}");
            }
        }
    }
}
```

## Set Categories on Outlook Messages

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class CategorizeMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var messages = mail.Outlook().GetMessages(
                new GetOutlookMailOptions()
                    .WithFolder("Inbox")
                    .WithOnlyUnreadMessages(true)
                    .WithTop(10)
            );

            foreach (MailMessage message in messages)
            {
                if (message.Subject.Contains("Urgent"))
                {
                    mail.Outlook().SetCategories(message, new List<string> { "Urgent", "Action Required" });
                }
            }
        }
    }
}
```

## Read Mail via IMAP

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class ImapMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var imapConnection = new ImapConnectionOptions("imap.gmail.com", 993)
                .WithEmail("user@gmail.com")
                .WithPassword("app-password")
                .WithSecureConnection(SecureSocketEncryption.SslOnConnect);

            var messages = mail.Imap(imapConnection).GetMessages(
                new GetImapMailOptions()
                    .WithFolder("Inbox")
                    .WithOnlyUnreadMessages(true)
                    .WithMarkAsRead(true)
                    .WithTop(10)
                    .WithOrder(EOrderByDate.NewestFirst)
            );

            Log($"Retrieved {messages.Count} messages via IMAP.");

            foreach (MailMessage message in messages)
            {
                Log($"Subject: {message.Subject}");
            }
        }
    }
}
```

## Read Mail via IMAP with Filter

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class ImapFilterWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var imapConnection = new ImapConnectionOptions("imap.example.com", 993)
                .WithEmail("user@example.com")
                .WithPassword("password")
                .WithSecureConnection(SecureSocketEncryption.SslOnConnect);

            var messages = mail.Imap(imapConnection).GetMessages(
                new GetImapMailOptions()
                    .WithFolder("Inbox")
                    .WithFilterExpression("SUBJECT \"Invoice\" SINCE 01-Jan-2026")
                    .WithTop(50)
            );

            foreach (MailMessage message in messages)
            {
                Log($"Invoice mail: {message.Subject} from {message.From}");
            }
        }
    }
}
```

## Send Email via SMTP

```csharp
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class SmtpMailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var smtpConnection = new MailConnectionOptions("smtp.gmail.com", 587)
                .WithEmail("sender@gmail.com")
                .WithPassword("app-password")
                .WithSecureConnection(SecureSocketEncryption.StartTls);

            mail.Smtp(smtpConnection).SendMail(
                new SendSmtpMailOptions()
                    .WithTo(new List<string> { "recipient@example.com" })
                    .WithSubject("Automated Report")
                    .WithBody("<h1>Report</h1><p>See attachment.</p>")
                    .WithHtmlBody(true)
                    .WithAttachments(new List<string> { @"C:\Reports\report.pdf" })
                    .WithSender("Automation Bot", "sender@gmail.com")
            );

            Log("Email sent via SMTP.");
        }
    }
}
```

## Read Mail via POP3

```csharp
using System.Net.Mail;
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class Pop3MailWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var pop3Connection = new MailConnectionOptions("pop.example.com", 995)
                .WithEmail("user@example.com")
                .WithPassword("password")
                .WithSecureConnection(SecureSocketEncryption.SslOnConnect);

            var messages = mail.Pop3(pop3Connection).GetMessages(
                new GetPop3MailOptions()
                    .WithTop(10)
                    .WithDeleteMessages(false)
            );

            Log($"Retrieved {messages.Count} messages via POP3.");

            foreach (MailMessage message in messages)
            {
                Log($"Subject: {message.Subject}");
            }
        }
    }
}
```

## Send on Behalf Of via Outlook

```csharp
using System.Collections.Generic;
using UiPath.Mail.Activities.Api;

namespace MyProject
{
    public class SendOnBehalfWorkflow : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            mail.Outlook().SendMail(
                new SendOutlookMailOptions()
                    .WithTo(new List<string> { "client@external.com" })
                    .WithSubject("Project Update")
                    .WithBody("Here is the latest project update.")
                    .WithAccount("shared@company.com")
                    .OnBehalfOf("manager@company.com")
                    .WithImportance(MailImportance.Normal)
                    .WithSensitivity(MailSensitivity.Confidential)
            );
        }
    }
}
```
