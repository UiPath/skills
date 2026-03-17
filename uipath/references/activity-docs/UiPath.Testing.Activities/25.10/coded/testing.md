# Testing Activities API Reference

Reference for the `testing` service from `UiPath.Testing.Activities` package.

**Required package:** `"UiPath.Testing.Activities": "[25.10.0]"`

**Auto-imported namespaces:** `System`, `System.Collections.Generic`, `UiPath.Testing.Activities.TestDataQueues.Enums`, `UiPath.Testing.Activities.TestData`, `UiPath.Testing.Enums`, `UiPath.Testing`, `UiPath.Testing.Activities.Models`, `UiPath.Testing.Activities.Api.Models`

**Service accessor:** `testing` (type `ITestingService`)

---

## API Categories

The Testing API has three main areas:

1. **Verification / Assertions** — Methods for verifying expressions, equality, comparisons, ranges, containment, and regex matching. See [testing-verification.md](testing-verification.md).

2. **Data Generation & Test Data Queues** — Random data generation (names, numbers, dates, strings, addresses) and Orchestrator test data queue operations (add, get, delete items). See [testing-data.md](testing-data.md).

3. **Document & Text Comparison** — PDF document and text comparison with rules, semantic analysis, and diff output. See [testing-comparison.md](testing-comparison.md).

For full coded workflow examples, see [examples.md](examples.md).

---

## Key Type Reference

### Enums

| Enum | Namespace | Values |
|---|---|---|
| `Comparison` | `UiPath.Testing` | `Equality` (=), `Inequality` (<>), `GreaterThan` (>), `GreaterThanOrEqual` (>=), `LessThan` (<), `LessThanOrEqual` (<=), `Contains`, `RegexMatch` |
| `VerificationType` | `UiPath.Testing.Activities` | `IsWithin` (0), `IsNotWithin` (1) |
| `ComparisonType` | `UiPath.Testing.Activities.Models` | `Line`, `Word`, `Character` |
| `Case` | `UiPath.Testing.Enums` | `LowerCase`, `UpperCase`, `CamelCase`, `Mixed` |
| `TestDataQueueItemStatus` | `UiPath.Testing.Activities.TestDataQueues.Enums` | `All` (0), `OnlyConsumed` (1), `OnlyNotConsumed` (2) |
| `Operation` | `UiPath.Testing.Activities.Models` | `Inserted`, `Deleted`, `Equal` |
| `DocumentOutputDiffType` | `UiPath.Testing.Activities.Models` | `None`, `Pdf`, `Unidiff`, `Html` |

### Classes

| Class | Namespace | Description |
|---|---|---|
| `TestDataQueueItem` | `UiPath.Testing.Core` | Represents a test data queue item with `Id` (`long?`), `Content` (`Dictionary<string, object>`), `IsConsumed` (`bool?`) |
| `ComparisonResult` | `UiPath.Testing.Activities.Models` | Result of a comparison with `AreEquivalent` (`bool`), `Differences` (`List<Difference>`), `SemanticDifferences` (`SemanticDifferences`) |
| `Difference` | `UiPath.Testing.Activities.Models` | A single difference with `Operation` (`Operation`) and `Text` (`string`) |
| `SemanticDifferences` | `UiPath.Testing.Activities.Models` | Semantic analysis result with `AreSemanticallyEquivalent` (`bool`), `Explanation` (`string`), `Differences` (`List<SemanticDifference>`) |
| `SemanticDifference` | `UiPath.Testing.Activities.Models` | A single semantic difference with `Explanation` (`string`) |
| `RegexRule` | `UiPath.Testing.Activities.Models` | Comparison rule using regex pattern. Constructor: `RegexRule(string name, string pattern, bool usePlaceholder = true)` |
| `WildcardRule` | `UiPath.Testing.Activities.Models` | Comparison rule using wildcard pattern (`*` and `?`). Constructor: `WildcardRule(string name, string pattern, bool usePlaceholder = true)` |
