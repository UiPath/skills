using System;
using System.Collections.Generic;
using System.Data;
using System.IO;
using UiPath.CodedWorkflows;
using UiPath.Core;
using UiPath.Core.Activities.Storage;
using UiPath.Orchestrator.Client.Models;

namespace CodedProc
{
    public class AddToQueue : CodedWorkflow
    {
        [Workflow]
        public void Execute(string queueName, DataTable excelData)
        {
            var outputFolder = Path.Combine(Directory.GetCurrentDirectory(), "GeneratedInvoices");
            Directory.CreateDirectory(outputFolder);

            Log($"Processing {excelData.Rows.Count} invoices. PDFs will be saved to: {outputFolder}");

            for (int i = 0; i < excelData.Rows.Count; i++)
            {
                var row = excelData.Rows[i];
                var invoiceId = row["Invoice ID"].ToString();

                // Step 1: Generate PDF invoice
                var pdfPath = InvoicePdfGenerator.Generate(row, outputFolder);
                Log($"Generated PDF for invoice {invoiceId}: {pdfPath}");

                // Step 2: Build queue item data with all columns + PDF path
                var data = new Dictionary<string, object>();
                foreach (DataColumn col in excelData.Columns)
                {
                    data[col.ColumnName] = row[col] ?? string.Empty;
                }
                data["InvoicePdfPath"] = pdfPath;

                // Step 3: Add to queue
                system.AddQueueItem(
                    queueName,
                    null,
                    default(DateTime),
                    data,
                    default(DateTime),
                    QueueItemPriority.Normal,
                    $"INV-{invoiceId}",
                    30000
                );

                Log($"Added invoice {invoiceId} to queue with PDF attached.");
            }

            Log($"Finished processing all {excelData.Rows.Count} invoices.");
        }
    }
}
