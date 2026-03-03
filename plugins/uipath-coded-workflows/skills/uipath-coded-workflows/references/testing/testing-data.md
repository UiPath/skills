# Testing — Data Generation & Test Data Queues

Random data generation and Orchestrator test data queue operations on the `testing` service (`ITestingService`). For general info see [testing.md](testing.md).

---

## Random Data Generation

### GivenName

Returns a random first name.

```csharp
string GivenName();
```

```csharp
string firstName = testing.GivenName(); // e.g. "John"
```

### LastName

Returns a random last name.

```csharp
string LastName();
```

```csharp
string lastName = testing.LastName(); // e.g. "Smith"
```

### RandomNumber

Returns a random decimal number.

```csharp
// No parameters — uses long.MinValue to long.MaxValue, 0 decimals
decimal RandomNumber();

// With range
decimal RandomNumber(long min, long max);

// With range and decimal places
decimal RandomNumber(long min, long max, int decimals);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `min` | `long` | `long.MinValue` | Minimum value (inclusive) |
| `max` | `long` | `long.MaxValue` | Maximum value (inclusive) |
| `decimals` | `int` | `0` | Number of decimal places |

```csharp
decimal amount = testing.RandomNumber(100, 5000, 2); // e.g. 2547.83
decimal wholeNumber = testing.RandomNumber(1, 100);   // e.g. 42
```

### RandomDate

Returns a random date within a range.

```csharp
DateTime RandomDate(DateTime minDate, DateTime maxDate);
```

| Parameter | Type | Description |
|---|---|---|
| `minDate` | `DateTime` | Inclusive lower bound |
| `maxDate` | `DateTime` | Exclusive upper bound |

```csharp
DateTime date = testing.RandomDate(new DateTime(2024, 1, 1), new DateTime(2025, 1, 1));
```

### RandomString

Returns a random string with a specified case and length.

```csharp
string RandomString(Case caseValue, int length);
```

| Parameter | Type | Description |
|---|---|---|
| `caseValue` | `Case` | Case style of the generated string |
| `length` | `int` | Length of the string |

**`Case` enum:**

| Value | Example |
|---|---|
| `Case.LowerCase` | `"abcdef"` |
| `Case.UpperCase` | `"ABCDEF"` |
| `Case.CamelCase` | `"Abcdef"` |
| `Case.Mixed` | `"aBcDeF"` |

```csharp
string code = testing.RandomString(Case.UpperCase, 8); // e.g. "XKQPLMRT"
```

### RandomValue

Picks a random line from a `.txt` or `.csv` file (1-column list).

```csharp
string RandomValue(string filePath);
```

| Parameter | Type | Description |
|---|---|---|
| `filePath` | `string` | Path to the source file |

```csharp
string city = testing.RandomValue(@"C:\TestData\cities.txt");
```

### Address

Returns a random address as a dictionary.

```csharp
Dictionary<string, string> Address(string country, string city);
```

| Parameter | Type | Description |
|---|---|---|
| `country` | `string` | Country for the address |
| `city` | `string` | City for the address |

```csharp
Dictionary<string, string> addr = testing.Address("US", "New York");
// Keys may include street, zip, state, etc.
```

---

## Attach Document

Attaches a document to the current test case in Orchestrator.

```csharp
// Without tags
void AttachDocument(string filePath);

// With tags
void AttachDocument(string filePath, IEnumerable<string> tags);
```

| Parameter | Type | Description |
|---|---|---|
| `filePath` | `string` | File path of the document to attach |
| `tags` | `IEnumerable<string>` | Tags to add to the test case |

```csharp
testing.AttachDocument(@"C:\Output\report.pdf");
testing.AttachDocument(@"C:\Output\screenshot.png", new[] { "evidence", "login-test" });
```

---

## Test Data Queue Operations

Operations for managing test data queues in Orchestrator.

### AddTestDataQueueItem

Adds a single item to a test data queue.

```csharp
// Minimal
void AddTestDataQueueItem(string queueName, Dictionary<string, object> itemInformation);

// With folder path
void AddTestDataQueueItem(string queueName, Dictionary<string, object> itemInformation, string folderPath);

// With folder path and timeout
void AddTestDataQueueItem(string queueName, Dictionary<string, object> itemInformation, string folderPath, int timeoutMs);
```

| Parameter | Type | Description |
|---|---|---|
| `queueName` | `string` | Queue name where to add data |
| `itemInformation` | `Dictionary<string, object>` | The item data as key-value pairs |
| `folderPath` | `string` | Orchestrator folder path |
| `timeoutMs` | `int` | Timeout in milliseconds |

```csharp
testing.AddTestDataQueueItem("InvoiceTestData", new Dictionary<string, object>
{
    { "InvoiceNumber", "INV-001" },
    { "Amount", 1500.00 },
    { "Customer", "Acme Corp" }
});
```

### BulkAddTestDataQueueItems

Adds multiple items to a test data queue from a DataTable.

```csharp
// Minimal
void BulkAddTestDataQueueItems(string queueName, DataTable queueItemsDataTable);

// With folder path
void BulkAddTestDataQueueItems(string queueName, DataTable queueItemsDataTable, string folderPath);

// With folder path and timeout
void BulkAddTestDataQueueItems(string queueName, DataTable queueItemsDataTable, string folderPath, int timeoutMs);
```

| Parameter | Type | Description |
|---|---|---|
| `queueName` | `string` | Queue name where items will be added |
| `queueItemsDataTable` | `DataTable` | DataTable with entries to add |
| `folderPath` | `string` | Orchestrator folder path |
| `timeoutMs` | `int` | Timeout in milliseconds |

```csharp
DataTable testData = new DataTable();
testData.Columns.Add("Name", typeof(string));
testData.Columns.Add("Amount", typeof(double));
testData.Rows.Add("Invoice-1", 100.0);
testData.Rows.Add("Invoice-2", 200.0);

testing.BulkAddTestDataQueueItems("InvoiceTestData", testData);
```

### GetTestDataQueueItem

Gets the next test data item from a queue.

```csharp
// Minimal
Dictionary<string, object> GetTestDataQueueItem(string queueName);

// With folder path
Dictionary<string, object> GetTestDataQueueItem(string queueName, string folderPath);

// Full parameters
Dictionary<string, object> GetTestDataQueueItem(string queueName, string folderPath, bool markConsumed, int timeoutMs);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `queueName` | `string` | — | Queue name |
| `folderPath` | `string` | `null` | Orchestrator folder path |
| `markConsumed` | `bool` | (not set) | Mark the item as consumed |
| `timeoutMs` | `int` | (not set) | Timeout in milliseconds |

```csharp
Dictionary<string, object> item = testing.GetTestDataQueueItem("InvoiceTestData");
string invoiceNumber = item["InvoiceNumber"].ToString();
```

### GetTestDataQueueItems

Gets all items from a specified queue.

```csharp
// Minimal
List<TestDataQueueItem> GetTestDataQueueItems(string queueName);

// With folder path
List<TestDataQueueItem> GetTestDataQueueItems(string queueName, string folderPath);

// Full parameters
List<TestDataQueueItem> GetTestDataQueueItems(
    string queueName,
    string folderPath,
    string idFilter,
    TestDataQueueItemStatus testDataQueueItemStatus,
    int? skip,
    int? top,
    int timeoutMs
);
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `queueName` | `string` | — | Queue name |
| `folderPath` | `string` | `null` | Orchestrator folder path |
| `idFilter` | `string` | `null` | Filter by ID |
| `testDataQueueItemStatus` | `TestDataQueueItemStatus` | (not set) | Filter by status: `All`, `OnlyConsumed`, `OnlyNotConsumed` |
| `skip` | `int?` | `null` | Number of items to skip (for pagination) |
| `top` | `int?` | `null` | Maximum number of items to return |
| `timeoutMs` | `int` | (not set) | Timeout in milliseconds |

**`TestDataQueueItem` properties:**

| Property | Type | Description |
|---|---|---|
| `Id` | `long?` | The item ID |
| `Content` | `Dictionary<string, object>` | The item data |
| `IsConsumed` | `bool?` | Whether the item has been consumed |

```csharp
// Get all unconsumed items
List<TestDataQueueItem> items = testing.GetTestDataQueueItems(
    "InvoiceTestData", null, null, TestDataQueueItemStatus.OnlyNotConsumed, null, null, 30000
);

foreach (var item in items)
{
    Log($"Item {item.Id}: {item.Content["InvoiceNumber"]}");
}
```

### DeleteTestDataQueueItems

Deletes specified test data queue items.

```csharp
// Minimal
void DeleteTestDataQueueItems(List<TestDataQueueItem> testDataQueueItems);

// With folder path
void DeleteTestDataQueueItems(List<TestDataQueueItem> testDataQueueItems, string folderPath);

// With folder path and timeout
void DeleteTestDataQueueItems(List<TestDataQueueItem> testDataQueueItems, string folderPath, int timeoutMs);
```

| Parameter | Type | Description |
|---|---|---|
| `testDataQueueItems` | `List<TestDataQueueItem>` | Items to delete |
| `folderPath` | `string` | Orchestrator folder path |
| `timeoutMs` | `int` | Timeout in milliseconds |

```csharp
List<TestDataQueueItem> consumed = testing.GetTestDataQueueItems(
    "InvoiceTestData", null, null, TestDataQueueItemStatus.OnlyConsumed, null, null, 30000
);
testing.DeleteTestDataQueueItems(consumed);
```
