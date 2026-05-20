# UiPath Testing Activities - Legacy Reference

## Overview
Test assertions, data generation, document comparison, and test data queue management. Package: `UiPath.Testing.Activities`.

---

## Assertion Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `VerifyExpression` | Assert boolean is true | Expression (bool), ContinueOnFailure (default true) |
| `VerifyExpressionWithOperator` | Compare two values | FirstExpression, SecondExpression, Operator |
| `VerifyRange` | Value within/outside range | Expression, LowerLimit, UpperLimit, VerificationType (IsWithin/IsNotWithin) |
| `VerifyControlAttribute` | Verify activity output | ActivityToTest, OutputArgument, Expression, Operator |

### Comparison Operators
Equality (=), Inequality (<>), GreaterThan (>), GreaterThanOrEqual (>=), LessThan (<), LessThanOrEqual (<=), Contains, RegexMatch

---

## Document Comparison (NET5+)

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `ComparePdfDocuments` | Diff two PDFs | BaselinePath, TargetPath, ComparisonType (Line/Word/Character), Rules, IncludeImages |
| `CompareText` | Diff two strings | BaselineText, TargetText, ComparisonType, OutputFilePath (HTML) |
| `CreateComparisonRule` | Custom ignore rules | RuleName, ComparisonRuleType (Regex/Wildcard), Pattern, UsePlaceholder |

### Comparison Output
- `Result` (bool): True if equivalent
- `Differences` (IEnumerable\<Difference\>): Each with Operation (Inserted/Deleted/Equal) and Text
- `SemanticDifferences`: AI analysis when InterpretDifferencesWithAutopilot=true

---

## Test Data Queue Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `GetTestDataQueueItem` | Get next item | QueueName, MarkConsumed (default true) |
| `GetTestDataQueueItems` | Batch fetch with filter | QueueName, Status (All/OnlyConsumed/OnlyNotConsumed), Top, Skip |
| `NewAddTestDataQueueItem` | Add single item | QueueName, ItemInformation (Dict\<string, InArgument\>) |
| `BulkAddTestDataQueue` | Add from DataTable | QueueName, QueueItemsDataTable |
| `DeleteTestDataQueueItems` | Delete items | TestDataQueueItems (must have valid Ids) |
| ~~`AddTestDataQueueItem`~~ | **OBSOLETE** | Use NewAddTestDataQueueItem instead |

---

## Test Data Generation

| Activity | Output | Key Arguments |
|----------|--------|---------------|
| `RandomString` | string | Case (Lower/Upper/Camel/Mixed), Length (default 10) |
| `RandomNumber` | decimal | Min, Max, Decimals (default 0) |
| `RandomDate` | DateTime | MinDate, MaxDate |
| `RandomValue` | string | FilePath (one value per line, random selection) |
| `GivenName` | string | (from predefined list) |
| `LastName` | string | (from predefined list) |
| `Address` | Dict\<string, string\> | Country, City (both hidden in designer) |

---

## Critical Gotchas

### Assertions
1. **ContinueOnFailure=true by default in designer activities** - assertions don't stop workflow; set to false for strict testing. **Note**: Coded workflow API defaults to `false` (opts?.ContinueOnError ?? false)
2. **Screenshot capture** available on both success and failure (separate flags, both default false)
3. **VerifyControlAttribute cannot be nested** inside another VerifyControlAttribute
4. **Type compatibility validated at CacheMetadata** - incompatible types cause design-time errors
5. **RegexMatch operator** uses full .NET regex engine

### Document Comparison
6. **ComparePdfDocuments creates visual diff PDFs** - `{filename}_result.pdf` for both baseline and target
7. **CompareText creates HTML diff report** at OutputFilePath (default "differences.html")
8. **Rules (regex/wildcard)** allow ignoring dynamic content (dates, IDs)
9. **Semantic analysis (Autopilot)** provides AI explanation separate from byte-level diff

### Test Data Queues
10. **Requires Orchestrator** - all queue operations go through IOrchestratorService
11. **MarkConsumed=true** prevents item from being returned again
12. **Batch fetch max 1000** items per internal API call
13. **Top=0 treated as null** (no limit)
14. **Delete requires valid Ids** - items must be previously retrieved
15. **BulkAdd DataTable columns must be unique** - throws InvalidArgumentsException
16. **Queue items stored as JSON** in Orchestrator

### Test Data Generation
17. **RandomValue reads from file** - file must exist with line-delimited values
18. **Address Country/City inputs hidden in designer** but available programmatically
19. **RandomDate validates MinDate < MaxDate** (skipped for expression arguments)

### Misc
20. **AttachDocument** uploads file to Orchestrator as test evidence
21. **CoverageMergeActivity is internal** (Browsable=false) - for test framework infrastructure only
