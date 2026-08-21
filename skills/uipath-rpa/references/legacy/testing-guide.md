# Testing & Debugging Guide

Test design strategy, mock testing patterns, and debugging guidance for legacy UiPath workflows.

Test assertion activity properties/XAML: [§ Testing Activities Reference](#testing-activities-reference) below.
Test data file generation: [§ Test Data Creation](#test-data-creation) below.
For CLI debug command, see [cli-reference.md](./cli-reference.md).

---

## 1. Test Case Structure

Test cases are `.xaml` workflows that verify specific behaviors of your automation.

### File Organization

```
{projectRoot}/
├── Tests/
│   ├── Test_ProcessInvoice_ValidData_Success.xaml
│   ├── Test_ProcessInvoice_MissingVendor_ThrowsBusinessException.xaml
│   ├── Test_ProcessInvoice_NegativeAmount_ThrowsBusinessException.xaml
│   ├── Test_ValidateInput_EmptyString_ReturnsFalse.xaml
│   └── Tests.xlsx                    # Test data for data-driven tests
```

### Naming Convention

`Test_[Workflow]_[Scenario]_[Expected].xaml`

| Part | Description | Examples |
|---|---|---|
| `Test_` | Prefix — identifies as test case | Always `Test_` |
| `[Workflow]` | Workflow being tested | `ProcessInvoice`, `ValidateInput`, `SendEmail` |
| `[Scenario]` | Input condition or scenario | `ValidData`, `MissingVendor`, `NegativeAmount`, `EmptyString` |
| `[Expected]` | Expected outcome | `Success`, `ThrowsBusinessException`, `ReturnsFalse`, `CreatesOutput` |

### Test Case Workflow Pattern

```
Sequence "Test_ProcessInvoice_ValidData_Success"
  ├── [SETUP] Prepare test data
  │   ├── Assign: testInvoiceNumber = "TEST-INV-001"
  │   ├── Assign: testAmount = 1500.00
  │   └── Assign: testVendor = "Acme Corp"
  │
  ├── [EXECUTE] Run the workflow under test
  │   └── Invoke Workflow File: "BusinessLogic/ProcessInvoice.xaml"
  │       Arguments: in_InvoiceNumber = testInvoiceNumber, in_Amount = testAmount, ...
  │       Output: out_Result = actualResult
  │
  ├── [VERIFY] Assert expected outcomes
  │   ├── Verify Expression: actualResult.Contains("Success")
  │   └── Verify Expression: out_ConfirmationNumber IsNot Nothing
  │
  └── [TEARDOWN] Clean up test artifacts
      └── Delete File: testOutputFile (if created)
```

---

## 2. Verification Activities

Use these activities from `UiPath.Testing.Activities` to assert expected outcomes.

### When to Use Each

| Activity | Use When | Example |
|---|---|---|
| **Verify Expression** | Boolean condition check | `actualResult = "Success"` |
| **Verify Expression with Operator** | Comparison with specific operator | `amount` Greater Than `0` |
| **Verify Control Attribute** | UI element attribute check | Button's `enabled` attribute = `True` |
| **Verify Range** | Numeric bounds check | `amount` Between `0` and `10000` |

### Rules

1. **One verification per test case** — test one behavior at a time. Multiple assertions make it unclear which behavior failed.
2. **Use descriptive assertion messages** — `"Invoice amount should be positive"` not `"Test failed"`
3. **Verify the OUTCOME, not the process** — check that the result is correct, not that specific activities were called

See [§ Testing Activities Reference](#testing-activities-reference) for activity properties, XAML syntax, and gotchas.

---

## 3. Data-Driven Testing

Run the same test with multiple data sets to verify behavior across different inputs.

### Pattern: Excel-Driven Tests

```
Sequence "Test_ValidateInput_MultipleScenarios"
  ├── Read Range: "Tests/TestData_ValidateInput.xlsx" → dt_TestData
  │
  └── For Each Row in dt_TestData
      ├── Assign: testInput = row("Input").ToString()
      ├── Assign: expectedResult = CBool(row("ExpectedValid"))
      │
      ├── Invoke Workflow File: "BusinessLogic/ValidateInput.xaml"
      │   Arguments: in_Value = testInput
      │   Output: out_IsValid = actualResult
      │
      └── Verify Expression: actualResult = expectedResult
          OutputMessage: "Failed for input: " & testInput
```

### Test Data Excel Structure

| Input | ExpectedValid | Description |
|---|---|---|
| `"INV-12345"` | True | Valid invoice number |
| `""` | False | Empty string |
| `"INV"` | False | Incomplete format |
| `"INV-99999999999"` | False | Number too long |
| `"inv-12345"` | True | Lowercase (should be case-insensitive) |

### Data Sources

| Source | Best For |
|---|---|
| Excel file in Tests/ folder | Small test data sets, easy to review |
| CSV file | Portable, version-control friendly |
| Orchestrator Test Data Queue | Cloud-hosted test data, shared across team |

---

## 4. Mock Testing

Isolate the workflow under test by replacing external dependencies with controlled substitutes.

### Strategy: Argument Injection

Design workflows with arguments for external dependencies, then inject mock data during testing:

**Production call:**
```
Invoke Workflow: ProcessInvoice.xaml
  in_TransactionItem = orchestratorQueueItem
  in_Config = productionConfig
```

**Test call:**
```
Invoke Workflow: ProcessInvoice.xaml
  in_TransactionItem = mockQueueItem      ← controlled test data
  in_Config = testConfig                  ← test-specific config
```

### What to Mock

| Dependency | Mock Strategy |
|---|---|
| Orchestrator Queue Item | Create a mock Dictionary(Of String, Object) with SpecificContent fields |
| API Response | Create a test JSON string matching the API response format |
| Database Query Result | Build a test DataTable with expected columns and sample rows |
| Email | Skip sending; verify that the email arguments are correct |
| File System | Use temp directory; create test files in setup, delete in teardown |
| Config.xlsx | Create a test Dictionary(Of String, Object) with test values |

### Mock Queue Item Example

```vb
' In test setup:
Dim mockSpecificContent As New Dictionary(Of String, Object) From {
    {"InvoiceNumber", "TEST-INV-001"},
    {"Amount", "1500.00"},
    {"VendorName", "Test Vendor"}
}
```

### Rules

1. **Mock external systems, not internal workflows** — mock the database/API/email, not the sub-workflow that calls them
2. **Verify mock inputs match production structure** — if the real API returns 20 fields, your mock should have the same 20 fields
3. **Test failure paths with mocks** — inject invalid data, empty responses, exception conditions
4. **Don't mock what you're testing** — if you're testing email sending, don't mock the email activity

---

## 5. Test Independence

### Rules

1. **Each test is self-contained** — creates its own test data, doesn't depend on other tests
2. **No execution order dependencies** — tests can run in any order and produce the same results
3. **Setup and teardown within each test** — create test files at start, delete them at end
4. **Clean state between tests** — don't assume a previous test left the system in a specific state
5. **No shared mutable state** — don't use global variables or shared files across tests

### Test Isolation Pattern

```
Sequence "Test_WriteReport_CreatesFile"
  ├── [SETUP]
  │   ├── Assign: testOutputPath = Path.Combine(Path.GetTempPath(), "test_report_" & Guid.NewGuid().ToString() & ".xlsx")
  │   └── Assign: testData = CreateTestDataTable()
  │
  ├── [EXECUTE]
  │   └── Invoke Workflow: WriteReport.xaml
  │       in_OutputPath = testOutputPath, in_Data = testData
  │
  ├── [VERIFY]
  │   ├── Verify Expression: File.Exists(testOutputPath)
  │   └── Read Range: testOutputPath → verify row count matches
  │
  └── [TEARDOWN]
      └── Delete File: testOutputPath
```

---

## 6. Debugging Guidance

When the agent advises users on debugging, or when documenting troubleshooting steps.

### Studio Debugging Tools

| Tool | Shortcut | Purpose |
|---|---|---|
| **Step Into** | F11 | Execute next activity, entering sub-workflows |
| **Step Over** | F10 | Execute next activity, skipping into sub-workflows |
| **Step Out** | Shift+F11 | Execute remaining activities in current workflow, return to caller |
| **Run to Activity** | Right-click → Run to This Activity | Execute until a specific activity |

### Breakpoints

| Feature | Usage |
|---|---|
| **Basic breakpoint** | Click line margin — pauses execution at that activity |
| **Conditional breakpoint** | Right-click breakpoint → Condition: `amount > 10000` — only pauses when condition is true |
| **Hit count** | Pause only after N executions — useful for debugging loop iteration 50 of 100 |
| **Log When Hit** | Log a message instead of pausing — non-intrusive tracing |

### Debug Panels

| Panel | Shows | Use For |
|---|---|---|
| **Locals** | All variables and arguments in current scope with values | Inspecting variable state at breakpoint |
| **Watch** | User-defined expressions evaluated at each step | Monitoring specific expressions across execution |
| **Immediate** | Execute VB.NET/C# expressions during pause | Testing expressions, calling methods, checking conditions |
| **Call Stack** | Workflow invocation chain (which workflow called which) | Understanding execution path, finding which caller triggered an error |
| **Output** | Log messages, system messages | Reviewing execution history |

### Binary Search Debugging Pattern

When a long workflow fails and the error isn't obvious:

1. Set a breakpoint at the **middle** of the workflow
2. Run — did the breakpoint hit without errors? The bug is in the second half.
3. Did it error before hitting the breakpoint? The bug is in the first half.
4. Move the breakpoint to the middle of the problem half.
5. Repeat until you isolate the failing activity.

### Test Activity Feature

Studio's **Test Activity** (right-click an activity → Test Activity) runs a single activity in isolation:
- Prompts for input argument values
- Executes only that activity
- Shows output values and any exceptions
- Useful for testing activities with complex configuration (HTTP Request, database queries)

---

## 7. Test Strategy

### What to Test

| Priority | Test Type | Examples |
|---|---|---|
| **1 (Critical)** | Happy path — normal successful execution | Valid invoice processes correctly |
| **2 (High)** | Business exceptions — invalid data handling | Missing fields, invalid formats, rule violations |
| **3 (High)** | Edge cases — boundary conditions | Zero amount, maximum length strings, empty DataTables |
| **4 (Medium)** | Negative tests — error conditions | API timeout, file not found, invalid credentials |
| **5 (Low)** | Regression tests — previously fixed bugs | Specific scenarios that caused past failures |

### Rules

1. **Test the automation, not the application** — verify that YOUR workflow handles data correctly, don't test that the web portal's Submit button works
2. **Prioritize critical paths** — test the main transaction processing flow first, edge cases second
3. **Include negative tests** — verify that invalid data throws `BusinessRuleException` (not silently processes)
4. **Run regression suite after changes** — any modification to a workflow should re-run all tests for that workflow
5. **Keep tests fast** — mock external systems to avoid network/UI delays in tests

---

## 8. CI/CD Integration

### Test Execution Strategy

| Stage | Tests | Purpose |
|---|---|---|
| **On commit** | Smoke tests (happy path only) | Fast feedback — catch breaking changes |
| **On deployment to Test** | Full regression suite | Comprehensive validation before UAT |
| **On deployment to Prod** | Smoke tests + critical path | Final validation in production environment |

### Orchestrator Test Sets

Tests can be organized into **Test Sets** in Orchestrator Test Manager:
- Group related tests (all invoice processing tests)
- Schedule test execution
- Track test results over time
- Integrate with CI/CD pipelines

### Rules

1. **Smoke tests should run in under 5 minutes** — fast feedback loop
2. **Full regression can take longer** — but should complete within a release window
3. **Test in an environment matching production** — same Orchestrator folder structure, same asset configuration
4. **Version test data alongside workflows** — test Excel files and expected results in the same project

---

## Test Data Creation

How to create test data files and UiPath types for legacy workflow testing.

---

### Excel Test Data (COM-Compliant)

#### Using ExcelApplicationScope (Interop — .xls/.xlsx)

Create a DataTable in code, then write it via Excel Interop:

```xml
<!-- Step 1: Build DataTable with InvokeCode -->
<ui:InvokeCode Code="
Dim dt As New DataTable()
dt.Columns.Add(&quot;Name&quot;, GetType(String))
dt.Columns.Add(&quot;Amount&quot;, GetType(Double))
dt.Columns.Add(&quot;Date&quot;, GetType(String))
dt.Columns.Add(&quot;Status&quot;, GetType(String))
dt.Rows.Add(&quot;Invoice-001&quot;, 1500.50, &quot;2024-01-15&quot;, &quot;Active&quot;)
dt.Rows.Add(&quot;Invoice-002&quot;, 2300.00, &quot;2024-02-20&quot;, &quot;Pending&quot;)
dt.Rows.Add(&quot;Invoice-003&quot;, 890.25, &quot;2024-03-10&quot;, &quot;Closed&quot;)
dt.Rows.Add(&quot;Invoice-004&quot;, 0, &quot;&quot;, &quot;Active&quot;)
dt.Rows.Add(&quot;Invoice-005&quot;, -100.00, &quot;2024-12-31&quot;, &quot;Error&quot;)
testData = dt" Language="VBNet">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <OutArgument x:TypeArguments="sd:DataTable" x:Key="testData">[dtTestData]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>

<!-- Step 2: Write to Excel via ExcelApplicationScope -->
<!-- Use ExcelApplicationScope + ExcelWriteRange (Interop) for .xls/.xlsx -->
```

#### Test data design principles
- Include edge cases: empty strings, zero values, negative numbers, special characters
- Include null/DBNull values to test null handling
- Mix data types per column to test type coercion
- Include dates in multiple formats to test parsing
- Include at least 5-10 rows for meaningful iteration testing

#### Using WriteCsvFile (Portable — no Excel needed)

```xml
<!-- Write CSV then optionally convert to Excel -->
<ui:WriteCsvFile FilePath="[Path.Combine(Environment.CurrentDirectory, &quot;Data&quot;, &quot;test.csv&quot;)]"
  DataTable="[dtTestData]" />
```

---

### Top 10 File Types

| File Type | How to Create | Key Activity | Notes |
|-----------|--------------|-------------|-------|
| **Excel (.xls/.xlsx)** | `ExcelApplicationScope` + `ExcelWriteRange` | COM Interop | Use `.xls` for max legacy compat; `.xlsx` for modern |
| **CSV (.csv)** | `WriteCsvFile` or `Write Text File` | Portable | Set `Delimitator` explicitly; specify `"UTF-8"` encoding |
| **Text (.txt)** | `Write Text File` activity | System.IO | Use `Encoding="UTF-8"` for portability |
| **JSON (.json)** | `Serialize JSON` + `Write Text File` | WebAPI package | Build JObject/JArray in InvokeCode, serialize, write |
| **XML (.xml)** | Build XDocument in InvokeCode + `Write Text File` | System.Xml.Linq | Or use `Serialize XML` if available |
| **PDF (.pdf)** | Export from Excel/Word scope, or HTML string + wkhtmltopdf | Requires source app | No native PDF creation activity in legacy |
| **Word (.docx)** | `WordApplicationScope` + `Word Write Text` | COM Interop | Requires Word installed |
| **HTML (.html)** | `Write Text File` with HTML string content | String building | Build HTML in InvokeCode or Assign |
| **Email (.eml/.msg)** | `Save Mail Message` from mail activities | Mail package | Create MailMessage object first |
| **Config (.xlsx)** | REFramework pattern: Config.xlsx with Settings/Constants/Assets sheets | Excel Interop | See `_REFRAMEWORK.md` for sheet structure |

#### Creating JSON test data

```vb
' InvokeCode — build JSON string
Dim json As String = "{" & vbCrLf &
  "  ""name"": ""Test User""," & vbCrLf &
  "  ""amount"": 1500.50," & vbCrLf &
  "  ""items"": [""A"", ""B"", ""C""]" & vbCrLf &
  "}"
output = json
```

#### Creating XML test data

```vb
' InvokeCode — build XML string
Dim xml As String = "<?xml version=""1.0"" encoding=""UTF-8""?>" & vbCrLf &
  "<Invoices>" & vbCrLf &
  "  <Invoice Id=""001"" Amount=""1500.50"" />" & vbCrLf &
  "  <Invoice Id=""002"" Amount=""2300.00"" />" & vbCrLf &
  "</Invoices>"
output = xml
```

---

### Top 10 UiPath Types

| Type | How to Create | Common Test Values | VB.NET Expression |
|------|--------------|-------------------|-------------------|
| **DataTable** | `Build Data Table` activity or InvokeCode | Headers + 5-10 rows, mixed types, nulls | `New DataTable()` |
| **String** | `Assign` / literal | `"test"`, `""`, `Nothing`, special chars `<>&"` | `"value"` |
| **Int32** | `Assign` / `CInt()` | `0`, `-1`, `Integer.MaxValue`, `Integer.MinValue` | `CInt("42")` |
| **Boolean** | `Assign` | `True`, `False` | `True` |
| **DateTime** | `Assign` / `DateTime.Parse()` | Today, epoch, future, `DateTime.MinValue` | `DateTime.Now` |
| **Dictionary(Of String, Object)** | InvokeCode or `Assign` | Config-style key-value pairs, nested objects | `New Dictionary(Of String, Object)` |
| **String()** (array) | `Assign` / `Split()` | Empty `{}`, single item, many items | `New String() {"a","b","c"}` |
| **SecureString** | `Get Credential` or InvokeCode | Test password strings | `New NetworkCredential("","pass").SecurePassword` |
| **MailMessage** | `Get Outlook Mail Messages` or InvokeCode | Email with To/Subject/Body/Attachments | `New System.Net.Mail.MailMessage()` |
| **QueueItem** | `Get Transaction Item` from Orchestrator | SpecificContent dictionary, Priority, Deadline | Requires Orchestrator queue |

#### Creating a test Dictionary (Config-style)

```vb
' InvokeCode
Dim config As New Dictionary(Of String, Object)
config("MaxRetryNumber") = 3
config("logF_BusinessProcessName") = "TestProcess"
config("OrchestratorQueueName") = "TestQueue"
config("ExcelFilePath") = "Data\Input\test.xlsx"
output = config
```

#### Creating a test DataTable with edge cases

```vb
' InvokeCode
Dim dt As New DataTable()
dt.Columns.Add("Name", GetType(String))
dt.Columns.Add("Amount", GetType(Double))
dt.Columns.Add("IsActive", GetType(Boolean))

' Normal rows
dt.Rows.Add("Alice", 100.50, True)
dt.Rows.Add("Bob", 0, False)

' Edge cases
dt.Rows.Add("", -999.99, True)           ' Empty name
dt.Rows.Add(DBNull.Value, DBNull.Value, DBNull.Value)  ' All nulls
dt.Rows.Add("Special <>&""chars", 1E+15, True)  ' Special chars, large number

testData = dt
```

---

## Testing Activities Reference

### Overview
Test assertions, data generation, document comparison, and test data queue management. Package: `UiPath.Testing.Activities`.

---

### Assertion Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `VerifyExpression` | Assert boolean is true | Expression (bool), ContinueOnFailure (default true) |
| `VerifyExpressionWithOperator` | Compare two values | FirstExpression, SecondExpression, Operator |
| `VerifyRange` | Value within/outside range | Expression, LowerLimit, UpperLimit, VerificationType (IsWithin/IsNotWithin) |
| `VerifyControlAttribute` | Verify activity output | ActivityToTest, OutputArgument, Expression, Operator |

#### Comparison Operators
Equality (=), Inequality (<>), GreaterThan (>), GreaterThanOrEqual (>=), LessThan (<), LessThanOrEqual (<=), Contains, RegexMatch

---

### Document Comparison (NET5+)

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `ComparePdfDocuments` | Diff two PDFs | BaselinePath, TargetPath, ComparisonType (Line/Word/Character), Rules, IncludeImages |
| `CompareText` | Diff two strings | BaselineText, TargetText, ComparisonType, OutputFilePath (HTML) |
| `CreateComparisonRule` | Custom ignore rules | RuleName, ComparisonRuleType (Regex/Wildcard), Pattern, UsePlaceholder |

#### Comparison Output
- `Result` (bool): True if equivalent
- `Differences` (IEnumerable\<Difference\>): Each with Operation (Inserted/Deleted/Equal) and Text
- `SemanticDifferences`: AI analysis when InterpretDifferencesWithAutopilot=true

---

### Test Data Queue Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `GetTestDataQueueItem` | Get next item | QueueName, MarkConsumed (default true) |
| `GetTestDataQueueItems` | Batch fetch with filter | QueueName, Status (All/OnlyConsumed/OnlyNotConsumed), Top, Skip |
| `NewAddTestDataQueueItem` | Add single item | QueueName, ItemInformation (Dict\<string, InArgument\>) |
| `BulkAddTestDataQueue` | Add from DataTable | QueueName, QueueItemsDataTable |
| `DeleteTestDataQueueItems` | Delete items | TestDataQueueItems (must have valid Ids) |
| ~~`AddTestDataQueueItem`~~ | **OBSOLETE** | Use NewAddTestDataQueueItem instead |

---

### Test Data Generation

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

### Critical Gotchas

#### Assertions
1. **ContinueOnFailure=true by default in designer activities** - assertions don't stop workflow; set to false for strict testing. **Note**: Coded workflow API defaults to `false` (opts?.ContinueOnError ?? false)
2. **Screenshot capture** available on both success and failure (separate flags, both default false)
3. **VerifyControlAttribute cannot be nested** inside another VerifyControlAttribute
4. **Type compatibility validated at CacheMetadata** - incompatible types cause design-time errors
5. **RegexMatch operator** uses full .NET regex engine

#### Document Comparison
6. **ComparePdfDocuments creates visual diff PDFs** - `{filename}_result.pdf` for both baseline and target
7. **CompareText creates HTML diff report** at OutputFilePath (default "differences.html")
8. **Rules (regex/wildcard)** allow ignoring dynamic content (dates, IDs)
9. **Semantic analysis (Autopilot)** provides AI explanation separate from byte-level diff

#### Test Data Queues
10. **Requires Orchestrator** - all queue operations go through IOrchestratorService
11. **MarkConsumed=true** prevents item from being returned again
12. **Batch fetch max 1000** items per internal API call
13. **Top=0 treated as null** (no limit)
14. **Delete requires valid Ids** - items must be previously retrieved
15. **BulkAdd DataTable columns must be unique** - throws InvalidArgumentsException
16. **Queue items stored as JSON** in Orchestrator

#### Test Data Generation
17. **RandomValue reads from file** - file must exist with line-delimited values
18. **Address Country/City inputs hidden in designer** but available programmatically
19. **RandomDate validates MinDate < MaxDate** (skipped for expression arguments)

#### Misc
20. **AttachDocument** uploads file to Orchestrator as test evidence
21. **CoverageMergeActivity is internal** (Browsable=false) - for test framework infrastructure only
