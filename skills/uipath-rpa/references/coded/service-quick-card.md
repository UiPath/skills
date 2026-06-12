# Coded Workflow Service Quick Card

Most-used service calls for coded workflows (`.cs`). Signature not here or need overloads/enums → read the package's coded-api.md (resolution order in SKILL.md § Coded Workflows Quick Reference). Only add `using` statements for packages present in `project.json` — see [coding-guidelines.md](coding-guidelines.md).

## `system` — UiPath.System.Activities

Package: `"UiPath.System.Activities": "*"`. Usings: `using UiPath.Core;` (+ `using UiPath.Orchestrator.Client.Models;` for queue/asset models, `using UiPath.Core.Activities.Storage;` for storage APIs). Direct method calls — no handles, no `using` blocks. Most methods have overloads adding `folderPath` / `timeoutMS`.

| Method | Signature | Returns | Example |
|--------|-----------|---------|---------|
| AddQueueItem | `void AddQueueItem(string queueType, string folderPath, Dictionary<string, object> itemInformationCollection)` | `void` (item status `New`) | `system.AddQueueItem("Invoices", "Shared", data);` |
| AddTransactionItem | `QueueItem AddTransactionItem(string queueType, string folderPath, string reference, Dictionary<string, object> transactionInformation, int timeoutMS)` | `QueueItem` — created transaction item | `var tx = system.AddTransactionItem("Invoices", null, "INV-1", data, 30000);` |
| BulkAddQueueItems | `DataTable BulkAddQueueItems(DataTable queueItemsDataTable, string queueName)` | `DataTable` — result of bulk operation (e.g., failed items) | `var failed = system.BulkAddQueueItems(dt, "Invoices");` |
| GetTransactionItem | `QueueItem GetTransactionItem(string queueType)` | `QueueItem` in `In Progress`; `null` if queue empty | `var item = system.GetTransactionItem("Invoices");` |
| SetTransactionStatus | `void SetTransactionStatus(QueueItem transactionItem, ProcessingStatus status)` | `void` | `system.SetTransactionStatus(item, ProcessingStatus.Successful);` |
| GetAsset | `object GetAsset(string assetName)` | `object` — cast to expected type | `var url = (string)system.GetAsset("ApiUrl");` |
| SetAsset | `void SetAsset(object value, string assetName)` | `void` | `system.SetAsset("https://api.example.com", "ApiUrl");` |
| GetCredential | `(string userName, SecureString password) GetCredential(string assetName, string folderPath = null, int timeoutMS = 1000, CacheStrategyEnum cacheStrategy = CacheStrategyEnum.None)` | tuple `(string, SecureString)` | `var (user, pwd) = system.GetCredential("AppLogin");` |

> **Platform types:** queue methods take/return the platform `QueueItem` (auto-imported `UiPath.Orchestrator.Client.Models`; `QueueItemDto` and related are the canonical shapes). Never define project-local queue-item records, credential helpers, or a local `BusinessRuleException` — throw `UiPath.Core.BusinessRuleException` for non-retryable business failures. See [coding-guidelines.md § Platform types](coding-guidelines.md#platform-types--do-not-reinvent).

> **Queue semantics:** the `Dictionary<string, object>` parameter is the data stored on the item. `BulkAddQueueItems` adds one item per DataTable row; its full overload's `commitType` selects all-at-once vs per-item commit, and the returned DataTable reflects the result (e.g., failed items) — check it before declaring success. Field-mapping details and remaining overloads: System package `coded-api.md` § Queue & Transaction Management.

## `excel` — UiPath.Excel.Activities

Package: `"UiPath.Excel.Activities": "*"`. Usings: `using UiPath.Excel; using UiPath.Excel.Activities; using UiPath.Excel.Activities.API; using UiPath.Excel.Activities.API.Models;`. Two surfaces: **Portable** `UseWorkBook` → `IWorkHandle` (cross-platform) and **Windows/Interop** `UseExcelFile` → `IWorkbookQuickHandle` (Windows only; sheet/table/chart indexers, `ForEachRow`, macros). Both handles are `IDisposable` — wrap in `using`.

Portable (`IWorkHandle` extension methods unless noted):

| Method | Signature | Returns | Example |
|--------|-----------|---------|---------|
| UseWorkBook | `IWorkHandle UseWorkBook(string path, bool createNew = true)` | `IWorkHandle` (disposable) | `using var wb = excel.UseWorkBook("data.xlsx");` |
| ReadRange | `ReadRange(string sheetName, string range, bool addHeaders, bool preserveFormat)` | `DataTable` — empty range reads whole sheet | `var dt = wb.ReadRange("Sheet1", "", true, false);` |
| WriteRange | `WriteRange(string sheetName, string startingCell, DataTable table, bool addHeaders)` | `void` — creates sheet if missing, saves immediately | `wb.WriteRange("Out", "A1", dt, true);` |
| AppendRange | `AppendRange(string sheetName, DataTable table)` | `void` — appends after existing data | `wb.AppendRange("Out", dt);` |
| ReadCell | `ReadCell(string sheetName, string cell, bool preserveFormat)` | `object` | `var v = wb.ReadCell("Sheet1", "B2", false);` |
| WriteCell | `WriteCell(string sheetName, string cell, string text)` | `void` | `wb.WriteCell("Sheet1", "C1", "done");` |
| UseExcelFile | `IWorkbookQuickHandle UseExcelFile(string path)` | `IWorkbookQuickHandle` — Windows/Interop surface | `using var xl = excel.UseExcelFile("report.xlsx");` |

## `testing` — UiPath.Testing.Activities

Package: `"UiPath.Testing.Activities": "[25.10.2]"`. Usings: `using UiPath.Testing;` (+ `using UiPath.Testing.Enums;` for enums, `using UiPath.Testing.Activities.TestData;` for test data queues). All `Verify*` methods return `bool` — `true` passed, `false` failed.

| Method | Signature | Returns | Example |
|--------|-----------|---------|---------|
| VerifyExpression | `bool VerifyExpression(bool expression, string outputMessageFormat)` | `bool` | `testing.VerifyExpression(count > 0, "Count positive");` |
| VerifyAreEqual | `bool VerifyAreEqual(object firstExpression, object secondExpression, string outputMessageFormat = null)` | `bool` | `testing.VerifyAreEqual(expected, actual, "Counts match");` |
| VerifyExpressionWithOperator | `bool VerifyExpressionWithOperator(object firstExpression, Comparison operatorValue, object secondExpression, string outputMessageFormat = null)` | `bool` — `Comparison`: `Equality`, `Inequality`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `Contains`, `RegexMatch` | `testing.VerifyExpressionWithOperator(price, Comparison.GreaterThan, 0, "Price > 0");` |
| VerifyContains | `bool VerifyContains(object firstExpression, object secondExpression, string outputMessageFormat = null)` | `bool` | `testing.VerifyContains(msg, "success");` |
| AttachDocument | `void AttachDocument(string filePath)` | `void` — attaches file to current test case in Orchestrator | `testing.AttachDocument("C:\\Output\\report.pdf");` |
| AddTestDataQueueItem | `void AddTestDataQueueItem(string queueName, Dictionary<string, object> itemInformation)` | `void` | `testing.AddTestDataQueueItem("InvoiceTestData", data);` |

## `uiAutomation` — UiPath.UIAutomation.Activities

No signatures here. UI automation uses the `uiAutomation` service with Object Repository `Descriptors` — read [ui-automation-guide.md](../ui-automation-guide.md) IN FULL and resolve descriptors via its Finding Descriptors hierarchy before writing any UI code.
