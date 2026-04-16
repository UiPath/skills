# Testing Guide

Reference for XAML test automation features in UiPath RPA projects — XAML test case structure, data-driven testing, XAML test activities, execution templates, and mock testing.

> For coded test case creation (Given-When-Then, assertions, Before/After hooks), see [coded/operations-guide.md § Add a Test Case File](coded/operations-guide.md).

## Table of Contents

- [XAML Test Case Structure (Given-When-Then)](#xaml-test-case-structure-given-when-then)
- [Data-Driven Testing](#data-driven-testing)
- [XAML Test Activities](#xaml-test-activities)
- [Execution Templates](#execution-templates)
- [Mock Testing (XAML Only) — WIP](#mock-testing-xaml-only--wip)

---

## XAML Test Case Structure (Given-When-Then)

XAML test cases use a **Given-When-Then** structure — three nested `<Sequence>` elements inside a parent Sequence. The agent generates these directly as XAML.

### XAML Structure — Test Case Invoking a Workflow

The core pattern: a parent Sequence with three child Sequences named `"... Given"`, `"... When"`, `"... Then"`. The **When** section invokes the workflow under test. Add verification activities in **Then**.

```xml
<!-- Body inside <Activity> (after namespaces/references) -->
<Sequence DisplayName="TestMyWorkflow">
  <!-- GIVEN — set up preconditions -->
  <Sequence DisplayName="... Given">
    <!-- Assign variables, open apps, prepare test data -->
  </Sequence>

  <!-- WHEN — execute the workflow under test -->
  <Sequence DisplayName="... When">
    <ui:InvokeWorkflowFile
      DisplayName="MyWorkflow - Invoke Workflow File (MyWorkflow.xaml)"
      WorkflowFileName="MyWorkflow.xaml"
      UnSafe="False">
      <ui:InvokeWorkflowFile.Arguments>
        <scg:Dictionary x:TypeArguments="x:String, Argument" />
      </ui:InvokeWorkflowFile.Arguments>
    </ui:InvokeWorkflowFile>
  </Sequence>

  <!-- THEN — verify results -->
  <Sequence DisplayName="... Then">
    <!-- VerifyExpression, VerifyExpressionWithOperator, etc. -->
  </Sequence>
</Sequence>
```

Required xmlns for `InvokeWorkflowFile`:
```
xmlns:ui="http://schemas.uipath.com/workflow/activities"
```

### XAML Structure — Standalone Test Case (with Placeholder)

For test cases designed to work with execution templates, use `ui:Placeholder` in the When container:

```xml
<Sequence DisplayName="... When">
  <ui:Placeholder
    Description="This placeholder activity will be replaced at build time and can only be used within an execution template." />
</Sequence>
```

### Passing Arguments to Invoked Workflows

If the workflow has arguments, pass them in the `InvokeWorkflowFile.Arguments` dictionary:

```xml
<ui:InvokeWorkflowFile WorkflowFileName="CalculateDiscount.xaml" UnSafe="False">
  <ui:InvokeWorkflowFile.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:Decimal" x:Key="amount">
        <CSharpValue x:TypeArguments="x:Decimal">1500.00m</CSharpValue>
      </InArgument>
      <InArgument x:TypeArguments="x:Decimal" x:Key="discountRate">
        <CSharpValue x:TypeArguments="x:Decimal">0.10m</CSharpValue>
      </InArgument>
    </scg:Dictionary>
  </ui:InvokeWorkflowFile.Arguments>
</ui:InvokeWorkflowFile>
```

### project.json Registration

Register XAML test cases in `fileInfoCollection`. Add `entryPoints` only for **Process** projects — **Tests and Library projects do NOT use `entryPoints`**:

```json
{
  "designOptions": {
    "fileInfoCollection": [
      {
        "editingStatus": "InProgress",
        "testCaseId": "<UNIQUE_GUID>",
        "testCaseType": "TestCase",
        "executionTemplateInvokeIsolated": false,
        "fileName": "TestCase.xaml"
      }
    ]
  },
  "entryPoints": [
    {
      "filePath": "TestCase.xaml",
      "uniqueId": "<SAME_GUID_AS_testCaseId>",
      "input": [],
      "output": []
    }
  ]
}
```

> **Note:** The `entryPoints` block above applies to Process projects only. For Tests and Library projects, only `fileInfoCollection` is needed.

> **`editingStatus` lifecycle:** Set to `"InProgress"` when creating a new test case. Update to `"Publishable"` only when the user explicitly asks to mark the test case as ready.
```

### What NOT to Do

- Do NOT place verification activities in the **When** container — verifications go in **Then**
- Do NOT forget to add the `xmlns:ui` namespace when using `InvokeWorkflowFile`

---

## Data-Driven Testing

Data-driven testing executes the same test case multiple times with different input data sets. Each data row represents a separate test scenario.

### Data Sources Overview

| Source | Where Data Lives | Best For | Agent Support |
|--------|-----------------|----------|---------------|
| **Variations files** | `.variations/` folder in project | File-based test data committed with the project | CLI: `add-test-data-variation` |
| **Test Data Queues** | UiPath Orchestrator | Large-scale distributed testing, parallel execution | CLI: `add-test-data-queue` |
| **Data Service** | UiPath Automation Cloud | Centralized, secure, shared test data | CLI: `add-test-data-entity` |

> For coded data-driven tests using default parameters, see [coded/operations-guide.md § Add a Test Case File](coded/operations-guide.md).

### Variations Files (Coded & XAML)

Store test data in the `.variations/` folder at the project root. Each JSON file maps to a test case and contains rows of input data.

```
MyProject/
├── .variations/
│   └── TestProcessInvoice.json
├── TestProcessInvoice.cs
└── project.json
```

The `.variations/` directory is available in all project types (Process, Tests, Library). Data files must be in **JSON format**.

### Adding Test Data via CLI

Three commands attach different data source types to a test case. All three register the data source in project metadata, extract arguments from the source schema, and add them to the test case (via Studio's workflow management API for XAML, via Roslyn for coded test cases).

#### `add-test-data-variation` — File-based (JSON)

```bash
uip rpa add-test-data-variation --test-case-path "<TEST_CASE_FILE>" --data-variation-path "<DATA_FILE>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-path` | Yes | Relative path to the test case file (`.xaml` or `.cs`) |
| `--data-variation-path` | Yes | Relative path to the JSON data file in `.variations/` |

Parses fields from the JSON file and creates one argument per field with matching type and a default value from the first entry.

**Example:**
```bash
uip rpa add-test-data-variation --test-case-path "TestProcessInvoice.cs" --data-variation-path ".variations/InvoiceData.json" --project-dir "C:\MyProject" --output json --use-studio
```

#### `add-test-data-queue` — Orchestrator Test Data Queue

> **Prerequisite:** Use the **uipath-platform** skill to discover queue details (name, ID, folder) before calling this command.

```bash
uip rpa add-test-data-queue --test-case-path "<TEST_CASE_FILE>" --queue-name "<QUEUE_NAME>" --folder-path "<FOLDER>" --queue-id <ID> --project-dir "<PROJECT_DIR>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-path` | Yes | Relative path to the test case (`.xaml` or `.cs`) |
| `--queue-name` | Yes | Name of the Test Data Queue in Orchestrator |
| `--folder-path` | Yes | Orchestrator folder path |
| `--queue-id` | Yes | Orchestrator ID of the queue |

Creates an `IDictionary<string, object>` argument named after the queue (camelCase).

**Example:**
```bash
uip rpa add-test-data-queue --test-case-path "TestLoanApproval.cs" --queue-name "loan_applications" --folder-path "Shared" --queue-id 123 --project-dir "C:\MyProject" --output json --use-studio
```

> **Critical:** Do NOT rename the auto-generated test data queue argument. If you change its name, data retrieval silently fails.

#### `add-test-data-entity` — Data Service Entity

> **Prerequisite:** Use the **uipath-platform** skill to discover available Data Service entities (name, type) before calling this command.

```bash
uip rpa add-test-data-entity --test-case-path "<TEST_CASE_FILE>" --entity-name "<ENTITY_NAME>" --entity-type-name "<ENTITY_TYPE>" --project-dir "<PROJECT_DIR>" --output json --use-studio
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--test-case-path` | Yes | Relative path to the test case (`.xaml` or `.cs`) |
| `--entity-name` | Yes | Name of the Data Service entity |
| `--entity-type-name` | Yes | Full type name of the entity |

Creates an argument of the entity type named after the entity (camelCase). Requires UiPath Data Service (Automation Cloud) with entities managed in the project.

**Example:**
```bash
uip rpa add-test-data-entity --test-case-path "TestLoanApproval.cs" --entity-name "LoanApplication" --entity-type-name "LoanApplication" --project-dir "C:\MyProject" --output json --use-studio
```

### Data-Driven Testing Best Practices

1. **Separate test data from test logic** — keep data in external sources, not hardcoded in test cases
2. **Include both positive and negative scenarios** — test expected failures too (invalid inputs, boundary values)
3. **Name data fields descriptively** — use field names like `ExpectedResult`, `Scenario` for traceability
4. **Keep data sets small and focused** — each data set should test one concern; avoid combinatorial explosion
5. **Use JSON format** for `.variations/` data files

---

## XAML Test Activities

The `UiPath.Testing.Activities` package provides XAML-specific test activities beyond what the coded `testing` service offers.

### Verification Activities

| Activity | Purpose | Key Properties |
|----------|---------|---------------|
| **VerifyExpression** | Assert a boolean expression is true | `Expression`, `OutputMessage` |
| **VerifyExpressionWithOperator** | Assert two values with a comparison operator | `FirstExpression`, `SecondExpression`, `Operator` |
| **VerifyControlAttribute** | Assert a UI element's attribute matches expected value | `Target`, `AttributeName`, `AttributeValue`, `Operator` |

### VerifyExpressionWithOperator

Compares two **string** expressions using a comparison operator. Both `FirstExpression` and `SecondExpression` are `InArgument<string>` — all values are compared as strings.

**Properties:**
- `FirstExpression` — left-hand value (string)
- `SecondExpression` — right-hand value / expected (string)
- `Operator` — comparison enum. Supported values: `Equality`, `Contains`, `DoesNotContain`, `StartsWith`, `EndsWith`, `Matches` (regex)
- `OutputMessage` — message shown on failure
- `TakeScreenshotIfFailed` (Boolean) — capture screenshot on assertion failure
- `TakeScreenshotIfSucceeded` (Boolean) — capture screenshot on success

> **Important:** `GreaterThan`, `LessThan`, and other numeric operators are NOT supported — they produce a validation error "Operator X is not supported for the specified expression." For numeric comparisons, use `VerifyExpression` with a boolean expression instead (e.g., `amount > 1000`).

### VerifyControlAttribute

Verifies a UI element's attribute (text, enabled state, visibility, etc.) against an expected value.

> **Requires UI automation targets.** This activity inspects live UI elements at runtime. The agent must configure targets using `uia-configure-target` (see [ui-automation-guide.md](ui-automation-guide.md)) before using this activity. The test case must run against a live application instance.

**Properties:**
- `Target` — the UI element to inspect (configured via `uia-configure-target`)
- `AttributeName` — attribute to verify (e.g., `"text"`, `"enabled"`, `"visible"`)
- `AttributeValue` — expected value
- `Operator` — comparison operator (same options as VerifyExpressionWithOperator)
- `TakeScreenshotIfFailed` / `TakeScreenshotIfSucceeded` — screenshot capture

**Constraints:**
- Cannot be nested inside another `VerifyControlAttribute` — causes validation error
- Has platform restrictions — may not work in Portable (cross-platform) projects

### Screenshot Capture on Assertions

All verification activities support automatic screenshot capture:
- `TakeScreenshotIfFailed` — captures the target application window when the assertion fails
- `TakeScreenshotIfSucceeded` — captures when the assertion passes
- Both are `[RequiredArgument]` on assert activities — explicitly set them to `True` or `False`
- Screenshots are attached to test execution results in Test Manager

### Given-When-Then in XAML

The Given-When-Then structure is three nested `<Sequence>` elements — not separate activity types. See [§ XAML Test Case Structure](#xaml-test-case-structure-given-when-then) above for the full XAML patterns and agent workflow.

Place verification activities (VerifyExpression, VerifyExpressionWithOperator, VerifyControlAttribute) inside the `"... Then"` Sequence.

### XAML Test Activity Gotchas

- **BookmarkResumptionHelper** — assert activities require this extension. Studio adds it automatically, but manual XAML construction must include `metadata.RequireExtension<BookmarkResumptionHelper>()` in CacheMetadata
- **VerifyControlAttribute nesting** — cannot nest one inside another
- **Required screenshot arguments** — `TakeScreenshotIfFailed` and `TakeScreenshotIfSucceeded` are required even though they default to `False`. Omitting them causes validation warnings.
- **Platform restrictions** — `VerifyControlAttribute` and some testing activities are Windows-only and may not work in Portable projects

---

## Execution Templates

Execution templates wrap test cases at runtime with predefined execution conditions. They let you reuse the same test case logic across different environments, configurations, or application states without duplicating test code.

### When to Use Execution Templates

- Run the same test case against **multiple environments** (dev, staging, prod)
- Apply **different browser/application configurations** per run
- Set up **common preconditions** (login, navigation) shared across many test cases
- Override **argument values** at runtime without modifying the test case

### How Execution Templates Work

1. Create an execution template: right-click the **Templates** folder → **Add → Execution Template**
2. Define variables and arguments in the template that match names in the test case
3. At runtime, Studio **merges** the test case and template into a temporary file:
   - Arguments with matching names are **linked** — template values override test case defaults
   - Variables with matching names are **linked** — template values take precedence
   - Non-overlapping arguments/variables from both files are included as-is

### Execution Template Structure

```
MyProject/
├── Templates/
│   ├── StagingEnvironment.xaml       ← sets environment-specific variables
│   └── ProductionEnvironment.xaml    ← different config for prod
├── TestCases/
│   └── TestInvoiceProcessing.xaml    ← generic test, environment-agnostic
└── project.json
```

### Key Rules

1. **Name matching is exact** — argument/variable names in the template must match the test case exactly (case-sensitive) for linking to work
2. **Templates do not execute independently** — they only run when associated with a test case
3. **One template per execution** — a test case runs with one execution template at a time; select it in Test Explorer before running
4. **Template arguments override test case defaults** — use this to inject environment-specific values (URLs, credentials, timeouts)

### What NOT to Do with Execution Templates

- Do NOT put test logic (assertions) in an execution template — templates are for configuration only
- Do NOT create templates with arguments that do not match any test case — they will be ignored
- Do NOT rely on execution templates for data-driven testing — use data sources (variations, Data Service, Queues) instead

---

## Mock Testing (XAML Only) — WIP

> **This section is a work in progress.** Full agent support for mock testing requires a CLI command to create mock copies of workflows (e.g., `uip rpa create-mock --file-path <WORKFLOW> --project-dir <DIR>`). Until that command exists, the agent can generate the test case XAML but cannot reliably create mock files programmatically.

Mock testing replaces selected activities or entire invoked workflows with lightweight stand-ins during a test run, isolating the code under test from side effects (database writes, API calls, UI interactions).

> **Coded test cases have no built-in mock framework.** There is no coded equivalent. To isolate dependencies in coded tests, design workflows with injectable parameters or test individual workflows in isolation.

### How Mocking Works

1. The test case's **When** container invokes a **mock copy** instead of the original workflow
2. The mock copy lives at `Mocks/<workflow>_mock.xaml` (mirrors source folder structure)
3. Inside the mock, specific activities are replaced with stand-ins that return predefined values
4. At runtime, mocked activities skip their real logic and return the configured test data

### Test Case with Mock — XAML Structure

```xml
<!-- When container invokes the mock copy instead of the original -->
<Sequence DisplayName="... When">
  <ui:InvokeWorkflowFile
    DisplayName="Main_mock - Invoke Workflow File (Mocks\Main_mock.xaml)"
    WorkflowFileName="Mocks\Main_mock.xaml"
    UnSafe="False">
    <ui:InvokeWorkflowFile.Arguments>
      <scg:Dictionary x:TypeArguments="x:String, Argument" />
    </ui:InvokeWorkflowFile.Arguments>
  </ui:InvokeWorkflowFile>
</Sequence>
```

### Mocks Folder Structure

```
MyProject/
├── Main.xaml                         ← original workflow
├── Mocks/
│   └── Main_mock.xaml                ← mock copy of Main.xaml
├── TestCase.xaml                     ← test case invoking Mocks\Main_mock.xaml
├── TestCaseNoMock.xaml               ← test case invoking Main.xaml directly
└── project.json
```

For workflows in subdirectories, the Mocks folder mirrors the source path:
```
MyProject/
├── Workflows/
│   └── ProcessInvoice.xaml
├── Mocks/
│   └── Workflows/
│       └── ProcessInvoice_mock.xaml
```

### Mock File Behavior

- **Auto-sync:** Changes to the source workflow are applied to the mock file when the project is saved in Studio
- **Edit scope:** In mock files opened in Studio, only mocked activities are editable — non-mocked activities are read-only
- **Multiple mocks:** You can have multiple mock files for the same workflow (different test scenarios)

### What the Agent Cannot Do Yet

1. **Create mock files** — there is no `uip rpa create-mock` CLI command. The mock file must be created via Studio's "Create Test Case" dialog with the **"Mock workflow under test"** checkbox, or manually copied (but Studio manages internal mock metadata that a raw file copy may miss).
2. **Surround with Mock** — wrapping individual activities in mock containers is a Studio GUI action. The agent cannot replicate this in XAML without the internal mock activity schema.

### Constraints

1. **Process projects only** — mocking is NOT available in Test Automation (`Tests`) projects
2. **XAML only** — no mock framework for coded test cases
3. **When container only** — mock invocations go inside the `"... When"` Sequence
4. **No nested mocks** — a mock container cannot be nested inside another mock container
5. **Package dependency** — requires `UiPath.Testing.Activities` installed
