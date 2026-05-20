# Testing & Debugging Guide

Test design strategy, mock testing patterns, and debugging guidance for legacy UiPath workflows.

For test assertion activity properties/XAML, see [activity-docs/Testing.md](./activity-docs/Testing.md).
For test data file generation, see [test-data-guide.md](./test-data-guide.md).
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

See [activity-docs/Testing.md](./activity-docs/Testing.md) for activity properties, XAML syntax, and gotchas.

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
