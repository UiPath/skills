# Error Handling Guidance — Coded Workflows

Patterns for building robust, self-recovering coded workflows that handle failures gracefully.

---

## Core Principle

**Expect failure. Design for recovery.**

Every external call (API, file system, database, UI) can fail. A well-designed workflow anticipates this, retries transient errors, captures permanent errors for human review, and always leaves the system in a known state.

---

## Exception Hierarchy

Understand which exceptions to catch and how to respond:

| Exception Type | Cause | Action |
|---|---|---|
| `System.Net.Http.HttpRequestException` | Network failure, DNS error | Retry with backoff |
| `System.Net.WebException` | HTTP timeout, connection refused | Retry with backoff |
| `System.TimeoutException` | Operation exceeded time limit | Retry with shorter scope or fail |
| `System.IO.FileNotFoundException` | Missing input file | Fail immediately, notify |
| `System.IO.IOException` | Disk full, file locked | Retry briefly, then fail |
| `System.UnauthorizedException` (custom) | Auth token expired | Re-authenticate, retry once |
| `Newtonsoft.Json.JsonException` | Malformed API response | Log response body, fail |
| `System.Exception` (base) | Catch-all for unexpected errors | Log full details, fail |

---

## Retry Pattern

Use exponential backoff for transient failures (network, rate limits, timeouts).

### Basic retry with exponential backoff

```csharp
using System;
using System.Threading;

namespace MyProject
{
    public static class RetryHelper
    {
        /// <summary>
        /// Retries an action up to maxAttempts times with exponential backoff.
        /// Throws the last exception if all attempts fail.
        /// </summary>
        public static T Execute<T>(
            Func<T> action,
            int maxAttempts = 3,
            int initialDelayMs = 1000,
            double backoffMultiplier = 2.0)
        {
            Exception? lastException = null;

            for (int attempt = 1; attempt <= maxAttempts; attempt++)
            {
                try
                {
                    return action();
                }
                catch (Exception ex) when (IsTransient(ex))
                {
                    lastException = ex;
                    if (attempt < maxAttempts)
                    {
                        var delayMs = (int)(initialDelayMs * Math.Pow(backoffMultiplier, attempt - 1));
                        Thread.Sleep(delayMs);
                    }
                }
            }

            throw lastException!;
        }

        private static bool IsTransient(Exception ex) =>
            ex is System.Net.Http.HttpRequestException ||
            ex is System.Net.WebException ||
            ex is TimeoutException ||
            ex is System.IO.IOException;
    }
}
```

### Using the retry helper in a workflow

```csharp
[Workflow]
public void Execute(string apiUrl)
{
    var result = RetryHelper.Execute(
        action: () => CallExternalApi(apiUrl),
        maxAttempts: 3,
        initialDelayMs: 2000
    );
    Log($"API call succeeded: {result}");
}

private string CallExternalApi(string url)
{
    using var client = new System.Net.Http.HttpClient { Timeout = TimeSpan.FromSeconds(30) };
    var response = client.GetAsync(url).Result;
    response.EnsureSuccessStatusCode();
    return response.Content.ReadAsStringAsync().Result;
}
```

### Built-in Delay for simple retries (no helper class)

```csharp
[Workflow]
public void Execute()
{
    const int MaxRetries = 3;
    Exception? lastError = null;

    for (int attempt = 1; attempt <= MaxRetries; attempt++)
    {
        try
        {
            ProcessDocument();
            return; // success — exit retry loop
        }
        catch (System.Net.Http.HttpRequestException ex)
        {
            lastError = ex;
            Log($"Attempt {attempt}/{MaxRetries} failed: {ex.Message}", LogLevel.Warn);
            if (attempt < MaxRetries)
                Delay(TimeSpan.FromSeconds(Math.Pow(2, attempt))); // 2s, 4s, 8s
        }
    }

    throw new Exception($"All {MaxRetries} attempts failed. Last error: {lastError?.Message}", lastError);
}
```

---

## Exception Handling Templates

### Template 1 — Try/Catch with queue failure handling

Use this when processing queue items that must be individually retried or marked failed:

```csharp
[Workflow]
public void Execute()
{
    var item = system.GetQueueItem("ProcessingQueue");
    if (item == null) return;

    try
    {
        // Main processing logic
        var result = ProcessQueueItem(item);
        system.SetTransactionStatus(item, UiPath.System.Models.QueueItemStatus.Successful,
            analytics: new Dictionary<string, object> { ["ProcessedAt"] = DateTime.UtcNow });

        Log($"Item {item.Id} processed successfully");
    }
    catch (System.Net.Http.HttpRequestException ex)
    {
        // Transient — retry up to queue's maxRetries setting
        Log($"Transient error on item {item.Id}: {ex.Message}", LogLevel.Warn);
        system.SetTransactionStatus(item, UiPath.System.Models.QueueItemStatus.Failed,
            error: ex.Message,
            errorType: UiPath.System.Models.QueueItemErrorType.ApplicationException);
    }
    catch (Exception ex)
    {
        // Business rule violation — don't retry
        Log($"Business error on item {item.Id}: {ex.Message}", LogLevel.Error);
        system.SetTransactionStatus(item, UiPath.System.Models.QueueItemStatus.Failed,
            error: ex.Message,
            errorType: UiPath.System.Models.QueueItemErrorType.BusinessException);
    }
}
```

### Template 2 — Global exception handler with Slack alert

```csharp
[Workflow]
public void Execute()
{
    try
    {
        RunMainLogic();
    }
    catch (Exception ex)
    {
        Log($"Unhandled exception: {ex.Message}\n{ex.StackTrace}", LogLevel.Error);
        SendSlackAlert(ex);
        throw; // re-throw so Orchestrator marks the job as faulted
    }
}

private void SendSlackAlert(Exception ex)
{
    try
    {
        var webhookUrl = system.GetAsset("SlackErrorWebhookUrl");
        var message = $"❌ *Automation Failed*\n" +
                      $"Job: {System.Reflection.Assembly.GetExecutingAssembly().GetName().Name}\n" +
                      $"Error: {ex.Message}\n" +
                      $"Time: {DateTime.UtcNow:yyyy-MM-dd HH:mm:ss} UTC";

        using var client = new System.Net.Http.HttpClient();
        var payload = Newtonsoft.Json.JsonConvert.SerializeObject(new { text = message });
        client.PostAsync(webhookUrl,
            new System.Net.Http.StringContent(payload, System.Text.Encoding.UTF8, "application/json")).Wait();
    }
    catch
    {
        // Never let alert failure mask the original exception
        Log("Failed to send Slack alert", LogLevel.Warn);
    }
}
```

### Template 3 — Finally block for guaranteed cleanup

```csharp
[Workflow]
public void Execute(string filePath)
{
    System.IO.FileStream? fileStream = null;

    try
    {
        fileStream = System.IO.File.OpenRead(filePath);
        ProcessFile(fileStream);
    }
    catch (System.IO.FileNotFoundException ex)
    {
        Log($"Input file not found: {filePath}. Error: {ex.Message}", LogLevel.Error);
        throw; // propagate — caller must handle missing file
    }
    catch (Exception ex)
    {
        Log($"Error processing {filePath}: {ex.Message}", LogLevel.Error);
        throw;
    }
    finally
    {
        // Always runs — even if exception is thrown
        fileStream?.Dispose();
        Log($"File handle released for: {filePath}");
    }
}
```

---

## Recovery Patterns

### Pattern 1 — Checkpoint and Resume

For long-running workflows processing hundreds of items, save progress checkpoints so you can resume after failure without reprocessing completed items.

```csharp
using System.IO;
using Newtonsoft.Json;

public class CheckpointManager
{
    private readonly string _checkpointPath;

    public CheckpointManager(string workflowName)
    {
        _checkpointPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "UiPath", "Checkpoints", $"{workflowName}.json");
        Directory.CreateDirectory(Path.GetDirectoryName(_checkpointPath)!);
    }

    public int GetLastProcessedIndex() =>
        File.Exists(_checkpointPath)
            ? JsonConvert.DeserializeObject<dynamic>(File.ReadAllText(_checkpointPath))!.lastIndex
            : 0;

    public void Save(int lastIndex) =>
        File.WriteAllText(_checkpointPath,
            JsonConvert.SerializeObject(new { lastIndex, savedAt = DateTime.UtcNow }));

    public void Clear() =>
        File.Delete(_checkpointPath);
}
```

Usage in a workflow:

```csharp
[Workflow]
public void Execute()
{
    var checkpoint = new CheckpointManager("InvoiceProcessor");
    var startIndex = checkpoint.GetLastProcessedIndex();

    var invoices = GetAllInvoices();
    Log($"Resuming from index {startIndex}/{invoices.Count}");

    for (int i = startIndex; i < invoices.Count; i++)
    {
        ProcessInvoice(invoices[i]);
        checkpoint.Save(i + 1); // save after each successful item

        if (i % 10 == 0)
            Log($"Progress: {i}/{invoices.Count}");
    }

    checkpoint.Clear(); // done — remove checkpoint
    Log("All invoices processed successfully");
}
```

### Pattern 2 — Dead-letter queue for unprocessable items

```csharp
private void ProcessWithDeadLetter(QueueItem item)
{
    try
    {
        ProcessItem(item);
        system.SetTransactionStatus(item, QueueItemStatus.Successful);
    }
    catch (Exception ex)
    {
        Log($"Moving item {item.Id} to dead-letter queue: {ex.Message}", LogLevel.Warn);

        // Add to a separate "failed" queue with error details for human review
        system.AddQueueItem("DeadLetterQueue", new Dictionary<string, object>
        {
            ["OriginalItemId"] = item.Id,
            ["OriginalData"]   = Newtonsoft.Json.JsonConvert.SerializeObject(item.SpecificContent),
            ["ErrorMessage"]   = ex.Message,
            ["FailedAt"]       = DateTime.UtcNow.ToString("o"),
            ["AttemptCount"]   = item.RetryNumber
        });

        system.SetTransactionStatus(item, QueueItemStatus.Failed,
            error: ex.Message,
            errorType: QueueItemErrorType.BusinessException); // prevent Orchestrator auto-retry
    }
}
```

### Pattern 3 — Circuit breaker for external APIs

Stop hammering a failing API and give it time to recover:

```csharp
public class CircuitBreaker
{
    private int _failureCount = 0;
    private DateTime _lastFailureTime = DateTime.MinValue;
    private readonly int _threshold;
    private readonly TimeSpan _openDuration;

    public CircuitBreaker(int failureThreshold = 5, int openForSeconds = 60)
    {
        _threshold    = failureThreshold;
        _openDuration = TimeSpan.FromSeconds(openForSeconds);
    }

    public bool IsOpen =>
        _failureCount >= _threshold &&
        DateTime.UtcNow - _lastFailureTime < _openDuration;

    public void RecordSuccess() => _failureCount = 0;

    public void RecordFailure()
    {
        _failureCount++;
        _lastFailureTime = DateTime.UtcNow;
    }
}
```

Usage:

```csharp
private static readonly CircuitBreaker ApiBreaker = new(failureThreshold: 3, openForSeconds: 30);

private string CallApi(string url)
{
    if (ApiBreaker.IsOpen)
        throw new Exception("Circuit breaker is open — API is unhealthy. Skipping call.");

    try
    {
        using var client = new System.Net.Http.HttpClient();
        var result = client.GetStringAsync(url).Result;
        ApiBreaker.RecordSuccess();
        return result;
    }
    catch (Exception ex)
    {
        ApiBreaker.RecordFailure();
        throw;
    }
}
```

---

## Logging Best Practices

```csharp
// ✅ Log at the right level
Log("Processing started",       LogLevel.Info);   // normal milestones
Log("Retrying after timeout",   LogLevel.Warn);   // recoverable issues
Log($"Fatal: {ex.Message}",     LogLevel.Error);  // unrecoverable failures

// ✅ Include context in log messages
Log($"Processing invoice {invoiceId} for vendor {vendorName} — amount {amount:C}");

// ✅ Log duration for performance monitoring
var sw = System.Diagnostics.Stopwatch.StartNew();
ProcessBatch();
Log($"Batch processed in {sw.ElapsedMilliseconds}ms");

// ❌ Never log sensitive values
Log($"API key: {apiKey}");       // WRONG — exposes secret
Log($"Password: {password}");    // WRONG — exposes credential
```

---

## Quick Reference

| Scenario | Pattern |
|---|---|
| API call that might fail | Retry with exponential backoff (3 attempts) |
| Processing 100+ queue items | Queue item exception handling + ApplicationException/BusinessException distinction |
| Long-running batch job | Checkpoint and resume |
| API is flapping / unreliable | Circuit breaker |
| Must clean up resources | `try/finally` with `Dispose()` |
| Alert on any failure | Global exception handler + Slack/email alert |
| Items that can't be processed | Dead-letter queue for human review |
