# UiPath Coded Workflows — Solopreneur Examples

Real end-to-end coded workflow examples for common solopreneur automation tasks.

---

## Example 1: Invoice Data Extraction and Excel Export

**Scenario:** Extract key fields from PDF invoices and append rows to an Excel tracker automatically.

```csharp
using UiPath.CodedWorkflows;
using UiPath.Excel.Models;
using System.Collections.Generic;

namespace InvoiceAutomation
{
    public class ProcessInvoice : CodedWorkflow
    {
        [Workflow]
        public void Execute(string invoicePdfPath, string excelTrackerPath)
        {
            Log($"Processing invoice: {invoicePdfPath}");

            // Step 1: Read invoice data (parsed by upstream Document Understanding workflow)
            var invoiceNumber = system.GetAsset("LastInvoiceNumber");
            var vendorName    = "Acme Corp";     // from DU extraction
            var totalAmount   = 1250.00m;         // from DU extraction
            var invoiceDate   = System.DateTime.Today;

            // Step 2: Append to Excel tracker
            using var workbook = excel.Open(excelTrackerPath, hasHeaders: true, isReadOnly: false);
            var sheet = workbook.Sheets["Invoices"];

            var newRow = new Dictionary<string, object>
            {
                ["InvoiceNumber"] = invoiceNumber,
                ["Vendor"]        = vendorName,
                ["Total"]         = totalAmount,
                ["Date"]          = invoiceDate.ToString("yyyy-MM-dd"),
                ["Status"]        = "Pending Review"
            };

            sheet.Append(newRow);
            workbook.Save();

            Log($"Appended invoice {invoiceNumber} to tracker. Total: {totalAmount:C}");
        }
    }
}
```

**Required packages in project.json:**
- `UiPath.Excel.Activities` — for `excel` service
- `UiPath.System.Activities` — for `system` service

---

## Example 2: Gmail → Airtable Lead Capture

**Scenario:** Read unread emails from a leads inbox, parse the sender's name/company, and add each as a record in Airtable.

```csharp
using UiPath.CodedWorkflows;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;

namespace LeadCapture
{
    public class CaptureEmailLeads : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var airtableApiKey = system.GetAsset("AirtableApiKey");
            var airtableBaseId = system.GetAsset("AirtableBaseId");

            // Step 1: Get unread emails from inbox (using mail service)
            var emails = mail.GetMailMessages(
                account: "leads@mycompany.com",
                filter: MailFilter.Unread,
                top: 20
            );

            Log($"Found {emails.Count} unread lead emails");

            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", airtableApiKey);

            foreach (var email in emails)
            {
                // Step 2: Parse lead info from email
                var senderEmail   = email.From.Address;
                var senderName    = email.From.DisplayName;
                var emailBody     = email.Body;

                // Step 3: Create Airtable record
                var payload = JsonConvert.SerializeObject(new {
                    fields = new {
                        Name    = senderName,
                        Email   = senderEmail,
                        Source  = "Email Inbound",
                        Status  = "New",
                        Subject = email.Subject,
                        Date    = email.Date.ToString("yyyy-MM-dd")
                    }
                });

                var response = httpClient.PostAsync(
                    $"https://api.airtable.com/v0/{airtableBaseId}/Leads",
                    new StringContent(payload, Encoding.UTF8, "application/json")
                ).Result;

                if (response.IsSuccessStatusCode)
                {
                    Log($"Lead added: {senderName} <{senderEmail}>");
                    mail.MarkAsRead(email);
                }
                else
                {
                    Log($"Failed to add lead {senderEmail}: {response.StatusCode}", LogLevel.Warn);
                }
            }
        }
    }
}
```

**Required packages:**
- `UiPath.Mail.Activities` — for `mail` service
- `UiPath.System.Activities` — for `system.GetAsset`
- `Newtonsoft.Json` — already available in UiPath projects

---

## Example 3: Queue-Based Batch Processor

**Scenario:** Process items from an Orchestrator queue (e.g., customer orders), call an external API per item, and update a tracking spreadsheet.

```csharp
using UiPath.CodedWorkflows;
using UiPath.System.Models;
using System.Net.Http;

namespace OrderProcessing
{
    public class ProcessOrderQueue : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var apiEndpoint = system.GetAsset("OrderApiEndpoint");
            var apiKey      = system.GetAsset("OrderApiKey");

            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Add("X-API-Key", apiKey);

            int processed = 0, failed = 0;

            // Process up to 50 items per run
            QueueItem? item;
            while ((item = system.GetQueueItem("OrderProcessingQueue")) != null && processed + failed < 50)
            {
                try
                {
                    var orderId     = item.SpecificContent["OrderId"].ToString();
                    var customerEmail = item.SpecificContent["CustomerEmail"].ToString();

                    Log($"Processing order {orderId} for {customerEmail}");

                    // Call order fulfillment API
                    var response = httpClient.PostAsync(
                        $"{apiEndpoint}/orders/{orderId}/fulfill",
                        null
                    ).Result;

                    if (response.IsSuccessStatusCode)
                    {
                        system.SetTransactionStatus(item, QueueItemStatus.Successful);
                        processed++;
                        Log($"Order {orderId} fulfilled successfully");
                    }
                    else
                    {
                        system.SetTransactionStatus(item, QueueItemStatus.Failed,
                            error: $"API returned {response.StatusCode}");
                        failed++;
                    }
                }
                catch (System.Exception ex)
                {
                    system.SetTransactionStatus(item, QueueItemStatus.Failed, error: ex.Message);
                    failed++;
                    Log($"Exception processing item: {ex.Message}", LogLevel.Error);
                }
            }

            Log($"Batch complete. Processed: {processed}, Failed: {failed}");
        }
    }
}
```

---

## Example 4: Slack Daily Summary Report

**Scenario:** Every morning, query Orchestrator for yesterday's job statistics and post a summary to a Slack channel.

```csharp
using UiPath.CodedWorkflows;
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using System;

namespace Reporting
{
    public class DailySummaryReport : CodedWorkflow
    {
        [Workflow]
        public void Execute()
        {
            var slackWebhook = system.GetAsset("SlackReportWebhookUrl");
            var yesterday    = DateTime.Today.AddDays(-1).ToString("yyyy-MM-dd");

            // Build summary (in production, query Orchestrator API for real stats)
            var successCount   = 47;
            var failureCount   = 2;
            var avgDurationMin = 3.2;

            var message = $"*UiPath Daily Report — {yesterday}*\n" +
                          $"✅ Successful jobs: {successCount}\n" +
                          $"❌ Failed jobs: {failureCount}\n" +
                          $"⏱ Avg duration: {avgDurationMin:F1} min\n" +
                          (failureCount > 0
                              ? $"⚠️ Review failures in <https://cloud.uipath.com|Orchestrator>"
                              : "🎉 All jobs completed successfully!");

            using var httpClient = new HttpClient();
            var payload  = JsonConvert.SerializeObject(new { text = message });
            var response = httpClient.PostAsync(
                slackWebhook,
                new StringContent(payload, Encoding.UTF8, "application/json")
            ).Result;

            Log($"Slack report sent. Status: {response.StatusCode}");
        }
    }
}
```

---

## Example 5: Excel to REST API Data Sync

**Scenario:** Read a product catalog Excel sheet and sync each row to an e-commerce API, skipping rows already synced.

```csharp
using UiPath.CodedWorkflows;
using System.Net.Http;
using System.Text;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace CatalogSync
{
    public class SyncProductCatalog : CodedWorkflow
    {
        [Workflow]
        public void Execute(string catalogPath)
        {
            var apiBaseUrl = system.GetAsset("EcommerceApiUrl");
            var apiKey     = system.GetAsset("EcommerceApiKey");

            using var workbook = excel.Open(catalogPath, hasHeaders: true, isReadOnly: true);
            var products = workbook.Sheets["Products"].Read();

            using var httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

            int synced = 0, skipped = 0;

            foreach (var row in products)
            {
                var sku    = row["SKU"]?.ToString();
                var synced_flag = row["Synced"]?.ToString();

                if (synced_flag == "Yes")
                {
                    skipped++;
                    continue;
                }

                var payload = JsonConvert.SerializeObject(new {
                    sku         = sku,
                    name        = row["ProductName"]?.ToString(),
                    price       = double.Parse(row["Price"]?.ToString() ?? "0"),
                    stock       = int.Parse(row["Stock"]?.ToString() ?? "0"),
                    description = row["Description"]?.ToString()
                });

                var response = httpClient.PostAsync(
                    $"{apiBaseUrl}/products",
                    new StringContent(payload, Encoding.UTF8, "application/json")
                ).Result;

                if (response.IsSuccessStatusCode)
                {
                    synced++;
                    Log($"Synced SKU: {sku}");
                }
                else
                {
                    Log($"Failed to sync SKU {sku}: {response.StatusCode}", LogLevel.Warn);
                }
            }

            Log($"Sync complete. Synced: {synced}, Skipped (already done): {skipped}");
        }
    }
}
```

**Required packages:**
- `UiPath.Excel.Activities`
- `UiPath.System.Activities`
