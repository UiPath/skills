# UiPath.Testing.Activities — Activity Reference

Activities for test case authoring, test data generation, test data queue management, and assertion-based verification. Requires UiPath Studio v2020.4+ and Orchestrator v2020.4+ for queue-based activities.

**Package ID:** `UiPath.Testing.Activities`
**Platform:** Cross-platform (Windows & Linux)

---

## XML Namespace Declarations

```xml
<!-- Main activities (most activities) -->
xmlns:uta="clr-namespace:UiPath.Testing.Activities;assembly=UiPath.Testing.Activities"

<!-- Test data generation activities -->
xmlns:utad="clr-namespace:UiPath.Testing.Activities.TestData;assembly=UiPath.Testing.Activities"
```

---

## Test Data Queues

Interact with Orchestrator Test Data Queues to supply parameterized test data to test cases.

| Activity | Class | Description |
|----------|-------|-------------|
| [Add Test Data Queue Item](activities/NewAddTestDataQueueItem.md) | `NewAddTestDataQueueItem` | Adds a single item (key-value dictionary) to a Test Data Queue. |
| [Bulk Add Test Data Queue Items](activities/BulkAddTestDataQueue.md) | `BulkAddTestDataQueue` | Adds multiple items from a DataTable to a Test Data Queue. |
| [Delete Test Data Queue Items](activities/DeleteTestDataQueueItems.md) | `DeleteTestDataQueueItems` | Deletes a list of test data queue items from Orchestrator. |
| [Get Test Data Queue Item](activities/GetTestDataQueueItem.md) | `GetTestDataQueueItem` | Retrieves and optionally consumes the next item from a queue. Returns `Dictionary<String, Object>`. |
| [Get Test Data Queue Items](activities/GetTestDataQueueItems.md) | `GetTestDataQueueItems` | Retrieves all items (or a filtered/paginated subset) from a queue. Returns `List<TestDataQueueItem>`. |

---

## Test Data

Generate synthetic test data and attach evidence to test cases.

| Activity | Class | Description |
|----------|-------|-------------|
| [Generate Address](activities/Address.md) | `Address` | Generates a random postal address as `Dictionary<String, String>`. Keys: `Country`, `City`, `State`, `StreetNumber`, `StreetName`, `PostalCode`. |
| [Generate Given Name](activities/GivenName.md) | `GivenName` | Generates a random first name. |
| [Generate Last Name](activities/LastName.md) | `LastName` | Generates a random last name. |
| [Generate Random Date](activities/RandomDate.md) | `RandomDate` | Generates a random `DateTime` within a specified range. |
| [Generate Random Number](activities/RandomNumber.md) | `RandomNumber` | Generates a random `Decimal` number with optional min, max, and decimal places. |
| [Generate Random String](activities/RandomString.md) | `RandomString` | Generates a random string of a specified length and casing (`LowerCase`, `UpperCase`, `CamelCase`, `Mixed`). |
| [Generate Random Value](activities/RandomValue.md) | `RandomValue` | Picks a random line from a `.txt` or `.csv` file and returns it as a string. |
| [Attach Document](activities/AttachDocument.md) | `AttachDocument` | Attaches a file to the current test case in Orchestrator. |

---

## Verification

Assert values, compare expressions, and compare text or PDF documents in test case workflows.

| Activity | Class | Description |
|----------|-------|-------------|
| [Verify Expression](activities/VerifyExpression.md) | `VerifyExpression` | Asserts a Boolean expression is `true`. Marks the test case as failed if not. |
| [Verify Expression with Operator](activities/VerifyExpressionWithOperator.md) | `VerifyExpressionWithOperator` | Compares two values using an operator (`=`, `<>`, `>`, `>=`, `<`, `<=`, `Contains`, `Regex-Match`). |
| [Verify Range](activities/VerifyRange.md) | `VerifyRange` | Asserts a value is within (or outside) a lower/upper bound range. |
| [Create Comparison Rule](activities/CreateComparisonRule.md) | `CreateComparisonRule` | Creates a `ComparisonRule` (regex or wildcard) for excluding dynamic sections in text/PDF comparisons. |
| [Compare Text](activities/CompareText.md) | `CompareText` | Compares two text strings at line/word/character granularity. Supports rules to exclude dynamic content and optional Autopilot semantic interpretation. |
| [Compare PDF Documents](activities/ComparePdfDocuments.md) | `ComparePdfDocuments` | Compares two PDF files for text and image equivalence. Supports comparison rules and Autopilot semantic interpretation. |

---

## Key Types

| Type | Description |
|------|-------------|
| `TestDataQueueItem` | Represents a single item in a Test Data Queue. Contains item ID, status, and field data. |
| `ComparisonRule` | A rule (regex or wildcard) that excludes matched text from comparisons. Created by **Create Comparison Rule**. |
| `Difference` | A single diff entry with `Operation` (`Equal`, `Inserted`, `Deleted`) and `Text`. |
| `SemanticDifferences` | AI-interpreted semantic diff result from Autopilot. |
| `Comparison` | Enum of comparison operators: `Equality`, `Inequality`, `GreaterThan`, `GreaterThanOrEqual`, `LessThan`, `LessThanOrEqual`, `Contains`, `RegexMatch`. |
| `ComparisonType` | Enum of text comparison granularities: `Line`, `Word`, `Character`. |
| `VerificationType` | Enum: `IsWithin`, `IsNotWithin` (for Verify Range). |
| `TestDataQueueItemStatus` | Enum: `All`, `OnlyConsumed`, `OnlyNotConsumed` (for Get Test Data Queue Items filter). |
| `Case` | Enum of string casing: `LowerCase`, `UpperCase`, `CamelCase`, `Mixed` (for Generate Random String). |
| `ComparisonRuleType` | Enum: `RegexRule`, `WildcardRule` (for Create Comparison Rule). |
