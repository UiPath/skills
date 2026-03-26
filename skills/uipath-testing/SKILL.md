---
name: uipath-testing
description: "UiPath Test Suite assistant — create and run test cases, manage test sets and test schedules, write assertions, generate test reports, and integrate automated testing into CI/CD pipelines. Covers coded test cases (C#), RPA test cases (XAML), Test Manager projects, and data-driven testing. TRIGGER when: User wants to write or run automated tests for a UiPath workflow; User mentions test cases, test sets, test schedules, or test execution; User wants to validate workflow correctness with assertions; User asks about UiPath Test Suite or Test Manager; User wants to integrate UiPath tests into a CI/CD pipeline; User wants to do data-driven testing with CSV or Excel input; User asks how to check if a workflow produces correct outputs. DO NOT TRIGGER when: User is building automation logic (use uipath-coded-workflows or uipath-rpa-workflows instead), or asking about Orchestrator deployment only (use uipath-platform instead)."
metadata:
   allowed-tools: Bash, Read, Write, Glob, Grep
---

# UiPath Test Suite Assistant

Build, run, and manage automated tests for UiPath automations — covering coded test cases, test sets, Test Manager, and CI/CD integration.

## When to Use This Skill

- User wants to **write a test case** for a coded workflow or RPA workflow
- User wants to **run tests** and check results from the CLI
- User wants to **organize tests** into test sets and schedule them
- User wants to **write assertions** to validate workflow outputs
- User wants to **do data-driven testing** using CSV or Excel test data
- User wants to **integrate tests into CI/CD** (GitHub Actions, Azure DevOps)
- User wants to **view test reports** and track pass/fail history
- User wants to **mock dependencies** or test workflows in isolation

## Quick Start

### Step 1 — Resolve project directory

Before creating or running tests, determine `PROJECT_DIR` (the folder with `project.json`). See the uipath-coded-workflows skill for the full resolution procedure.

### Step 2 — Create a test project (if no project exists)

```bash
uip rpa create-project \
  --name "MyAutomation.Tests" \
  --location "<PARENT_DIR>" \
  --template-id TestAutomationProjectTemplate \
  --studio-dir "<STUDIO_DIR>" \
  --format json
```

### Step 3 — Write test cases

Test cases are C# classes inheriting from `CodedWorkflow` with `[TestCase]` attribute. See [Coded Test Cases](#coded-test-cases) below.

### Step 4 — Run tests

```bash
# Run all tests in the project
uip rpa run-tests --project-dir "<PROJECT_DIR>" --studio-dir "<STUDIO_DIR>" --format json

# Run a specific test file
uip rpa run-tests --project-dir "<PROJECT_DIR>" --file-path "<TEST_FILE>.cs" --studio-dir "<STUDIO_DIR>" --format json
```

## Task Navigation

| I need to... | Read these |
|---|---|
| **Write a coded test case (C#)** | [Coded Test Cases](#coded-test-cases) |
| **Write a XAML test case** | [XAML Test Cases](#xaml-test-cases) |
| **Use assertions** | [Assertions & Verification](#assertions--verification) |
| **Do data-driven testing** | [Data-Driven Testing](#data-driven-testing) |
| **Organize tests into test sets** | [Test Sets & Test Manager](#test-sets--test-manager) |
| **Schedule automated test runs** | [Test Schedules](#test-schedules) |
| **Run tests from CI/CD** | [CI/CD Integration](#cicd-integration) |
| **View and export test reports** | [Test Reports](#test-reports) |
| **Mock workflow dependencies** | [Mocking & Isolation](#mocking--isolation) |

---

## Coded Test Cases

Coded test cases use C# with the `[TestCase]` attribute to test workflow logic programmatically.

### Structure

```csharp
using UiPath.CodedWorkflows;
using UiPath.Testing.API;

namespace MyAutomation_Tests
{
    public class InvoiceProcessingTests : CodedWorkflow
    {
        [TestCase]
        public void ValidInvoice_ExtractsCorrectTotal()
        {
            // Arrange
            var testInvoicePath = "TestData/sample-invoice.pdf";

            // Act — invoke the workflow under test
            var result = workflows.ProcessInvoice(testInvoicePath);

            // Assert
            testing.VerifyExpression(result.TotalAmount == 1250.00m, "Total amount should be 1250.00");
            testing.VerifyExpression(result.VendorName == "Acme Corp", "Vendor name should be Acme Corp");
        }

        [TestCase]
        public void MissingVendor_ThrowsValidationError()
        {
            // Arrange
            var invalidInvoicePath = "TestData/missing-vendor.pdf";

            // Act & Assert — expect exception
            testing.VerifyExpressionWithOperator(
                workflows.ProcessInvoice(invalidInvoicePath).IsValid,
                false,
                "Invalid invoice should fail validation"
            );
        }
    }
}
```

### Key rules for test cases

1. **Inherit from `CodedWorkflow`** — same as regular workflows
2. **Attribute must be `[TestCase]`** — NOT `[Workflow]`
3. **Method name describes the test** — use `MethodUnderTest_Scenario_ExpectedResult` naming
4. **One assertion per test** — keep tests focused; multiple assertions are allowed but test one behavior
5. **Generate `.cs.json` metadata** alongside each test file
6. **Add to `fileInfoCollection`** in `project.json` — test files go here, not in `entryPoints`

### project.json entry for test cases

```json
{
  "fileInfoCollection": [
    {
      "fileName": "InvoiceProcessingTests.cs",
      "entryPoint": "InvoiceProcessingTests.ValidInvoice_ExtractsCorrectTotal",
      "filePath": "InvoiceProcessingTests.cs"
    },
    {
      "fileName": "InvoiceProcessingTests.cs",
      "entryPoint": "InvoiceProcessingTests.MissingVendor_ThrowsValidationError",
      "filePath": "InvoiceProcessingTests.cs"
    }
  ]
}
```

---

## XAML Test Cases

For testing RPA/XAML workflows, use the **Test Case** workflow type in Studio.

### Create a XAML test case via CLI

```bash
uip rpa find-activities --query "VerifyExpression" --project-dir "<PROJECT_DIR>" --format json
```

XAML test cases use the same `[TestCase]` workflow type. Key activities:
- `Verify Expression` — assert a boolean expression is true
- `Verify Expression With Operator` — compare two values with an operator
- `Verify Control Attribute` — assert a UI element property matches expected value
- `Take Screenshot` — capture evidence for test reports
- `Mock Application` — replace an application's behavior for isolated testing

---

## Assertions & Verification

### Coded workflow assertions

```csharp
// Boolean assertion
testing.VerifyExpression(actualValue == expectedValue, "Values should match");

// Comparison with operator
testing.VerifyExpressionWithOperator(actualCount, 5, "Item count should be 5");

// String contains
testing.VerifyExpression(
    result.Contains("SUCCESS"),
    $"Result '{result}' should contain SUCCESS"
);

// Numeric range
testing.VerifyExpression(
    responseTime.TotalMilliseconds < 3000,
    $"Response time {responseTime.TotalMilliseconds}ms should be under 3000ms"
);
```

### Assertion failure behavior

When an assertion fails:
- The test case is marked **Failed** in the test report
- The failure message you provided appears in the results
- Execution stops at the failed assertion (does not continue to next line)
- Subsequent test cases in the same test set continue running

### Common assertion patterns

| What to verify | Assertion |
|---|---|
| Value equals expected | `testing.VerifyExpression(actual == expected, msg)` |
| Value not null | `testing.VerifyExpression(result != null, msg)` |
| Collection not empty | `testing.VerifyExpression(items.Count > 0, msg)` |
| String starts with | `testing.VerifyExpression(str.StartsWith("INV-"), msg)` |
| File was created | `testing.VerifyExpression(File.Exists(path), msg)` |

---

## Data-Driven Testing

Run the same test case with multiple input/output combinations from a CSV or Excel file.

### Step 1 — Create test data file

Create `TestData/invoices.csv`:
```csv
FilePath,ExpectedVendor,ExpectedTotal
TestData/acme-invoice.pdf,Acme Corp,1250.00
TestData/globex-invoice.pdf,Globex Corp,3400.50
TestData/initech-invoice.pdf,Initech,875.00
```

### Step 2 — Link data source in project.json

```json
{
  "fileInfoCollection": [
    {
      "fileName": "InvoiceTests.cs",
      "entryPoint": "InvoiceTests.ValidateInvoice",
      "filePath": "InvoiceTests.cs",
      "dataVariations": {
        "dataSource": "TestData/invoices.csv",
        "dataSourceType": "CSV"
      }
    }
  ]
}
```

### Step 3 — Accept data parameters in test case

```csharp
[TestCase]
public void ValidateInvoice(string filePath, string expectedVendor, decimal expectedTotal)
{
    var result = workflows.ProcessInvoice(filePath);
    testing.VerifyExpression(result.VendorName == expectedVendor, $"Vendor: expected {expectedVendor}");
    testing.VerifyExpression(result.TotalAmount == expectedTotal, $"Total: expected {expectedTotal}");
}
```

Each CSV row generates one test execution — results appear individually in the test report.

---

## Test Sets & Test Manager

Organize test cases into test sets for structured test campaigns.

### CLI commands for Test Manager

```bash
# List Test Manager projects
uip tm projects list --format json

# Create a test set
uip tm testsets create --project-id "<PROJECT_ID>" --name "Regression Suite v2.1" --format json

# Add test cases to a test set
uip tm testsets add-cases --testset-id "<TESTSET_ID>" --case-ids "<CASE_ID_1>,<CASE_ID_2>" --format json

# Execute a test set
uip tm testsets execute --testset-id "<TESTSET_ID>" --format json

# List test executions
uip tm executions list --project-id "<PROJECT_ID>" --format json

# Get execution results
uip tm executions get --execution-id "<EXECUTION_ID>" --format json
```

### Test set organization strategy

```
Test Manager Project
├── Smoke Tests (run on every deployment, ~5 min)
│   ├── ConnectivityCheck
│   ├── AuthenticationTest
│   └── BasicWorkflowRun
├── Regression Suite (run nightly, ~30 min)
│   ├── InvoiceProcessingTests
│   ├── EmailAutomationTests
│   └── QueueProcessingTests
└── Performance Tests (run weekly)
    ├── HighVolumeProcessingTest
    └── ConcurrentJobTest
```

---

## Test Schedules

Automatically run test sets on a schedule.

### CLI commands

```bash
# Create a test schedule (daily at 2 AM)
uip tm schedules create \
  --project-id "<PROJECT_ID>" \
  --testset-id "<TESTSET_ID>" \
  --name "Nightly Regression" \
  --cron "0 2 * * *" \
  --format json

# List schedules
uip tm schedules list --project-id "<PROJECT_ID>" --format json

# Enable/disable a schedule
uip tm schedules enable --schedule-id "<SCHEDULE_ID>" --format json
uip tm schedules disable --schedule-id "<SCHEDULE_ID>" --format json
```

### Recommended schedule strategy

| Test Set | Schedule | Rationale |
|---|---|---|
| Smoke Tests | After every deployment | Fast validation of critical paths |
| Regression Suite | Nightly (2 AM) | Full coverage without blocking CI |
| Performance Tests | Weekly (Sunday midnight) | Track degradation over time |

---

## CI/CD Integration

Integrate UiPath test execution into GitHub Actions or Azure DevOps.

### GitHub Actions example

```yaml
name: UiPath Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UiPath CLI
        run: npm install -g @uipath/cli

      - name: Authenticate with UiPath Cloud
        run: |
          uip login \
            --client-id "${{ secrets.UIPATH_CLIENT_ID }}" \
            --client-secret "${{ secrets.UIPATH_CLIENT_SECRET }}" \
            --tenant "${{ secrets.UIPATH_TENANT }}" \
            --format json

      - name: Execute test set
        run: |
          uip tm testsets execute \
            --testset-id "${{ vars.TESTSET_ID }}" \
            --format json

      - name: Wait for results and check pass/fail
        run: |
          # Poll until execution completes, then exit 1 if any failures
          # See test-runner script in your repo
```

### Azure DevOps

Use the **UiPath Test Run** task from the UiPath Azure DevOps extension, or use the CLI commands above in a script step.

---

## Test Reports

View, filter, and export test results.

### CLI commands

```bash
# Get test execution summary
uip tm executions get --execution-id "<EXECUTION_ID>" --format json

# List all test case results for an execution
uip tm results list --execution-id "<EXECUTION_ID>" --format json

# Download execution report (PDF/HTML)
uip tm executions export --execution-id "<EXECUTION_ID>" --output-path "./report.pdf" --format json

# Get failed tests only
uip tm results list --execution-id "<EXECUTION_ID>" --status Failed --format json
```

### Reading results programmatically

```bash
# Get pass rate
uip tm executions get --execution-id "<EXECUTION_ID>" --format json \
  | jq '.Data.PassRate'

# Get failed test names
uip tm results list --execution-id "<EXECUTION_ID>" --status Failed --format json \
  | jq '.Data[].TestCaseName'
```

---

## Mocking & Isolation

Test workflows in isolation by mocking external dependencies.

### Mock Orchestrator assets in test environments

Create a dedicated test folder in Orchestrator with test-specific asset values:
```bash
uip or folders create --name "TestEnvironment" --format json
uip resources assets create --name "ApiEndpoint" --value "https://mock.api.internal" --folder "TestEnvironment" --format json
```

Point your test workflow runs at the `TestEnvironment` folder.

### Mock external HTTP calls

Use a local mock server (e.g., WireMock) running on `localhost` and set the base URL asset to the mock endpoint:

```csharp
// In test setup — point to mock server
var apiBaseUrl = "http://localhost:9090";  // mock server
// In production workflow — reads from asset
var apiBaseUrl = system.GetAsset("ApiBaseUrl");
```

### Isolate queue processing tests

Create a dedicated test queue and inject test items before running:

```bash
uip resources queues create --name "TestInvoiceQueue" --folder "TestEnvironment" --format json
uip resources queueitems add --queue "TestInvoiceQueue" --data '{"InvoicePath":"TestData/sample.pdf"}' --folder "TestEnvironment" --format json
```

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Test passes locally but fails in CI | Ensure Studio is installed on CI agent; use `--studio-dir` flag |
| `[TestCase]` method not found in results | Check `fileInfoCollection` in `project.json`; validate the file |
| Data-driven test runs only once | Verify `dataVariations` section in `project.json`; CSV column names must match parameter names exactly |
| Assertion failure message is unhelpful | Include actual values in the message: `$"Expected 5, got {actual}"` |
| Tests interact with production data | Always use a separate test Orchestrator folder and test assets |
| Test set execution times out | Break large test sets into smaller ones; increase execution timeout in Test Manager |

## References

- **[UiPath Platform Skill](../uipath-platform/SKILL.md)** — Test Manager CLI commands, authentication
- **[Coded Workflows Skill](../uipath-coded-workflows/SKILL.md)** — Coded workflow patterns, project structure, validation
- **[UiPath Test Suite docs](https://docs.uipath.com/test-suite)** — Official product documentation
- **[UiPath Test Manager docs](https://docs.uipath.com/test-manager)** — Test project, test set, and schedule management
